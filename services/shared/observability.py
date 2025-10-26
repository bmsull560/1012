"""
Centralized Observability Module
Provides structured logging, metrics, tracing, and alerting for all services
"""

import os
import logging
import json
import time
from typing import Optional, Dict, Any
from datetime import datetime
from functools import wraps
from contextlib import contextmanager

# Third-party imports
from pythonjsonlogger import jsonlogger
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import datadog
from datadog import statsd


class ObservabilityConfig:
    """Centralized observability configuration for all services"""
    
    def __init__(
        self, 
        service_name: str,
        version: str = "1.0.0",
        environment: Optional[str] = None
    ):
        self.service_name = service_name
        self.version = version
        self.environment = environment or os.getenv("ENVIRONMENT", "development")
        
        # Initialize all observability components
        self.logger = self.setup_logging()
        self.setup_metrics()
        self.setup_tracing()
        self.setup_error_tracking()
        
        # Metrics collectors
        self.request_counter = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status', 'tenant_id']
        )
        
        self.request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint', 'tenant_id']
        )
        
        self.active_users = Gauge(
            'active_users',
            'Number of active users',
            ['tenant_id']
        )
        
        self.business_metrics = Counter(
            'business_operations_total',
            'Business operations counter',
            ['operation', 'tenant_id', 'status']
        )
    
    def setup_logging(self) -> logging.Logger:
        """Configure structured JSON logging with correlation IDs"""
        
        # Create logger
        logger = logging.getLogger(self.service_name)
        logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        logger.handlers = []
        
        # Create JSON formatter
        log_handler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(levelname)s %(name)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            json_default=str
        )
        log_handler.setFormatter(formatter)
        logger.addHandler(log_handler)
        
        # Add service context to all logs
        old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.service = self.service_name
            record.environment = self.environment
            record.version = self.version
            
            # Add trace context if available
            span = trace.get_current_span()
            if span.is_recording():
                ctx = span.get_span_context()
                record.trace_id = format(ctx.trace_id, '032x')
                record.span_id = format(ctx.span_id, '016x')
            
            return record
        
        logging.setLogRecordFactory(record_factory)
        
        return logger
    
    def setup_metrics(self):
        """Configure metrics collection with Prometheus and DataDog"""
        
        # DataDog configuration
        if os.getenv('DD_API_KEY'):
            datadog.initialize(
                api_key=os.getenv('DD_API_KEY'),
                app_key=os.getenv('DD_APP_KEY'),
                host_name=os.getenv('HOSTNAME', 'localhost')
            )
            
            # Set global tags
            statsd.constant_tags = [
                f'service:{self.service_name}',
                f'env:{self.environment}',
                f'version:{self.version}'
            ]
        
        # OpenTelemetry metrics
        if os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT'):
            reader = PeriodicExportingMetricReader(
                exporter=OTLPMetricExporter(
                    endpoint=os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT'),
                    insecure=self.environment == 'development'
                ),
                export_interval_millis=10000
            )
            
            provider = MeterProvider(metric_readers=[reader])
            metrics.set_meter_provider(provider)
            
            self.meter = metrics.get_meter(self.service_name, self.version)
    
    def setup_tracing(self):
        """Configure distributed tracing with OpenTelemetry"""
        
        if os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT'):
            # Set up tracer provider
            provider = TracerProvider()
            trace.set_tracer_provider(provider)
            
            # Configure OTLP exporter
            otlp_exporter = OTLPSpanExporter(
                endpoint=os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT'),
                insecure=self.environment == 'development'
            )
            
            # Add span processor
            span_processor = BatchSpanProcessor(otlp_exporter)
            provider.add_span_processor(span_processor)
            
            # Auto-instrument libraries
            FastAPIInstrumentor.instrument()
            RequestsInstrumentor.instrument()
            SQLAlchemyInstrumentor.instrument()
            
            self.tracer = trace.get_tracer(self.service_name, self.version)
    
    def setup_error_tracking(self):
        """Configure Sentry for error tracking and alerting"""
        
        if os.getenv('SENTRY_DSN'):
            sentry_sdk.init(
                dsn=os.getenv('SENTRY_DSN'),
                integrations=[
                    FastApiIntegration(transaction_style="endpoint"),
                    SqlalchemyIntegration(),
                ],
                traces_sample_rate=0.1 if self.environment == 'production' else 1.0,
                environment=self.environment,
                release=f"{self.service_name}@{self.version}",
                attach_stacktrace=True,
                send_default_pii=False,  # GDPR compliance
                before_send=self._filter_sensitive_data
            )
    
    def _filter_sensitive_data(self, event, hint):
        """Filter out sensitive data before sending to Sentry"""
        
        # List of sensitive keys to redact
        sensitive_keys = {
            'password', 'token', 'secret', 'api_key', 'authorization',
            'credit_card', 'ssn', 'tax_id', 'bank_account'
        }
        
        def redact_dict(d):
            if isinstance(d, dict):
                for key in list(d.keys()):
                    if any(s in key.lower() for s in sensitive_keys):
                        d[key] = '[REDACTED]'
                    elif isinstance(d[key], dict):
                        redact_dict(d[key])
                    elif isinstance(d[key], list):
                        for item in d[key]:
                            if isinstance(item, dict):
                                redact_dict(item)
        
        # Redact request data
        if 'request' in event and 'data' in event['request']:
            redact_dict(event['request']['data'])
        
        # Redact extra context
        if 'extra' in event:
            redact_dict(event['extra'])
        
        return event
    
    def log_request(self, method: str, path: str, status: int, duration: float, tenant_id: Optional[str] = None):
        """Log HTTP request with metrics"""
        
        # Log the request
        self.logger.info(
            "HTTP Request",
            extra={
                "method": method,
                "path": path,
                "status": status,
                "duration_ms": duration * 1000,
                "tenant_id": tenant_id
            }
        )
        
        # Update metrics
        self.request_counter.labels(
            method=method,
            endpoint=path,
            status=status,
            tenant_id=tenant_id or "unknown"
        ).inc()
        
        self.request_duration.labels(
            method=method,
            endpoint=path,
            tenant_id=tenant_id or "unknown"
        ).observe(duration)
        
        # DataDog metrics
        if os.getenv('DD_API_KEY'):
            statsd.increment(
                'api.request.count',
                tags=[
                    f'method:{method}',
                    f'endpoint:{path}',
                    f'status:{status}',
                    f'tenant:{tenant_id or "unknown"}'
                ]
            )
            
            statsd.histogram(
                'api.request.duration',
                duration * 1000,
                tags=[
                    f'method:{method}',
                    f'endpoint:{path}',
                    f'tenant:{tenant_id or "unknown"}'
                ]
            )
    
    def log_business_operation(
        self, 
        operation: str, 
        tenant_id: str, 
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log business operations with context"""
        
        status = "success" if success else "failure"
        
        self.logger.info(
            f"Business operation: {operation}",
            extra={
                "operation": operation,
                "tenant_id": tenant_id,
                "status": status,
                "metadata": metadata or {}
            }
        )
        
        # Update business metrics
        self.business_metrics.labels(
            operation=operation,
            tenant_id=tenant_id,
            status=status
        ).inc()
        
        # DataDog business metrics
        if os.getenv('DD_API_KEY'):
            statsd.increment(
                f'business.{operation}',
                tags=[
                    f'tenant:{tenant_id}',
                    f'status:{status}'
                ]
            )
    
    def track_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Track errors with full context"""
        
        self.logger.error(
            f"Error occurred: {str(error)}",
            exc_info=True,
            extra={"error_context": context or {}}
        )
        
        # Send to Sentry
        if os.getenv('SENTRY_DSN'):
            with sentry_sdk.push_scope() as scope:
                if context:
                    for key, value in context.items():
                        scope.set_extra(key, value)
                sentry_sdk.capture_exception(error)
        
        # DataDog error tracking
        if os.getenv('DD_API_KEY'):
            statsd.increment(
                'errors.count',
                tags=[
                    f'error_type:{type(error).__name__}',
                    f'service:{self.service_name}'
                ]
            )
    
    @contextmanager
    def trace_operation(self, operation_name: str, attributes: Optional[Dict[str, Any]] = None):
        """Context manager for tracing operations"""
        
        if hasattr(self, 'tracer'):
            with self.tracer.start_as_current_span(operation_name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, str(value))
                
                start_time = time.time()
                try:
                    yield span
                finally:
                    duration = time.time() - start_time
                    span.set_attribute("duration_ms", duration * 1000)
        else:
            yield None
    
    def create_middleware(self):
        """Create FastAPI middleware for automatic observability"""
        
        async def observability_middleware(request, call_next):
            # Extract tenant ID from JWT or headers
            tenant_id = request.headers.get('X-Tenant-ID', 'unknown')
            
            # Generate correlation ID
            correlation_id = request.headers.get('X-Correlation-ID', str(time.time()))
            
            # Add to context
            with self.trace_operation(
                f"{request.method} {request.url.path}",
                {
                    "http.method": request.method,
                    "http.url": str(request.url),
                    "tenant.id": tenant_id,
                    "correlation.id": correlation_id
                }
            ):
                start_time = time.time()
                
                try:
                    response = await call_next(request)
                    duration = time.time() - start_time
                    
                    # Log successful request
                    self.log_request(
                        method=request.method,
                        path=request.url.path,
                        status=response.status_code,
                        duration=duration,
                        tenant_id=tenant_id
                    )
                    
                    # Add correlation ID to response
                    response.headers["X-Correlation-ID"] = correlation_id
                    
                    return response
                    
                except Exception as e:
                    duration = time.time() - start_time
                    
                    # Log failed request
                    self.log_request(
                        method=request.method,
                        path=request.url.path,
                        status=500,
                        duration=duration,
                        tenant_id=tenant_id
                    )
                    
                    # Track error
                    self.track_error(e, {
                        "request_method": request.method,
                        "request_path": request.url.path,
                        "tenant_id": tenant_id,
                        "correlation_id": correlation_id
                    })
                    
                    raise
        
        return observability_middleware


# Singleton instance
_observability_instance: Optional[ObservabilityConfig] = None


def get_observability(service_name: str, version: str = "1.0.0") -> ObservabilityConfig:
    """Get or create observability instance"""
    global _observability_instance
    
    if _observability_instance is None:
        _observability_instance = ObservabilityConfig(service_name, version)
    
    return _observability_instance


# Decorator for timing functions
def timed_operation(operation_name: str):
    """Decorator to time and trace operations"""
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            obs = get_observability("default")
            with obs.trace_operation(operation_name):
                start = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start
                    
                    obs.logger.info(
                        f"Operation {operation_name} completed",
                        extra={"duration_ms": duration * 1000}
                    )
                    
                    return result
                except Exception as e:
                    duration = time.time() - start
                    obs.logger.error(
                        f"Operation {operation_name} failed",
                        extra={"duration_ms": duration * 1000, "error": str(e)}
                    )
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            obs = get_observability("default")
            with obs.trace_operation(operation_name):
                start = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start
                    
                    obs.logger.info(
                        f"Operation {operation_name} completed",
                        extra={"duration_ms": duration * 1000}
                    )
                    
                    return result
                except Exception as e:
                    duration = time.time() - start
                    obs.logger.error(
                        f"Operation {operation_name} failed",
                        extra={"duration_ms": duration * 1000, "error": str(e)}
                    )
                    raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# Export key components
__all__ = [
    'ObservabilityConfig',
    'get_observability',
    'timed_operation'
]

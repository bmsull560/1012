"""
Prometheus metrics instrumentation for ValueVerse Billing System
"""

from prometheus_client import (
    Counter, Histogram, Gauge, Info,
    generate_latest, CONTENT_TYPE_LATEST
)
from fastapi import Response
import time
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# ==================== Metrics Definitions ====================

# HTTP metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint']
)

# Business metrics - Billing
billing_usage_events_total = Counter(
    'billing_usage_events_total',
    'Total usage events recorded',
    ['organization', 'metric_name']
)

billing_usage_ingestion_duration_seconds = Histogram(
    'billing_usage_ingestion_duration_seconds',
    'Usage event ingestion duration in seconds',
    ['metric_name'],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0)
)

billing_invoices_generated_total = Counter(
    'billing_invoices_generated_total',
    'Total invoices generated',
    ['status', 'plan_type']
)

billing_invoice_generation_failures_total = Counter(
    'billing_invoice_generation_failures_total',
    'Total invoice generation failures',
    ['error_type']
)

billing_invoice_amount_total = Counter(
    'billing_invoice_amount_total',
    'Total invoice amount in cents',
    ['currency', 'plan_type']
)

# Payment metrics
billing_payment_attempts_total = Counter(
    'billing_payment_attempts_total',
    'Total payment attempts',
    ['provider', 'payment_method']
)

billing_payment_failures_total = Counter(
    'billing_payment_failures_total',
    'Total payment failures',
    ['provider', 'payment_method', 'error_type']
)

billing_payment_amount_total = Counter(
    'billing_payment_amount_total',
    'Total payment amount in cents',
    ['provider', 'currency']
)

billing_payment_duration_seconds = Histogram(
    'billing_payment_duration_seconds',
    'Payment processing duration in seconds',
    ['provider'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0)
)

# Subscription metrics
billing_subscriptions_active = Gauge(
    'billing_subscriptions_active',
    'Number of active subscriptions',
    ['plan', 'status']
)

billing_subscriptions_created_total = Counter(
    'billing_subscriptions_created_total',
    'Total subscriptions created',
    ['plan']
)

billing_subscriptions_canceled_total = Counter(
    'billing_subscriptions_canceled_total',
    'Total subscriptions canceled',
    ['plan', 'reason']
)

billing_subscription_mrr = Gauge(
    'billing_subscription_mrr',
    'Monthly Recurring Revenue in cents',
    ['currency']
)

# Cache metrics
cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_name', 'operation']
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_name', 'operation']
)

cache_operation_duration_seconds = Histogram(
    'cache_operation_duration_seconds',
    'Cache operation duration in seconds',
    ['cache_name', 'operation'],
    buckets=(0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05, 0.1)
)

# Database metrics
database_queries_total = Counter(
    'database_queries_total',
    'Total database queries',
    ['query_type', 'table']
)

database_query_duration_seconds = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type', 'table'],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0)
)

database_connections_active = Gauge(
    'database_connections_active',
    'Number of active database connections'
)

database_connections_idle = Gauge(
    'database_connections_idle',
    'Number of idle database connections'
)

# Event bus metrics
event_bus_messages_published_total = Counter(
    'event_bus_messages_published_total',
    'Total messages published to event bus',
    ['event_type']
)

event_bus_messages_consumed_total = Counter(
    'event_bus_messages_consumed_total',
    'Total messages consumed from event bus',
    ['event_type']
)

event_bus_message_processing_duration_seconds = Histogram(
    'event_bus_message_processing_duration_seconds',
    'Message processing duration in seconds',
    ['event_type'],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0)
)

# System info
system_info = Info(
    'billing_system_info',
    'Billing system information'
)
system_info.info({
    'version': '1.0.0',
    'service': 'billing-api',
    'environment': 'production'
})

# ==================== Decorators ====================

def track_request_metrics(method: str, endpoint: str):
    """Decorator to track HTTP request metrics"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                status = getattr(result, 'status_code', 200)
                http_requests_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status=str(status)
                ).inc()
                return result
            except Exception as e:
                http_requests_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status='500'
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                http_request_duration_seconds.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
                http_requests_in_progress.labels(
                    method=method,
                    endpoint=endpoint
                ).dec()
        
        return wrapper
    return decorator

def track_database_metrics(query_type: str, table: str):
    """Decorator to track database query metrics"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                database_queries_total.labels(
                    query_type=query_type,
                    table=table
                ).inc()
                return result
            finally:
                duration = time.time() - start_time
                database_query_duration_seconds.labels(
                    query_type=query_type,
                    table=table
                ).observe(duration)
        
        return wrapper
    return decorator

def track_cache_metrics(cache_name: str, operation: str):
    """Decorator to track cache operation metrics"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                # Determine if it was a hit or miss based on result
                if operation == 'get' and result is not None:
                    cache_hits_total.labels(
                        cache_name=cache_name,
                        operation=operation
                    ).inc()
                elif operation == 'get' and result is None:
                    cache_misses_total.labels(
                        cache_name=cache_name,
                        operation=operation
                    ).inc()
                
                return result
            finally:
                duration = time.time() - start_time
                cache_operation_duration_seconds.labels(
                    cache_name=cache_name,
                    operation=operation
                ).observe(duration)
        
        return wrapper
    return decorator

# ==================== Metrics Endpoint ====================

async def metrics_endpoint() -> Response:
    """Endpoint to expose metrics for Prometheus scraping"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

# ==================== Helper Functions ====================

def track_usage_event(organization: str, metric_name: str, duration: float):
    """Track usage event metrics"""
    billing_usage_events_total.labels(
        organization=organization,
        metric_name=metric_name
    ).inc()
    
    billing_usage_ingestion_duration_seconds.labels(
        metric_name=metric_name
    ).observe(duration)

def track_invoice_generated(status: str, plan_type: str, amount: float, currency: str):
    """Track invoice generation metrics"""
    billing_invoices_generated_total.labels(
        status=status,
        plan_type=plan_type
    ).inc()
    
    if amount > 0:
        billing_invoice_amount_total.labels(
            currency=currency,
            plan_type=plan_type
        ).inc(int(amount * 100))  # Convert to cents

def track_payment(provider: str, payment_method: str, success: bool, 
                  amount: float, currency: str, duration: float, error_type: str = None):
    """Track payment metrics"""
    billing_payment_attempts_total.labels(
        provider=provider,
        payment_method=payment_method
    ).inc()
    
    if not success:
        billing_payment_failures_total.labels(
            provider=provider,
            payment_method=payment_method,
            error_type=error_type or 'unknown'
        ).inc()
    else:
        billing_payment_amount_total.labels(
            provider=provider,
            currency=currency
        ).inc(int(amount * 100))  # Convert to cents
    
    billing_payment_duration_seconds.labels(
        provider=provider
    ).observe(duration)

def update_subscription_metrics(active_by_plan: dict, mrr_by_currency: dict):
    """Update subscription gauge metrics"""
    for plan, count in active_by_plan.items():
        billing_subscriptions_active.labels(
            plan=plan,
            status='active'
        ).set(count)
    
    for currency, mrr in mrr_by_currency.items():
        billing_subscription_mrr.labels(
            currency=currency
        ).set(int(mrr * 100))  # Convert to cents

def track_event_bus_message(event_type: str, operation: str, duration: float = None):
    """Track event bus metrics"""
    if operation == 'publish':
        event_bus_messages_published_total.labels(
            event_type=event_type
        ).inc()
    elif operation == 'consume':
        event_bus_messages_consumed_total.labels(
            event_type=event_type
        ).inc()
    
    if duration:
        event_bus_message_processing_duration_seconds.labels(
            event_type=event_type
        ).observe(duration)

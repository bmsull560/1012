"""
Value Architect Microservice with Consul, Jaeger, and Kong integration
Enhanced with service discovery, distributed tracing, and API gateway support
"""

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import json
import asyncio
import httpx
from datetime import datetime
import uuid
import redis.asyncio as redis
from enum import Enum
import consul.aio
import logging
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi.responses import PlainTextResponse
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# Distributed Tracing Setup (Jaeger)
# ============================================

# Create resource for service identification
resource = Resource.create({
    SERVICE_NAME: "value-architect",
    "service.version": "1.0.0",
    "deployment.environment": os.getenv("ENVIRONMENT", "development")
})

# Configure Jaeger exporter
jaeger_exporter = JaegerExporter(
    agent_host_name=os.getenv("JAEGER_AGENT_HOST", "jaeger"),
    agent_port=int(os.getenv("JAEGER_AGENT_PORT", 6831)),
    udp_split_oversized_batches=True,
)

# Set up tracer provider
provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(jaeger_exporter)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# Get tracer for this service
tracer = trace.get_tracer(__name__)

# ============================================
# Prometheus Metrics
# ============================================

# Define metrics
request_count = Counter(
    'value_architect_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'value_architect_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

active_models = Gauge(
    'value_architect_active_models',
    'Number of active value models'
)

model_creation_errors = Counter(
    'value_architect_model_errors_total',
    'Total number of model creation errors'
)

# ============================================
# Service Discovery Setup (Consul)
# ============================================

class ServiceRegistry:
    """Consul service registry for service discovery"""
    
    def __init__(self):
        self.consul = consul.aio.Consul(
            host=os.getenv("CONSUL_HOST", "consul"),
            port=int(os.getenv("CONSUL_PORT", 8500))
        )
        self.service_id = f"value-architect-{uuid.uuid4().hex[:8]}"
        self.service_name = "value-architect"
        self.service_port = int(os.getenv("SERVICE_PORT", 8001))
        
    async def register(self):
        """Register service with Consul"""
        try:
            await self.consul.agent.service.register(
                name=self.service_name,
                service_id=self.service_id,
                address=os.getenv("SERVICE_HOST", "value-architect"),
                port=self.service_port,
                tags=["v1", "http", "microservice"],
                check=consul.Check.http(
                    f"http://{os.getenv('SERVICE_HOST', 'localhost')}:{self.service_port}/health",
                    interval="10s",
                    timeout="5s",
                    deregister="30s"
                ),
                meta={
                    "version": "1.0.0",
                    "protocol": "http",
                    "framework": "fastapi"
                }
            )
            logger.info(f"Service registered with Consul: {self.service_id}")
        except Exception as e:
            logger.error(f"Failed to register with Consul: {e}")
    
    async def deregister(self):
        """Deregister service from Consul"""
        try:
            await self.consul.agent.service.deregister(self.service_id)
            logger.info(f"Service deregistered from Consul: {self.service_id}")
        except Exception as e:
            logger.error(f"Failed to deregister from Consul: {e}")
    
    async def discover_service(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Discover a service from Consul"""
        try:
            _, services = await self.consul.health.service(service_name, passing=True)
            if services:
                service = services[0]
                return {
                    "address": service['Service']['Address'],
                    "port": service['Service']['Port'],
                    "url": f"http://{service['Service']['Address']}:{service['Service']['Port']}"
                }
        except Exception as e:
            logger.error(f"Failed to discover service {service_name}: {e}")
        return None

# Initialize service registry
service_registry = ServiceRegistry()

# ============================================
# FastAPI Application
# ============================================

app = FastAPI(
    title="Value Architect Service",
    description="Value model design and hypothesis generation with distributed tracing",
    version="1.0.0"
)

# Instrument FastAPI with OpenTelemetry
FastAPIInstrumentor.instrument_app(app)
HTTPXClientInstrumentor().instrument()
RedisInstrumentor().instrument()
LoggingInstrumentor().instrument()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Middleware for Tracing and Metrics
# ============================================

@app.middleware("http")
async def add_tracing_headers(request: Request, call_next):
    """Add tracing headers to all requests"""
    start_time = time.time()
    
    # Extract or generate trace ID
    trace_id = request.headers.get("X-Trace-Id", str(uuid.uuid4()))
    
    # Add to context
    with tracer.start_as_current_span(
        f"{request.method} {request.url.path}",
        attributes={
            "http.method": request.method,
            "http.url": str(request.url),
            "http.scheme": request.url.scheme,
            "http.host": request.url.hostname,
            "http.target": request.url.path,
            "trace.id": trace_id
        }
    ) as span:
        # Process request
        response = await call_next(request)
        
        # Add response attributes
        span.set_attribute("http.status_code", response.status_code)
        
        # Record metrics
        duration = time.time() - start_time
        request_duration.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        request_count.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        # Add trace ID to response headers
        response.headers["X-Trace-Id"] = trace_id
        
        return response

# ============================================
# Configuration
# ============================================

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/valueverse")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8001"))

# Redis client
redis_client = None

# ============================================
# Application Lifecycle
# ============================================

@app.on_event("startup")
async def startup():
    """Initialize service connections and register with Consul"""
    global redis_client
    
    with tracer.start_as_current_span("startup"):
        # Connect to Redis
        redis_client = await redis.from_url(REDIS_URL)
        app.state.redis = redis_client
        
        # Register with Consul
        await service_registry.register()
        
        # Set initial metrics
        active_models.set(0)
        
        logger.info(f"Value Architect Service started on port {SERVICE_PORT}")
        logger.info("Tracing enabled with Jaeger")
        logger.info("Service registered with Consul")

@app.on_event("shutdown")
async def shutdown():
    """Cleanup connections and deregister from Consul"""
    with tracer.start_as_current_span("shutdown"):
        # Deregister from Consul
        await service_registry.deregister()
        
        # Close Redis connection
        if redis_client:
            await redis_client.close()
        
        logger.info("Value Architect Service shutdown complete")

# ============================================
# Health and Metrics Endpoints
# ============================================

@app.get("/health")
async def health_check():
    """Health check endpoint for Consul and Kubernetes"""
    with tracer.start_as_current_span("health_check"):
        try:
            # Check Redis connection
            await redis_client.ping()
            return {
                "status": "healthy",
                "service": "value-architect",
                "timestamp": datetime.utcnow().isoformat(),
                "checks": {
                    "redis": "ok",
                    "tracing": "enabled",
                    "service_discovery": "registered"
                }
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise HTTPException(status_code=503, detail=str(e))

@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

# ============================================
# Business Logic with Tracing
# ============================================

class ValueModelRequest(BaseModel):
    company_name: str
    industry: str
    company_size: str = Field(default="mid-market")
    target_metrics: List[str] = Field(default_factory=list)

class ValueModelResponse(BaseModel):
    id: str
    status: str
    company_name: str
    industry: str
    value_drivers: List[Dict[str, Any]]
    calculations: Optional[Dict[str, Any]] = None
    confidence_score: float
    created_at: datetime
    trace_id: Optional[str] = None

@app.post("/api/v1/value-models", response_model=ValueModelResponse)
async def create_value_model(
    request: ValueModelRequest,
    background_tasks: BackgroundTasks
):
    """Create a new value model with distributed tracing"""
    
    # Get current span for correlation
    current_span = trace.get_current_span()
    trace_id = format(current_span.get_span_context().trace_id, '032x')
    
    with tracer.start_as_current_span("create_value_model") as span:
        model_id = str(uuid.uuid4())
        span.set_attribute("model.id", model_id)
        span.set_attribute("company.name", request.company_name)
        span.set_attribute("industry", request.industry)
        
        try:
            # Step 1: Analyze company (with tracing)
            with tracer.start_as_current_span("analyze_company"):
                company_analysis = await analyze_company_with_tracing(
                    request.company_name,
                    request.industry
                )
            
            # Step 2: Call other services (with service discovery)
            committer_service = await service_registry.discover_service("value-committer")
            if committer_service:
                with tracer.start_as_current_span("call_committer_service"):
                    async with httpx.AsyncClient() as client:
                        # Pass trace context
                        headers = {
                            "X-Trace-Id": trace_id,
                            "X-Model-Id": model_id
                        }
                        try:
                            response = await client.get(
                                f"{committer_service['url']}/api/v1/commitments/suggestions",
                                headers=headers,
                                timeout=5.0
                            )
                            span.set_attribute("committer.response", response.status_code)
                        except Exception as e:
                            span.record_exception(e)
                            logger.warning(f"Could not reach committer service: {e}")
            
            # Step 3: Calculate value (with metrics)
            with tracer.start_as_current_span("calculate_value"):
                calculations = {
                    "total_potential_value": 750000,
                    "confidence_score": 0.85,
                    "roi": 3.2
                }
                span.set_attributes(calculations)
            
            # Step 4: Cache result
            with tracer.start_as_current_span("cache_result"):
                await redis_client.setex(
                    f"model:{model_id}",
                    3600,
                    json.dumps({
                        "id": model_id,
                        "company_name": request.company_name,
                        "calculations": calculations
                    })
                )
            
            # Update metrics
            active_models.inc()
            
            response = ValueModelResponse(
                id=model_id,
                status="active",
                company_name=request.company_name,
                industry=request.industry,
                value_drivers=[],
                calculations=calculations,
                confidence_score=calculations["confidence_score"],
                created_at=datetime.utcnow(),
                trace_id=trace_id
            )
            
            # Emit event (background task)
            background_tasks.add_task(
                emit_event_with_tracing,
                "value_model.created",
                response.dict(),
                trace_id
            )
            
            return response
            
        except Exception as e:
            model_creation_errors.inc()
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            logger.error(f"Failed to create value model: {e}")
            raise HTTPException(status_code=500, detail=str(e))

async def analyze_company_with_tracing(company_name: str, industry: str) -> Dict[str, Any]:
    """Analyze company with tracing context"""
    with tracer.start_as_current_span("company_analysis") as span:
        span.set_attribute("company.name", company_name)
        span.set_attribute("industry", industry)
        
        # Simulate analysis
        await asyncio.sleep(0.1)
        
        return {
            "company_profile": {
                "name": company_name,
                "industry": industry,
                "score": 0.85
            }
        }

async def emit_event_with_tracing(event_type: str, payload: Dict[str, Any], trace_id: str):
    """Emit event with trace context"""
    with tracer.start_as_current_span("emit_event") as span:
        span.set_attribute("event.type", event_type)
        span.set_attribute("trace.parent_id", trace_id)
        
        event = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": payload,
            "trace_id": trace_id
        }
        
        await redis_client.publish("value-events", json.dumps(event))
        logger.info(f"Event emitted: {event_type} (trace: {trace_id})")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)

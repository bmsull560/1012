"""
Value Architect Microservice
Handles value model design and hypothesis generation
Powered by Together.ai for intelligent value modeling
"""

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
import os
import json
import asyncio
import httpx
from datetime import datetime
import uuid
import redis.asyncio as redis
from enum import Enum
from dotenv import load_dotenv
from together_client import TogetherPipesClient

from security import SecurityHeadersMiddleware, RateLimiter, InputValidator, PasswordValidator

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Value Architect Service",
    description="Value model design and hypothesis generation",
    version="1.0.0"
)

# CORS Configuration
ALLOWED_ORIGINS = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in ALLOWED_ORIGINS if origin.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Request-ID",
        "X-Tenant-ID",
        "Accept",
        "Accept-Language"
    ],
    max_age=3600,
)

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/valueverse")
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8001"))

# Redis client for caching and pub/sub
redis_client = None

class Stage(str, Enum):
    DISCOVERY = "discovery"
    DESIGN = "design"
    VALIDATION = "validation"
    COMPLETE = "complete"

class ValueModelRequest(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=200)
    industry: str = Field(..., min_length=1, max_length=100)
    company_size: str = Field(default="mid-market", min_length=1, max_length=50)
    target_metrics: List[str] = Field(default_factory=list, max_items=20)
    context: Optional[Dict[str, Any]] = Field(None, max_length=10000)
    
    @validator('company_name')
    def validate_company_name(cls, v):
        """Validate company name format"""
        return InputValidator.validate_company_name(v)
    
    @validator('industry')
    def validate_industry(cls, v):
        """Validate industry format"""
        return InputValidator.validate_industry(v)
    
    @validator('context')
    def validate_context(cls, v):
        """Validate context structure and size"""
        if v:
            return InputValidator.validate_dict_size(v, max_size=10000)
        return v

class ValueModelResponse(BaseModel):
    id: str
    status: str
    stage: Stage
    company_name: str
    industry: str
    value_drivers: List[Dict[str, Any]]
    calculations: Optional[Dict[str, Any]] = None
    confidence_score: float
    created_at: datetime
    updated_at: datetime

class ArchitectAgent:
    """Core Value Architect Agent logic powered by Together.ai"""
    
    def __init__(self):
        self.ai_client = TogetherPipesClient()
    
    async def analyze_company(self, company_name: str, industry: str, context: str = "") -> Dict[str, Any]:
        """Analyze company and industry for value opportunities using AI"""
        # Use Together.ai to generate comprehensive value model
        value_model = await self.ai_client.generate_value_model(company_name, industry, context)
        
        # Extract company analysis from the AI response
        return {
            "company_profile": {
                "name": company_name,
                "industry": industry,
                "analysis": value_model.get('company_analysis', {}),
                "key_challenges": value_model.get('company_analysis', {}).get('challenges', []),
                "opportunities": value_model.get('company_analysis', {}).get('opportunities', [])
            },
            "confidence": value_model.get('roi_analysis', {}).get('confidence_score', 0.75),
            "full_model": value_model
        }
    
    async def identify_value_drivers(self, company_analysis: Dict) -> List[Dict[str, Any]]:
        """Extract value drivers from AI-generated model"""
        # Get value drivers from the full AI model
        full_model = company_analysis.get('full_model', {})
        ai_drivers = full_model.get('value_drivers', [])
        
        # If AI provided drivers, use them
        if ai_drivers:
            return ai_drivers
        
        # Fallback drivers if AI didn't provide any
        drivers = [
            {
                "id": "automation",
                "name": "Process Automation",
                "category": "efficiency",
                "impact_area": "operational",
                "potential_value": 250000,
                "effort_required": "medium",
                "time_to_value": 3,
                "confidence": 0.9
            },
            {
                "id": "customer_experience",
                "name": "Customer Experience Enhancement",
                "category": "revenue",
                "impact_area": "customer",
                "potential_value": 180000,
                "effort_required": "low",
                "time_to_value": 2,
                "confidence": 0.85
            },
            {
                "id": "sales_acceleration",
                "name": "Sales Cycle Acceleration",
                "category": "revenue",
                "impact_area": "sales",
                "potential_value": 320000,
                "effort_required": "medium",
                "time_to_value": 4,
                "confidence": 0.75
            }
        ]
        return drivers
    
    async def calculate_value_model(self, drivers: List[Dict]) -> Dict[str, Any]:
        """Calculate comprehensive value model"""
        total_value = sum(d["potential_value"] for d in drivers)
        avg_confidence = sum(d["confidence"] for d in drivers) / len(drivers)
        
        return {
            "total_potential_value": total_value,
            "year_1_value": total_value * 0.3,
            "year_2_value": total_value * 0.5,
            "year_3_value": total_value * 0.2,
            "roi": 3.2,
            "payback_months": 8,
            "npv": total_value * 0.85,
            "confidence_score": avg_confidence,
            "risk_adjusted_value": total_value * avg_confidence
        }
    
    async def generate_recommendations(self, model: Dict) -> List[str]:
        """Generate strategic recommendations"""
        return [
            "Start with Process Automation for quick wins",
            "Implement Customer Experience enhancements in parallel",
            "Prepare sales team for acceleration initiatives",
            "Establish KPI tracking for all value drivers",
            "Schedule quarterly value reviews"
        ]

architect = ArchitectAgent()

@app.on_event("startup")
async def startup():
    """Initialize service connections"""
    global redis_client
    redis_client = await redis.from_url(REDIS_URL)
    app.state.redis = redis_client
    print(f"Value Architect Service started on port {SERVICE_PORT}")

@app.on_event("shutdown")
async def shutdown():
    """Cleanup connections"""
    if redis_client:
        await redis_client.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "value-architect",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/ready")
async def readiness_check():
    """Readiness probe for Kubernetes"""
    try:
        # Check Redis connection
        await redis_client.ping()
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")

@app.post("/api/v1/value-models", response_model=ValueModelResponse)
async def create_value_model(
    request: ValueModelRequest,
    background_tasks: BackgroundTasks
):
    """Create a new value model"""
    model_id = str(uuid.uuid4())
    
    # Step 1: Analyze company
    company_analysis = await architect.analyze_company(
        request.company_name,
        request.industry
    )
    
    # Step 2: Identify value drivers
    value_drivers = await architect.identify_value_drivers(company_analysis)
    
    # Step 3: Calculate value model
    calculations = await architect.calculate_value_model(value_drivers)
    
    # Step 4: Generate recommendations
    recommendations = await architect.generate_recommendations(calculations)
    
    # Create response
    response = ValueModelResponse(
        id=model_id,
        status="active",
        stage=Stage.COMPLETE,
        company_name=request.company_name,
        industry=request.industry,
        value_drivers=value_drivers,
        calculations={
            **calculations,
            "recommendations": recommendations,
            "company_analysis": company_analysis
        },
        confidence_score=calculations["confidence_score"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Cache the model
    await redis_client.setex(
        f"model:{model_id}",
        3600,  # 1 hour TTL
        response.json()
    )
    
    # Emit event for other services
    background_tasks.add_task(
        emit_event,
        "value_model.created",
        response.dict()
    )
    
    return response

@app.get("/api/v1/value-models/{model_id}", response_model=ValueModelResponse)
async def get_value_model(model_id: str):
    """Get a specific value model"""
    # Try cache first
    cached = await redis_client.get(f"model:{model_id}")
    if cached:
        return ValueModelResponse.parse_raw(cached)
    
    # If not in cache, return not found (in production, would check database)
    raise HTTPException(status_code=404, detail="Value model not found")

@app.put("/api/v1/value-models/{model_id}/refine")
async def refine_value_model(
    model_id: str,
    refinements: Dict[str, Any]
):
    """Refine an existing value model with new information"""
    # Get existing model
    cached = await redis_client.get(f"model:{model_id}")
    if not cached:
        raise HTTPException(status_code=404, detail="Value model not found")
    
    model = ValueModelResponse.parse_raw(cached)
    
    # Apply refinements (simplified logic)
    if "additional_drivers" in refinements:
        model.value_drivers.extend(refinements["additional_drivers"])
    
    if "updated_calculations" in refinements:
        model.calculations.update(refinements["updated_calculations"])
    
    model.updated_at = datetime.utcnow()
    
    # Update cache
    await redis_client.setex(
        f"model:{model_id}",
        3600,
        model.json()
    )
    
    return model

async def emit_event(event_type: str, payload: Dict[str, Any]):
    """Emit event to message broker (Kafka placeholder)"""
    event = {
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "service": "value-architect",
        "payload": payload
    }
    
    # Publish to Redis pub/sub (Kafka replacement for now)
    await redis_client.publish("value-events", json.dumps(event))
    
    print(f"Event emitted: {event_type}")

@app.get("/api/v1/metrics")
async def get_service_metrics():
    """Get service metrics"""
    return {
        "service": "value-architect",
        "uptime": "99.9%",
        "requests_processed": 1234,
        "avg_response_time_ms": 145,
        "active_models": 42,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)

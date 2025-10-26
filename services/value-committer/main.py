"""
Value Committer Microservice
Handles value commitments, contracts, and deal structuring
"""

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import json
import asyncio
import httpx
from datetime import datetime, timedelta
import uuid
import redis.asyncio as redis
from enum import Enum

app = FastAPI(
    title="Value Committer Service",
    description="Value commitments and contract management",
    version="1.0.0"
)

# CORS Configuration
ALLOWED_ORIGINS = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in ALLOWED_ORIGINS if origin.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/valueverse")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8002"))
ARCHITECT_SERVICE = os.getenv("ARCHITECT_SERVICE", "http://value-architect:8001")

redis_client = None

class CommitmentStatus(str, Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    NEGOTIATING = "negotiating"
    SIGNED = "signed"
    ACTIVE = "active"
    ACHIEVED = "achieved"

class CommitmentRequest(BaseModel):
    model_id: str
    company_name: str
    stakeholder_name: str
    stakeholder_role: str
    target_value: float
    timeline_months: int
    success_metrics: List[Dict[str, Any]]
    terms: Optional[Dict[str, Any]] = None

class CommitmentResponse(BaseModel):
    id: str
    model_id: str
    status: CommitmentStatus
    company_name: str
    stakeholder: Dict[str, str]
    committed_value: float
    timeline: Dict[str, Any]
    milestones: List[Dict[str, Any]]
    success_criteria: List[Dict[str, Any]]
    confidence_score: float
    created_at: datetime
    updated_at: datetime

class CommitterAgent:
    """Core Value Committer Agent logic"""
    
    async def structure_commitment(self, request: CommitmentRequest) -> Dict[str, Any]:
        """Structure value commitment based on model"""
        # Calculate risk-adjusted commitment
        risk_factor = 0.8  # Conservative commitment factor
        committed_value = request.target_value * risk_factor
        
        return {
            "committed_value": committed_value,
            "guarantee_percentage": 80,
            "at_risk_amount": committed_value * 0.2,
            "upside_sharing": {
                "threshold": committed_value,
                "sharing_percentage": 30
            }
        }
    
    async def create_milestones(self, timeline_months: int, value: float) -> List[Dict[str, Any]]:
        """Create value realization milestones"""
        milestones = []
        quarterly_value = value / (timeline_months / 3)
        
        for quarter in range(1, (timeline_months // 3) + 1):
            milestone = {
                "id": str(uuid.uuid4()),
                "quarter": quarter,
                "target_date": (datetime.utcnow() + timedelta(days=quarter * 90)).isoformat(),
                "target_value": quarterly_value * quarter,
                "description": f"Q{quarter} Value Realization",
                "status": "pending",
                "success_criteria": [
                    f"Achieve {quarterly_value:,.0f} in realized value",
                    f"Complete Q{quarter} implementation milestones",
                    f"Stakeholder satisfaction > 8/10"
                ]
            }
            milestones.append(milestone)
        
        return milestones
    
    async def define_success_criteria(self, metrics: List[Dict]) -> List[Dict[str, Any]]:
        """Define clear success criteria"""
        criteria = []
        for metric in metrics:
            criterion = {
                "id": str(uuid.uuid4()),
                "metric": metric.get("name", "Unknown metric"),
                "target": metric.get("target", 0),
                "measurement_method": metric.get("method", "Manual tracking"),
                "frequency": metric.get("frequency", "Monthly"),
                "owner": metric.get("owner", "Customer Success")
            }
            criteria.append(criterion)
        
        return criteria
    
    async def calculate_confidence(self, commitment: Dict, model_data: Dict = None) -> float:
        """Calculate confidence in commitment achievement"""
        base_confidence = 0.75
        
        # Adjust based on various factors
        if model_data and model_data.get("confidence_score", 0) > 0.8:
            base_confidence += 0.1
        
        # Timeline factor (shorter = higher confidence)
        timeline_factor = max(0, (12 - commitment.get("timeline_months", 12)) / 12 * 0.1)
        base_confidence += timeline_factor
        
        return min(0.95, base_confidence)

committer = CommitterAgent()

@app.on_event("startup")
async def startup():
    """Initialize service connections"""
    global redis_client
    redis_client = await redis.from_url(REDIS_URL)
    app.state.redis = redis_client
    print(f"Value Committer Service started on port {SERVICE_PORT}")

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
        "service": "value-committer",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/ready")
async def readiness_check():
    """Readiness probe for Kubernetes"""
    try:
        await redis_client.ping()
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")

@app.post("/api/v1/commitments", response_model=CommitmentResponse)
async def create_commitment(
    request: CommitmentRequest,
    background_tasks: BackgroundTasks
):
    """Create a new value commitment"""
    commitment_id = str(uuid.uuid4())
    
    # Get value model data from architect service
    model_data = None
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ARCHITECT_SERVICE}/api/v1/value-models/{request.model_id}")
            if response.status_code == 200:
                model_data = response.json()
    except Exception as e:
        print(f"Could not fetch model data: {e}")
    
    # Structure the commitment
    commitment_structure = await committer.structure_commitment(request)
    
    # Create milestones
    milestones = await committer.create_milestones(
        request.timeline_months,
        commitment_structure["committed_value"]
    )
    
    # Define success criteria
    success_criteria = await committer.define_success_criteria(request.success_metrics)
    
    # Calculate confidence
    confidence = await committer.calculate_confidence(
        {"timeline_months": request.timeline_months},
        model_data
    )
    
    # Create response
    response = CommitmentResponse(
        id=commitment_id,
        model_id=request.model_id,
        status=CommitmentStatus.PROPOSED,
        company_name=request.company_name,
        stakeholder={
            "name": request.stakeholder_name,
            "role": request.stakeholder_role
        },
        committed_value=commitment_structure["committed_value"],
        timeline={
            "months": request.timeline_months,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=request.timeline_months * 30)).isoformat()
        },
        milestones=milestones,
        success_criteria=success_criteria,
        confidence_score=confidence,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Cache the commitment
    await redis_client.setex(
        f"commitment:{commitment_id}",
        3600,
        response.json()
    )
    
    # Emit event
    background_tasks.add_task(
        emit_event,
        "commitment.created",
        response.dict()
    )
    
    return response

@app.get("/api/v1/commitments/{commitment_id}", response_model=CommitmentResponse)
async def get_commitment(commitment_id: str):
    """Get a specific commitment"""
    cached = await redis_client.get(f"commitment:{commitment_id}")
    if cached:
        return CommitmentResponse.parse_raw(cached)
    
    raise HTTPException(status_code=404, detail="Commitment not found")

@app.put("/api/v1/commitments/{commitment_id}/sign")
async def sign_commitment(
    commitment_id: str,
    signature_data: Dict[str, Any]
):
    """Sign and activate a commitment"""
    cached = await redis_client.get(f"commitment:{commitment_id}")
    if not cached:
        raise HTTPException(status_code=404, detail="Commitment not found")
    
    commitment = CommitmentResponse.parse_raw(cached)
    commitment.status = CommitmentStatus.SIGNED
    commitment.updated_at = datetime.utcnow()
    
    # Update cache
    await redis_client.setex(
        f"commitment:{commitment_id}",
        3600,
        commitment.json()
    )
    
    # Emit event for other services
    await emit_event("commitment.signed", commitment.dict())
    
    return {"status": "signed", "commitment_id": commitment_id}

@app.post("/api/v1/commitments/{commitment_id}/milestones/{milestone_id}/complete")
async def complete_milestone(
    commitment_id: str,
    milestone_id: str,
    completion_data: Dict[str, Any]
):
    """Mark a milestone as complete"""
    # Implementation for milestone tracking
    return {
        "status": "completed",
        "milestone_id": milestone_id,
        "achieved_value": completion_data.get("value", 0),
        "completion_date": datetime.utcnow().isoformat()
    }

async def emit_event(event_type: str, payload: Dict[str, Any]):
    """Emit event to message broker"""
    event = {
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "service": "value-committer",
        "payload": payload
    }
    
    await redis_client.publish("value-events", json.dumps(event))
    print(f"Event emitted: {event_type}")

@app.get("/api/v1/metrics")
async def get_service_metrics():
    """Get service metrics"""
    return {
        "service": "value-committer",
        "uptime": "99.9%",
        "commitments_created": 89,
        "commitments_signed": 67,
        "total_committed_value": 5430000,
        "avg_confidence_score": 0.82,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)

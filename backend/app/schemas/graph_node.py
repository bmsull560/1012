from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class GraphNodeBase(BaseModel):
    node_type: str = Field(..., description="Type of node")
    phase: int = Field(0, ge=0, le=3, description="Lifecycle phase")
    properties: Dict[str, Any] = Field(default_factory=dict)
    confidence_score: float = Field(0.5, ge=0.0, le=1.0)

class GraphNodeCreate(GraphNodeBase):
    pass

class GraphNodeUpdate(BaseModel):
    phase: Optional[int] = None
    properties: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    valid_to: Optional[datetime] = None

class GraphNode(GraphNodeBase):
    id: UUID
    valid_from: datetime
    valid_to: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

"""Value Model Schemas for ValueVerse platform"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class ValueDriver(BaseModel):
    """Value driver schema"""
    id: Optional[str] = None
    name: str
    category: str
    baseline_value: float
    target_value: float
    unit: str
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    impact: str = "medium"  # low, medium, high
    
    model_config = ConfigDict(from_attributes=True)


class IndustryPattern(BaseModel):
    """Industry pattern schema"""
    pattern_id: str
    name: str
    industry: str
    use_case: str
    typical_value: str
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    
    model_config = ConfigDict(from_attributes=True)


class ValueHypothesis(BaseModel):
    """Value hypothesis schema"""
    hypothesis_id: Optional[str] = None
    company_name: str
    industry: str
    use_case: str
    total_value: float
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    drivers: List[ValueDriver] = Field(default_factory=list)
    patterns: List[IndustryPattern] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    timeline_months: int = 12
    created_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class ValueHypothesisCreate(BaseModel):
    """Create value hypothesis request"""
    company_name: str
    industry: str
    use_case: str
    requirements: Optional[Dict[str, Any]] = None


class ValueHypothesisResponse(BaseModel):
    """Value hypothesis response"""
    success: bool
    hypothesis: Optional[ValueHypothesis] = None
    error: Optional[str] = None

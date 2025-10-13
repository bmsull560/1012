"""Pydantic schemas for ValueVerse platform"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class ValueStage(str, Enum):
    """Value lifecycle stages"""
    HYPOTHESIS = "hypothesis"
    COMMITMENT = "commitment"
    REALIZATION = "realization"
    PROOF = "proof"


class UserRole(str, Enum):
    """User roles"""
    ADMIN = "admin"
    ANALYST = "analyst"
    SALES = "sales"
    CSM = "csm"
    VIEWER = "viewer"


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common fields"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        orm_mode = True
        use_enum_values = True


# User schemas
class UserBase(BaseModel):
    email: str
    full_name: str
    role: UserRole = UserRole.VIEWER
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class User(UserBase, BaseSchema):
    id: str
    last_login: Optional[datetime] = None


# Value Driver schemas
class ValueDriverBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    estimated_impact: float = Field(ge=0)
    confidence: float = Field(ge=0, le=1)
    measurement_method: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)


class ValueDriverCreate(ValueDriverBase):
    pass


class ValueDriver(ValueDriverBase, BaseSchema):
    id: str
    actual_impact: Optional[float] = None
    variance: Optional[float] = None


# Value Hypothesis schemas
class ValueHypothesis(BaseSchema):
    id: str
    customer_id: str
    company_name: str
    stage: ValueStage = ValueStage.HYPOTHESIS
    
    # Core value data
    value_drivers: List[ValueDriver]
    total_value_potential: float
    estimated_investment: float = 0
    confidence_score: float = Field(ge=0, le=1)
    
    # Context
    industry: Optional[str] = None
    company_size: Optional[str] = None
    key_stakeholders: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    success_metrics: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metadata
    created_by: str
    approved_by: Optional[str] = None
    approval_date: Optional[datetime] = None


# Value Commitment schemas
class ValueCommitment(BaseSchema):
    id: str
    hypothesis_id: str
    customer_id: str
    stage: ValueStage = ValueStage.COMMITMENT
    
    # Contract details
    contract_value: float
    contract_term_months: int
    start_date: datetime
    end_date: datetime
    
    # KPIs and metrics
    committed_kpis: List[Dict[str, Any]]
    penalties: Optional[Dict[str, float]] = None
    bonuses: Optional[Dict[str, float]] = None
    
    # Stakeholder sign-offs
    signed_by: List[str]
    signature_date: datetime


# Value Realization schemas
class ValueRealization(BaseSchema):
    id: str
    commitment_id: str
    customer_id: str
    stage: ValueStage = ValueStage.REALIZATION
    
    # Progress tracking
    current_progress: float = Field(ge=0, le=1)
    realized_value: float
    projected_value: float
    
    # Metrics
    metrics: Dict[str, Any]
    telemetry_data: Optional[Dict[str, Any]] = None
    
    # Status
    is_on_track: bool
    variance_percentage: float
    risk_level: str = "low"  # low, medium, high, critical
    
    # Actions
    mitigation_actions: List[str] = Field(default_factory=list)
    next_review_date: Optional[datetime] = None


# Value Proof schemas
class ValueProof(BaseSchema):
    id: str
    realization_id: str
    customer_id: str
    stage: ValueStage = ValueStage.PROOF
    
    # Final outcomes
    total_value_delivered: float
    roi_percentage: float
    payback_period_months: float
    
    # Evidence
    evidence_documents: List[str] = Field(default_factory=list)
    testimonials: List[Dict[str, str]] = Field(default_factory=list)
    case_study_url: Optional[str] = None
    
    # Expansion opportunities
    whitespace_identified: List[Dict[str, Any]] = Field(default_factory=list)
    expansion_potential: float
    renewal_probability: float = Field(ge=0, le=1)


# Industry Pattern schemas
class IndustryPattern(BaseModel):
    id: str
    industry: str
    pattern_name: str
    description: str
    
    # Pattern data
    common_pain_points: List[str]
    typical_value_drivers: List[str]
    average_roi: float
    implementation_timeline_months: int
    
    # Success factors
    success_rate: float = Field(ge=0, le=1)
    key_success_factors: List[str]
    common_risks: List[str]
    
    # Relevance
    relevance_score: float = Field(ge=0, le=1)
    usage_count: int = 0
    last_used: Optional[datetime] = None


# Canvas Component schemas
class CanvasComponent(BaseModel):
    id: str
    type: str  # value_driver, metric, chart, narrative
    position: Dict[str, float]  # {x, y}
    size: Dict[str, float]  # {width, height}
    data: Dict[str, Any]
    style: Optional[Dict[str, Any]] = None
    interactions: Optional[List[str]] = None


# Workspace schemas
class WorkspaceState(BaseModel):
    id: str
    user_id: str
    customer_id: str
    
    # Canvas state
    canvas_components: List[CanvasComponent]
    active_template: str
    zoom_level: float = 1.0
    
    # Chat state
    conversation_history: List[Dict[str, Any]]
    agent_context: Dict[str, Any]
    
    # Metadata
    last_saved: datetime
    version: int = 1


# API Response schemas
class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AgentResponse(BaseModel):
    agent: str
    response: str
    confidence: float
    reasoning: List[str]
    canvas_update: Optional[Dict[str, Any]] = None
    next_actions: Optional[List[str]] = None


class ValueModelResponse(BaseModel):
    hypothesis: ValueHypothesis
    patterns_applied: List[IndustryPattern]
    roi_projection: Dict[str, Any]
    confidence_score: float
    reasoning_summary: str


# WebSocket Event schemas
class WebSocketEvent(BaseModel):
    event_type: str
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class CanvasUpdateEvent(WebSocketEvent):
    event_type: str = "canvas_update"
    components: List[CanvasComponent]
    template: str
    updated_by: str


class AgentThoughtEvent(WebSocketEvent):
    event_type: str = "agent_thought"
    thought: str
    confidence: float
    evidence: List[str]
    agent: str

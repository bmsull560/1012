from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.agents.value_architect import ValueArchitect, ValueHypothesis

router = APIRouter(prefix="/agents", tags=["agents"])

# Initialize agent
architect = ValueArchitect()

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[dict]] = None

class PainPointRequest(BaseModel):
    conversation: str

class HypothesisRequest(BaseModel):
    pain_points: List[str]
    product_features: List[str]

@router.post("/architect/chat")
def chat_with_architect(request: ChatRequest):
    '''Chat with Value Architect for discovery'''
    try:
        response = architect.chat(request.message, request.conversation_history)
        return {"response": response, "agent": "value_architect"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/architect/discover")
def discover_pain_points(request: PainPointRequest):
    '''Extract pain points from conversation'''
    try:
        result = architect.discover_pain_points(request.conversation)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/architect/hypothesis", response_model=ValueHypothesis)
def generate_hypothesis(request: HypothesisRequest):
    '''Generate value hypothesis'''
    try:
        hypothesis = architect.generate_hypothesis(
            request.pain_points,
            request.product_features
        )
        return hypothesis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

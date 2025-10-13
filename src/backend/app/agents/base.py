"""Base agent class for ValueVerse AI agents"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio
import json
from enum import Enum
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class AgentStage(str, Enum):
    """Agent lifecycle stages"""
    PRE_SALES = "pre_sales"
    SALES = "sales"
    DELIVERY = "delivery"
    SUCCESS = "success"


class ThoughtStream(BaseModel):
    """Represents agent reasoning process"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    thought: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)
    next_action: Optional[str] = None


class AgentContext(BaseModel):
    """Context passed between agents"""
    customer_id: str
    company_name: str
    stage: AgentStage
    previous_stage: Optional[AgentStage] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    history: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseAgent(ABC):
    """Base class for all ValueVerse agents"""
    
    def __init__(self, name: str, stage: AgentStage):
        self.name = name
        self.stage = stage
        self.thought_stream: List[ThoughtStream] = []
        self.capabilities: List[str] = []
        self.tools: List[Any] = []
        
    async def think(self, thought: str, confidence: float = 0.8, evidence: List[str] = None) -> ThoughtStream:
        """Add a thought to the agent's reasoning stream"""
        thought_obj = ThoughtStream(
            thought=thought,
            confidence=confidence,
            evidence=evidence or []
        )
        self.thought_stream.append(thought_obj)
        
        # Log the thought for transparency
        logger.info(f"[{self.name}] Thinking: {thought} (confidence: {confidence})")
        
        # Broadcast thought to connected clients via WebSocket
        await self.broadcast_thought(thought_obj)
        
        return thought_obj
    
    async def broadcast_thought(self, thought: ThoughtStream):
        """Broadcast agent thoughts to connected clients"""
        # This will be implemented with WebSocket manager
        pass
    
    @abstractmethod
    async def execute(self, context: AgentContext) -> Dict[str, Any]:
        """Execute the agent's main task"""
        pass
    
    @abstractmethod
    async def validate_input(self, context: AgentContext) -> bool:
        """Validate input before execution"""
        pass
    
    async def handoff(self, next_agent: 'BaseAgent', context: AgentContext, result: Dict[str, Any]) -> AgentContext:
        """Hand off to the next agent in the lifecycle"""
        # Update context for next agent
        context.previous_stage = self.stage
        context.stage = next_agent.stage
        context.data.update(result)
        context.history.append({
            "agent": self.name,
            "stage": self.stage.value,
            "timestamp": datetime.utcnow().isoformat(),
            "result": result,
            "thought_stream": [t.dict() for t in self.thought_stream]
        })
        
        logger.info(f"Handoff from {self.name} to {next_agent.name}")
        
        return context
    
    def clear_thoughts(self):
        """Clear the thought stream"""
        self.thought_stream = []
    
    def get_reasoning_summary(self) -> str:
        """Get a summary of the agent's reasoning"""
        if not self.thought_stream:
            return "No reasoning recorded"
        
        summary = []
        for thought in self.thought_stream:
            summary.append(f"• {thought.thought} (confidence: {thought.confidence:.0%})")
        
        return "\n".join(summary)

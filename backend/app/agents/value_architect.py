import os
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

class ValueHypothesis(BaseModel):
    '''Value hypothesis generated from conversation'''
    pain_point: str = Field(description="Customer's pain point")
    value_driver: str = Field(description="How product addresses pain")
    roi_estimate: str = Field(description="Estimated ROI or benefit")
    confidence: float = Field(description="Confidence score 0-1")
    assumptions: List[str] = Field(description="Key assumptions")

class ValueArchitect:
    '''Agent for discovering pain points and generating value hypotheses'''
    
    def __init__(self, llm_provider: str = "together", model: str = "meta-llama/Llama-3.1-70B-Instruct-Turbo"):
        api_key = os.getenv("TOGETHER_API_KEY", "")
        
        self.llm = ChatOpenAI(
            base_url="https://api.together.xyz/v1",
            api_key=api_key,
            model=model,
            temperature=0.7
        )
        
        self.system_prompt = """You are a Value Architect helping discover business value.

Your role:
1. Ask clarifying questions to understand customer pain points
2. Identify value drivers (how product addresses pain)
3. Generate ROI hypotheses
4. List key assumptions

Be consultative, insightful, and ROI-focused."""
    
    def discover_pain_points(self, conversation: str) -> Dict[str, Any]:
        '''Extract pain points from conversation'''
        
        prompt = f"""Analyze this conversation and extract pain points:

{conversation}

Extract:
- Key pain points mentioned
- Impact on business
- Severity (high/medium/low)

Return JSON format."""
        
        try:
            response = self.llm.invoke([
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ])
            
            return {
                "pain_points": response.content,
                "agent": "value_architect"
            }
        except Exception as e:
            return {
                "pain_points": f"Error: {str(e)}",
                "agent": "value_architect"
            }
    
    def generate_hypothesis(self, pain_points: List[str], product_features: List[str]) -> ValueHypothesis:
        '''Generate value hypothesis from pain points'''
        
        prompt = f"""Given these pain points:
{', '.join(pain_points)}

And these product features:
{', '.join(product_features)}

Generate a value hypothesis with:
1. How features address pain
2. ROI estimate
3. Confidence level
4. Key assumptions"""
        
        try:
            response = self.llm.invoke([
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ])
            
            # Parse response - simplified for now
            return ValueHypothesis(
                pain_point=pain_points[0] if pain_points else "Unknown",
                value_driver=f"Leveraging {product_features[0] if product_features else 'automation'}",
                roi_estimate="20-30% efficiency improvement",
                confidence=0.75,
                assumptions=[
                    "Current baseline metrics are available",
                    "Implementation takes 3-6 months",
                    "Team adoption rate is high"
                ]
            )
        except Exception as e:
            # Fallback hypothesis
            return ValueHypothesis(
                pain_point=pain_points[0] if pain_points else "Unknown pain point",
                value_driver="Process improvement",
                roi_estimate="Estimated 20% improvement",
                confidence=0.5,
                assumptions=["Requires validation"]
            )
    
    def chat(self, user_message: str, conversation_history: List[Dict] = None) -> str:
        '''Interactive chat for discovery'''
        
        messages = [{"role": "system", "content": self.system_prompt}]
        
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            return f"I'm having trouble connecting right now. Error: {str(e)}"

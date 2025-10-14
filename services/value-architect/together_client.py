"""
Together.ai Client for AI-powered Value Modeling
Based on https://docs.together.ai/docs/quickstart
"""

import os
import json
import httpx
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime

class TogetherPipesClient:
    """Client for Together.ai API
    
    Together.ai provides fast inference for open-source models.
    Documentation: https://docs.together.ai/docs/quickstart
    
    To get started:
    1. Sign up at https://api.together.xyz/
    2. Get your API key from the dashboard
    3. Set TOGETHER_API_KEY environment variable
    
    Available models include:
    - mistralai/Mixtral-8x7B-Instruct-v0.1
    - meta-llama/Llama-2-70b-chat-hf
    - NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO
    - togethercomputer/CodeLlama-34b-Instruct
    """
    
    def __init__(self):
        self.api_key = os.getenv('TOGETHER_API_KEY', '')
        # Correct API endpoint per Together.ai docs
        self.base_url = "https://api.together.xyz/v1"
        # Use Mixtral which is fast and good for structured output
        self.model = os.getenv('TOGETHER_MODEL', 'mistralai/Mixtral-8x7B-Instruct-v0.1')
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    async def generate_value_model(self, company_name: str, industry: str, context: str = "") -> Dict[str, Any]:
        """Generate a comprehensive value model using Together.ai"""
        
        # Create a structured prompt for value model generation
        prompt = f"""You are a Value Architect AI agent specializing in B2B SaaS value creation. 
        
Analyze {company_name} in the {industry} industry and create a comprehensive value model.

Context: {context}

Provide a detailed analysis in the following JSON structure:
{{
  "company_analysis": {{
    "strengths": ["list of key strengths"],
    "challenges": ["list of main challenges"],
    "opportunities": ["list of growth opportunities"],
    "market_position": "brief market position analysis"
  }},
  "value_drivers": [
    {{
      "name": "Driver Name",
      "category": "efficiency|growth|retention|innovation|compliance",
      "impact_area": "operational|financial|strategic|customer",
      "description": "Detailed description of the value driver",
      "potential_value": numeric_value_in_dollars,
      "confidence": 0.0-1.0,
      "time_to_value": months_as_integer,
      "effort_required": "low|medium|high",
      "implementation_steps": ["step 1", "step 2", "step 3"],
      "success_metrics": ["metric 1", "metric 2"],
      "risks": ["risk 1", "risk 2"]
    }}
  ],
  "recommendations": {{
    "quick_wins": ["recommendation 1", "recommendation 2"],
    "strategic_initiatives": ["initiative 1", "initiative 2"],
    "measurement_framework": "How to measure success",
    "next_steps": ["step 1", "step 2", "step 3"]
  }},
  "roi_analysis": {{
    "total_potential_value": numeric_total,
    "investment_required": numeric_investment,
    "payback_period_months": integer,
    "three_year_roi": percentage,
    "confidence_score": 0.0-1.0
  }}
}}

Focus on being specific to {industry} industry best practices and {company_name}'s likely situation.
Provide realistic, actionable insights that a business executive would find valuable.
"""

        try:
            # Check if API key is set
            if not self.api_key:
                print("Warning: TOGETHER_API_KEY not set. Using fallback mode.")
                return self._generate_fallback_model(company_name, industry, context)
            
            async with httpx.AsyncClient() as client:
                # Using Together.ai's chat completions endpoint as per their docs
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a Value Architect AI that provides detailed, data-driven value models for B2B companies. Always respond with valid JSON."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.7,
                        "max_tokens": 2000,
                        "stream": False
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result['choices'][0]['message']['content']
                    
                    # Parse the JSON response
                    try:
                        value_model = json.loads(ai_response)
                        return self._enhance_value_model(value_model, company_name, industry)
                    except json.JSONDecodeError:
                        # Fallback if JSON parsing fails
                        return self._generate_fallback_model(company_name, industry, ai_response)
                else:
                    print(f"Together.ai API error: {response.status_code}")
                    return self._generate_fallback_model(company_name, industry)
                    
        except Exception as e:
            print(f"Error calling Together.ai: {e}")
            return self._generate_fallback_model(company_name, industry)
    
    async def refine_value_driver(self, driver: Dict[str, Any], additional_context: str) -> Dict[str, Any]:
        """Refine a specific value driver with additional context"""
        
        prompt = f"""Refine and expand this value driver with additional insights:

Current Driver: {json.dumps(driver, indent=2)}

Additional Context: {additional_context}

Provide an enhanced version with more specific implementation details, refined value estimates, 
and industry-specific best practices. Return as JSON maintaining the same structure but with 
improved content."""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a Value Architect AI refining value drivers with precision and expertise."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.6,
                        "max_tokens": 1000
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    refined_content = result['choices'][0]['message']['content']
                    try:
                        return json.loads(refined_content)
                    except:
                        return driver  # Return original if parsing fails
                else:
                    return driver
                    
        except Exception as e:
            print(f"Error refining driver: {e}")
            return driver
    
    async def generate_executive_summary(self, value_model: Dict[str, Any]) -> str:
        """Generate an executive summary of the value model"""
        
        prompt = f"""Based on this value model analysis, write a compelling executive summary 
        that a C-level executive would appreciate:

{json.dumps(value_model, indent=2)}

The summary should:
1. Start with the total value opportunity
2. Highlight the top 3 value drivers
3. Outline the implementation approach
4. Include key success metrics
5. Be concise (under 300 words) but impactful
"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an executive communication expert."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.7,
                        "max_tokens": 500
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result['choices'][0]['message']['content']
                else:
                    return "Executive summary generation pending."
                    
        except Exception as e:
            print(f"Error generating summary: {e}")
            return "Executive summary generation pending."
    
    def _enhance_value_model(self, model: Dict[str, Any], company_name: str, industry: str) -> Dict[str, Any]:
        """Enhance the AI-generated model with additional structure"""
        
        # Ensure all required fields are present
        if 'value_drivers' not in model:
            model['value_drivers'] = []
        
        # Add IDs and timestamps to value drivers
        for i, driver in enumerate(model.get('value_drivers', [])):
            driver['id'] = f"vd_{i+1}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            driver['created_at'] = datetime.utcnow().isoformat()
            
            # Ensure all fields have defaults
            driver.setdefault('potential_value', 100000)
            driver.setdefault('confidence', 0.75)
            driver.setdefault('time_to_value', 3)
            driver.setdefault('effort_required', 'medium')
        
        # Calculate total if not present
        if 'roi_analysis' not in model:
            model['roi_analysis'] = {}
        
        if 'total_potential_value' not in model['roi_analysis']:
            total = sum(d.get('potential_value', 0) for d in model.get('value_drivers', []))
            model['roi_analysis']['total_potential_value'] = total
        
        # Add metadata
        model['metadata'] = {
            'company_name': company_name,
            'industry': industry,
            'generated_at': datetime.utcnow().isoformat(),
            'model_version': '2.0',
            'ai_model': self.model
        }
        
        return model
    
    def _generate_fallback_model(self, company_name: str, industry: str, context: str = "") -> Dict[str, Any]:
        """Generate a fallback model if AI call fails"""
        
        # Industry-specific fallback templates
        industry_templates = {
            'SaaS': {
                'drivers': [
                    {'name': 'Customer Acquisition Optimization', 'value': 500000, 'category': 'growth'},
                    {'name': 'Churn Reduction Program', 'value': 400000, 'category': 'retention'},
                    {'name': 'Product-Led Growth Implementation', 'value': 600000, 'category': 'growth'}
                ]
            },
            'FinTech': {
                'drivers': [
                    {'name': 'Compliance Automation', 'value': 700000, 'category': 'compliance'},
                    {'name': 'Fraud Detection Enhancement', 'value': 500000, 'category': 'risk'},
                    {'name': 'Payment Processing Optimization', 'value': 400000, 'category': 'efficiency'}
                ]
            },
            'Healthcare': {
                'drivers': [
                    {'name': 'Patient Experience Digital Transformation', 'value': 800000, 'category': 'innovation'},
                    {'name': 'Clinical Workflow Optimization', 'value': 600000, 'category': 'efficiency'},
                    {'name': 'Revenue Cycle Management', 'value': 500000, 'category': 'financial'}
                ]
            }
        }
        
        template = industry_templates.get(industry, industry_templates['SaaS'])
        
        return {
            'company_analysis': {
                'strengths': ['Strong market position', 'Experienced team', 'Solid technology foundation'],
                'challenges': ['Scaling challenges', 'Competitive pressure', 'Resource constraints'],
                'opportunities': ['Market expansion', 'Product innovation', 'Strategic partnerships'],
                'market_position': f'{company_name} is positioned for growth in the {industry} sector'
            },
            'value_drivers': [
                {
                    'name': driver['name'],
                    'category': driver['category'],
                    'impact_area': 'strategic',
                    'description': f"Implementation of {driver['name']} to drive business value",
                    'potential_value': driver['value'],
                    'confidence': 0.7,
                    'time_to_value': 6,
                    'effort_required': 'medium',
                    'implementation_steps': ['Assessment', 'Planning', 'Execution', 'Optimization'],
                    'success_metrics': ['ROI improvement', 'Efficiency gains'],
                    'risks': ['Implementation complexity', 'Change management']
                }
                for driver in template['drivers']
            ],
            'recommendations': {
                'quick_wins': ['Start with pilot program', 'Focus on high-impact areas'],
                'strategic_initiatives': ['Digital transformation', 'Data-driven decision making'],
                'measurement_framework': 'Establish KPIs and regular review cycles',
                'next_steps': ['Stakeholder alignment', 'Resource allocation', 'Implementation roadmap']
            },
            'roi_analysis': {
                'total_potential_value': sum(d['value'] for d in template['drivers']),
                'investment_required': 250000,
                'payback_period_months': 12,
                'three_year_roi': 320,
                'confidence_score': 0.75
            },
            'metadata': {
                'company_name': company_name,
                'industry': industry,
                'generated_at': datetime.utcnow().isoformat(),
                'model_version': '2.0',
                'fallback_mode': True
            }
        }

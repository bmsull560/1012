"""ValueArchitect Agent - Pre-Sales Value Definition"""

from typing import Any, Dict, List, Optional
import asyncio
import httpx
from datetime import datetime
import json

from app.agents.base import BaseAgent, AgentContext, AgentStage
from app.services.research import CompanyResearchService
from app.services.pattern_matching import PatternMatchingService
from app.services.value_synthesis import ValueSynthesisService
from app.models.schemas import ValueHypothesis, ValueDriver, IndustryPattern


class ValueArchitect(BaseAgent):
    """Pre-Sales Agent: Defines value hypothesis through research and pattern matching"""
    
    def __init__(self):
        super().__init__(name="ValueArchitect", stage=AgentStage.PRE_SALES)
        self.capabilities = [
            "pain_discovery",
            "roi_hypothesis_generation",
            "value_driver_mapping",
            "industry_benchmarking",
            "competitive_analysis",
            "stakeholder_mapping"
        ]
        
        # Initialize services
        self.research_service = CompanyResearchService()
        self.pattern_service = PatternMatchingService()
        self.synthesis_service = ValueSynthesisService()
    
    async def execute(self, context: AgentContext) -> Dict[str, Any]:
        """Define value hypothesis for the customer"""
        
        await self.think(
            f"Starting value definition process for {context.company_name}",
            confidence=1.0
        )
        
        # Step 1: Research the prospect company
        await self.think(
            f"Researching {context.company_name} to understand their business context",
            confidence=0.9
        )
        company_intel = await self.research_prospect(context.company_name)
        
        # Step 2: Find similar patterns from historical data
        await self.think(
            "Analyzing historical patterns from similar companies and deals",
            confidence=0.85,
            evidence=[f"Found {len(company_intel.get('similar_companies', []))} similar companies"]
        )
        patterns = await self.find_patterns(company_intel)
        
        # Step 3: Synthesize value hypothesis
        await self.think(
            "Synthesizing value hypothesis based on research and patterns",
            confidence=0.9,
            evidence=[
                f"Industry: {company_intel.get('industry')}",
                f"Company size: {company_intel.get('size')}",
                f"Identified {len(patterns)} relevant patterns"
            ]
        )
        hypothesis = await self.synthesize_hypothesis(
            company_intel=company_intel,
            patterns=patterns,
            context=context
        )
        
        # Step 4: Generate initial ROI projections
        await self.think(
            "Calculating initial ROI projections",
            confidence=0.75,
            evidence=[f"Based on {len(hypothesis.value_drivers)} value drivers"]
        )
        roi_projection = await self.calculate_roi_projection(hypothesis)
        
        return {
            "hypothesis": hypothesis.dict(),
            "company_intel": company_intel,
            "patterns_applied": [p.dict() for p in patterns],
            "roi_projection": roi_projection,
            "confidence_score": self.calculate_confidence(hypothesis, patterns),
            "reasoning": self.get_reasoning_summary()
        }
    
    async def validate_input(self, context: AgentContext) -> bool:
        """Validate that we have necessary input to proceed"""
        return bool(context.company_name and context.customer_id)
    
    async def research_prospect(self, company_name: str) -> Dict[str, Any]:
        """Research the prospect company"""
        
        # Simulate research (in production, this would call real APIs)
        research_data = await self.research_service.research_company(company_name)
        
        return {
            "company_name": company_name,
            "industry": research_data.get("industry", "Technology"),
            "size": research_data.get("employee_count", "1000-5000"),
            "revenue": research_data.get("revenue", "$100M-$500M"),
            "pain_points": research_data.get("pain_points", [
                "Manual processes",
                "Data silos",
                "Slow decision making"
            ]),
            "tech_stack": research_data.get("tech_stack", []),
            "competitors": research_data.get("competitors", []),
            "recent_initiatives": research_data.get("initiatives", []),
            "similar_companies": research_data.get("similar_companies", [])
        }
    
    async def find_patterns(self, company_intel: Dict[str, Any]) -> List[IndustryPattern]:
        """Find relevant patterns from historical data"""
        
        patterns = await self.pattern_service.find_similar_patterns(
            industry=company_intel.get("industry"),
            company_size=company_intel.get("size"),
            pain_points=company_intel.get("pain_points", [])
        )
        
        # Sort by relevance score
        patterns.sort(key=lambda p: p.relevance_score, reverse=True)
        
        return patterns[:5]  # Return top 5 most relevant patterns
    
    async def synthesize_hypothesis(
        self,
        company_intel: Dict[str, Any],
        patterns: List[IndustryPattern],
        context: AgentContext
    ) -> ValueHypothesis:
        """Synthesize value hypothesis from research and patterns"""
        
        # Generate value drivers based on patterns and company context
        value_drivers = await self.synthesis_service.generate_value_drivers(
            company_intel=company_intel,
            patterns=patterns
        )
        
        # Create hypothesis
        hypothesis = ValueHypothesis(
            customer_id=context.customer_id,
            company_name=context.company_name,
            stage="hypothesis",
            value_drivers=value_drivers,
            total_value_potential=sum(vd.estimated_impact for vd in value_drivers),
            confidence_score=self.calculate_confidence_score(value_drivers, patterns),
            created_at=datetime.utcnow(),
            industry=company_intel.get("industry"),
            company_size=company_intel.get("size"),
            key_stakeholders=self.identify_stakeholders(company_intel),
            risk_factors=self.identify_risks(company_intel, patterns),
            success_metrics=self.define_success_metrics(value_drivers)
        )
        
        return hypothesis
    
    async def calculate_roi_projection(self, hypothesis: ValueHypothesis) -> Dict[str, Any]:
        """Calculate ROI projections based on value hypothesis"""
        
        total_investment = hypothesis.estimated_investment
        total_value = hypothesis.total_value_potential
        
        # Calculate metrics
        roi = ((total_value - total_investment) / total_investment) * 100 if total_investment > 0 else 0
        payback_period = total_investment / (total_value / 36) if total_value > 0 else 0  # Assuming 3-year value realization
        
        return {
            "total_investment": total_investment,
            "total_value_potential": total_value,
            "roi_percentage": round(roi, 1),
            "payback_period_months": round(payback_period, 1),
            "break_even_point": round(payback_period, 1),
            "three_year_value": total_value,
            "confidence_level": hypothesis.confidence_score
        }
    
    def calculate_confidence(self, hypothesis: ValueHypothesis, patterns: List[IndustryPattern]) -> float:
        """Calculate overall confidence in the hypothesis"""
        
        # Factors affecting confidence
        pattern_confidence = sum(p.relevance_score for p in patterns) / len(patterns) if patterns else 0.5
        driver_confidence = hypothesis.confidence_score
        data_completeness = 0.8  # Based on how much data we have
        
        # Weighted average
        confidence = (
            pattern_confidence * 0.4 +
            driver_confidence * 0.4 +
            data_completeness * 0.2
        )
        
        return min(confidence, 0.95)  # Cap at 95% confidence
    
    def calculate_confidence_score(self, value_drivers: List[ValueDriver], patterns: List[IndustryPattern]) -> float:
        """Calculate confidence score for the hypothesis"""
        
        if not value_drivers or not patterns:
            return 0.5
        
        # Average confidence from value drivers
        driver_confidence = sum(vd.confidence for vd in value_drivers) / len(value_drivers)
        
        # Average relevance from patterns
        pattern_relevance = sum(p.relevance_score for p in patterns) / len(patterns)
        
        # Combined confidence
        return (driver_confidence * 0.6 + pattern_relevance * 0.4)
    
    def identify_stakeholders(self, company_intel: Dict[str, Any]) -> List[str]:
        """Identify key stakeholders based on company intel"""
        
        # Standard stakeholders based on company size
        size = company_intel.get("size", "")
        
        if "enterprise" in size.lower() or "10000" in size:
            return ["C-Suite", "VP Sales", "VP Operations", "CFO", "CTO", "Procurement"]
        elif "mid" in size.lower() or "1000" in size:
            return ["VP Sales", "Director Operations", "CFO", "IT Director"]
        else:
            return ["CEO", "Head of Sales", "Operations Manager"]
    
    def identify_risks(self, company_intel: Dict[str, Any], patterns: List[IndustryPattern]) -> List[str]:
        """Identify potential risk factors"""
        
        risks = []
        
        # Industry-specific risks
        industry = company_intel.get("industry", "").lower()
        if "financial" in industry:
            risks.append("Regulatory compliance requirements")
        if "healthcare" in industry:
            risks.append("HIPAA compliance and data privacy")
        
        # Size-based risks
        size = company_intel.get("size", "")
        if "enterprise" in size.lower():
            risks.append("Complex approval process")
            risks.append("Change management challenges")
        
        # Pattern-based risks
        for pattern in patterns:
            if pattern.common_risks:
                risks.extend(pattern.common_risks[:2])  # Add top 2 risks from each pattern
        
        return list(set(risks))[:5]  # Return unique risks, max 5
    
    def define_success_metrics(self, value_drivers: List[ValueDriver]) -> List[Dict[str, Any]]:
        """Define success metrics based on value drivers"""
        
        metrics = []
        
        for driver in value_drivers:
            metric = {
                "name": f"{driver.name} Realization",
                "target": driver.estimated_impact,
                "measurement_method": driver.measurement_method,
                "frequency": "Monthly",
                "owner": "Customer Success Team"
            }
            metrics.append(metric)
        
        return metrics

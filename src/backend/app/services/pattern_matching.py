"""Pattern Matching Service - Stub for testing"""

from typing import Dict, Any, List


class PatternMatchingService:
    """Stub service for pattern matching"""
    
    async def find_patterns(self, industry: str, use_case: str) -> List[Dict[str, Any]]:
        """Find value patterns (stub implementation)"""
        return [
            {
                "pattern_id": "1",
                "name": "Digital Transformation ROI",
                "industry": industry,
                "use_case": use_case,
                "typical_value": "20-30% cost reduction",
            }
        ]

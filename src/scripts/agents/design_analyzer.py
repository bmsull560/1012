#!/usr/bin/env python3
"""
Agent 1: Design Analyzer
Analyzes design documentation and extracts component specifications.
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from typing import Dict

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agents.api_clients import get_together_client
from agents.prompt_templates import get_prompt


def read_design_docs(docs_dir: str = "docs") -> str:
    """Read all design documentation files."""
    docs_path = Path(docs_dir)
    
    if not docs_path.exists():
        raise FileNotFoundError(f"Documentation directory not found: {docs_dir}")
    
    all_docs = []
    
    # Read all markdown files
    for doc_file in docs_path.glob("*.md"):
        try:
            with open(doc_file, 'r', encoding='utf-8') as f:
                content = f.read()
                all_docs.append(f"# FILE: {doc_file.name}\n\n{content}\n\n{'='*80}\n\n")
        except Exception as e:
            print(f"⚠️  Warning: Could not read {doc_file}: {e}")
    
    combined_docs = "".join(all_docs)
    
    print(f"📚 Read {len(all_docs)} documentation files ({len(combined_docs)} characters)")
    
    return combined_docs


def extract_json_from_response(response: str) -> Dict:
    """Extract JSON object from AI response."""
    import re
    
    # Pattern 1: ```json ... ```
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Pattern 2: Direct JSON object
    json_match = re.search(r'(\{[^{]*"component"[^}]*\{.*\}.*\})', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Pattern 3: Try parsing entire response
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    raise ValueError("Could not extract valid JSON from AI response")


async def analyze_design(client, component_name: str, design_docs: str) -> Dict:
    """
    Analyze design documentation and generate component specification.
    
    Args:
        component_name: Name of component to generate spec for
        design_docs: Combined design documentation content
    
    Returns:
        Component specification as dictionary
    """
    print(f"\n🔍 Agent 1: Analyzing design for {component_name}...")
    
    
    try:
        # Get prompt template
        prompt = get_prompt(
            'design_analyzer',
            component_name=component_name,
            design_docs=design_docs
        )
        
        # Call AI with long context window
        print("🤖 Calling Together AI for design analysis...")
        response = await client.generate(
            prompt=prompt,
            model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            max_tokens=4096,
            temperature=0.3  # Lower temperature for more consistent structured output
        )
        
        # Extract JSON from response
        try:
            spec = extract_json_from_response(response)
            print("✅ Extracted component specification")
        except ValueError as e:
            print(f"⚠️  Warning: {e}")
            print("📝 Raw response:")
            print(response[:500] + "..." if len(response) > 500 else response)
            
            # Create a basic spec as fallback
            spec = {
                "component": {
                    "name": component_name,
                    "type": "interface",
                    "priority": "medium",
                    "description": f"Generated specification for {component_name}"
                },
                "design_principles": ["dual-brain", "progressive-disclosure"],
                "user_stories": [],
                "technical_requirements": {
                    "framework": "Next.js 14",
                    "component_type": "'use client'",
                    "state_management": "local",
                    "styling": "tailwind",
                    "real_time": "none",
                    "accessibility": "WCAG 2.1 AA"
                },
                "props": {},
                "state": {},
                "behaviors": [],
                "api_integrations": [],
                "styling_requirements": {},
                "progressive_disclosure": {},
                "real_time_features": [],
                "accessibility_requirements": [],
                "dependencies": []
            }
            print("⚠️  Using fallback specification")
        
        # Validate required fields
        required_fields = ['component', 'design_principles', 'technical_requirements']
        for field in required_fields:
            if field not in spec:
                print(f"⚠️  Warning: Missing required field '{field}' in specification")
        
        return spec


async def main():
    """Main execution."""
    try:
        # Get component name from request or environment
        request_file = 'output/request.json'
        
        if os.path.exists(request_file):
            with open(request_file, 'r') as f:
                request = json.load(f)
                component_name = request.get('component_name')
        else:
            component_name = os.getenv('COMPONENT_NAME')
        
        if not component_name:
            print("❌ Error: No component name provided")
            sys.exit(1)
        
        print(f"🎯 Target component: {component_name}")
        
        # Read design documentation
        design_docs = read_design_docs()
        
        # Analyze design
    client = get_together_client()
    try:
        spec = await analyze_design(client, component_name, design_docs)
    finally:
        await client.close()
        
        # Save specification
        output_dir = 'output'
        os.makedirs(output_dir, exist_ok=True)
        
        spec_file = os.path.join(output_dir, 'component_spec.json')
        with open(spec_file, 'w') as f:
            json.dump(spec, f, indent=2)
        
        print(f"💾 Saved specification to {spec_file}")
        
        # Print summary
        print("\n📊 Design Analysis Summary:")
        print(f"   Component: {spec['component']['name']}")
        print(f"   Type: {spec['component']['type']}")
        print(f"   Priority: {spec['component']['priority']}")
        print(f"   Design Principles: {', '.join(spec.get('design_principles', []))}")
        
        print("\n✅ Agent 1 (Design Analyzer) completed successfully")
        
    except Exception as e:
        print(f"\n❌ Error in Design Analyzer: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

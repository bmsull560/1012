#!/usr/bin/env python3
"""
Agent 4: Integration Engineer
Adds API integrations and real-time features to generated components.
"""

import asyncio
import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agents.api_clients import get_together_client
from agents.prompt_templates import get_prompt


def get_api_endpoints() -> str:
    """Get documentation of available API endpoints."""
    endpoints = """
# Available Backend API Endpoints

## Graph Nodes API
- POST   /api/v1/graph/nodes - Create graph node
- GET    /api/v1/graph/nodes - List nodes (filter by phase/type)
- GET    /api/v1/graph/nodes/{id} - Get specific node
- PATCH  /api/v1/graph/nodes/{id} - Update node

## AI Agents API
- POST   /api/v1/agents/architect/chat - Chat with Value Architect
- POST   /api/v1/agents/architect/discover - Extract pain points
- POST   /api/v1/agents/architect/hypothesis - Generate hypothesis

## Salesforce Integration API
- GET    /api/v1/integrations/salesforce/opportunities - List opportunities
- GET    /api/v1/integrations/salesforce/opportunities/{id} - Get opportunity
- PATCH  /api/v1/integrations/salesforce/opportunities/{id} - Update
- POST   /api/v1/integrations/salesforce/opportunities/{id}/roi - Update ROI
- GET    /api/v1/integrations/salesforce/health - Connection health

## WebSocket
- ws://localhost:8000/api/v1/ws/{workspace_id} - Real-time updates

## Health Checks
- GET    /health - Backend health
- GET    /api/v1/health - API version health
"""
    return endpoints


def read_generated_code(output_dir: str = "output/generated_code") -> str:
    """Read all generated component files."""
    path = Path(output_dir)
    
    if not path.exists():
        raise FileNotFoundError(f"Generated code directory not found: {output_dir}")
    
    all_code = []
    
    for file_path in path.rglob('*.tsx'):
        with open(file_path, 'r') as f:
            content = f.read()
            all_code.append(f"// FILE: {file_path.relative_to(path)}\n{content}\n\n")
    
    for file_path in path.rglob('*.ts'):
        if not file_path.name.endswith('.tsx'):
            with open(file_path, 'r') as f:
                content = f.read()
                all_code.append(f"// FILE: {file_path.relative_to(path)}\n{content}\n\n")
    
    return "\n".join(all_code)


async def integrate_apis(client, component_code: str, architecture_plan: Dict) -> Tuple[str, Dict]:
    """
    Add API integrations to component code.
    
    Args:
        component_code: Generated component code
        architecture_plan: Architecture plan with integration points
    
    Returns:
        Enhanced code with API integrations and metadata
    """
    print("\n🔌 Agent 4: Adding API integrations...")
    
    # Get API endpoints documentation
    api_endpoints = get_api_endpoints()
    
    
    try:
        # Get prompt template
        prompt = get_prompt(
            'integration_engineer',
            component_code=component_code,
            api_endpoints=api_endpoints
        )
        
        # Call AI
        print("🤖 Calling Together AI for API integration...")
        response = await client.generate(
            prompt=prompt,
            model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            max_tokens=4096,
            temperature=0.4
        )
        
        # Try to extract enhanced code
        code_blocks = re.findall(r'```(?:typescript|tsx)?\n(.*?)```', response, re.DOTALL)
        
        if code_blocks:
            enhanced_code = code_blocks[0]
            print("✅ Extracted enhanced code")
        else:
            print("⚠️  Could not extract enhanced code, using original")
            enhanced_code = component_code
        
        # This is a simplified metadata return. In a real scenario, you'd get this from the client.
        metadata = {
            'model': "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            'input_tokens': 0,
            'output_tokens': 0,
            'cost': 0
        }
        
        return enhanced_code, metadata


async def apply_integrations(client, output_dir: str = "output/generated_code") -> Dict:
    """Apply integrations to all generated files."""
    path = Path(output_dir)
    
    if not path.exists():
        raise FileNotFoundError(f"Generated code directory not found: {output_dir}")
    
    # Load architecture plan
    plan_file = 'output/architecture_plan.json'
    with open(plan_file, 'r') as f:
        architecture_plan = json.load(f)
    
    # Read all generated code
    component_code = read_generated_code(output_dir)
    
    # Apply integrations
    enhanced_code, metadata = await integrate_apis(client, component_code, architecture_plan)
    
    # For now, save the enhanced code as a single integrated file
    # In a real implementation, we'd parse and update individual files
    integrated_dir = "output/integrated_code"
    os.makedirs(integrated_dir, exist_ok=True)
    
    # Save enhanced code (simplified - would need proper file parsing)
    integrated_file = os.path.join(integrated_dir, "integrated_component.tsx")
    with open(integrated_file, 'w') as f:
        f.write(enhanced_code)
    
    print(f"💾 Saved integrated code to {integrated_file}")
    
    # Add metadata
    integration_metadata = {
        'agent': 'integration_engineer',
        'model': metadata['model'],
        'tokens': {'input': metadata['input_tokens'], 'output': metadata['output_tokens']},
        'cost': metadata['cost'],
        'integrations_added': len(architecture_plan.get('integration_points', []))
    }
    
    return integration_metadata


async def main():
    """Main execution."""
    try:
        print("🎯 Adding API integrations to generated components")
        
        # Apply integrations
    client = get_together_client()
    try:
        metadata = await apply_integrations(client)
    finally:
        await client.close()
        
        # Save metadata
        metadata_file = 'output/integration_metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Print summary
        print("\n📊 Integration Summary:")
        print(f"   Integrations added: {metadata['integrations_added']}")
        print(f"   Cost: ${metadata['cost']:.4f}")
        
        print("\n✅ Agent 4 (Integration Engineer) completed successfully")
        
    except Exception as e:
        print(f"\n❌ Error in Integration Engineer: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

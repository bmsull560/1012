#!/usr/bin/env python3
"""
Agent 2: Architecture Planner
Plans component file structure, hierarchy, and data flow.
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from typing import Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agents.api_clients import get_together_client
from agents.prompt_templates import get_prompt
from agents.design_analyzer import extract_json_from_response


def get_codebase_structure(base_dir: str = "frontend/src") -> str:
    """Get current codebase structure."""
    path = Path(base_dir)
    
    if not path.exists():
        return "# Codebase structure not found\n"
    
    structure = []
    structure.append(f"# Current Frontend Structure\n\n")
    
    # List key directories
    for item in sorted(path.iterdir()):
        if item.is_dir() and not item.name.startswith('.'):
            structure.append(f"- {item.name}/")
            
            # List second level for components
            if item.name == 'components':
                for subitem in sorted(item.iterdir()):
                    if subitem.is_dir():
                        structure.append(f"  - {subitem.name}/")
    
    return "\n".join(structure)


async def plan_architecture(component_spec: Dict) -> Dict:
    """
    Plan component architecture based on specification.
    
    Args:
        component_spec: Component specification from Agent 1
    
    Returns:
        Architecture plan as dictionary
    """
    component_name = component_spec['component']['name']
    
    print(f"\n🏗️  Agent 2: Planning architecture for {component_name}...")
    
    # Get current codebase structure
    file_tree = get_codebase_structure()
    
    client = get_together_client()
    
    try:
        # Get prompt template
        prompt = get_prompt(
            'architecture_planner',
            component_spec=json.dumps(component_spec, indent=2),
            file_tree=file_tree
        )
        
        # Call AI
        print("🤖 Calling Together AI for architecture planning...")
        response = await client.generate(
            prompt=prompt,
            model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            max_tokens=3072,
            temperature=0.4
        )
        
        # Extract JSON from response
        try:
            plan = extract_json_from_response(response)
            print(f"✅ Extracted architecture plan")
        except ValueError as e:
            print(f"⚠️  Warning: {e}")
            
            # Create a basic plan as fallback
            plan = {
                "files_to_create": [
                    {
                        "path": f"frontend/src/components/{component_name}/index.tsx",
                        "type": "component",
                        "purpose": "Main component export",
                        "dependencies": ["react"]
                    },
                    {
                        "path": f"frontend/src/components/{component_name}/types.ts",
                        "type": "types",
                        "purpose": "TypeScript interfaces",
                        "dependencies": []
                    }
                ],
                "component_hierarchy": {
                    component_name: {
                        "children": [],
                        "props_flow": "top-down",
                        "state_management": "local state"
                    }
                },
                "imports_structure": {
                    "external": ["react"],
                    "internal": [],
                    "types": []
                },
                "data_flow": {
                    "user_interaction": "Component → Event Handler → State Update → Re-render",
                    "api_calls": "None",
                    "websocket": "None"
                },
                "integration_points": [],
                "state_architecture": {
                    "global_state": None,
                    "local_state": [
                        {
                            "name": "isOpen",
                            "type": "boolean",
                            "purpose": "Track open/closed state"
                        }
                    ],
                    "server_state": []
                },
                "reusable_patterns": [],
                "styling_approach": {
                    "method": "Tailwind utility classes",
                    "theme_usage": "colors.primary",
                    "responsive": "mobile-first",
                    "dark_mode": "Future enhancement"
                },
                "testing_strategy": {
                    "unit_tests": f"frontend/src/components/{component_name}/__tests__/",
                    "integration_tests": "Test user interactions",
                    "accessibility_tests": "jest-axe"
                }
            }
            print("⚠️  Using fallback architecture plan")
        
        # Validate required fields
        required_fields = ['files_to_create', 'component_hierarchy', 'data_flow']
        for field in required_fields:
            if field not in plan:
                print(f"⚠️  Warning: Missing required field '{field}' in plan")
        
        return plan
    finally:
        await client.close()


async def main():
    """Main execution."""
    try:
        # Load component specification from Agent 1
        spec_file = 'output/component_spec.json'
        
        if not os.path.exists(spec_file):
            print(f"❌ Error: Component specification not found at {spec_file}")
            print("   Run design_analyzer.py first")
            sys.exit(1)
        
        with open(spec_file, 'r') as f:
            component_spec = json.load(f)
        
        component_name = component_spec['component']['name']
        print(f"🎯 Planning architecture for: {component_name}")
        
        # Plan architecture
        plan = await plan_architecture(component_spec)
        
        # Save architecture plan
        output_dir = 'output'
        plan_file = os.path.join(output_dir, 'architecture_plan.json')
        
        with open(plan_file, 'w') as f:
            json.dump(plan, f, indent=2)
        
        print(f"💾 Saved architecture plan to {plan_file}")
        
        # Print summary
        print(f"\n📊 Architecture Planning Summary:")
        print(f"   Files to create: {len(plan.get('files_to_create', []))}")
        print(f"   Integration points: {len(plan.get('integration_points', []))}")
        print(f"   State management: {plan.get('state_architecture', {}).get('global_state') or 'Local only'}")
        
        # List files
        print(f"\n📁 Files to be generated:")
        for file_info in plan.get('files_to_create', []):
            print(f"   - {file_info['path']}")
        
        print("\n✅ Agent 2 (Architecture Planner) completed successfully")
        
    except Exception as e:
        print(f"\n❌ Error in Architecture Planner: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

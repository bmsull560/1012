#!/usr/bin/env python3
"""
Agent 3: Component Generator
Generates production-ready React/TypeScript component code.
"""

import os
import sys
import json
import re
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agents.api_clients import get_openai_client
from agents.prompt_templates import get_prompt


def get_design_tokens() -> str:
    """Get design system tokens (Tailwind config, colors, etc.)."""
    tailwind_config = """
# Design Tokens (Tailwind CSS Configuration)

## Colors
- Primary: blue-600 (#2563EB)
- Secondary: gray-700 (#374151)
- Success: green-600 (#16A34A)
- Warning: amber-600 (#D97706)
- Error: red-600 (#DC2626)
- Background: gray-50 (#F9FAFB)
- Surface: white (#FFFFFF)
- Text Primary: gray-900 (#111827)
- Text Secondary: gray-600 (#4B5563)

## Typography
- Font Family: Inter, system-ui, sans-serif
- Heading: font-bold text-2xl md:text-3xl lg:text-4xl
- Subheading: font-semibold text-xl md:text-2xl
- Body: text-base text-gray-900
- Small: text-sm text-gray-600

## Spacing
- xs: 0.25rem (1)
- sm: 0.5rem (2)
- md: 1rem (4)
- lg: 1.5rem (6)
- xl: 2rem (8)
- 2xl: 3rem (12)

## Border Radius
- sm: rounded-sm (0.125rem)
- md: rounded-md (0.375rem)
- lg: rounded-lg (0.5rem)
- xl: rounded-xl (0.75rem)
- full: rounded-full (9999px)

## Shadows
- sm: shadow-sm
- md: shadow-md
- lg: shadow-lg
- xl: shadow-xl

## Responsive Breakpoints
- sm: 640px
- md: 768px
- lg: 1024px
- xl: 1280px
- 2xl: 1536px
"""
    return tailwind_config


def get_existing_patterns() -> str:
    """Get examples of existing component patterns."""
    patterns = """
# Existing Component Patterns

## Pattern 1: Client Component with State
```typescript
'use client'

import { useState } from 'react'

export function ExampleComponent() {
  const [state, setState] = useState(false)
  
  return <div>...</div>
}
```

## Pattern 2: API Integration with React Query
```typescript
import { useQuery } from '@tanstack/react-query'

const { data, isLoading } = useQuery({
  queryKey: ['resource', id],
  queryFn: () => fetch(`/api/v1/resource/${id}`).then(r => r.json())
})
```

## Pattern 3: WebSocket Integration
```typescript
import { useWebSocket } from '@/hooks/useWebSocket'

const { lastMessage, sendMessage } = useWebSocket(
  `ws://localhost:8000/api/v1/ws/${workspaceId}`
)
```

## Pattern 4: Error Boundary
```typescript
'use client'

import { ErrorBoundary } from '@/components/ErrorBoundary'

<ErrorBoundary fallback={<ErrorFallback />}>
  <Component />
</ErrorBoundary>
```
"""
    return patterns


def parse_generated_files(response: str) -> List[Tuple[str, str]]:
    """
    Parse generated code files from AI response.
    
    Returns:
        List of (file_path, file_content) tuples
    """
    files = []
    
    # Pattern: FILE: path\n---\ncontent\n---
    file_pattern = re.compile(
        r'FILE:\s*([^\n]+)\n---\n(.*?)\n---',
        re.DOTALL
    )
    
    matches = file_pattern.findall(response)
    
    if matches:
        for file_path, content in matches:
            files.append((file_path.strip(), content.strip()))
        return files
    
    # Fallback: Look for code blocks with file hints
    code_blocks = re.findall(r'```(?:typescript|tsx|ts)?\n(.*?)```', response, re.DOTALL)
    
    if code_blocks and len(code_blocks) > 0:
        # Try to guess file paths from content
        for i, code in enumerate(code_blocks):
            # Check for component exports
            if 'export function' in code or 'export const' in code:
                # Extract component name
                match = re.search(r'export (?:function|const)\s+(\w+)', code)
                if match:
                    comp_name = match.group(1)
                    file_path = f"frontend/src/components/{comp_name}/index.tsx"
                    files.append((file_path, code.strip()))
            elif 'interface' in code or 'type ' in code:
                # Types file
                file_path = "frontend/src/components/Component/types.ts"
                files.append((file_path, code.strip()))
    
    return files


def generate_component(architecture_plan: Dict, component_spec: Dict) -> List[Tuple[str, str]]:
    """
    Generate component code based on architecture plan.
    
    Args:
        architecture_plan: Architecture plan from Agent 2
        component_spec: Component specification from Agent 1
    
    Returns:
        List of (file_path, file_content) tuples
    """
    component_name = component_spec['component']['name']
    
    print(f"\n💻 Agent 3: Generating code for {component_name}...")
    
    # Get design tokens and patterns
    design_tokens = get_design_tokens()
    existing_patterns = get_existing_patterns()
    
    # Get API client (GPT-4 for best code generation)
    client = get_openai_client()
    
    # Get prompt template
    prompt = get_prompt(
        'component_generator',
        architecture_plan=json.dumps(architecture_plan, indent=2),
        design_tokens=design_tokens,
        existing_patterns=existing_patterns
    )
    
    # Call AI
    print("🤖 Calling GPT-4 for component generation...")
    response, metadata = client.complete(
        prompt=prompt,
        model="gpt-4-turbo-preview",
        max_tokens=8192,  # Large token limit for code generation
        temperature=0.5
    )
    
    print(f"✅ Received response ({metadata['output_tokens']} tokens, ${metadata['cost']:.4f})")
    
    # Parse generated files
    files = parse_generated_files(response)
    
    if not files:
        print("⚠️  Warning: No files extracted from response")
        print("📝 Creating fallback component...")
        
        # Create a basic fallback component
        main_file = f"frontend/src/components/{component_name}/index.tsx"
        main_content = f"""'use client'

import {{ useState }} from 'react'

interface {component_name}Props {{
  className?: string
}}

/**
 * {component_name} component
 * {component_spec['component'].get('description', '')}
 */
export function {component_name}({{ className }}: {component_name}Props) {{
  const [isLoading, setIsLoading] = useState(false)
  
  return (
    <div className={{`flex flex-col p-4 bg-white rounded-lg shadow-md ${{className || ''}}`}}>
      <h2 className="text-2xl font-bold text-gray-900 mb-4">
        {component_name}
      </h2>
      <p className="text-gray-600">
        Component implementation pending.
      </p>
    </div>
  )
}}
"""
        
        types_file = f"frontend/src/components/{component_name}/types.ts"
        types_content = f"""export interface {component_name}Props {{
  className?: string
}}

export interface {component_name}State {{
  isLoading: boolean
}}
"""
        
        files = [(main_file, main_content), (types_file, types_content)]
        print("⚠️  Using fallback component files")
    
    print(f"✅ Generated {len(files)} file(s)")
    
    # Add metadata to response
    generation_metadata = {
        'agent': 'component_generator',
        'model': metadata['model'],
        'tokens': {'input': metadata['input_tokens'], 'output': metadata['output_tokens']},
        'cost': metadata['cost'],
        'files_generated': len(files)
    }
    
    return files, generation_metadata


def save_generated_files(files: List[Tuple[str, str]], output_dir: str = "output/generated_code"):
    """Save generated files to disk."""
    os.makedirs(output_dir, exist_ok=True)
    
    for file_path, content in files:
        # Convert frontend/src/... to output/generated_code/...
        relative_path = file_path.replace('frontend/src/', '')
        full_path = os.path.join(output_dir, relative_path)
        
        # Create parent directories
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Write file
        with open(full_path, 'w') as f:
            f.write(content)
        
        print(f"   💾 {relative_path}")
    
    return output_dir


def main():
    """Main execution."""
    try:
        # Load architecture plan from Agent 2
        plan_file = 'output/architecture_plan.json'
        
        if not os.path.exists(plan_file):
            print(f"❌ Error: Architecture plan not found at {plan_file}")
            print("   Run architecture_planner.py first")
            sys.exit(1)
        
        with open(plan_file, 'r') as f:
            architecture_plan = json.load(f)
        
        # Load component spec from Agent 1
        spec_file = 'output/component_spec.json'
        with open(spec_file, 'r') as f:
            component_spec = json.load(f)
        
        component_name = component_spec['component']['name']
        print(f"🎯 Generating component: {component_name}")
        
        # Generate component
        files, metadata = generate_component(architecture_plan, component_spec)
        
        # Save files
        output_dir = save_generated_files(files)
        
        print(f"\n💾 Saved {len(files)} files to {output_dir}")
        
        # Save metadata
        metadata_file = 'output/generation_metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Print summary
        print("\n📊 Code Generation Summary:")
        print(f"   Files generated: {len(files)}")
        print(f"   Output directory: {output_dir}")
        print(f"   Cost: ${metadata['cost']:.4f}")
        
        print("\n📁 Generated files:")
        for file_path, _ in files:
            print(f"   - {file_path}")
        
        print("\n✅ Agent 3 (Component Generator) completed successfully")
        
    except Exception as e:
        print(f"\n❌ Error in Component Generator: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

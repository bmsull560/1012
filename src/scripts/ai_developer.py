#!/usr/bin/env python3
"""
AI Developer - Main orchestrator for automated feature development.
Analyzes GitHub issues and generates complete implementations using multiple AI models.
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict
import anthropic
import openai
from google import generativeai as genai
from github import Github
import tiktoken

# ValueVerse Platform Context
PLATFORM_CONTEXT = """
# ValueVerse Platform Architecture

## Core Stack
- **Backend**: FastAPI (Python 3.11+), LangGraph for agent orchestration
- **Frontend**: Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS + shadcn/ui
- **Database**: PostgreSQL 15 + TimescaleDB (time-series data)
- **Cache**: Redis 7
- **AI**: LangChain, CrewAI, OpenAI, Anthropic

## Key Components

### Four AI Agents
1. **ValueArchitect** (Pre-Sales): Define value, ROI hypothesis, value driver mapping
2. **ValueCommitter** (Sales): Commit to value, KPI definition, contract embedding
3. **ValueExecutor** (Delivery): Execute value, progress tracking, variance management
4. **ValueAmplifier** (Customer Success): Prove & grow value, ROI validation, expansion

### Living Value Graph
Temporal knowledge structure tracking:
- hypothesis → commitment → realization → proof
- Causal links, dependencies, attributions
- Pattern recognition across customers

### Unified Workspace
- **Left Brain**: Conversational AI with transparent reasoning
- **Right Brain**: Interactive canvas with real-time updates
- WebSocket synchronization (<100ms latency)

## Coding Standards

### Security (Non-Negotiable)
- All inputs validated (Pydantic for Python, Zod for TypeScript)
- OAuth2 + JWT authentication required
- No hardcoded secrets - use environment variables
- TLS 1.3 for all network communication
- RBAC with principle of least privilege

### Code Quality
- 80%+ test coverage (100% for critical paths)
- Comprehensive error handling with logging
- Type hints for all Python functions
- Strict TypeScript (no 'any')
- Async/await for I/O operations

### Architecture
- API-first development with OpenAPI docs
- Stateless services for horizontal scaling
- Event-driven with message queues for async tasks
"""

CODING_STANDARDS = """
# Implementation Requirements

## Python/FastAPI Backend
- Use Pydantic v2 for all data models with validators
- Async endpoints with comprehensive error handling
- Dependency injection for testability
- Structured logging with context
- OpenAPI documentation with examples

## TypeScript/React Frontend
- Functional components with hooks
- Custom hooks for reusable logic
- Error boundaries for error handling
- Accessibility (WCAG 2.1 AA)
- Responsive design (mobile-first)

## Testing
- pytest for backend (unit, integration, async)
- Jest + React Testing Library for frontend
- Playwright for E2E tests
- Mock external dependencies
- Test edge cases and error scenarios

## Documentation
- Docstrings for all public functions/classes
- JSDoc for TypeScript functions
- README for each major component
- Architecture diagrams when complex
"""


class MultiModelOrchestrator:
    """Manages multiple AI models for optimal task allocation."""
    
    def __init__(self):
        """Initialize AI clients."""
        self.claude = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        openai.api_key = os.getenv('OPENAI_API_KEY')
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        self.gemini = genai.GenerativeModel('gemini-pro')
        self.encoding = tiktoken.encoding_for_model("gpt-4")
        
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))
    
    def analyze_issue(self, issue_data: Dict, docs_context: str) -> Dict:
        """
        Analyze issue using Claude-3-Opus for best reasoning capability.
        
        Args:
            issue_data: GitHub issue information
            docs_context: Relevant documentation context
            
        Returns:
            Analysis including component type, complexity, files needed
        """
        print("🔍 Analyzing issue with Claude-3-Opus...")
        
        prompt = f"""{PLATFORM_CONTEXT}

## Relevant Documentation
{docs_context[:3000]}

## Issue to Analyze
**Title**: {issue_data['title']}
**Description**: {issue_data['body']}
**Labels**: {', '.join(issue_data['labels'])}

## Required Analysis

Analyze this feature request and provide a detailed implementation plan in JSON format:

{{
  "component_type": "backend|frontend|fullstack|agent|integration",
  "complexity": "low|medium|high",
  "estimated_hours": <number>,
  "files_to_create": [
    {{
      "path": "relative/path/to/file.py",
      "purpose": "Brief description",
      "dependencies": ["list", "of", "imports"]
    }}
  ],
  "architecture_decisions": {{
    "database_changes": "Description of any schema changes needed",
    "api_endpoints": ["List of new endpoints"],
    "components": ["List of React components"],
    "agents": ["List of AI agents involved"]
  }},
  "security_considerations": ["List security requirements"],
  "testing_requirements": {{
    "unit_tests": ["List of test files"],
    "integration_tests": ["List of integration tests"],
    "e2e_tests": ["List of E2E scenarios"]
  }},
  "dependencies": {{
    "python": ["fastapi", "langchain"],
    "npm": ["@tanstack/react-query", "zod"]
  }}
}}

Ensure the analysis is comprehensive and follows ValueVerse architecture patterns."""

        try:
            response = self.claude.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4096,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            
            # Extract JSON from response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                analysis = json.loads(content[json_start:json_end])
                print(f"✅ Analysis complete: {analysis['component_type']} - {analysis['complexity']} complexity")
                return analysis
            else:
                raise ValueError("Could not extract JSON from response")
                
        except Exception as e:
            print(f"❌ Error analyzing issue: {e}")
            # Return fallback analysis
            return {
                "component_type": "fullstack",
                "complexity": "medium",
                "estimated_hours": 8,
                "files_to_create": [],
                "error": str(e)
            }
    
    def generate_backend_code(self, analysis: Dict, context: str, file_spec: Dict) -> str:
        """
        Generate backend code using Claude-3-Opus.
        
        Args:
            analysis: Issue analysis results
            context: Documentation context
            file_spec: Specification for the file to generate
            
        Returns:
            Generated Python code
        """
        print(f"💻 Generating backend: {file_spec['path']}")
        
        prompt = f"""{PLATFORM_CONTEXT}
{CODING_STANDARDS}

## Context
{context[:2000]}

## File to Generate
**Path**: {file_spec['path']}
**Purpose**: {file_spec['purpose']}
**Dependencies**: {', '.join(file_spec.get('dependencies', []))}

## Requirements
{json.dumps(analysis, indent=2)}

## Instructions

Generate COMPLETE, PRODUCTION-READY Python code for this file that:

1. **Follows ValueVerse Architecture**:
   - Use FastAPI with async/await
   - Pydantic v2 models with validators
   - Proper dependency injection
   - Structured error handling

2. **Security Requirements**:
   - Input validation on all endpoints
   - OAuth2/JWT authentication where needed
   - No hardcoded secrets
   - SQL injection protection

3. **Code Quality**:
   - Type hints for all functions
   - Comprehensive docstrings
   - Error handling with proper status codes
   - Logging with context

4. **Testing Ready**:
   - Pure functions where possible
   - Dependency injection for mocking
   - Clear test boundaries

Output ONLY the Python code, no explanations. Include all necessary imports."""

        try:
            response = self.claude.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=8000,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )
            
            code = response.content[0].text
            
            # Extract code from markdown if present
            if '```python' in code:
                start = code.find('```python') + 9
                end = code.rfind('```')
                code = code[start:end].strip()
            
            print(f"✅ Generated {len(code)} characters")
            return code
            
        except Exception as e:
            print(f"❌ Error generating backend code: {e}")
            return f"# Error generating code: {e}\n# TODO: Implement {file_spec['purpose']}"
    
    def generate_frontend_code(self, analysis: Dict, context: str, file_spec: Dict) -> str:
        """
        Generate frontend code using GPT-4-Turbo (better for React/TypeScript).
        
        Args:
            analysis: Issue analysis results
            context: Documentation context
            file_spec: Specification for the file to generate
            
        Returns:
            Generated TypeScript/React code
        """
        print(f"⚛️  Generating frontend: {file_spec['path']}")
        
        prompt = f"""{PLATFORM_CONTEXT}
{CODING_STANDARDS}

## Context
{context[:2000]}

## File to Generate
**Path**: {file_spec['path']}
**Purpose**: {file_spec['purpose']}

## Requirements
{json.dumps(analysis, indent=2)}

## Instructions

Generate COMPLETE, PRODUCTION-READY TypeScript React code that:

1. **Modern React Patterns**:
   - Functional components with hooks
   - Custom hooks for logic reuse
   - Proper state management (Zustand/React Query)
   - Error boundaries

2. **TypeScript**:
   - Strict mode (no 'any')
   - Proper interfaces and types
   - Type-safe props and state

3. **Styling**:
   - Tailwind CSS classes
   - shadcn/ui components where appropriate
   - Responsive design (mobile-first)

4. **Accessibility**:
   - WCAG 2.1 AA compliance
   - Proper ARIA labels
   - Keyboard navigation

5. **Performance**:
   - Memoization where needed
   - Lazy loading for large components
   - Optimistic updates for mutations

Output ONLY the TypeScript code, no explanations. Include all imports."""

        try:
            response = openai.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=8000,
                temperature=0.2
            )
            
            code = response.choices[0].message.content
            
            # Extract code from markdown if present
            if '```typescript' in code or '```tsx' in code:
                start = code.find('```') + 3
                start = code.find('\n', start) + 1
                end = code.rfind('```')
                code = code[start:end].strip()
            
            print(f"✅ Generated {len(code)} characters")
            return code
            
        except Exception as e:
            print(f"❌ Error generating frontend code: {e}")
            return f"// Error generating code: {e}\n// TODO: Implement {file_spec['purpose']}"
    
    def generate_tests(self, code: str, file_path: str, component_type: str) -> str:
        """
        Generate tests using Gemini-Pro (cost-effective for test generation).
        
        Args:
            code: The code to generate tests for
            file_path: Path to the code file
            component_type: Type of component (backend/frontend)
            
        Returns:
            Generated test code
        """
        print(f"🧪 Generating tests for {file_path}")
        
        test_framework = "pytest with pytest-asyncio" if component_type == "backend" else "Jest with React Testing Library"
        
        prompt = f"""Generate comprehensive tests for this code:

```
{code}
```

Requirements:
- Use {test_framework}
- Target 80%+ code coverage
- Test happy paths and edge cases
- Test error handling
- Mock external dependencies
- Clear, descriptive test names

Output complete test file with all imports."""

        try:
            response = self.gemini.generate_content(prompt)
            test_code = response.text
            
            # Extract code if in markdown
            if '```' in test_code:
                start = test_code.find('```') + 3
                start = test_code.find('\n', start) + 1
                end = test_code.rfind('```')
                test_code = test_code[start:end].strip()
            
            print(f"✅ Generated {len(test_code)} characters of tests")
            return test_code
            
        except Exception as e:
            print(f"❌ Error generating tests: {e}")
            return f"# Error generating tests: {e}\n# TODO: Write tests"


def load_documentation() -> str:
    """Load relevant ValueVerse documentation."""
    docs_path = Path('docs')
    context_parts = []
    
    priority_docs = ['design_brief.md', 'operatingsystem.md', 'value_drivers.md']
    
    for doc_file in priority_docs:
        file_path = docs_path / doc_file
        if file_path.exists():
            with open(file_path) as f:
                content = f.read()
                # Take first 5000 chars to manage tokens
                context_parts.append(f"## {doc_file}\n{content[:5000]}")
    
    return "\n\n".join(context_parts)


def get_issue_data() -> Dict:
    """Fetch issue data from GitHub."""
    gh = Github(os.getenv('GITHUB_TOKEN'))
    repo_name = os.getenv('GITHUB_REPOSITORY')
    issue_num = int(os.getenv('ISSUE_NUMBER'))
    
    repo = gh.get_repo(repo_name)
    issue = repo.get_issue(issue_num)
    
    return {
        'number': issue_num,
        'title': issue.title,
        'body': issue.body or '',
        'labels': [label.name for label in issue.labels]
    }


def write_file(file_path: str, content: str):
    """Write content to file, creating directories as needed."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)
    print(f"📝 Wrote {file_path}")


def main():
    """Main execution flow."""
    print("🚀 AI Developer Bot Starting...")
    print("=" * 60)
    
    # Initialize
    orchestrator = MultiModelOrchestrator()
    
    # Load context
    print("\n📚 Loading documentation context...")
    docs_context = load_documentation()
    print(f"✅ Loaded {len(docs_context)} characters of documentation")
    
    # Get issue
    print("\n📋 Fetching issue data...")
    issue_data = get_issue_data()
    print(f"✅ Issue #{issue_data['number']}: {issue_data['title']}")
    
    # Analyze
    print("\n🔍 Analyzing requirements...")
    analysis = orchestrator.analyze_issue(issue_data, docs_context)
    print(f"✅ Component: {analysis.get('component_type')}")
    print(f"✅ Complexity: {analysis.get('complexity')}")
    print(f"✅ Files to create: {len(analysis.get('files_to_create', []))}")
    
    # Generate code
    print("\n💻 Generating implementation...")
    
    for file_spec in analysis.get('files_to_create', [])[:5]:  # Limit to 5 files per run
        file_path = file_spec['path']
        
        if 'backend' in file_path and file_path.endswith('.py'):
            code = orchestrator.generate_backend_code(analysis, docs_context, file_spec)
            write_file(file_path, code)
            
            # Generate tests
            test_path = file_path.replace('app/', 'tests/').replace('.py', '_test.py')
            test_code = orchestrator.generate_tests(code, file_path, 'backend')
            write_file(test_path, test_code)
            
        elif 'frontend' in file_path and (file_path.endswith('.tsx') or file_path.endswith('.ts')):
            code = orchestrator.generate_frontend_code(analysis, docs_context, file_spec)
            write_file(file_path, code)
            
            # Generate tests
            test_path = file_path.replace('.tsx', '.test.tsx').replace('.ts', '.test.ts')
            if not test_path.endswith('.test.tsx'):
                test_path = file_path.replace('.tsx', '.test.tsx')
            test_code = orchestrator.generate_tests(code, file_path, 'frontend')
            write_file(test_path, test_code)
    
    # Save analysis for reference
    write_file('ai_analysis.json', json.dumps(analysis, indent=2))
    
    print("\n✨ Implementation Complete!")
    print("=" * 60)
    print(f"Generated {len(analysis.get('files_to_create', []))} files")
    print("Ready for PR creation...")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

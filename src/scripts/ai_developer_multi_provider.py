#!/usr/bin/env python3
"""
AI Developer - Multi-Provider Support
Supports: Anthropic, OpenAI, Google, OpenRouter, Together.ai, and Windsurf AI
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict
import httpx
from github import Github

# ValueVerse Platform Context (same as before)
PLATFORM_CONTEXT = """
# ValueVerse Platform Architecture
Backend: FastAPI (Python 3.11+), LangGraph agents
Frontend: Next.js 14, React 18, TypeScript, Tailwind CSS
Database: PostgreSQL 15 + TimescaleDB, Redis 7
Four AI Agents: ValueArchitect, ValueCommitter, ValueExecutor, ValueAmplifier
Living Value Graph: Temporal knowledge structure
"""

CODING_STANDARDS = """
Security: OAuth2+JWT, input validation (Pydantic/Zod), no hardcoded secrets
Quality: 80%+ test coverage, type hints, comprehensive error handling
Architecture: API-first, stateless services, async communication
"""


class MultiProviderAI:
    """Unified interface for multiple AI providers."""
    
    def __init__(self):
        """Initialize all available AI clients."""
        self.provider = os.getenv('AI_PROVIDER', 'openrouter')  # Default to OpenRouter
        self.api_key = self._get_api_key()
        
    def _get_api_key(self) -> str:
        """Get API key based on provider."""
        key_map = {
            'openrouter': 'OPENROUTER_API_KEY',
            'together': 'TOGETHER_API_KEY',
            'windsurf': 'WINDSURF_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'openai': 'OPENAI_API_KEY',
            'google': 'GOOGLE_API_KEY'
        }
        key_name = key_map.get(self.provider)
        api_key = os.getenv(key_name)
        
        if not api_key:
            raise ValueError(f"API key {key_name} not set for provider {self.provider}")
        
        return api_key
    
    def _call_openrouter(self, prompt: str, model: str = None, max_tokens: int = 4096) -> str:
        """
        Call OpenRouter API - supports 100+ models with unified interface.
        Models: claude-3-opus, gpt-4-turbo, llama-3-70b, mixtral-8x7b, etc.
        """
        if not model:
            model = os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3-opus')
        
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/valueverse",
            "X-Title": "ValueVerse AI Developer"
        }
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.2
        }
        
        response = httpx.post(url, json=data, headers=headers, timeout=120.0)
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content']
    
    def _call_together(self, prompt: str, model: str = None, max_tokens: int = 4096) -> str:
        """
        Call Together.ai API - fast inference, competitive pricing.
        Models: meta-llama/Llama-3-70b, mistralai/Mixtral-8x7B, etc.
        """
        if not model:
            model = os.getenv('TOGETHER_MODEL', 'meta-llama/Llama-3-70b-chat-hf')
        
        url = "https://api.together.xyz/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.2,
            "stop": ["```\n\n", "###"]
        }
        
        try:
            response = httpx.post(url, json=data, headers=headers, timeout=120.0)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
        except httpx.HTTPStatusError as e:
            print(f"⚠️  Together.ai API error: {e}")
            print(f"Response body: {e.response.text[:500]}")
            raise
    
    def _call_windsurf(self, prompt: str, model: str = None, max_tokens: int = 4096) -> str:
        """
        Call Windsurf AI (Codeium's API) - optimized for code generation.
        This uses Codeium's inference API if available.
        """
        if not model:
            model = os.getenv('WINDSURF_MODEL', 'windsurf-cascade')
        
        # Windsurf/Codeium API endpoint
        url = "https://api.codeium.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.2
        }
        
        try:
            response = httpx.post(url, json=data, headers=headers, timeout=120.0)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            # Fallback: If Windsurf API not available, suggest using OpenRouter with a good model
            print(f"⚠️  Windsurf API not available: {e}")
            print("💡 Tip: Use OpenRouter with 'anthropic/claude-3-opus' instead")
            raise
    
    def _call_anthropic(self, prompt: str, model: str = None, max_tokens: int = 4096) -> str:
        """Call Anthropic API directly."""
        import anthropic
        
        if not model:
            model = "claude-3-opus-20240229"
        
        client = anthropic.Anthropic(api_key=self.api_key)
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    
    def _call_openai(self, prompt: str, model: str = None, max_tokens: int = 4096) -> str:
        """Call OpenAI API directly."""
        import openai
        
        if not model:
            model = "gpt-4-turbo-preview"
        
        openai.api_key = self.api_key
        response = openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.2
        )
        return response.choices[0].message.content
    
    def generate(self, prompt: str, task_type: str = "general", max_tokens: int = 4096) -> str:
        """
        Generate response using configured provider.
        
        Args:
            prompt: The prompt to send
            task_type: Type of task (analysis, backend, frontend, tests)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        # Model selection based on task type
        model_preferences = {
            'openrouter': {
                'analysis': 'anthropic/claude-3-opus',
                'backend': 'anthropic/claude-3-opus',
                'frontend': 'openai/gpt-4-turbo',
                'tests': 'google/gemini-pro',
                'general': 'anthropic/claude-3-sonnet'
            },
            'together': {
                'analysis': 'meta-llama/Llama-3-70b-chat-hf',
                'backend': 'meta-llama/Llama-3-70b-chat-hf',
                'frontend': 'meta-llama/Llama-3-70b-chat-hf',
                'tests': 'mistralai/Mixtral-8x7B-Instruct-v0.1',
                'general': 'meta-llama/Llama-3-70b-chat-hf'
            },
            'windsurf': {
                'analysis': 'windsurf-cascade',
                'backend': 'windsurf-cascade',
                'frontend': 'windsurf-cascade',
                'tests': 'windsurf-cascade',
                'general': 'windsurf-cascade'
            }
        }
        
        model = model_preferences.get(self.provider, {}).get(task_type)
        
        print(f"🤖 Using {self.provider} - Model: {model} - Task: {task_type}")
        
        # Route to appropriate provider
        if self.provider == 'openrouter':
            return self._call_openrouter(prompt, model, max_tokens)
        elif self.provider == 'together':
            return self._call_together(prompt, model, max_tokens)
        elif self.provider == 'windsurf':
            return self._call_windsurf(prompt, model, max_tokens)
        elif self.provider == 'anthropic':
            return self._call_anthropic(prompt, model, max_tokens)
        elif self.provider == 'openai':
            return self._call_openai(prompt, model, max_tokens)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")


class AIOrchestrator:
    """Main orchestrator using multi-provider AI."""
    
    def __init__(self):
        self.ai = MultiProviderAI()
    
    def analyze_issue(self, issue_data: Dict, docs_context: str) -> Dict:
        """Analyze issue and generate implementation plan."""
        prompt = f"""{PLATFORM_CONTEXT}

## Documentation Context
{docs_context[:3000]}

## Issue to Analyze
Title: {issue_data['title']}
Description: {issue_data['body']}

Analyze and provide JSON with:
- component_type (backend/frontend/fullstack)
- complexity (low/medium/high)
- files_to_create (list with path, purpose)
- security_considerations
- testing_requirements

Return only valid JSON."""

        response = self.ai.generate(prompt, task_type='analysis', max_tokens=4096)
        
        # Extract JSON with improved parsing
        json_start = response.find('{')
        if json_start == -1:
            print("⚠️  No JSON found in response, using defaults")
            return {'component_type': 'fullstack', 'complexity': 'high', 'files_to_create': []}
        
        # Find matching closing brace
        brace_count = 0
        json_end = json_start
        for i in range(json_start, len(response)):
            if response[i] == '{':
                brace_count += 1
            elif response[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    json_end = i + 1
                    break
        
        try:
            json_str = response[json_start:json_end]
            result = json.loads(json_str)
            print(f"✅ Parsed analysis: {result.get('component_type')}, {result.get('complexity')}")
            return result
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parse error: {e}")
            print(f"Attempted to parse: {json_str[:200]}...")
            return {'component_type': 'fullstack', 'complexity': 'high', 'files_to_create': []}
    
    def generate_backend_code(self, analysis: Dict, context: str, file_spec: Dict) -> str:
        """Generate backend code."""
        prompt = f"""{PLATFORM_CONTEXT}
{CODING_STANDARDS}

File: {file_spec['path']}
Purpose: {file_spec['purpose']}

Generate production-ready FastAPI code with:
- Async endpoints, Pydantic validation
- OAuth2 authentication
- Comprehensive error handling
- Type hints and docstrings

Output only Python code, no explanations."""

        return self.ai.generate(prompt, task_type='backend', max_tokens=8000)
    
    def generate_frontend_code(self, analysis: Dict, context: str, file_spec: Dict) -> str:
        """Generate frontend code."""
        prompt = f"""{PLATFORM_CONTEXT}
{CODING_STANDARDS}

File: {file_spec['path']}
Purpose: {file_spec['purpose']}

Generate Next.js 14 TypeScript component with:
- Functional component with hooks
- Tailwind CSS styling
- Strict TypeScript (no 'any')
- Accessibility (WCAG 2.1 AA)

Output only TypeScript code, no explanations."""

        return self.ai.generate(prompt, task_type='frontend', max_tokens=8000)
    
    def generate_tests(self, code: str, file_path: str, component_type: str) -> str:
        """Generate comprehensive tests."""
        framework = "pytest" if component_type == "backend" else "Jest + React Testing Library"
        
        prompt = f"""Generate comprehensive tests for:

```
{code[:4000]}
```

Use {framework}. Target 80%+ coverage.
Include unit tests, integration tests, edge cases.
Output complete test file."""

        return self.ai.generate(prompt, task_type='tests', max_tokens=6000)


def load_documentation() -> str:
    """Load ValueVerse documentation."""
    docs_path = Path('docs')
    context_parts = []
    
    for doc_file in ['design_brief.md', 'operatingsystem.md', 'value_drivers.md']:
        file_path = docs_path / doc_file
        if file_path.exists():
            with open(file_path) as f:
                context_parts.append(f"## {doc_file}\n{f.read()[:5000]}")
    
    return "\n\n".join(context_parts)


def get_issue_data() -> Dict:
    """Fetch issue data from GitHub."""
    gh = Github(os.getenv('GITHUB_TOKEN'))
    repo = gh.get_repo(os.getenv('GITHUB_REPOSITORY'))
    issue_num = int(os.getenv('ISSUE_NUMBER'))
    issue = repo.get_issue(issue_num)
    
    return {
        'number': issue_num,
        'title': issue.title,
        'body': issue.body or '',
        'labels': [label.name for label in issue.labels]
    }


def write_file(file_path: str, content: str):
    """Write content to file."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Extract code from markdown if present
    if '```' in content:
        lines = content.split('\n')
        in_code = False
        code_lines = []
        
        for line in lines:
            if line.strip().startswith('```'):
                in_code = not in_code
                continue
            if in_code:
                code_lines.append(line)
        
        if code_lines:
            content = '\n'.join(code_lines)
    
    with open(path, 'w') as f:
        f.write(content)
    
    print(f"✅ Wrote {file_path}")


def main():
    """Main execution."""
    print("🚀 AI Developer (Multi-Provider) Starting...")
    print(f"Provider: {os.getenv('AI_PROVIDER', 'openrouter')}")
    print("=" * 60)
    
    orchestrator = AIOrchestrator()
    
    print("\n📚 Loading documentation...")
    docs_context = load_documentation()
    
    print("\n📋 Fetching issue...")
    issue_data = get_issue_data()
    print(f"Issue #{issue_data['number']}: {issue_data['title']}")
    
    print("\n🔍 Analyzing requirements...")
    analysis = orchestrator.analyze_issue(issue_data, docs_context)
    print(f"Component: {analysis.get('component_type')}")
    print(f"Complexity: {analysis.get('complexity')}")
    
    print("\n💻 Generating implementation...")
    for file_spec in analysis.get('files_to_create', [])[:5]:
        file_path = file_spec['path']
        
        if 'backend' in file_path and file_path.endswith('.py'):
            code = orchestrator.generate_backend_code(analysis, docs_context, file_spec)
            write_file(file_path, code)
            
            test_path = file_path.replace('app/', 'tests/').replace('.py', '_test.py')
            tests = orchestrator.generate_tests(code, file_path, 'backend')
            write_file(test_path, tests)
            
        elif 'frontend' in file_path and (file_path.endswith('.tsx') or file_path.endswith('.ts')):
            code = orchestrator.generate_frontend_code(analysis, docs_context, file_spec)
            write_file(file_path, code)
            
            test_path = file_path.replace('.tsx', '.test.tsx').replace('.ts', '.test.ts')
            tests = orchestrator.generate_tests(code, file_path, 'frontend')
            write_file(test_path, tests)
    
    write_file('ai_analysis.json', json.dumps(analysis, indent=2))
    
    print("\n✨ Implementation Complete!")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

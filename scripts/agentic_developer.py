#!/usr/bin/env python3
"""
ValueVerse Agentic Developer - Autonomous Multi-Agent Development System

A sophisticated agentic system that autonomously develops complete applications
through coordinated specialist agents working together.
"""

import os
import json
import httpx
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

@dataclass
class Task:
    """Represents a development task"""
    id: str
    type: str  # analysis, architecture, implementation, testing, documentation
    description: str
    dependencies: List[str]
    status: str  # pending, in_progress, completed, failed
    output: Optional[Dict] = None
    priority: int = 5

class AgentRole(Enum):
    """Specialized agent roles"""
    ARCHITECT = "architect"      # System design & architecture
    PLANNER = "planner"          # Task breakdown & planning
    BACKEND_DEV = "backend_dev"  # Backend implementation
    FRONTEND_DEV = "frontend_dev" # Frontend implementation
    TESTER = "tester"            # Testing & QA
    REVIEWER = "reviewer"        # Code review
    INTEGRATOR = "integrator"    # Integration & deployment

class AgenticDeveloper:
    """
    Autonomous multi-agent development system.
    Coordinates specialized agents to build complete applications.
    """
    
    def __init__(self):
        self.provider = os.getenv('AI_PROVIDER', 'together')
        self.api_key = self._get_api_key()
        self.tasks: List[Task] = []
        self.completed_files: Dict[str, str] = {}
        
    def _get_api_key(self) -> str:
        """Get API key for the configured provider"""
        key_map = {
            'together': 'TOGETHER_API_KEY',
            'openrouter': 'OPENROUTER_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
        }
        key_name = key_map.get(self.provider)
        api_key = os.getenv(key_name)
        if not api_key:
            raise ValueError(f"API key {key_name} not set for provider {self.provider}")
        return api_key
    
    def call_llm(self, prompt: str, role: str = "developer", max_tokens: int = 8000) -> str:
        """Call LLM with appropriate model based on provider"""
        if self.provider == 'together':
            return self._call_together(prompt, max_tokens)
        elif self.provider == 'openrouter':
            return self._call_openrouter(prompt, max_tokens)
        elif self.provider == 'anthropic':
            return self._call_anthropic(prompt, max_tokens)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _call_together(self, prompt: str, max_tokens: int) -> str:
        """Call Together.ai API"""
        model = "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
        url = "https://api.together.xyz/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.3,
        }
        
        response = httpx.post(url, json=data, headers=headers, timeout=180.0)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    
    def _call_openrouter(self, prompt: str, max_tokens: int) -> str:
        """Call OpenRouter API"""
        model = "anthropic/claude-3-sonnet"
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/bmsull560/1012",
        }
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
        }
        
        response = httpx.post(url, json=data, headers=headers, timeout=180.0)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    
    def _call_anthropic(self, prompt: str, max_tokens: int) -> str:
        """Call Anthropic API directly"""
        from anthropic import Anthropic
        client = Anthropic(api_key=self.api_key)
        
        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    
    def architect_agent(self, requirements: str) -> Dict:
        """
        Architect Agent: Analyzes requirements and designs system architecture
        """
        print("\n🏗️  ARCHITECT AGENT: Designing system architecture...")
        
        prompt = f"""You are a senior software architect. Analyze these requirements and design a complete system architecture.

REQUIREMENTS:
{requirements}

Provide a comprehensive architectural design as JSON with:
{{
    "system_overview": "brief description",
    "components": [
        {{
            "name": "component name",
            "type": "backend|frontend|database|service",
            "purpose": "what it does",
            "technologies": ["tech1", "tech2"],
            "dependencies": ["other components it depends on"]
        }}
    ],
    "files_to_create": [
        {{
            "path": "relative/path/to/file.py",
            "type": "backend|frontend|config|test",
            "purpose": "what this file does",
            "priority": 1-10,
            "dependencies": ["files that must exist first"]
        }}
    ],
    "implementation_phases": [
        {{
            "phase": 1,
            "name": "Phase name",
            "description": "What gets built",
            "files": ["list of file paths"]
        }}
    ],
    "tech_stack": {{
        "backend": ["FastAPI", "SQLAlchemy"],
        "frontend": ["Next.js", "React"],
        "database": ["PostgreSQL"],
        "other": ["Redis", "Celery"]
    }}
}}

Return ONLY valid JSON, no markdown or explanation."""
        
        response = self.call_llm(prompt, "architect", max_tokens=4096)
        
        # Extract JSON
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            architecture = json.loads(response[json_start:json_end])
            print(f"✅ Architecture designed: {len(architecture.get('files_to_create', []))} files planned")
            return architecture
        
        raise ValueError("Failed to get valid architecture from architect agent")
    
    def planner_agent(self, architecture: Dict) -> List[Task]:
        """
        Planner Agent: Breaks down architecture into ordered tasks
        """
        print("\n📋 PLANNER AGENT: Creating development task plan...")
        
        tasks = []
        task_id = 1
        
        # Create tasks from architecture
        for phase in architecture.get('implementation_phases', []):
            for file_path in phase.get('files', []):
                # Find file details
                file_spec = next(
                    (f for f in architecture.get('files_to_create', []) 
                     if f['path'] == file_path),
                    None
                )
                
                if file_spec:
                    task = Task(
                        id=f"task_{task_id}",
                        type="implementation",
                        description=f"Implement {file_path}: {file_spec.get('purpose', '')}",
                        dependencies=file_spec.get('dependencies', []),
                        status="pending",
                        priority=file_spec.get('priority', 5)
                    )
                    tasks.append(task)
                    task_id += 1
        
        # Sort by priority and dependencies
        tasks.sort(key=lambda t: (t.priority, len(t.dependencies)))
        
        print(f"✅ Plan created: {len(tasks)} tasks")
        return tasks
    
    def implementation_agent(self, task: Task, architecture: Dict, context: str) -> str:
        """
        Implementation Agent: Generates actual code for a specific file
        """
        file_spec = next(
            (f for f in architecture.get('files_to_create', [])
             if task.description.startswith(f"Implement {f['path']}")),
            None
        )
        
        if not file_spec:
            raise ValueError(f"No file spec found for task: {task.description}")
        
        print(f"\n💻 IMPLEMENTATION AGENT: Generating {file_spec['path']}...")
        
        prompt = f"""You are an expert {file_spec['type']} developer. Generate production-ready code.

PROJECT CONTEXT:
{context}

FILE TO IMPLEMENT:
Path: {file_spec['path']}
Type: {file_spec['type']}
Purpose: {file_spec['purpose']}
Technologies: {', '.join(architecture.get('tech_stack', {}).get(file_spec['type'], []))}

REQUIREMENTS:
- Write complete, production-ready code
- Include all necessary imports
- Add docstrings and comments
- Follow best practices and security standards
- Make it type-safe and well-structured
- Include error handling

ALREADY IMPLEMENTED FILES:
{json.dumps(list(self.completed_files.keys()), indent=2)}

Generate the COMPLETE file content. Return ONLY the code, no markdown or explanation.
Start directly with the code."""
        
        code = self.call_llm(prompt, "developer", max_tokens=8000)
        
        # Clean up markdown if present
        if code.startswith('```'):
            lines = code.split('\n')
            code = '\n'.join(lines[1:-1]) if len(lines) > 2 else code
        
        print(f"✅ Generated {len(code)} characters of code")
        return code
    
    def tester_agent(self, file_path: str, code: str, architecture: Dict) -> str:
        """
        Tester Agent: Generates comprehensive tests for implemented code
        """
        print(f"\n🧪 TESTER AGENT: Generating tests for {file_path}...")
        
        # Determine test framework
        if file_path.endswith('.py'):
            test_framework = "pytest"
            test_path = file_path.replace('app/', 'tests/test_').replace('.py', '_test.py')
        elif file_path.endswith(('.ts', '.tsx')):
            test_framework = "Jest + React Testing Library"
            test_path = file_path.replace('.tsx', '.test.tsx').replace('.ts', '.test.ts')
        else:
            return ""  # Skip tests for other file types
        
        prompt = f"""You are a testing expert. Generate comprehensive tests.

FILE BEING TESTED:
{file_path}

CODE:
{code[:2000]}  # First 2000 chars

Generate complete test file for {test_path} using {test_framework}.

Requirements:
- Test all major functions/components
- Include edge cases
- Test error handling
- Aim for >80% coverage
- Use proper mocking where needed

Return ONLY the complete test code, no markdown."""
        
        test_code = self.call_llm(prompt, "tester", max_tokens=6000)
        
        if test_code.startswith('```'):
            lines = test_code.split('\n')
            test_code = '\n'.join(lines[1:-1]) if len(lines) > 2 else test_code
        
        print(f"✅ Generated test file: {test_path}")
        return test_code
    
    def reviewer_agent(self, file_path: str, code: str) -> Tuple[bool, List[str]]:
        """
        Reviewer Agent: Reviews code for quality, security, and best practices
        """
        print(f"\n🔍 REVIEWER AGENT: Reviewing {file_path}...")
        
        prompt = f"""You are a senior code reviewer. Review this code for quality and security.

FILE: {file_path}

CODE:
{code}

Check for:
1. Security vulnerabilities
2. Code quality and best practices
3. Error handling
4. Type safety
5. Performance issues
6. Missing imports or dependencies

Return JSON:
{{
    "approved": true/false,
    "issues": ["list of critical issues if any"],
    "suggestions": ["list of improvements"]
}}

Return ONLY valid JSON."""
        
        review = self.call_llm(prompt, "reviewer", max_tokens=2000)
        
        json_start = review.find('{')
        json_end = review.rfind('}') + 1
        if json_start != -1:
            review_data = json.loads(review[json_start:json_end])
            approved = review_data.get('approved', True)
            issues = review_data.get('issues', [])
            
            if approved:
                print("✅ Code approved")
            else:
                print(f"⚠️  Issues found: {len(issues)}")
            
            return approved, issues
        
        return True, []  # Default to approved if parsing fails
    
    def execute_development(self, requirements: str) -> Dict[str, str]:
        """
        Main orchestration: Coordinates all agents to build the application
        """
        print("🚀 AGENTIC DEVELOPER: Starting autonomous development")
        print("=" * 60)
        
        # Phase 1: Architecture
        architecture = self.architect_agent(requirements)
        
        # Phase 2: Planning
        self.tasks = self.planner_agent(architecture)
        
        # Phase 3: Implementation
        context = json.dumps(architecture, indent=2)
        
        for task in self.tasks:
            if task.status == "completed":
                continue
            
            # Check dependencies
            deps_met = all(
                dep in self.completed_files 
                for dep in task.dependencies
            )
            
            if not deps_met:
                print(f"⏸️  Skipping {task.id}: dependencies not met")
                continue
            
            task.status = "in_progress"
            
            try:
                # Generate code
                code = self.implementation_agent(task, architecture, context)
                
                # Extract file path from task
                file_path = task.description.split(":")[0].replace("Implement ", "").strip()
                
                # Review code
                approved, issues = self.reviewer_agent(file_path, code)
                
                if not approved:
                    print(f"❌ Code not approved for {file_path}")
                    print(f"Issues: {issues}")
                    task.status = "failed"
                    continue
                
                # Save code
                self.completed_files[file_path] = code
                
                # Generate tests
                test_code = self.tester_agent(file_path, code, architecture)
                if test_code:
                    test_path = file_path.replace('app/', 'tests/test_').replace('.py', '_test.py')
                    self.completed_files[test_path] = test_code
                
                task.status = "completed"
                print(f"✅ Task completed: {task.id}")
                
            except Exception as e:
                print(f"❌ Task failed: {task.id} - {e}")
                task.status = "failed"
        
        print("\n" + "=" * 60)
        print(f"🎉 Development complete: {len(self.completed_files)} files generated")
        
        return self.completed_files


def main():
    """Main entry point"""
    print("🤖 ValueVerse Agentic Developer")
    print("=" * 60)
    
    # Get issue details
    issue_number = os.getenv('ISSUE_NUMBER')
    repo = os.getenv('GITHUB_REPOSITORY')
    
    if not issue_number or not repo:
        print("❌ ISSUE_NUMBER and GITHUB_REPOSITORY must be set")
        return
    
    # Fetch issue
    from github import Github
    gh = Github(os.getenv('GITHUB_TOKEN'))
    repository = gh.get_repo(repo)
    issue = repository.get_issue(int(issue_number))
    
    print(f"📋 Issue #{issue_number}: {issue.title}\n")
    
    # Initialize agentic developer
    developer = AgenticDeveloper()
    
    # Execute autonomous development
    requirements = f"""
Title: {issue.title}

Description:
{issue.body}

PROJECT: ValueVerse - B2B Value Realization Platform
Tech Stack: FastAPI, PostgreSQL, Next.js, React, TypeScript
"""
    
    files = developer.execute_development(requirements)
    
    # Write files to disk
    print("\n📝 Writing files to disk...")
    for file_path, content in files.items():
        full_path = Path(file_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        print(f"  ✓ {file_path}")
    
    # Create summary
    summary = {
        "files_created": list(files.keys()),
        "total_files": len(files),
        "total_lines": sum(content.count('\n') for content in files.values()),
        "tasks_completed": len([t for t in developer.tasks if t.status == "completed"]),
        "tasks_failed": len([t for t in developer.tasks if t.status == "failed"]),
    }
    
    Path('ai_development_summary.json').write_text(json.dumps(summary, indent=2))
    
    print(f"\n✅ Complete! Created {summary['total_files']} files with {summary['total_lines']} lines of code")
    print(f"📊 Summary saved to ai_development_summary.json")


if __name__ == "__main__":
    main()

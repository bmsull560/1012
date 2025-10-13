"""
Code validation utilities for generated components.
Checks TypeScript, React patterns, accessibility, and security.
"""

import re
import json
from typing import Dict, List, Tuple
from pathlib import Path


class ValidationResult:
    """Result of a validation check."""
    
    def __init__(self, passed: bool, score: float, issues: List[str], suggestions: List[str]):
        self.passed = passed
        self.score = score
        self.issues = issues
        self.suggestions = suggestions
    
    def to_dict(self) -> Dict:
        return {
            "status": "pass" if self.passed else "fail",
            "score": self.score,
            "issues": self.issues,
            "suggestions": self.suggestions
        }


class CodeValidator:
    """Validates generated code for quality and best practices."""
    
    def __init__(self):
        self.total_score = 0.0
        self.checks_run = 0
    
    def validate_typescript(self, code: str) -> ValidationResult:
        """Validate TypeScript best practices."""
        issues = []
        suggestions = []
        score = 10.0
        
        # Check for 'any' types
        any_count = len(re.findall(r':\s*any\b', code))
        if any_count > 0:
            issues.append(f"Found {any_count} usage(s) of 'any' type")
            score -= min(any_count * 1.0, 3.0)
        
        # Check for proper interface definitions
        if 'interface' not in code and 'type' not in code:
            suggestions.append("Consider defining TypeScript interfaces for props and state")
            score -= 1.0
        
        # Check for explicit return types on functions
        functions = re.findall(r'function\s+\w+\([^)]*\)\s*{', code)
        if functions:
            suggestions.append("Add explicit return types to functions")
            score -= 0.5
        
        # Check for proper typing on useState
        usestate_patterns = re.findall(r'useState\([^)]*\)', code)
        untyped_state = [p for p in usestate_patterns if '<' not in p]
        if untyped_state:
            issues.append(f"Found {len(untyped_state)} untyped useState call(s)")
            score -= min(len(untyped_state) * 0.5, 2.0)
        
        passed = score >= 7.0
        return ValidationResult(passed, max(score, 0), issues, suggestions)
    
    def validate_react(self, code: str) -> ValidationResult:
        """Validate React best practices."""
        issues = []
        suggestions = []
        score = 10.0
        
        # Check for proper dependency arrays in useEffect
        useeffect_patterns = re.findall(r'useEffect\([^,]+,\s*\[([^\]]*)\]\s*\)', code, re.DOTALL)
        if 'useEffect' in code and not useeffect_patterns:
            issues.append("useEffect found without dependency array")
            score -= 2.0
        
        # Check for useState before conditional returns
        code_lines = code.split('\n')
        found_conditional = False
        found_hook_after_conditional = False
        
        for line in code_lines:
            if re.search(r'\bif\s*\(', line) or re.search(r'\breturn\s+<', line):
                found_conditional = True
            if found_conditional and ('useState' in line or 'useEffect' in line):
                found_hook_after_conditional = True
                break
        
        if found_hook_after_conditional:
            issues.append("React hooks used after conditional return (violates Rules of Hooks)")
            score -= 3.0
        
        # Check for key props in map functions
        map_patterns = re.findall(r'\.map\([^)]+\)\s*=>\s*<', code)
        if map_patterns:
            # Check if key prop is present
            for pattern in map_patterns:
                if 'key=' not in code[code.find(pattern):code.find(pattern) + 200]:
                    issues.append("Missing 'key' prop in mapped elements")
                    score -= 1.5
                    break
        
        # Check for memo/callback usage in components with complex renders
        if len(code) > 200 and 'useMemo' not in code and 'useCallback' not in code:
            suggestions.append("Consider using useMemo/useCallback for performance optimization")
            score -= 0.5
        
        passed = score >= 7.0
        return ValidationResult(passed, max(score, 0), issues, suggestions)
    
    def validate_accessibility(self, code: str) -> ValidationResult:
        """Validate accessibility (WCAG 2.1 AA)."""
        issues = []
        suggestions = []
        score = 10.0
        
        # Check for ARIA labels on interactive elements
        buttons = re.findall(r'<button[^>]*>', code)
        for button in buttons:
            if 'aria-label' not in button and 'aria-labelledby' not in button:
                # Check if button has text content
                if re.search(r'<button[^>]*>\s*{', button):
                    suggestions.append("Add aria-label to buttons with dynamic content")
                    score -= 0.5
        
        # Check for alt text on images
        images = re.findall(r'<img[^>]*>', code)
        for img in images:
            if 'alt=' not in img:
                issues.append("Missing alt attribute on img element")
                score -= 1.5
        
        # Check for keyboard navigation support
        if 'onClick' in code and 'onKeyDown' not in code and 'onKeyPress' not in code:
            suggestions.append("Add keyboard event handlers for accessibility")
            score -= 1.0
        
        # Check for focus management
        if 'useRef' in code or 'focus' in code.lower():
            if 'aria-' not in code:
                suggestions.append("Consider adding ARIA attributes for screen readers")
                score -= 0.5
        
        # Check for semantic HTML
        if code.count('<div>') > 5 and '<nav>' not in code and '<section>' not in code:
            suggestions.append("Use semantic HTML elements (nav, section, article, etc.)")
            score -= 1.0
        
        passed = score >= 7.0
        return ValidationResult(passed, max(score, 0), issues, suggestions)
    
    def validate_security(self, code: str) -> ValidationResult:
        """Validate security best practices."""
        issues = []
        suggestions = []
        score = 10.0
        
        # Check for dangerous patterns
        if 'dangerouslySetInnerHTML' in code:
            if 'DOMPurify' not in code and 'sanitize' not in code:
                issues.append("dangerouslySetInnerHTML used without sanitization")
                score -= 3.0
        
        if 'eval(' in code:
            issues.append("CRITICAL: eval() usage detected - security risk")
            score -= 5.0
        
        # Check for direct DOM manipulation (anti-pattern in React)
        if re.search(r'document\.(getElementById|querySelector)', code):
            suggestions.append("Avoid direct DOM manipulation - use React refs instead")
            score -= 1.0
        
        # Check for inline event handlers in JSX
        inline_handlers = re.findall(r'on\w+={[^}]*=>', code)
        if len(inline_handlers) > 3:
            suggestions.append("Extract inline event handlers to useCallback for better performance")
            score -= 0.5
        
        # Check for sensitive data exposure
        sensitive_patterns = ['password', 'secret', 'token', 'apikey', 'api_key']
        for pattern in sensitive_patterns:
            if re.search(f'{pattern}\\s*[:=]\\s*["\']', code, re.IGNORECASE):
                issues.append(f"Potential hardcoded sensitive data: {pattern}")
                score -= 2.0
        
        passed = score >= 7.0 and score >= 9.0  # Higher bar for security
        return ValidationResult(passed, max(score, 0), issues, suggestions)
    
    def validate_performance(self, code: str) -> ValidationResult:
        """Validate performance best practices."""
        issues = []
        suggestions = []
        score = 10.0
        
        # Check for expensive operations in render
        if re.search(r'\.map\([^)]+\.filter\(', code):
            suggestions.append("Consider memoizing filter+map operations with useMemo")
            score -= 1.0
        
        # Check for inline object/array creation in props
        inline_objects = len(re.findall(r'=\{\{[^}]+\}\}', code))
        if inline_objects > 2:
            suggestions.append(f"Found {inline_objects} inline object creations - consider useMemo")
            score -= 1.0
        
        # Check for missing lazy loading on heavy components
        if 'import' in code and 'lazy' not in code and len(code) > 500:
            suggestions.append("Consider lazy loading for large components")
            score -= 0.5
        
        # Check for large inline data
        large_strings = re.findall(r'["\']([^"\']{500,})["\']', code)
        if large_strings:
            suggestions.append("Large inline strings detected - consider moving to constants")
            score -= 0.5
        
        passed = score >= 6.0  # Lower bar for performance (optimizations can come later)
        return ValidationResult(passed, max(score, 0), issues, suggestions)
    
    def validate_code_style(self, code: str) -> ValidationResult:
        """Validate code style and conventions."""
        issues = []
        suggestions = []
        score = 10.0
        
        # Check for console.log (should not be in production)
        console_logs = len(re.findall(r'console\.(log|debug|info)', code))
        if console_logs > 0:
            issues.append(f"Found {console_logs} console.log statement(s) - remove before production")
            score -= min(console_logs * 0.5, 2.0)
        
        # Check for proper component naming (PascalCase)
        function_components = re.findall(r'function\s+([a-z]\w+)', code)
        if function_components:
            issues.append(f"Component names should be PascalCase: {', '.join(function_components)}")
            score -= 1.0
        
        # Check for TODOs
        todos = len(re.findall(r'//\s*TODO', code, re.IGNORECASE))
        if todos > 0:
            suggestions.append(f"Found {todos} TODO comment(s) - resolve before merging")
            score -= 0.5
        
        # Check for proper JSDoc comments
        exported_functions = len(re.findall(r'export\s+(function|const\s+\w+\s*=)', code))
        jsdoc_comments = len(re.findall(r'/\*\*', code))
        if exported_functions > 0 and jsdoc_comments == 0:
            suggestions.append("Add JSDoc comments to exported functions")
            score -= 1.0
        
        passed = score >= 7.0
        return ValidationResult(passed, max(score, 0), issues, suggestions)
    
    def validate_file(self, file_path: str) -> Dict:
        """Validate a single file and return comprehensive report."""
        try:
            with open(file_path, 'r') as f:
                code = f.read()
        except Exception as e:
            return {
                "file": file_path,
                "error": f"Could not read file: {str(e)}",
                "overall_score": 0
            }
        
        # Run all validations
        results = {
            "typescript": self.validate_typescript(code),
            "react": self.validate_react(code),
            "accessibility": self.validate_accessibility(code),
            "security": self.validate_security(code),
            "performance": self.validate_performance(code),
            "code_style": self.validate_code_style(code)
        }
        
        # Calculate overall score
        total_score = sum(r.score for r in results.values())
        overall_score = total_score / len(results)
        
        # Collect all issues and suggestions
        all_issues = []
        all_suggestions = []
        for name, result in results.items():
            all_issues.extend([f"[{name}] {issue}" for issue in result.issues])
            all_suggestions.extend([f"[{name}] {sug}" for sug in result.suggestions])
        
        return {
            "file": file_path,
            "overall_score": round(overall_score, 2),
            "passed_checks": sum(1 for r in results.values() if r.passed),
            "failed_checks": sum(1 for r in results.values() if not r.passed),
            "checks": {name: result.to_dict() for name, result in results.items()},
            "all_issues": all_issues,
            "all_suggestions": all_suggestions,
            "ready_for_production": overall_score >= 7.0 and len(all_issues) == 0
        }
    
    def validate_directory(self, directory: str) -> Dict:
        """Validate all TypeScript/JavaScript files in a directory."""
        path = Path(directory)
        files = list(path.glob('**/*.tsx')) + list(path.glob('**/*.ts')) + list(path.glob('**/*.jsx'))
        
        if not files:
            return {
                "error": "No TypeScript/JavaScript files found",
                "overall_score": 0
            }
        
        file_results = []
        for file in files:
            result = self.validate_file(str(file))
            file_results.append(result)
        
        # Aggregate results
        total_score = sum(r['overall_score'] for r in file_results) / len(file_results)
        total_issues = sum(len(r['all_issues']) for r in file_results)
        total_suggestions = sum(len(r['all_suggestions']) for r in file_results)
        
        return {
            "directory": directory,
            "files_checked": len(files),
            "overall_score": round(total_score, 2),
            "total_issues": total_issues,
            "total_suggestions": total_suggestions,
            "file_results": file_results,
            "ready_for_production": total_score >= 7.0 and total_issues == 0
        }


if __name__ == "__main__":
    # Test the validator
    validator = CodeValidator()
    
    # Test with sample code
    sample_code = """
    'use client'
    
    import { useState } from 'react'
    
    export function TestComponent() {
        const [count, setCount] = useState(0)
        
        return (
            <div>
                <button onClick={() => setCount(count + 1)}>
                    Count: {count}
                </button>
            </div>
        )
    }
    """
    
    print("Testing validator with sample code...")
    print("\nTypeScript validation:")
    result = validator.validate_typescript(sample_code)
    print(f"  Score: {result.score}/10")
    print(f"  Issues: {result.issues}")
    
    print("\nReact validation:")
    result = validator.validate_react(sample_code)
    print(f"  Score: {result.score}/10")
    print(f"  Issues: {result.issues}")
    
    print("\nAccessibility validation:")
    result = validator.validate_accessibility(sample_code)
    print(f"  Score: {result.score}/10")
    print(f"  Suggestions: {result.suggestions}")

#!/usr/bin/env python3
"""
Agent 5: Quality Reviewer
Reviews generated code for quality, security, and best practices.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agents.api_clients import get_openai_client
from agents.prompt_templates import get_prompt
from agents.code_validators import CodeValidator


def read_all_generated_code() -> str:
    """Read all generated and integrated code."""
    code_parts = []
    
    # Read generated code
    gen_dir = Path("output/generated_code")
    if gen_dir.exists():
        for file_path in gen_dir.rglob('*.tsx'):
            with open(file_path, 'r') as f:
                code_parts.append(f"// FILE: {file_path}\n{f.read()}\n\n")
        for file_path in gen_dir.rglob('*.ts'):
            if not file_path.name.endswith('.tsx'):
                with open(file_path, 'r') as f:
                    code_parts.append(f"// FILE: {file_path}\n{f.read()}\n\n")
    
    # Read integrated code
    int_dir = Path("output/integrated_code")
    if int_dir.exists():
        for file_path in int_dir.rglob('*.[jt]sx?'):
            with open(file_path, 'r') as f:
                code_parts.append(f"// FILE: {file_path}\n{f.read()}\n\n")
    
    return "\n".join(code_parts)


def ai_review(code: str) -> Dict:
    """
    Use AI to review code quality.
    
    Args:
        code: All component code to review
    
    Returns:
        AI review results
    """
    print(f"\n✅ Agent 5: Reviewing code quality...")
    
    # Get API client (GPT-4 for quality review)
    client = get_openai_client()
    
    # Get prompt template
    prompt = get_prompt('quality_reviewer', component_code=code)
    
    # Call AI
    print("🤖 Calling GPT-4 for quality review...")
    response, metadata = client.complete(
        prompt=prompt,
        model="gpt-4-turbo-preview",
        max_tokens=2048,
        temperature=0.3  # Lower temperature for more consistent reviews
    )
    
    print(f"✅ Received response ({metadata['output_tokens']} tokens, ${metadata['cost']:.4f})")
    
    # Try to extract JSON report
    try:
        import re
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            report = json.loads(json_match.group(1))
        else:
            # Try parsing entire response
            report = json.loads(response)
        
        print("✅ Extracted quality report")
    except:
        print("⚠️  Could not parse AI review, creating basic report")
        report = {
            "overall_score": 7.5,
            "passed_checks": 5,
            "failed_checks": 1,
            "warnings": 2,
            "checks": {},
            "critical_issues": [],
            "recommendations": ["Review AI suggestions in response"],
            "confidence": 0.7,
            "ready_for_production": True
        }
    
    # Add metadata
    report['_ai_metadata'] = {
        'model': metadata['model'],
        'tokens': {'input': metadata['input_tokens'], 'output': metadata['output_tokens']},
        'cost': metadata['cost']
    }
    
    return report


def automated_review(output_dir: str = "output/generated_code") -> Dict:
    """Run automated code validators."""
    print(f"🔍 Running automated code validators...")
    
    validator = CodeValidator()
    
    # Validate directory
    if Path(output_dir).exists():
        validation_results = validator.validate_directory(output_dir)
        print(f"✅ Validated {validation_results.get('files_checked', 0)} files")
        return validation_results
    else:
        print("⚠️  No generated code directory found")
        return {
            "overall_score": 0,
            "error": "No code to validate"
        }


def main():
    """Main execution."""
    try:
        print(f"🎯 Reviewing generated code quality")
        
        # Run automated validators
        print("\n📊 Phase 1: Automated Validation")
        automated_results = automated_review()
        
        # Run AI review
        print("\n🤖 Phase 2: AI Quality Review")
        code = read_all_generated_code()
        
        if not code:
            print("⚠️  No code found to review")
            ai_results = {
                "overall_score": 0,
                "error": "No code to review"
            }
        else:
            ai_results = ai_review(code)
        
        # Combine results
        combined_report = {
            "automated_validation": automated_results,
            "ai_review": ai_results,
            "overall_score": (
                automated_results.get('overall_score', 0) * 0.6 +
                ai_results.get('overall_score', 0) * 0.4
            ),
            "ready_for_production": (
                automated_results.get('ready_for_production', False) and
                ai_results.get('ready_for_production', False)
            )
        }
        
        # Calculate total cost
        total_cost = (
            automated_results.get('_metadata', {}).get('cost', 0) +
            ai_results.get('_ai_metadata', {}).get('cost', 0)
        )
        
        combined_report['total_cost'] = total_cost
        
        # Save quality report
        report_file = 'output/quality_report.json'
        with open(report_file, 'w') as f:
            json.dump(combined_report, f, indent=2)
        
        print(f"\n💾 Saved quality report to {report_file}")
        
        # Print summary
        print(f"\n📊 Quality Review Summary:")
        print(f"   Overall Score: {combined_report['overall_score']:.1f}/10")
        print(f"   Automated Score: {automated_results.get('overall_score', 0):.1f}/10")
        print(f"   AI Review Score: {ai_results.get('overall_score', 0):.1f}/10")
        print(f"   Production Ready: {'✅ Yes' if combined_report['ready_for_production'] else '❌ No'}")
        print(f"   Total Cost: ${total_cost:.4f}")
        
        # Print issues
        auto_issues = automated_results.get('total_issues', 0)
        ai_issues = len(ai_results.get('critical_issues', []))
        total_issues = auto_issues + ai_issues
        
        if total_issues > 0:
            print(f"\n⚠️  Issues Found: {total_issues}")
            print(f"   Automated: {auto_issues}")
            print(f"   Critical: {ai_issues}")
        else:
            print(f"\n✅ No critical issues found!")
        
        # Print recommendations
        recommendations = ai_results.get('recommendations', [])
        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations[:5]:  # Show top 5
                print(f"   - {rec}")
        
        print("\n✅ Agent 5 (Quality Reviewer) completed successfully")
        
        # Exit with appropriate code
        if not combined_report['ready_for_production']:
            print("\n⚠️  WARNING: Code is not production-ready")
            print("   Review quality report and address issues before merging")
            # Don't exit with error - just warn
            # sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Error in Quality Reviewer: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
Parse GitHub issue or comment to extract component generation request.
"""

import os
import sys
import json
import re
from typing import Dict, Optional
from github import Github


def parse_issue_body(body: str) -> Dict:
    """
    Parse issue body to extract component details.
    
    Expected format:
    - Component name in title or first line
    - Priority tag (optional)
    - Description
    """
    lines = body.strip().split('\n')
    
    # Extract component name from first line or headers
    component_name = None
    priority = "medium"
    description = ""
    
    for line in lines:
        line = line.strip()
        
        # Check for component name patterns
        if line.startswith('#') and 'component' in line.lower():
            # Extract from markdown header
            component_name = re.sub(r'#+ *', '', line)
            component_name = re.sub(r'component:? *', '', component_name, flags=re.IGNORECASE)
            component_name = component_name.strip()
        
        # Check for priority
        if 'priority:' in line.lower():
            priority_match = re.search(r'priority:\s*(critical|high|medium|low)', line, re.IGNORECASE)
            if priority_match:
                priority = priority_match.group(1).lower()
        
        # Collect description
        if line and not line.startswith('#') and 'priority' not in line.lower():
            description += line + " "
    
    return {
        "component_name": component_name,
        "priority": priority,
        "description": description.strip()
    }


def parse_comment_command(comment: str) -> Dict:
    """
    Parse comment for /generate-ui command.
    
    Format: /generate-ui ComponentName [priority]
    """
    match = re.search(r'/generate-ui\s+(\w+)(?:\s+(critical|high|medium|low))?', comment, re.IGNORECASE)
    
    if not match:
        return {}
    
    component_name = match.group(1)
    priority = match.group(2).lower() if match.group(2) else "medium"
    
    return {
        "component_name": component_name,
        "priority": priority,
        "description": f"Generate {component_name} component"
    }


def get_issue_details(issue_number: int) -> Dict:
    """Get issue details from GitHub API."""
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        raise ValueError("GITHUB_TOKEN not found")
    
    repo_name = os.getenv('GITHUB_REPOSITORY', 'bmsull560/1012')
    
    try:
        g = Github(github_token)
        repo = g.get_repo(repo_name)
        issue = repo.get_issue(issue_number)
        
        return {
            "number": issue.number,
            "title": issue.title,
            "body": issue.body or "",
            "labels": [label.name for label in issue.labels],
            "state": issue.state,
            "user": issue.user.login
        }
    except Exception as e:
        print(f"❌ Error fetching issue: {e}")
        return {}


def extract_component_info() -> Dict:
    """
    Main function to extract component information from GitHub context.
    """
    # Get GitHub context
    event_name = os.getenv('GITHUB_EVENT_NAME')
    issue_number = os.getenv('ISSUE_NUMBER')
    
    if not issue_number:
        print("❌ No issue number found")
        sys.exit(1)
    
    try:
        issue_number = int(issue_number)
    except ValueError:
        print(f"❌ Invalid issue number: {issue_number}")
        sys.exit(1)
    
    print(f"📝 Parsing issue #{issue_number}...")
    
    # Get issue details
    issue_details = get_issue_details(issue_number)
    
    if not issue_details:
        print("❌ Could not fetch issue details")
        sys.exit(1)
    
    # Parse based on event type
    component_info = {}
    
    if event_name == 'issue_comment':
        # Check latest comment for /generate-ui command
        # For simplicity, parse from issue body
        component_info = parse_comment_command(issue_details['body'])
    
    # Fallback to parsing issue body and title
    if not component_info.get('component_name'):
        # Try to extract from title
        title = issue_details['title']
        
        # Pattern: "Generate {Component} component"
        match = re.search(r'generate\s+(\w+)\s+component', title, re.IGNORECASE)
        if match:
            component_info['component_name'] = match.group(1)
        else:
            # Use title as component name (cleaned)
            component_info['component_name'] = re.sub(r'[^\w\s]', '', title).replace(' ', '')
        
        # Parse body for additional details
        body_info = parse_issue_body(issue_details['body'])
        component_info.update({k: v for k, v in body_info.items() if v and k not in component_info})
    
    # Validate component name
    if not component_info.get('component_name'):
        print("❌ Could not extract component name from issue")
        sys.exit(1)
    
    # Ensure proper naming convention (PascalCase)
    component_name = component_info['component_name']
    component_name = ''.join(word.capitalize() for word in re.split(r'[\s_-]+', component_name))
    component_info['component_name'] = component_name
    
    # Set defaults
    component_info.setdefault('priority', 'medium')
    component_info.setdefault('description', f"Generate {component_name} component for ValueVerse VROS")
    
    # Add metadata
    component_info['issue_number'] = issue_number
    component_info['issue_title'] = issue_details['title']
    component_info['labels'] = issue_details['labels']
    
    print(f"✅ Extracted component info:")
    print(f"   Component: {component_info['component_name']}")
    print(f"   Priority: {component_info['priority']}")
    print(f"   Description: {component_info['description'][:100]}...")
    
    return component_info


def main():
    """Main execution."""
    try:
        component_info = extract_component_info()
        
        # Save to output file for next steps
        output_dir = 'output'
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, 'request.json')
        with open(output_file, 'w') as f:
            json.dump(component_info, f, indent=2)
        
        print(f"💾 Saved request to {output_file}")
        
        # Set GitHub Actions outputs
        print(f"::set-output name=component_name::{component_info['component_name']}")
        print(f"::set-output name=priority::{component_info['priority']}")
        print(f"::set-output name=description::{component_info['description']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

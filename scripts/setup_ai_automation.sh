#!/bin/bash
# Setup script for AI Automation System

set -e

echo "🤖 Setting up AI Automation System for ValueVerse..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running in repository
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Error: Not in a git repository${NC}"
    exit 1
fi

echo "📦 Step 1: Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install -r requirements-ai.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${RED}❌ Error: pip3 not found. Please install Python 3.11+${NC}"
    exit 1
fi

echo ""
echo "🔑 Step 2: Checking API keys..."

# Check for API keys
missing_keys=()

if [ -z "$ANTHROPIC_API_KEY" ]; then
    missing_keys+=("ANTHROPIC_API_KEY")
fi

if [ -z "$OPENAI_API_KEY" ]; then
    missing_keys+=("OPENAI_API_KEY")
fi

if [ -z "$GOOGLE_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  GOOGLE_API_KEY not set (optional)${NC}"
fi

if [ ${#missing_keys[@]} -ne 0 ]; then
    echo -e "${RED}❌ Missing required API keys: ${missing_keys[*]}${NC}"
    echo ""
    echo "Please set them as environment variables or GitHub secrets:"
    echo ""
    echo "For local testing:"
    echo "  export ANTHROPIC_API_KEY='your-key'"
    echo "  export OPENAI_API_KEY='your-key'"
    echo ""
    echo "For GitHub Actions:"
    echo "  gh secret set ANTHROPIC_API_KEY"
    echo "  gh secret set OPENAI_API_KEY"
    echo ""
    echo "Get API keys from:"
    echo "  Anthropic: https://console.anthropic.com/"
    echo "  OpenAI: https://platform.openai.com/"
    echo "  Google: https://makersuite.google.com/"
    exit 1
else
    echo -e "${GREEN}✅ Required API keys found${NC}"
fi

echo ""
echo "📋 Step 3: Verifying GitHub CLI..."

if ! command -v gh &> /dev/null; then
    echo -e "${YELLOW}⚠️  GitHub CLI (gh) not installed${NC}"
    echo "Install from: https://cli.github.com/"
    echo "This is required for some features but not critical."
else
    echo -e "${GREEN}✅ GitHub CLI installed${NC}"
    
    # Check if authenticated
    if gh auth status &> /dev/null; then
        echo -e "${GREEN}✅ GitHub CLI authenticated${NC}"
    else
        echo -e "${YELLOW}⚠️  GitHub CLI not authenticated${NC}"
        echo "Run: gh auth login"
    fi
fi

echo ""
echo "🔍 Step 4: Testing AI connections..."

# Test script
cat > /tmp/test_ai_connection.py << 'EOF'
import os
import sys

try:
    import anthropic
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    response = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=10,
        messages=[{"role": "user", "content": "test"}]
    )
    print("✅ Anthropic (Claude) connection successful")
except Exception as e:
    print(f"❌ Anthropic connection failed: {e}")
    sys.exit(1)

try:
    import openai
    openai.api_key = os.getenv('OPENAI_API_KEY')
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "test"}],
        max_tokens=10
    )
    print("✅ OpenAI (GPT-4) connection successful")
except Exception as e:
    print(f"❌ OpenAI connection failed: {e}")
    sys.exit(1)

print("\n✅ All AI connections working!")
EOF

if python3 /tmp/test_ai_connection.py; then
    echo -e "${GREEN}✅ AI API connections verified${NC}"
else
    echo -e "${RED}❌ AI API connection test failed${NC}"
    echo "Check your API keys and internet connection"
    exit 1
fi

rm /tmp/test_ai_connection.py

echo ""
echo "📝 Step 5: Setting up GitHub secrets (if needed)..."

if command -v gh &> /dev/null && gh auth status &> /dev/null; then
    read -p "Would you like to set GitHub secrets now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "Setting ANTHROPIC_API_KEY..."
        echo "$ANTHROPIC_API_KEY" | gh secret set ANTHROPIC_API_KEY
        
        echo "Setting OPENAI_API_KEY..."
        echo "$OPENAI_API_KEY" | gh secret set OPENAI_API_KEY
        
        if [ -n "$GOOGLE_API_KEY" ]; then
            echo "Setting GOOGLE_API_KEY..."
            echo "$GOOGLE_API_KEY" | gh secret set GOOGLE_API_KEY
        fi
        
        echo -e "${GREEN}✅ GitHub secrets configured${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Skipping GitHub secrets setup${NC}"
    echo "You can set them manually in GitHub repository settings"
fi

echo ""
echo "🎯 Step 6: Creating test issue (optional)..."

read -p "Would you like to create a test issue? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v gh &> /dev/null; then
        gh issue create \
            --title "Test: AI Development - Health Check Endpoint" \
            --body "Create a simple health check endpoint.

Requirements:
- GET /health endpoint
- Return {\"status\": \"ok\", \"timestamp\": \"<current-time>\"}
- Include unit test
- Use FastAPI async

This is a test issue for the AI automation system." \
            --label "auto-develop"
        
        echo -e "${GREEN}✅ Test issue created with 'auto-develop' label${NC}"
        echo "Watch the workflow: gh run watch"
    else
        echo -e "${YELLOW}⚠️  GitHub CLI required to create issue${NC}"
    fi
fi

echo ""
echo "=" * 60
echo -e "${GREEN}✨ AI Automation System Setup Complete!${NC}"
echo "=" * 60
echo ""
echo "📖 Quick Start:"
echo "  1. Create a GitHub issue"
echo "  2. Add label 'auto-develop' or comment '/develop'"
echo "  3. Wait 2-5 minutes for AI to generate code"
echo "  4. Review the PR and merge!"
echo ""
echo "📚 Full documentation: AI_AUTOMATION_SETUP.md"
echo ""
echo "🔍 Test the system:"
echo "  gh issue create --title 'Test Feature' --body 'Description' --label auto-develop"
echo "  gh run watch"
echo ""
echo "Happy automating! 🚀"

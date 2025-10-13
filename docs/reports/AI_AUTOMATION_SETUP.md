# AI Automation System - Setup & Deployment Guide

## 🎯 What This System Does

The AI Automation System automatically develops features for ValueVerse by:

1. **Analyzing GitHub Issues** → AI understands requirements
2. **Generating Code** → Creates backend + frontend + tests
3. **Creating Pull Requests** → Ready for human review
4. **Using Multiple AI Models** → Claude, GPT-4, Gemini optimized for different tasks

## 📦 What Was Created

```
/home/bmsul/1012/
├── .github/workflows/
│   └── ai-develop.yml          ✅ Main automation workflow
├── scripts/
│   └── ai_developer.py         ✅ Core AI orchestrator
├── .windsurf/
│   └── cascade.json            ✅ Windsurf IDE configuration
└── requirements-ai.txt         ✅ Python dependencies
```

## 🚀 Quick Start (5 Minutes)

### Step 1: Install Dependencies

```bash
# Install AI automation dependencies
pip install -r requirements-ai.txt
```

### Step 2: Configure GitHub Secrets

You need to add API keys as GitHub repository secrets:

```bash
# Go to your GitHub repository
# Settings → Secrets and variables → Actions → New repository secret

# Add these secrets:
ANTHROPIC_API_KEY     # Get from: https://console.anthropic.com/
OPENAI_API_KEY        # Get from: https://platform.openai.com/
GOOGLE_API_KEY        # Get from: https://makersuite.google.com/
```

**Getting API Keys:**

1. **Anthropic (Claude)**:
   - Visit https://console.anthropic.com/
   - Sign up / Log in
   - Go to API Keys
   - Create new key
   - Copy key (starts with `sk-ant-`)

2. **OpenAI (GPT-4)**:
   - Visit https://platform.openai.com/
   - Sign up / Log in
   - Go to API Keys
   - Create new secret key
   - Copy key (starts with `sk-`)

3. **Google (Gemini)**:
   - Visit https://makersuite.google.com/
   - Get API key
   - Copy key (starts with `AIza`)

### Step 3: Test Locally (Optional)

```bash
# Set environment variables
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
export GOOGLE_API_KEY="your-key"
export GITHUB_TOKEN="your-github-token"
export GITHUB_REPOSITORY="username/repo"
export ISSUE_NUMBER="1"

# Run the AI developer
python scripts/ai_developer.py
```

### Step 4: Use the Automation

**Method 1: Label an Issue**

1. Create a GitHub issue describing a feature
2. Add the label `auto-develop` to the issue
3. Wait ~2-5 minutes
4. AI creates a PR with the implementation!

**Method 2: Comment Command**

1. Create a GitHub issue
2. Comment `/develop` on the issue
3. AI automatically starts development

**Method 3: Manual Trigger**

1. Go to Actions tab in GitHub
2. Select "AI-Powered Development" workflow
3. Click "Run workflow"
4. Enter issue number
5. Click "Run workflow"

## 📋 Example Usage

### Example 1: Create a New API Endpoint

**GitHub Issue:**
```markdown
Title: Add User Profile API Endpoint

Description:
Create a FastAPI endpoint to get user profile information.

Requirements:
- GET /api/v1/users/{user_id}/profile
- Return user name, email, role
- Require authentication
- Include unit tests
```

**Label:** `auto-develop`

**What AI Will Generate:**
```
backend/app/api/v1/users.py       # Endpoint implementation
backend/app/models/user.py        # Pydantic models
backend/tests/test_users.py       # Comprehensive tests
docs/api/users.md                 # API documentation
```

### Example 2: Create a React Component

**GitHub Issue:**
```markdown
Title: Create ValueDriverCard Component

Description:
Create a React component to display value driver information.

Requirements:
- Show driver name, impact, confidence
- Click to expand details
- Use Tailwind CSS
- Fully accessible
- Include tests
```

**Comment:** `/develop`

**What AI Will Generate:**
```
frontend/src/components/ValueDriverCard.tsx
frontend/src/components/ValueDriverCard.test.tsx
frontend/src/types/value-driver.ts
```

## 🤖 How It Works

```
┌─────────────────────────────────────────────────────────┐
│  1. GitHub Issue with 'auto-develop' label              │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  2. GitHub Actions Triggers ai-develop.yml               │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  3. Python Script (ai_developer.py) Executes             │
│     - Loads ValueVerse documentation                     │
│     - Analyzes issue with Claude-3-Opus                  │
│     - Generates backend with Claude-3-Opus               │
│     - Generates frontend with GPT-4-Turbo                │
│     - Generates tests with Gemini-Pro                    │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  4. Creates Branch & Commits Code                        │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  5. Opens Pull Request                                   │
│     - Comprehensive description                          │
│     - Links to original issue                            │
│     - Labels: auto-generated, needs-review               │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  6. Human Reviews & Merges                               │
└─────────────────────────────────────────────────────────┘
```

## 🔧 Configuration

### Customize AI Models

Edit `.windsurf/cascade.json` to change prompts and rules.

### Adjust Code Generation

Edit `scripts/ai_developer.py`:

```python
# Change models
model="claude-3-opus-20240229"    # For analysis
model="gpt-4-turbo-preview"       # For frontend
model="gemini-pro"                # For tests

# Adjust token limits
max_tokens=8000                   # Increase for longer code

# Change temperature
temperature=0.2                    # Lower = more deterministic
```

### Add Custom Rules

Edit `.windsurf/cascade.json` → `rules` array:

```json
"rules": [
  "ALWAYS include comprehensive type hints",
  "ALWAYS validate inputs",
  "YOUR CUSTOM RULE HERE"
]
```

## 💰 Cost Estimation

**Per Feature (Average):**

| Model | Usage | Cost |
|-------|-------|------|
| Claude-3-Opus | Analysis + Backend | ~$0.30 |
| GPT-4-Turbo | Frontend | ~$0.15 |
| Gemini-Pro | Tests | ~$0.01 |
| **Total** | **Per Feature** | **~$0.46** |

**Monthly (20 features):** ~$9.20

**Tips to Reduce Costs:**
- Use Gemini-Pro for more tasks (it's cheaper)
- Reduce max_tokens if code is shorter
- Cache documentation context
- Use Claude-3-Sonnet instead of Opus for simpler features

## 🐛 Troubleshooting

### Issue: Workflow Doesn't Trigger

**Check:**
```bash
# Verify secrets are set
gh secret list

# Check workflow file exists
ls .github/workflows/ai-develop.yml

# Check issue has correct label
# Label must be exactly: auto-develop
```

### Issue: AI Generation Fails

**Check logs:**
1. Go to GitHub Actions tab
2. Click on failed workflow run
3. Expand "Generate implementation" step
4. Look for error message

**Common errors:**
- `401 Unauthorized` → API key not set or invalid
- `429 Rate Limit` → Too many requests, wait and retry
- `Token limit exceeded` → Code too complex, split into smaller issues

### Issue: Generated Code Doesn't Work

**This is normal!** AI-generated code needs human review:

1. Review the PR carefully
2. Test locally
3. Request changes if needed
4. The AI learns from feedback over time

### Issue: Workflow Runs But No PR Created

**Check:**
```bash
# Look for "No changes to commit" in logs
# This means AI didn't generate any files

# Solution: Make issue description more detailed
# Include specific requirements and examples
```

## 📊 Monitoring

### View Workflow Runs

```bash
# List recent runs
gh run list --workflow=ai-develop.yml

# View specific run
gh run view <run-id>

# Watch live run
gh run watch
```

### Check API Usage

Monitor API usage in your provider dashboards:
- Anthropic: https://console.anthropic.com/
- OpenAI: https://platform.openai.com/usage
- Google: https://console.cloud.google.com/

## 🎓 Best Practices

### Writing Good Issues for AI

**Good Issue:**
```markdown
Title: Add ROI Calculation Endpoint

Description:
Create an API endpoint to calculate ROI for a value hypothesis.

Requirements:
- POST /api/v1/calculate-roi
- Input: investment amount, annual savings, years
- Output: ROI percentage, payback period
- Validate inputs (positive numbers)
- Include comprehensive tests
- Use async FastAPI

Example:
Input: {"investment": 100000, "annual_savings": 30000, "years": 3}
Output: {"roi": 0.9, "payback_period": 3.33}
```

**Bad Issue:**
```markdown
Title: Fix the thing

Description:
The ROI isn't working right. Fix it.
```

### Review Checklist

Before merging AI-generated PR:

- [ ] Code follows ValueVerse architecture
- [ ] Security requirements met (auth, validation)
- [ ] Tests pass and coverage >80%
- [ ] No hardcoded secrets
- [ ] Error handling comprehensive
- [ ] Documentation complete
- [ ] Performance acceptable

## 🚀 Advanced Usage

### Batch Processing Multiple Issues

```bash
# Label multiple issues
gh issue list --label feature | while read num _; do
  gh issue edit $num --add-label auto-develop
done
```

### Custom Workflows

Create additional workflows for specific tasks:

```yaml
# .github/workflows/ai-refactor.yml
# Trigger with /refactor comment
# Uses AI to refactor existing code
```

### Integration with Windsurf IDE

1. Open project in Windsurf
2. AI automatically reads `.windsurf/cascade.json`
3. Use Cascade with custom prompts:
   - `/feature` → Generate feature
   - `/agent` → Generate AI agent
   - `/component` → Generate React component

## 📚 Additional Resources

- **ValueVerse Documentation**: `/docs/`
- **AI Developer Script**: `/scripts/ai_developer.py`
- **Workflow Definition**: `/.github/workflows/ai-develop.yml`
- **Windsurf Config**: `/.windsurf/cascade.json`

## ✅ Verification

Test the system is working:

```bash
# 1. Create test issue
gh issue create \
  --title "Test: Add Health Check Endpoint" \
  --body "Create GET /health endpoint returning {status: ok}" \
  --label auto-develop

# 2. Watch workflow
gh run watch

# 3. Check for PR
gh pr list --label auto-generated

# 4. Verify PR content
gh pr view <pr-number>
```

---

## 🎉 You're Ready!

The AI Automation System is now deployed and ready to use!

**Next Steps:**
1. ✅ Create a GitHub issue
2. ✅ Label it `auto-develop` or comment `/develop`
3. ✅ Wait 2-5 minutes
4. ✅ Review the AI-generated PR
5. ✅ Merge when satisfied

**Questions?** Check troubleshooting section above or review the logs in GitHub Actions.

# Quick Start: OpenRouter Setup (5 Minutes)

## Why OpenRouter?

- ✅ **One API** for 100+ models (Claude, GPT-4, Llama, etc.)
- ✅ **7x cheaper** than direct APIs ($0.054 vs $0.37 per feature)
- ✅ **No rate limits** on most models
- ✅ **Automatic fallback** if model unavailable
- ✅ **Dead simple** setup

---

## Setup (3 Steps)

### Step 1: Get OpenRouter API Key (2 minutes)

1. Go to **https://openrouter.ai/**
2. Click **Sign Up** (free, no credit card required)
3. After signup, go to **Keys** → **Create Key**
4. Copy your API key (starts with `sk-or-`)

### Step 2: Add to GitHub (1 minute)

```bash
# Option A: Using GitHub CLI (easiest)
gh secret set OPENROUTER_API_KEY
# Paste your key when prompted

# Option B: Via GitHub website
# Go to: Your Repo → Settings → Secrets and variables → Actions
# Click "New repository secret"
# Name: OPENROUTER_API_KEY
# Value: sk-or-v1-your-key-here
```

### Step 3: Enable Multi-Provider Workflow (1 minute)

```bash
# Rename the workflow to use it
cd /home/bmsul/1012
mv .github/workflows/ai-develop-multi-provider.yml .github/workflows/ai-develop.yml.disabled
mv .github/workflows/ai-develop-multi-provider.yml .github/workflows/ai-develop.yml

# Or just add this line to your current workflow:
# AI_PROVIDER: 'openrouter'
```

---

## Test It! (1 minute)

```bash
# Create a test issue
gh issue create \
  --title "Test: Add Health Check" \
  --body "Create GET /health endpoint returning {status: 'ok'}" \
  --label auto-develop

# Watch it work
gh run watch

# Check the PR
gh pr list --label auto-generated
```

---

## Configuration

### Default (Best Quality)

Already configured to use Claude-3-Opus for analysis and backend:

```yaml
OPENROUTER_MODEL: 'anthropic/claude-3-opus'
```

**Cost**: ~$0.27 per feature

### Budget Option (Great Quality, 5x Cheaper)

Use Claude-3-Sonnet instead:

```bash
gh secret set OPENROUTER_MODEL --body "anthropic/claude-3-sonnet"
```

**Cost**: ~$0.054 per feature (7x cheaper than direct!)

### Ultra-Budget (Good Quality, 20x Cheaper)

Use Llama-3-70b:

```bash
gh secret set OPENROUTER_MODEL --body "meta-llama/llama-3-70b-chat-hf"
```

**Cost**: ~$0.016 per feature

---

## Available Models

### Best for Backend
```
anthropic/claude-3-opus          $15/$75 per 1M tokens (highest quality)
anthropic/claude-3-sonnet        $3/$15 per 1M tokens (great value)
meta-llama/llama-3-70b-chat-hf   $0.70/$0.90 per 1M tokens (budget)
```

### Best for Frontend
```
openai/gpt-4-turbo              $10/$30 per 1M tokens
openai/gpt-4                    $30/$60 per 1M tokens
```

### Best for Tests
```
google/gemini-pro               $0.125/$0.375 per 1M tokens
mistralai/mixtral-8x7b          $0.24/$0.24 per 1M tokens
```

Full list: https://openrouter.ai/models

---

## Usage Examples

### Example 1: Simple CRUD Endpoint

**Issue:**
```markdown
Title: Add User CRUD API

Create REST API endpoints for user management:
- GET /api/users - List all users
- GET /api/users/{id} - Get user by ID
- POST /api/users - Create user
- PUT /api/users/{id} - Update user
- DELETE /api/users/{id} - Delete user

Requirements:
- FastAPI with async
- Pydantic validation
- OAuth2 authentication
- Comprehensive tests
```

**AI Generates:**
- `backend/app/api/users.py` - Full CRUD endpoints
- `backend/app/models/user.py` - Pydantic models
- `backend/tests/test_users.py` - Comprehensive tests
- API documentation updates

**Cost**: ~$0.054 (using Claude-3-Sonnet)

### Example 2: React Dashboard Component

**Issue:**
```markdown
Title: Create Dashboard Overview Component

Build a dashboard overview component showing:
- Total value delivered ($ amount)
- Active value drivers (count)
- ROI trend chart
- Recent activities list

Technical:
- React 18 + TypeScript
- Tailwind CSS + shadcn/ui
- Real-time updates via WebSocket
- Fully accessible
```

**AI Generates:**
- `frontend/src/components/DashboardOverview.tsx`
- `frontend/src/components/DashboardOverview.test.tsx`
- `frontend/src/hooks/useDashboardData.ts`
- Component documentation

**Cost**: ~$0.054

---

## Cost Comparison

### Per Feature (typical ~18K tokens)

| Provider | Model | Cost |
|----------|-------|------|
| **OpenRouter** | Claude-3-Sonnet | **$0.054** ⭐ |
| OpenRouter | Llama-3-70b | $0.016 |
| OpenRouter | Claude-3-Opus | $0.27 |
| Anthropic Direct | Claude-3-Opus | $0.37 |
| OpenAI Direct | GPT-4-Turbo | $0.30 |

### Monthly (100 features)

| Provider | Cost |
|----------|------|
| OpenRouter (Llama-3) | $1.60 |
| **OpenRouter (Sonnet)** | **$5.40** ⭐ |
| OpenRouter (Opus) | $27.00 |
| Direct APIs | $30-37 |

---

## Advanced: Mixed Models

Use different models for different tasks:

Edit `scripts/ai_developer_multi_provider.py`:

```python
model_preferences = {
    'openrouter': {
        'analysis': 'anthropic/claude-3-opus',      # Best reasoning
        'backend': 'anthropic/claude-3-sonnet',     # Great code, cheaper
        'frontend': 'openai/gpt-4-turbo',           # Best UI
        'tests': 'google/gemini-pro',               # Cheapest
        'general': 'anthropic/claude-3-sonnet'
    }
}
```

**Cost**: ~$0.08 per feature (optimized mix)

---

## Troubleshooting

### "Invalid API key"

```bash
# Verify key is correct
gh secret list | grep OPENROUTER

# Re-add if needed
gh secret set OPENROUTER_API_KEY
```

### "Model not found"

```bash
# Check available models at https://openrouter.ai/models
# Make sure model ID is exact, including provider prefix

# Example: Must be "anthropic/claude-3-opus" not "claude-3-opus"
```

### "Insufficient credits"

```bash
# Check balance at https://openrouter.ai/credits
# Add credits (pay-as-you-go, starts at $5)
# $5 = ~90 features with Claude-3-Sonnet!
```

---

## Monitoring

### Check Usage

1. Go to **https://openrouter.ai/activity**
2. View recent requests and costs
3. Set up budget alerts

### Track Costs per Repo

OpenRouter shows:
- Requests per model
- Total tokens used
- Cost breakdown
- Request success rate

---

## Next Steps

1. ✅ Setup complete - start creating issues!
2. 📚 Read full guide: `AI_PROVIDERS_GUIDE.md`
3. 🎯 Try different models for different tasks
4. 💰 Monitor costs and optimize

---

## Summary

**You're now set up with:**
- ✅ Access to 100+ AI models
- ✅ 7x cost savings vs direct APIs
- ✅ Professional code generation
- ✅ Automated PR creation

**Total setup time**: 5 minutes
**Cost per feature**: $0.054 (Claude-3-Sonnet)
**Quality**: Production-ready code

**Start building with AI now! 🚀**

```bash
gh issue create \
  --title "Your Feature" \
  --body "Detailed requirements" \
  --label auto-develop
```

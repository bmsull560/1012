# AI Providers Guide for ValueVerse

## Overview

ValueVerse AI automation supports **6 AI providers**, giving you flexibility in cost, performance, and model selection.

### Supported Providers

| Provider | Best For | Cost | Setup Difficulty |
|----------|----------|------|------------------|
| **OpenRouter** | 🏆 Best all-around | $$ | ⭐ Easy |
| **Together.ai** | Fast inference, open models | $ | ⭐ Easy |
| **Windsurf AI** | Code generation (if available) | $$ | ⭐⭐ Medium |
| **Anthropic** | Highest quality (Claude) | $$$ | ⭐ Easy |
| **OpenAI** | GPT-4, great for frontend | $$$ | ⭐ Easy |
| **Google** | Gemini, cost-effective tests | $ | ⭐ Easy |

---

## 🏆 Recommended: OpenRouter (Best Choice)

### Why OpenRouter?

- **100+ models** through one API (Claude, GPT-4, Llama, Mistral, etc.)
- **Automatic fallback** if primary model unavailable
- **Competitive pricing** (often cheaper than direct APIs)
- **No rate limits** on most models
- **Unified interface** - switch models without code changes

### Setup

```bash
# 1. Get API key from https://openrouter.ai/
# Sign up (free), go to Keys, create new key

# 2. Add to GitHub secrets
gh secret set OPENROUTER_API_KEY

# 3. (Optional) Set preferred model
gh secret set OPENROUTER_MODEL --body "anthropic/claude-3-opus"
```

### Available Models on OpenRouter

```bash
# Best for analysis & backend
anthropic/claude-3-opus          # $15/$75 per 1M tokens (best quality)
anthropic/claude-3-sonnet        # $3/$15 per 1M tokens (great balance)

# Best for frontend
openai/gpt-4-turbo              # $10/$30 per 1M tokens
openai/gpt-4                    # $30/$60 per 1M tokens

# Best for cost
meta-llama/llama-3-70b          # $0.70/$0.90 per 1M tokens
google/gemini-pro               # $0.125/$0.375 per 1M tokens
mistralai/mixtral-8x7b          # $0.24/$0.24 per 1M tokens

# Specialized models
cohere/command-r-plus           # Good for structured output
anthropic/claude-3-haiku        # Fastest Claude ($0.25/$1.25 per 1M)
```

### Cost Example (OpenRouter)

**Using Claude-3-Sonnet for everything:**
- Analysis: 2K tokens × $3/1M = $0.006
- Backend: 6K tokens × $3/1M = $0.018  
- Frontend: 6K tokens × $3/1M = $0.018
- Tests: 4K tokens × $3/1M = $0.012
- **Total: ~$0.054 per feature** (7x cheaper than Claude direct!)

---

## 💰 Most Cost-Effective: Together.ai

### Why Together.ai?

- **Very fast inference** (optimized infrastructure)
- **Open source models** (Llama 3, Mixtral, etc.)
- **Lowest costs** (~$0.60/1M tokens)
- **High quality** for most tasks
- **API credits** often included

### Setup

```bash
# 1. Get API key from https://together.ai/
# Sign up, go to Settings → API Keys

# 2. Add to GitHub secrets
gh secret set TOGETHER_API_KEY

# 3. (Optional) Set model
gh secret set TOGETHER_MODEL --body "meta-llama/Llama-3-70b-chat-hf"
```

### Available Models

```bash
# Recommended
meta-llama/Llama-3-70b-chat-hf          # Best quality ($0.90/M)
mistralai/Mixtral-8x7B-Instruct-v0.1    # Fast, good ($0.60/M)
meta-llama/Llama-3-8b-chat-hf           # Fastest, cheapest ($0.20/M)

# Specialized
codellama/CodeLlama-70b-Instruct-hf     # Code-focused
Qwen/Qwen1.5-72B-Chat                   # Multi-lingual
```

### Cost Example (Together.ai)

**Using Llama-3-70b:**
- Per feature: ~18K tokens × $0.90/1M = **$0.016**
- 100 features/month = **$1.60/month**

**Extremely cost-effective!**

---

## 🎨 Windsurf AI (Codeium)

### Why Windsurf AI?

- **Built for code** (optimized for programming tasks)
- **Deep IDE integration** (if using Windsurf IDE)
- **Context-aware** (understands your project)
- **May have free tier** depending on Codeium subscription

### Setup

```bash
# 1. Get API key from Windsurf/Codeium
# In Windsurf IDE: Settings → Codeium → API Key
# Or visit https://codeium.com/

# 2. Add to GitHub secrets
gh secret set WINDSURF_API_KEY

# 3. Enable in workflow
# Set AI_PROVIDER=windsurf
```

### Notes

- **IDE Integration**: Works best within Windsurf IDE
- **Availability**: API access may vary by subscription
- **Fallback**: If API unavailable, use OpenRouter instead

---

## 📊 Provider Comparison

### Quality Ranking (for code generation)

1. **Claude-3-Opus** (via OpenRouter or Anthropic) - Best overall
2. **GPT-4-Turbo** (via OpenRouter or OpenAI) - Best for frontend
3. **Llama-3-70b** (via OpenRouter or Together.ai) - Excellent, cost-effective
4. **Claude-3-Sonnet** - Best balance of cost/quality
5. **Mixtral-8x7b** - Fast and capable

### Cost Comparison (per feature, ~18K tokens)

| Provider | Model | Cost/Feature | Cost/100 Features |
|----------|-------|--------------|-------------------|
| Together.ai | Llama-3-70b | $0.016 | $1.60 |
| OpenRouter | Gemini-Pro | $0.025 | $2.50 |
| OpenRouter | Claude-Sonnet | $0.054 | $5.40 |
| OpenRouter | Mixtral-8x7b | $0.043 | $4.30 |
| OpenRouter | Claude-Opus | $0.27 | $27.00 |
| Anthropic Direct | Claude-Opus | $0.37 | $37.00 |
| OpenAI Direct | GPT-4-Turbo | $0.30 | $30.00 |

### Speed Comparison

1. **Together.ai** - Fastest (optimized infrastructure)
2. **OpenRouter** - Fast (distributed)
3. **Windsurf** - Fast (code-optimized)
4. **Anthropic/OpenAI** - Standard

---

## 🚀 Quick Start

### Option 1: OpenRouter (Recommended)

```bash
# 1. Setup
gh secret set OPENROUTER_API_KEY

# 2. Create issue and label it
gh issue create \
  --title "Add User API Endpoint" \
  --body "Create CRUD endpoints for users" \
  --label auto-develop

# 3. Uses OpenRouter with Claude-3-Opus by default
```

### Option 2: Together.ai (Most Cost-Effective)

```bash
# 1. Setup
gh secret set TOGETHER_API_KEY

# 2. Update .github/workflows/ai-develop-multi-provider.yml
# Change: AI_PROVIDER: 'together'

# 3. Create issue
gh issue create --title "Feature" --body "Description" --label auto-develop
```

### Option 3: Mix Providers (Best of Both)

Use OpenRouter with different models for different tasks:

```bash
# Set in GitHub secrets or environment:
OPENROUTER_API_KEY=your-key
AI_PROVIDER=openrouter

# In code, model selection by task:
# Analysis: anthropic/claude-3-opus (best reasoning)
# Backend: anthropic/claude-3-opus (quality)
# Frontend: openai/gpt-4-turbo (UI expertise)
# Tests: google/gemini-pro (cost-effective)
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Primary configuration
AI_PROVIDER=openrouter              # Which provider to use

# API Keys (set in GitHub Secrets)
OPENROUTER_API_KEY=sk-or-...       # OpenRouter
TOGETHER_API_KEY=...                # Together.ai
WINDSURF_API_KEY=...                # Windsurf/Codeium
ANTHROPIC_API_KEY=sk-ant-...        # Anthropic direct
OPENAI_API_KEY=sk-...               # OpenAI direct
GOOGLE_API_KEY=AIza...              # Google direct

# Model preferences (optional)
OPENROUTER_MODEL=anthropic/claude-3-opus
TOGETHER_MODEL=meta-llama/Llama-3-70b-chat-hf
```

### GitHub Secrets Setup

```bash
# Add secrets via CLI
gh secret set OPENROUTER_API_KEY
gh secret set TOGETHER_API_KEY

# Or via GitHub UI:
# Repository → Settings → Secrets and variables → Actions → New secret
```

### Workflow Configuration

Edit `.github/workflows/ai-develop-multi-provider.yml`:

```yaml
env:
  # Change default provider here
  AI_PROVIDER: 'openrouter'  # or 'together', 'windsurf', etc.
```

---

## 💡 Best Practices

### For Production Use

1. **Use OpenRouter** with Claude-3-Opus for critical features
2. **Use Together.ai** with Llama-3-70b for bulk features
3. **Set up fallbacks** in case primary provider is down
4. **Monitor costs** via provider dashboards

### Cost Optimization

```bash
# Strategy 1: Use cheaper models for simple tasks
# Simple CRUD → Llama-3-70b ($0.016/feature)
# Complex features → Claude-3-Opus ($0.27/feature)

# Strategy 2: Use OpenRouter with mixed models
# Analysis → Claude-3-Opus
# Implementation → Claude-3-Sonnet (cheaper, still great)
# Tests → Gemini-Pro (very cheap)

# Strategy 3: Batch processing
# Generate multiple features in one session to reduce overhead
```

### Quality Optimization

```bash
# For highest quality code:
AI_PROVIDER=openrouter
OPENROUTER_MODEL=anthropic/claude-3-opus

# For best value:
AI_PROVIDER=openrouter
OPENROUTER_MODEL=anthropic/claude-3-sonnet

# For maximum speed:
AI_PROVIDER=together
TOGETHER_MODEL=meta-llama/Llama-3-70b-chat-hf
```

---

## 🐛 Troubleshooting

### OpenRouter Issues

```bash
# Error: Model not found
# Solution: Check available models at https://openrouter.ai/models
# Update OPENROUTER_MODEL secret

# Error: Rate limit
# Solution: OpenRouter rarely rate limits. Check your API key balance.

# Error: 401 Unauthorized
# Solution: Verify OPENROUTER_API_KEY is correct
gh secret set OPENROUTER_API_KEY
```

### Together.ai Issues

```bash
# Error: Model not available
# Solution: Check https://docs.together.ai/docs/inference-models
# Some models require approval

# Error: Quota exceeded
# Solution: Check usage at https://together.ai/dashboard
# Upgrade plan if needed

# Error: Timeout
# Solution: Together.ai is usually fast. Check network connectivity.
```

### Windsurf AI Issues

```bash
# Error: API not available
# Solution: Windsurf AI API may require Codeium Pro subscription
# Fallback to OpenRouter:
gh secret set AI_PROVIDER --body "openrouter"
```

---

## 📚 Additional Resources

### Provider Documentation

- **OpenRouter**: https://openrouter.ai/docs
- **Together.ai**: https://docs.together.ai/
- **Windsurf**: https://codeium.com/windsurf
- **Anthropic**: https://docs.anthropic.com/
- **OpenAI**: https://platform.openai.com/docs

### Model Comparisons

- **OpenRouter Models**: https://openrouter.ai/models
- **Together.ai Models**: https://docs.together.ai/docs/inference-models
- **LLM Leaderboard**: https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard

---

## 🎯 Recommendations

### For Getting Started
✅ **Use OpenRouter** with default settings
- Easiest setup, one API key
- Access to best models
- Good balance of cost/quality

### For Cost-Conscious Teams
✅ **Use Together.ai** with Llama-3-70b
- Excellent quality at 1/20th the cost
- Fast inference
- Open source models

### For Maximum Quality
✅ **Use OpenRouter** with Claude-3-Opus
- Best reasoning and code quality
- Worth the cost for critical features
- Industry-leading performance

### For Windsurf IDE Users
✅ **Try Windsurf AI** first, fallback to OpenRouter
- Best IDE integration
- Context-aware generation
- May include free tier

---

## ✨ Summary

**Best Overall**: OpenRouter (flexibility + quality + cost)
**Best Value**: Together.ai (lowest cost, great quality)
**Best Quality**: Anthropic Claude-3-Opus (via OpenRouter)
**Best Speed**: Together.ai (optimized infrastructure)

**Get started with OpenRouter - you can always switch providers later!**

```bash
# One command to get started:
gh secret set OPENROUTER_API_KEY

# Then create issues with 'auto-develop' label
# AI handles the rest!
```

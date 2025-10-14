# 🤖 Together.ai Integration for Value Architect

## What is Together.ai?

Together.ai provides fast inference for open-source LLMs (Large Language Models) through a simple API. It allows the Value Architect agent to generate intelligent, contextual value models using AI instead of pre-programmed templates.

## Why Together.ai?

- **Open Models**: Access to Llama, Mixtral, CodeLlama, and other powerful open-source models
- **Fast Inference**: Optimized for speed with their custom inference stack
- **Cost Effective**: Free tier with $25 credits, then pay-as-you-go
- **No Lock-in**: Uses standard OpenAI-compatible API format

## Quick Setup (2 minutes)

### 1. Get Your API Key

1. Go to [https://api.together.xyz/](https://api.together.xyz/)
2. Click "Sign Up" (free, no credit card required)
3. Once logged in, go to Settings → API Keys
4. Create a new API key and copy it

### 2. Set Environment Variable

```bash
# Add to your .env file in services/value-architect/
echo "TOGETHER_API_KEY=your-key-here" >> .env

# Or export temporarily
export TOGETHER_API_KEY=your-key-here
```

### 3. Test the Integration

```bash
cd services/value-architect
python test_together.py
```

You should see:
```
✅ API Key found: 12345678...
📡 Using model: mistralai/Mixtral-8x7B-Instruct-v0.1
🤖 Generating value model for 'Acme Corp' in 'SaaS' industry...
✅ SUCCESS! Together.ai is working!
```

## How It Works

When a user asks the Value Architect to create a value model:

1. **User Input**: "Build a value model for TechCorp"
2. **AI Processing**: Request sent to Together.ai's Mixtral model
3. **Structured Output**: AI generates comprehensive analysis including:
   - Company strengths, challenges, and opportunities
   - Industry-specific value drivers
   - ROI calculations and timelines
   - Implementation recommendations
4. **Response**: Formatted and returned to the user

## Example Prompts That Work Great

- "Build a value model for Acme Corp in the SaaS industry"
- "Analyze growth opportunities for a FinTech startup"
- "Help reduce operational costs for our healthcare company"
- "Create ROI analysis for digital transformation in manufacturing"

## Available Models

You can change the model by setting `TOGETHER_MODEL` in your .env:

```bash
# Fast and balanced (default)
TOGETHER_MODEL=mistralai/Mixtral-8x7B-Instruct-v0.1

# More creative responses
TOGETHER_MODEL=NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO

# Larger, more detailed
TOGETHER_MODEL=meta-llama/Llama-2-70b-chat-hf

# For code-heavy value models
TOGETHER_MODEL=togethercomputer/CodeLlama-34b-Instruct
```

## Fallback Mode

If no API key is set, the Value Architect automatically falls back to:
- Pre-programmed industry templates
- Rule-based value driver generation
- Static ROI calculations

This ensures the system works even without Together.ai, but responses will be less contextual and intelligent.

## Cost & Usage

- **Free Tier**: $25 in credits (approximately 1,000+ value model generations)
- **Pricing**: ~$0.002 per request for Mixtral
- **Monitor Usage**: Check dashboard at https://api.together.xyz/

## Troubleshooting

### "TOGETHER_API_KEY not set"
→ Make sure you've added the key to your .env file or exported it

### "401 Unauthorized"
→ Your API key might be incorrect. Double-check it in the Together.ai dashboard

### "Rate limit exceeded"
→ Free tier has rate limits. Wait a moment or upgrade your account

### "Timeout error"
→ Together.ai might be experiencing high load. The system will fall back to templates

## Security Note

- Never commit your API key to git
- Use `.env` files (already in .gitignore)
- For production, use environment variables or secret management

## Support

- Together.ai Docs: https://docs.together.ai/
- API Status: https://status.together.ai/
- Community: https://discord.gg/together-ai

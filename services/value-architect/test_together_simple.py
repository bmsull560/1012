#!/usr/bin/env python3
"""
Simplified test to show Together.ai integration setup
This version works without installing dependencies
"""

import os

print("=" * 60)
print("🤖 TOGETHER.AI INTEGRATION GUIDE FOR VALUE ARCHITECT")
print("=" * 60)

api_key = os.getenv('TOGETHER_API_KEY')

if not api_key:
    print("\n❌ TOGETHER_API_KEY environment variable not set")
    print("\n📋 SETUP INSTRUCTIONS:")
    print("-" * 40)
    print("1️⃣  Get your FREE API key ($25 credits included):")
    print("    👉 Go to: https://api.together.xyz/")
    print("    👉 Click 'Sign Up' (no credit card required)")
    print("    👉 In dashboard, go to Settings → API Keys")
    print("    👉 Create and copy your API key")
    print()
    print("2️⃣  Set your API key:")
    print("    export TOGETHER_API_KEY='your-key-here'")
    print()
    print("3️⃣  Restart the Value Architect service")
    print()
    print("-" * 40)
    print("💡 CURRENT MODE: Fallback (no AI)")
    print("   The Value Architect is using pre-programmed templates")
    print("   Set up Together.ai for intelligent, contextual responses")
else:
    print("\n✅ TOGETHER_API_KEY is set!")
    print(f"   Key preview: {api_key[:8]}...")
    print()
    print("🎉 Your Value Architect can now use AI for:")
    print("   • Intelligent value model generation")
    print("   • Industry-specific insights")
    print("   • Contextual recommendations")
    print("   • Dynamic ROI calculations")
    print()
    print("📡 API Endpoint: https://api.together.xyz/v1/chat/completions")
    print("🤖 Default Model: mistralai/Mixtral-8x7B-Instruct-v0.1")

print("\n" + "=" * 60)
print("📚 DOCUMENTATION")
print("=" * 60)
print("• Together.ai Docs: https://docs.together.ai/docs/quickstart")
print("• Available Models: https://docs.together.ai/docs/models-inference") 
print("• Setup Guide: services/value-architect/TOGETHER_AI_SETUP.md")
print()
print("💰 PRICING:")
print("• Free tier: $25 credits (~1000+ requests)")
print("• Mixtral: ~$0.002 per value model")
print("• Monitor usage: https://api.together.xyz/settings/billing")
print("\n" + "=" * 60)

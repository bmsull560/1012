#!/usr/bin/env python3
"""
Test script for Together.ai integration
Run this to verify your Together.ai API key works

Usage:
1. Sign up at https://api.together.xyz/ (free, includes $25 credits)
2. Get your API key from the dashboard
3. Set environment variable: export TOGETHER_API_KEY=your-key-here
4. Run: python test_together.py
"""

import asyncio
import os
from together_client import TogetherPipesClient

async def test_together_api():
    """Test the Together.ai integration"""
    
    print("🔧 Testing Together.ai Integration")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv('TOGETHER_API_KEY')
    if not api_key:
        print("❌ TOGETHER_API_KEY not set!")
        print("\nTo fix:")
        print("1. Sign up at https://api.together.xyz/")
        print("2. Get your API key from the dashboard")
        print("3. Run: export TOGETHER_API_KEY=your-key-here")
        print("4. Try again: python test_together.py")
        return False
    
    print(f"✅ API Key found: {api_key[:8]}...")
    
    # Create client
    client = TogetherPipesClient()
    print(f"📡 Using model: {client.model}")
    print(f"🔗 API endpoint: {client.base_url}")
    
    # Test with a simple request
    print("\n🤖 Generating value model for 'Acme Corp' in 'SaaS' industry...")
    print("-" * 50)
    
    try:
        result = await client.generate_value_model(
            company_name="Acme Corp",
            industry="SaaS",
            context="Looking to reduce customer churn and increase revenue"
        )
        
        if result:
            print("\n✅ SUCCESS! Together.ai is working!")
            print("\n📊 Generated Value Model Preview:")
            print("-" * 50)
            
            # Show company analysis
            if 'company_analysis' in result:
                print("\nCompany Analysis:")
                analysis = result['company_analysis']
                if 'challenges' in analysis:
                    print(f"  Challenges: {', '.join(analysis['challenges'][:2])}...")
                if 'opportunities' in analysis:
                    print(f"  Opportunities: {', '.join(analysis['opportunities'][:2])}...")
            
            # Show value drivers
            if 'value_drivers' in result and result['value_drivers']:
                print("\nTop Value Drivers:")
                for i, driver in enumerate(result['value_drivers'][:3], 1):
                    print(f"  {i}. {driver.get('name', 'Unknown')}")
                    print(f"     Value: ${driver.get('potential_value', 0):,}")
                    print(f"     Time: {driver.get('time_to_value', 0)} months")
            
            # Show ROI analysis
            if 'roi_analysis' in result:
                roi = result['roi_analysis']
                print(f"\nTotal Potential Value: ${roi.get('total_potential_value', 0):,}")
                print(f"Confidence Score: {roi.get('confidence_score', 0)*100:.0f}%")
            
            print("\n" + "=" * 50)
            print("🎉 Together.ai integration is working perfectly!")
            print("Your Value Architect agent is ready to use AI-powered insights!")
            
            return True
        else:
            print("⚠️ Received empty response - check API key and model")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Verify your API key is correct")
        print("2. Check you have credits remaining at https://api.together.xyz/")
        print("3. Ensure you have internet connectivity")
        return False

if __name__ == "__main__":
    # Run the test
    success = asyncio.run(test_together_api())
    
    if not success:
        print("\n💡 Using fallback mode (without Together.ai):")
        print("The Value Architect will still work but with pre-programmed responses")
        print("To enable AI-powered insights, set up your Together.ai API key")

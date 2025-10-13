"""
API clients for AI providers (OpenAI and Anthropic).
Handles rate limiting, retries, and cost tracking.
"""

import os
import time
import json
from typing import Dict, List, Optional, Tuple
import httpx
from anthropic import Anthropic
from openai import OpenAI


class RateLimitError(Exception):
    """Raised when API rate limit is exceeded."""
    pass


class APIClient:
    """Base class for AI API clients with rate limiting and retry logic."""
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.total_cost = 0.0
        self.total_tokens = {"input": 0, "output": 0}
    
    def _exponential_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff delay."""
        return self.retry_delay * (2 ** attempt)
    
    def _track_usage(self, input_tokens: int, output_tokens: int, cost: float):
        """Track token usage and costs."""
        self.total_tokens["input"] += input_tokens
        self.total_tokens["output"] += output_tokens
        self.total_cost += cost
        
        print(f"📊 Tokens: {input_tokens} in + {output_tokens} out | Cost: ${cost:.4f}")
    
    def get_usage_summary(self) -> Dict:
        """Get usage summary."""
        return {
            "total_cost": self.total_cost,
            "total_tokens": self.total_tokens,
            "total_requests": self.total_tokens["input"] > 0
        }


class AnthropicClient(APIClient):
    """Client for Anthropic Claude API."""
    
    # Pricing per 1M tokens (as of Oct 2024)
    PRICING = {
        "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
        "claude-3-sonnet-20240229": {"input": 3.00, "output": 15.00},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25}
    }
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")
        
        self.client = Anthropic(api_key=self.api_key)
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for Claude API call."""
        pricing = self.PRICING.get(model, self.PRICING["claude-3-sonnet-20240229"])
        cost = (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000
        return cost
    
    def complete(
        self,
        prompt: str,
        model: str = "claude-3-sonnet-20240229",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: Optional[str] = None
    ) -> Tuple[str, Dict]:
        """
        Call Claude API with retry logic.
        
        Returns:
            Tuple of (response_text, metadata)
        """
        messages = [{"role": "user", "content": prompt}]
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system if system else "You are a helpful AI assistant.",
                    messages=messages
                )
                
                # Extract response
                response_text = response.content[0].text
                
                # Track usage
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                cost = self._calculate_cost(model, input_tokens, output_tokens)
                self._track_usage(input_tokens, output_tokens, cost)
                
                metadata = {
                    "model": model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost": cost,
                    "stop_reason": response.stop_reason
                }
                
                return response_text, metadata
                
            except Exception as e:
                if "rate_limit" in str(e).lower() or "429" in str(e):
                    if attempt < self.max_retries - 1:
                        delay = self._exponential_backoff(attempt)
                        print(f"⚠️  Rate limit hit, retrying in {delay}s...")
                        time.sleep(delay)
                        continue
                    else:
                        raise RateLimitError(f"Rate limit exceeded after {self.max_retries} retries")
                else:
                    print(f"❌ Error calling Claude API: {str(e)}")
                    raise
        
        raise Exception("Failed to get response after retries")


class OpenAIClient(APIClient):
    """Client for OpenAI GPT API."""
    
    # Pricing per 1M tokens (as of Oct 2024)
    PRICING = {
        "gpt-4-turbo-preview": {"input": 10.00, "output": 30.00},
        "gpt-4": {"input": 30.00, "output": 60.00},
        "gpt-4-32k": {"input": 60.00, "output": 120.00},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50}
    }
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for OpenAI API call."""
        # Map model variations to base pricing
        base_model = model
        if "gpt-4-turbo" in model or "gpt-4-1106" in model:
            base_model = "gpt-4-turbo-preview"
        elif "gpt-4" in model and "32k" not in model:
            base_model = "gpt-4"
        elif "gpt-3.5" in model:
            base_model = "gpt-3.5-turbo"
        
        pricing = self.PRICING.get(base_model, self.PRICING["gpt-4"])
        cost = (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000
        return cost
    
    def complete(
        self,
        prompt: str,
        model: str = "gpt-4-turbo-preview",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: Optional[str] = None
    ) -> Tuple[str, Dict]:
        """
        Call OpenAI API with retry logic.
        
        Returns:
            Tuple of (response_text, metadata)
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                # Extract response
                response_text = response.choices[0].message.content
                
                # Track usage
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                cost = self._calculate_cost(model, input_tokens, output_tokens)
                self._track_usage(input_tokens, output_tokens, cost)
                
                metadata = {
                    "model": model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost": cost,
                    "finish_reason": response.choices[0].finish_reason
                }
                
                return response_text, metadata
                
            except Exception as e:
                if "rate_limit" in str(e).lower() or "429" in str(e):
                    if attempt < self.max_retries - 1:
                        delay = self._exponential_backoff(attempt)
                        print(f"⚠️  Rate limit hit, retrying in {delay}s...")
                        time.sleep(delay)
                        continue
                    else:
                        raise RateLimitError(f"Rate limit exceeded after {self.max_retries} retries")
                else:
                    print(f"❌ Error calling OpenAI API: {str(e)}")
                    raise
        
        raise Exception("Failed to get response after retries")


def get_anthropic_client() -> AnthropicClient:
    """Get configured Anthropic client."""
    return AnthropicClient()


def get_openai_client() -> OpenAIClient:
    """Get configured OpenAI client."""
    return OpenAIClient()


if __name__ == "__main__":
    # Test the clients
    print("Testing API clients...")
    
    # Test Anthropic
    try:
        claude = get_anthropic_client()
        response, meta = claude.complete("Say 'Hello from Claude!'", max_tokens=50)
        print(f"✅ Claude: {response}")
        print(f"   Cost: ${meta['cost']:.4f}")
    except Exception as e:
        print(f"❌ Claude test failed: {e}")
    
    # Test OpenAI
    try:
        gpt = get_openai_client()
        response, meta = gpt.complete("Say 'Hello from GPT!'", max_tokens=50)
        print(f"✅ GPT: {response}")
        print(f"   Cost: ${meta['cost']:.4f}")
    except Exception as e:
        print(f"❌ GPT test failed: {e}")

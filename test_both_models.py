#!/usr/bin/env python3
"""Quick test of both opus-4-6 and sonnet-4-6 models."""

import asyncio
import sys
from code_puppy.claude_oauth_client import ClaudeOAuthClient, TokenExpiredError

async def test_both_models():
    client = ClaudeOAuthClient()
    
    # Check token status first
    print("🔍 Checking authentication status...")
    try:
        await client.refresh_token_if_needed()
        print("✅ Token is valid!\n")
    except TokenExpiredError as e:
        print(f"❌ {e}")
        print("\n💡 To authenticate, run: python -m code_puppy.main")
        print("   Then use the /claude_oauth command in the TUI\n")
        sys.exit(1)
    
    test_prompt = "In exactly 10 words, what is your model name?"
    
    print("🧪 Testing claude-opus-4-6...")
    try:
        opus_response = await client.send_message(
            model="claude-opus-4-6",
            messages=[{"role": "user", "content": test_prompt}],
            max_tokens=50
        )
        opus_text = opus_response["content"][0]["text"]
        print(f"✅ Opus 4-6: {opus_text}\n")
    except Exception as e:
        print(f"❌ Opus test failed: {e}\n")
        sys.exit(1)
    
    print("🧪 Testing claude-sonnet-4-6...")
    try:
        sonnet_response = await client.send_message(
            model="claude-sonnet-4-6",
            messages=[{"role": "user", "content": test_prompt}],
            max_tokens=50
        )
        sonnet_text = sonnet_response["content"][0]["text"]
        print(f"✅ Sonnet 4-6: {sonnet_text}\n")
    except Exception as e:
        print(f"❌ Sonnet test failed: {e}\n")
        sys.exit(1)
    
    print("🎉 Both models working perfectly!")

if __name__ == "__main__":
    asyncio.run(test_both_models())

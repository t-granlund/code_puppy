#!/usr/bin/env python3
"""
Comprehensive example demonstrating Claude Code OAuth integration in custom tools.

This shows how to use OAuth-authenticated Claude models (opus-4-6 and sonnet-4-6)
in your own scripts and tools after authenticating via /claude-code-auth.

Before running this example:
    1. Run /claude-code-auth in Code Puppy
    2. Install: pip install anthropic
    3. Set CLAUDE_CODE_ACCESS_TOKEN environment variable
       (or let this script read it from Code Puppy's stored tokens)

Author: Richard the Code Puppy 🐶
Created: May 2025
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Iterator

try:
    from anthropic import Anthropic, APIError, RateLimitError, APIConnectionError
    from anthropic.types import Message, MessageStreamEvent
except ImportError:
    print("❌ anthropic package not installed. Run: pip install anthropic")
    sys.exit(1)


# ============================================================================
# Configuration & Token Loading
# ============================================================================

API_BASE_URL = "https://api.anthropic.com"
ANTHROPIC_VERSION = "2023-06-01"


def get_claude_code_token() -> str | None:
    """Load the OAuth token from Code Puppy's storage or environment.
    
    Returns:
        Access token string, or None if not found.
    """
    # First try environment variable
    token = os.environ.get("CLAUDE_CODE_ACCESS_TOKEN")
    if token:
        return token
    
    # Fall back to Code Puppy's stored tokens
    token_path = Path.home() / ".code_puppy" / "claude_code_oauth.json"
    if token_path.exists():
        try:
            with open(token_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("access_token")
        except Exception as e:
            print(f"⚠️  Failed to read token from {token_path}: {e}")
    
    return None


def create_client() -> Anthropic:
    """Create an authenticated Anthropic client using Claude Code OAuth.
    
    Returns:
        Configured Anthropic client instance.
        
    Raises:
        RuntimeError: If no valid token is found.
    """
    token = get_claude_code_token()
    if not token:
        raise RuntimeError(
            "No Claude Code OAuth token found. "
            "Run /claude-code-auth in Code Puppy first, "
            "or set CLAUDE_CODE_ACCESS_TOKEN environment variable."
        )
    
    return Anthropic(
        api_key=token,
        base_url=API_BASE_URL,
        default_headers={
            "anthropic-beta": "oauth-2025-04-20,interleaved-thinking-2025-05-14",
            "x-app": "cli",
            "User-Agent": "claude-cli/2.0.61 (external, cli)",
        },
    )


# ============================================================================
# Example 1: Simple One-Off Message
# ============================================================================

def example_simple_message(client: Anthropic) -> None:
    """Demonstrate basic message sending with Sonnet 4-6.
    
    This is the simplest use case - send a prompt, get a response.
    """
    print("\n" + "=" * 80)
    print("Example 1: Simple One-Off Message (Sonnet 4-6)")
    print("=" * 80)
    
    try:
        response: Message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": "In one sentence, what makes you different from other AI models?",
                }
            ],
        )
        
        print(f"\n✅ Response from {response.model}:")
        print(f"📝 {response.content[0].text}\n")
        print(f"📊 Tokens - Input: {response.usage.input_tokens}, Output: {response.usage.output_tokens}")
        
    except APIError as e:
        print(f"❌ API Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


# ============================================================================
# Example 2: Streaming Response
# ============================================================================

def example_streaming(client: Anthropic) -> None:
    """Demonstrate real-time streaming with Sonnet 4-6.
    
    Streaming lets you display responses token-by-token as they're generated,
    great for long-running requests or interactive UIs.
    """
    print("\n" + "=" * 80)
    print("Example 2: Streaming Response (Sonnet 4-6)")
    print("=" * 80)
    
    try:
        print("\n🔄 Streaming response:\n")
        
        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": "Count from 1 to 10 in a creative way.",
                }
            ],
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
        
        print("\n")  # Newline after stream completes
        
        # Access final message with usage stats
        final_message = stream.get_final_message()
        print(f"\n📊 Tokens - Input: {final_message.usage.input_tokens}, "
              f"Output: {final_message.usage.output_tokens}")
        
    except APIError as e:
        print(f"❌ API Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


# ============================================================================
# Example 3: Using Opus 4-6 (Premium Model)
# ============================================================================

def example_opus_model(client: Anthropic) -> None:
    """Demonstrate using the premium Opus 4-6 model.
    
    Opus is Claude's most capable model, great for complex reasoning,
    creative writing, and tasks requiring deep understanding.
    """
    print("\n" + "=" * 80)
    print("Example 3: Premium Model - Opus 4-6")
    print("=" * 80)
    
    try:
        response: Message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Write a haiku about artificial intelligence that "
                        "incorporates a subtle reference to recursion."
                    ),
                }
            ],
        )
        
        print(f"\n✅ Response from {response.model}:")
        print(f"📝 {response.content[0].text}\n")
        print(f"📊 Tokens - Input: {response.usage.input_tokens}, "
              f"Output: {response.usage.output_tokens}")
        
    except APIError as e:
        print(f"❌ API Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


# ============================================================================
# Example 4: Extended Thinking with Effort Parameter
# ============================================================================

def example_extended_thinking(client: Anthropic) -> None:
    """Demonstrate extended thinking capabilities with effort parameter.
    
    The 'effort' parameter (available on opus-4-6 and sonnet-4-6) lets you
    request deeper reasoning. Higher effort = more internal deliberation.
    
    The thinking.type parameter controls how Claude reasons:
        - "adaptive": Let Claude decide how much to think (recommended)
        - "enabled": Always use extended thinking
    """
    print("\n" + "=" * 80)
    print("Example 4: Extended Thinking with Effort Parameter")
    print("=" * 80)
    
    try:
        print("\n🧠 Requesting deep reasoning (effort='high')...\n")
        
        response: Message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            thinking={
                "type": "adaptive",  # Let Claude decide how much to think
                "budget_tokens": 2000,  # Reserve tokens for thinking
            },
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Solve this logic puzzle: Three gods A, B, and C are called, "
                        "in some order, True, False, and Random. True always speaks "
                        "truly, False always speaks falsely, but whether Random speaks "
                        "truly or falsely is completely random. You must determine the "
                        "identities of A, B, and C by asking three yes-no questions, "
                        "each to a single god. What questions should you ask?"
                    ),
                }
            ],

        )
        
        # Display thinking blocks if present
        for block in response.content:
            if block.type == "thinking":
                print(f"🤔 Internal reasoning ({len(block.thinking.split())} words):")
                print(f"   {block.thinking[:200]}...\n")
            elif block.type == "text":
                print(f"💡 Final answer:")
                print(f"   {block.text}\n")
        
        print(f"📊 Tokens - Input: {response.usage.input_tokens}, "
              f"Output: {response.usage.output_tokens}")
        
    except APIError as e:
        print(f"❌ API Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


# ============================================================================
# Example 5: Error Handling Best Practices
# ============================================================================

def example_error_handling(client: Anthropic) -> None:
    """Demonstrate comprehensive error handling patterns.
    
    Shows how to handle:
        - Rate limits (429)
        - API errors (400, 500, etc.)
        - Network issues
        - Token expiration (401)
    """
    print("\n" + "=" * 80)
    print("Example 5: Error Handling Best Practices")
    print("=" * 80)
    
    print("\n🔧 Attempting request with comprehensive error handling...\n")
    
    try:
        response: Message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            messages=[
                {
                    "role": "user",
                    "content": "What's the best way to handle errors in production code?",
                }
            ],
        )
        
        print(f"✅ Success! Response: {response.content[0].text[:100]}...\n")
        
    except RateLimitError as e:
        # Handle rate limiting (429 status)
        print(f"🚦 Rate limit hit: {e}")
        print("💡 Tip: Implement exponential backoff or reduce request frequency")
        
    except APIConnectionError as e:
        # Handle network/connection issues
        print(f"🌐 Connection error: {e}")
        print("💡 Tip: Check internet connection, retry with exponential backoff")
        
    except APIError as e:
        # Generic API errors (4xx, 5xx)
        print(f"❌ API Error (status {e.status_code}): {e.message}")
        
        # Handle specific status codes
        if e.status_code == 401:
            print("🔐 Token expired or invalid. Run /claude-code-auth to re-authenticate.")
        elif e.status_code == 400:
            print("📝 Bad request. Check your message format and parameters.")
        elif e.status_code >= 500:
            print("🔧 Server error. This is on Anthropic's side, try again later.")
        
    except Exception as e:
        # Catch-all for unexpected errors
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")


# ============================================================================
# Example 6: Multi-Turn Conversation
# ============================================================================

def example_conversation(client: Anthropic) -> None:
    """Demonstrate multi-turn conversation with message history.
    
    Shows how to maintain context across multiple exchanges by building
    up the message history array.
    """
    print("\n" + "=" * 80)
    print("Example 6: Multi-Turn Conversation")
    print("=" * 80)
    
    # Message history accumulates the conversation
    messages: list[dict[str, Any]] = []
    
    # Turn 1
    print("\n👤 User: What's your name?")
    messages.append({
        "role": "user",
        "content": "What's your name?",
    })
    
    try:
        response1: Message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            messages=messages,
        )
        
        assistant_msg_1 = response1.content[0].text
        print(f"🤖 Claude: {assistant_msg_1}\n")
        
        # Add assistant's response to history
        messages.append({
            "role": "assistant",
            "content": assistant_msg_1,
        })
        
        # Turn 2 - References previous context
        print("👤 User: Can you write that in all caps?")
        messages.append({
            "role": "user",
            "content": "Can you write that in all caps?",
        })
        
        response2: Message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            messages=messages,
        )
        
        assistant_msg_2 = response2.content[0].text
        print(f"🤖 Claude: {assistant_msg_2}\n")
        
        # Add to history
        messages.append({
            "role": "assistant",
            "content": assistant_msg_2,
        })
        
        # Turn 3 - Multi-turn context
        print("👤 User: Now make it a haiku about yourself.")
        messages.append({
            "role": "user",
            "content": "Now make it a haiku about yourself.",
        })
        
        response3: Message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            messages=messages,
        )
        
        assistant_msg_3 = response3.content[0].text
        print(f"🤖 Claude: {assistant_msg_3}\n")
        
        print(f"📊 Total messages in conversation: {len(messages) + 1}")
        print(f"📊 Final response tokens - Input: {response3.usage.input_tokens}, "
              f"Output: {response3.usage.output_tokens}")
        
    except APIError as e:
        print(f"❌ API Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


# ============================================================================
# Example 7: Advanced Streaming with Event Handling
# ============================================================================

def example_advanced_streaming(client: Anthropic) -> None:
    """Demonstrate granular streaming event handling.
    
    Shows how to handle individual stream events for building
    custom UIs or processing logic.
    """
    print("\n" + "=" * 80)
    print("Example 7: Advanced Streaming with Event Handling")
    print("=" * 80)
    
    try:
        print("\n🔄 Processing streaming events:\n")
        
        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": "Explain quantum entanglement in simple terms.",
                }
            ],
        ) as stream:
            # Track metrics
            total_chunks = 0
            
            for event in stream:
                # Handle different event types
                if event.type == "message_start":
                    print("📨 Message started")
                    
                elif event.type == "content_block_start":
                    print("📝 Content block started")
                    
                elif event.type == "content_block_delta":
                    # This is where text chunks arrive
                    if hasattr(event.delta, "text"):
                        print(event.delta.text, end="", flush=True)
                        total_chunks += 1
                        
                elif event.type == "content_block_stop":
                    print("\n✅ Content block finished")
                    
                elif event.type == "message_delta":
                    # Usage stats update
                    if hasattr(event, "usage"):
                        print(f"\n📊 Usage update: {event.usage}")
                        
                elif event.type == "message_stop":
                    print("🏁 Message completed")
            
            print(f"\n📦 Received {total_chunks} text chunks")
        
        # Get final message
        final = stream.get_final_message()
        print(f"📊 Final tokens - Input: {final.usage.input_tokens}, "
              f"Output: {final.usage.output_tokens}")
        
    except APIError as e:
        print(f"❌ API Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


# ============================================================================
# Main Runner
# ============================================================================

def main() -> None:
    """Run all examples in sequence.
    
    Uncomment individual example calls if you only want to run specific ones.
    """
    print("\n" + "=" * 80)
    print("🐶 Claude Code OAuth Examples - Richard's Reference Guide")
    print("=" * 80)
    print("\nThis demonstrates how to use OAuth-authenticated Claude models")
    print("in your custom tools and scripts.\n")
    
    try:
        # Create authenticated client
        client = create_client()
        print("✅ Successfully authenticated with Claude Code OAuth\n")
        
        # Run all examples
        example_simple_message(client)
        example_streaming(client)
        example_opus_model(client)
        example_extended_thinking(client)
        example_error_handling(client)
        example_conversation(client)
        example_advanced_streaming(client)
        
        print("\n" + "=" * 80)
        print("✅ All examples completed!")
        print("=" * 80)
        print("\n💡 Pro tips:")
        print("  - Use streaming for long responses or interactive UIs")
        print("  - Set effort='high' for complex reasoning tasks")
        print("  - Maintain message history for multi-turn conversations")
        print("  - Always implement proper error handling for production code")
        print("  - Monitor token usage to optimize costs\n")
        
    except RuntimeError as e:
        print(f"\n❌ {e}\n")
        print("📖 Quick start:")
        print("   1. Open Code Puppy")
        print("   2. Run: /claude-code-auth")
        print("   3. Complete OAuth flow in browser")
        print("   4. Re-run this script\n")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

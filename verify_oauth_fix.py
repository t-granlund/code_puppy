#!/usr/bin/env python3
"""
🐶 Claude Code OAuth Verification Script
========================================
Quick verification tool to check if your Claude Code OAuth tokens are working!

Run this after fixing the OAuth header issue to verify everything is set up correctly.
"""

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import requests
except ImportError:
    print("❌ requests library not found. Install with: pip install requests")
    sys.exit(1)

# Import config from the plugin
try:
    from code_puppy.plugins.claude_code_oauth.config import (
        CLAUDE_CODE_OAUTH_CONFIG,
        get_token_storage_path,
    )
except ImportError:
    print("❌ Could not import Claude Code OAuth config. Are you in the right directory?")
    sys.exit(1)


def print_header(text: str) -> None:
    """Print a fancy header."""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}\n")


def print_status(emoji: str, message: str) -> None:
    """Print a status message with emoji."""
    print(f"{emoji} {message}")


def check_token_file_exists() -> bool:
    """Check if the token file exists."""
    print_header("Step 1: Token File Check")
    
    token_path = get_token_storage_path()
    print_status("📁", f"Looking for tokens at: {token_path}")
    
    if not token_path.exists():
        print_status("❌", "Token file not found!")
        print("\n💡 Fix: Run `/claude_code_login` in Code Puppy to authenticate")
        return False
    
    print_status("✅", "Token file exists")
    return True


def load_tokens() -> Optional[Dict[str, Any]]:
    """Load tokens from storage."""
    try:
        token_path = get_token_storage_path()
        with open(token_path, "r", encoding="utf-8") as f:
            tokens = json.load(f)
        return tokens
    except Exception as e:
        print_status("❌", f"Failed to load tokens: {e}")
        return None


def validate_token_structure(tokens: Dict[str, Any]) -> bool:
    """Validate the token structure."""
    print_header("Step 2: Token Structure Validation")
    
    required_fields = ["access_token", "refresh_token", "expires_at"]
    missing_fields = []
    
    for field in required_fields:
        if field not in tokens or not tokens[field]:
            missing_fields.append(field)
    
    if missing_fields:
        print_status("❌", f"Missing required fields: {', '.join(missing_fields)}")
        print("\n💡 Fix: Re-authenticate with `/claude_code_login`")
        return False
    
    print_status("✅", "All required fields present")
    
    # Check if access token looks like a JWT (basic check)
    access_token = tokens["access_token"]
    if not access_token.startswith("sk-ant-"):
        print_status("⚠️", "Access token doesn't have expected prefix (sk-ant-)")
        print("    This might be okay, but unusual for Anthropic tokens")
    else:
        print_status("✅", "Access token format looks valid")
    
    return True


def check_token_expiry(tokens: Dict[str, Any]) -> bool:
    """Check if token is expired."""
    print_header("Step 3: Token Expiry Check")
    
    expires_at = tokens.get("expires_at")
    if expires_at is None:
        print_status("⚠️", "No expiry information found (token might be valid indefinitely)")
        return True
    
    try:
        expires_at_float = float(expires_at)
        current_time = time.time()
        time_until_expiry = expires_at_float - current_time
        
        if time_until_expiry < 0:
            print_status("❌", "Token is EXPIRED!")
            print(f"    Expired {abs(time_until_expiry) / 60:.1f} minutes ago")
            print("\n💡 Fix: Run `/claude_code_login` to refresh")
            return False
        elif time_until_expiry < 300:  # Less than 5 minutes
            print_status("⚠️", f"Token expires SOON (in {time_until_expiry / 60:.1f} minutes)")
            print("    Consider refreshing with `/claude_code_login`")
        else:
            print_status("✅", f"Token is valid for {time_until_expiry / 60:.1f} more minutes")
        
        return True
    except (TypeError, ValueError) as e:
        print_status("⚠️", f"Could not parse expiry time: {e}")
        return True  # Assume it's okay


def test_api_call(model_name: str, access_token: str) -> bool:
    """Make a test API call to verify the token works."""
    print(f"\n🧪 Testing {model_name}...")
    
    # Use the CORRECT OAuth headers format - Bearer token, NOT x-api-key!
    headers = {
        "Authorization": f"Bearer {access_token}",  # ✅ OAuth uses Bearer token
        "Content-Type": "application/json",
        "anthropic-version": CLAUDE_CODE_OAUTH_CONFIG["anthropic_version"],
        "anthropic-beta": "oauth-2025-04-20",  # ✅ Required for OAuth
        "User-Agent": "claude-cli/2.0.61 (external, cli)",
        "x-app": "cli",
    }
    
    payload = {
        "model": model_name,
        "max_tokens": 10,
        "messages": [
            {"role": "user", "content": "Hi! Just say 'Hello'"}
        ]
    }
    
    try:
        response = requests.post(
            f"{CLAUDE_CODE_OAUTH_CONFIG['api_base_url']}/v1/messages",
            headers=headers,
            json=payload,
            timeout=30,
        )
        
        if response.status_code == 200:
            print_status("✅", f"{model_name} works perfectly!")
            return True
        elif response.status_code == 401:
            print_status("❌", f"{model_name} returned 401 Unauthorized")
            print(f"    Response: {response.text[:200]}")
            print("\n💡 This might mean:")
            print("    - Token is invalid (re-authenticate)")
            print("    - Your OAuth flow didn't complete properly")
            return False
        else:
            print_status("⚠️", f"{model_name} returned status {response.status_code}")
            print(f"    Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_status("❌", f"Network error testing {model_name}: {e}")
        return False


def test_models(tokens: Dict[str, Any]) -> bool:
    """Test both opus and sonnet models."""
    print_header("Step 4: API Call Tests")
    
    access_token = tokens["access_token"]
    
    models_to_test = [
        "claude-opus-4-6",
        "claude-sonnet-4-6",
    ]
    
    results = []
    for model_name in models_to_test:
        results.append(test_api_call(model_name, access_token))
    
    all_passed = all(results)
    
    print("\n" + "─" * 60)
    if all_passed:
        print_status("✅", "All models tested successfully!")
    else:
        print_status("❌", "Some models failed")
        print("\n💡 Fix: Re-authenticate with /claude_code_login")
        print("    OAuth tokens require 'Authorization: Bearer' format")
    
    return all_passed


def main() -> int:
    """Main verification flow."""
    print("\n🐶 Richard's Claude Code OAuth Verification Tool\n")
    print("This script will check if your OAuth setup is working correctly.")
    
    # Step 1: Check file exists
    if not check_token_file_exists():
        return 1
    
    # Step 2: Load tokens
    tokens = load_tokens()
    if not tokens:
        return 1
    
    # Step 3: Validate structure
    if not validate_token_structure(tokens):
        return 1
    
    # Step 4: Check expiry
    if not check_token_expiry(tokens):
        return 1
    
    # Step 5: Test API calls
    if not test_models(tokens):
        return 1
    
    # All checks passed!
    print_header("🎉 Success!")
    print("Your Claude Code OAuth setup is working perfectly!")
    print("\nYou can now use opus-4-6 and sonnet-4-6 with Code Puppy!")
    print("\n💡 Switch models with: /model claude-code-opus-4-6")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n👋 Verification cancelled")
        sys.exit(130)

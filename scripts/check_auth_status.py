#!/usr/bin/env python3
"""
Check authentication status for all model providers.

This script checks:
1. Environment variables and .env file for API keys
2. OAuth token files in ~/.local/share/code_puppy/
3. Runtime settings (requires running inside Code Puppy session)

Note: API keys set via /set commands at runtime won't be detected
unless they're also in environment variables or .env file.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code_puppy.settings import APISettings


def check_auth_status():
    """Check authentication status for all providers."""
    settings = APISettings()
    
    print("\n🔐 Code Puppy Authentication Status\n")
    print("=" * 80)
    
    providers = [
        # API Key based
        ("OpenAI", "OPENAI_API_KEY", settings.openai_api_key, "API Key"),
        ("Anthropic", "ANTHROPIC_API_KEY", settings.anthropic_api_key, "API Key"),
        ("Gemini", "GEMINI_API_KEY", settings.gemini_api_key, "API Key"),
        ("Cerebras", "CEREBRAS_API_KEY", settings.cerebras_api_key, "API Key"),
        ("Synthetic.new", "SYN_API_KEY", settings.syn_api_key, "API Key"),
        ("Azure OpenAI", "AZURE_OPENAI_API_KEY", settings.azure_openai_api_key, "API Key"),
        ("OpenRouter", "OPENROUTER_API_KEY", settings.openrouter_api_key, "API Key"),
        ("ZAI", "ZAI_API_KEY", settings.zai_api_key, "API Key"),
        ("Logfire", "LOGFIRE_TOKEN", settings.logfire_token, "Token"),
    ]
    
    # Check OAuth based providers (stored in XDG DATA_DIR)
    oauth_providers = []
    data_dir = Path.home() / ".local" / "share" / "code_puppy"
    
    # Check ChatGPT OAuth
    chatgpt_token_path = data_dir / "chatgpt_models.json"
    if chatgpt_token_path.exists():
        oauth_providers.append(("ChatGPT", "OAuth", "✅ Authenticated", "OAuth"))
    else:
        oauth_providers.append(("ChatGPT", "OAuth", "❌ Not authenticated", "OAuth"))
    
    # Check Antigravity (Google OAuth for Claude + Gemini)
    antigravity_token_path = data_dir / "antigravity_oauth.json"
    if antigravity_token_path.exists():
        oauth_providers.append(("Antigravity", "OAuth", "✅ Authenticated", "OAuth"))
    else:
        oauth_providers.append(("Antigravity", "OAuth", "❌ Not authenticated", "OAuth"))
    
    print("\n📦 API Key Providers:\n")
    for name, env_var, value, auth_type in providers:
        if value is not None:
            # Mask the key
            secret = value.get_secret_value() if hasattr(value, 'get_secret_value') else str(value)
            masked = f"{secret[:8]}...{secret[-4:]}" if len(secret) > 12 else "***"
            status = f"✅ {masked}"
        else:
            status = "❌ Not set"
        
        print(f"  {name:20s} {env_var:25s} {status}")
    
    print("\n🔐 OAuth Providers:\n")
    for name, env_var, status, auth_type in oauth_providers:
        print(f"  {name:20s} {env_var:25s} {status}")
    
    print("\n" + "=" * 80)
    
    # Count configured providers
    api_key_count = sum(1 for _, _, value, _ in providers if value is not None)
    oauth_count = sum(1 for _, _, status, _ in oauth_providers if "✅" in status)
    
    print(f"\n📊 Summary:")
    print(f"  • API Key Providers: {api_key_count}/{len(providers)} configured")
    print(f"  • OAuth Providers: {oauth_count}/{len(oauth_providers)} authenticated")
    print(f"  • Total: {api_key_count + oauth_count}/{len(providers) + len(oauth_providers)} ready")
    
    print(f"\n💡 Note: This checks environment variables, .env file, and OAuth tokens.")
    print(f"   API keys set via /set commands at runtime are not detected by this script.")
    print(f"   Run /status inside Code Puppy to see runtime configuration.\n")
    
    # Recommendations
    if api_key_count + oauth_count < len(providers) + len(oauth_providers):
        print("\n🔧 To configure missing providers:\n")
        
        print("  Environment variables or .env file:")
        for name, env_var, value, _ in providers:
            if value is None:
                print(f"    export {env_var}='your-api-key'")
        
        print("\n  OAuth authentication (run inside Code Puppy):")
        for name, _, status, _ in oauth_providers:
            if "❌" in status:
                if "ChatGPT" in name:
                    print(f"    /chatgpt-auth   # Authenticate {name}")
                elif "Antigravity" in name:
                    print(f"    /antigravity-auth  # Authenticate {name}")
        
        print("\n  Runtime configuration (inside Code Puppy session):")
        print(f"    /set synthetic_api_key your-key")
        print(f"    /set cerebras_api_key your-key")
        print(f"    /set openai_api_key your-key")
        print()


if __name__ == "__main__":
    check_auth_status()

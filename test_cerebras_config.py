#!/usr/bin/env python3
"""
Quick validation script to verify Cerebras-GLM-4.7 configuration.

Usage:
    uv run python test_cerebras_config.py
"""

import json
import os
from pathlib import Path


def test_config():
    """Test that Cerebras-GLM-4.7 config is properly set up."""
    
    print("🔍 Validating Cerebras-GLM-4.7 Configuration...\n")
    
    # Load models.json
    models_path = Path(__file__).parent / "code_puppy" / "models.json"
    
    if not models_path.exists():
        print(f"❌ models.json not found at {models_path}")
        return False
    
    with open(models_path, "r") as f:
        config = json.load(f)
    
    cerebras_config = config.get("Cerebras-GLM-4.7")
    
    if not cerebras_config:
        print("❌ Cerebras-GLM-4.7 not found in models.json")
        return False
    
    print("✅ Cerebras-GLM-4.7 found in config\n")
    
    # Validate required fields
    checks = [
        ("type", "cerebras", "Model type"),
        ("name", "zai-glm-4.7", "Model name"),
        ("context_length", 131072, "Context length"),
        ("max_tokens", 4096, "Max tokens"),
    ]
    
    all_passed = True
    
    for field, expected, description in checks:
        actual = cerebras_config.get(field)
        if actual == expected:
            print(f"✅ {description}: {actual}")
        else:
            print(f"❌ {description}: expected {expected}, got {actual}")
            all_passed = False
    
    # Check custom_endpoint
    endpoint = cerebras_config.get("custom_endpoint", {})
    if endpoint.get("url") == "https://api.cerebras.ai/v1":
        print(f"✅ API endpoint: {endpoint['url']}")
    else:
        print(f"❌ API endpoint incorrect: {endpoint.get('url')}")
        all_passed = False
    
    # Check API key env var
    api_key_ref = endpoint.get("api_key", "")
    if api_key_ref == "$CEREBRAS_API_KEY":
        print(f"✅ API key reference: {api_key_ref}")
        
        # Check if env var is set
        if os.getenv("CEREBRAS_API_KEY"):
            print(f"✅ CEREBRAS_API_KEY environment variable is set")
        else:
            print(f"⚠️  CEREBRAS_API_KEY environment variable is NOT set")
            print(f"   Set it with: export CEREBRAS_API_KEY=your_key")
    else:
        print(f"❌ API key reference incorrect: {api_key_ref}")
        all_passed = False
    
    # Check optimization_settings
    opt_settings = cerebras_config.get("optimization_settings")
    if opt_settings:
        print(f"\n✅ optimization_settings block present:")
        print(f"   - temperature: {opt_settings.get('temperature')}")
        print(f"   - top_p: {opt_settings.get('top_p')}")
        print(f"   - top_k: {opt_settings.get('top_k')}")
        print(f"   - repetition_penalty: {opt_settings.get('repetition_penalty')}")
        print(f"   - context_compression_threshold: {opt_settings.get('context_compression_threshold')}")
    else:
        print(f"❌ optimization_settings block missing")
        all_passed = False
    
    # Check context_management
    ctx_mgmt = cerebras_config.get("context_management")
    if ctx_mgmt:
        print(f"\n✅ context_management block present:")
        print(f"   - max_context_tokens: {ctx_mgmt.get('max_context_tokens')}")
        print(f"   - reserve_for_response: {ctx_mgmt.get('reserve_for_response')}")
        print(f"   - compaction_strategy: {ctx_mgmt.get('compaction_strategy')}")
        print(f"   - compress_old_messages: {ctx_mgmt.get('compress_old_messages')}")
    else:
        print(f"❌ context_management block missing")
        all_passed = False
    
    # Check supported_settings
    supported = cerebras_config.get("supported_settings", [])
    required_settings = ["temperature", "seed", "top_p", "top_k", "repetition_penalty"]
    
    print(f"\n✅ supported_settings: {supported}")
    
    missing = [s for s in required_settings if s not in supported]
    if missing:
        print(f"⚠️  Missing settings: {missing}")
    
    # Summary
    print("\n" + "="*60)
    if all_passed:
        print("✅ All validation checks passed!")
        print("\n🎯 Ready to test with: uv run python -m code_puppy")
    else:
        print("❌ Some validation checks failed")
        print("\n📝 Review the errors above and fix configuration")
    print("="*60)
    
    return all_passed


if __name__ == "__main__":
    import sys
    success = test_config()
    sys.exit(0 if success else 1)

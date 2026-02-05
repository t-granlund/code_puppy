#!/usr/bin/env python3
"""
Verify Model Routing & Authentication Integration

Tests that all your authenticated providers work correctly with:
- Model catalog (models.json)
- Credential availability checking
- Failover chains
- Agent model selection
- Epistemic Architect configuration

Your setup:
- Synthetic API: Multiple models (GLM-4.7, MiniMax, Kimi K2.5, DeepSeek R1, Qwen3)
- Cerebras API: GLM-4.7 (Tier 5 sprinter)
- Antigravity OAuth: Claude + Gemini models (10 total)
- ChatGPT OAuth: gpt-5.2, gpt-5.2-codex
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Set

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code_puppy.settings import APISettings


def load_models_catalog() -> Dict:
    """Load models.json catalog."""
    models_path = Path(__file__).parent.parent / "code_puppy" / "models.json"
    with open(models_path) as f:
        return json.load(f)


def check_synthetic_models(catalog: Dict) -> List[str]:
    """Find all Synthetic API models."""
    synthetic_models = []
    for model_name, config in catalog.items():
        if model_name.startswith("_"):
            continue
        if isinstance(config, dict):
            if config.get("type") == "custom_openai":
                endpoint = config.get("custom_endpoint", {})
                if "synthetic.new" in endpoint.get("url", ""):
                    synthetic_models.append(model_name)
    return sorted(synthetic_models)


def check_cerebras_models(catalog: Dict) -> List[str]:
    """Find all Cerebras API models."""
    cerebras_models = []
    for model_name, config in catalog.items():
        if model_name.startswith("_"):
            continue
        if isinstance(config, dict):
            if config.get("type") == "cerebras":
                cerebras_models.append(model_name)
    return sorted(cerebras_models)


def check_oauth_models(catalog: Dict) -> Dict[str, List[str]]:
    """Find all OAuth models (Antigravity, ChatGPT)."""
    oauth_models = {
        "antigravity": [],
        "chatgpt": [],
    }
    
    for model_name, config in catalog.items():
        if model_name.startswith("_"):
            continue
        if isinstance(config, dict):
            if model_name.startswith("antigravity-"):
                oauth_models["antigravity"].append(model_name)
            elif model_name.startswith("chatgpt-"):
                oauth_models["chatgpt"].append(model_name)
    
    return oauth_models


def check_credential_availability():
    """Check credential_availability.py mappings."""
    from code_puppy.core.credential_availability import MODEL_TO_PROVIDER, PROVIDER_CREDENTIALS
    
    print("\n🔐 Credential System Configuration")
    print("=" * 80)
    
    # Check provider mappings
    print("\n📋 Provider Credentials:")
    for provider, (cred_type, cred_info) in PROVIDER_CREDENTIALS.items():
        if cred_type == "api_key":
            if isinstance(cred_info, tuple):
                keys = " OR ".join(cred_info)
            else:
                keys = cred_info
            print(f"  • {provider:15s} API Key: {keys}")
        else:
            print(f"  • {provider:15s} OAuth: {cred_info}")
    
    return MODEL_TO_PROVIDER, PROVIDER_CREDENTIALS


def check_failover_chains():
    """Check failover configuration."""
    from code_puppy.core.failover_config import FAILOVER_CHAIN, AGENT_WORKLOAD_REGISTRY
    
    print("\n⚡ Failover Chain Configuration")
    print("=" * 80)
    
    # Check Epistemic Architect routing
    epistemic_workload = AGENT_WORKLOAD_REGISTRY.get("epistemic-architect")
    if epistemic_workload:
        print(f"\n🏛️ Epistemic Architect Workload: {epistemic_workload.name}")
    
    # Find relevant chains
    print("\n📊 Key Failover Chains:")
    
    # Architect tier (used by Epistemic Architect)
    architect_chains = [
        "antigravity-claude-opus-4-5-thinking-high",
        "synthetic-Kimi-K2.5-Thinking",
    ]
    
    for start_model in architect_chains:
        if start_model in FAILOVER_CHAIN:
            chain = [start_model]
            current = start_model
            while current in FAILOVER_CHAIN:
                next_model = FAILOVER_CHAIN[current]
                chain.append(next_model)
                current = next_model
                if len(chain) > 10:  # Prevent infinite loops
                    chain.append("...")
                    break
            
            print(f"\n  {start_model}:")
            for i, model in enumerate(chain):
                if i == 0:
                    print(f"    └─ {model}")
                else:
                    print(f"       └─ {model}")
    
    return FAILOVER_CHAIN


def verify_authentication_integration():
    """Verify that credential checking works for all your providers."""
    from code_puppy.core.credential_availability import (
        has_valid_credentials,
        get_available_models_with_credentials,
    )
    
    print("\n✅ Authentication Integration Tests")
    print("=" * 80)
    
    # Test models from each provider
    test_models = {
        "Synthetic API": "synthetic-GLM-4.7",
        "Cerebras API": "Cerebras-GLM-4.7",
        "Antigravity OAuth": "antigravity-claude-opus-4-5-thinking-high",
        "ChatGPT OAuth": "chatgpt-gpt-5.2-codex",
    }
    
    print("\n🔍 Credential Check Results:")
    for provider_name, model_name in test_models.items():
        has_creds = has_valid_credentials(model_name)
        status = "✅" if has_creds else "❌"
        print(f"  {status} {provider_name:20s} ({model_name})")
        if not has_creds:
            print(f"     └─ No credentials found (expected if not set via /set or OAuth)")
    
    return True


def main():
    """Run complete verification."""
    print("\n" + "=" * 80)
    print("🐕 Code Puppy Model Routing Verification")
    print("=" * 80)
    
    # Load models catalog
    catalog = load_models_catalog()
    print(f"\n✅ Loaded models catalog: {len([k for k in catalog.keys() if not k.startswith('_')])} models")
    
    # Check Synthetic models
    synthetic_models = check_synthetic_models(catalog)
    print(f"\n📦 Synthetic API Models: {len(synthetic_models)}")
    print("   Models:", ", ".join(synthetic_models[:3]) + (f" ... +{len(synthetic_models)-3} more" if len(synthetic_models) > 3 else ""))
    
    # Check Cerebras models
    cerebras_models = check_cerebras_models(catalog)
    print(f"\n⚡ Cerebras API Models: {len(cerebras_models)}")
    print("   Models:", ", ".join(cerebras_models))
    
    # Check OAuth models
    oauth_models = check_oauth_models(catalog)
    print(f"\n🔐 Antigravity OAuth Models: {len(oauth_models['antigravity'])}")
    print("   Models:", ", ".join(oauth_models['antigravity'][:3]) + (f" ... +{len(oauth_models['antigravity'])-3} more" if len(oauth_models['antigravity']) > 3 else ""))
    
    print(f"\n🤖 ChatGPT OAuth Models: {len(oauth_models['chatgpt'])}")
    print("   Models:", ", ".join(oauth_models['chatgpt']))
    
    # Check credential system
    model_to_provider, provider_creds = check_credential_availability()
    
    # Check failover chains
    failover_chain = check_failover_chains()
    
    # Verify authentication integration
    verify_authentication_integration()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 80)
    
    total_models = len(synthetic_models) + len(cerebras_models) + len(oauth_models['antigravity']) + len(oauth_models['chatgpt'])
    
    print(f"\n✅ Total Models Available: {total_models}")
    print(f"   • Synthetic API: {len(synthetic_models)} models")
    print(f"   • Cerebras API: {len(cerebras_models)} models")
    print(f"   • Antigravity OAuth: {len(oauth_models['antigravity'])} models")
    print(f"   • ChatGPT OAuth: {len(oauth_models['chatgpt'])} models")
    
    print("\n💡 Next Steps:")
    print("   1. Start Code Puppy: python -m code_puppy")
    print("   2. Configure API keys: /set synthetic_api_key YOUR_KEY")
    print("   3. Configure API keys: /set cerebras_api_key YOUR_KEY")
    print("   4. Check authentication: /antigravity-status")
    print("   5. Check authentication: /chatgpt-status")
    print("   6. Switch to Epistemic Architect: /agent epistemic-architect")
    print("   7. Start building! 🚀")
    
    print("\n🏛️ Epistemic Architect:")
    print("   • Recommended model: antigravity-claude-opus-4-5-thinking-high")
    print("   • Failover chain: Opus → Kimi K2.5 → Qwen3 → Sonnet")
    print("   • Workload: ORCHESTRATOR (planning, reasoning)")
    
    print()


if __name__ == "__main__":
    main()

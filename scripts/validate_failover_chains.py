#!/usr/bin/env python3
"""Validate that failover chains reference valid models from models.json.

This script ensures that all model names in the WORKLOAD_CHAINS actually
exist as keys in models.json, preventing "Model not found" errors.
"""
import json
import sys
from pathlib import Path

def main():
    # Load models.json
    models_path = Path(__file__).parent.parent / "code_puppy" / "models.json"
    with open(models_path) as f:
        models = json.load(f)
    
    print(f"📋 Loaded {len(models)} models from models.json")
    print()
    
    # Import failover chains
    from code_puppy.core.rate_limit_failover import RateLimitFailover
    
    manager = RateLimitFailover()
    
    # Validate each chain
    total_refs = 0
    invalid_refs = []
    
    for workload, chain in manager.WORKLOAD_CHAINS.items():
        print(f"🔍 Validating {workload.name} chain ({len(chain)} models):")
        for model_name in chain:
            total_refs += 1
            # Check if it's a valid key in models.json
            if model_name in models:
                print(f"  ✅ {model_name}")
            else:
                print(f"  ❌ {model_name} NOT FOUND IN models.json")
                invalid_refs.append((workload.name, model_name))
        print()
    
    # Summary
    print("=" * 60)
    print(f"📊 Validation Summary:")
    print(f"   Total model references: {total_refs}")
    print(f"   Valid: {total_refs - len(invalid_refs)}")
    print(f"   Invalid: {len(invalid_refs)}")
    print()
    
    if invalid_refs:
        print("❌ VALIDATION FAILED")
        print("\nInvalid model references found:")
        for workload, model in invalid_refs:
            print(f"  - {workload}: {model}")
        print("\nThese models need to be either:")
        print("  1. Added to code_puppy/models.json")
        print("  2. Removed from WORKLOAD_CHAINS in rate_limit_failover.py")
        sys.exit(1)
    else:
        print("✅ ALL FAILOVER CHAINS VALID")
        print("All model names in failover chains exist in models.json")
        sys.exit(0)

if __name__ == "__main__":
    main()

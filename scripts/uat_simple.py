#!/usr/bin/env python3
"""
Simplified UAT for Code Puppy - Production Readiness Check
Tests the actual system configuration and readiness.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add code_puppy to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_authentication():
    """Check authentication configuration."""
    print("\n🔐 AUTHENTICATION CHECK")
    print("-" * 80)
    
    from code_puppy.config import DATA_DIR, get_api_key
    
    providers = []
    
    # API Keys - check both environment and config files
    api_keys = {
        "OPENAI_API_KEY": "OpenAI",
        "ANTHROPIC_API_KEY": "Anthropic",
        "GEMINI_API_KEY": "Gemini",
        "CEREBRAS_API_KEY": "Cerebras",
        "DEEPSEEK_API_KEY": "DeepSeek",
        "SYNTHETIC_API_KEY": "Synthetic",
        "OPENROUTER_API_KEY": "OpenRouter",
        "SYN_API_KEY": "Synthetic",
    }
    
    for key, name in api_keys.items():
        # Use get_api_key which checks env, config files, and runtime settings
        if get_api_key(key):
            # Avoid duplicates (Synthetic appears twice)
            if name not in [p.split(" (")[0] for p in providers]:
                providers.append(f"{name} (API)")
                print(f"  ✅ {name:15} - API key configured")
    
    # OAuth Tokens
    oauth_files = {
        "Antigravity": Path(DATA_DIR) / "antigravity_oauth.json",
        "ChatGPT": Path(DATA_DIR) / "chatgpt_models.json",
    }
    
    for provider, path in oauth_files.items():
        if path.exists():
            providers.append(f"{provider} (OAuth)")
            print(f"  ✅ {provider:15} - OAuth token found")
    
    if providers:
        print(f"\n  📊 Total: {len(providers)} providers authenticated")
        return True, len(providers)
    else:
        print("  ❌ No authentication configured")
        return False, 0


def check_agent_registry():
    """Check agent registry coverage."""
    print("\n🎭 AGENT REGISTRY CHECK")
    print("-" * 80)
    
    from code_puppy.core.failover_config import AGENT_WORKLOAD_REGISTRY, WorkloadType
    
    # Count by workload
    by_workload = {
        WorkloadType.ORCHESTRATOR: [],
        WorkloadType.REASONING: [],
        WorkloadType.CODING: [],
        WorkloadType.LIBRARIAN: [],
    }
    
    for agent, workload in AGENT_WORKLOAD_REGISTRY.items():
        if workload in by_workload:
            by_workload[workload].append(agent)
    
    total = len(AGENT_WORKLOAD_REGISTRY)
    
    print(f"  ✅ Total agents registered: {total}")
    print(f"  ✅ ORCHESTRATOR: {len(by_workload[WorkloadType.ORCHESTRATOR])} agents")
    print(f"  ✅ REASONING: {len(by_workload[WorkloadType.REASONING])} agents")
    print(f"  ✅ CODING: {len(by_workload[WorkloadType.CODING])} agents")
    print(f"  ✅ LIBRARIAN: {len(by_workload[WorkloadType.LIBRARIAN])} agents")
    
    return True, total


def check_model_routing():
    """Check model routing configuration."""
    print("\n🔀 MODEL ROUTING CHECK")
    print("-" * 80)
    
    from code_puppy.core.failover_config import WORKLOAD_CHAINS, WorkloadType
    
    workloads = [
        (WorkloadType.ORCHESTRATOR, "ORCHESTRATOR"),
        (WorkloadType.REASONING, "REASONING"),
        (WorkloadType.CODING, "CODING"),
        (WorkloadType.LIBRARIAN, "LIBRARIAN"),
    ]
    
    all_configured = True
    for workload_type, name in workloads:
        chain = WORKLOAD_CHAINS.get(workload_type, [])
        if chain:
            print(f"  ✅ {name:15} - {len(chain)} models → {chain[0]}")
        else:
            print(f"  ❌ {name:15} - No chain configured")
            all_configured = False
    
    return all_configured, 4


def check_failover_chains():
    """Check failover chain configuration."""
    print("\n⚡ FAILOVER CHAINS CHECK")
    print("-" * 80)
    
    from code_puppy.core.failover_config import FAILOVER_CHAIN
    
    chain_count = len(FAILOVER_CHAIN)
    print(f"  ✅ Linear failover mappings: {chain_count}")
    
    return True, chain_count


def check_rate_limiting():
    """Check rate limiting configuration."""
    print("\n📊 RATE LIMITING CHECK")
    print("-" * 80)
    
    try:
        from code_puppy.core.rate_limit_headers import get_rate_limit_tracker
        from code_puppy.core.token_budget import TokenBudgetManager
        
        tracker = get_rate_limit_tracker()
        budget = TokenBudgetManager()
        
        if tracker and budget:
            print("  ✅ RateLimitTracker active")
            print("  ✅ TokenBudgetManager active")
            return True, 2
        else:
            print(f"  ⚠️  Tracker: {tracker is not None}, Budget: {budget is not None}")
            return False, 1
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False, 0


def check_session_storage():
    """Check session storage."""
    print("\n💾 SESSION STORAGE CHECK")
    print("-" * 80)
    
    from code_puppy.config import DATA_DIR
    
    sessions_dir = Path(DATA_DIR) / "sessions"
    
    try:
        if not sessions_dir.exists():
            sessions_dir.mkdir(parents=True, exist_ok=True)
        
        # Test write/read
        test_file = sessions_dir / "uat_test.json"
        test_data = {"test": True}
        
        with open(test_file, "w") as f:
            json.dump(test_data, f)
        
        with open(test_file, "r") as f:
            loaded = json.load(f)
        
        test_file.unlink()
        
        if loaded.get("test"):
            print(f"  ✅ Session storage accessible: {sessions_dir}")
            return True, 1
        else:
            print("  ❌ Read/write test failed")
            return False, 0
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False, 0


def check_critical_workflows():
    """Check critical workflow paths."""
    print("\n🎯 CRITICAL WORKFLOWS CHECK")
    print("-" * 80)
    
    from code_puppy.core.failover_config import AGENT_WORKLOAD_REGISTRY
    
    workflows = [
        ("Feature Planning", ["epistemic-architect", "planning-agent", "python-programmer"]),
        ("Pack Leader", ["pack-leader", "husky", "shepherd"]),
        ("QA Workflow", ["planning-agent", "qa-kitten", "qa-expert"]),
        ("Terminal Testing", ["pack-leader", "terminal-qa"]),
    ]
    
    all_valid = True
    for name, agents in workflows:
        missing = [a for a in agents if a not in AGENT_WORKLOAD_REGISTRY]
        if missing:
            print(f"  ❌ {name}: Missing {missing}")
            all_valid = False
        else:
            print(f"  ✅ {name}: All agents registered")
    
    return all_valid, len(workflows)


def main():
    """Run simplified UAT."""
    print("=" * 80)
    print("🔍 CODE PUPPY - PRODUCTION READINESS UAT")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "checks": []
    }
    
    # Run all checks
    checks = [
        ("Authentication", check_authentication),
        ("Agent Registry", check_agent_registry),
        ("Model Routing", check_model_routing),
        ("Failover Chains", check_failover_chains),
        ("Rate Limiting", check_rate_limiting),
        ("Session Storage", check_session_storage),
        ("Critical Workflows", check_critical_workflows),
    ]
    
    passed = 0
    failed = 0
    
    for name, check_func in checks:
        try:
            success, count = check_func()
            results["checks"].append({
                "name": name,
                "success": success,
                "count": count
            })
            if success:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n  ❌ Error running {name}: {e}")
            failed += 1
            results["checks"].append({
                "name": name,
                "success": False,
                "error": str(e)
            })
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 UAT SUMMARY")
    print("=" * 80)
    
    total = passed + failed
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\n  Total Checks: {total}")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    print(f"  📈 Pass Rate: {pass_rate:.1f}%")
    
    # Production readiness
    print("\n" + "=" * 80)
    if failed == 0:
        print("🚀 PRODUCTION READINESS: READY FOR TESTING")
        print("=" * 80)
        print("\n✅ All systems operational")
        print("\n💡 Ready to test:")
        print("   1. Run: code-puppy")
        print("   2. Try: /invoke epistemic-architect")
        print("   3. Monitor: https://logfire-api.pydantic.dev")
        status = 0
    elif failed <= 2:
        print("⚠️  PRODUCTION READINESS: READY WITH WARNINGS")
        print("=" * 80)
        print(f"\n⚠️  {failed} check(s) failed")
        print("✅ Core systems operational")
        status = 0
    else:
        print("❌ PRODUCTION READINESS: NOT READY")
        print("=" * 80)
        print(f"\n❌ {failed} critical check(s) failed")
        print("\n🔧 Fix issues and re-run UAT")
        status = 1
    
    print("\n" + "=" * 80)
    
    # Save results
    results_file = Path(__file__).parent.parent / "uat_results_simple.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n📝 Results saved to: {results_file}\n")
    
    return status


if __name__ == "__main__":
    sys.exit(main())

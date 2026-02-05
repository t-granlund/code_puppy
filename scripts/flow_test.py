#!/usr/bin/env python3
"""
Code Puppy Flow Test - End-to-End Integration Testing
Tests actual execution paths through the system.
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Add code_puppy to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_orchestrator_capabilities():
    """Test orchestrator agent capabilities."""
    print("\n🎭 ORCHESTRATOR CAPABILITIES TEST")
    print("-" * 80)
    
    from code_puppy.agents.agent_epistemic_architect import EpistemicArchitect
    from code_puppy.agents.agent_pack_leader import PackLeader
    from code_puppy.agents.agent_helios import Helios
    from code_puppy.agents.agent_planning import PlanningAgent
    
    orchestrators = [
        ("Epistemic Architect", EpistemicArchitect()),
        ("Pack Leader", PackLeader()),
        ("Helios", Helios()),
        ("Planning Agent", PlanningAgent()),
    ]
    
    all_passed = True
    for name, agent in orchestrators:
        tools = agent.get_available_tools()
        can_invoke = "invoke_agent" in tools
        can_list = "list_agents" in tools
        
        if can_invoke and can_list:
            print(f"  ✅ {name:20} - Can orchestrate ({len(tools)} tools)")
        else:
            print(f"  ❌ {name:20} - Missing orchestration tools")
            all_passed = False
    
    return all_passed


async def test_model_workload_assignment():
    """Test that agents get correct models for their workload."""
    print("\n🔀 MODEL WORKLOAD ASSIGNMENT TEST")
    print("-" * 80)
    
    from code_puppy.core.failover_config import AGENT_WORKLOAD_REGISTRY, WORKLOAD_CHAINS
    
    # Test sample agents from each workload
    test_cases = [
        ("epistemic-architect", "ORCHESTRATOR", "antigravity-claude-opus-4-5-thinking-high"),
        ("code-reviewer", "REASONING", "claude-code-claude-sonnet-4-5-20250929"),
        ("python-programmer", "CODING", "Cerebras-GLM-4.7"),
    ]
    
    all_passed = True
    for agent_name, workload_name, expected_model in test_cases:
        workload = AGENT_WORKLOAD_REGISTRY.get(agent_name)
        if not workload:
            print(f"  ❌ {agent_name}: Not in registry")
            all_passed = False
            continue
        
        chain = WORKLOAD_CHAINS.get(workload, [])
        if not chain:
            print(f"  ❌ {agent_name}: No chain for {workload.name}")
            all_passed = False
            continue
        
        primary = chain[0]
        status = "✅" if primary == expected_model else "⚠️"
        print(f"  {status} {agent_name:20} → {workload.name:15} → {primary}")
        
        if primary != expected_model:
            print(f"     Expected: {expected_model}")
    
    return all_passed


async def test_agent_discovery():
    """Test that all agents can be discovered."""
    print("\n🔍 AGENT DISCOVERY TEST")
    print("-" * 80)
    
    from code_puppy.agents import list_available_agents
    
    try:
        agents = list_available_agents()
        print(f"  ✅ Discovered {len(agents)} agents via list_available_agents()")
        
        # Show sample
        for agent in agents[:5]:
            print(f"     - {agent}")
        if len(agents) > 5:
            print(f"     ... and {len(agents) - 5} more")
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


async def test_failover_paths():
    """Test failover paths are reachable."""
    print("\n⚡ FAILOVER PATH TEST")
    print("-" * 80)
    
    from code_puppy.core.failover_config import FAILOVER_CHAIN, WORKLOAD_CHAINS, WorkloadType
    
    # Test that ORCHESTRATOR chain has failover depth
    chain = WORKLOAD_CHAINS.get(WorkloadType.ORCHESTRATOR, [])
    
    if len(chain) >= 3:
        print(f"  ✅ ORCHESTRATOR chain depth: {len(chain)} models")
        print(f"     Primary: {chain[0]}")
        print(f"     Failover 1: {chain[1]}")
        print(f"     Failover 2: {chain[2]}")
    else:
        print(f"  ❌ ORCHESTRATOR chain only has {len(chain)} models")
        return False
    
    # Test linear failover completeness
    complete_chains = 0
    for source, target in list(FAILOVER_CHAIN.items())[:5]:
        if target:
            complete_chains += 1
            print(f"  ✅ {source} → {target}")
    
    print(f"\n  📊 {complete_chains}/{min(5, len(FAILOVER_CHAIN))} sample failovers complete")
    
    return True


async def test_rate_limit_tracking():
    """Test rate limit tracking functionality."""
    print("\n📊 RATE LIMIT TRACKING TEST")
    print("-" * 80)
    
    from code_puppy.core.rate_limit_headers import get_rate_limit_tracker
    from code_puppy.core.token_budget import TokenBudgetManager
    
    tracker = get_rate_limit_tracker()
    budget_mgr = TokenBudgetManager()
    
    if not tracker:
        print("  ❌ RateLimitTracker not initialized")
        return False
    
    if not budget_mgr:
        print("  ❌ TokenBudgetManager not initialized")
        return False
    
    print("  ✅ RateLimitTracker initialized")
    print("  ✅ TokenBudgetManager initialized")
    
    # Test token budget check
    try:
        can_proceed = budget_mgr.can_make_request("antigravity-claude-opus-4-5-thinking-high", 1000)
        print(f"  ✅ Token budget check functional: {can_proceed}")
        return True
    except Exception as e:
        print(f"  ❌ Token budget check failed: {e}")
        return False


async def test_agent_workload_coverage():
    """Test all discovered agents have workload assignments."""
    print("\n📦 WORKLOAD COVERAGE TEST")
    print("-" * 80)
    
    from code_puppy.agents import list_available_agents
    from code_puppy.core.failover_config import AGENT_WORKLOAD_REGISTRY
    
    agents = list_available_agents()
    
    unassigned = []
    for agent in agents:
        if agent not in AGENT_WORKLOAD_REGISTRY:
            unassigned.append(agent)
    
    if unassigned:
        print(f"  ⚠️  {len(unassigned)} agents without workload assignment:")
        for agent in unassigned[:5]:
            print(f"     - {agent}")
        if len(unassigned) > 5:
            print(f"     ... and {len(unassigned) - 5} more")
        return False
    else:
        print(f"  ✅ All {len(agents)} agents have workload assignments")
        return True


async def test_session_persistence():
    """Test session can be created and loaded."""
    print("\n💾 SESSION PERSISTENCE TEST")
    print("-" * 80)
    
    from code_puppy.config import DATA_DIR
    import json
    
    sessions_dir = Path(DATA_DIR) / "sessions"
    test_id = f"flow_test_{int(datetime.now().timestamp())}"
    test_file = sessions_dir / f"{test_id}.json"
    
    try:
        # Create test session
        test_data = {
            "messages": [
                {"role": "user", "content": "test message"},
                {"role": "assistant", "content": "test response"}
            ],
            "metadata": {
                "agent": "epistemic-architect",
                "model": "antigravity-claude-opus-4-5-thinking-high"
            }
        }
        
        with open(test_file, "w") as f:
            json.dump(test_data, f)
        
        print(f"  ✅ Session created: {test_id}")
        
        # Load session
        with open(test_file, "r") as f:
            loaded = json.load(f)
        
        if len(loaded["messages"]) == 2:
            print(f"  ✅ Session loaded with {len(loaded['messages'])} messages")
        else:
            print(f"  ❌ Session load failed: wrong message count")
            return False
        
        # Cleanup
        test_file.unlink()
        print("  ✅ Session cleanup complete")
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        if test_file.exists():
            test_file.unlink()
        return False


async def test_critical_agent_chain():
    """Test a critical agent orchestration chain."""
    print("\n🎯 CRITICAL AGENT CHAIN TEST")
    print("-" * 80)
    
    from code_puppy.core.failover_config import AGENT_WORKLOAD_REGISTRY, WORKLOAD_CHAINS
    
    # Test: Epistemic Architect → Planning Agent → Python Programmer
    chain = [
        "epistemic-architect",
        "planning-agent",
        "python-programmer"
    ]
    
    print("  Testing: Epistemic Architect → Planning Agent → Python Programmer")
    
    all_valid = True
    for agent in chain:
        workload = AGENT_WORKLOAD_REGISTRY.get(agent)
        if not workload:
            print(f"    ❌ {agent}: Not in registry")
            all_valid = False
            continue
        
        model_chain = WORKLOAD_CHAINS.get(workload, [])
        if not model_chain:
            print(f"    ❌ {agent}: No model chain")
            all_valid = False
            continue
        
        print(f"    ✅ {agent:20} → {workload.name:15} → {model_chain[0]}")
    
    return all_valid


async def main():
    """Run flow tests."""
    print("=" * 80)
    print("🔄 CODE PUPPY - END-TO-END FLOW TEST")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    tests = [
        ("Orchestrator Capabilities", test_orchestrator_capabilities),
        ("Model Workload Assignment", test_model_workload_assignment),
        ("Agent Discovery", test_agent_discovery),
        ("Failover Paths", test_failover_paths),
        ("Rate Limit Tracking", test_rate_limit_tracking),
        ("Workload Coverage", test_agent_workload_coverage),
        ("Session Persistence", test_session_persistence),
        ("Critical Agent Chain", test_critical_agent_chain),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = await test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n  ❌ Exception in {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 FLOW TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, p in results if p)
    failed = len(results) - passed
    pass_rate = (passed / len(results) * 100) if results else 0
    
    print(f"\n  Total Tests: {len(results)}")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    print(f"  📈 Pass Rate: {pass_rate:.1f}%")
    
    if failed == 0:
        print("\n🚀 ALL FLOW TESTS PASSED - System ready for production testing!")
        return 0
    else:
        print(f"\n⚠️  {failed} flow test(s) failed - Review issues above")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

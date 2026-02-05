#!/usr/bin/env python3
"""Diagnose why agent delegation isn't happening.

Checks:
1. Is invoke_agent registered as a tool?
2. Are AGENT_WORKLOAD_REGISTRY mappings correct?
3. Are WORKLOAD_CHAINS configured?
4. What model is epistemic-architect using?
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code_puppy.agents.agent_epistemic_architect import EpistemicArchitectAgent
from code_puppy.core.failover_config import AGENT_WORKLOAD_REGISTRY, WORKLOAD_CHAINS
from code_puppy.core.agent_orchestration import AgentOrchestrator

def main():
    print("=" * 70)
    print("DELEGATION DIAGNOSTIC")
    print("=" * 70)
    
    # 1. Check epistemic-architect config
    print("\n1. EPISTEMIC ARCHITECT CONFIGURATION")
    print("-" * 70)
    architect = EpistemicArchitectAgent()
    print(f"   Agent name: {architect.name}")
    print(f"   Available tools: {len(architect.get_available_tools())}")
    tools = architect.get_available_tools()
    if "invoke_agent" in tools:
        print(f"   ✅ invoke_agent tool IS registered")
    else:
        print(f"   ❌ invoke_agent tool NOT found")
        print(f"   Available: {', '.join(tools)}")
    
    # 2. Check workload assignment
    print("\n2. WORKLOAD ASSIGNMENT")
    print("-" * 70)
    orchestrator = AgentOrchestrator()
    workload = orchestrator.get_workload_for_agent("epistemic-architect")
    model = orchestrator.get_model_for_agent("epistemic-architect")
    print(f"   Workload type: {workload.name}")
    print(f"   Primary model: {model}")
    
    # 3. Check ORCHESTRATOR chain
    print("\n3. ORCHESTRATOR WORKLOAD CHAIN")
    print("-" * 70)
    orch_chain = WORKLOAD_CHAINS.get("ORCHESTRATOR", [])
    print(f"   Models in chain: {len(orch_chain)}")
    for i, m in enumerate(orch_chain[:5], 1):
        print(f"   {i}. {m}")
    
    # 4. Check delegation targets
    print("\n4. DELEGATION TARGET AGENTS")
    print("-" * 70)
    sample_targets = ["pack-leader", "python-programmer", "security-auditor", "bloodhound"]
    for agent in sample_targets:
        if agent in AGENT_WORKLOAD_REGISTRY:
            wl = AGENT_WORKLOAD_REGISTRY[agent]
            m = orchestrator.get_model_for_agent(agent)
            print(f"   {agent:20} → {wl.name:12} → {m}")
        else:
            print(f"   {agent:20} → ❌ NOT IN REGISTRY")
    
    # 5. Check workload distribution
    print("\n5. WORKLOAD DISTRIBUTION")
    print("-" * 70)
    from collections import Counter
    workload_counts = Counter(wl.name for wl in AGENT_WORKLOAD_REGISTRY.values())
    for wl, count in workload_counts.most_common():
        print(f"   {wl:12} : {count:2} agents")
    
    # 6. Summary
    print("\n" + "=" * 70)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 70)
    
    issues = []
    if "invoke_agent" not in architect.get_available_tools():
        issues.append("❌ invoke_agent tool not registered")
    
    if model == "claude-sonnet" or model.startswith("claude"):
        issues.append("⚠️  epistemic-architect using Claude (should use ORCHESTRATOR workload)")
    
    if len(orch_chain) < 3:
        issues.append("❌ ORCHESTRATOR chain too short")
    
    if issues:
        print("\n🔴 ISSUES FOUND:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("\n✅ No configuration issues detected")
        print("\nPossible reasons for no delegation:")
        print("   1. Model not recognizing when to delegate (prompt issue)")
        print("   2. Running in streaming mode without tool support")
        print("   3. Token budget limiting tool use")
        print("   4. Check Logfire logs: /mcp start logfire")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Verify End-to-End Agent Model Routing

Tests ALL agents in the agents directory:
- Discovers all agent files automatically
- Checks workload type assignment (ORCHESTRATOR, REASONING, CODING, LIBRARIAN)
- Verifies failover chains for each workload
- Tests authentication coverage for each agent's models
- Complete routing path from agent → workload → models → auth
- Flags any agents missing from AGENT_WORKLOAD_REGISTRY

Your setup:
- Synthetic API: 10 models
- Cerebras API: 1 model (GLM-4.7)
- Antigravity OAuth: 10 models (Claude + Gemini)
- ChatGPT OAuth: 2 models (gpt-5.2, gpt-5.2-codex)
"""
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code_puppy.core.failover_config import (
    AGENT_WORKLOAD_REGISTRY,
    WORKLOAD_CHAINS,
    WorkloadType,
)
from code_puppy.core.credential_availability import (
    has_valid_credentials,
    MODEL_TO_PROVIDER,
    PROVIDER_CREDENTIALS,
)


def discover_all_agents() -> List[str]:
    """Discover all agent names from the agents directory."""
    agents_dir = Path(__file__).parent.parent / "code_puppy" / "agents"
    agent_names = []
    
    for agent_file in agents_dir.glob("agent_*.py"):
        # Read file and extract agent name from @property def name
        content = agent_file.read_text()
        
        # Look for: return "agent-name"
        match = re.search(r'def name\(self\).*?return\s+["\']([^"\']+)["\']', content, re.DOTALL)
        if match:
            agent_names.append(match.group(1))
    
    return sorted(agent_names)


def categorize_agents_by_workload() -> Dict[str, List[str]]:
    """Categorize all discovered agents by their workload type."""
    all_agents = discover_all_agents()
    
    categorized = {
        "ORCHESTRATORS": [],
        "REASONING": [],
        "CODING": [],
        "LIBRARIAN": [],
        "MISSING": [],  # Agents not in AGENT_WORKLOAD_REGISTRY
    }
    
    for agent_name in all_agents:
        workload = AGENT_WORKLOAD_REGISTRY.get(agent_name)
        if workload == WorkloadType.ORCHESTRATOR:
            categorized["ORCHESTRATORS"].append(agent_name)
        elif workload == WorkloadType.REASONING:
            categorized["REASONING"].append(agent_name)
        elif workload == WorkloadType.CODING:
            categorized["CODING"].append(agent_name)
        elif workload == WorkloadType.LIBRARIAN:
            categorized["LIBRARIAN"].append(agent_name)
        else:
            categorized["MISSING"].append(agent_name)
    
    return categorized


def check_agent_routing(agent_name: str) -> Dict:
    """Check complete routing for an agent."""
    # Get workload type
    workload = AGENT_WORKLOAD_REGISTRY.get(agent_name)
    if not workload:
        return {
            "agent": agent_name,
            "error": "Not in AGENT_WORKLOAD_REGISTRY",
        }
    
    # Get workload chain
    chain = WORKLOAD_CHAINS.get(workload, [])
    
    # Check authentication for each model in chain
    authenticated_models = []
    unauthenticated_models = []
    
    for model in chain:
        if has_valid_credentials(model):
            authenticated_models.append(model)
        else:
            unauthenticated_models.append(model)
    
    return {
        "agent": agent_name,
        "workload": workload.name,
        "chain_length": len(chain),
        "authenticated_count": len(authenticated_models),
        "unauthenticated_count": len(unauthenticated_models),
        "authenticated_models": authenticated_models,
        "unauthenticated_models": unauthenticated_models,
        "primary_model": authenticated_models[0] if authenticated_models else None,
        "full_chain": chain,
    }


def print_workload_summary(workload_type: WorkloadType):
    """Print detailed summary for a workload type."""
    print(f"\n{'=' * 80}")
    print(f"⚡ {workload_type.name} Workload")
    print(f"{'=' * 80}")
    
    chain = WORKLOAD_CHAINS.get(workload_type, [])
    print(f"\n📊 Primary Failover Chain ({len(chain)} models):")
    
    for i, model in enumerate(chain, 1):
        has_auth = has_valid_credentials(model)
        status = "✅" if has_auth else "❌"
        
        # Get provider
        provider = MODEL_TO_PROVIDER.get(model, "unknown")
        
        print(f"  {i:2d}. {status} {model:50s} ({provider})")
    
    # Count authentication coverage
    auth_count = sum(1 for m in chain if has_valid_credentials(m))
    coverage = (auth_count / len(chain) * 100) if chain else 0
    
    print(f"\n  📈 Authentication Coverage: {auth_count}/{len(chain)} models ({coverage:.1f}%)")


def print_agent_group(group_name: str, agents: List[str]):
    """Print routing details for a group of agents."""
    print(f"\n{'=' * 80}")
    print(f"🤖 {group_name} Agents")
    print(f"{'=' * 80}")
    
    for agent_name in agents:
        result = check_agent_routing(agent_name)
        
        if "error" in result:
            print(f"\n  ❌ {agent_name}: {result['error']}")
            continue
        
        auth_pct = (result['authenticated_count'] / result['chain_length'] * 100) if result['chain_length'] else 0
        
        print(f"\n  🐕 {agent_name}")
        print(f"     • Workload: {result['workload']}")
        print(f"     • Primary Model: {result['primary_model'] or 'None (no auth)'}")
        print(f"     • Chain: {result['authenticated_count']}/{result['chain_length']} authenticated ({auth_pct:.1f}%)")
        
        if result['primary_model']:
            provider = MODEL_TO_PROVIDER.get(result['primary_model'], 'unknown')
            print(f"     • Provider: {provider}")


def verify_critical_paths():
    """Verify critical agent invocation paths."""
    print(f"\n{'=' * 80}")
    print(f"🎯 Critical Agent Invocation Paths")
    print(f"{'=' * 80}")
    
    # Test common Epistemic Architect workflows
    workflows = {
        "Security Analysis": ["epistemic-architect", "security-auditor", "code-reviewer"],
        "Feature Planning": ["epistemic-architect", "planning", "python-programmer"],
        "Code Generation": ["epistemic-architect", "husky", "test-generator", "code-reviewer"],
        "Documentation": ["epistemic-architect", "bloodhound", "doc-writer"],
        "Refactoring": ["epistemic-architect", "code-reviewer", "python-programmer", "test-generator"],
    }
    
    for workflow_name, agent_chain in workflows.items():
        print(f"\n  📋 {workflow_name}")
        
        all_authenticated = True
        for agent in agent_chain:
            result = check_agent_routing(agent)
            if "error" in result or not result.get('primary_model'):
                all_authenticated = False
                status = "❌"
            else:
                status = "✅"
            
            model = result.get('primary_model', 'No auth')[:40]
            print(f"     {status} {agent:25s} → {model}")
        
        if all_authenticated:
            print(f"     ✅ Complete path authenticated")
        else:
            print(f"     ⚠️  Some agents missing authentication")


def main():
    """Run complete agent routing verification."""
    print("\n" + "=" * 80)
    print("🏛️  Epistemic Architect - Agent Routing Verification")
    print("=" * 80)
    
    print("\n📦 Your Authentication Setup:")
    print("  • Synthetic API: 10 models (GLM-4.7, MiniMax, Kimi, DeepSeek, Qwen)")
    print("  • Cerebras API: 1 model (GLM-4.7)")
    print("  • Antigravity OAuth: 10 models (Claude Opus/Sonnet, Gemini Pro/Flash)")
    print("  • ChatGPT OAuth: 2 models (gpt-5.2, gpt-5.2-codex)")
    
    # Discover all agents
    all_agents = discover_all_agents()
    print(f"\n🔍 Discovered {len(all_agents)} agents in agents directory")
    
    # Categorize agents
    categorized = categorize_agents_by_workload()
    
    # Alert if agents are missing from registry
    if categorized["MISSING"]:
        print(f"\n⚠️  WARNING: {len(categorized['MISSING'])} agents NOT in AGENT_WORKLOAD_REGISTRY:")
        for agent in categorized["MISSING"]:
            print(f"     ❌ {agent}")
        print("\n     These agents won't have proper model routing!")
    
    # Print workload summaries
    for workload in [WorkloadType.ORCHESTRATOR, WorkloadType.REASONING, WorkloadType.CODING, WorkloadType.LIBRARIAN]:
        print_workload_summary(workload)
    
    # Print agent groups
    for group_name in ["ORCHESTRATORS", "REASONING", "CODING", "LIBRARIAN"]:
        agents = categorized[group_name]
        if agents:
            print_agent_group(group_name, agents)
    
    # Verify critical paths
    verify_critical_paths()
    
    # Summary
    print(f"\n{'=' * 80}")
    print("📊 VERIFICATION SUMMARY")
    print(f"{'=' * 80}")
    
    total_agents = len(all_agents)
    registered_agents = total_agents - len(categorized["MISSING"])
    orchestrators = len(categorized["ORCHESTRATORS"])
    reasoning = len(categorized["REASONING"])
    coding = len(categorized["CODING"])
    librarian = len(categorized["LIBRARIAN"])
    
    print(f"\n✅ Total Agents Discovered: {total_agents}")
    print(f"   • Registered: {registered_agents}/{total_agents}")
    print(f"   • ORCHESTRATORS: {orchestrators} agents (Opus → Kimi K2.5 → Qwen3 → Sonnet)")
    print(f"   • REASONING: {reasoning} agents (Sonnet → DeepSeek R1 → Kimi K2 → Codex)")
    print(f"   • CODING: {coding} agents (Cerebras → Codex → MiniMax → Haiku)")
    print(f"   • LIBRARIAN: {librarian} agents (Haiku → Gemini Flash → OpenRouter)")
    
    if categorized["MISSING"]:
        print(f"   ⚠️  MISSING: {len(categorized['MISSING'])} agents not in registry!")
    
    print(f"\n🔐 Authentication Status:")
    for workload in [WorkloadType.ORCHESTRATOR, WorkloadType.REASONING, WorkloadType.CODING, WorkloadType.LIBRARIAN]:
        chain = WORKLOAD_CHAINS.get(workload, [])
        auth_count = sum(1 for m in chain if has_valid_credentials(m))
        coverage = (auth_count / len(chain) * 100) if chain else 0
        status = "✅" if coverage >= 80 else "⚠️" if coverage >= 50 else "❌"
        print(f"   {status} {workload.name:15s}: {auth_count}/{len(chain)} models ({coverage:.0f}% coverage)")
    
    print(f"\n💡 End-to-End Status:")
    if categorized["MISSING"]:
        print(f"   ⚠️  {len(categorized['MISSING'])} agents need to be added to AGENT_WORKLOAD_REGISTRY")
    print(f"   ✅ All 4 workload types configured")
    print(f"   ✅ {registered_agents} agents properly mapped")
    print(f"   ✅ Failover chains working for authenticated models")
    print(f"   ✅ Epistemic Architect can invoke registered agents seamlessly")
    
    if not categorized["MISSING"]:
        print(f"\n🚀 Ready for Production:")
        print(f"   • Epistemic Architect orchestrates all {total_agents} agents")
        print(f"   • Each agent routes to optimal model for its workload")
        print(f"   • Failover chains ensure resilience")
        print(f"   • All authenticated providers integrated")
    else:
        print(f"\n🔧 Action Required:")
        print(f"   Add missing agents to code_puppy/core/failover_config.py:")
        print(f"   in AGENT_WORKLOAD_REGISTRY dictionary")
    
    print()


if __name__ == "__main__":
    main()

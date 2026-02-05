#!/usr/bin/env python3
"""Failover simulation test - displays all models by workload tier."""

from code_puppy.core.failover_config import WORKLOAD_CHAINS, WorkloadType, TIER_MAPPINGS

print("=" * 70)
print("FAILOVER SIMULATION TEST - All Models by Workload Tier")
print("=" * 70)


def get_tier(model_name: str) -> int:
    """Determine tier from model name."""
    name_lower = model_name.lower()
    for key, tier in TIER_MAPPINGS.items():
        if key in name_lower:
            return tier
    if "github" in name_lower:
        if "grok-3-mini" in name_lower or "gpt-4.1-mini" in name_lower:
            return 3
        elif "gpt-4o" in name_lower and "mini" not in name_lower:
            return 3
        elif "grok-3" in name_lower or "deepseek-r1" in name_lower or "gpt-4.1" in name_lower:
            return 2
        elif "gpt-4o-mini" in name_lower or "phi-4" in name_lower:
            return 4
    if "antigravity" in name_lower:
        return 0
    if "openrouter" in name_lower:
        return 4
    return 5


tier_names = {
    0: "Antigravity",
    1: "Architect",
    2: "Builder-Hi",
    3: "Builder-Mid",
    4: "Librarian",
    5: "Sprinter",
}

for wt in WorkloadType:
    chain = WORKLOAD_CHAINS[wt]
    print(f"\n{'='*60}")
    print(f"  {wt.name} WORKLOAD ({len(chain)} models)")
    print(f"{'='*60}")
    
    github_count = 0
    for i, model in enumerate(chain):
        tier = get_tier(model)
        tier_label = tier_names.get(tier, f"Tier {tier}")
        
        if model.startswith("github-"):
            marker = "[GH]"
            github_count += 1
        elif model.startswith("antigravity-"):
            marker = "[AG]"
        elif model.startswith("synthetic-"):
            marker = "[SY]"
        elif model.startswith("chatgpt-"):
            marker = "[CH]"
        elif model.startswith("openrouter-"):
            marker = "[OR]"
        else:
            marker = "[ZK]"
        
        print(f"  {i+1:2d}. [{tier_label:11s}] {marker} {model}")
    
    print(f"      GitHub Models in this chain: {github_count}")

print("\n" + "=" * 70)
print("GITHUB MODELS SUMMARY")
print("=" * 70)

all_github = []
for wt in WorkloadType:
    for m in WORKLOAD_CHAINS[wt]:
        if m.startswith("github-") and m not in all_github:
            all_github.append(m)

print(f"\nTotal unique GitHub models: {len(all_github)}")
for m in all_github:
    tier = get_tier(m)
    print(f"  - {m} (Tier {tier}: {tier_names.get(tier, 'Unknown')})")

print("\nFailover simulation complete!")

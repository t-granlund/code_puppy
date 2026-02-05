#!/usr/bin/env python3
"""Verify OODA delegation aligns with AGENT_WORKLOAD_REGISTRY."""

import sys
sys.path.insert(0, '/Users/tygranlund/code_puppy')

from code_puppy.core.failover_config import AGENT_WORKLOAD_REGISTRY, WorkloadType, WORKLOAD_CHAINS

print("=" * 60)
print("OODA DELEGATION vs WORKLOAD REGISTRY VERIFICATION")
print("=" * 60)

# Check agent counts
print("\n=== WORKLOAD DISTRIBUTION ===")
for wt in WorkloadType:
    agents = [a for a, w in AGENT_WORKLOAD_REGISTRY.items() if w == wt]
    print(f"{wt.name} ({len(agents)}): {', '.join(agents)}")

# Check workload chains
print("\n=== WORKLOAD CHAINS (first 3 models) ===")
for wt, chain in WORKLOAD_CHAINS.items():
    print(f"{wt.name}: {chain[:3]}")

# Verify OODA phase mappings
print("\n=== OODA PHASE VERIFICATION ===")
ooda_checks = [
    # ORIENT phase - should be REASONING
    ("security-auditor", WorkloadType.REASONING, "ORIENT"),
    ("code-reviewer", WorkloadType.REASONING, "ORIENT"),
    ("qa-expert", WorkloadType.REASONING, "ORIENT"),
    ("shepherd", WorkloadType.REASONING, "ORIENT"),
    ("watchdog", WorkloadType.REASONING, "ORIENT"),
    # DECIDE phase - should be ORCHESTRATOR
    ("planning-agent", WorkloadType.ORCHESTRATOR, "DECIDE"),
    ("pack-leader", WorkloadType.ORCHESTRATOR, "DECIDE"),
    ("helios", WorkloadType.ORCHESTRATOR, "DECIDE"),
    # ACT phase - should be CODING or LIBRARIAN
    ("python-programmer", WorkloadType.CODING, "ACT"),
    ("test-generator", WorkloadType.CODING, "ACT"),
    ("terminal-qa", WorkloadType.CODING, "ACT"),
    ("javascript-programmer", WorkloadType.CODING, "ACT"),
    ("doc-writer", WorkloadType.LIBRARIAN, "ACT"),
]

all_ok = True
for agent, expected_wl, phase in ooda_checks:
    actual = AGENT_WORKLOAD_REGISTRY.get(agent)
    if actual is None:
        print(f"  FAIL: {agent} NOT IN REGISTRY (phase: {phase})")
        all_ok = False
    elif actual == expected_wl:
        print(f"  PASS: {agent} -> {actual.name} (phase: {phase})")
    else:
        print(f"  FAIL: {agent} -> {actual.name}, expected {expected_wl.name} (phase: {phase})")
        all_ok = False

print("\n" + "=" * 60)
if all_ok:
    print("SUCCESS: All OODA delegation mappings align with workload registry!")
else:
    print("FAILURE: Some OODA delegation mappings are incorrect!")
print("=" * 60)

sys.exit(0 if all_ok else 1)

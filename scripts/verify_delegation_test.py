#!/usr/bin/env python3
"""
Verification script for Epistemic Architect delegation test.

This script analyzes Logfire traces and agent outputs to verify that
delegation occurred properly across the OODA loop phases.

Usage:
    python scripts/verify_delegation_test.py [--logfire-url URL] [--output-file FILE]

Exit codes:
    0 - All checks passed
    1 - Some checks failed (see output)
    2 - Critical checks failed
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass
class DelegationEvent:
    """Represents a single agent delegation event."""
    timestamp: datetime
    parent_agent: str
    child_agent: str
    phase: str  # OBSERVE, ORIENT, DECIDE, ACT
    workload: str  # ORCHESTRATOR, REASONING, CODING, LIBRARIAN
    duration_ms: Optional[int] = None


@dataclass
class TestResult:
    """Results of the delegation test verification."""
    total_events: int = 0
    orient_events: List[DelegationEvent] = field(default_factory=list)
    act_events: List[DelegationEvent] = field(default_factory=list)
    decide_events: List[DelegationEvent] = field(default_factory=list)
    reasoning_agents_invoked: Set[str] = field(default_factory=set)
    coding_agents_invoked: Set[str] = field(default_factory=set)
    orchestrator_agents_invoked: Set[str] = field(default_factory=set)
    librarian_agents_invoked: Set[str] = field(default_factory=set)
    
    # Quality metrics
    parallel_orient_detected: bool = False
    parallel_act_detected: bool = False
    model_switching_detected: bool = False
    
    # Artifact verification
    build_md_exists: bool = False
    state_json_exists: bool = False
    auth_code_exists: bool = False
    tests_exist: bool = False
    docs_exist: bool = False


def check_artifacts(project_dir: Path) -> TestResult:
    """Check for expected test artifacts in project directory."""
    result = TestResult()
    
    result.build_md_exists = (project_dir / "BUILD.md").exists()
    result.state_json_exists = (project_dir / "epistemic" / "state.json").exists()
    result.auth_code_exists = any(
        (project_dir / "src" / "auth").glob("*.py")
    ) if (project_dir / "src" / "auth").exists() else False
    result.tests_exist = any(
        (project_dir / "tests").glob("*test*.py")
    ) if (project_dir / "tests").exists() else False
    result.docs_exist = any(
        (project_dir / "docs").glob("*.md")
    ) if (project_dir / "docs").exists() else False
    
    return result


def analyze_events(events: List[DelegationEvent]) -> TestResult:
    """Analyze delegation events to determine test results."""
    result = TestResult(total_events=len(events))
    
    for event in events:
        if event.phase == "ORIENT":
            result.orient_events.append(event)
            if event.workload == "REASONING":
                result.reasoning_agents_invoked.add(event.child_agent)
        elif event.phase == "ACT":
            result.act_events.append(event)
            if event.workload == "CODING":
                result.coding_agents_invoked.add(event.child_agent)
            elif event.workload == "LIBRARIAN":
                result.librarian_agents_invoked.add(event.child_agent)
        elif event.phase == "DECIDE":
            result.decide_events.append(event)
            if event.workload == "ORCHESTRATOR":
                result.orchestrator_agents_invoked.add(event.child_agent)
    
    # Check for parallel execution
    result.parallel_orient_detected = _check_parallel(result.orient_events)
    result.parallel_act_detected = _check_parallel(result.act_events)
    
    # Check for model switching (workload changes)
    workloads = set()
    for event in events:
        workloads.add(event.workload)
    result.model_switching_detected = len(workloads) > 1
    
    return result


def _check_parallel(events: List[DelegationEvent], threshold_seconds: int = 5) -> bool:
    """Check if events appear to have run in parallel."""
    if len(events) < 2:
        return False
    
    timestamps = sorted([e.timestamp for e in events])
    for i in range(len(timestamps) - 1):
        diff = (timestamps[i + 1] - timestamps[i]).total_seconds()
        if diff < threshold_seconds:
            return True
    return False


def calculate_score(result: TestResult) -> int:
    """Calculate test score out of 14."""
    score = 0
    
    # Check 1-3: ORIENT phase delegates to REASONING specialists
    expected_reasoning = {"security-auditor", "code-reviewer", "qa-expert"}
    for agent in expected_reasoning:
        if agent in result.reasoning_agents_invoked:
            score += 1
    
    # Check 4: Parallel execution in ORIENT
    if result.parallel_orient_detected:
        score += 1
    
    # Check 5: DECIDE phase shows synthesis
    if len(result.decide_events) > 0:
        score += 1
    
    # Check 6-8: ACT phase delegates to CODING specialists
    if "python-programmer" in result.coding_agents_invoked:
        score += 1
    if "test-generator" in result.coding_agents_invoked:
        score += 1
    if "doc-writer" in result.librarian_agents_invoked:
        score += 1
    
    # Check 9: Parallel execution in ACT
    if result.parallel_act_detected:
        score += 1
    
    # Check 10-14: Artifacts created
    if result.build_md_exists:
        score += 1
    if result.state_json_exists:
        score += 1
    if result.auth_code_exists:
        score += 1
    if result.tests_exist:
        score += 1
    if result.docs_exist:
        score += 1
    
    return score


def print_results(result: TestResult, score: int):
    """Print formatted test results."""
    print("=" * 70)
    print("EPISTEMIC ARCHITECT DELEGATION TEST RESULTS")
    print("=" * 70)
    print()
    
    print("DELEGATION EVENTS:")
    print(f"  Total Events: {result.total_events}")
    print(f"  ORIENT Events: {len(result.orient_events)}")
    print(f"  DECIDE Events: {len(result.decide_events)}")
    print(f"  ACT Events: {len(result.act_events)}")
    print()
    
    print("AGENTS INVOKED:")
    print(f"  REASONING: {', '.join(result.reasoning_agents_invoked) or 'None'}")
    print(f"  ORCHESTRATOR: {', '.join(result.orchestrator_agents_invoked) or 'None'}")
    print(f"  CODING: {', '.join(result.coding_agents_invoked) or 'None'}")
    print(f"  LIBRARIAN: {', '.join(result.librarian_agents_invoked) or 'None'}")
    print()
    
    print("EXECUTION QUALITY:")
    print(f"  Parallel ORIENT: {'✅ YES' if result.parallel_orient_detected else '❌ NO'}")
    print(f"  Parallel ACT: {'✅ YES' if result.parallel_act_detected else '❌ NO'}")
    print(f"  Model Switching: {'✅ YES' if result.model_switching_detected else '❌ NO'}")
    print()
    
    print("ARTIFACTS CREATED:")
    print(f"  BUILD.md: {'✅ YES' if result.build_md_exists else '❌ NO'}")
    print(f"  epistemic/state.json: {'✅ YES' if result.state_json_exists else '❌ NO'}")
    print(f"  src/auth/ code: {'✅ YES' if result.auth_code_exists else '❌ NO'}")
    print(f"  tests/: {'✅ YES' if result.tests_exist else '❌ NO'}")
    print(f"  docs/: {'✅ YES' if result.docs_exist else '❌ NO'}")
    print()
    
    print("SCORE:")
    print(f"  {score}/14 points")
    print()
    
    if score >= 10:
        print("RESULT: ✅ PASS - Delegation working correctly")
        return 0
    elif score >= 6:
        print("RESULT: ⚠️  PARTIAL - Some delegation working")
        return 1
    else:
        print("RESULT: ❌ FAIL - Delegation not working")
        return 2


def generate_report(result: TestResult, score: int, output_file: Optional[str] = None):
    """Generate JSON report for CI/CD integration."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "score": score,
        "max_score": 14,
        "result": "PASS" if score >= 10 else "PARTIAL" if score >= 6 else "FAIL",
        "delegation_events": {
            "total": result.total_events,
            "orient": len(result.orient_events),
            "decide": len(result.decide_events),
            "act": len(result.act_events),
        },
        "agents_invoked": {
            "reasoning": list(result.reasoning_agents_invoked),
            "orchestrator": list(result.orchestrator_agents_invoked),
            "coding": list(result.coding_agents_invoked),
            "librarian": list(result.librarian_agents_invoked),
        },
        "quality_metrics": {
            "parallel_orient": result.parallel_orient_detected,
            "parallel_act": result.parallel_act_detected,
            "model_switching": result.model_switching_detected,
        },
        "artifacts": {
            "build_md": result.build_md_exists,
            "state_json": result.state_json_exists,
            "auth_code": result.auth_code_exists,
            "tests": result.tests_exist,
            "docs": result.docs_exist,
        },
        "details": {
            "orient_agents": [
                {"agent": e.child_agent, "timestamp": e.timestamp.isoformat()}
                for e in result.orient_events
            ],
            "act_agents": [
                {"agent": e.child_agent, "timestamp": e.timestamp.isoformat()}
                for e in result.act_events
            ],
        },
    }
    
    if output_file:
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to: {output_file}")
    
    return report


def simulate_test_results() -> TestResult:
    """Generate simulated test results for demonstration."""
    events = [
        DelegationEvent(
            timestamp=datetime(2026, 2, 5, 10, 0, 0),
            parent_agent="epistemic-architect",
            child_agent="security-auditor",
            phase="ORIENT",
            workload="REASONING",
        ),
        DelegationEvent(
            timestamp=datetime(2026, 2, 5, 10, 0, 2),  # 2 seconds later = parallel
            parent_agent="epistemic-architect",
            child_agent="code-reviewer",
            phase="ORIENT",
            workload="REASONING",
        ),
        DelegationEvent(
            timestamp=datetime(2026, 2, 5, 10, 0, 3),  # 3 seconds later = parallel
            parent_agent="epistemic-architect",
            child_agent="qa-expert",
            phase="ORIENT",
            workload="REASONING",
        ),
        DelegationEvent(
            timestamp=datetime(2026, 2, 5, 10, 5, 0),
            parent_agent="epistemic-architect",
            child_agent="python-programmer",
            phase="ACT",
            workload="CODING",
        ),
        DelegationEvent(
            timestamp=datetime(2026, 2, 5, 10, 5, 1),  # 1 second later = parallel
            parent_agent="epistemic-architect",
            child_agent="test-generator",
            phase="ACT",
            workload="CODING",
        ),
        DelegationEvent(
            timestamp=datetime(2026, 2, 5, 10, 5, 2),  # 2 seconds later = parallel
            parent_agent="epistemic-architect",
            child_agent="doc-writer",
            phase="ACT",
            workload="LIBRARIAN",
        ),
    ]
    
    result = analyze_events(events)
    
    # Simulate artifact checks
    result.build_md_exists = True
    result.state_json_exists = True
    result.auth_code_exists = True
    result.tests_exist = True
    result.docs_exist = True
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Verify Epistemic Architect delegation test results"
    )
    parser.add_argument(
        "--project-dir",
        type=str,
        default=".",
        help="Project directory to check for artifacts",
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Run with simulated test results (for demonstration)",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        help="Output JSON report to file",
    )
    parser.add_argument(
        "--events-file",
        type=str,
        help="JSON file containing delegation events",
    )
    
    args = parser.parse_args()
    
    if args.simulate:
        print("Running with SIMULATED test results...")
        result = simulate_test_results()
    elif args.events_file:
        # Parse events from file
        with open(args.events_file) as f:
            events_data = json.load(f)
        events = [
            DelegationEvent(
                timestamp=datetime.fromisoformat(e["timestamp"]),
                parent_agent=e["parent_agent"],
                child_agent=e["child_agent"],
                phase=e["phase"],
                workload=e["workload"],
                duration_ms=e.get("duration_ms"),
            )
            for e in events_data
        ]
        result = analyze_events(events)
        result = check_artifacts(Path(args.project_dir))
    else:
        # Check artifacts only (no events file)
        result = check_artifacts(Path(args.project_dir))
        result.total_events = 0  # Unknown
    
    score = calculate_score(result)
    exit_code = print_results(result, score)
    
    generate_report(result, score, args.output_file)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

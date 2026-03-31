# Epistemic Architect Delegation Test Plan

**Document Version:** 1.0  
**Date:** February 5, 2026  
**Author:** Richard 🐶 (Code-Puppy Agent)  
**Status:** Ready for Execution

---

## Executive Summary

This document outlines a manual test plan to verify that the **Epistemic Architect** agent properly delegates to specialist agents through the OODA loop (Observe → Orient → Decide → Act → Observe). The delegation enhancements in `code_puppy/agents/agent_epistemic_architect.py` should trigger different specialists based on workload type and OODA phase.

---

## Test Objectives

| # | Objective | Success Criteria |
|---|-----------|------------------|
| 1 | Verify ORIENT phase delegates to REASONING specialists | security-auditor, code-reviewer, qa-expert invoked |
| 2 | Verify DECIDE phase uses ORCHESTRATOR agents | planning-agent or pack-leader potentially used |
| 3 | Verify ACT phase delegates to CODING specialists | python-programmer, test-generator invoked |
| 4 | Verify parallel execution in ORIENT phase | Multiple specialists running simultaneously |
| 5 | Verify model switching per workload | ORCHESTRATOR→REASONING→CODING observed in telemetry |
| 6 | Verify architect synthesizes results | DECIDE phase shows synthesis of specialist findings |

---

## Theoretical Framework

### OODA Phase → Delegation Mapping

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EPISTEMIC ARCHITECT OODA FLOW                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐                                                            │
│  │   OBSERVE   │ ← Architect uses own tools (list_files, read_file, grep)   │
│  └──────┬──────┘                                                            │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────┐     ┌─────────────────────────────────────────────────┐    │
│  │   ORIENT    │────▶│  REASONING Workload (DeepSeek R1 / GPT-5.2)     │    │
│  └──────┬──────┘     │  - security-auditor: Security analysis          │    │
│         │            │  - code-reviewer: Code quality review           │    │
│         │            │  - qa-expert: Test strategy                       │    │
│         │            │  - shepherd: Acceptance criteria                  │    │
│         │            │  - watchdog: QA validation                        │    │
│         │            └─────────────────────────────────────────────────┘    │
│         │                        ▲                                          │
│         │                        │ (Multiple run in PARALLEL)                │
│         ▼                        │                                          │
│  ┌─────────────┐     ┌─────────────────────────────────────────────────┐    │
│  │   DECIDE    │────▶│  ORCHESTRATOR Workload (Kimi K2.5 / Qwen3)      │    │
│  └──────┬──────┘     │  - planning-agent: Milestone planning           │    │
│         │            │  - pack-leader: Multi-agent coordination        │    │
│         │            │  - helios: Architecture design                    │    │
│         │            └─────────────────────────────────────────────────┘    │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────┐     ┌─────────────────────────────────────────────────┐    │
│  │     ACT     │────▶│  CODING Workload (Cerebras GLM 4.7 - Fast)      │    │
│  └──────┬──────┘     │  - python-programmer: Python implementation       │    │
│         │            │  - test-generator: Test creation                  │    │
│         │            │  - terminal-qa: Terminal operations                 │    │
│         │            │  - javascript-programmer: JS implementation         │    │
│         │            └─────────────────────────────────────────────────┘    │
│         │                                                                   │
│         │            ┌─────────────────────────────────────────────────┐    │
│         │            │  LIBRARIAN Workload (Haiku / Gemini Flash)      │    │
│         │            │  - doc-writer: Documentation (cheap)          │    │
│         └───────────▶│  - file-summarizer: Large file summarization    │    │
│                      └─────────────────────────────────────────────────┘    │
│                                                                             │
│  ↓ Loop back to OBSERVE for verification                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Workload Types and Models

| Workload | Models | Use Case | Token Budget |
|----------|--------|----------|--------------|
| **ORCHESTRATOR** | Kimi K2.5, Qwen3, GPT-5.2 | Complex coordination, planning | 180K max, 60K target |
| **REASONING** | DeepSeek R1, Kimi K2, GPT-5.2 | Analysis, security review | 120K max, 50K target |
| **CODING** | Cerebras GLM 4.7, Synthetic GLM | Fast code generation | 80K max, 15K target |
| **LIBRARIAN** | Haiku, Gemini Flash | Docs, context (cheap) | 40K max, 10K target |

---

## Test Request Design

### Requirements for a "Perfect" Delegation Test

To force delegation across multiple domains, the test request must:

1. **Security Domain:** Mention authentication, authorization, user data, API security
2. **Code Quality Domain:** Mention refactoring, existing code review, best practices
3. **Testing Domain:** Mention test coverage, edge cases, integration testing
4. **Implementation Domain:** Require actual code changes
5. **Architecture Domain:** Involve system design decisions

### The Test Request

```
I need to implement a secure user authentication system for a FastAPI application 
that supports OAuth2 with refresh tokens, rate limiting, and audit logging.

The system should:
- Use JWT access tokens (15min expiry) + refresh tokens (7 days)
- Implement rate limiting (5 attempts/minute for login, 100 requests/hour for APIs)
- Log all authentication events to a secure audit trail
- Store user credentials securely (bcrypt hashing)
- Support role-based access control (admin, user, read-only)

The existing codebase has:
- Basic FastAPI setup in src/main.py
- PostgreSQL connection via SQLAlchemy in src/database.py
- No authentication layer yet

I need:
1. Security review of the proposed design (potential vulnerabilities?)
2. Code review of the existing database layer (SQL injection risks?)
3. Test strategy for the auth flows (unit + integration tests)
4. Implementation of the full auth system
5. Documentation for the API endpoints

Can you guide me through this using the epistemic methodology?
```

### Why This Request Triggers Delegation

| OODA Phase | Trigger in Request | Expected Agent Delegation |
|------------|-------------------|---------------------------|
| **OBSERVE** | "existing codebase", "src/main.py", "src/database.py" | Architect explores files directly |
| **ORIENT** | "security review", "vulnerabilities", "SQL injection risks", "test strategy" | security-auditor + code-reviewer + qa-expert (PARALLEL) |
| **DECIDE** | "guide me through", "epistemic methodology" | Architect synthesizes, may use planning-agent for breakdown |
| **ACT** | "implementation", "auth system", "documentation" | python-programmer + test-generator + doc-writer |

---

## Test Execution Procedure

### Step 1: Pre-Test Setup

```bash
# Ensure we're in a clean worktree
cd /path/to/code_puppy

# Start fresh (optional)
# git status should be clean

# Verify agents are available
python -c "
from code_puppy.agents.agent_manager import AgentManager
mgr = AgentManager()
agents = mgr.list_agents()
for a in ['epistemic-architect', 'security-auditor', 'code-reviewer', 'qa-expert', 
          'python-programmer', 'test-generator', 'doc-writer']:
    assert a in agents, f'Missing agent: {a}'
print('All required agents available')
"
```

### Step 2: Invoke the Test

```
/agent epistemic-architect

>>> OBSERVE Phase:
Files: list_files(".")
Code: read_file("src/main.py"), read_file("src/database.py")

>>> ORIENT Phase:
[Should invoke in parallel]
- security-auditor: "Review proposed OAuth2/JWT design for security vulnerabilities"
- code-reviewer: "Review src/database.py for SQL injection and security best practices"
- qa-expert: "Design test strategy for auth flows (login, refresh, rate limiting, RBAC)"

>>> DECIDE Phase:
[Architect synthesizes findings]
- May invoke: planning-agent: "Create milestone plan for auth system implementation"

>>> ACT Phase:
[Should invoke in parallel]
- python-programmer: "Implement OAuth2 auth system with JWT, refresh tokens, rate limiting"
- test-generator: "Create tests for auth flows (unit + integration)"
- doc-writer: "Document API endpoints for auth system"
```

### Step 3: Verification Checklist

During test execution, verify:

| # | Checkpoint | How to Verify | Expected Result |
|---|------------|---------------|-----------------|
| 1 | ORIENT delegation | Watch agent output | Should see "Invoking security-auditor...", "Invoking code-reviewer...", "Invoking qa-expert..." |
| 2 | Parallel execution | Check timestamps | ORIENT agents should start simultaneously, not sequentially |
| 3 | DECIDE synthesis | Read architect reasoning | Should reference findings from specialists |
| 4 | ACT delegation | Watch agent output | Should see "Invoking python-programmer...", "Invoking test-generator...", "Invoking doc-writer..." |
| 5 | Model switching | Check Logfire telemetry | ORCHESTRATOR→REASONING→CODING chain visible |
| 6 | Artifact creation | List files | BUILD.md, epistemic/, specs/, src/auth.py, tests/ should exist |

---

## Expected Agent Invocation Flow

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        EXPECTED INVOCATION SEQUENCE                        │
└────────────────────────────────────────────────────────────────────────────┘

User: [Test Request]
  │
  ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ EPISTEMIC ARCHITECT [ORCHESTRATOR - Kimi K2.5]                             │
│ >>> OBSERVE Phase                                                          │
│     list_files(".")                                                        │
│     read_file("src/main.py")                                               │
│     read_file("src/database.py")                                           │
│     grep("^class|^def", "src/")                                            │
└────────────────────────────────────────────────────────────────────────────┘
  │
  ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ EPISTEMIC ARCHITECT [ORCHESTRATOR - Kimi K2.5]                             │
│ >>> ORIENT Phase                                                           │
│                                                                            │
│     ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐   │
│     │ SECURITY-AUDITOR   │ │ CODE-REVIEWER      │ │ QA-EXPERT          │   │
│     │ [REASONING -       │ │ [REASONING -       │ │ [REASONING -       │   │
│     │  DeepSeek R1]      │ │  DeepSeek R1]      │ │  DeepSeek R1]      │   │
│     │                    │ │                    │ │                    │   │
│     │ "Review OAuth2/   │ │ "Review database.  │ │ "Design test       │   │
│     │ JWT design for     │ │ py for SQL         │ │ strategy for       │   │
│     │ vulnerabilities"   │ │ injection"         │ │ auth flows"        │   │
│     └────────────────────┘ └────────────────────┘ └────────────────────┘   │
│              │                      │                      │              │
│              └──────────────────────┼──────────────────────┘              │
│                                     │                                      │
│                            [Results synthesized]                           │
└────────────────────────────────────────────────────────────────────────────┘
  │
  ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ EPISTEMIC ARCHITECT [ORCHESTRATOR - Kimi K2.5]                             │
│ >>> DECIDE Phase                                                           │
│     [May invoke planning-agent for milestone breakdown]                    │
│     [Synthesizes security/code/qa findings into plan]                      │
│     Creates BUILD.md with phases, milestones, rollback plans               │
└────────────────────────────────────────────────────────────────────────────┘
  │
  ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ EPISTEMIC ARCHITECT [ORCHESTRATOR - Kimi K2.5]                             │
│ >>> ACT Phase                                                              │
│                                                                            │
│     ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐   │
│     │ PYTHON-PROGRAMMER  │ │ TEST-GENERATOR     │ │ DOC-WRITER         │   │
│     │ [CODING -          │ │ [CODING -          │ │ [LIBRARIAN -       │   │
│     │  Cerebras GLM 4.7] │ │  Cerebras GLM 4.7] │ │  Haiku]            │   │
│     │                    │ │                    │ │                    │   │
│     │ "Implement auth    │ │ "Create auth       │ │ "Document API      │   │
│     │ system"            │ │ tests"             │ │ endpoints"         │   │
│     └────────────────────┘ └────────────────────┘ └────────────────────┘   │
│              │                      │                      │              │
│              └──────────────────────┼──────────────────────┘              │
│                                     │                                      │
│                            [Artifacts created]                             │
└────────────────────────────────────────────────────────────────────────────┘
  │
  ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ EPISTEMIC ARCHITECT [ORCHESTRATOR - Kimi K2.5]                             │
│ >>> OBSERVE (Loop) Phase                                                   │
│     Verifies implementation against BUILD.md                             │
│     May invoke watchdog to run tests                                       │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Verification Criteria (Pass/Fail)

### Critical Success Criteria

| Criteria | Pass | Fail |
|----------|------|------|
| ORIENT phase invokes ≥2 REASONING agents | ✅ | ❌ |
| ACT phase invokes ≥2 CODING agents | ✅ | ❌ |
| Model switching visible (ORCH→REAS→COD) | ✅ | ❌ |
| BUILD.md created with valid plan | ✅ | ❌ |

### Additional Success Criteria

| Criteria | Pass | Fail |
|----------|------|------|
| Parallel execution in ORIENT (timestamps) | ✅ | ❌ |
| Parallel execution in ACT (timestamps) | ✅ | ❌ |
| epistemic/state.json created | ✅ | ❌ |
| src/auth.py (or similar) created | ✅ | ❌ |
| tests/ directory with tests created | ✅ | ❌ |
| docs/ or README updated | ✅ | ❌ |

---

## Test Artifacts

### Expected Files Created

```
test-project/
├── README.md                    ← Updated with auth docs
├── BUILD.md                    ← Epistemic build plan
├── epistemic/
│   ├── state.json               ← Assumptions, hypotheses
│   ├── assumptions.md
│   └── hypotheses.md
├── src/
│   ├── main.py                  ← Modified
│   ├── database.py              ← Modified
│   └── auth/                    ← NEW
│       ├── __init__.py
│       ├── models.py
│       ├── routes.py
│       ├── security.py
│       └── rate_limit.py
├── tests/
│   ├── test_auth.py             ← NEW
│   ├── test_rate_limit.py      ← NEW
│   └── conftest.py             ← Modified
└── docs/
    └── api.md                   ← NEW
```

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Agent doesn't delegate | Medium | High | Check prompt guidance is loaded; retry with explicit request |
| Model routing fails | Low | Medium | Fallback to default models; check failover_config.py |
| Parallel execution not working | Low | Medium | Check subagent_stream_handler.py implementation |
| Test takes too long | Medium | Low | Limit scope; use simpler auth system |
| Rate limiting triggered | Low | High | Pre-check rate limit status; use cached results |

---

## Post-Test Actions

### Success Path

1. **Document Results:** Update this file with actual test results
2. **Logfire Verification:** Query traces for model switching
3. **Update Documentation:** If successful, mark delegation enhancements as verified
4. **Close Issue:** `bd close <issue-id>` for delegation test

### Failure Path

1. **Capture Logs:** Save agent output and Logfire traces
2. **Identify Root Cause:** Was delegation guidance ignored? Model routing issue?
3. **File Issue:** Create follow-up issue with reproduction steps
4. **Update Status:** Mark delegation enhancements as "needs fixes"

---

## Appendix: Quick Reference Commands

### Check Agent Availability

```python
from code_puppy.agents.agent_manager import AgentManager
mgr = AgentManager()
for name in ['epistemic-architect', 'security-auditor', 'code-reviewer', 
             'qa-expert', 'python-programmer', 'test-generator', 'doc-writer']:
    print(f"{name}: {'✅' if name in mgr.list_agents() else '❌'}")
```

### Verify Logfire Delegation

```sql
-- Query Logfire traces for agent invocations
SELECT 
    timestamp,
    agent_name,
    phase,
    model_name,
    duration_ms
FROM agent_invocations
WHERE parent_agent = 'epistemic-architect'
ORDER BY timestamp;
```

### Manual Agent Test

```python
# Test individual agent invocation
from code_puppy.agents.agent_manager import AgentManager
mgr = AgentManager()
result = mgr.invoke_agent("security-auditor", "Review this code for vulnerabilities: def login(): pass")
print(result)
```

---

## Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Test Designer | Richard 🐶 | 2026-02-05 | [AUTO] |
| Reviewer | TBD | | |
| Approver | TBD | | |

---

*This test plan was generated by the Code-Puppy agent system.*

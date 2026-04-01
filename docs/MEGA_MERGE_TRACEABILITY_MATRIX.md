# Code Puppy + Gastown Mega-Merge Traceability Matrix

**Document ID**: TM-2026-04-01-v1
**Planning Agent**: planning-agent-1c636b
**Created**: 2026-04-01
**Last Updated**: 2026-04-01
**Status**: ACTIVE — Phase 0 in progress

---

## Table of Contents

1. [Executive Status Summary](#1-executive-status-summary)
2. [Requirement Traceability Matrix](#2-requirement-traceability-matrix)
3. [Phase 0: Foundation](#3-phase-0-foundation)
4. [Phase 1: Dolt as State Store](#4-phase-1-dolt-as-state-store)
5. [Phase 2: Beads Integration](#5-phase-2-beads-integration)
6. [Phase 3: Dolt User-Facing Tools](#6-phase-3-dolt-user-facing-tools)
7. [Phase 4: Gastown Orchestration](#7-phase-4-gastown-orchestration)
8. [Phase 5: Polish & Patterns](#8-phase-5-polish--patterns)
9. [Model Duplication Resolution](#9-model-duplication-resolution)
10. [Agent Assignment Registry](#10-agent-assignment-registry)
11. [Risk Register](#11-risk-register)
12. [Dependency Graph](#12-dependency-graph)
13. [Sign-Off Log](#13-sign-off-log)

---

## 1. Executive Status Summary

| Phase | Plan Target | Status | Completion | Blocking? |
|-------|-------------|--------|------------|-----------|
| **Phase 0**: Foundation | Weeks 1-2 | 🟡 In Progress | **~70%** | No |
| **Phase 1**: Dolt State Store | Weeks 3-4 | 🔴 Not Started | **0%** | Yes — blocks Phase 3 |
| **Phase 2**: Beads Integration | Weeks 5-6 | 🟡 Partial | **~40%** | Yes — blocks Phase 4 |
| **Phase 3**: Dolt User Tools | Weeks 7-8 | 🔴 Not Started | **0%** | Blocked by Phase 1 |
| **Phase 4**: Gastown Orchestration | Weeks 9-12 | 🟡 Models Only | **~25%** | Blocked by Phase 2 |
| **Phase 5**: Polish & Patterns | Weeks 13-14 | 🔴 Not Started | **~10%** | Blocked by all |

### Critical Findings

1. **Model Duplication**: 3 separate model sets for Gastown concepts (see §9)
2. **No beads_client in bridges/**: Plan requires it; only legacy plugin-level client exists
3. **Execution Gap = 100%**: All models/bridges exist; zero execution logic implemented
4. **Test Debt**: 77 KB of bridge code (dolt_client + go_binary_manager) has zero tests

---

## 2. Requirement Traceability Matrix

### Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Complete — code exists, tested, reviewed |
| ✅⚠️ | Complete but needs attention (untested, wrong pattern, etc.) |
| 🟡 | Partial — some code exists, incomplete |
| 🔴 | Not started |
| 🔵 | Blocked by dependency |
| N/A | Not applicable |

---

## 3. Phase 0: Foundation

**Plan Target**: Get Go binaries managed and callable from Python
**Overall Status**: 🟡 ~70% Complete

### 3.1 Existing Components (Layer 1 — Keep As-Is)

| Req ID | Requirement | Status | Location | Tests | Agent Assigned | Sign-Off |
|--------|-------------|--------|----------|-------|----------------|----------|
| P0-L1-001 | 65+ LLM providers | ✅ | `model_factory.py`, `failover_model.py` | ✅ Extensive | N/A (keep) | — |
| P0-L1-002 | 50+ tools | ✅ | `tools/` (46 files, 683.5 KB) | ✅ Extensive | N/A (keep) | — |
| P0-L1-003 | 30 agent types | ✅ | `agents/` (26 files, 338 KB) | ✅ | N/A (keep) | — |
| P0-L1-004 | BART epistemic system | ✅ | `epistemic/` | ✅ | N/A (keep) | — |
| P0-L1-005 | Token management | ✅ | `core/token_budget.py`, `tools/token_*` | ✅ | N/A (keep) | — |
| P0-L1-006 | Rich CLI/TUI | ✅ | `cli_runner.py` (45.7 KB) | ✅ | N/A (keep) | — |
| P0-L1-007 | Plugin callback system | ✅ | `plugins/__init__.py`, `callbacks.py` | ✅ | N/A (keep) | — |
| P0-L1-008 | Custom commands | ✅ | `plugins/customizable_commands/` | ✅ | N/A (keep) | — |
| P0-L1-009 | MCP integration | ✅ | `mcp_/` | ✅ | N/A (keep) | — |
| P0-L1-010 | Beads CLI (bd binary) | ✅ | External Go binary | N/A | N/A (keep) | — |
| P0-L1-011 | Dolt CLI + SQL server | ✅ | External Go binary | N/A | N/A (keep) | — |
| P0-L1-012 | Beads ↔ Dolt integration | ✅ | External (bd uses dolt) | N/A | N/A (keep) | — |
| P0-L1-013 | Rate limit handling | ✅ | `core/rate_limit_failover.py`, `core/circuit_breaker.py` | ✅ | N/A (keep) | — |
| P0-L1-014 | Logfire observability | ✅ | `core/observability.py` | ✅ | N/A (keep) | — |

### 3.2 In-Repo Partial Implementations

| Req ID | Requirement | Status | Location | What Exists | What's Missing | Tests | Agent Assigned | Sign-Off |
|--------|-------------|--------|----------|-------------|----------------|-------|----------------|----------|
| P0-IR-001 | Orchestra plugin models | ✅⚠️ | `plugins/orchestra/models/` (5 files) | AgentRole, AgentState, AgentIdentity, AgentSession, Rig, RigState, RigConfig, Convoy, ConvoyState, ConvoyPriority, Hook, HookState, Mail, MailPriority, MailStatus | Uses dataclasses not Pydantic v2; duplicates bridges models | 🔴 None | **husky** | ⬜ |
| P0-IR-002 | Orchestra tool registration | 🟡 | `plugins/orchestra/register_callbacks.py` (9.2 KB) | `orchestra_rig_list`, `orchestra_rig_create`, `orchestra_spawn_agent`, `orchestra_convoy_create`, `orchestra_send_mail` + slash commands | All tools are placeholders; spawn/convoy/mail return hardcoded strings | 🔴 None | **husky** | ⬜ |
| P0-IR-003 | Orchestra RigManager | 🟡 | `plugins/orchestra/rig/manager.py` (6.9 KB) | Singleton, JSON persistence, create/list/get/delete rigs | Not connected to gastown_client bridge; no git worktree ops | 🔴 None | **husky** | ⬜ |
| P0-IR-004 | BeadsClient (plugin) | ✅⚠️ | `plugins/beads_tracker/client.py` (9.7 KB) | Full `bd` CLI wrapper: create, show, list, ready, update, close, dep_add/remove/list, formula_list, cook, mol_pour, prime, compact, status | Uses dataclasses, sync subprocess, `from_dict()` — not async, not Pydantic v2 | 🔴 None | **husky** | ⬜ |
| P0-IR-005 | Beads tool registration | ✅ | `plugins/beads_tracker/register_callbacks.py` | `bd_ready`, `bd_create`, `bd_show`, `bd_claim`, `bd_close`, `bd_dep_add`, `bd_list` + slash commands | Missing `bd_search`, `bd_molecule` | 🔴 None | **husky** | ⬜ |
| P0-IR-006 | Formulas plugin templates | ✅ | `plugins/formulas/templates/` | 4 TOML templates: code_review, tdd_cycle, design_doc, release | No execution engine, no variable interpolation, no step tracking | 🔴 None | **husky** | ⬜ |
| P0-IR-007 | Dashboard plugin skeleton | 🟡 | `plugins/dashboard/register_callbacks.py` | Slash commands, placeholder tools (`dashboard_open`, `feed_events`) | No TUI, no real-time feed, no agent tree | 🔴 None | **husky** | ⬜ |
| P0-IR-008 | Research docs | ✅ | `research/` (8 files, 99 KB) | Architecture analysis, key concepts, design principles, recommendations | Informational only | N/A | N/A | ✅ |

### 3.3 Phase 0 New Development

| Req ID | Requirement | Status | Location | Details | Tests | Agent Assigned | Reviewer | Sign-Off |
|--------|-------------|--------|----------|---------|-------|----------------|----------|----------|
| P0-NEW-001 | `bridges/` package init | ✅ | `bridges/__init__.py` (1.4 KB) | Exports GoBinaryManager, DoltClient, GastownClient + all models/exceptions | N/A | code-puppy | python-reviewer | ✅ |
| P0-NEW-002 | `go_binary_manager.py` | ✅⚠️ | `bridges/go_binary_manager.py` (19.9 KB) | GoBinaryManager, BinaryConfig, BinaryInfo; resolves bd/dolt/gt; npm/github/system install; version check | 🔴 **No tests** | code-puppy | python-reviewer | ⬜ Needs tests |
| P0-NEW-003 | `dolt_client/` package | ✅⚠️ | `bridges/dolt_client/` (10 files, 57.5 KB) | Full async client: SQL, branches, commits, diffs, remotes, tables, server mgmt. Pydantic v2 models. | 🔴 **No tests** | code-puppy | python-reviewer, security-auditor | ⬜ Needs tests |
| P0-NEW-004 | `gastown_client/` package | ✅ | `bridges/gastown_client/` (13 files, 42.2 KB) | Mixin architecture: convoy, polecat, rig, hook, mail, escalation, utility. Semaphore, timeout clamping, options allowlists, `--` sentinel. | ✅ `test_gastown_client.py` (68 tests) | code-puppy | python-reviewer, security-auditor | ✅ Reviewed + tested |
| P0-NEW-005 | `bridges/models/` package | ✅⚠️ | `bridges/models/` (4 files, 30.1 KB) | Pydantic v2: beads_models, dolt_models, gastown_models | 🔴 **No tests**; gastown_models **duplicates** gastown_client/models.py | code-puppy | python-reviewer | ⬜ Needs dedup |
| P0-NEW-006 | BeadsClient in bridges | 🔴 | `bridges/beads_client/` — **DOES NOT EXIST** | Plan requires async Pydantic v2 wrapper mirroring gastown_client pattern | 🔴 | **husky** | python-reviewer, security-auditor | ⬜ |
| P0-NEW-007 | Pydantic v2 BeadsClient upgrade | 🔴 | — | Legacy `plugins/beads_tracker/client.py` uses dataclasses + sync subprocess | — | **husky** | python-reviewer | ⬜ |
| P0-NEW-008 | Graceful degradation at startup | 🟡 | `go_binary_manager.py`, `gastown_client` | Individual checks exist; no unified startup feature-gating | 🔴 | **husky** | python-reviewer | ⬜ |
| P0-NEW-009 | Integration tests: Python→Go→parse | 🟡 | `tests/test_gastown_client.py` (68 tests, mock-only) | gastown_client tested; dolt_client, go_binary_manager untested | 🔴 Partial | **husky** | qa-expert | ⬜ |
| P0-NEW-010 | test_dolt_client.py | 🔴 | `tests/test_dolt_client.py` — **DOES NOT EXIST** | 57.5 KB of untested code | 🔴 | **husky** | qa-expert, python-reviewer | ⬜ |
| P0-NEW-011 | test_go_binary_manager.py | 🔴 | `tests/test_go_binary_manager.py` — **DOES NOT EXIST** | 19.9 KB of untested code | 🔴 | **husky** | qa-expert, python-reviewer | ⬜ |

---

## 4. Phase 1: Dolt as State Store

**Plan Target**: Replace JSON/SQLite with Dolt for all persistent state
**Overall Status**: 🔴 0% Complete
**Blocks**: Phase 3 (Dolt User Tools), Phase 5 (Polish)
**Depends On**: Phase 0 (dolt_client ✅)

| Req ID | Requirement | Status | Location | Details | Tests | Agent Assigned | Reviewer | Sign-Off |
|--------|-------------|--------|----------|---------|-------|----------------|----------|----------|
| P1-001 | Dolt schema: `agent_sessions` | 🔴 | `schemas/sessions.sql` — DNE | Conversation history, token usage per session | 🔴 | **husky** | solutions-architect | ⬜ |
| P1-002 | Dolt schema: `agent_memory` | 🔴 | `schemas/agent_memory.sql` — DNE | Persistent context per agent identity | 🔴 | **husky** | solutions-architect | ⬜ |
| P1-003 | Dolt schema: `tool_results` | 🔴 | `schemas/tool_results.sql` — DNE | Cached tool outputs with versioning | 🔴 | **husky** | solutions-architect | ⬜ |
| P1-004 | Dolt schema: `config_state` | 🔴 | `schemas/config_state.sql` — DNE | Runtime configuration snapshots | 🔴 | **husky** | solutions-architect | ⬜ |
| P1-005 | Dolt schema: `cost_tracking` | 🔴 | `schemas/cost_tracking.sql` — DNE | Per-session, per-model cost history | 🔴 | **husky** | solutions-architect | ⬜ |
| P1-006 | Schema migration system | 🔴 | `schemas/migrations/` — DNE | Version upgrades, initial creation, data migration | 🔴 | **husky** | solutions-architect | ⬜ |
| P1-007 | `DoltStateProvider` class | 🔴 | `core/dolt_state_provider.py` — DNE | Replaces `session_storage.py` (10.7 KB); same interface, Dolt backend | 🔴 | **husky** | python-reviewer, solutions-architect | ⬜ |
| P1-008 | Auto-commit on session changes | 🔴 | — | Session changes become Dolt commits | 🔴 | **husky** | python-reviewer | ⬜ |
| P1-009 | Branch-per-conversation | 🔴 | — | Parallel conversations on separate Dolt branches | 🔴 | **husky** | solutions-architect | ⬜ |
| P1-010 | `dolt_time_travel` tool | 🔴 | `tools/dolt_tools.py` — DNE | Agent tool to query historical state | 🔴 | **husky** | python-reviewer | ⬜ |
| P1-011 | Fallback chain: Dolt→SQLite→JSON | 🔴 | `core/graceful_degradation.py` — DNE | Multi-level fallback when Dolt unavailable | 🔴 | **husky** | python-reviewer, qa-expert | ⬜ |

---

## 5. Phase 2: Beads Integration

**Plan Target**: Full issue tracking and workflow management
**Overall Status**: 🟡 ~40% Complete
**Blocks**: Phase 4 (Gastown Orchestration)
**Depends On**: Phase 0 (BeadsClient)

| Req ID | Requirement | Status | Location | Details | Tests | Agent Assigned | Reviewer | Sign-Off |
|--------|-------------|--------|----------|---------|-------|----------------|----------|----------|
| P2-001 | BeadsClient CLI wrapper | ✅⚠️ | `plugins/beads_tracker/client.py` (9.7 KB) | All bd commands wrapped; dataclass-based, sync | 🔴 | **husky** | python-reviewer | ⬜ Needs Pydantic upgrade |
| P2-002 | Bead tools registered | ✅ | `plugins/beads_tracker/register_callbacks.py` | 7 tools: bd_ready, bd_create, bd_show, bd_claim, bd_close, bd_dep_add, bd_list | 🔴 | N/A (keep) | — | ✅ |
| P2-003 | Slash commands /bd, /beads | ✅ | `plugins/beads_tracker/register_callbacks.py` | Working | N/A | N/A (keep) | — | ✅ |
| P2-004 | `bd prime` → system prompt injection | 🔴 | — | **Highest-value single missing item**. Run `bd prime` on session start and inject context into agent system prompts. | 🔴 | **husky** | python-reviewer, security-auditor | ⬜ |
| P2-005 | `bd_search` tool | 🔴 | — | Not yet registered | 🔴 | **husky** | python-reviewer | ⬜ |
| P2-006 | Molecule execution engine | 🔴 | — | Map formulas to `bd mol pour/wisp/squash`; variable interpolation; step tracking | 🔴 | **husky** | python-reviewer | ⬜ |
| P2-007 | Atomic claiming → Pack Leader | 🔴 | — | When Pack Leader assigns work, call `bd claim`. Modify `agent_pack_leader.py` | 🔴 | **husky** | python-reviewer | ⬜ |
| P2-008 | Gates → circuit breaker | 🔴 | — | Blocked gates = circuit open. Integrate with `core/circuit_breaker.py` | 🔴 | **husky** | python-reviewer | ⬜ |
| P2-009 | `bd_molecule` tool | 🔴 | — | Workflow execution from agents | 🔴 | **husky** | python-reviewer | ⬜ |
| P2-010 | JSON schema compatibility testing | 🔴 | — | Test all tools against current bd CLI version | 🔴 | **husky** | qa-expert | ⬜ |

---

## 6. Phase 3: Dolt User-Facing Tools

**Plan Target**: Agents can help users with versioned data operations
**Overall Status**: 🔴 0% Complete
**Blocks**: Phase 5
**Depends On**: Phase 1 (DoltStateProvider)

| Req ID | Requirement | Status | Location | Details | Tests | Agent Assigned | Reviewer | Sign-Off |
|--------|-------------|--------|----------|---------|-------|----------------|----------|----------|
| P3-001 | `tools/dolt_tools.py` | 🔴 | DNE | `dolt_query`, `dolt_branch`, `dolt_diff`, `dolt_commit`, `dolt_merge` agent tools | 🔴 | **husky** | python-reviewer, security-auditor | ⬜ |
| P3-002 | Data Analysis Agent | 🔴 | `agents/agent_data_analyst.py` — DNE | Specialized agent combining Dolt SQL + LLM reasoning | 🔴 | **agent-creator** | python-reviewer | ⬜ |
| P3-003 | `dolt sql-server` mgmt as tool | 🟡 | `bridges/dolt_client/server.py` (7.8 KB) | `DoltSQLServerManager` exists but not exposed as agent tool | 🔴 | **husky** | python-reviewer | ⬜ |
| P3-004 | Data branching workflows | 🔴 | — | Branch → experiment → merge/discard from agents | 🔴 | **husky** | solutions-architect | ⬜ |
| P3-005 | Import/export tools | 🟡 | `bridges/dolt_client/table_ops.py` | `export_table()` supports csv/json/parquet/sql; not agent-accessible | 🔴 | **husky** | python-reviewer | ⬜ |
| P3-006 | Permission framework for data ops | 🔴 | — | `isDestructive()`, `isReadOnly()` on new Dolt tools | 🔴 | **husky** | security-auditor | ⬜ |

---

## 7. Phase 4: Gastown Orchestration

**Plan Target**: Multi-agent coordination at scale
**Overall Status**: 🟡 ~25% (models only, zero execution)
**Depends On**: Phase 2 (Beads Integration)

| Req ID | Requirement | Status | Location | Details | Tests | Agent Assigned | Reviewer | Sign-Off |
|--------|-------------|--------|----------|---------|-------|----------------|----------|----------|
| P4-001 | Convoy model + state machine | ✅⚠️ | `plugins/orchestra/models/convoy.py` (6.0 KB) | Full state machine: FORMING→MOUNTAIN→DISPATCHING→ACTIVE→STALLED→COMPLETING→ARCHIVED. Dataclass-based. | 🔴 | N/A (exists) | — | ⬜ Needs Pydantic migration |
| P4-002 | Agent role/state/identity models | ✅⚠️ | `plugins/orchestra/models/agent_role.py` (5.3 KB) | AgentRole, AgentState, AgentIdentity, AgentSession. Dataclass-based. | 🔴 | N/A (exists) | — | ⬜ Needs Pydantic migration |
| P4-003 | Rig model + RigConfig | ✅⚠️ | `plugins/orchestra/models/rig.py` (4.6 KB) | Rig, RigState, RigConfig with dataclass to_dict/from_dict | 🔴 | N/A (exists) | — | ⬜ Needs Pydantic migration |
| P4-004 | Hook model | ✅⚠️ | `plugins/orchestra/models/hook.py` (4.9 KB) | Hook, HookState with work/mail/state path helpers | 🔴 | N/A (exists) | — | ⬜ Needs Pydantic migration |
| P4-005 | Mail model | ✅⚠️ | `plugins/orchestra/models/mail.py` (4.8 KB) | Mail, MailPriority, MailStatus with send/read/reply helpers | 🔴 | N/A (exists) | — | ⬜ Needs Pydantic migration |
| P4-006 | GastownClient bridge | ✅ | `bridges/gastown_client/` (42.2 KB) | Full async client for all gt CLI commands | ✅ 68 tests | code-puppy | python-reviewer, security-auditor | ✅ |
| P4-007 | Orchestra tool stubs | 🟡 | `plugins/orchestra/register_callbacks.py` | 5 tools registered but return placeholder strings | 🔴 | **husky** | python-reviewer | ⬜ |
| P4-008 | **Hook execution engine** | 🔴 | DNE | Git worktree creation/management, context persistence, hook lifecycle (create→activate→archive) | 🔴 | **husky** | solutions-architect, security-auditor | ⬜ |
| P4-009 | **AgentSpawner** | 🔴 | DNE | Launch Code Puppy agents as subprocesses with polecat identity; support claude/codex/cursor runtimes | 🔴 | **husky** | solutions-architect, security-auditor | ⬜ |
| P4-010 | **Convoy execution engine** | 🔴 | DNE | State machine driver, bead assignment, progress tracking, stall detection, completion handling | 🔴 | **husky** | python-reviewer, qa-expert | ⬜ |
| P4-011 | **Mail delivery system** | 🔴 | DNE | Queue, delivery mechanism, inbox management | 🔴 | **husky** | python-reviewer | ⬜ |
| P4-012 | Capacity governance merge | 🔴 | — | Merge Pack Leader rate limits with Gastown capacity governor | 🔴 | **husky** | python-reviewer | ⬜ |
| P4-013 | Escalation routing | 🔴 | — | P0/P1/P2 → invoke appropriate expert agent | 🔴 | **husky** | python-reviewer | ⬜ |
| P4-014 | Seance (predecessor context) | 🔴 | — | Query predecessor agent context for session inheritance | 🔴 | **husky** | python-reviewer | ⬜ |
| P4-015 | Witness monitoring | 🔴 | — | Per-rig health checks | 🔴 | **husky** | qa-expert | ⬜ |
| P4-016 | Deacon supervision | 🔴 | — | Cross-rig oversight | 🔴 | **husky** | qa-expert | ⬜ |
| P4-017 | Dashboard TUI implementation | 🔴 | `plugins/dashboard/` (skeleton only) | Real-time event feed, agent tree view, convoy panel | 🔴 | **husky** | experience-architect | ⬜ |
| P4-018 | `tools/gastown_tools.py` | 🔴 | DNE | `gt_convoy_create`, `gt_polecat_spawn`, `gt_escalate`, `gt_seance`, `gt_rig_status` | 🔴 | **husky** | python-reviewer | ⬜ |
| P4-019 | `tools/beads_tools.py` (bridge-level) | 🔴 | DNE | `beads_create`, `beads_ready`, `beads_claim`, `beads_close`, `beads_search`, `beads_molecule` | 🔴 | **husky** | python-reviewer | ⬜ |
| P4-020 | Convoy Coordinator Agent | 🔴 | `agents/agent_convoy_coordinator.py` — DNE | Bridges Pack Leader + Convoy system + Beads task tracking | 🔴 | **agent-creator** | python-reviewer | ⬜ |

---

## 8. Phase 5: Polish & Patterns

**Plan Target**: Borrow Claude Code patterns, harden the system
**Overall Status**: 🔴 ~10% Complete
**Depends On**: All previous phases

| Req ID | Requirement | Status | Location | Details | Tests | Agent Assigned | Reviewer | Sign-Off |
|--------|-------------|--------|----------|---------|-------|----------------|----------|----------|
| P5-001 | Parallel startup optimization | 🔴 | — | Prefetch Go binary health, Dolt warmup, Beads context in parallel. Target <500ms. | 🔴 | **husky** | python-reviewer | ⬜ |
| P5-002 | Graceful degradation (full) | 🟡 | Partial in go_binary_manager, gastown_client | Dolt→SQLite→JSON; Beads→markdown lists; Gastown→local Pack agents | 🔴 | **husky** | python-reviewer, qa-expert | ⬜ |
| P5-003 | Permission framework for new tools | 🔴 | — | `isDestructive()`, `isReadOnly()`, `isConcurrencySafe()` on Dolt/Beads/Gastown tools | 🔴 | **husky** | security-auditor | ⬜ |
| P5-004 | Cost tracking in Dolt | 🔴 | — | Extend `core/cost_budget.py` to persist to Dolt | 🔴 | **husky** | python-reviewer | ⬜ |
| P5-005 | Unified config system | 🔴 | `core/unified_config.py` — DNE | Merge puppy.cfg + ~/.gt/ + .beads/config.yaml into single hierarchy | 🔴 | **husky** | solutions-architect | ⬜ |
| P5-006 | Comprehensive bridge test suite | 🟡 | `tests/test_gastown_client.py` only | Need test_dolt_client, test_go_binary_manager, test_beads_client | 🔴 Partial | **husky** | qa-expert | ⬜ |
| P5-007 | `bd prime` context injection | 🔴 | — | Auto-inject into system prompts: git status + `bd prime` + Dolt branch + rig hooks | 🔴 | **husky** | python-reviewer | ⬜ |
| P5-008 | Dolt-backed session/history | 🔴 | — | Dedup, hash-based paste storage, session-aware retrieval | 🔴 | **husky** | solutions-architect | ⬜ |
| P5-009 | Config Unifier | 🔴 | `core/unified_config.py` — DNE | Hierarchical config: Code Puppy authoritative, Gastown/Beads read-only | 🔴 | **husky** | solutions-architect | ⬜ |
| P5-010 | Cross-Language Event Bus | 🔴 | `core/cross_lang_events.py` — DNE | Python↔Go IPC via named pipes/unix sockets/gRPC | 🔴 | **husky** | solutions-architect, security-auditor | ⬜ |
| P5-011 | Wasteland Federation Client | 🔴 | — | Python client for Gastown federated coordination via DoltHub | 🔴 | **husky** | solutions-architect | ⬜ |

---

## 9. Model Duplication Resolution

### Problem Statement

Three separate model definitions exist for the **same Gastown/Orchestra concepts**:

| Location | Pattern | Models Defined | Used By |
|----------|---------|----------------|---------|
| **A**: `plugins/orchestra/models/` | `@dataclass` + `to_dict/from_dict` | AgentRole, AgentState, AgentIdentity, AgentSession, Rig, RigState, RigConfig, Convoy, ConvoyState, ConvoyPriority, Hook, HookState, Mail, MailPriority, MailStatus | Orchestra plugin, RigManager |
| **B**: `bridges/gastown_client/models.py` | Pydantic v2 `BaseModel` | Convoy, ConvoyState, ConvoyPriority, Polecat, PolecatRole, PolecatState, Rig, RigState, Hook, HookState, Mail, MailStatus, MailPriority, Escalation, EscalationSeverity, CommandResult | GastownClient bridge |
| **C**: `bridges/models/gastown_models.py` | Pydantic v2 `BaseModel` | Polecat, Convoy, Rig, Hook, Mail, AgentRole, AgentState, ConvoyState, Escalation | Bridges models package |

### Resolution Plan

| Step | Action | Agent | Reviewer |
|------|--------|-------|----------|
| 9.1 | Designate **B** (`bridges/gastown_client/models.py`) as canonical — it has UTC-aware timestamps, most complete fields, Pydantic v2 | planning-agent | — |
| 9.2 | Merge any unique fields from **A** into **B** (e.g., `AgentIdentity`, `AgentSession`, `RigConfig`, `completed_beads`, `progress_pct`, `mail_inbox`) | **husky** | python-reviewer |
| 9.3 | Update **A** (`plugins/orchestra/models/`) to re-export from **B**. Keep backward-compatible aliases. | **husky** | python-reviewer |
| 9.4 | Delete **C** (`bridges/models/gastown_models.py`) or reduce to re-exports from **B** | **husky** | python-reviewer |
| 9.5 | Update all imports across codebase (`orchestra/register_callbacks.py`, `rig/manager.py`) | **husky** | python-reviewer |
| 9.6 | Run full test suite to verify no breakage | **husky** | qa-expert |

**Req ID**: P0-DEDUP-001 through P0-DEDUP-006

---

## 10. Agent Assignment Registry

### Primary Agents (Build)

| Agent | Role | Assigned Req IDs | Workload |
|-------|------|-------------------|----------|
| **husky** 🐺 | Heavy-lift executor | P0-NEW-006 through P0-NEW-011, P1-001 through P1-011, P2-004 through P2-010, P3-001/003/004/005, P4-007 through P4-019, P5-001 through P5-011, P0-DEDUP-002 through P0-DEDUP-006 | **~65 tasks** (primary workhorse) |
| **code-puppy** 🐶 | Foundation builder | P0-NEW-001 through P0-NEW-005 (done), any husky-overflow tasks | ~5 tasks (done) |
| **agent-creator** 🏗️ | New agent specs | P3-002 (Data Analysis Agent), P4-020 (Convoy Coordinator Agent) | 2 tasks |
| **planning-agent** 📋 | Coordination | This document, task prioritization, phase gate reviews | Ongoing |

### Review Agents (Quality Gate)

| Agent | Role | Reviews | Quality Gate |
|-------|------|---------|--------------|
| **python-reviewer** 🐍 | Code quality | ALL Python code changes | Idiomatic Python, type safety, async patterns |
| **security-auditor** 🛡️ | Security review | P0-NEW-003, P0-NEW-004, P2-004, P3-006, P4-008, P4-009, P5-003, P5-010 | CWE analysis, injection prevention, subprocess safety |
| **qa-expert** 🐾 | Test coverage | P0-NEW-009/010/011, P2-010, P4-010/015/016, P5-002/006 | Test adequacy, edge cases, coverage gaps |
| **solutions-architect** 🏛️ | Architecture review | P1-001 through P1-009, P3-004, P4-008/009, P5-005/008/009/010/011 | Schema design, state management, IPC patterns |
| **experience-architect** 🎨 | UX review | P4-017 (Dashboard TUI) | TUI design, accessibility |
| **shepherd** 🐕 | Code review critic | Any PR-level reviews during implementation | General code quality |

### Sign-Off Authority

Each requirement needs **THREE** sign-offs to be marked complete:

1. **Builder** — Agent that wrote the code (typically husky or code-puppy)
2. **Reviewer** — Assigned review agent (python-reviewer, security-auditor, etc.)
3. **Tester** — Agent that verified tests pass (qa-expert or the builder if self-tested)

---

## 11. Risk Register

| Risk ID | Risk | Impact | Likelihood | Phase(s) | Mitigation | Owner |
|---------|------|--------|------------|----------|------------|-------|
| R-001 | Model duplication causes import conflicts during migration | High | High | P0, P4 | Resolve in P0 before any Phase 4 work (§9) | planning-agent |
| R-002 | Go binary distribution fails on some platforms | High | Medium | P0 | npm package fallback; manual install docs | husky |
| R-003 | Dolt cold start >2s breaks startup target | Medium | Medium | P1, P5 | Lazy init; parallel startup (P5-001) | husky |
| R-004 | IPC overhead Python↔Go subprocess per command | Medium | Medium | P0, P4 | Batch commands; `dolt sql-server` for SQL (persistent conn) | husky |
| R-005 | Config conflicts between 3 config systems | Low | Medium | P5 | Clear hierarchy: Code Puppy authoritative | husky |
| R-006 | Gastown assumes tmux for session mgmt | Medium | Medium | P4 | Abstract session mgmt; support tmux/screen/direct | husky |
| R-007 | 77 KB untested bridge code (dolt_client + go_binary_manager) | High | High | P0 | Prioritize P0-NEW-010 and P0-NEW-011 immediately | husky |
| R-008 | BeadsClient async migration breaks existing tools | Medium | Medium | P0 | Keep legacy client; add bridges-level async client alongside | husky |
| R-009 | Phase 4 execution layer scope creep (10+ items) | High | High | P4 | Strict MVP: Hook engine + Agent spawner first; mail/escalation later | planning-agent |
| R-010 | Rate limiting on external APIs during agent coordination | Medium | High | P4 | Merge capacity governor with existing circuit breakers | husky |

---

## 12. Dependency Graph

```
PHASE 0 — Foundation (70% done)
│
│  P0-NEW-006 (beads_client bridge) ──────────────┐
│  P0-NEW-010 (test_dolt_client) ─────────┐       │
│  P0-NEW-011 (test_go_binary_manager) ──┐│       │
│  P0-DEDUP-001..006 (model dedup) ─────┐││       │
│                                        │││       │
├── PHASE 1 — Dolt State Store ◄─────────┘││       │
│   │  P1-001..006 (schemas)              ││       │
│   │  P1-007 (DoltStateProvider) ◄───────┘│       │
│   │  P1-008..009 (auto-commit, branching)│       │
│   │  P1-010 (dolt_time_travel tool)      │       │
│   │  P1-011 (fallback chain)             │       │
│   │                                      │       │
│   └── PHASE 3 — Dolt User Tools ◄───────┘       │
│       P3-001..006                                │
│                                                  │
├── PHASE 2 — Beads Integration ◄──────────────────┘
│   │  P2-001 (BeadsClient upgrade)
│   │  P2-004 (bd prime injection) ★ HIGHEST VALUE
│   │  P2-005..010 (remaining beads work)
│   │
│   └── PHASE 4 — Gastown Orchestration
│       │  P4-008 (Hook engine) ★ HEAVIEST LIFT
│       │  P4-009 (AgentSpawner) ★ HEAVIEST LIFT
│       │  P4-010 (Convoy engine)
│       │  P4-011..020 (remaining orchestration)
│       │
│       └── PHASE 5 — Polish & Patterns
│           P5-001..011
```

**Critical Path**: P0-NEW-006 → P2-001 → P2-004 → P4-008 → P4-009 → P4-010

**Parallel Track**: P0-NEW-010/011 → P1-001..007 → P3-001 (can run alongside Phase 2)

---

## 13. Sign-Off Log

### Completed Sign-Offs

| Req ID | Requirement | Builder | Build Date | Reviewer | Review Date | Tester | Test Date | Status |
|--------|-------------|---------|------------|----------|-------------|--------|-----------|--------|
| P0-NEW-001 | bridges/ package init | code-puppy | 2026-03-31 | python-reviewer | 2026-03-31 | N/A | N/A | ✅ COMPLETE |
| P0-NEW-004 | gastown_client/ package | code-puppy | 2026-04-01 | python-reviewer, security-auditor | 2026-04-01 | code-puppy (68 tests) | 2026-04-01 | ✅ COMPLETE |
| P0-IR-008 | Research docs | N/A | Pre-existing | N/A | N/A | N/A | N/A | ✅ COMPLETE |

### Pending Sign-Offs

| Req ID | Requirement | Builder | Reviewer | Tester | Blocker |
|--------|-------------|---------|----------|--------|---------|
| P0-NEW-002 | go_binary_manager.py | code-puppy ✅ | python-reviewer ⬜ | qa-expert ⬜ (no tests) | Needs P0-NEW-011 |
| P0-NEW-003 | dolt_client/ package | code-puppy ✅ | python-reviewer ⬜ | qa-expert ⬜ (no tests) | Needs P0-NEW-010 |
| P0-NEW-005 | bridges/models/ package | code-puppy ✅ | python-reviewer ⬜ | qa-expert ⬜ (no tests) | Needs P0-DEDUP |
| P0-IR-001 | Orchestra plugin models | N/A (exists) | — | — | Needs P0-DEDUP |
| P0-IR-004 | BeadsClient (plugin) | N/A (exists) | — | — | Needs P0-NEW-006 |
| P0-NEW-006 | beads_client in bridges | ⬜ | ⬜ | ⬜ | **NEXT PRIORITY** |
| P0-NEW-010 | test_dolt_client.py | ⬜ | ⬜ | ⬜ | **NEXT PRIORITY** |
| P0-NEW-011 | test_go_binary_manager.py | ⬜ | ⬜ | ⬜ | **NEXT PRIORITY** |

---

## Appendix A: File Inventory

### bridges/ (29 files, 151.7 KB)

```
bridges/
├── __init__.py                     (1.4 KB)  — P0-NEW-001 ✅
├── go_binary_manager.py            (19.9 KB) — P0-NEW-002 ✅⚠️
├── dolt_client/                    (57.5 KB) — P0-NEW-003 ✅⚠️
│   ├── __init__.py, client.py, models.py, exceptions.py
│   ├── branch_ops.py, commit_ops.py, diff_ops.py
│   ├── remote_ops.py, table_ops.py, server.py
├── gastown_client/                 (42.2 KB) — P0-NEW-004 ✅
│   ├── __init__.py, client.py, models.py, exceptions.py, helpers.py
│   └── mixins/ (convoy, polecat, rig, hook, mail, escalation, utility)
├── models/                         (30.1 KB) — P0-NEW-005 ✅⚠️ (has duplicates)
│   ├── beads_models.py, dolt_models.py, gastown_models.py
└── beads_client/                   — P0-NEW-006 🔴 DOES NOT EXIST
```

### plugins/ relevant (4 plugins)

```
plugins/
├── orchestra/          (26.3 KB) — P0-IR-001/002/003, P4-*
├── beads_tracker/      (17.9 KB) — P0-IR-004/005, P2-*
├── formulas/           (9.1 KB)  — P0-IR-006
└── dashboard/          (2.5 KB)  — P0-IR-007, P4-017
```

### tests/ (bridges coverage)

```
tests/
├── test_gastown_client.py   (21.8 KB, 68 tests) — P0-NEW-004 ✅
├── test_dolt_client.py      — 🔴 DOES NOT EXIST
├── test_go_binary_manager.py — 🔴 DOES NOT EXIST
└── test_beads_client.py     — 🔴 DOES NOT EXIST
```

### core/ (planned new files)

```
core/
├── dolt_state_provider.py    — P1-007 🔴 DNE
├── graceful_degradation.py   — P1-011/P5-002 🔴 DNE
├── unified_config.py         — P5-005/009 🔴 DNE
├── cross_lang_events.py      — P5-010 🔴 DNE
└── polecat_identity.py       — P4-009 🔴 DNE
```

### tools/ (planned new files)

```
tools/
├── dolt_tools.py      — P3-001 🔴 DNE
├── beads_tools.py     — P4-019 🔴 DNE
└── gastown_tools.py   — P4-018 🔴 DNE
```

### agents/ (planned new files)

```
agents/
├── agent_data_analyst.py        — P3-002 🔴 DNE
└── agent_convoy_coordinator.py  — P4-020 🔴 DNE
```

### schemas/ (planned new directory)

```
schemas/              — 🔴 ENTIRE DIRECTORY DNE
├── sessions.sql        — P1-001
├── agent_memory.sql    — P1-002
├── tool_results.sql    — P1-003
├── config_state.sql    — P1-004
├── cost_tracking.sql   — P1-005
└── migrations/         — P1-006
```

---

## Appendix B: Success Criteria Traceability

| Success Criterion | Req IDs Required | Current Status |
|-------------------|------------------|----------------|
| 1. CLI starts in <2s with all Go components | P5-001 | 🔴 Not measured |
| 2. Single agent can create/claim/close Beads issues | P2-001, P2-002, P2-007 | 🟡 Tools exist but no atomic claiming |
| 3. Agent history survives restarts (Dolt-backed) | P1-007, P1-008 | 🔴 Still JSON-based |
| 4. Pack Leader can spawn 5-agent convoy via Beads | P4-009, P4-010, P2-007 | 🔴 No agent spawner |
| 5. Agent can branch/analyze/compare data | P3-001, P3-002, P3-004 | 🔴 No user-facing Dolt tools |
| 6. Graceful operation when Go components unavailable | P5-002, P0-NEW-008 | 🟡 Partial checks exist |
| 7. Zero breaking changes to existing commands | All phases | ✅ Current (no breakage yet) |

---

*Document maintained by planning-agent-1c636b. Next review: upon Phase 0 completion.*

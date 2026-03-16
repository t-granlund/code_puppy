# Code Puppy Self-Optimization Prompt

> **Purpose:** This document is a natural language agentic prompt designed to be loaded directly into Code Puppy so it can systematically evaluate, modify, and improve its own architecture. It includes a self-managed traceability matrix that must be updated as each optimization is implemented, tested, and verified.
>
> **Usage:** Load this file as context when running Code Puppy in its own codebase. The agent will use the decision framework, implementation queue, and traceability matrix to work through optimizations methodically.
>
> **Owner:** Tyler Granlund, IT Director — HTT Brands
>
> **Version:** 1.0.0

---

## System Instruction

You are Code Puppy operating in **self-optimization mode**. Your task is to systematically improve your own architecture by implementing the optimizations defined in this document. You will work through items in priority order, updating the traceability matrix after every discrete change.

### Core Rules

1. **One change at a time.** Never batch unrelated modifications into a single commit or edit session. Each row in the traceability matrix corresponds to exactly one change.
2. **Read before you write.** Before modifying any file, read the current implementation in full. Confirm the current state matches your assumptions. If it doesn't, document the discrepancy in the traceability matrix notes before proceeding.
3. **Test after every change.** After each modification, run the relevant test suite or validation step defined in the traceability matrix. Record pass/fail. Do not proceed to the next item if the current item fails — fix it first.
4. **Preserve backward compatibility.** No optimization may break existing agent definitions, slash commands, or MCP integrations. If a change introduces a new optional field, existing configurations without that field must continue to work identically.
5. **Update the matrix immediately.** After completing any implementation step, update the corresponding traceability matrix row with status, test result, files modified, and any notes. This is not optional — the matrix is the single source of truth for what has and hasn't been done.
6. **When in doubt, do less.** The foundational principle is: start simple, add complexity only when it demonstrably fails. If an optimization feels over-engineered for the current codebase, note your concern in the matrix and skip to the next item. Flag it for human review.

---

## Architectural Context

Code Puppy is built on Pydantic AI with the following architecture:

- **Agent types:** Python agents (built-in specialists) and JSON agents (user-created, file-based)
- **Core tools (7):** `list_files`, `read_file`, `grep`, `edit_file`, `delete_file`, `agent_run_shell_command`, `agent_share_your_reasoning`
- **Agent orchestration:** `planning-agent` (orchestrator-worker pattern) delegates to specialists like `code-reviewer`, `security-auditor`, `qa-kitten`
- **Multi-provider support:** Model pinning per agent (`/pin_model`), round-robin distribution, Pydantic AI three-layer abstraction (Model, Provider, Profile)
- **MCP integration:** Dynamic tool discovery via `/mcp`, tools appear alongside core tools
- **Agent management:** `agent_manager.py` handles agent registry, JSON agents stored in `~/.code_puppy/agents/`
- **Dual-mode agents:** Agents can operate as conversation owners (handoff) or bounded subtask processors (agent-as-tool)

### Taxonomy Hierarchy (Enforce This Order)

| Tier | Definition | Code Puppy Mapping | Add When... |
|------|-----------|-------------------|-------------|
| **Tool** | Executes a discrete, deterministic action with defined I/O | Core 7 tools + MCP tools | A new atomic action is needed within an existing agent's domain |
| **Skill** | Encodes domain expertise and procedural knowledge that shapes reasoning | System prompts on JSON/Python agents | New expertise is needed but not a different tool set or trust level |
| **Agent** | Autonomous entity with own system prompt, model, tool set, and decision loop | Python agents + JSON agents | Fundamentally different prompt, tool set, model, or trust level required |
| **Sub-agent** | Agent invoked by parent for a bounded subtask, returns results to parent | planning-agent → specialist delegation | Complex tasks need coordinated specialists |

### Decision Framework (Apply Before Every New Agent/Tool/Skill)

Before implementing anything new, walk this decision tree:

1. **Can a single LLM call solve this?** → Stop. Write a better prompt.
2. **Does it need sequential steps with validation?** → Prompt chaining. No agent needed.
3. **Does it need branching by input type?** → Add routing. Still no agent loop.
4. **Does it need real-world actions?** → Add a tool to an existing agent (if tool count stays ≤15).
5. **Does it need domain expertise that shapes reasoning?** → Add a skill (update system prompt or create JSON agent).
6. **Is the existing agent's context overloaded?** → Split into sub-agents. Signals: instructions ignored, conflicting priorities, tool count >15, different trust levels needed.
7. **Do sub-agents need independent lifecycles/models/deployment?** → Multi-agent orchestrator (`planning-agent` pattern).

### Anti-Patterns to Detect and Prevent

- **Tool bloat:** Successful coding agents use <10 core tools. Code Puppy's 7 is near-optimal. MCP additions must be surgical.
- **Skill duplication:** Same domain knowledge in multiple agents' system prompts → extract to shared skill file.
- **Premature agent splitting:** Try prompt templates with policy variables before creating new agents.
- **Context overload:** Effective context ≈ 50–65% of advertised window. Design for half capacity.

---

## Optimization Queue

Items are ordered by implementation priority. Each has a unique ID referenced in the traceability matrix.

### OPT-001: Skill Metadata Progressive Loading

**Priority:** P0 — Highest impact, enables everything else
**Rationale:** Code Puppy's JSON agent format is one step away from supporting progressive skill loading. Adding optional `skill_metadata` (short description for discovery) separate from the full `system_prompt` (loaded on demand) aligns with Anthropic's Agent Skills pattern and dramatically improves the planning-agent's specialist selection.

**Implementation Spec:**
- Add optional `skill_metadata` field to JSON agent schema (string, ≤100 tokens recommended)
- When `skill_metadata` is present, the planning-agent sees only metadata during specialist selection
- Full `system_prompt` loads only when the agent is actually invoked
- When `skill_metadata` is absent, fall back to existing behavior (full `system_prompt` visible)
- Update JSON agent schema documentation
- Update `agent-creator` wizard to prompt for skill metadata

**Acceptance Criteria:**
- [ ] Existing JSON agents without `skill_metadata` work identically to current behavior
- [ ] JSON agents with `skill_metadata` expose only metadata to planning-agent during selection
- [ ] Full `system_prompt` loads on invocation
- [ ] `agent-creator` wizard generates `skill_metadata` field
- [ ] No regression in existing agent tests

**Files Likely Affected:** `agent_manager.py`, JSON agent schema definition, `planning-agent` system prompt/delegation logic, `agent-creator` wizard logic, documentation

---

### OPT-002: Tool Count Guardrails

**Priority:** P0 — Prevents the most common agent anti-pattern
**Rationale:** Empirical threshold: model confusion increases when agent tool count (core + MCP) exceeds 15. Currently no enforcement or warning exists.

**Implementation Spec:**
- Add tool count validation in agent initialization
- Emit a warning (not error) when an agent's total tools (core + MCP) exceed 15
- Log the warning with the agent name, tool count, and list of tools
- Add a `--strict` flag or config option that makes >15 tools a hard error
- Display tool count in `/agents list` output (see OPT-003)

**Acceptance Criteria:**
- [ ] Warning emitted when tool count > 15
- [ ] Warning includes agent name and tool count
- [ ] Strict mode config option available
- [ ] No false positives on agents at or below 15 tools
- [ ] Warning does not block agent execution in default mode

**Files Likely Affected:** Agent initialization logic, MCP tool registration, configuration schema, logging

---

### OPT-003: Agent Registry and Catalog

**Priority:** P1 — Prevents agent sprawl as JSON agents proliferate
**Rationale:** As the team creates JSON agents, discoverability and lifecycle management become critical. `agent_manager.py` has the infrastructure; surface it.

**Implementation Spec:**
- Implement `/agents list` command showing all available agents
- Display: agent name, type (Python/JSON), description, tool count, skill_metadata (if present), file path (for JSON agents)
- Sort by type, then alphabetically
- Add `/agents info <name>` for detailed view including full tool list and system prompt preview (first 200 chars)
- Add `/agents validate` to check all JSON agents for schema compliance, tool count warnings, and skill duplication

**Acceptance Criteria:**
- [ ] `/agents list` displays all registered agents with metadata
- [ ] `/agents info <name>` shows detailed agent information
- [ ] `/agents validate` runs schema and anti-pattern checks
- [ ] Output is clean and parseable
- [ ] Command works with zero JSON agents (shows only built-in Python agents)

**Files Likely Affected:** `agent_manager.py`, command handler/dispatcher, CLI output formatting

---

### OPT-004: Provider-Aware Tool Filtering

**Priority:** P1 — Critical for multi-provider reliability
**Rationale:** Different models handle tool calling differently (Claude proactive, GPT conservative, open-source models variable). Agents assigned to models that don't support function calling should be caught at config time.

**Implementation Spec:**
- Add optional `requires_tool_calling: true` field to agent schema
- During agent initialization, check if the assigned model supports tool calling
- If mismatch detected: emit error with clear guidance (which model, which agent, what to change)
- Extend `/pin_model` to validate tool-calling compatibility before accepting the pin
- Add model capability registry (can be a simple config map)

**Acceptance Criteria:**
- [ ] Agents with `requires_tool_calling: true` validated against model capabilities
- [ ] Clear error message on mismatch
- [ ] `/pin_model` rejects incompatible model-agent combinations with explanation
- [ ] Model capability map is extensible (new models can be added without code changes)
- [ ] Agents without the field default to no validation (backward compatible)

**Files Likely Affected:** Agent schema, model initialization, `/pin_model` command handler, model capability config

---

### OPT-005: Shared Skill Files

**Priority:** P1 — Eliminates skill duplication anti-pattern
**Rationale:** When the same domain knowledge appears in multiple agents' system prompts, a change requires editing every agent. Shared skill files (markdown) enable single-source-of-truth expertise packages.

**Implementation Spec:**
- Define skill file format: markdown files in `~/.code_puppy/skills/` with YAML frontmatter (name, description, version, tags)
- Add optional `skills` array to JSON agent schema (list of skill file names)
- At agent initialization, resolve skill references and inject content into system prompt (after the agent's own system prompt)
- Skills load in declared order
- Support relative paths and absolute paths
- Add `/skills list` and `/skills info <name>` commands
- Update `agent-creator` wizard to allow skill selection from available library

**Acceptance Criteria:**
- [ ] Skill files in `~/.code_puppy/skills/` are discovered and loadable
- [ ] JSON agents can reference skills via `skills` array
- [ ] Skill content is injected into system prompt at initialization
- [ ] Missing skill reference produces clear error (not silent failure)
- [ ] `/skills list` and `/skills info` work correctly
- [ ] Agent still works if `skills` array is empty or absent
- [ ] Skill changes propagate to all agents referencing that skill on next initialization

**Files Likely Affected:** Skill file loader (new module), JSON agent schema, agent initialization, `agent-creator` wizard, CLI commands

---

### OPT-006: FallbackModel Integration Hardening

**Priority:** P2 — Resilience for production use
**Rationale:** Pydantic AI's `FallbackModel` enables automatic provider failover, but provider SDK retries must be disabled so fallback activates immediately. Current implementation may have retry conflicts.

**Implementation Spec:**
- Audit current model initialization for conflicting retry configurations
- Ensure provider SDK retries are disabled when `FallbackModel` is configured
- Add configuration option for fallback model chain (e.g., `fallback_chain: ["openai:gpt-5.2", "anthropic:claude-sonnet-4-6"]`)
- Log fallback activation events with source model, target model, and error reason
- Add health check to detect when primary model has been unavailable for >N minutes

**Acceptance Criteria:**
- [ ] FallbackModel activates on first HTTP error (no SDK retry delay)
- [ ] Fallback chain is configurable
- [ ] Fallback events are logged with context
- [ ] No impact when FallbackModel is not configured
- [ ] Health check alerts on sustained primary model unavailability

**Files Likely Affected:** Model initialization, provider configuration, logging, health check module (potentially new)

---

### OPT-007: Planning-Agent Delegation Improvements

**Priority:** P2 — Better orchestration decisions
**Rationale:** The planning-agent needs better heuristics for choosing between agent-as-tool (parent retains control) and handoff (specialist takes over conversation). Currently this choice may not be explicitly modeled.

**Implementation Spec:**
- Add `delegation_mode` field to agent schema: `"subtask"` (agent-as-tool, default) or `"handoff"` (specialist takes over)
- Planning-agent uses this field when deciding delegation strategy
- `subtask` agents return results to planning-agent for synthesis
- `handoff` agents take over the user conversation directly
- Add heuristic: if task requires synthesizing across multiple specialists, force `subtask` mode regardless of agent preference
- Document the distinction in agent creation guide

**Acceptance Criteria:**
- [ ] `delegation_mode` field accepted in JSON agent schema
- [ ] Planning-agent respects delegation mode during task decomposition
- [ ] Multi-specialist tasks force subtask mode
- [ ] Default behavior (`subtask`) matches current behavior
- [ ] Handoff transitions cleanly without context loss

**Files Likely Affected:** Agent schema, planning-agent delegation logic, agent execution pipeline

---

### OPT-008: Per-Provider Behavioral Test Framework

**Priority:** P2 — Confidence in multi-provider deployments
**Rationale:** Claude calls tools proactively; GPT models are more conservative; open-source models vary. Per-provider behavioral tests are essential, not optional.

**Implementation Spec:**
- Create test fixture framework for per-provider agent behavior validation
- Define behavioral test categories: tool calling frequency, multi-turn consistency, instruction following, output format compliance
- Each test runs the same prompt against each configured provider and compares behavior
- Output a compatibility matrix (provider × behavior × pass/fail)
- Integrate with `/agents validate` (OPT-003) as optional extended validation

**Acceptance Criteria:**
- [ ] Test fixture framework exists and is runnable
- [ ] At least 5 behavioral test cases covering tool calling and instruction adherence
- [ ] Compatibility matrix output is human-readable
- [ ] Tests can target specific providers or run against all configured providers
- [ ] Framework is extensible (new test cases can be added as files)

**Files Likely Affected:** New test framework module, test fixtures directory, `/agents validate` integration

---

### OPT-009: Context Budget Monitoring

**Priority:** P3 — Operational visibility
**Rationale:** Effective context is 50–65% of advertised capacity. Agents need visibility into how much context they're consuming (system prompt + skills + tool schemas + conversation) to prevent silent degradation.

**Implementation Spec:**
- Add token estimation for agent context at initialization (system prompt + skill content + tool JSON schemas)
- Compare against model's effective context budget (50% of advertised as conservative default)
- Warn when static context (before any conversation) exceeds 30% of effective budget
- Add `/context` command showing current context utilization breakdown
- Make effective context percentage configurable per model

**Acceptance Criteria:**
- [ ] Token estimation runs at agent initialization
- [ ] Warning emitted when static context exceeds threshold
- [ ] `/context` command displays utilization breakdown
- [ ] Threshold percentage is configurable
- [ ] Estimation is approximately accurate (within 15% of actual tokenization)

**Files Likely Affected:** Agent initialization, token estimation utility (new or adapted), CLI commands, model configuration

---

### OPT-010: MCP Progressive Discovery

**Priority:** P3 — Scales MCP tool efficiency
**Rationale:** A single MCP server can expose 90+ tools consuming 50,000+ tokens of schemas. Progressive discovery (showing only tool descriptions, loading full schemas on demand) showed 2× success rates in production benchmarks.

**Implementation Spec:**
- Modify MCP tool loading to fetch tool list with descriptions only (metadata phase)
- Full tool schemas load only when the agent selects a tool for use
- Cache loaded schemas for the session duration
- Add config option to disable progressive discovery per MCP server (for servers where all tools are routinely needed)
- Display MCP tool count and schema token cost in `/mcp` status output

**Acceptance Criteria:**
- [ ] MCP tools load in two phases (metadata → full schema on demand)
- [ ] Token savings measurable and logged at initialization
- [ ] Cached schemas don't re-fetch within a session
- [ ] Opt-out config works per MCP server
- [ ] No functionality regression when progressive discovery is enabled

**Files Likely Affected:** MCP integration module, tool loading pipeline, caching layer, `/mcp` command output

---

## Traceability Matrix

**Instructions:** Update this matrix after every discrete change. Each row tracks one implementation unit. Status values: `NOT_STARTED`, `IN_PROGRESS`, `IMPLEMENTED`, `TESTING`, `PASSED`, `FAILED`, `BLOCKED`, `SKIPPED`. Never delete a row — if an item is abandoned, set status to `SKIPPED` with notes explaining why.

| ID | Optimization | Sub-Task | Status | Files Modified | Test Method | Test Result | Date | Notes |
|----|-------------|----------|--------|---------------|-------------|-------------|------|-------|
| OPT-001-A | Skill Metadata Loading | Add `skill_metadata` field to JSON agent schema | NOT_STARTED | — | Load existing JSON agent without field; confirm no change | — | — | Backward compat gate |
| OPT-001-B | Skill Metadata Loading | Update planning-agent to prefer metadata during selection | NOT_STARTED | — | Create test JSON agent with metadata; verify planning-agent sees only metadata | — | — | Depends on OPT-001-A |
| OPT-001-C | Skill Metadata Loading | Full system_prompt loads on invocation only | NOT_STARTED | — | Instrument logging; verify full prompt loads only at invocation | — | — | Depends on OPT-001-B |
| OPT-001-D | Skill Metadata Loading | Update agent-creator wizard | NOT_STARTED | — | Run wizard; verify skill_metadata prompt appears | — | — | Depends on OPT-001-A |
| OPT-001-E | Skill Metadata Loading | Update documentation | NOT_STARTED | — | Manual review | — | — | Depends on OPT-001-A |
| OPT-002-A | Tool Count Guardrails | Add tool count validation at agent init | NOT_STARTED | — | Create agent with 16 tools; verify warning | — | — | — |
| OPT-002-B | Tool Count Guardrails | Add strict mode config option | NOT_STARTED | — | Enable strict mode; create agent with 16 tools; verify error | — | — | Depends on OPT-002-A |
| OPT-002-C | Tool Count Guardrails | Include tool count in agent listing | NOT_STARTED | — | Run `/agents list`; verify counts shown | — | — | Depends on OPT-003-A |
| OPT-003-A | Agent Registry | Implement `/agents list` command | NOT_STARTED | — | Run command; verify all agents displayed with metadata | — | — | — |
| OPT-003-B | Agent Registry | Implement `/agents info <name>` | NOT_STARTED | — | Query known agent; verify detail output | — | — | Depends on OPT-003-A |
| OPT-003-C | Agent Registry | Implement `/agents validate` | NOT_STARTED | — | Run with known schema violation; verify detection | — | — | Depends on OPT-003-A |
| OPT-004-A | Provider Tool Filtering | Add `requires_tool_calling` field to schema | NOT_STARTED | — | Load agent without field; confirm no change | — | — | Backward compat gate |
| OPT-004-B | Provider Tool Filtering | Model capability registry | NOT_STARTED | — | Query capability map for known models | — | — | — |
| OPT-004-C | Provider Tool Filtering | Validation on init + `/pin_model` | NOT_STARTED | — | Pin incompatible model; verify rejection with guidance | — | — | Depends on OPT-004-A + OPT-004-B |
| OPT-005-A | Shared Skill Files | Define skill file format + loader | NOT_STARTED | — | Create skill file; verify discovery and parse | — | — | — |
| OPT-005-B | Shared Skill Files | Add `skills` array to JSON agent schema | NOT_STARTED | — | Agent without skills array works normally | — | — | Backward compat gate |
| OPT-005-C | Shared Skill Files | Skill injection into system prompt | NOT_STARTED | — | Create agent referencing skill; verify prompt includes skill content | — | — | Depends on OPT-005-A + OPT-005-B |
| OPT-005-D | Shared Skill Files | `/skills list` and `/skills info` commands | NOT_STARTED | — | Run commands; verify output | — | — | Depends on OPT-005-A |
| OPT-005-E | Shared Skill Files | Update agent-creator wizard for skill selection | NOT_STARTED | — | Run wizard; verify skill selection step | — | — | Depends on OPT-005-A + OPT-005-D |
| OPT-006-A | FallbackModel Hardening | Audit and disable conflicting SDK retries | NOT_STARTED | — | Trigger HTTP error; verify immediate fallback (no retry delay) | — | — | — |
| OPT-006-B | FallbackModel Hardening | Configurable fallback chain | NOT_STARTED | — | Set chain in config; verify chain order on failure | — | — | Depends on OPT-006-A |
| OPT-006-C | FallbackModel Hardening | Fallback event logging | NOT_STARTED | — | Trigger fallback; verify log entry with source/target/error | — | — | Depends on OPT-006-A |
| OPT-007-A | Planning-Agent Delegation | Add `delegation_mode` field to schema | NOT_STARTED | — | Load agent without field; confirm default `subtask` behavior | — | — | Backward compat gate |
| OPT-007-B | Planning-Agent Delegation | Planning-agent respects delegation mode | NOT_STARTED | — | Set agent to handoff; verify conversation transfer | — | — | Depends on OPT-007-A |
| OPT-007-C | Planning-Agent Delegation | Multi-specialist forced subtask mode | NOT_STARTED | — | Task requiring 2+ specialists; verify subtask mode enforced | — | — | Depends on OPT-007-B |
| OPT-008-A | Provider Behavioral Tests | Test fixture framework | NOT_STARTED | — | Run empty framework; verify scaffold works | — | — | — |
| OPT-008-B | Provider Behavioral Tests | 5+ behavioral test cases | NOT_STARTED | — | Run tests against available provider; verify matrix output | — | — | Depends on OPT-008-A |
| OPT-008-C | Provider Behavioral Tests | Integration with `/agents validate` | NOT_STARTED | — | Run validate with extended flag; verify behavioral tests included | — | — | Depends on OPT-003-C + OPT-008-B |
| OPT-009-A | Context Budget Monitoring | Token estimation at agent init | NOT_STARTED | — | Initialize agent; verify token estimate in logs | — | — | — |
| OPT-009-B | Context Budget Monitoring | Warning on threshold exceeded | NOT_STARTED | — | Create agent with oversized prompt; verify warning | — | — | Depends on OPT-009-A |
| OPT-009-C | Context Budget Monitoring | `/context` command | NOT_STARTED | — | Run command; verify breakdown displayed | — | — | Depends on OPT-009-A |
| OPT-010-A | MCP Progressive Discovery | Two-phase tool loading | NOT_STARTED | — | Connect MCP server; verify metadata-only initial load | — | — | — |
| OPT-010-B | MCP Progressive Discovery | On-demand schema loading + caching | NOT_STARTED | — | Invoke tool; verify full schema loads and caches | — | — | Depends on OPT-010-A |
| OPT-010-C | MCP Progressive Discovery | Opt-out config per MCP server | NOT_STARTED | — | Set opt-out; verify full load at connect | — | — | Depends on OPT-010-A |
| OPT-010-D | MCP Progressive Discovery | Token savings reporting in `/mcp` | NOT_STARTED | — | Run `/mcp`; verify token count display | — | — | Depends on OPT-010-A |

---

## Dependency Graph

```
OPT-001-A ──→ OPT-001-B ──→ OPT-001-C
    │              │
    ├──→ OPT-001-D │
    └──→ OPT-001-E │
                    │
OPT-002-A ──→ OPT-002-B
    └──────────────────→ OPT-002-C (also needs OPT-003-A)

OPT-003-A ──→ OPT-003-B
    └──→ OPT-003-C ──────────→ OPT-008-C (also needs OPT-008-B)

OPT-004-A ─┐
OPT-004-B ─┴→ OPT-004-C

OPT-005-A ──→ OPT-005-C (also needs OPT-005-B)
    │              └──→ OPT-005-E (also needs OPT-005-D)
    ├──→ OPT-005-B
    └──→ OPT-005-D

OPT-006-A ──→ OPT-006-B
    └──→ OPT-006-C

OPT-007-A ──→ OPT-007-B ──→ OPT-007-C

OPT-008-A ──→ OPT-008-B ──→ OPT-008-C

OPT-009-A ──→ OPT-009-B
    └──→ OPT-009-C

OPT-010-A ──→ OPT-010-B
    ├──→ OPT-010-C
    └──→ OPT-010-D
```

**Recommended execution order (respecting dependencies):**
1. OPT-001-A → OPT-002-A → OPT-003-A (foundations — can be parallelized)
2. OPT-001-B/C/D/E, OPT-002-B, OPT-003-B/C (build on foundations)
3. OPT-004-A/B → OPT-004-C, OPT-005-A → OPT-005-B/C/D/E (schema extensions)
4. OPT-006-A/B/C, OPT-007-A/B/C (resilience + orchestration)
5. OPT-008-A/B/C, OPT-009-A/B/C, OPT-010-A/B/C/D (testing + monitoring + scaling)

---

## Change Log

| Date | Author | Change | Matrix Rows Affected |
|------|--------|--------|---------------------|
| — | Code Puppy | Initial document creation | All (set to NOT_STARTED) |

---

## Validation Checklist (Run Before Declaring Any Optimization Complete)

For each optimization (all sub-tasks `PASSED`), verify:

- [ ] **Backward compatibility:** All existing agents, commands, and integrations work unchanged
- [ ] **Schema compliance:** JSON agent schema validates with and without new optional fields
- [ ] **Documentation updated:** Any new field, command, or behavior is documented
- [ ] **Error handling:** Invalid inputs produce clear, actionable error messages (not stack traces)
- [ ] **Logging:** Significant events (warnings, fallbacks, configuration loads) are logged with context
- [ ] **Traceability matrix current:** All rows updated with status, files, test results, and dates

---

## How to Use This Prompt

### Starting a Session

```
Load this file as context, then:

"You are in self-optimization mode. Read the traceability matrix to determine 
the next NOT_STARTED item that has all dependencies satisfied. Confirm the 
item and your implementation plan before writing any code. After each change, 
update the matrix and run the specified test."
```

### Resuming Work

```
"Resume self-optimization. Read the traceability matrix. Report:
1. What was last completed (most recent PASSED row)
2. What is currently IN_PROGRESS (if any)
3. What is next in the queue
Then proceed with the next item."
```

### Reviewing Progress

```
"Report optimization status. For each OPT-XXX group, show:
- Completion percentage (sub-tasks PASSED / total sub-tasks)
- Any FAILED or BLOCKED items with notes
- Estimated remaining work"
```

### Handling Failures

```
"OPT-XXX-X has failed testing. Read the test output, diagnose the root cause,
propose a fix, and implement it. Update the matrix row with failure details
before applying the fix. After fixing, re-run the test and update the result."
```

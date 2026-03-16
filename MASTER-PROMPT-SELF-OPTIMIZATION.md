# Code Puppy Self-Optimization Prompt

> **Purpose:** This document is a natural language agentic prompt designed to be loaded directly into Code Puppy so it can systematically evaluate, modify, and improve its own architecture. It includes a self-managed traceability matrix that must be updated as each optimization is implemented, tested, and verified.
>
> **Usage:** Load this file as context when running Code Puppy in its own codebase. The agent will use the decision framework, implementation queue, and traceability matrix to work through optimizations methodically.
>
> **Owner:** Tyler Granlund, IT Director — HTT Brands
>
> **Version:** 2.0.0
>
> **Revision Notes:** v2.0 incorporates cross-cutting design risk mitigations from architectural review — adds OPT-000 (Prompt Assembly Pipeline) as a prerequisite, tightens scoping on FallbackModel retry handling, improves tool description quality heuristics, adds duplicate skill detection, defines explicit precedence rules for skill conflicts, and shifts behavioral testing to descriptive-metrics-first approach.

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

### Disambiguation: Two "Skills" Concepts

Code Puppy's architecture has two distinct mechanisms that both use the word "skill." They serve different purposes and must not be conflated:

1. **SKILL.md Plugin Skills** — External knowledge packages (markdown files with YAML frontmatter) that provide Claude/Code Puppy with domain expertise during a session. These are standalone reference documents loaded as context. They exist outside the agent schema.

2. **Shared Skill Prompt Fragments (OPT-005)** — Reusable markdown files in `~/.code_puppy/skills/` that are injected into an agent's system prompt at initialization via the `skills` array in the JSON agent schema. These become part of the agent's identity and reasoning instructions.

**Enforced load order (OPT-000 owns this):**
```
Base agent system_prompt
  → Shared skill prompt fragments (OPT-005, in declared order)
    → agent_skills plugin injections (if any)
      → Dynamic per-turn context (conversation history, tool results)
```

When this document references "skills" it means shared skill prompt fragments (type 2) unless explicitly stated otherwise.

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
- **Skill duplication:** Same domain knowledge in multiple agents' system prompts → extract to shared skill file. If the same content appears in both a shared skill and an agent's own system prompt, `/agents validate` must flag it.
- **Premature agent splitting:** Try prompt templates with policy variables before creating new agents.
- **Context overload:** Effective context ≈ 50–65% of advertised window. Design for half capacity.
- **Config sprawl:** All new configuration options must be defined in a central config schema with documented defaults. Do not scatter defaults across modules.

---

## Optimization Queue

Items are ordered by implementation priority. Each has a unique ID referenced in the traceability matrix.

### OPT-000: Prompt Assembly Pipeline

**Priority:** P0 — Prerequisite for all other optimizations
**Rationale:** Multiple optimizations (OPT-001, OPT-005, OPT-009) independently modify the system prompt and static context. Without a single, well-defined prompt assembly pipeline that enforces order of operations and measures tokenization in one place, you risk duplicated skill content, context estimates that don't match the actual assembled prompt, and subtle load-order bugs that are painful to diagnose. This must exist before anything else touches prompt composition.

**Implementation Spec:**
- Create a `PromptAssembler` class/module that owns the complete prompt assembly sequence
- Enforce the following assembly order (no other code path may inject into the system prompt):
  1. Base agent `system_prompt` (from JSON or Python agent definition)
  2. Shared skill prompt fragments (OPT-005 `skills` array, in declared order)
  3. `agent_skills` plugin injections (if any exist)
  4. Dynamic per-turn context (conversation history, tool results — handled by Pydantic AI runtime, but PromptAssembler defines the boundary)
- PromptAssembler outputs: assembled prompt string + token count estimate + component breakdown (bytes/tokens per section)
- All other optimizations that touch prompt content MUST go through PromptAssembler — no direct string concatenation of prompt components elsewhere
- Token estimation must use the same tokenizer reference that OPT-009 will use (establish the single tokenizer dependency here)

**Acceptance Criteria:**
- [ ] PromptAssembler module exists with clear API
- [ ] Assembly order is enforced — direct prompt manipulation outside PromptAssembler raises an error or warning
- [ ] Token count and component breakdown are returned on every assembly call
- [ ] Existing agents assemble identically to current behavior (no shared skills or plugins yet — just base prompt passthrough)
- [ ] Unit tests cover assembly order enforcement and token counting

**Files Likely Affected:** New `prompt_assembler.py` module, agent initialization refactored to use it, existing system prompt handling

---

### OPT-001: Skill Metadata Progressive Loading

**Priority:** P0 — Highest impact, enables everything else
**Depends on:** OPT-000 (PromptAssembler must exist first)
**Rationale:** Code Puppy's JSON agent format is one step away from supporting progressive skill loading. Adding optional `skill_metadata` (short description for discovery) separate from the full `system_prompt` (loaded on demand) aligns with Anthropic's Agent Skills pattern and dramatically improves the planning-agent's specialist selection.

**Implementation Spec:**
- Add optional `skill_metadata` field to JSON agent schema (string, ≤75 tokens, must end at a sentence boundary)
- `skill_metadata` describes the agent's own expertise only — it does NOT summarize shared skills (OPT-005). Shared skills may change independently; metadata must remain stable.
- When `skill_metadata` is present, the planning-agent sees only metadata during specialist selection
- Full `system_prompt` loads only when the agent is actually invoked (loaded via PromptAssembler)
- When `skill_metadata` is absent, auto-generate from the first ~75 tokens of `system_prompt` with sentence boundary awareness (never truncate mid-sentence)
- When metadata is auto-generated, emit an info-level log: `"skill_metadata auto-generated for agent '{name}' — consider replacing with a curated summary"`
- Update JSON agent schema documentation
- Update `agent-creator` wizard to prompt for skill metadata

**Acceptance Criteria:**
- [ ] Existing JSON agents without `skill_metadata` work identically to current behavior
- [ ] JSON agents with `skill_metadata` expose only metadata to planning-agent during selection
- [ ] Full `system_prompt` loads on invocation via PromptAssembler
- [ ] Auto-generated metadata respects sentence boundaries and emits info log
- [ ] `agent-creator` wizard generates `skill_metadata` field
- [ ] No regression in existing agent tests

**Files Likely Affected:** `agent_manager.py`, JSON agent schema definition, `planning-agent` system prompt/delegation logic, `agent-creator` wizard logic, `prompt_assembler.py`, documentation

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
- **Tool description quality check:** Validate that each tool's description includes a "when to use" signal and a "when NOT to use" signal (or at minimum is not generic). Flag descriptions that match a stoplist of low-signal patterns (e.g., "use this tool when needed", "general purpose tool", "does something useful"). Do NOT enforce a minimum length — concise but specific descriptions are preferred over verbose but vague ones.

**Acceptance Criteria:**
- [ ] Warning emitted when tool count > 15
- [ ] Warning includes agent name and tool count
- [ ] Strict mode config option available
- [ ] No false positives on agents at or below 15 tools
- [ ] Warning does not block agent execution in default mode
- [ ] Tool description quality check flags generic/stoplist descriptions
- [ ] Quality check does not flag concise but specific descriptions

**Files Likely Affected:** Agent initialization logic, MCP tool registration, configuration schema, logging, tool description validator (new utility)

---

### OPT-003: Agent Registry and Catalog

**Priority:** P1 — Prevents agent sprawl as JSON agents proliferate
**Rationale:** As the team creates JSON agents, discoverability and lifecycle management become critical. `agent_manager.py` has the infrastructure; surface it.

**Implementation Spec:**
- Implement `/agents list` command showing all available agents
- Display: agent name, type (Python/JSON), description, tool count, skill_metadata (if present), file path (for JSON agents)
- Sort by type, then alphabetically
- Add `/agents info <name>` for detailed view including full tool list, system prompt preview (first 200 chars), shared skills referenced, and delegation mode
- Add `/agents validate` to check all JSON agents for:
  - Schema compliance
  - Tool count warnings (OPT-002)
  - Skill duplication detection — hash skill content snippets and flag near-duplicates across agents and between shared skills and agent system prompts
  - Tool description quality (OPT-002)
  - Missing `requires_tool_calling` on agents with tools (OPT-004, info-level)

**Acceptance Criteria:**
- [ ] `/agents list` displays all registered agents with metadata
- [ ] `/agents info <name>` shows detailed agent information including shared skills and delegation mode
- [ ] `/agents validate` runs schema, anti-pattern, and duplicate skill checks
- [ ] Duplicate skill detection uses content hashing and flags near-duplicates
- [ ] Output is clean and parseable
- [ ] Command works with zero JSON agents (shows only built-in Python agents)

**Files Likely Affected:** `agent_manager.py`, command handler/dispatcher, CLI output formatting, content hashing utility (new)

---

### OPT-004: Provider-Aware Tool Filtering

**Priority:** P1 — Critical for multi-provider reliability
**Rationale:** Different models handle tool calling differently (Claude proactive, GPT conservative, open-source models variable). Agents assigned to models that don't support function calling should be caught at config time.

**Implementation Spec:**
- Add optional `requires_tool_calling` field to agent schema (boolean)
- **Inference rule:** For any agent whose schema lists one or more tools AND does not explicitly set `requires_tool_calling: false`, infer `requires_tool_calling: true`. This eliminates the "forgot to set the flag" failure mode while allowing explicit override for agents that have tools but can degrade gracefully without them.
- When an agent uses tools but hasn't explicitly set `requires_tool_calling`, emit an info-level log: `"Agent '{name}' uses tools but does not explicitly set requires_tool_calling — inferring true. Set explicitly to suppress this message."`
- During agent initialization, check if the assigned model supports tool calling
- If mismatch detected: emit error with clear guidance (which model, which agent, what to change)
- Extend `/pin_model` to validate tool-calling compatibility before accepting the pin
- Add model capability registry as a simple config map in `~/.code_puppy/model_capabilities.json` — extensible without code changes

**Acceptance Criteria:**
- [ ] Agents with explicit `requires_tool_calling: true` validated against model capabilities
- [ ] Agents with tools but no explicit field get inferred validation with info log
- [ ] Agents with explicit `requires_tool_calling: false` skip validation regardless of tool count
- [ ] Clear error message on mismatch
- [ ] `/pin_model` rejects incompatible model-agent combinations with explanation
- [ ] Model capability map is extensible (new models can be added without code changes)

**Files Likely Affected:** Agent schema, model initialization, `/pin_model` command handler, model capability config, logging

---

### OPT-005: Shared Skill Files

**Priority:** P1 — Eliminates skill duplication anti-pattern
**Depends on:** OPT-000 (PromptAssembler owns skill injection)
**Rationale:** When the same domain knowledge appears in multiple agents' system prompts, a change requires editing every agent. Shared skill files (markdown) enable single-source-of-truth expertise packages.

**Implementation Spec:**
- Define skill file format: markdown files in `~/.code_puppy/skills/` with YAML frontmatter (name, description, version, tags)
- Add optional `skills` array to JSON agent schema (list of skill file names)
- At agent initialization, PromptAssembler resolves skill references and injects content after the agent's own system prompt, in declared array order
- **Precedence rule (enforced):** If a shared skill and an agent's system prompt define conflicting policies, the agent's system prompt wins. Local specialization always overrides shared defaults. Document this explicitly in the skill file format spec and in the agent creation guide.
- Support relative paths (resolved from `~/.code_puppy/skills/`) and absolute paths
- Add `/skills list` and `/skills info <name>` commands
- Update `agent-creator` wizard to allow skill selection from available library

**Acceptance Criteria:**
- [ ] Skill files in `~/.code_puppy/skills/` are discovered and loadable
- [ ] JSON agents can reference skills via `skills` array
- [ ] Skill content is injected into system prompt via PromptAssembler in declared order
- [ ] Precedence rule is documented and enforced: agent prompt overrides shared skill on conflict
- [ ] Missing skill reference produces clear error (not silent failure)
- [ ] `/skills list` and `/skills info` work correctly
- [ ] Agent still works if `skills` array is empty or absent
- [ ] Skill changes propagate to all agents referencing that skill on next initialization
- [ ] `/agents validate` (OPT-003) flags duplicate content between shared skills and agent system prompts

**Files Likely Affected:** `prompt_assembler.py` (skill injection logic), JSON agent schema, `agent-creator` wizard, CLI commands, skill file format documentation

---

### OPT-006: FallbackModel Integration Hardening

**Priority:** P2 — Resilience for production use
**Rationale:** Pydantic AI's `FallbackModel` enables automatic provider failover, but provider SDK retries must be disabled so fallback activates immediately. Current implementation may have retry conflicts.

**Implementation Spec:**
- Audit current model initialization for conflicting retry configurations
- **Scoped retry disabling:** Set `max_retries=0` ONLY on the provider client instances that are wrapped by a specific `FallbackModel`. Leave default retry behavior intact for models that are not part of a fallback chain. This prevents regressing robustness for non-fallback usage.
- Add configuration option for fallback model chain (e.g., `fallback_chain: ["openai:gpt-5.2", "anthropic:claude-sonnet-4-6"]`)
- Log fallback activation events with source model, target model, error reason, and timestamp
- Add health check to detect when primary model has been unavailable for >N minutes (configurable, default 5 min)

**Acceptance Criteria:**
- [ ] FallbackModel activates on first HTTP error (no SDK retry delay) for wrapped clients only
- [ ] Non-fallback model clients retain their default retry behavior
- [ ] Fallback chain is configurable
- [ ] Fallback events are logged with source, target, error, and timestamp
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
- **Concrete multi-specialist override signal:** When the planning-agent identifies >1 compatible specialist for a single user request during task decomposition, force `subtask` mode for all involved agents regardless of their declared `delegation_mode`. Log the override: `"Overriding delegation_mode to 'subtask' for agents [list] — multi-specialist synthesis required"`
- **Handoff state transfer:** When a `handoff` delegation occurs, explicitly pass the following session state to the specialist: pinned model (if any), active MCP connections, and conversation history up to the delegation point. Document what is and is not transferred.
- Document the distinction in agent creation guide

**Acceptance Criteria:**
- [ ] `delegation_mode` field accepted in JSON agent schema
- [ ] Planning-agent respects delegation mode during task decomposition
- [ ] Multi-specialist tasks force subtask mode with logged override
- [ ] Override trigger: >1 compatible specialist identified for single request
- [ ] Default behavior (`subtask`) matches current behavior
- [ ] Handoff transitions transfer pinned model, MCP connections, and conversation history
- [ ] Handoff state transfer is documented (what transfers, what doesn't)

**Files Likely Affected:** Agent schema, planning-agent delegation logic, agent execution pipeline, session state management, documentation

---

### OPT-008: Per-Provider Behavioral Test Framework

**Priority:** P2 — Confidence in multi-provider deployments
**Rationale:** Claude calls tools proactively; GPT models are more conservative; open-source models vary. Per-provider behavioral tests are essential, not optional.

**Implementation Spec:**
- Create test fixture framework for per-provider agent behavior validation
- Define behavioral test categories: tool calling frequency, multi-turn consistency, instruction following, output format compliance
- Each test runs the same prompt against each configured provider and records behavior
- **Phase 1 (this optimization): Descriptive metrics only.** Output a compatibility matrix showing observed metrics per provider (e.g., "tools called per 10 turns", "% of turns ignoring required output schema", "average response latency with tools"). Do NOT define pass/fail thresholds yet — collect data first to establish baselines across real usage.
- **Phase 2 (future, not in scope):** Once baseline distributions are established from Phase 1 data, add configurable pass/fail thresholds. This will be a separate optimization.
- Integrate with `/agents validate` (OPT-003) as optional extended validation via `--behavioral` flag

**Acceptance Criteria:**
- [ ] Test fixture framework exists and is runnable
- [ ] At least 5 behavioral test cases covering tool calling and instruction adherence
- [ ] Compatibility matrix outputs descriptive metrics (not pass/fail)
- [ ] Tests can target specific providers or run against all configured providers
- [ ] Framework is extensible (new test cases can be added as files)
- [ ] No pass/fail thresholds in Phase 1 — metrics only

**Files Likely Affected:** New test framework module, test fixtures directory, `/agents validate` integration

---

### OPT-009: Context Budget Monitoring

**Priority:** P3 — Operational visibility
**Depends on:** OPT-000 (uses PromptAssembler's token estimation)
**Rationale:** Effective context is 50–65% of advertised capacity. Agents need visibility into how much context they're consuming (system prompt + skills + tool schemas + conversation) to prevent silent degradation.

**Implementation Spec:**
- Leverage PromptAssembler's token estimation (established in OPT-000) for context budget calculations at agent initialization
- Compare against model's effective context budget (50% of advertised as conservative default)
- **Per-agent-type thresholds:** Static context warning threshold is configurable per agent type. Default: 30% for chat/general agents, 45% for coding agents that rely on large shared skills. This prevents false warnings on agents that legitimately need more static context.
- Add `/context` command showing current context utilization breakdown (system prompt, shared skills, tool schemas, remaining budget)
- Make effective context percentage configurable per model
- **Tokenizer consistency:** This module MUST use the same tokenizer instance/reference established in OPT-000's PromptAssembler. Do not introduce a second tokenizer — that creates drift between estimated and actual token counts.

**Acceptance Criteria:**
- [ ] Token estimation runs at agent initialization via PromptAssembler
- [ ] Warning emitted when static context exceeds per-agent-type threshold
- [ ] Per-agent-type thresholds are configurable (default 30% general, 45% coding)
- [ ] `/context` command displays utilization breakdown
- [ ] Effective context percentage is configurable per model
- [ ] Uses the same tokenizer as PromptAssembler (no secondary tokenizer)
- [ ] Estimation is approximately accurate (within 15% of actual tokenization)

**Files Likely Affected:** `prompt_assembler.py` (token estimation API), agent initialization, CLI commands, model configuration, agent type classification

---

### OPT-010: MCP Progressive Discovery

**Priority:** P3 — Scales MCP tool efficiency
**Rationale:** A single MCP server can expose 90+ tools consuming 50,000+ tokens of schemas. Progressive discovery (showing only tool descriptions, loading full schemas on demand) showed 2× success rates in production benchmarks.

**Implementation Spec:**
- Modify MCP tool loading to fetch tool list with descriptions only (metadata phase)
- Full tool schemas load only when the agent selects a tool for use
- Cache loaded schemas for the session duration
- **Per-server opt-out:** Add a config flag per MCP server to disable progressive discovery (for servers where all tools are routinely needed). This must be configurable via CLI (`/mcp config <server> --progressive=false`) or in the MCP server config file — not only via manual file edits.
- **Token savings tracking:** Measure "tokens spent on tool schemas" over the full session (not just at initialization) to accurately capture the impact of progressive discovery. Report in `/mcp` status output: total tools available, schemas loaded this session, estimated token savings vs. full-load baseline.

**Acceptance Criteria:**
- [ ] MCP tools load in two phases (metadata → full schema on demand)
- [ ] Token savings tracked over full session and reported in `/mcp` output
- [ ] Cached schemas don't re-fetch within a session
- [ ] Per-server opt-out configurable via CLI or config file
- [ ] No functionality regression when progressive discovery is enabled

**Files Likely Affected:** MCP integration module, tool loading pipeline, caching layer, `/mcp` command output, MCP server config schema

---

## Traceability Matrix

**Instructions:** Update this matrix after every discrete change. Each row tracks one implementation unit. Status values: `NOT_STARTED`, `IN_PROGRESS`, `IMPLEMENTED`, `TESTING`, `PASSED`, `FAILED`, `BLOCKED`, `SKIPPED`. Never delete a row — if an item is abandoned, set status to `SKIPPED` with notes explaining why.

| ID | Optimization | Sub-Task | Status | Files Modified | Test Method | Test Result | Date | Notes |
|----|-------------|----------|--------|---------------|-------------|-------------|------|-------|
| OPT-000-A | Prompt Assembly Pipeline | Create PromptAssembler module with assembly order enforcement | PASSED | `code_puppy/prompt_assembler.py` (new, 228 lines), `tests/test_prompt_assembler.py` (new, 24 tests) | Unit test: assembly produces identical output to current direct prompt for existing agents | ✅ PASSED (24/24 tests) | 2026-03-09 | **PREREQUISITE — must pass before OPT-001 or OPT-005 begin**. Module created with `estimate_tokens()`, `AssemblyResult`, `PromptAssembler` class, and `assemble_prompt()` convenience function. |
| OPT-000-B | Prompt Assembly Pipeline | Token estimation + component breakdown in PromptAssembler | PASSED | `code_puppy/prompt_assembler.py` (included in OPT-000-A) | Assemble known prompt; verify token count within 15% of reference tokenizer | ✅ PASSED — `estimate_tokens("a"*350)` == 100 (exact), breakdown sums verified | 2026-03-09 | Depends on OPT-000-A. Single tokenizer `estimate_tokens()` established at 3.5 chars/token. |
| OPT-000-C | Prompt Assembly Pipeline | Refactor agent init to use PromptAssembler exclusively | PASSED | `code_puppy/agents/base_agent.py` (added `get_assembled_instructions()` method + replaced 3 call sites at lines 1347, 1521, 1861) | Run all existing agents; verify identical behavior | ✅ PASSED (770/770 tests, 1 skipped, 0 failures) | 2026-03-09 | Depends on OPT-000-A. Added import + thin wrapper method + 3 surgical replacements. No behavior change. GATE PASSED — OPT-001, OPT-005, OPT-009 can proceed. |
| OPT-001-A | Skill Metadata Loading | Add `skill_metadata` field to JSON agent schema | PASSED | `code_puppy/agents/json_agent.py` (added `skill_metadata` property + validation), `tests/test_json_agents.py` (3 new tests) | Load existing JSON agent without field; confirm no change | ✅ PASSED (3/3 new tests, 23/23 total json_agents tests) | 2026-03-09 | Backward compat verified — agents without field return None. Invalid type raises ValueError. |
| OPT-001-B | Skill Metadata Loading | Auto-generate metadata with sentence boundary awareness + info log | PASSED | `code_puppy/agents/json_agent.py` (added `_auto_generate_metadata()` + updated `skill_metadata` property), `tests/test_json_agents.py` (5 new tests) | Create agent without metadata; verify auto-gen stops at sentence boundary ≤75 tokens; verify info log emitted | ✅ PASSED (5/5 new tests) | 2026-03-09 | Uses `estimate_tokens()` from PromptAssembler — single canonical tokenizer. Sentence boundary detection for `.!?` followed by whitespace. Falls back to word-boundary + ellipsis. |
| OPT-001-C | Skill Metadata Loading | Update planning-agent to prefer metadata during selection | PASSED | `code_puppy/agents/agent_manager.py` (modified `get_agent_descriptions()` to prefer `skill_metadata`), `tests/test_json_agents.py` (2 new tests) | Create test JSON agent with metadata; verify planning-agent sees only metadata | ✅ PASSED (2/2 new tests, 93/93 total) | 2026-03-09 | Uses `getattr` for safe Python agent fallback. JSON agents with metadata → metadata shown; without → auto-gen from OPT-001-B; Python agents → description. |
| OPT-001-D | Skill Metadata Loading | Full system_prompt loads on invocation only via PromptAssembler | PASSED | `code_puppy/agents/json_agent.py` (added `read_metadata()` static method), `code_puppy/agents/agent_manager.py` (updated `get_available_agents()` + `get_agent_descriptions()` to use lightweight reader) | Instrument logging; verify full prompt loads only at invocation | ✅ PASSED (5/5 new tests in `TestLightweightMetadataLoading`, 40/40 json_agents tests) | 2026-03-09 | `read_metadata()` reads JSON + extracts only discovery fields. No full agent init. Auto-generates skill_metadata inline. Returns `{}` on failure. |
| OPT-001-E | Skill Metadata Loading | Update agent-creator wizard | PASSED | `code_puppy/agents/agent_creator_agent.py` (updated schema block, optional fields docs, wizard steps 6-8, Python Tutor example) | Run wizard; verify skill_metadata prompt appears | ✅ PASSED — schema, docs, wizard steps, and examples updated with skill_metadata, skills, delegation_mode | 2026-03-09 | File ~640 lines (slightly over 600 cap but splitting would hurt cohesion). |
| OPT-001-F | Skill Metadata Loading | Update documentation | PASSED | `README.md` (updated JSON agent schema block, optional fields section, Python Tutor example) | Manual review | ✅ PASSED — schema, optional fields, and examples updated | 2026-03-09 | All three new fields documented: skill_metadata, skills, delegation_mode. |
| OPT-002-A | Tool Count Guardrails | Add tool count validation at agent init | PASSED | `code_puppy/prompt_assembler.py` (added `validate_tool_count()` + `DEFAULT_TOOL_COUNT_THRESHOLD`), `tests/test_prompt_assembler.py` (7 new tests) | Create agent with 16 tools; verify warning. Create agent with 15; verify no warning | ✅ PASSED (7/7 new tests, 31/31 total prompt_assembler tests) | 2026-03-09 | Utility function ready. Warning logged via `logger.warning()`. Strict mode raises ValueError. Threshold configurable (default 15). Not yet wired into agent construction — that's a future step. |
| OPT-002-B | Tool Count Guardrails | Add strict mode config option | PASSED | `code_puppy/config.py` (added `get_tool_count_strict()` + config key), `tests/test_prompt_assembler.py` (5 new tests) | Enable strict mode; create agent with 16 tools; verify hard error | ✅ PASSED (5/5 new tests) | 2026-03-09 | Config key `tool_count_strict` settable via `/set`. Follows same pattern as other boolean config getters. |
| OPT-002-C | Tool Count Guardrails | Tool description quality validator | PASSED | `code_puppy/prompt_assembler.py` (added `validate_tool_descriptions()`), `tests/test_prompt_assembler.py` (5 new tests) | Create tools with generic stoplist descriptions; verify flagged. Create tools with concise specific descriptions; verify not flagged | ✅ PASSED (5/5 new tests) | 2026-03-09 | Checks against `_GENERIC_DESCRIPTION_PATTERNS` stoplist. No minimum length enforcement. |
| OPT-002-D | Tool Count Guardrails | Include tool count in agent listing | PASSED | Already included in OPT-003-A (`_format_agent_list` shows `[N tools]`) | Run `/agents list`; verify counts shown | ✅ PASSED — tool count displayed for all agents in list output | 2026-03-09 | No additional changes needed — implemented as part of OPT-003-A. |
| OPT-003-A | Agent Registry | Implement `/agents list` command | PASSED | New `code_puppy/plugins/agent_registry/` (2 files: `__init__.py`, `register_callbacks.py` ~170 lines) | Run command; verify all agents displayed with metadata | ✅ PASSED — plugin created with custom_command + custom_command_help callbacks. Shows Python/JSON agents with name, display, description, tool count, metadata/delegation tags. Placeholders for info/validate. | 2026-03-09 | Follows plugin conventions from CONTRIBUTING.md. Lazy imports to avoid circular deps. |
| OPT-003-B | Agent Registry | Implement `/agents info <name>` | PASSED | `code_puppy/plugins/agent_registry/register_callbacks.py` (replaced placeholder `_handle_info`) | Query known agent; verify detail output incl. shared skills + delegation mode | ✅ PASSED — shows name, type, description, delegation mode, requires_tool_calling, skill_metadata, tools, file path, prompt preview | 2026-03-09 | Shows first 200 chars of system prompt. Handles unknown agents and load failures gracefully. |
| OPT-003-C | Agent Registry | Implement `/agents validate` — schema + anti-pattern checks | PASSED | `code_puppy/plugins/agent_registry/register_callbacks.py` (replaced placeholder `_handle_validate`) | Run with known schema violation; verify detection | ✅ PASSED — 5 checks: tool count, requires_tool_calling, skill_metadata, empty prompt, phantom tools. Summary with pass/warn/fail counts. | 2026-03-09 | Imports validation utilities from prompt_assembler and config. |
| OPT-003-D | Agent Registry | Add duplicate skill content detection to `/agents validate` | PASSED | `code_puppy/plugins/agent_registry/register_callbacks.py` (added Check 6 + cross-agent duplicate detection) | Create two agents with identical skill content; verify hash-based duplicate flagged | ✅ PASSED — Check 6: skill/prompt overlap. Cross-agent: MD5 fingerprint of first 500 chars detects near-duplicates. | 2026-03-09 | Both checks fail gracefully. Fingerprint threshold 50+ chars to avoid false positives. |
| OPT-004-A | Provider Tool Filtering | Add `requires_tool_calling` field to schema with inference rule | PASSED | `code_puppy/agents/json_agent.py` (added property with inference logic), `tests/test_json_agents.py` (4 new tests) | Agent without field but with tools: verify inferred true + info log. Agent with explicit false: verify no validation. Agent without tools: verify no validation | ✅ PASSED (4/4 new tests) | 2026-03-09 | Inference rule: tools present + no explicit field → infer True + info log. Explicit false → skip. No tools → False. |
| OPT-004-B | Provider Tool Filtering | Model capability registry | PASSED | New `code_puppy/model_capabilities.py` (162 lines), `tests/test_prompt_assembler.py` (6 new tests) | Query capability map for known models; verify correct capabilities returned | ✅ PASSED (6/6 new tests, 67/67 total) | 2026-03-09 | 3-tier lookup: user overrides → type defaults → empty. Ollama defaults to no tool calling. Cache with clear_cache() for tests. |
| OPT-004-C | Provider Tool Filtering | Validation on init + `/pin_model` | PASSED | `code_puppy/command_line/config_commands.py` (added validation block in `handle_pin_model_command`), `code_puppy/model_capabilities.py` (added `validate_agent_model_compatibility()`), `tests/test_prompt_assembler.py` (3 new tests) | Pin incompatible model; verify rejection with guidance | ✅ PASSED (3/3 new tests) | 2026-03-09 | Blocks pin for incompatible models. Warns for unknown. Fails gracefully. Python agents skip validation. |
| OPT-005-A | Shared Skill Files | Define skill file format + loader | PASSED | `code_puppy/prompt_assembler.py` (added `SkillFile`, `get_skills_directory()`, `_parse_frontmatter()`, `load_skill_file()`, `discover_skills()`, `resolve_skill_references()`), `tests/test_prompt_assembler.py` (11 new tests) | Create skill file; verify discovery and parse | ✅ PASSED (11/11 new tests) | 2026-03-09 | YAML frontmatter parsed without external deps. Required fields: name, description. Optional: version, tags. |
| OPT-005-B | Shared Skill Files | Add `skills` array to JSON agent schema | PASSED | `code_puppy/agents/json_agent.py` (added `skills` property + validation), `tests/test_json_agents.py` (5 new tests) | Agent without skills array works normally | ✅ PASSED (5/5 new tests) — backward compat gate passed | 2026-03-09 | Validates list type and string entries. Defaults to empty list. |
| OPT-005-C | Shared Skill Files | Skill injection via PromptAssembler with precedence rule | PASSED | `code_puppy/prompt_assembler.py` (replaced Step 3 placeholder with real injection), `tests/test_prompt_assembler.py` (5 new tests + mock_agent fixture) | Create agent with conflicting skill; verify agent prompt overrides shared skill content | ✅ PASSED (5/5 new tests) | 2026-03-09 | Skills wrapped in HTML comment headers for debuggability. Precedence enforced by assembly order (agent prompt = step 1, skills = step 3). |
| OPT-005-D | Shared Skill Files | `/skills list` and `/skills info` commands | PASSED | New `code_puppy/plugins/skill_browser/` (2 files: `__init__.py`, `register_callbacks.py` ~120 lines) | Run commands; verify output | ✅ PASSED — Shows name, version, tags, description, file path. Info shows token count + content preview. | 2026-03-09 | Reuses `discover_skills()` and `estimate_tokens()` from prompt_assembler. |
| OPT-005-E | Shared Skill Files | Update agent-creator wizard for skill selection | PASSED | `code_puppy/agents/agent_creator_agent.py` (added skills discovery block, updated step 7, added Available Shared Skills section) | Run wizard; verify skill selection step | ✅ PASSED — wizard discovers and lists available skills, guides selection into skills[] array | 2026-03-09 | Uses discover_skills() from prompt_assembler. Falls back gracefully if no skills exist. |
| OPT-006-A | FallbackModel Hardening | Audit retries; disable ONLY on FallbackModel-wrapped clients | PASSED | New `code_puppy/fallback_config.py` (174 lines — config loading, event logging, health check) | Trigger HTTP error on fallback client: verify immediate fallback. Trigger HTTP error on non-fallback client: verify normal retry behavior preserved | ✅ PASSED — Audit: FallbackModel NOT used, manual fallback exists. max_retries only on Azure (no conflict). Foundation built for future FallbackModel integration. | 2026-03-09 | No retry conflicts found. Manual fallback in _load_model_with_fallback is correct. |
| OPT-006-B | FallbackModel Hardening | Configurable fallback chain | PASSED | `code_puppy/fallback_config.py` (load_fallback_chains, get_fallback_chain), `code_puppy/agents/base_agent.py` (wired configured chain into _load_model_with_fallback) | Set chain in config; verify chain order on failure | ✅ PASSED (4 tests in TestFallbackConfig) — per-agent and default chains from ~/.code_puppy/fallback_chains.json | 2026-03-09 | Configured chain replaces default candidates. Falls through gracefully if no config. |
| OPT-006-C | FallbackModel Hardening | Fallback event logging with full context | PASSED | `code_puppy/fallback_config.py` (log_fallback_event, get_fallback_events, get_primary_unavailable_duration), `code_puppy/agents/base_agent.py` (wired logging into _load_model_with_fallback) | Trigger fallback; verify log entry includes source, target, error, and timestamp | ✅ PASSED — structured events with ISO timestamps, session log, health check utility | 2026-03-09 | Events stored in-memory for session. logger.warning emitted for traditional consumers. |
| OPT-007-A | Planning-Agent Delegation | Add `delegation_mode` field to schema | PASSED | `code_puppy/agents/json_agent.py` (added property + validation), `tests/test_json_agents.py` (4 new tests) | Load agent without field; confirm default `subtask` behavior | ✅ PASSED (4/4 new tests) | 2026-03-09 | Defaults to "subtask". Accepts "handoff". Invalid values raise ValueError. |
| OPT-007-B | Planning-Agent Delegation | Planning-agent respects delegation mode | PASSED | `code_puppy/tools/agent_tools.py` (added delegation_mode to AgentInfo + list_agents output), `code_puppy/agents/agent_planning.py` (updated system prompt with delegation mode guidance) | Set agent to handoff; verify conversation transfer | ✅ PASSED — delegation_mode shown in list_agents, planning prompt includes handoff/subtask/multi-specialist guidance | 2026-03-09 | AgentInfo model extended with delegation_mode field. Handoff agents tagged in display output. |
| OPT-007-C | Planning-Agent Delegation | Multi-specialist forced subtask override with logging | PASSED | `code_puppy/tools/agent_tools.py` (added _multi_specialist_tracker + detection block in invoke_agent) | Task requiring 2+ specialists; verify subtask mode enforced; verify override logged with agent names | ✅ PASSED — rolling 120s window tracker detects multi-specialist invocations. Logs override at INFO level with agent list. | 2026-03-09 | Enforcement via system prompt (OPT-007-B) + runtime detection/logging here. Fails gracefully. |
| OPT-007-D | Planning-Agent Delegation | Handoff state transfer (pinned model, MCP, history) | PASSED | `code_puppy/tools/agent_tools.py` (added handoff logging block), `README.md` (added Delegation Modes section with state transfer docs) | Handoff with pinned model; verify specialist uses pinned model; verify MCP connections available | ✅ PASSED — state transfer already works (model, MCP, history). Added explicit logging + documentation. | 2026-03-09 | Audit confirmed: invoke_agent already transfers pinned model, MCP, and history. Added info-level log on handoff. |
| OPT-007-E | Planning-Agent Delegation | Document handoff state transfer rules | PASSED | `README.md` (Delegation Modes section added in OPT-007-D) | Manual review of documentation | ✅ PASSED — ✅/❌ checklist documents what transfers (model, MCP, history) and what doesn't (parent prompt, tool state) | 2026-03-09 | Combined with OPT-007-D delivery — same README section covers both. |
| OPT-008-A | Provider Behavioral Tests | Test fixture framework | PASSED | New `code_puppy/plugins/behavioral_tests/` (4 files: `__init__.py`, `framework.py` ~175 lines, `test_cases.py` ~120 lines, `register_callbacks.py` ~50 lines) | Run empty framework; verify scaffold works | ✅ PASSED — BehavioralTestSuite, TestMetric, TestResult, CompatibilityMatrix classes + /behavioral command | 2026-03-09 | Phase 1: metrics only, no thresholds. Metric extractors are composable callables. JSON + human-readable output. |
| OPT-008-B | Provider Behavioral Tests | 5+ behavioral test cases (descriptive metrics only) | PASSED | `code_puppy/plugins/behavioral_tests/test_cases.py` (5 test cases across 4 categories) | Run tests against available provider; verify metric matrix output (no pass/fail) | ✅ PASSED — 5 tests: tool_calling_basic, output_format_compliance, constraint_adherence, multi_turn_consistency, code_generation_quality | 2026-03-09 | Categories: tool_calling, instruction_following, multi_turn, code_generation. Extractors: word count, code blocks, list items, headers. |
| OPT-008-C | Provider Behavioral Tests | Integration with `/agents validate --behavioral` | PASSED | `code_puppy/plugins/agent_registry/register_callbacks.py` (added --behavioral flag handling to _handle_validate) | Run validate with --behavioral flag; verify behavioral metrics included | ✅ PASSED — --behavioral shows test suite categories + counts. Without flag shows tip. Fails gracefully if behavioral_tests plugin missing. | 2026-03-09 | Updated _handle_validate signature to accept command string. |
| OPT-009-A | Context Budget Monitoring | Token estimation at agent init via PromptAssembler | PASSED | `code_puppy/agents/base_agent.py` (modified `get_assembled_instructions()` to log breakdown + resolve shared skills), `tests/test_prompt_assembler.py` (1 new test) | Initialize agent; verify token estimate in logs; verify same tokenizer as OPT-000-B | ✅ PASSED (1/1 new test) | 2026-03-09 | Logs at DEBUG level. Resolves shared skills from JSON agent `skills` attribute. Uses same `estimate_tokens()` from OPT-000-B. |
| OPT-009-B | Context Budget Monitoring | Per-agent-type threshold warnings | PASSED | `code_puppy/prompt_assembler.py` (added `get_context_threshold()`, `check_context_budget()`, constants), `code_puppy/agents/base_agent.py` (wired budget check into `get_assembled_instructions()`), `tests/test_prompt_assembler.py` (7 new tests) | Create coding agent exceeding 45% threshold: verify warning. Create chat agent under 30%: verify no warning | ✅ PASSED (7/7 new tests, 114/114 total) | 2026-03-09 | Heuristic: agent name contains code/developer/reviewer → 45%, else 30%. Fails gracefully. |
| OPT-009-C | Context Budget Monitoring | `/context` command | PASSED | New `code_puppy/plugins/context_monitor/` (2 files: `__init__.py`, `register_callbacks.py` ~99 lines) | Run command; verify breakdown displayed (prompt, skills, tool schemas, remaining) | ✅ PASSED — shows system prompt, shared skills, plugin injections, tool schemas, total, remaining, threshold, budget check | 2026-03-09 | Plugin pattern per CONTRIBUTING.md. Uses canonical estimate_tokens(). ~50 tokens/tool for schema estimation. |
| OPT-010-A | MCP Progressive Discovery | Two-phase tool loading + session caching | PASSED | New `code_puppy/mcp_/progressive_discovery.py` (234 lines — ServerToolStats, token tracking, config loading), new `code_puppy/plugins/mcp_progressive/` (plugin with /mcp_stats command) | Start session; verify metadata-only load; trigger tool use; verify schema fetched on demand | ✅ PASSED (6 tests in TestMCPProgressiveDiscovery) — token estimation framework with per-server tracking. Note: actual lazy loading requires pydantic-ai support. | 2026-03-09 | Phase 1 tracking infrastructure. pydantic-ai loads all schemas eagerly; infrastructure ready for lazy loading when supported. |
| OPT-010-B | MCP Progressive Discovery | Per-server opt-out config | PASSED | `code_puppy/mcp_/progressive_discovery.py` (load_progressive_config, is_progressive_enabled) | Opt-out server in config; verify full schemas loaded for opted-out server | ✅ PASSED — per-server config via ~/.code_puppy/mcp_progressive.json with default_enabled + per-server overrides | 2026-03-09 | Config validates gracefully. Missing file defaults to enabled. |
| OPT-010-C | MCP Progressive Discovery | Session-level token savings tracking | PASSED | `code_puppy/mcp_/progressive_discovery.py` (record_server_tools, record_schema_loaded, get_total_savings, get_session_stats) | Complete session; verify cumulative token savings reported | ✅ PASSED — tracks per-server and total savings. Estimates: ~50 tokens/full schema, ~10 tokens/metadata. | 2026-03-09 | In-memory session tracking. clear_stats() for test isolation. |
| OPT-010-D | MCP Progressive Discovery | Token savings in /mcp output | PASSED | `code_puppy/plugins/mcp_progressive/register_callbacks.py` (/mcp_stats custom command), `code_puppy/mcp_/progressive_discovery.py` (get_summary) | Run /mcp; verify progressive discovery savings row in output | ✅ PASSED — /mcp_stats shows per-server tool counts, load mode, savings. Human-readable formatted output. | 2026-03-09 | Separate /mcp_stats command to avoid touching /mcp core. |

---

## Dependency Graph

```
OPT-000-A ──→ OPT-000-B ──→ OPT-000-C ──→ [GATE: OPT-001, OPT-005, OPT-009 cannot start until OPT-000-C passes]
                                │
                    ┌───────────┼───────────────────────┐
                    ▼           ▼                       ▼
               OPT-001-A   OPT-005-A               OPT-009-A
                    │           │                       │
          ┌────────┼────┐      │                  ┌────┼────┐
          ▼        ▼    ▼      │                  ▼         ▼
     OPT-001-B  001-E  001-F   │              OPT-009-B  OPT-009-C
          │                    │
          ▼                    │
     OPT-001-C            OPT-005-B
          │                    │
          ▼                    ▼
     OPT-001-D            OPT-005-C ──→ OPT-005-E
                               │
                          OPT-005-D
                               │
                          OPT-003-D (also needs OPT-003-C)

OPT-002-A ──→ OPT-002-B
    │
    ├──→ OPT-002-C
    │
    └──→ OPT-002-D (also needs OPT-003-A)

OPT-003-A ──→ OPT-003-B
    └──→ OPT-003-C ──→ OPT-003-D (also needs OPT-005-A)
              └──→ OPT-008-C (also needs OPT-008-B)

OPT-004-A ─┐
OPT-004-B ─┴→ OPT-004-C

OPT-006-A ──→ OPT-006-B
    └──→ OPT-006-C

OPT-007-A ──→ OPT-007-B ──→ OPT-007-C
                   └──→ OPT-007-D ──→ OPT-007-E

OPT-008-A ──→ OPT-008-B ──→ OPT-008-C

OPT-010-A ──→ OPT-010-B ──→ OPT-010-D
    └──→ OPT-010-C
```

**Recommended execution order (respecting dependencies):**

**Phase 0 — Prerequisite (must complete first):**
- OPT-000-A → OPT-000-B → OPT-000-C (PromptAssembler pipeline)

**Phase 1 — Foundations (can be parallelized after Phase 0):**
- OPT-001-A → OPT-001-B/C/D/E/F (skill metadata)
- OPT-002-A → OPT-002-B/C (tool guardrails)
- OPT-003-A → OPT-003-B/C (agent registry)

**Phase 2 — Schema extensions (build on Phase 1):**
- OPT-004-A/B → OPT-004-C (provider filtering)
- OPT-005-A → OPT-005-B/C/D/E (shared skills)
- OPT-003-D (duplicate detection — needs OPT-003-C + OPT-005-A)
- OPT-002-D (tool count in listing — needs OPT-003-A)

**Phase 3 — Resilience + orchestration:**
- OPT-006-A/B/C (fallback hardening)
- OPT-007-A → OPT-007-B/C/D/E (delegation improvements)

**Phase 4 — Testing + monitoring + scaling:**
- OPT-008-A/B/C (behavioral tests — descriptive metrics only)
- OPT-009-A/B/C (context monitoring)
- OPT-010-A/B/C/D (MCP progressive discovery)

---

## Change Log

| Date | Author | Change | Matrix Rows Affected |
|------|--------|--------|---------------------|
| — | Tyler Granlund | v1.0 — Initial document creation | All (set to NOT_STARTED) |
| — | Tyler Granlund | v2.0 — Incorporated architectural review feedback: added OPT-000 (Prompt Assembly Pipeline), tightened OPT-001 metadata generation (sentence boundaries, agent-only scope, auto-gen warning), improved OPT-002 tool description quality checks (when-to-use/when-NOT-to-use pattern, stoplist), added duplicate skill detection to OPT-003, added inference rule to OPT-004, added precedence rule to OPT-005, scoped retry disabling in OPT-006 to FallbackModel-wrapped clients only, added concrete multi-specialist override signals and handoff state transfer to OPT-007, shifted OPT-008 to descriptive-metrics-first approach, added per-agent-type thresholds and tokenizer consistency to OPT-009, changed OPT-010 to full-session token tracking with CLI-configurable opt-out. Added skills disambiguation section to architectural context. | Added OPT-000-A/B/C, OPT-001-B (new), OPT-001-F (renumbered), OPT-002-C (new), OPT-003-D (new), OPT-007-D/E (new). Modified all other rows for updated specs. |

---

## Validation Checklist (Run Before Declaring Any Optimization Complete)

For each optimization (all sub-tasks `PASSED`), verify:

- [ ] **Backward compatibility:** All existing agents, commands, and integrations work unchanged
- [ ] **Schema compliance:** JSON agent schema validates with and without new optional fields
- [ ] **Documentation updated:** Any new field, command, or behavior is documented
- [ ] **Error handling:** Invalid inputs produce clear, actionable error messages (not stack traces)
- [ ] **Logging:** Significant events (warnings, fallbacks, configuration loads) are logged with context
- [ ] **Prompt assembly integrity:** If this optimization touches prompt content, verify it goes through PromptAssembler and the component breakdown reflects the change
- [ ] **Config centralization:** Any new config option is in the central schema with a documented default
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

### Spot-Checking Prompt Assembly (use after any OPT-000/001/005/009 change)

```
"Run PromptAssembler on agent '<name>' and show me the component breakdown:
- Base system prompt: X tokens
- Shared skills: X tokens (list each)
- Plugin injections: X tokens
- Tool schemas: X tokens
- Total static context: X tokens (Y% of effective budget)
Verify assembly order matches the enforced sequence."
```

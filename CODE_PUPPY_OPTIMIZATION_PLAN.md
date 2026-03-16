# Code Puppy Self-Optimization Plan — Complete Reference

> **Purpose:** This is the authoritative, end-to-end reference document combining the original self-optimization prompt, validated research findings from March 9, 2026, and the revised execution plan. It supersedes `code-puppy-self-optimization-prompt.md` for implementation purposes.
>
> **Owner:** Tyler Granlund, IT Director — HTT Brands
> **Version:** 2.0.0
> **Date:** March 9, 2026
> **Code Puppy Version:** 0.0.425
> **Pydantic AI Version:** 1.56.0 (current), 1.67.0 (recommended upgrade target)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Research Validation Results](#research-validation-results)
3. [Revised Architectural Context](#revised-architectural-context)
4. [Optimization Queue (Revised)](#optimization-queue-revised)
5. [Traceability Matrix](#traceability-matrix)
6. [Dependency Graph](#dependency-graph)
7. [Execution Phases](#execution-phases)
8. [Risks & Mitigations](#risks--mitigations)
9. [Sources & Citations](#sources--citations)
10. [Change Log](#change-log)

---

## Executive Summary

Code Puppy's self-optimization plan defines 10 architectural improvements (OPT-001 through OPT-010) plus one newly identified opportunity (OPT-011). These optimizations span five categories:

| Category | Optimizations | Priority Range |
|----------|--------------|---------------|
| **Context Efficiency** | OPT-001 (Skill Metadata), OPT-009 (Context Budget), OPT-010 (MCP Progressive) | P0–P3 |
| **Safety Guardrails** | OPT-002 (Tool Count), OPT-004 (Provider Filtering) | P0–P1 |
| **Developer Experience** | OPT-003 (Agent Registry), OPT-005 (Shared Skills) | P1 |
| **Resilience** | OPT-006 (FallbackModel), OPT-011 (Prompt Caching) | P1–P2 |
| **Orchestration** | OPT-007 (Delegation), OPT-008 (Behavioral Tests) | P2 |

**Key changes from v1.0 (based on research):**
- OPT-001 justification reframed from "Anthropic Agent Skills pattern" → "orchestrator-worker context optimization"
- OPT-002 tool count guardrail made configurable, not hard-coded at 15
- OPT-009 context budget default updated from 50-65% → 80-90% for current models
- NEW: OPT-011 Prompt Caching Strategy added (estimated 40-60% cost reduction)
- Recommendation to upgrade pydantic-ai-slim from 1.56.0 → 1.67.0

**Total scope:** 35 sub-tasks across 10 optimizations, ~19-27 hours estimated effort.

---

## Research Validation Results

Research was conducted on March 9, 2026 via web-puppy using 14 primary sources (all Tier 1 — official documentation from Anthropic, OpenAI, Pydantic AI, and MCP specification). Full research artifacts are preserved in `./research/`.

### Finding 1: FallbackModel SDK Retry Conflict

| Field | Value |
|-------|-------|
| **Verdict** | ✅ **CONFIRMED** |
| **Claim** | Provider SDK retries conflict with FallbackModel behavior |
| **Evidence** | Pydantic AI Issue [#3267](https://github.com/pydantic/pydantic-ai/issues/3267), Fix PR [#3294](https://github.com/pydantic/pydantic-ai/pull/3294) (merged Nov 2025) |
| **Detail** | OpenAI SDK has `DEFAULT_MAX_RETRIES = 2` built-in. On 429 errors, it respects `Retry-After` headers (up to 60 seconds). These retries happen **before** FallbackModel ever sees the error. |
| **Fix** | Set `max_retries=0` on all provider clients used with FallbackModel |
| **Impact on Plan** | OPT-006 is validated. Implementation should set `max_retries=0` on provider clients in model factory. |

**FallbackModel Timeline (from PR history):**
- Feb 25, 2025: Introduced (PR #894 by sydney-runkle)
- Mar 2025: Instrumentation fixes
- Aug 2025: Settings, string model names, price() method
- Nov 2025: SDK retry warning, Google error wrapping, output mode support
- API is **stable** — constructor signature unchanged since introduction. 27 merged PRs, additive only.

### Finding 2: Tool Count Threshold of 15

| Field | Value |
|-------|-------|
| **Verdict** | ⚠️ **DIRECTIONALLY CORRECT, NOT PRECISE** |
| **Claim** | Model confusion increases when agent tool count exceeds 15 |
| **Evidence** | Anthropic docs: ["Consolidate related operations into fewer tools"](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use), "description quality is by far the most important factor" |
| **Detail** | No specific numeric threshold published by any major provider. Claude Opus 4.6 "handles multiple tools better." A new "Tool search" feature in Anthropic API suggests they expect large tool sets. Anthropic's "Building Effective Agents" mentions successful coding agents use <10 core tools. |
| **Token cost** | ~346 tokens per tool definition. 15 tools ≈ 5,190 tokens — trivial in 200K context windows. |
| **Impact on Plan** | OPT-002 keeps the guardrail but makes threshold configurable (default 15). Reframe as cognitive limit, not context limit. Description quality improvement is higher ROI than count reduction. |

### Finding 3: MCP Progressive Discovery

| Field | Value |
|-------|-------|
| **Verdict** | ℹ️ **NOT IN MCP SPEC — CLIENT-SIDE ONLY** |
| **Claim** | MCP supports progressive/lazy tool schema loading |
| **Evidence** | [MCP Spec 2025-11-25](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2025-11-25/server/tools.mdx), [Draft changelog](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/draft/changelog.mdx) |
| **What MCP provides** | ✅ Cursor-based pagination on `tools/list`, ✅ `listChanged` notifications, ✅ Tool annotations/title/icons (2025-11-25+) |
| **What MCP does NOT provide** | ❌ Lazy/progressive schema loading, ❌ Tool search endpoint, ❌ Schema-on-demand, ❌ Category/tag filtering |
| **Impact on Plan** | OPT-010 is a valid client-side optimization. Code Puppy's two-phase approach (metadata → full schema on demand) is architecturally sound but is a custom implementation with maintenance burden. Monitor MCP spec `extensions` field for future native support. |

### Finding 4: "Anthropic Agent Skills" Pattern

| Field | Value |
|-------|-------|
| **Verdict** | ⚠️ **REFRAME NEEDED** |
| **Claim** | Progressive skill loading "aligns with Anthropic's Agent Skills pattern" |
| **Evidence** | Anthropic ["Building Effective Agents"](https://www.anthropic.com/engineering/building-effective-agents) (Dec 2024), [Claude 4.6 Prompting Best Practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| **Detail** | Anthropic has **no published pattern** called "Agent Skills" or "progressive skill loading." However, the underlying concept is strongly aligned with: Anthropic's orchestrator-worker pattern, OpenAI's `agent.as_tool(tool_description=...)`, and Pydantic AI's agent delegation where the parent doesn't see the child's system prompt. |
| **Impact on Plan** | Keep OPT-001 feature, reframe justification: "Applies orchestrator-worker principles to context management: the planning-agent sees compact agent descriptions during selection, and full system prompts load only on invocation." |

### Finding 5: Effective Context Capacity (50-65%)

| Field | Value |
|-------|-------|
| **Verdict** | ⚠️ **OUTDATED FOR CURRENT MODELS** |
| **Claim** | Effective context is 50-65% of advertised capacity |
| **Evidence** | [Claude API Models Overview](https://platform.claude.com/docs/en/about-claude/models/overview), [Prompt Caching Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching), [Prompting Best Practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| **Updated guidance** | Current-generation models (Claude 4.x, GPT-5.x) with proper structuring: **80-90% effective capacity**. Previous-gen (Claude 3.x, GPT-4.x): 65-75%. Legacy/unknown: 50-65% conservative fallback. |
| **Key insight** | The constraint has shifted from **capacity** to **structure** — documents first, queries last, XML tag delineation. Claude 4.6 has native context awareness (model tracks remaining budget). Queries at end improve quality by ~30%. |
| **Impact on Plan** | OPT-009 default threshold updated to 80-90%. Make threshold configurable per model generation. Add structuring guidelines. |

### Finding 6: Subtask vs Handoff Delegation Patterns

| Field | Value |
|-------|-------|
| **Verdict** | ✅ **FULLY VALIDATED** |
| **Claim** | Subtask (parent retains control) and handoff (specialist takes over) are the two canonical delegation patterns |
| **Evidence** | [Anthropic "Building Effective Agents"](https://www.anthropic.com/engineering/building-effective-agents), [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/agents/), [Pydantic AI Multi-Agent](https://ai.pydantic.dev/multi-agent-applications/) |

**Industry consensus mapping:**

| | Subtask | Handoff |
|---|---|---|
| **Anthropic** | Orchestrator-workers | Routing |
| **OpenAI SDK** | Manager (`as_tool()`) | Handoffs (`transfer_to_X`) |
| **Pydantic AI** | Agent delegation (level 2) | Programmatic hand-off (level 3) |

| **Impact on Plan** | OPT-007 design is validated. Subtask is correct default for coding agents. All three vendors recommend orchestrator-worker for coding tasks. |

**New finding:** Claude 4.6 has native subagent orchestration — it proactively decides when to delegate. Anthropic warns it can "overtrigger," so lighter-touch orchestration prompts may be appropriate for planning-agent.

### Finding 7: Prompt Caching Opportunity (NEW)

| Field | Value |
|-------|-------|
| **Verdict** | 💡 **NEW OPTIMIZATION IDENTIFIED** |
| **Detail** | Anthropic's prompt caching: automatic caching with 5-min TTL, 1-hour option at 2x cost, 90% cost reduction on cached reads, workspace-level isolation (updated Feb 5, 2026). |
| **Minimum cacheable** | 4,096 tokens (Opus 4.6), 2,048 tokens (Sonnet 4.6) |
| **Estimated impact** | 40-60% cost reduction on input tokens for typical multi-turn coding sessions |
| **Impact on Plan** | Added as OPT-011. System prompts, tool definitions, and shared skill content are ideal caching candidates. |

### Additional Recommendations from Research

| # | Recommendation | Priority | Effort | Source |
|---|---------------|----------|--------|--------|
| R1 | Upgrade pydantic-ai-slim 1.56.0 → 1.67.0 (11 versions behind, FallbackModel fixes, GPT-5.4 support) | 🔴 Critical | Medium | GitHub releases |
| R2 | Improve tool descriptions (3-4 sentences minimum, "when to use" and "when NOT to use") | 🟡 Important | Medium | Anthropic docs |
| R3 | Consider `strict: true` for tool definitions (guaranteed schema conformance) | 🟡 Important | Low | Anthropic docs |
| R4 | Research Anthropic's "Tool Search" feature for future integration | 🟢 Watch | Low | Anthropic docs sidebar |
| R5 | Test Claude 4.6 native subagent orchestration before over-engineering delegation | 🟢 Watch | Medium | Anthropic prompting docs |

---

## Revised Architectural Context

### Current Architecture (v0.0.425)

```
code_puppy/
├── callbacks.py               ← 30+ lifecycle hooks (the plugin contract)
├── plugins/                   ← 16 plugins (builtin + user)
│   ├── agent_skills/          ← Skill discovery, activation, prompt injection
│   ├── shell_safety/          ← Shell command risk assessment
│   ├── file_permission_handler/ ← Diff preview + approval prompts
│   ├── universal_constructor/ ← Custom tool creation (Helios)
│   ├── frontend_emitter/      ← WebSocket event bridge
│   ├── scheduler/             ← TUI + slash commands
│   └── ...                    ← OAuth plugins, customizable_commands, etc.
├── agents/                    ← 29+ agents (Python + JSON)
│   ├── base_agent.py          ← 85KB! Agent construction, MCP, compaction
│   ├── agent_manager.py       ← Registry, discovery, session management
│   ├── json_agent.py          ← JSON agent loader (schema: name, description, system_prompt, tools)
│   ├── agent_planning.py      ← Planning agent (orchestrator)
│   ├── agent_creator_agent.py ← JSON agent creation wizard
│   └── pack/                  ← Bloodhound, Husky, Retriever, Shepherd, Terrier, Watchdog
├── tools/                     ← 7 core tools + browser + skills + UC
├── model_factory.py           ← Multi-provider model creation, round-robin
├── mcp_/                      ← MCP server management, tool discovery
├── command_line/              ← TUI, slash commands, menus (50 files)
└── config.py                  ← XDG-aware config, 57KB
```

**Key stats:**
- 29 registered agents (Python + JSON + pack)
- 7 core tools: `list_files`, `read_file`, `grep`, `edit_file`, `delete_file`, `agent_run_shell_command`, `agent_share_your_reasoning`
- 93+ test files
- 16 builtin plugins
- Pydantic AI 1.56.0

### Taxonomy Hierarchy (Enforced)

| Tier | Definition | Code Puppy Mapping | Add When... |
|------|-----------|-------------------|-------------|
| **Tool** | Executes a discrete, deterministic action with defined I/O | Core 7 tools + MCP tools | A new atomic action is needed within an existing agent's domain |
| **Skill** | Encodes domain expertise and procedural knowledge that shapes reasoning | System prompts on JSON/Python agents | New expertise is needed but not a different tool set or trust level |
| **Agent** | Autonomous entity with own system prompt, model, tool set, and decision loop | Python agents + JSON agents | Fundamentally different prompt, tool set, model, or trust level required |
| **Sub-agent** | Agent invoked by parent for a bounded subtask, returns results to parent | planning-agent → specialist delegation | Complex tasks need coordinated specialists |

### Decision Framework (Apply Before Every New Agent/Tool/Skill)

1. **Can a single LLM call solve this?** → Stop. Write a better prompt.
2. **Does it need sequential steps with validation?** → Prompt chaining. No agent needed.
3. **Does it need branching by input type?** → Add routing. Still no agent loop.
4. **Does it need real-world actions?** → Add a tool to an existing agent (if tool count stays ≤ configurable threshold, default 15).
5. **Does it need domain expertise that shapes reasoning?** → Add a skill (update system prompt or create JSON agent).
6. **Is the existing agent's context overloaded?** → Split into sub-agents. Signals: instructions ignored, conflicting priorities, tool count > threshold, different trust levels needed.
7. **Do sub-agents need independent lifecycles/models/deployment?** → Multi-agent orchestrator (`planning-agent` pattern).

### Context Budget Design Guidelines (Updated March 2026)

| Model Generation | Effective Capacity | Strategy |
|-----------------|-------------------|----------|
| Current (Claude 4.x, GPT-5.x) | ~80-90% with structured placement | Structure: docs first, queries last. Use XML tags. Leverage context awareness. |
| Previous (Claude 3.x, GPT-4.x) | ~65-75% | Place critical content in first and last 20%. Watch for "lost in the middle." |
| Legacy / Unknown | ~50-65% (conservative) | Minimize context, use aggressive summarization. |

**Structuring rules (from Anthropic Claude 4.6 docs):**
1. Place longform data/documents at the **top** of the prompt
2. Place queries/instructions at the **bottom** (30% quality improvement)
3. Wrap distinct content sections in XML tags
4. Use prompt caching for repeated content (90% cost reduction on reads)
5. For tasks exceeding one context window, use multi-window workflows with state files

### Anti-Patterns to Detect and Prevent

- **Tool bloat:** Keep active tool set lean. Description quality > tool count. Code Puppy's 7 core tools are near-optimal.
- **Skill duplication:** Same domain knowledge in multiple agents' system prompts → extract to shared skill file (OPT-005).
- **Premature agent splitting:** Try prompt templates with policy variables before creating new agents.
- **Context overload:** Design for model-generation-appropriate capacity (see table above).
- **Over-specified orchestration:** Claude 4.6 has native subagent orchestration. Don't over-engineer delegation logic.

---

## Optimization Queue (Revised)

### OPT-001: Skill Metadata Progressive Loading

| Field | Value |
|-------|-------|
| **Priority** | P0 — Highest impact, enables everything else |
| **Status** | NOT_STARTED |
| **Revised Rationale** | Applies orchestrator-worker principles (Anthropic, 2024; OpenAI, 2025) to context management: the planning-agent sees compact agent descriptions during specialist selection, and full system prompts load only on invocation. This reduces context window consumption during the selection phase and improves planning quality. |

**Implementation Spec:**
- Add optional `skill_metadata` field to JSON agent schema (string, ≤100 tokens recommended)
- When `skill_metadata` is present, the planning-agent sees only metadata during specialist selection
- Full `system_prompt` loads only when the agent is actually invoked
- When `skill_metadata` is absent, fall back to existing behavior (full `system_prompt` visible)
- **NEW:** Consider auto-generating `skill_metadata` from first 100 tokens of `system_prompt` when not explicitly provided
- Update JSON agent schema documentation
- Update `agent-creator` wizard to prompt for skill metadata

**Acceptance Criteria:**
- [ ] Existing JSON agents without `skill_metadata` work identically to current behavior
- [ ] JSON agents with `skill_metadata` expose only metadata to planning-agent during selection
- [ ] Full `system_prompt` loads on invocation
- [ ] `agent-creator` wizard generates `skill_metadata` field
- [ ] No regression in existing agent tests

**Files Likely Affected:** `json_agent.py`, `agent_manager.py`, `agent_planning.py`, `agent_creator_agent.py`, `AGENTS.md`

---

### OPT-002: Tool Count Guardrails

| Field | Value |
|-------|-------|
| **Priority** | P0 — Prevents the most common agent anti-pattern |
| **Status** | NOT_STARTED |
| **Revised Rationale** | Tool count guardrails serve as a cognitive limit warning, not a context limit. Anthropic's guidance is qualitative ("consolidate related operations"), and description quality matters more than raw count. The threshold should be configurable with 15 as a reasonable default based on "Building Effective Agents" (<10 for coding agents). |

**Implementation Spec:**
- Add tool count validation in agent initialization
- Emit a warning (not error) when an agent's total tools (core + MCP) exceed the configurable threshold (default: 15)
- Log the warning with the agent name, tool count, and list of tools
- Add config option `tool_count_threshold` (integer, default 15) and `strict_tool_limit` (boolean, default false)
- Strict mode makes exceeding the threshold a hard error
- Display tool count in `/agents list` output (see OPT-003)
- **NEW:** Also warn about tool description quality — flag tools with descriptions shorter than 2 sentences

**Acceptance Criteria:**
- [ ] Warning emitted when tool count exceeds configured threshold
- [ ] Warning includes agent name and tool count
- [ ] Threshold is configurable via config
- [ ] Strict mode config option available
- [ ] No false positives on agents at or below threshold
- [ ] Warning does not block agent execution in default mode

**Files Likely Affected:** `base_agent.py`, `config.py`, agent_registry plugin

---

### OPT-003: Agent Registry and Catalog

| Field | Value |
|-------|-------|
| **Priority** | P1 — Prevents agent sprawl as JSON agents proliferate |
| **Status** | NOT_STARTED |

**Implementation Spec:**
- New plugin: `code_puppy/plugins/agent_registry/`
- Implement `/agents list` command showing all available agents
- Display: agent name, type (Python/JSON), description, tool count, `skill_metadata` (if present), file path (for JSON agents)
- Sort by type, then alphabetically
- Add `/agents info <name>` for detailed view including full tool list and system prompt preview (first 200 chars)
- Add `/agents validate` to check all JSON agents for schema compliance, tool count warnings, and skill duplication

**Acceptance Criteria:**
- [ ] `/agents list` displays all registered agents with metadata
- [ ] `/agents info <name>` shows detailed agent information
- [ ] `/agents validate` runs schema and anti-pattern checks
- [ ] Output is clean and parseable
- [ ] Command works with zero JSON agents (shows only built-in Python agents)

**Files Likely Affected:** New plugin `agent_registry/`, `agent_manager.py`, CLI output formatting

---

### OPT-004: Provider-Aware Tool Filtering

| Field | Value |
|-------|-------|
| **Priority** | P1 — Critical for multi-provider reliability |
| **Status** | NOT_STARTED |

**Implementation Spec:**
- Add optional `requires_tool_calling: true` field to agent schema
- During agent initialization, check if the assigned model supports tool calling
- If mismatch detected: emit error with clear guidance (which model, which agent, what to change)
- Extend `/pin_model` to validate tool-calling compatibility before accepting the pin
- Add model capability registry (config map, extensible via `~/.code_puppy/model_capabilities.json`)

**Acceptance Criteria:**
- [ ] Agents with `requires_tool_calling: true` validated against model capabilities
- [ ] Clear error message on mismatch
- [ ] `/pin_model` rejects incompatible model-agent combinations with explanation
- [ ] Model capability map is extensible (new models added without code changes)
- [ ] Agents without the field default to no validation (backward compatible)

**Files Likely Affected:** `json_agent.py`, `model_utils.py` or `model_factory.py`, pin command handler, config

---

### OPT-005: Shared Skill Files

| Field | Value |
|-------|-------|
| **Priority** | P1 — Eliminates skill duplication anti-pattern |
| **Status** | NOT_STARTED |
| **Note** | This is DISTINCT from the existing `agent_skills` plugin. That plugin manages directory-based SKILL.md procedural skills with `activate_skill` tool. OPT-005 is about **reusable prompt fragments** injected into system prompts at agent initialization. |

**Implementation Spec:**
- New plugin: `code_puppy/plugins/shared_skills/`
- Define skill file format: markdown files in `~/.code_puppy/skills/` with YAML frontmatter (name, description, version, tags)
- Add optional `skills` array to JSON agent schema (list of skill file names)
- At agent initialization, resolve skill references and inject content into system prompt (after the agent's own system prompt)
- Skills load in declared order
- Support relative paths and absolute paths
- Add `/shared-skills list` and `/shared-skills info <name>` commands (avoids collision with existing `/skills`)
- Update `agent-creator` wizard to allow skill selection from available library

**Acceptance Criteria:**
- [ ] Skill files in `~/.code_puppy/skills/` are discovered and loadable
- [ ] JSON agents can reference skills via `skills` array
- [ ] Skill content is injected into system prompt at initialization
- [ ] Missing skill reference produces clear error (not silent failure)
- [ ] `/shared-skills list` and `/shared-skills info` work correctly
- [ ] Agent still works if `skills` array is empty or absent
- [ ] Skill changes propagate to all agents referencing that skill on next initialization

**Files Likely Affected:** New plugin `shared_skills/`, `json_agent.py`, `agent_creator_agent.py`, CLI commands

---

### OPT-006: FallbackModel Integration Hardening

| Field | Value |
|-------|-------|
| **Priority** | P2 — Resilience for production use |
| **Status** | NOT_STARTED |
| **Research Validation** | ✅ SDK retry conflict CONFIRMED (Issue #3267, Fix PR #3294). FallbackModel API is stable (13+ months, 27 PRs, additive only). |

**Implementation Spec:**
- Set `max_retries=0` on all provider clients (OpenAI, Anthropic) when FallbackModel is configured
- Add configuration option for fallback model chain (e.g., `fallback_chain: ["openai:gpt-5.2", "anthropic:claude-sonnet-4-6"]`)
- Log fallback activation events with source model, target model, and error reason
- Add health check to detect when primary model has been unavailable for >N minutes
- **NEW:** Recommend upgrading pydantic-ai-slim to 1.67.0 first (includes FallbackModel bug fixes for settings, output modes, Google error wrapping)

**Acceptance Criteria:**
- [ ] FallbackModel activates on first HTTP error (no SDK retry delay)
- [ ] Fallback chain is configurable
- [ ] Fallback events are logged with context
- [ ] No impact when FallbackModel is not configured
- [ ] Health check alerts on sustained primary model unavailability

**Files Likely Affected:** `model_factory.py`, `config.py`, logging, health check module

---

### OPT-007: Planning-Agent Delegation Improvements

| Field | Value |
|-------|-------|
| **Priority** | P2 — Better orchestration decisions |
| **Status** | NOT_STARTED |
| **Research Validation** | ✅ Subtask vs handoff patterns fully validated as industry consensus across Anthropic, OpenAI, and Pydantic AI. |

**Implementation Spec:**
- Add `delegation_mode` field to agent schema: `"subtask"` (agent-as-tool, default) or `"handoff"` (specialist takes over)
- Planning-agent uses this field when deciding delegation strategy
- `subtask` agents return results to planning-agent for synthesis
- `handoff` agents take over the user conversation directly
- Add heuristic: if task requires synthesizing across multiple specialists, force `subtask` mode regardless of agent preference
- **NEW:** Keep orchestration prompts lighter-touch — Claude 4.6 has native subagent orchestration that can "overtrigger" with heavy-handed delegation instructions
- Document the distinction in agent creation guide

**Acceptance Criteria:**
- [ ] `delegation_mode` field accepted in JSON agent schema
- [ ] Planning-agent respects delegation mode during task decomposition
- [ ] Multi-specialist tasks force subtask mode
- [ ] Default behavior (`subtask`) matches current behavior
- [ ] Handoff transitions cleanly without context loss

**Files Likely Affected:** `json_agent.py`, `agent_planning.py`, `agent_tools.py`

---

### OPT-008: Per-Provider Behavioral Test Framework

| Field | Value |
|-------|-------|
| **Priority** | P2 — Confidence in multi-provider deployments |
| **Status** | NOT_STARTED |

**Implementation Spec:**
- Create test fixture framework in `tests/behavioral/`
- Define behavioral test categories: tool calling frequency, multi-turn consistency, instruction following, output format compliance
- Each test runs the same prompt against each configured provider and compares behavior
- Output a compatibility matrix (provider × behavior × pass/fail)
- Integrate with `/agents validate` (OPT-003) as optional extended validation
- Mark tests with `@pytest.mark.behavioral` — excluded from default test runs

**Acceptance Criteria:**
- [ ] Test fixture framework exists and is runnable
- [ ] At least 5 behavioral test cases covering tool calling and instruction adherence
- [ ] Compatibility matrix output is human-readable
- [ ] Tests can target specific providers or run against all configured providers
- [ ] Framework is extensible (new test cases can be added as files)

**Files Likely Affected:** New `tests/behavioral/` directory

---

### OPT-009: Context Budget Monitoring

| Field | Value |
|-------|-------|
| **Priority** | P3 — Operational visibility |
| **Status** | NOT_STARTED |
| **Research Validation** | ⚠️ Default threshold updated from 50-65% → 80-90% for current models. Make configurable per model generation. |

**Implementation Spec:**
- New plugin: `code_puppy/plugins/context_monitor/`
- Add token estimation for agent context at initialization (system prompt + skill content + tool JSON schemas)
- Compare against model's effective context budget (configurable, default 80% for current models)
- Warn when static context (before any conversation) exceeds 30% of effective budget
- Add `/context` command showing current context utilization breakdown
- Make effective context percentage configurable per model
- **NEW:** Include structuring guidance in warnings (docs first, queries last, XML tags)

**Acceptance Criteria:**
- [ ] Token estimation runs at agent initialization
- [ ] Warning emitted when static context exceeds threshold
- [ ] `/context` command displays utilization breakdown
- [ ] Threshold percentage is configurable per model generation
- [ ] Estimation is approximately accurate (within 15% of actual tokenization)

**Files Likely Affected:** New plugin `context_monitor/`, config

---

### OPT-010: MCP Progressive Discovery

| Field | Value |
|-------|-------|
| **Priority** | P3 — Scales MCP tool efficiency |
| **Status** | NOT_STARTED |
| **Research Validation** | ℹ️ Not supported natively in MCP spec. This is a client-side optimization. Monitor MCP `extensions` field for future native support. |

**Implementation Spec:**
- Modify MCP tool loading to fetch tool list with descriptions only (metadata phase)
- Full tool schemas load only when the agent selects a tool for use
- Cache loaded schemas for the session duration
- Add config option to disable progressive discovery per MCP server (for servers where all tools are routinely needed)
- Display MCP tool count and schema token cost in `/mcp` status output
- **NEW:** Use MCP's pagination support (`tools/list` with cursor) for servers with many tools

**Acceptance Criteria:**
- [ ] MCP tools load in two phases (metadata → full schema on demand)
- [ ] Token savings measurable and logged at initialization
- [ ] Cached schemas don't re-fetch within a session
- [ ] Opt-out config works per MCP server
- [ ] No functionality regression when progressive discovery is enabled

**Files Likely Affected:** `mcp_/manager.py`, `mcp_/registry.py`, `config.py`, `/mcp` command output

---

### OPT-011: Prompt Caching Strategy (NEW)

| Field | Value |
|-------|-------|
| **Priority** | P1 — High impact, moderate effort |
| **Status** | NOT_STARTED |
| **Source** | Research Finding 7 (March 9, 2026) |

**Rationale:** Anthropic's prompt caching reduces cost by 90% on repeated system prompts, tool definitions, and skill content. Every agent turn currently reprocesses the full system prompt + tools. With automatic caching (5-min TTL), multi-turn coding sessions benefit immediately.

**Implementation Spec:**
- Enable automatic caching for all multi-turn Anthropic conversations
- Use explicit cache breakpoints for system prompt + tool definitions
- Cache shared skill content that multiple agents use
- Consider 1-hour TTL option (`"anthropic-beta": "prompt-caching-2025-07-14"`) for long-running agent sessions
- Verify Code Puppy's `ClaudeCacheAsyncClient` (existing!) already handles some of this
- Add cache hit/miss metrics to agent run logging

**Acceptance Criteria:**
- [ ] Prompt caching active for Anthropic models in multi-turn conversations
- [ ] Cache breakpoints set at system prompt + tool definition boundaries
- [ ] Cache hit/miss metrics logged per agent run
- [ ] No impact on non-Anthropic providers
- [ ] Cost reduction measurable in usage logs

**Files Likely Affected:** `claude_cache_client.py` (already exists!), `base_agent.py`, `config.py`, logging

---

## Traceability Matrix

**Instructions:** Update this matrix after every discrete change. Status values: `NOT_STARTED`, `IN_PROGRESS`, `IMPLEMENTED`, `TESTING`, `PASSED`, `FAILED`, `BLOCKED`, `SKIPPED`.

| ID | Optimization | Sub-Task | Status | Files Modified | Test Method | Test Result | Date | Notes |
|----|-------------|----------|--------|---------------|-------------|-------------|------|-------|
| OPT-001-A | Skill Metadata Loading | Add `skill_metadata` field to JSON agent schema | NOT_STARTED | — | Load existing JSON agent without field; confirm no change | — | — | Backward compat gate |
| OPT-001-B | Skill Metadata Loading | Update planning-agent to prefer metadata during selection | NOT_STARTED | — | Create test JSON agent with metadata; verify planning-agent sees only metadata | — | — | Depends on OPT-001-A |
| OPT-001-C | Skill Metadata Loading | Full system_prompt loads on invocation only | NOT_STARTED | — | Instrument logging; verify full prompt loads only at invocation | — | — | Depends on OPT-001-B |
| OPT-001-D | Skill Metadata Loading | Update agent-creator wizard | NOT_STARTED | — | Run wizard; verify skill_metadata prompt appears | — | — | Depends on OPT-001-A |
| OPT-001-E | Skill Metadata Loading | Update documentation | NOT_STARTED | — | Manual review | — | — | Depends on OPT-001-A |
| OPT-002-A | Tool Count Guardrails | Add tool count validation at agent init | NOT_STARTED | — | Create agent with 16 tools; verify warning | — | — | Threshold configurable |
| OPT-002-B | Tool Count Guardrails | Add strict mode config option | NOT_STARTED | — | Enable strict mode; create agent with 16 tools; verify error | — | — | Depends on OPT-002-A |
| OPT-002-C | Tool Count Guardrails | Include tool count in agent listing | NOT_STARTED | — | Run `/agents list`; verify counts shown | — | — | Depends on OPT-003-A |
| OPT-003-A | Agent Registry | Implement `/agents list` command | NOT_STARTED | — | Run command; verify all agents displayed with metadata | — | — | New plugin |
| OPT-003-B | Agent Registry | Implement `/agents info <name>` | NOT_STARTED | — | Query known agent; verify detail output | — | — | Depends on OPT-003-A |
| OPT-003-C | Agent Registry | Implement `/agents validate` | NOT_STARTED | — | Run with known schema violation; verify detection | — | — | Depends on OPT-003-A |
| OPT-004-A | Provider Tool Filtering | Add `requires_tool_calling` field to schema | NOT_STARTED | — | Load agent without field; confirm no change | — | — | Backward compat gate |
| OPT-004-B | Provider Tool Filtering | Model capability registry | NOT_STARTED | — | Query capability map for known models | — | — | Extensible via config |
| OPT-004-C | Provider Tool Filtering | Validation on init + `/pin_model` | NOT_STARTED | — | Pin incompatible model; verify rejection with guidance | — | — | Depends on OPT-004-A + B |
| OPT-005-A | Shared Skill Files | Define skill file format + loader | NOT_STARTED | — | Create skill file; verify discovery and parse | — | — | New plugin |
| OPT-005-B | Shared Skill Files | Add `skills` array to JSON agent schema | NOT_STARTED | — | Agent without skills array works normally | — | — | Backward compat gate |
| OPT-005-C | Shared Skill Files | Skill injection into system prompt | NOT_STARTED | — | Create agent referencing skill; verify prompt includes skill content | — | — | Depends on OPT-005-A + B |
| OPT-005-D | Shared Skill Files | `/shared-skills list` and `/shared-skills info` commands | NOT_STARTED | — | Run commands; verify output | — | — | Depends on OPT-005-A |
| OPT-005-E | Shared Skill Files | Update agent-creator wizard for skill selection | NOT_STARTED | — | Run wizard; verify skill selection step | — | — | Depends on OPT-005-A + D |
| OPT-006-A | FallbackModel Hardening | Audit and disable conflicting SDK retries | NOT_STARTED | — | Trigger HTTP error; verify immediate fallback | — | — | Upgrade pydantic-ai first |
| OPT-006-B | FallbackModel Hardening | Configurable fallback chain | NOT_STARTED | — | Set chain in config; verify chain order on failure | — | — | Depends on OPT-006-A |
| OPT-006-C | FallbackModel Hardening | Fallback event logging | NOT_STARTED | — | Trigger fallback; verify log entry with source/target/error | — | — | Depends on OPT-006-A |
| OPT-007-A | Planning-Agent Delegation | Add `delegation_mode` field to schema | NOT_STARTED | — | Load agent without field; confirm default `subtask` behavior | — | — | Backward compat gate |
| OPT-007-B | Planning-Agent Delegation | Planning-agent respects delegation mode | NOT_STARTED | — | Set agent to handoff; verify conversation transfer | — | — | Depends on OPT-007-A |
| OPT-007-C | Planning-Agent Delegation | Multi-specialist forced subtask mode | NOT_STARTED | — | Task requiring 2+ specialists; verify subtask mode enforced | — | — | Depends on OPT-007-B |
| OPT-008-A | Provider Behavioral Tests | Test fixture framework | NOT_STARTED | — | Run empty framework; verify scaffold works | — | — | New test directory |
| OPT-008-B | Provider Behavioral Tests | 5+ behavioral test cases | NOT_STARTED | — | Run tests against available provider; verify matrix output | — | — | Depends on OPT-008-A |
| OPT-008-C | Provider Behavioral Tests | Integration with `/agents validate` | NOT_STARTED | — | Run validate with extended flag; verify behavioral tests included | — | — | Depends on OPT-003-C + OPT-008-B |
| OPT-009-A | Context Budget Monitoring | Token estimation at agent init | NOT_STARTED | — | Initialize agent; verify token estimate in logs | — | — | New plugin |
| OPT-009-B | Context Budget Monitoring | Warning on threshold exceeded | NOT_STARTED | — | Create agent with oversized prompt; verify warning | — | — | Depends on OPT-009-A |
| OPT-009-C | Context Budget Monitoring | `/context` command | NOT_STARTED | — | Run command; verify breakdown displayed | — | — | Depends on OPT-009-A |
| OPT-010-A | MCP Progressive Discovery | Two-phase tool loading | NOT_STARTED | — | Connect MCP server; verify metadata-only initial load | — | — | Client-side implementation |
| OPT-010-B | MCP Progressive Discovery | On-demand schema loading + caching | NOT_STARTED | — | Invoke tool; verify full schema loads and caches | — | — | Depends on OPT-010-A |
| OPT-010-C | MCP Progressive Discovery | Opt-out config per MCP server | NOT_STARTED | — | Set opt-out; verify full load at connect | — | — | Depends on OPT-010-A |
| OPT-010-D | MCP Progressive Discovery | Token savings reporting in `/mcp` | NOT_STARTED | — | Run `/mcp`; verify token count display | — | — | Depends on OPT-010-A |
| OPT-011-A | Prompt Caching Strategy | Audit existing ClaudeCacheAsyncClient | NOT_STARTED | — | Review current caching behavior; document gaps | — | — | Existing file! |
| OPT-011-B | Prompt Caching Strategy | Enable automatic caching for multi-turn | NOT_STARTED | — | Multi-turn session; verify cache hits in logs | — | — | Depends on OPT-011-A |
| OPT-011-C | Prompt Caching Strategy | Cache hit/miss metrics logging | NOT_STARTED | — | Run agent; verify cache metrics in output | — | — | Depends on OPT-011-B |

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

OPT-011-A ──→ OPT-011-B ──→ OPT-011-C

Cross-dependencies:
  OPT-001 → OPT-005 (skill_metadata used by shared skills)
  OPT-002 → OPT-003 (tool counts surfaced in /agents list)
  OPT-004 → OPT-006 (capability registry feeds fallback chain)
  OPT-003 → OPT-008 (/agents validate uses behavioral tests)
```

---

## Execution Phases

### Phase 1: Foundation Schema Extensions [Est. 3-4 hours]
*Backward-compatible schema additions. Can be parallelized.*

| Task | OPT | Agent | Files |
|------|-----|-------|-------|
| Add `skill_metadata` to JSON schema | OPT-001-A | code-puppy → python-reviewer | `json_agent.py`, `tests/test_json_agents.py` |
| Add tool count validation | OPT-002-A | code-puppy → python-reviewer | `base_agent.py`, `config.py` |
| Create `/agents` plugin scaffold | OPT-003-A | code-puppy | New `plugins/agent_registry/` |
| Add `requires_tool_calling` field | OPT-004-A | code-puppy | `json_agent.py` |
| Create shared_skills plugin scaffold | OPT-005-A+B | code-puppy | New `plugins/shared_skills/`, `json_agent.py` |
| Add `delegation_mode` field | OPT-007-A | code-puppy | `json_agent.py` |

### Phase 2: Core Logic [Est. 5-7 hours]
*Builds on Phase 1 schema extensions.*

| Task | OPT | Agent | Files |
|------|-----|-------|-------|
| Planning-agent metadata selection | OPT-001-B+C | code-puppy | `agent_planning.py`, `agent_tools.py`, `agent_manager.py` |
| Strict mode + wizard update | OPT-002-B, OPT-001-D | code-puppy | `base_agent.py`, `agent_creator_agent.py` |
| `/agents info` + `/agents validate` | OPT-003-B+C, OPT-002-C | code-puppy | `plugins/agent_registry/commands.py` |
| Model capability registry + validation | OPT-004-B+C | code-puppy | `model_utils.py`, pin command |
| Skill injection + commands | OPT-005-C+D+E | code-puppy | `json_agent.py`, `plugins/shared_skills/` |
| Planning-agent delegation logic | OPT-007-B+C | code-puppy | `agent_planning.py`, `agent_tools.py` |

### Phase 3: Resilience & Monitoring [Est. 4-6 hours]
*Independent features, parallelizable.*

| Task | OPT | Agent | Files |
|------|-----|-------|-------|
| FallbackModel SDK retry fix | OPT-006-A | code-puppy → security-auditor | `model_factory.py` |
| Fallback chain + logging | OPT-006-B+C | code-puppy | `model_factory.py`, `config.py` |
| Prompt caching audit + enable | OPT-011-A+B+C | code-puppy | `claude_cache_client.py`, `base_agent.py` |
| Context monitor plugin | OPT-009-A+B+C | code-puppy | New `plugins/context_monitor/` |

### Phase 4: Testing & MCP [Est. 5-7 hours]

| Task | OPT | Agent | Files |
|------|-----|-------|-------|
| Behavioral test framework | OPT-008-A+B | code-puppy → qa-expert | New `tests/behavioral/` |
| `/agents validate` integration | OPT-008-C | code-puppy | `plugins/agent_registry/` |
| MCP two-phase loading | OPT-010-A+B | code-puppy → security-auditor | `mcp_/manager.py`, `mcp_/registry.py` |
| MCP opt-out + reporting | OPT-010-C+D | code-puppy | `config.py`, MCP status command |

### Phase 5: Documentation & Finalization [Est. 2-3 hours]

| Task | OPT | Agent | Files |
|------|-----|-------|-------|
| Update docs + AGENTS.md | OPT-001-E, all | code-puppy | `AGENTS.md`, `README.md`, `docs/` |
| Update traceability matrix | — | code-puppy | This file |
| Final regression testing | — | qa-expert | All test files |

**Total estimated effort: 19-27 hours**

---

## Risks & Mitigations

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|-----------|
| 1 | `base_agent.py` is 85KB — any edit risks side-effects | Medium | High | Surgical edits only. Grep for exact insertion points. Run full test suite after each change. |
| 2 | "skills" naming collision with existing `agent_skills` plugin | High | Medium | Name new plugin `shared_skills`. Use `/shared-skills` command. Document the distinction. |
| 3 | MCP progressive discovery may break some MCP servers | Medium | Medium | Per-server opt-out config. Default to progressive but allow `"progressive_discovery": false`. |
| 4 | FallbackModel has no current usage in Code Puppy | Low | Low | Implement as optional feature gated by `fallback_chain` config. No impact when unconfigured. |
| 5 | Behavioral tests require live API calls (cost + latency) | High | Low | Mark with `@pytest.mark.behavioral`. Exclude from default runs. CI schedule only. |
| 6 | Plugin circular imports | Medium | High | Use lazy imports inside callback functions per CONTRIBUTING.md principle #8. |
| 7 | pydantic-ai-slim upgrade (1.56.0 → 1.67.0) may break things | Medium | High | Test thoroughly in isolation before combining with other changes. Check upgrade guide. |
| 8 | Claude 4.6 native subagent orchestration may conflict with explicit delegation logic | Low | Medium | Keep orchestration prompts lighter-touch. Test with Claude 4.6 specifically. |
| 9 | MCP spec may add progressive discovery natively, making OPT-010 redundant | Medium (1-2 years) | Low | Monitor spec evolution. Custom code is easily removable. |

---

## Sources & Citations

All sources are Tier 1 (official documentation) unless noted otherwise. Full research artifacts preserved in `./research/`.

### Pydantic AI Sources
| ID | Source | URL | Accessed |
|----|--------|-----|----------|
| S-PAI-1 | FallbackModel API Reference | https://ai.pydantic.dev/api/models/fallback/ | 2026-03-09 |
| S-PAI-2 | PR #894 — Add FallbackModel | https://github.com/pydantic/pydantic-ai/pull/894 | 2026-03-09 |
| S-PAI-3 | Issue #3267 — SDK Retry Conflict | https://github.com/pydantic/pydantic-ai/issues/3267 | 2026-03-09 |
| S-PAI-4 | PR #3294 — Retry Warning Docs | https://github.com/pydantic/pydantic-ai/pull/3294 | 2026-03-09 |
| S-PAI-5 | Multi-Agent Patterns | https://ai.pydantic.dev/multi-agent-applications/ | 2026-03-09 |
| S-PAI-6 | GitHub Releases | https://github.com/pydantic/pydantic-ai/releases | 2026-03-09 |

### Anthropic Sources
| ID | Source | URL | Accessed |
|----|--------|-----|----------|
| S-ANT-1 | Building Effective Agents | https://www.anthropic.com/engineering/building-effective-agents | 2026-03-09 |
| S-ANT-2 | Models Overview | https://platform.claude.com/docs/en/about-claude/models/overview | 2026-03-09 |
| S-ANT-3 | Prompt Caching | https://platform.claude.com/docs/en/build-with-claude/prompt-caching | 2026-03-09 |
| S-ANT-4 | Prompting Best Practices | https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices | 2026-03-09 |
| S-ANT-5 | Tool Use Overview | https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview | 2026-03-09 |
| S-ANT-6 | Tool Implementation | https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use | 2026-03-09 |

### OpenAI Sources
| ID | Source | URL | Accessed |
|----|--------|-----|----------|
| S-OAI-1 | Agents SDK Main | https://openai.github.io/openai-agents-python/ | 2026-03-09 |
| S-OAI-2 | Handoffs Docs | https://openai.github.io/openai-agents-python/handoffs/ | 2026-03-09 |
| S-OAI-3 | Agents Docs | https://openai.github.io/openai-agents-python/agents/ | 2026-03-09 |

### MCP Sources
| ID | Source | URL | Accessed |
|----|--------|-----|----------|
| S-MCP-1 | Tools Spec (2025-11-25) | https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2025-11-25/server/tools.mdx | 2026-03-09 |
| S-MCP-2 | Draft Changelog | https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/draft/changelog.mdx | 2026-03-09 |
| S-MCP-3 | Extensions Directory | https://github.com/modelcontextprotocol/modelcontextprotocol/tree/main/docs/extensions | 2026-03-09 |

---

## Core Rules (Self-Optimization Mode)

When implementing this plan, the agent operates under these rules:

1. **One change at a time.** Each traceability matrix row = exactly one change.
2. **Read before you write.** Read the current implementation in full before modifying.
3. **Test after every change.** Run the relevant test suite. Record pass/fail. Fix before proceeding.
4. **Preserve backward compatibility.** No optimization may break existing agents, commands, or MCP integrations.
5. **Update the matrix immediately.** After each implementation step, update status, files, test results, dates.
6. **When in doubt, do less.** Start simple. Flag over-engineered items for human review.

---

## Validation Checklist (Per Optimization)

For each optimization (all sub-tasks `PASSED`), verify:

- [ ] **Backward compatibility:** All existing agents, commands, and integrations work unchanged
- [ ] **Schema compliance:** JSON agent schema validates with and without new optional fields
- [ ] **Documentation updated:** Any new field, command, or behavior is documented
- [ ] **Error handling:** Invalid inputs produce clear, actionable error messages (not stack traces)
- [ ] **Logging:** Significant events (warnings, fallbacks, configuration loads) are logged with context
- [ ] **Traceability matrix current:** All rows updated with status, files, test results, and dates

---

## Change Log

| Date | Author | Change | Matrix Rows Affected |
|------|--------|--------|---------------------|
| — | Code Puppy | Initial v1.0 document creation | All (set to NOT_STARTED) |
| 2026-03-09 | Planning Agent + Web-Puppy | v2.0: Research validation, revised rationales, updated context budgets, added OPT-011, reframed OPT-001/002/009, added sources | All rows reviewed; OPT-011-A/B/C added |

# Pydantic AI Architecture Claims Validation

**Date:** 2026-03-09
**Researcher:** web-puppy-92a8ec
**Project:** Code Puppy (pydantic-ai-slim==1.56.0, mcp>=1.9.4)
**Latest Pydantic AI:** v1.67.0 (2026-03-06)
**Latest MCP Spec:** 2025-11-25 (draft has only minor changes)

---

## Executive Summary

Three technical claims from an optimization plan were validated against primary sources.
All three are **substantially correct** but require important nuance.

| # | Claim | Verdict | Confidence |
|---|-------|---------|------------|
| 1 | FallbackModel has provider SDK retry conflicts | ✅ **Confirmed** — documented issue #3267, fix merged Nov 2025 | **Very High** |
| 2 | Tool confusion increases above ~15 tools | ⚠️ **Directionally correct, but no hard threshold** — Anthropic recommends consolidation; no official number cited | **Medium** |
| 3 | MCP supports progressive/lazy tool discovery | ❌ **Not supported** — only pagination and listChanged; no lazy schema loading in spec or draft | **Very High** |

---

## Finding 1: Pydantic AI FallbackModel

### Version History
- **Introduced:** v0.0.36 (PR #894 by sydney-runkle, merged Feb 25, 2025)
- **Key improvements through v1.x:**
  - PR #1076/#1121/#1147 (Mar 2025): Instrumentation/span fixes
  - PR #2540 (Aug 13, 2025): Fixed respecting each model's settings
  - PR #2564 (Aug 15, 2025): Accept string model names
  - PR #3139 (Nov 18, 2025): Wrapped Google errors as ModelHTTPError for FallbackModel compatibility
  - PR #3294 (Nov 7, 2025): **Docs warning about implicit retries**
  - PR #3303 (Nov 5, 2025): Native/Prompted output mode support

### Current API (v1.67.0)
```python
from pydantic_ai.models.fallback import FallbackModel

model = FallbackModel(
    default_model,                    # Model | KnownModelName | str
    *fallback_models,                 # Model | KnownModelName | str
    fallback_on=(ModelAPIError,),     # tuple[type[Exception], ...] | Callable[[Exception], bool]
)
```

The API is **stable since v0.x** — the constructor signature and behavior have not changed.
Improvements have been additive (string names, better instrumentation, output mode support).

### ⚠️ CRITICAL: Provider SDK Retry Conflict (CONFIRMED)

**Issue #3267** (Oct 27, 2025) documents this problem precisely:

> "The FallbackModel documentation doesn't mention that underlying provider SDKs (like
> OpenAI SDK) (might) have built-in retry logic that can significantly delay or prevent
> the fallback model from being triggered."

**Root Cause:**
1. OpenAI SDK has `DEFAULT_MAX_RETRIES = 2` built-in
2. On 429 errors, it respects the `Retry-After` header (up to **60 seconds**)
3. These retries happen **before** FallbackModel ever sees the error
4. FallbackModel only activates after all SDK-level retries are exhausted

**Observed Symptom:**
```
{"event": "Retrying request to /chat/completions in 60.000000 seconds"}
```
Rate limit errors retry for extended periods instead of immediately falling back.

**Solution (from issue and PR #3294):**
```python
import openai

# Disable SDK-level retries
openai_client = openai.AsyncOpenAI(
    api_key=...,
    max_retries=0,  # Critical: disable SDK-level retries
)

openai_model = OpenAIModel('gpt-4o', openai_client=openai_client)
anthropic_model = AnthropicModel('claude-3-5-sonnet-latest')
fallback_model = FallbackModel(openai_model, anthropic_model)
```

**Code Puppy Impact:** Since Code Puppy uses both OpenAI and Anthropic providers
(openai>=1.99.1, anthropic==0.79.0), any FallbackModel implementation MUST disable
provider-level retries. The Anthropic SDK likely has similar behavior.

---

## Finding 2: Tool Count Limits

### What Anthropic's Current Docs Say (March 2026)

**From "How to implement tool use" → "Best practices for tool definitions":**

> "**Consolidate related operations into fewer tools.** Rather than creating a separate
> tool for every action (`create_pr`, `review_pr`, `merge_pr`), group them into a
> single tool with an `action` parameter. Fewer, more capable tools reduce selection
> ambiguity and make your tool surface easier for Claude to navigate."

> "**Use meaningful namespacing in tool names.** When your tools span multiple services
> or resources, prefix names with the service (e.g., `github_list_prs`,
> `slack_send_message`). This makes tool selection unambiguous as your library grows,
> and is especially important when using **tool search**."

**Key observations:**
1. **No specific numeric threshold** is cited in current Anthropic docs
2. Anthropic recommends **consolidation** (fewer, more capable tools) rather than citing a limit
3. Claude Opus (4.6) is recommended for "complex tools and ambiguous queries; it handles multiple tools better"
4. A new **"Tool search"** feature appears in the docs sidebar under "Tool infrastructure" — this is a provider-level feature that suggests Anthropic acknowledges the scaling problem with many tools
5. The `strict: true` option for guaranteed schema conformance was highlighted as important for production agents

### What the Academic Research Says

From previous research (July 2025) cross-referencing:
- **Gorilla LLM** (UC Berkeley, 2023): LLMs struggle with large API sets; retrieval-augmented approach improves tool selection
- **ToolBench** (2023): Open-source models significantly limited with large tool sets
- **Berkeley Function Calling Leaderboard**: Industry-standard benchmark for tool use

### Assessment of the "15 Tool" Claim

**Verdict: Directionally correct but imprecise.**

- There is **no official Anthropic or OpenAI guidance** citing "15" as a threshold
- Anthropic's guidance is **qualitative** ("consolidate," "fewer," "namespace") not quantitative
- The 2025 research concluded: "15 is conservative; real threshold is 20-30 for modern models, but context budget matters more"
- Modern models (Claude Opus 4.6, GPT-5.4) likely handle more tools than older models
- The new Anthropic "Tool search" feature suggests they're building infrastructure for 50+ tools
- **Description quality matters more than raw count** — 10 poorly described tools can confuse more than 25 well-described ones

### Practical Recommendations for Code Puppy

1. **Keep the ~15 heuristic as a soft guideline**, not a hard rule
2. **Invest more in tool description quality** — "3-4 sentences per tool description"
3. **Consolidate where possible** — use `action` parameters instead of separate tools
4. **Use namespacing** for multi-service tools
5. **Watch for Anthropic's "Tool search" feature** — could change the calculus entirely
6. **Consider `strict: true`** for production tool definitions

---

## Finding 3: MCP Progressive Discovery

### What MCP Spec (2025-11-25) Actually Supports

**Pagination — YES (since 2025-03-26):**
```json
// Request
{"jsonrpc": "2.0", "id": 1, "method": "tools/list",
 "params": {"cursor": "optional-cursor-value"}}

// Response
{"jsonrpc": "2.0", "id": 1, "result": {
  "tools": [...],
  "nextCursor": "next-page-cursor"
}}
```

**Dynamic Tool List Updates — YES:**
- Servers declare `listChanged` capability
- Send `notifications/tools/list_changed` when tool list changes
- Clients re-fetch with `tools/list`

**Progressive/Lazy Schema Loading — NO:**
- All tool schemas are delivered with `tools/list`
- No mechanism for "list names only, fetch schema on demand"
- No `tools/search` or `tools/getSchema` endpoint
- No way to request a subset of tools by category or tag

### Draft Spec (Next Revision) — No Changes

The draft changelog shows only:
1. Add `extensions` field to capabilities (for optional protocol extensions)
2. OpenTelemetry trace context propagation conventions

**No progressive discovery features planned.**

### MCP Extensions Directory

Only two extensions exist:
- `apps/` — Application extensions
- `auth/` — Authentication extensions

**No tool-search or progressive-loading extension.**

### Anthropic's "Tool Search" — Provider-Level Only

Anthropic's Claude API docs now list "Tool search" as a feature under "Tool infrastructure."
This is a **provider-level API feature**, not an MCP spec feature. It appears to be new
(sidebar link present but page may be incomplete as of March 2026).

### Implications for Two-Phase Tool Loading

Any two-phase tool loading pattern MUST be implemented at the **client/application layer**:

1. **Phase 1:** Fetch full tool list via `tools/list` (with pagination if needed), but only expose **metadata/names** to the LLM via a "discovery tool"
2. **Phase 2:** When the LLM selects a tool, register the full schema for that tool

This is exactly what Code Puppy's `skill_metadata` + `activate_skill` pattern does — it's
a sound architectural pattern that works *around* MCP's limitations rather than relying
on non-existent spec features.

**Key risk:** This pattern is entirely custom and has no MCP SDK support. It will need
maintenance as MCP and Pydantic AI evolve.

---

## Project-Specific Context

Code Puppy is on pydantic-ai-slim==1.56.0 (11 versions behind v1.67.0). Key improvements
since 1.56.0 that are relevant:
- FallbackModel improvements (settings, output modes, error wrapping)
- Google error wrapping for FallbackModel compatibility
- GPT-5.4 support (v1.67.0)
- Various MCP fixes

**Recommendation:** Upgrade to v1.67.0 to benefit from FallbackModel fixes and new model support.

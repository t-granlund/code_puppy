# Recommendations for Code Puppy

## Priority 1: Critical (Do Now)

### R1: Disable Provider SDK Retries with FallbackModel
**Confidence: Very High** | **Effort: Low** | **Impact: High**

When implementing FallbackModel in Code Puppy, configure all provider clients with
`max_retries=0`. Without this, rate limit errors will retry at the SDK level for up
to 60 seconds before FallbackModel even sees them.

```python
# In the model factory or register_model_type callback:
import openai
import anthropic

# OpenAI
openai_client = openai.AsyncOpenAI(max_retries=0)

# Anthropic
anthropic_client = anthropic.AsyncAnthropic(max_retries=0)
```

**Source:** GitHub Issue #3267, PR #3294 (merged, official recommendation)

### R2: Upgrade pydantic-ai-slim from 1.56.0 to 1.67.0
**Confidence: High** | **Effort: Medium** | **Impact: Medium**

11 versions behind. Key improvements:
- FallbackModel bug fixes (settings, output modes, error wrapping)
- Google provider FallbackModel compatibility
- GPT-5.4 support
- Various MCP fixes

**Risk:** Test thoroughly — there may be breaking changes across 11 minor versions.
Check the upgrade guide at https://ai.pydantic.dev/upgrade-guide/.

---

## Priority 2: Important (Plan This Sprint)

### R3: Keep the Skill Metadata Pattern — It's Validated
**Confidence: Very High** | **Effort: None** | **Impact: N/A (validation)**

Code Puppy's `skill_metadata` + `activate_skill` architecture directly mirrors
Anthropic's own recommendation to "consolidate related operations" and use
progressive disclosure. MCP does NOT provide native support for this pattern,
confirming that Code Puppy's client-side implementation is the correct approach.

### R4: Improve Tool Descriptions (Higher ROI Than Reducing Count)
**Confidence: High** | **Effort: Medium** | **Impact: High**

Anthropic's docs state descriptions are "by far the most important factor in tool
performance." Ensure all tools have:
- 3-4 sentence descriptions minimum
- Clear "when to use" and "when NOT to use" guidance
- Parameter descriptions with examples
- Consider `input_examples` for complex tools

### R5: Consider `strict: true` for Tool Definitions
**Confidence: High** | **Effort: Low** | **Impact: Medium**

Anthropic now offers `strict: true` on tool definitions for guaranteed schema
conformance. This eliminates type mismatches and missing fields — important for
production agents.

---

## Priority 3: Monitor (Track These)

### R6: Watch Anthropic's "Tool Search" Feature
A "Tool search" feature now appears in Anthropic's docs sidebar. If it provides
native server-side tool filtering, it could:
- Reduce the need for client-side progressive discovery
- Offer better tool selection for large tool sets
- Potentially integrate with MCP in future spec revisions

### R7: Monitor MCP Spec Evolution
The MCP spec's new `extensions` field in capabilities (draft) opens the door for
progressive loading as an optional extension. Monitor:
- https://github.com/modelcontextprotocol/modelcontextprotocol/tree/main/docs/specification/draft
- MCP GitHub issues tagged with tool-related labels

### R8: Track the "15 Tool" Heuristic Against Newer Models
As Claude Opus 4.6 and GPT-5.4 improve, the practical tool count limit likely
increases. Consider running your own benchmarks with Code Puppy's actual tool set
using Pydantic Evals.

---

## Summary Matrix

| # | Action | Priority | Effort | Source Confidence |
|---|--------|----------|--------|-------------------|
| R1 | Disable SDK retries with FallbackModel | 🔴 Critical | Low | Very High |
| R2 | Upgrade pydantic-ai-slim to 1.67.0 | 🔴 Critical | Medium | High |
| R3 | Keep skill metadata pattern | 🟡 Validate | None | Very High |
| R4 | Improve tool descriptions | 🟡 Important | Medium | High |
| R5 | Add `strict: true` to tools | 🟡 Important | Low | High |
| R6 | Monitor Anthropic Tool Search | 🟢 Watch | None | Medium |
| R7 | Monitor MCP spec evolution | 🟢 Watch | None | High |
| R8 | Benchmark tool counts on new models | 🟢 Watch | Medium | Medium |

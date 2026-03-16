# Multi-Dimensional Analysis

## 1. FallbackModel — Detailed Analysis

### Security Dimension
- **Risk:** Provider SDK retries can mask rate-limiting responses, causing unpredictable latency
- **Mitigation:** Set `max_retries=0` on all provider clients used with FallbackModel
- **Note:** The `fallback_on` parameter defaults to `(ModelAPIError,)` — ensure custom fallback conditions don't inadvertently catch security-relevant errors

### Cost Dimension
- **Without retry fix:** A 429 error can trigger 60-second SDK retry + additional API calls before fallback, wasting time and potentially billing for partial responses
- **With retry fix:** Immediate fallback minimizes wasted API spend
- **FallbackModel itself has no extra cost** — it's a client-side routing mechanism

### Implementation Complexity
- **Low:** FallbackModel API is straightforward and stable since v0.x
- **Gotcha:** Must configure each provider's client separately to disable retries
- **For Code Puppy specifically:** The `register_model_type` callback hook is the right place to set `max_retries=0` on provider clients when FallbackModel is used

### Stability
- **Mature:** 13+ months in production since Feb 2025
- **Well-tested:** 27 merged PRs addressing various edge cases
- **Active maintenance:** Google error wrapping (Nov 2025), output mode support (Nov 2025)
- **Breaking changes:** None identified; API additive only

### Compatibility with Code Puppy
- Code Puppy's `register_model_type` hook can handle FallbackModel setup
- The `load_models_config` callback can inject FallbackModel configurations
- Need to verify: Does Code Puppy's model factory already handle FallbackModel, or does it need a custom type handler?

---

## 2. Tool Count — Detailed Analysis

### What We Know vs. What We Don't

**Known (high confidence):**
- Anthropic recommends tool consolidation (fewer, more capable tools)
- Description quality is "by far the most important factor" in tool performance
- Modern models (Claude Opus 4.6) handle multiple tools better than older models
- Namespacing helps with large tool sets
- Anthropic built a "Tool search" feature — direct evidence they expect large tool sets

**Unknown (lower confidence):**
- No published quantitative threshold from any major provider
- The "15 tool" number is not traceable to an official source
- No published benchmarks testing tool counts specifically (BFCL tests function calling accuracy, not scaling)
- We don't know Anthropic's "Tool search" implementation details

### Practical Analysis for Code Puppy

Code Puppy currently uses the `agent_skills` pattern:
- `list_or_search_skills` — metadata-only discovery tool
- `activate_skill` — on-demand tool registration

This is **more sophisticated than just limiting tool count**. It's effectively a two-phase
approach that keeps the active tool set small while offering a large library.

**Token cost analysis:**
- Each tool definition costs ~200-500 tokens in context
- 15 tools ≈ 3,000-7,500 tokens of context overhead
- 30 tools ≈ 6,000-15,000 tokens of context overhead
- With 200K context windows, this is 1.5-7.5% — manageable
- But with tool schemas in system prompt, they're in the *highest attention position*

### Recommendation
The skill metadata pattern is better than any fixed tool count limit. Keep it.
The "15 tool" heuristic is reasonable as a default for *active* tools, but the
real constraint is description quality and context budget, not a hard count.

---

## 3. MCP Progressive Discovery — Detailed Analysis

### What MCP Actually Provides

| Feature | Status | Spec Version |
|---------|--------|-------------|
| `tools/list` with pagination | ✅ Supported | 2025-03-26+ |
| `listChanged` notifications | ✅ Supported | 2025-03-26+ |
| Tool annotations | ✅ Supported | 2025-11-25+ |
| Tool `title` field | ✅ Supported | 2025-11-25+ |
| Tool `icons` | ✅ Supported | 2025-11-25+ |
| `outputSchema` | ✅ Supported | 2025-11-25+ |
| Tool search endpoint | ❌ Not in spec | — |
| Lazy schema loading | ❌ Not in spec | — |
| Category/tag filtering | ❌ Not in spec | — |
| Schema-on-demand | ❌ Not in spec | — |

### The Gap

The MCP spec assumes a "list everything upfront" model:
1. Client calls `tools/list` (with pagination for large sets)
2. Client receives ALL tool definitions with FULL schemas
3. Client presents all tools to the LLM

For a server with 50+ tools, this means:
- All schemas loaded into memory
- All tool definitions injected into LLM context
- No way to load a subset based on user intent

### What Could Change

1. **Anthropic's "Tool search" feature** — provider-level, could influence future MCP spec
2. **MCP extensions framework** (draft spec) — could allow custom progressive loading
3. **Community proposals** — The `extensions` field in capabilities opens the door

### Code Puppy's Architecture Validation

Code Puppy's two-phase approach (`skill_metadata` → `activate_skill`) is:
- ✅ **Architecturally sound** — mirrors Anthropic's own recommendations
- ✅ **MCP-compatible** — works alongside MCP without conflicting
- ⚠️ **Custom implementation** — no framework support, maintenance burden
- ⚠️ **May become unnecessary** if Anthropic's Tool Search or a future MCP extension provides native support

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| MCP adds progressive loading, making custom code redundant | Medium (1-2 years) | Low (just remove custom code) | Monitor MCP spec evolution |
| Pydantic AI changes toolset API | Medium | Medium | Pin version, test on upgrade |
| Custom pattern breaks with new model behavior | Low | Medium | Eval suite for tool selection |
| Anthropic Tool Search obsoletes pattern | Medium | Low | Pattern is provider-agnostic |

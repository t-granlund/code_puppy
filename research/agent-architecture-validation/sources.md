# Sources & Credibility Assessment

**Research Date:** March 9, 2026

---

## Tier 1 Sources (Highest — Official Documentation & Primary Research)

### S1: Anthropic — "Building Effective AI Agents"
- **URL:** https://www.anthropic.com/engineering/building-effective-agents
- **Type:** Official engineering blog post
- **Authors:** Erik Schluntz and Barry Zhang (Anthropic)
- **Published:** December 2024 (original), still live March 2026
- **Credibility:** ★★★★★ — Primary source from Anthropic's own engineering team
- **Currency:** Still referenced by Anthropic's current docs. Patterns remain canonical.
- **Key content:** Defines workflow taxonomy (prompt chaining, routing, parallelization, orchestrator-workers, evaluator-optimizer) and autonomous agent patterns. Emphasizes simplicity, tool documentation, ACI design.
- **Bias assessment:** Low — engineering-focused, not marketing material. Framework-agnostic.
- **Verification:** Cross-referenced with current Anthropic documentation; patterns are consistent.

### S2: Anthropic — Claude API Docs: Models Overview
- **URL:** https://platform.claude.com/docs/en/about-claude/models/overview
- **Type:** Official API documentation
- **Last updated:** Current (references Claude Opus 4.6, Sonnet 4.6)
- **Credibility:** ★★★★★ — Primary source for model specifications
- **Key content:** Context windows (200K / 1M beta), max output tokens (64K–128K), pricing
- **Currency note:** Shows models up to Claude Opus 4.6 and Sonnet 4.6 as current

### S3: Anthropic — Claude API Docs: Prompt Caching
- **URL:** https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- **Type:** Official API documentation
- **Last updated:** Current (references workspace-level isolation change Feb 5, 2026)
- **Credibility:** ★★★★★ — Primary source for caching mechanics
- **Key content:** Automatic caching, explicit breakpoints, pricing, minimum cacheable lengths, 1-hour TTL option, cache invalidation rules
- **Relevance:** Critical for understanding context management strategies

### S4: Anthropic — Claude API Docs: Prompting Best Practices
- **URL:** https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- **Type:** Official prompt engineering guide
- **Last updated:** Current (references Claude 4.6 extensively)
- **Credibility:** ★★★★★ — Primary source for prompt engineering
- **Key content:** Long context tips, agentic systems guidance, subagent orchestration, context awareness, multi-context window workflows, state tracking
- **Critical finding:** Discusses Claude 4.6's native subagent orchestration and context awareness

### S5: Anthropic — Claude API Docs: Tool Use with Claude
- **URL:** https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview
- **Type:** Official API documentation
- **Last updated:** Current (references Claude Opus 4.6)
- **Credibility:** ★★★★★ — Primary source for tool use
- **Key content:** Client vs server tools, tool token overhead (~346 tokens per tool definition), MCP integration, tool search mention for scaling
- **Critical finding:** References "Advanced tool use" for scaling to hundreds of tools

### S6: Pydantic AI — Multi-Agent Patterns Documentation
- **URL:** https://ai.pydantic.dev/multi-agent-applications/
- **Type:** Official framework documentation
- **Last updated:** Current (references GPT-5.2, Gemini 3)
- **Credibility:** ★★★★★ — Primary source for the framework Code Puppy is built on
- **Key content:** Five levels of complexity (single agent → agent delegation → programmatic hand-off → graph-based → deep agents), delegation examples, dependency passing
- **Direct relevance:** Code Puppy is built on Pydantic AI; these patterns are immediately implementable

### S7: OpenAI — Agents SDK Documentation (Main)
- **URL:** https://openai.github.io/openai-agents-python/
- **Type:** Official SDK documentation
- **Last updated:** Current (references GPT-5.4, GPT-5-nano)
- **Credibility:** ★★★★★ — Primary source from OpenAI
- **Key content:** Agents, agents-as-tools/handoffs, guardrails, sessions, tracing

### S8: OpenAI — Agents SDK: Handoffs Documentation
- **URL:** https://openai.github.io/openai-agents-python/handoffs/
- **Type:** Official SDK documentation
- **Last updated:** Current
- **Credibility:** ★★★★★ — Primary source for handoff pattern
- **Key content:** Handoff mechanics, input filters, nested handoff history, input_type for metadata

### S9: OpenAI — Agents SDK: Agents Documentation
- **URL:** https://openai.github.io/openai-agents-python/agents/
- **Type:** Official SDK documentation
- **Last updated:** Current
- **Credibility:** ★★★★★ — Primary source for agent design patterns
- **Key content:** Explicitly documents "Manager (agents as tools)" vs "Handoffs" as the two multi-agent design patterns. Code examples for both.

---

## Sources Attempted But Not Accessible

| URL | Reason | Notes |
|-----|--------|-------|
| Google Search | CAPTCHA block | Automated browser detected |
| DuckDuckGo Search | CAPTCHA block | Automated browser detected |
| platform.openai.com/docs/guides/agents | Cloudflare protection | "Just a moment..." page |
| github.com/anthropics/claude-code | Rate limited | Too many requests |
| Various /engineering/ blog posts | 404 | Anthropic blog URL structure may have changed |

---

## Source Validation Matrix

| Claim | Primary Sources | Cross-References | Confidence |
|-------|----------------|-----------------|------------|
| "Agent Skills pattern" from Anthropic | S1 (no such named pattern) | S4 (subagent orchestration discussion) | High — claim is inaccurate as stated |
| Progressive loading concept valid | S1 (orchestrator-worker), S4 (context awareness) | S6 (agent delegation), S9 (agents as tools) | High — concept is sound, attribution is wrong |
| "50-65% effective context" | S2 (200K-1M windows), S4 (context awareness, 30% boost with placement) | S3 (caching strategies) | High — heuristic is outdated for current models |
| Subtask vs handoff patterns | S1 (orchestrator-workers), S9 (explicit dual pattern), S6 (delegation vs hand-off) | S7, S8 | Very high — industry consensus |
| Tool count ~15 threshold | S1 (mentions ~10 for coding agents), S5 (tool token overhead) | S4 (subagent delegation for scaling) | Medium — no exact number published, but <15 is safe |

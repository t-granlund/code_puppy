# Sources & Credibility Assessment

## Tier 1 — Primary Sources (Highest Credibility)

### S1: Anthropic — "Building Effective Agents"
- **URL:** https://www.anthropic.com/engineering/building-effective-agents
- **Published:** December 19, 2024
- **Type:** Official vendor engineering blog
- **Authority:** Anthropic's own engineering team; based on working with "dozens of teams"
- **Credibility:** ★★★★★ — Primary source from model creator
- **Used for:** Agent patterns, delegation, orchestration, tool use philosophy
- **Key quotes:** "The most successful implementations use simple, composable patterns rather than complex frameworks"; distinguishes workflows (predefined paths) from agents (LLM-directed)

### S2: Pydantic AI FallbackModel — Source Code
- **URL:** https://github.com/pydantic/pydantic-ai/blob/main/pydantic_ai_slim/pydantic_ai/models/fallback.py
- **Accessed:** 2025-07-17
- **Type:** Primary source code (latest `main` branch)
- **Authority:** Official Pydantic AI repository
- **Credibility:** ★★★★★ — The actual implementation
- **Used for:** FallbackModel behavior, exception handling, configuration options

### S3: Pydantic AI Official Documentation — Models & Providers
- **URL:** https://ai.pydantic.dev/models/
- **Accessed:** 2025-07-17
- **Type:** Official documentation
- **Authority:** Pydantic AI maintainers
- **Credibility:** ★★★★★ — Official docs
- **Used for:** FallbackModel usage, SDK retry configuration, known gotchas

### S4: MCP Specification — Tools (2025-03-26)
- **URL:** https://spec.modelcontextprotocol.io/specification/2025-03-26/server/tools/
- **Source file:** https://github.com/modelcontextprotocol/specification/blob/main/docs/specification/2025-03-26/server/tools.mdx
- **Type:** Protocol specification
- **Authority:** MCP working group (Anthropic-led)
- **Credibility:** ★★★★★ — The authoritative spec
- **Used for:** Tool listing/calling protocol, pagination, listChanged notifications

### S5: Pydantic AI — Multi-Agent Patterns Documentation
- **URL:** https://ai.pydantic.dev/multi-agent-applications/
- **Accessed:** 2025-07-17
- **Type:** Official documentation
- **Authority:** Pydantic AI maintainers
- **Credibility:** ★★★★★ — Official docs
- **Used for:** Agent delegation, agent-as-tool, hand-off patterns

### S6: Anthropic — Tool Use Best Practices & Limitations
- **URL:** https://docs.anthropic.com/en/docs/build-with-claude/tool-use/best-practices-and-limitations
- **Accessed:** 2025-07-17
- **Type:** Official vendor documentation
- **Authority:** Anthropic
- **Credibility:** ★★★★★
- **Used for:** Tool count guidance, tool descriptions best practices

### S7: Pydantic AI Exceptions Source Code
- **URL:** https://github.com/pydantic/pydantic-ai/blob/main/pydantic_ai_slim/pydantic_ai/exceptions.py
- **Accessed:** 2025-07-17
- **Type:** Source code
- **Credibility:** ★★★★★
- **Used for:** FallbackExceptionGroup, ModelAPIError, ModelHTTPError hierarchy

### S8: OpenAI Agents SDK — Handoffs Documentation
- **URL:** https://openai.github.io/openai-agents-python/handoffs/
- **Accessed:** 2025-07-17
- **Type:** Official SDK documentation
- **Authority:** OpenAI
- **Credibility:** ★★★★★
- **Used for:** Handoff pattern, agent delegation comparison

### S9: Pydantic AI FallbackModel Tests
- **URL:** https://github.com/pydantic/pydantic-ai/blob/main/tests/models/test_fallback.py
- **Type:** Test suite (945 lines)
- **Credibility:** ★★★★★ — Shows actual behavior and edge cases

## Tier 2 — Academic & Research Sources (High Credibility)

### S10: "Lost in the Middle" — Liu et al. (2023)
- **URL:** https://arxiv.org/abs/2307.03172
- **Published:** 2023, updated through 2024
- **Type:** Academic paper (Stanford, UC Berkeley, Samaya AI)
- **Credibility:** ★★★★☆ — Seminal paper, heavily cited, but models have improved since
- **Finding:** Language models perform worst retrieving information from the middle of long contexts; U-shaped performance curve

### S11: RULER Benchmark — Hsieh et al. (2024)
- **URL:** https://arxiv.org/abs/2404.06654
- **Published:** April 2024
- **Type:** Academic paper (Google)
- **Credibility:** ★★★★☆
- **Finding:** NIAH tests are insufficient; effective context length is much shorter than advertised for complex retrieval tasks

### S12: InfLLM — Xiao et al. (2024)
- **URL:** https://arxiv.org/abs/2404.07143
- **Published:** April 2024
- **Type:** Academic paper
- **Credibility:** ★★★★☆
- **Used for:** Context window management approaches

### S13: Gorilla LLM — Patil et al. (2023)
- **URL:** https://arxiv.org/abs/2305.15334
- **Published:** 2023
- **Type:** Academic paper (UC Berkeley)
- **Credibility:** ★★★★☆
- **Finding:** LLMs struggle with large API sets; retrieval-augmented approach for tool selection

### S14: ToolBench — Qin et al. (2023)
- **URL:** https://arxiv.org/abs/2307.16789
- **Published:** 2023
- **Type:** Academic paper
- **Credibility:** ★★★★☆
- **Finding:** Open-source models significantly limited in tool-use with large tool sets

### S15: Berkeley Function Calling Leaderboard (BFCL)
- **URL:** https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html
- **Accessed:** 2025-07-17
- **Type:** Benchmark
- **Credibility:** ★★★★☆ — Widely used industry benchmark

### S16: ToolSandbox — Lu et al. (2024)
- **URL:** https://arxiv.org/abs/2408.04682
- **Published:** August 2024
- **Type:** Academic paper (Apple)
- **Credibility:** ★★★★☆
- **Finding:** Comprehensive tool-use evaluation framework

## Tier 3 — Secondary Sources (Medium Credibility)

### S17: PyPI — pydantic-ai-slim Package Info
- **URL:** https://pypi.org/pypi/pydantic-ai-slim/json
- **Accessed:** 2025-07-17
- **Type:** Package registry
- **Credibility:** ★★★★☆
- **Used for:** Version verification (latest: 1.67.0 vs pinned 1.56.0)

### S18: Anthropic Claude Code — Sub-agents Documentation
- **URL:** https://docs.anthropic.com/en/docs/claude-code/sub-agents
- **Accessed:** 2025-07-17
- **Type:** Official product documentation
- **Credibility:** ★★★★★
- **Used for:** Real-world sub-agent implementation patterns

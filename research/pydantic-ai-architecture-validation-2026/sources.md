# Sources & Credibility Assessment

## Tier 1 — Primary Sources (Directly Verified)

### S1: Pydantic AI FallbackModel API Reference
- **URL:** https://ai.pydantic.dev/api/models/fallback/
- **Accessed:** 2026-03-09
- **Version:** v1.67.0 (latest)
- **Type:** Official API documentation with source code
- **Credibility:** ★★★★★
- **Key data:** Full API signature, source code lines 23-154, `fallback_on` parameter supports both tuple of exception types and callable

### S2: GitHub PR #894 — "Add FallbackModel support"
- **URL:** https://github.com/pydantic/pydantic-ai/pull/894
- **Author:** sydney-runkle (Pydantic core team)
- **Merged:** Feb 25, 2025
- **Type:** Primary source — the PR that introduced FallbackModel
- **Credibility:** ★★★★★
- **Key data:** FallbackModel was introduced around v0.0.36

### S3: GitHub Issue #3267 — "FallbackModel and Provider/Client SDK Retry Behavior"
- **URL:** https://github.com/pydantic/pydantic-ai/issues/3267
- **Opened:** Oct 27, 2025 by LysanderKie
- **Status:** Closed (fixed by PR #3294)
- **Type:** Bug report with detailed analysis
- **Credibility:** ★★★★★ — Confirmed by maintainers, fix merged
- **Key data:** OpenAI SDK `DEFAULT_MAX_RETRIES = 2`, Retry-After header up to 60s, solution is `max_retries=0`

### S4: GitHub PR #3294 — "Warn about implicit retries on FallbackModel docs"
- **URL:** https://github.com/pydantic/pydantic-ai/pull/3294
- **Author:** dsfaccini (Collaborator)
- **Merged:** Nov 7, 2025 by DouweM
- **Type:** Documentation fix
- **Credibility:** ★★★★★
- **Key data:** Official acknowledgment that provider SDK retries conflict with FallbackModel

### S5: MCP Specification — Tools (2025-11-25)
- **URL:** https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2025-11-25/server/tools.mdx
- **Accessed:** 2026-03-09
- **Type:** Protocol specification (full text extracted)
- **Authority:** MCP working group (Anthropic-led)
- **Credibility:** ★★★★★
- **Key data:** `tools/list` supports cursor-based pagination, `listChanged` notifications, no progressive/lazy loading, no tool search endpoint

### S6: MCP Draft Spec Changelog
- **URL:** https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/draft/changelog.mdx
- **Accessed:** 2026-03-09
- **Type:** Draft specification changelog
- **Credibility:** ★★★★★
- **Key data:** Only minor changes planned: extensions field, OpenTelemetry trace propagation. No progressive discovery features.

### S7: Anthropic — "How to implement tool use"
- **URL:** https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use
- **Accessed:** 2026-03-09
- **Type:** Official vendor documentation
- **Credibility:** ★★★★★
- **Key data:** "Consolidate related operations into fewer tools," namespacing guidance, "Tool search" feature in sidebar, Claude Opus 4.6 for complex multi-tool usage

### S8: Anthropic — "Tool use with Claude" Overview
- **URL:** https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview
- **Accessed:** 2026-03-09
- **Type:** Official vendor documentation
- **Credibility:** ★★★★★
- **Key data:** LAB-Bench FigQA and SWE-bench benchmarks cited, `strict: true` for schema conformance, `input_examples` support

### S9: GitHub Releases — pydantic/pydantic-ai
- **URL:** https://github.com/pydantic/pydantic-ai/releases
- **Accessed:** 2026-03-09
- **Type:** Official release history
- **Credibility:** ★★★★★
- **Key data:** Latest v1.67.0 (2026-03-06), searched for "fallback" across all releases

### S10: GitHub PR History for FallbackModel
- **URL:** https://github.com/pydantic/pydantic-ai/pulls?q=is%3Apr+FallbackModel+is%3Aclosed+sort%3Acreated-asc
- **Accessed:** 2026-03-09
- **Type:** Complete PR history (27 closed, 6 open)
- **Credibility:** ★★★★★
- **Key data:** Full evolution from PR #532 (first attempt, Jan 2025) through PR #3303 (Nov 2025)

### S11: MCP Extensions Directory
- **URL:** https://github.com/modelcontextprotocol/modelcontextprotocol/tree/main/docs/extensions
- **Accessed:** 2026-03-09
- **Type:** Protocol extensions repository
- **Credibility:** ★★★★★
- **Key data:** Only `apps/` and `auth/` extensions exist. No tool-search or progressive-loading extension.

### S12: MCP Specification Versions
- **URL:** https://github.com/modelcontextprotocol/modelcontextprotocol/tree/main/docs/specification
- **Accessed:** 2026-03-09
- **Type:** Specification version directory
- **Credibility:** ★★★★★
- **Key data:** Versions: 2024-11-05, 2025-03-26, 2025-06-18, 2025-11-25, draft

## Tier 2 — Cross-Referenced Sources

### S13: Previous Research (July 2025)
- **File:** ./research/agent-architecture-optimization/README.md
- **Researcher:** web-puppy-d58be4
- **Credibility:** ★★★★☆ — Well-sourced but 8 months old
- **Key data:** Validated 6 optimization approaches including tool counts, FallbackModel, MCP discovery

### S14: Anthropic — "Best practices and limitations" (archived URL)
- **URL:** https://docs.anthropic.com/en/docs/build-with-claude/tool-use/best-practices-and-limitations
- **Note:** URL now redirects to platform.claude.com; content appears reorganized into "How to implement tool use"
- **Credibility:** ★★★★★ (when originally accessed July 2025)
- **Previous finding:** Contained tool count guidance that informed the "15 tool" heuristic

## Sources NOT Available (Access Blocked)

### OpenAI Function Calling Documentation
- **URL:** https://platform.openai.com/docs/guides/function-calling
- **Status:** Blocked by Cloudflare CAPTCHA (automated browser access denied)
- **Impact:** Could not verify OpenAI-specific tool count guidance for March 2026

### Google/DuckDuckGo Search
- **Status:** Both blocked automated searches (CAPTCHA)
- **Impact:** Could not run broad web searches; relied on direct navigation to authoritative sources

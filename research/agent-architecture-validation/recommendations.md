# Project-Specific Recommendations for Code Puppy

**Research Date:** March 9, 2026
**Priority:** Immediate action items for the optimization plan

---

## Priority 1: Reframe OPT-001 (Skill Metadata Progressive Loading)

### Problem
The optimization plan claims progressive skill loading "aligns with Anthropic's Agent Skills pattern." No such named pattern exists in any Anthropic publication.

### Recommendation
**Keep the feature, fix the justification.**

Replace:
> "Adding optional `skill_metadata` aligns with Anthropic's Agent Skills pattern"

With:
> "Adding optional `skill_metadata` applies orchestrator-worker principles (Anthropic, 2024) to context management: the planning-agent sees compact agent descriptions during specialist selection, and full system prompts load only on invocation. This reduces context window consumption during the selection phase and improves planning quality."

### Additional Context
- Anthropic's orchestrator-worker pattern (S1) is the direct ancestor of this concept
- OpenAI's `agent.as_tool(tool_description=...)` achieves the same thing — the tool description acts as discovery metadata while the full agent config loads on invocation
- Pydantic AI's agent delegation pattern naturally supports this — the parent doesn't see the child's system prompt

### Implementation Note
Consider making `skill_metadata` auto-generatable: if not provided, generate a summary from the first 100 tokens of the system prompt. This ensures backward compatibility while providing metadata for all agents.

---

## Priority 2: Update Context Budget Guidance

### Problem
The optimization plan states "effective context ≈ 50–65% of advertised window." This was a reasonable heuristic for 2023-2024 models but is outdated for current-generation Claude 4.x and GPT-5.x models.

### Recommendation
**Update the architectural context section with tiered guidance:**

```markdown
### Context Budget Design Guidelines (Updated March 2026)

| Model Generation | Effective Capacity | Strategy |
|-----------------|-------------------|----------|
| Current (Claude 4.x, GPT-5.x) | ~80-90% with structured placement | Structure: docs first, queries last. Use XML tags. Leverage context awareness. |
| Previous (Claude 3.x, GPT-4.x) | ~65-75% | Place critical content in first and last 20%. Watch for "lost in the middle." |
| Legacy / Unknown | ~50-65% (conservative) | Minimize context, use aggressive summarization. |

#### Key Structuring Rules (from Anthropic Claude 4.6 docs):
1. Place longform data/documents at the **top** of the prompt
2. Place queries/instructions at the **bottom** (30% quality improvement)
3. Wrap distinct content sections in XML tags
4. Use prompt caching for repeated content (90% cost reduction on reads)
5. For tasks exceeding one context window, use multi-window workflows with state files
```

### Implementation Impact
- **OPT-001 (skill metadata):** Still valuable but less urgent — modern models handle larger contexts better
- **OPT-002 (tool count guardrails):** Slightly raise the threshold — with 346 tokens per tool, 15 tools = ~5,190 tokens, which is trivial in a 200K window. The guardrail should be about model confusion, not context exhaustion
- **Prompt caching:** Implement aggressively for system prompts, skill definitions, and tool schemas

---

## Priority 3: Validate Dual-Mode Agent Architecture

### Finding
Code Puppy's dual-mode agent architecture (subtask + handoff) is validated by industry consensus:

| Code Puppy Concept | Anthropic Equivalent | OpenAI Equivalent | Pydantic AI Equivalent |
|-------------------|---------------------|-------------------|----------------------|
| Subtask mode | Orchestrator-workers | Manager (agents as tools) | Agent delegation |
| Handoff mode | Routing | Handoffs | Programmatic agent hand-off |

### Recommendation
**No changes needed to the architectural approach.** The existing implementation is sound. However:

1. **Document the when-to-use-which decision framework:**
   - **Subtask:** Coding tasks, multi-file changes, research, parallel work, when parent needs to synthesize
   - **Handoff:** User-facing triage, domain-specific conversations, when specialist needs full history

2. **Adopt context filtering for subtask mode:**
   - OpenAI SDK's `input_filter` concept is valuable — control what context the specialist sees
   - In Code Puppy, this maps to controlling what message history is passed to delegate agents
   - Pydantic AI supports this via the `message_history` parameter on `agent.run()`

3. **Leverage Claude 4.6's native subagent orchestration:**
   - Claude 4.6 can decide to delegate proactively
   - Keep agent descriptions (tool descriptions) clear and concise to help the model select correctly
   - Add guidance in planning-agent's system prompt about when delegation IS and ISN'T warranted

---

## Priority 4: Update Tool Count Guidance (OPT-002)

### Finding
Anthropic's "Building Effective Agents" mentions that successful coding agents use <10 core tools. Code Puppy has 7 core tools. However, the 15-tool guardrail threshold needs context:

- Tool token overhead is ~346 tokens per tool definition (Claude 4.6)
- 15 tools = ~5,190 tokens — negligible in a 200K context window
- The real concern is **model confusion**, not context exhaustion
- Anthropic's tool use docs mention "tool search" for scaling to hundreds of tools

### Recommendation
- **Keep the 15-tool warning** but reframe it as a cognitive limit, not a context limit
- **Add tool search awareness** — research Anthropic's advanced tool use / tool search capability for future integration
- **Consider tool categorization** — grouping tools by domain (file ops, shell ops, agent ops) may help model selection even when count is high

---

## Priority 5: New Opportunity — Prompt Caching Strategy

### Finding
Anthropic's prompt caching (S3) offers significant optimization that isn't in the current plan:

- **Automatic caching** with 5-minute TTL — perfect for multi-turn coding sessions
- **1-hour caching** at 2x cost — useful for long-running agents  
- **90% cost reduction** on cached reads
- **Minimum cacheable:** 4,096 tokens (Opus 4.6), 2,048 tokens (Sonnet 4.6)

### Recommendation
Add a new optimization item:

```
### OPT-NEW: Prompt Caching Strategy
**Priority:** P1
**Rationale:** Prompt caching reduces cost by 90% on repeated system prompts,
tool definitions, and skill content. Every agent turn currently reprocesses
the full system prompt + tools.

**Implementation:**
- Enable automatic caching for all multi-turn conversations
- Use explicit cache breakpoints for system prompt + tool definitions
- Cache shared skill content that multiple agents use
- Consider 1-hour TTL for long-running agent sessions

**Expected impact:** 40-60% cost reduction on input tokens for typical sessions.
```

---

## Priority 6: Consider Native Subagent Orchestration

### Finding
Claude 4.6 documentation (S4) reveals the model now has **native subagent orchestration** — it can recognize when to delegate without explicit instruction. This is new compared to when the optimization plan was written.

### Implications for Code Puppy
- The planning-agent may benefit from lighter-touch orchestration prompts
- Over-specifying when to delegate may cause "overtriggering" (per Anthropic's warning)
- The model's own ability to manage context and delegation reduces the complexity needed in the orchestration layer

### Recommendation
Test Claude 4.6's native orchestration with Code Puppy's planning-agent before over-engineering the delegation logic. The model may already handle specialist selection well with just good tool descriptions.

---

## Summary Action Matrix

| Item | Priority | Effort | Impact | Action |
|------|----------|--------|--------|--------|
| Reframe OPT-001 justification | P0 | Low | Medium | Update documentation/rationale only |
| Update context budget guidance | P0 | Low | High | Update architectural context section |
| Implement prompt caching | P1 | Medium | High | New optimization item |
| Add tool categorization | P1 | Medium | Medium | Enhance OPT-002 scope |
| Document subtask vs handoff decision framework | P1 | Low | Medium | Add to agent creation docs |
| Test Claude 4.6 native orchestration | P2 | Medium | High | May simplify planning-agent design |
| Research advanced tool search | P2 | Low | Medium | Future-proofing for tool scaling |

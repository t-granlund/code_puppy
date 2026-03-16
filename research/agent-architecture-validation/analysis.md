# Multi-Dimensional Analysis

**Research Date:** March 9, 2026

---

## Topic 1: "Anthropic's Agent Skills Pattern" — Progressive Skill Loading

### What Anthropic Actually Says

**From "Building Effective Agents" (S1):**
Anthropic defines these agentic patterns:
1. **Augmented LLM** — base building block with tools, retrieval, memory
2. **Prompt chaining** — sequential steps with validation gates
3. **Routing** — classify input, direct to specialized follow-up
4. **Parallelization** — sectioning or voting across parallel LLM calls
5. **Orchestrator-workers** — "central LLM dynamically breaks down tasks, delegates them to worker LLMs, and synthesizes their results"
6. **Evaluator-optimizer** — generate then evaluate in a loop
7. **Autonomous agents** — LLMs using tools in a feedback loop

There is **no pattern called "Agent Skills"** in any Anthropic publication. There is no mention of "progressive skill loading" or "metadata-first discovery."

**From Prompting Best Practices (S4, Claude 4.6):**
```
"Claude's latest models demonstrate significantly improved native subagent
orchestration capabilities. These models can recognize when tasks would benefit
from delegating work to specialized subagents and do so proactively."
```

This suggests Claude 4.6 already handles agent selection natively. The model itself decides when to delegate, reducing the need for explicit metadata-based discovery.

**However, S4 also warns:**
```
"Watch for overuse: Claude Opus 4.6 has a strong predilection for subagents
and may spawn them in situations where a simpler, direct approach would suffice."
```

### Analysis: Is Progressive Skill Loading a Good Idea?

| Dimension | Assessment |
|-----------|------------|
| **Alignment with Anthropic** | Not a named pattern, but consistent with orchestrator-worker principles and context efficiency goals |
| **Implementation Complexity** | Low — adding an optional `skill_metadata` field to JSON agent schema is minimal code change |
| **Context Efficiency** | High value — prevents loading full system prompts into planning-agent's context window during selection |
| **Compatibility** | Excellent — backward compatible (field is optional), works with existing Pydantic AI agent delegation |
| **Risk** | Low — falls back to current behavior when metadata absent |
| **Maintenance** | Minimal — one additional optional field |

### Verdict

The concept is **architecturally sound** even though it's not an Anthropic-named pattern. The key insight — showing agents a summary during selection rather than full system prompts — is a valid context window optimization that maps to how orchestrator-workers should function.

**Recommendation:** Keep OPT-001 but reframe the justification. Don't claim it's "Anthropic's pattern." Instead:
> "Progressive skill loading applies orchestrator-worker principles to context management: the orchestrator sees agent metadata for selection, and full prompts load only on invocation."

---

## Topic 2: Context Window Effective Capacity

### Current State of Model Context Windows (March 2026)

| Model | Context Window | Max Output | Notes |
|-------|---------------|------------|-------|
| Claude Opus 4.6 | 200K / 1M (beta) | 128K | Adaptive thinking, context awareness |
| Claude Sonnet 4.6 | 200K / 1M (beta) | 64K | Extended/adaptive thinking |
| Claude Haiku 4.5 | 200K | 64K | Fastest model |
| GPT-5.2 | Referenced in Pydantic AI docs | — | Current OpenAI flagship |
| GPT-5-nano | Referenced in OpenAI SDK | — | Lightweight model |

### What Has Changed Since the "50-65%" Heuristic

**1. Context Awareness (New in Claude 4.x):**
From S4: Claude 4.6 and 4.5 models "feature context awareness, enabling the model to track its remaining context window throughout a conversation." This means the model actively manages its own context budget — a fundamental change from earlier models that had no self-knowledge of remaining capacity.

**2. Long Context Performance Improvements:**
From S4: "Queries at the end can improve response quality by up to 30% in tests, especially with complex, multi-document inputs." This suggests the "lost in the middle" problem that drove the 50-65% heuristic has been significantly mitigated.

**3. Multi-Context Window Workflows:**
Anthropic now recommends working across multiple context windows with state persistence rather than trying to fit everything in one window:
- Write state to files between windows
- Use git for checkpoint tracking
- Start fresh rather than compacting when possible

**4. Prompt Caching Fundamentals:**
From S3: Prompt caching now supports automatic caching, 1-hour TTL, up to 4 explicit breakpoints, and workspace-level isolation. This changes the economics of context usage — cached content is 90% cheaper to read.

### Analysis: What Should the Guidance Be?

| Era | Heuristic | Reasoning |
|-----|-----------|-----------|
| 2023-2024 (GPT-4, Claude 2/3) | 50-65% effective | "Lost in the middle" problem, no context awareness, poor long-context retrieval |
| 2025-early 2026 (Claude 3.5/4, GPT-4o/5) | 70-80% effective | Improved long-context handling, but still some degradation at extremes |
| Current (Claude 4.6, GPT-5.x) | **80-90% with proper structuring** | Context awareness, improved retrieval, structured placement strategies |

The **key insight** from current docs is that the constraint has shifted from **capacity** to **structure**:
- Place long documents at the TOP
- Place queries at the BOTTOM  
- Use XML tags for clear delineation
- Use prompt caching for repeated context
- Leverage multi-window workflows for truly massive tasks

### Verdict

The "50-65%" heuristic is **outdated for current-generation models** but remains a **conservative safety margin** that prevents context-related failures. For Code Puppy:

**Recommendation:**
- Update guidance to: **"Design for 80% effective capacity with structured placement. Use 50-65% as fallback for unknown or mixed-generation model deployments."**
- Add context structuring guidelines (docs first, queries last) to agent system prompts
- Implement prompt caching aggressively for repeated system prompts and skill definitions
- Consider multi-context-window workflows for very large tasks

---

## Topic 3: Multi-Agent Delegation Patterns — Subtask vs Handoff

### Industry Consensus (Cross-Source Analysis)

All three major AI agent frameworks now explicitly document the same two patterns:

#### Pattern 1: Subtask / Agent-as-Tool / Orchestrator-Worker

| Framework | Name | Mechanism | Parent Control |
|-----------|------|-----------|---------------|
| **Anthropic** | Orchestrator-workers | Central LLM breaks tasks, delegates, synthesizes | ✅ Parent retains control |
| **OpenAI Agents SDK** | Manager (agents as tools) / `as_tool()` | Sub-agent exposed as a tool | ✅ Parent retains control |
| **Pydantic AI** | Agent delegation | Agent called within a tool, returns result | ✅ Parent retains control |

**When to use:** Complex coding tasks, multi-file changes, research gathering, any task where the parent needs to synthesize results from multiple specialists.

**Key characteristics:**
- Parent agent maintains conversation ownership
- Child agent runs in bounded scope, returns results
- Parent can invoke multiple children sequentially or in parallel
- Usage/costs tracked across parent and child (Pydantic AI: pass `ctx.usage`)

#### Pattern 2: Handoff / Agent Hand-Off / Transfer

| Framework | Name | Mechanism | Parent Control |
|-----------|------|-----------|---------------|
| **Anthropic** | Routing (closest analog) | Classify input, direct to specialist | ❌ Specialist takes over |
| **OpenAI Agents SDK** | Handoffs | `transfer_to_<agent>` tool | ❌ Child takes over conversation |
| **Pydantic AI** | Programmatic agent hand-off | Application code decides next agent | ❌ Next agent takes over |

**When to use:** Customer support triage, domain-specific conversations, when the next agent needs full conversation history, when a specialist is better equipped to handle the entire remaining task.

**Key characteristics:**
- Conversation ownership transfers to the child
- The child sees full conversation history (configurable via input filters in OpenAI SDK)
- No automatic return to parent
- Best for triage/routing scenarios

### What's New in 2025-2026

**1. OpenAI's Explicit Dual Pattern:**
OpenAI Agents SDK (S9) now officially documents both patterns as first-class:
```python
# Subtask pattern
customer_facing_agent = Agent(
    tools=[
        booking_agent.as_tool(tool_name="booking_expert", ...),
        refund_agent.as_tool(tool_name="refund_expert", ...),
    ],
)

# Handoff pattern
triage_agent = Agent(
    handoffs=[booking_agent, refund_agent],
)
```

**2. Pydantic AI's Five Levels:**
Pydantic AI (S6) now defines five distinct levels of multi-agent complexity:
1. Single agent
2. **Agent delegation** (subtask)
3. **Programmatic agent hand-off** (handoff)
4. Graph-based control flow
5. Deep agents (autonomous)

**3. Anthropic's Native Subagent Orchestration (Claude 4.6):**
From S4: Claude 4.6 can natively decide when to delegate to subagents without explicit instruction. This means the orchestrator pattern can be partly automated:
```
"Use subagents when tasks can run in parallel, require isolated context,
or involve independent workstreams that don't need to share state."
```

**4. Nested Handoff History (OpenAI SDK, beta):**
OpenAI's SDK now supports `nest_handoff_history` — collapsing prior conversation into a summary when handing off. This is a hybrid between subtask and handoff, allowing conversation transfer with context compression.

### Analysis for Code Puppy

| Dimension | Subtask Mode | Handoff Mode |
|-----------|-------------|-------------|
| **Use in Code Puppy** | planning-agent → specialist delegation | Not currently used |
| **Alignment with Coding** | ★★★★★ — Primary pattern for coding agents | ★★☆☆☆ — Better for conversational triage |
| **Context efficiency** | High — child sees only relevant context | Lower — child sees full history |
| **Result synthesis** | Easy — parent collects and synthesizes | Hard — no parent to synthesize |
| **Error handling** | Parent can retry/fallback | No parent to handle errors |
| **Pydantic AI support** | ✅ Direct — agent called within tool | ✅ Direct — sequential agent runs |

### Verdict

Code Puppy's existing architecture with **subtask as the default mode** is the **correct choice** and aligns with industry consensus for coding agents. The handoff mode should be available but reserved for specific scenarios (user-facing triage, long-running conversational tasks).

**Recommendation:** 
- Keep subtask as default for `planning-agent → specialist` delegation
- Document when to use handoff mode in agent creation guidelines
- Consider adopting OpenAI SDK's `input_filter` concept for controlling what context specialists see
- Leverage Claude 4.6's native subagent orchestration by keeping agent/tool descriptions clear and concise

---

## Cross-Cutting Concerns

### Prompt Caching Impact on Architecture

The availability of prompt caching (S3) significantly impacts several optimization decisions:

1. **System prompt caching:** Skill definitions and system prompts can be cached at 10% read cost. This reduces the urgency of progressive skill loading for cost reasons (though context window reasons remain valid).

2. **Tool definition caching:** Tool definitions are cacheable. With 346 tokens overhead per tool (S5), caching 15 tools saves ~5,190 tokens of reprocessing per turn.

3. **Multi-turn conversations:** Automatic caching handles growing conversation history efficiently. The cache breakpoint moves forward automatically.

### Model Generation Considerations

The optimization plan was likely written when Claude 3.5 Sonnet was current. As of March 2026:
- **Claude Opus 4.6** is the flagship (200K context, 128K output, adaptive thinking)
- **Claude Sonnet 4.6** is the speed/intelligence balance (200K context, 64K output)
- Models now have **native context awareness** and **subagent orchestration**

Some optimizations in the plan may be less critical than originally anticipated because the models themselves have become more capable at managing context and delegation.

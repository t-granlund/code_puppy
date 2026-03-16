# Multi-Agent Patterns: Cross-Framework Comparison

**Retrieved:** March 9, 2026

---

## OpenAI Agents SDK — Explicit Dual Pattern (S9)

> "There are many ways to design multi-agent systems, but we commonly see two broadly applicable patterns:
> 1. Manager (agents as tools): A central manager/orchestrator invokes specialized sub-agents as tools and retains control of the conversation.
> 2. Handoffs: Peer agents hand off control to a specialized agent that takes over the conversation. This is decentralized."

### Manager Pattern Code:
```python
customer_facing_agent = Agent(
    name="Customer-facing agent",
    tools=[
        booking_agent.as_tool(
            tool_name="booking_expert",
            tool_description="Handles booking questions and requests.",
        ),
        refund_agent.as_tool(
            tool_name="refund_expert",
            tool_description="Handles refund questions and requests.",
        )
    ],
)
```

### Handoff Pattern Code:
```python
triage_agent = Agent(
    name="Triage agent",
    handoffs=[booking_agent, refund_agent],
)
```

---

## Pydantic AI — Five Levels of Complexity (S6)

> "There are roughly five levels of complexity when building applications with Pydantic AI:
> 1. Single agent workflows
> 2. Agent delegation — agents using another agent via tools
> 3. Programmatic agent hand-off — one agent runs, then application code calls another agent
> 4. Graph based control flow
> 5. Deep Agents — autonomous agents with planning, file operations, task delegation"

### Agent Delegation (Subtask) Example:
```python
@joke_selection_agent.tool
async def joke_factory(ctx: RunContext[None], count: int) -> list[str]:
    r = await joke_generation_agent.run(
        f'Please generate {count} jokes.',
        usage=ctx.usage,  # Pass usage tracking
    )
    return r.output  # Parent retains control
```

### Key Design Notes:
- "Agents are stateless and designed to be global"
- "Pass ctx.usage to the usage keyword argument of the delegate agent run so usage within that run counts towards the total usage of the parent agent run"
- Delegate agents can use different models from calling agents

---

## OpenAI Agents SDK — Handoff Details (S8)

Key handoff features:
- `input_filter`: Controls what history the receiving agent sees
- `on_handoff`: Callback when handoff is invoked
- `input_type`: Schema for handoff metadata (reason, priority, etc.)
- `nest_handoff_history` (beta): Collapses prior transcript into summary

> "Handoffs stay within a single run. Input guardrails still apply only to the first agent in the chain, and output guardrails only to the agent that produces the final output."

---

## Anthropic — Orchestrator-Workers (S1)

> "In the orchestrator-workers workflow, a central LLM dynamically breaks down tasks, delegates them to worker LLMs, and synthesizes their results."

> "This workflow is well-suited for complex tasks where you can't predict the subtasks needed (in coding, for example, the number of files that need to be changed and the nature of the change in each file likely depend on the task)."

---

## Pattern Decision Matrix (Synthesized)

| Scenario | Recommended Pattern | Rationale |
|----------|-------------------|-----------|
| Coding: multi-file changes | Subtask/Manager | Parent needs to synthesize across files |
| Coding: single specialist task | Subtask/Manager | Results return to orchestrator |
| Customer support triage | Handoff | Specialist handles full conversation |
| Research across domains | Subtask/Manager | Orchestrator collects and synthesizes |
| Step-by-step workflow | Programmatic hand-off | Application controls sequence |
| Complex state machine | Graph-based (Pydantic AI) | Multiple paths, conditions, loops |

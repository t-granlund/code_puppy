# Key Excerpts: Anthropic Prompting Best Practices — Agentic Systems

**Source:** https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
**Retrieved:** March 9, 2026 (Current — references Claude 4.6)

---

## Long Context Prompting
> "Put longform data at the top: Place your long documents and inputs near the top of your prompt, above your query, instructions, and examples. This can significantly improve performance across all models."
> "Queries at the end can improve response quality by up to 30% in tests, especially with complex, multi-document inputs."

## Context Awareness (Claude 4.6)
> "Claude 4.6 and Claude 4.5 models feature context awareness, enabling the model to track its remaining context window (i.e. 'token budget') throughout a conversation."

## Multi-Context Window Workflows
> "For tasks spanning multiple context windows:"
> - "Use the first context window to set up a framework (write tests, create setup scripts)"
> - "Have the model write tests in a structured format"
> - "Set up quality of life tools: Encourage Claude to create setup scripts"
> - "Starting fresh vs compacting: When a context window is cleared, consider starting with a brand new context window rather than using compaction."

## Subagent Orchestration
> "Claude's latest models demonstrate significantly improved native subagent orchestration capabilities. These models can recognize when tasks would benefit from delegating work to specialized subagents and do so proactively without requiring explicit instruction."

> "Ensure well-defined subagent tools: Have subagent tools available and described in tool definitions"
> "Let Claude orchestrate naturally: Claude will delegate appropriately without explicit instruction"
> "Watch for overuse: Claude Opus 4.6 has a strong predilection for subagents and may spawn them in situations where a simpler, direct approach would suffice."

## Guidance for Subagent Use
> "Use subagents when tasks can run in parallel, require isolated context, or involve independent workstreams that don't need to share state. For simple tasks, sequential operations, single-file edits, or tasks where you need to maintain context across steps, work directly rather than delegating."

## Overeagerness Warning
> "Claude Opus 4.5 and Claude Opus 4.6 have a tendency to overengineer by creating extra files, adding unnecessary abstractions, or building in flexibility that wasn't requested."

## Tool Usage (Claude 4.6)
> "Claude Opus 4.5 and Claude Opus 4.6 are also more responsive to the system prompt than previous models. If your prompts were designed to reduce undertriggering on tools or skills, these models may now overtrigger."

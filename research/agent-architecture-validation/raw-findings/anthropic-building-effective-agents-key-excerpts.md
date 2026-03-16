# Key Excerpts: Anthropic — Building Effective AI Agents

**Source:** https://www.anthropic.com/engineering/building-effective-agents
**Authors:** Erik Schluntz, Barry Zhang (Anthropic)
**Retrieved:** March 9, 2026

---

## On Simplicity
> "When building applications with LLMs, we recommend finding the simplest solution possible, and only increasing complexity when needed."

## On Frameworks
> "We suggest that developers start by using LLM APIs directly: many patterns can be implemented in a few lines of code."

## On Orchestrator-Workers
> "In the orchestrator-workers workflow, a central LLM dynamically breaks down tasks, delegates them to worker LLMs, and synthesizes their results."
> "This workflow is well-suited for complex tasks where you can't predict the subtasks needed (in coding, for example, the number of files that need to be changed and the nature of the change in each file likely depend on the task)."

## On Tool Design (ACI)
> "One rule of thumb is to think about how much effort goes into human-computer interfaces (HCI), and plan to invest just as much effort in creating good agent-computer interfaces (ACI)."
> "While building our agent for SWE-bench, we actually spent more time optimizing our tools than the overall prompt."

## On Tool Format
> "Give the model enough tokens to 'think' before it writes itself into a corner."
> "Keep the format close to what the model has seen naturally occurring in text on the internet."

## Three Core Principles for Agents
> 1. Maintain simplicity in your agent's design.
> 2. Prioritize transparency by explicitly showing the agent's planning steps.
> 3. Carefully craft your agent-computer interface (ACI) through thorough tool documentation and testing.

## On Coding Agents
> "Code solutions are verifiable through automated tests; Agents can iterate on solutions using test results as feedback; The problem space is well-defined and structured; Output quality can be measured objectively."

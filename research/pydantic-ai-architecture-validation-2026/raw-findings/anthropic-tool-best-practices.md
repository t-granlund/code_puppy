# Anthropic Tool Best Practices (March 2026)

Source: https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use

## "Best practices for tool definitions" Section (Exact Text)

> To get the best performance out of Claude when using tools, follow these guidelines:

### 1. Provide extremely detailed descriptions
> This is by far the most important factor in tool performance. Your descriptions
> should explain every detail about the tool, including:
> - What the tool does
> - When it should be used (and when it shouldn't)
> - What each parameter means and how it affects the tool's behavior
> - Any important caveats or limitations, such as what information the tool does
>   not return if the tool name is unclear. The more context you can give Claude
>   about your tools, the better it will be at deciding when and how to use them.
>   Aim for at least 3-4 sentences per tool description, more if the tool is complex.

### 2. Prioritize descriptions, but consider using `input_examples` for complex tools
> Clear descriptions are most important, but for tools with complex inputs, nested
> objects, or format-sensitive parameters, you can [provide examples]

### 3. Consolidate related operations into fewer tools
> Rather than creating a separate tool for every action (`create_pr`, `review_pr`,
> `merge_pr`), group them into a single tool with an `action` parameter. Fewer,
> more capable tools reduce selection ambiguity and make your tool surface easier
> for Claude to navigate.

### 4. Use meaningful namespacing in tool names
> When your tools span multiple services or resources, prefix names with the
> service (e.g., `github_list_prs`, `slack_send_message`). This makes tool
> selection unambiguous as your library grows, and is especially important when
> using **tool search**.

### 5. Design tool responses to return only high-signal information
> Return semantic, stable identifiers (e.g., slugs or UUIDs) rather than opaque
> internal references, and include only the fields Claude needs to reason about
> its next step. Bloated responses waste context and make it harder for Claude
> to extract what matters.

## "Choosing a model" Section
> Use the latest Claude Opus (4.6) model for complex tools and ambiguous queries;
> it handles multiple tools better and seeks clarification when needed.
>
> Use Claude Haiku models for straightforward tools, but note they may infer
> missing parameters.

## New Features Observed
- **"Tool search"** — appears in sidebar under "Tool infrastructure" (new section)
- **"Programmatic tool calling"** — new
- **"Fine-grained tool streaming"** — new
- **`strict: true`** — guarantees schema conformance on tool inputs
- **"Context management" section** — includes context windows, compaction, context editing, prompt caching

## Notable Absence
**No specific numeric tool count limit or threshold is mentioned anywhere in the
current documentation.** The guidance is entirely qualitative: consolidate, describe
well, namespace, return less.

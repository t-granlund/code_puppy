# 🐶 How to Use Code Puppy with Cerebras Code Pro

This guide covers how to use Code Puppy effectively with Cerebras Code Pro, including the new **Token Efficient Mode** for optimized token usage.

## Cerebras Code Pro Limits

Understanding your limits is key to efficient usage:

| Limit | Value | Notes |
|-------|-------|-------|
| Requests per Minute (RPM) | 50 | Pace your requests |
| Tokens per Minute (TPM) | 1,000,000 | Input + output combined |
| Daily Token Limit | 24,000,000 | Plan for ~8-hour workday |

**Key insight**: The daily limit means ~3M tokens per hour, or ~50K per minute. The bottleneck is usually **input tokens** - keeping your context small is critical.

---

## Token Efficient Mode for Cerebras Code Pro

### Quick Start

1. Switch to the token-efficient agent:
   ```text
   /agent pack-leader-cerebras-efficient
   ```

2. Set optional budget tuning:
   ```text
   /set cerebras_token_budget = 50000
   /set cerebras_output_limit = 200
   ```

3. Use `/truncate 6` regularly to keep history lean.

### What This Agent Does Differently

The `pack-leader-cerebras-efficient` agent enforces these rules:

1. **Diff-Driven Workflow**: Prefers `git diff` and small file snippets over full file reads
2. **Output Limiting**: All shell commands capped to 200 lines by default
3. **Micro-Patch Rule**: Max 2 files per iteration, unified diff only (120 lines max)
4. **Truncation Reminders**: Prompts you every 2 iterations to run `/truncate 6`
5. **Budget Guard**: Warns when context approaches token budget

### Example Session Commands

```text
# Start with efficient agent
/agent pack-leader-cerebras-efficient

# Check current context size
/status

# Truncate history to last 6 messages
/truncate 6

# Use summarization instead of truncation
/set compaction_strategy = summarization
/compact
```

### Sample Token-Efficient Prompt

```text
Fix the failing test in test_auth.py.

Use only:
- git diff to see recent changes
- grep to find the specific test
- Read only the failing test function (not the whole file)
- Show fix as unified diff only
```

---

## Runbook: Avoiding Token Burn

### Before Starting Work

1. **Start fresh**: Run `/truncate 6` or `/session rotate`
2. **Use efficient agent**: `/agent pack-leader-cerebras-efficient`
3. **Set model**: `/model Cerebras-GLM-4.6` or your preferred Cerebras model

### During Work

1. **Every 2-3 exchanges**: Check `/status` for message count
2. **Every 5 exchanges**: Run `/truncate 6` to clear history
3. **Large file requests**: Ask for specific line ranges only
4. **Test output**: Always use `pytest -q --tb=short`

### Signs You're Burning Tokens

- Responses getting slower
- Agent repeating context from earlier
- "Token limit" or "context too long" errors
- Running out of daily quota before day ends

### Emergency Token Recovery

```text
# Nuclear option: fresh context
/session rotate

# Aggressive truncation
/truncate 4

# Switch to summarization mode
/set compaction_strategy = summarization
/compact
```

---

## Multi-Provider Strategy

For complex projects, consider this division of labor:

| Provider | Best For | Notes |
|----------|----------|-------|
| **Cerebras Code Pro** | Primary coding, fast iteration | Minimize input tokens per request |
| **Claude Max** | Architecture, deep debugging | 200K context, but pace usage |
| **ChatGPT Teams** | Planning, copywriting, research | Good for non-code tasks |
| **Google AI Pro** | Multimodal, UX review | Images and diagrams |

### Pinning Models to Agents

```text
# Use Cerebras for main coding
/model Cerebras-GLM-4.6

# Pin Claude for complex reviews
/pin_model code-reviewer claude-code-claude-opus-4-1-20250805

# Pin Haiku for fast validation
/pin_model python-reviewer claude-code-claude-haiku-4-5-20251001
```

---

## Basic Setup Guide

### 1. First Startup & The "Enter" Quirk
After installation, run `code-puppy` in your terminal.
1.  **Name your agent:** Enter any name (e.g., `PuppyBot`).
2.  **The Blank Enter:** Once the tool starts, **hit `Enter` one time** on the blank line.
    *   *Note: The tool often fails to recognize commands like `/set` until this first blank enter is registered.*

### 2. Configuration & Model Pinning
Copy and paste these commands one by one to set up your keys, authentication, and model bindings.

```text
/set cerebras_api_key = "YOUR_API_KEY_HERE"
/set yolo_mode = true

/claude-code-auth 
```
*(Follow the browser instructions to authenticate Claude)*

```text
/model Cerebras-GLM-4.6
/pin_model planning-agent claude-code-claude-opus-4-1-20250805
/pin_model code-reviewer claude-code-claude-haiku-4-5-20251001
/pin_model python-reviewer claude-code-claude-haiku-4-5-20251001
```
*(Note: You can pin different reviewers depending on your language needs, e.g., java-reviewer)*

### 3. Restart
**Close and restart** Code Puppy. This ensures all configurations and pinned models are loaded correctly.

### 4. Running the Planning Agent
To start a task, always switch to the planning agent first. It will plan, verify with you, and then drive the other agents.

```text
/agent planning-agent 
```

### 5. Prompting Strategy
Copy and paste the prompt below to ensure the agent implements features, reviews them automatically, and avoids running the backend prematurely.

```markdown
Your task is to implement "REQUIREMENTS.MD".

For that use code-puppy to implement. Use python-reviewer to verify the implementation. If there are errors give the feedback to code_puppy to fix. Repeat until the reviewer has no more "urgent" fixes, maximum 3 times.

During development never execute the backend. Only verify with compiling!

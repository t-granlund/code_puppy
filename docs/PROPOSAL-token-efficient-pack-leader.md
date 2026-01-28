# Feature Proposal: Token-Efficient Pack Leader Agent for Cerebras Code Pro

**To:** mpfaffenberger  
**From:** Tyler Granlund  
**Date:** January 28, 2026  
**Re:** New agent profile for minimizing token usage on Cerebras Code Pro

---

Hi Matt,

I've been working on an enhancement to Code Puppy that I'd like to share with you. It addresses a real problem I've encountered when using Cerebras Code Pro as the primary coding model.

## The Problem

Cerebras Code Pro has excellent rate limits on paper:
- 50 requests per minute
- 1,000,000 tokens per minute  
- 24 million tokens per day

But in practice, I kept burning through my daily quota too fast. The issue isn't the model—it's **context bloat**. Agent packs accumulate large message histories, and every request sends the full context. When you're doing iterative coding with file reads, test outputs, and diffs, the input tokens per request grow rapidly.

A typical pattern:
1. Read a 500-line file → 2,000 tokens
2. Run tests, get output → 1,500 tokens  
3. Read another file → 2,000 tokens
4. Now every subsequent request includes all of that → 5,500+ tokens of context

By request #10, you're sending 20K+ tokens per request. Multiply by the back-and-forth of agent coordination, and you're through your daily budget by lunch.

## The Solution

I created a new agent profile called `pack-leader-cerebras-efficient` that enforces strict token economy through behavioral constraints rather than code changes:

### 1. Diff-Driven Workflow
- Prefers `git diff` and `sed -n 'start,end p'` over full file reads
- Refuses to read entire large files—asks for specific line ranges
- Uses `grep` to locate code sections before reading

### 2. Command Output Limiter  
- All shell output capped to 200 lines (configurable)
- Test runs use `pytest -q --tb=short` by default
- Prevents log files and verbose output from bloating context

### 3. Micro-Patch Rule
- Maximum 2 files modified per iteration
- Changes shown as unified diff only (max 120 lines)
- Forces incremental, reviewable changes

### 4. Truncation Cadence
- Agent reminds user every 2 iterations to run `/truncate 6`
- Keeps conversation history from growing unbounded

### 5. Token Budget Guard
- Estimates context size (~2.5 chars/token heuristic)
- Warns when approaching configurable budget (default 50K)
- Suggests narrowing requests before continuing

## What I Built

| File | Purpose |
|------|---------|
| `code_puppy/agents/agent_pack_leader_cerebras_efficient.py` | The new agent with token-efficient system prompt |
| `code_puppy/tools/token_budget_guard.py` | Utilities for token estimation, output limiting, budget warnings |
| `tests/test_token_budget_guard.py` | 18 unit tests for the utilities |
| `docs/CEREBRAS.md` | Updated with Token Efficient Mode guide + runbook |

Also updated model references from GLM-4.6 → GLM-4.7 throughout.

## Usage

```bash
/agent pack-leader-cerebras-efficient
/set cerebras_token_budget = 50000  # optional tuning
```

The agent's system prompt does the heavy lifting—no changes to core agent infrastructure needed.

## Questions / Sanity Check

A few things I wanted to run by you:

1. **Is behavioral enforcement the right approach?** I chose to encode token discipline into the system prompt rather than adding hard limits in code. This keeps the implementation simple but relies on the model following instructions. Should there be actual enforcement (e.g., truncating tool outputs programmatically)?

2. **Integration with existing pack agents?** The pack dogs (bloodhound, husky, shepherd, etc.) don't have this optimization. Should there be a "cerebras-efficient" variant for each, or is the pack leader sufficient since it orchestrates?

3. **Round-robin synergy?** The existing `RoundRobinModel` distributes requests across API keys. Combined with token-efficient prompting, this could maximize throughput. Worth documenting as a recommended pattern?

4. **Token budget guard placement?** Currently it's utilities-only. Should it hook into `base_agent.py` to warn automatically, or is opt-in via the specific agent sufficient?

## What's Missing

If you like this direction, future enhancements could include:

- **Smart router**: Route by task type (code → Cerebras, architecture → Claude, research → ChatGPT)
- **Usage telemetry**: Track tokens per session to spot patterns
- **Auto-compaction**: Trigger `/compact` automatically when budget threshold hit
- **Per-agent budgets**: Different limits for different agents in the pack

## The Branch

I have this ready locally on `feature/token-efficient-pack-leader`. I don't have push access to the repo, so let me know how you'd like me to submit it—I can push to a fork and open a PR, or send you the patch files directly.

Let me know what you think!

Best,  
Tyler

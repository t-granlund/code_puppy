# Token Optimization Overview

This document summarizes all token efficiency optimizations implemented in code_puppy.

---

## 1. Cerebras Optimizer (`code_puppy/cerebras_optimizer.py`)

The Cerebras model has strict limits (50K input tokens, 24M daily). The optimizer manages this through:

### Sliding Window Compaction
- **What**: Keeps only the last N request/response exchanges, discarding older history
- **Why**: Prevents context from growing unbounded across long sessions
- **Config**: `max_exchanges: 4` (aggressive, was 6)

### Orphan Tool Result Filtering
- **What**: Removes `tool-return` messages whose corresponding `tool-call` was compacted away
- **Why**: Tool results without their calls confuse the model and waste tokens
- **How**: Tracks `tool_call_id` from ModelResponse parts, only keeps returns with matching calls

### Task-Aware Max Tokens
- **What**: Dynamically adjusts `max_tokens` based on detected task type
- **Why**: Tool calls need ~300 tokens, code generation needs ~3000
- **Task Types**: TOOL_CALL, CODE_GENERATION, EXPLANATION, PLANNING, REVIEW, UNKNOWN

### Budget Thresholds (Aggressive)
| Metric | Value | Trigger |
|--------|-------|---------|
| Compaction Threshold | 30% (15K tokens) | Start sliding window |
| Hard Limit | 50% (25K tokens) | Block new requests |
| Target Input | 15K tokens | Compaction target |

### Max Output by Task Type
| Task | Max Tokens |
|------|------------|
| TOOL_CALL | 300 |
| CODE_GENERATION | 3000 |
| EXPLANATION | 1800 |
| PLANNING | 1200 |
| REVIEW | 1500 |
| UNKNOWN | 1500 |

---

## 2. IO Budget Enforcer (`code_puppy/tools/io_budget_enforcer.py`)

Prevents tools from returning excessive output that bloats context.

### Budget Categories
- **FULL**: Complete output (for small results)
- **SUMMARIZED**: Compressed with key info preserved
- **TRUNCATED**: Hard cut with "...truncated" marker
- **ERROR_ONLY**: Just error messages, no stdout

### Per-Tool Limits
Each tool has configured limits for stdout/stderr based on typical usage patterns.

### Narrowing Modes
1. **ERROR_ONLY**: Only show errors (most aggressive)
2. **HEADS_TAILS**: Show first/last N lines
3. **SMART_SUMMARY**: Extract key information

---

## 3. Compaction Strategy (`code_puppy/agents/compaction_strategy.py`)

Intelligent message history compression beyond simple truncation.

### Strategies
1. **Sliding Window**: Keep last N exchanges (default for Cerebras)
2. **Summarization**: Use smaller model to summarize older context
3. **Selective Pruning**: Remove low-value messages (acknowledgments, retries)

### Integration with Agents
- `base_agent.py` uses `CEREBRAS_LIMITS["max_exchanges"]` for dynamic configuration
- Compaction runs automatically when thresholds exceeded

---

## 4. Model Factory Optimizations (`code_puppy/model_factory.py`)

### Cerebras-Specific Settings
```python
if "cerebras" in model_name.lower():
    max_tokens = 1500  # Reduced from 2000
```

### Token Counting
- Pre-flight token estimation before requests
- Warns when approaching limits

---

## 5. Summarization Agent (`code_puppy/summarization_agent.py`)

Uses a smaller, cheaper model to compress conversation history.

### When Used
- Before compaction, to preserve important context
- For long-running sessions approaching limits

### Output
- Condensed summary replacing multiple messages
- Preserves: decisions made, files modified, current task

---

## 6. Usage Analysis Results

Based on `cerebras_usage_NEW.csv` (2,517 requests analyzed):

| Metric | Before Optimization | Target |
|--------|---------------------|--------|
| Avg tokens/request | 28,326 | <15,000 |
| Input:Output ratio | 87:1 | Maintain |
| Daily limit usage | 99% | <80% |

### Session Efficiency Trend
| Session | Avg Tokens | Status |
|---------|------------|--------|
| 1-5 | 30,000-40,000 | Pre-optimization |
| 6-8 | 20,000-25,000 | Partial optimization |
| 9-11 | 11,000-16,000 | Full optimization |

---

## 7. Configuration Summary

### CEREBRAS_LIMITS (Current Aggressive Settings)
```python
CEREBRAS_LIMITS = {
    "compaction_threshold": 0.30,      # Trigger at 30% (15K tokens)
    "hard_limit_threshold": 0.50,      # Block at 50% (25K tokens)
    "target_input_tokens": 15_000,     # Target after compaction
    "max_exchanges": 4,                # Keep last 4 exchanges
    "max_input_tokens": 50_000,        # Cerebras limit
    "max_output_by_task": {...},       # Task-specific limits
    "default_max_output": 1500,        # Fallback limit
}
```

---

## 8. Audit Trail

| Audit | Focus | Status |
|-------|-------|--------|
| AUDIT-1.0 | Initial compaction implementation | ✅ Complete |
| AUDIT-1.1 | Orphan tool result filtering | ✅ Complete |
| AUDIT-1.2 | Cerebras optimizer deep dive | ✅ Complete |

---

## 9. Key Files

| File | Purpose |
|------|---------|
| `cerebras_optimizer.py` | Main optimization logic |
| `io_budget_enforcer.py` | Tool output limiting |
| `compaction_strategy.py` | Message history compression |
| `summarization_agent.py` | Context summarization |
| `model_factory.py` | Model-specific configurations |
| `base_agent.py` | Agent integration with limits |

---

## 10. Logfire Telemetry for Capacity Management

All token optimization features emit **real-time telemetry** via Pydantic Logfire:

| Event | Level | Purpose |
|-------|-------|---------|
| `capacity_warning` | WARN | Emitted at ≥80% usage, enables proactive failover |
| `rate_limit` | WARN | Tracks 429 errors with `consecutive_429s` counter |
| `workload_routing` | INFO | Verifies correct model assignment (CODING→GLM-4.7) |

### Health Check Queries
See [LOGFIRE-OBSERVABILITY.md](LOGFIRE-OBSERVABILITY.md) for SQL queries to verify:
- ✅ CODING workload uses GLM-4.7 (not Kimi-K2.5)
- ✅ Capacity warnings precede rate limits
- ✅ Failover triggers when capacity warnings accumulate

---

## 11. Recommendations for Further Optimization

1. **Monitor live usage** after aggressive limits deployed
2. **Tune task detection** if wrong max_tokens assigned frequently
3. **Consider model switching** for simple tasks (use smaller model)
4. **Implement token caching** for repeated tool calls
5. **Add metrics dashboard** to track efficiency over time
6. **Use Logfire** to correlate capacity warnings with failover patterns

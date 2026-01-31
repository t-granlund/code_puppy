# Token Optimization Audit Report

**Date**: 2026-01-30  
**Status**: ✅ FIXES IMPLEMENTED

## Executive Summary

Three overlapping but disconnected token optimization systems existed in the codebase. 
**This has now been fixed** - token_slimmer is now used for ALL providers, not just Cerebras.

### Changes Made (2026-01-30)

1. **Added `_detect_provider()` method** in `base_agent.py`
   - Correctly maps all 15+ production models to their provider keys
   - Handles failover detection via `_last_model_name`
   
2. **Rewrote `message_history_processor()`**  
   - Now uses `token_slimmer` for ALL providers (Claude Code, Antigravity, ChatGPT, etc.)
   - Diet-themed logging: 🏋️ Boot Camp, 🥗 Balanced, 🍽️ Maintenance

3. **Added deprecation notice to `io_budget_enforcer.py`**
   - 652 lines of dead code marked for future cleanup

4. **Added test coverage**: `tests/test_provider_detection.py` (24 tests)

---

## System Inventory

### 1. `tools/token_slimmer.py` (713 lines) 🟡 PARTIALLY USED

**Purpose**: Universal provider-aware token optimization engine.

**Features**:
- Provider-specific `PROVIDER_LIMITS` dict with thresholds for:
  - `cerebras`: Boot camp mode (20% compaction threshold, 8K target, 3 max exchanges)
  - `antigravity`: Balanced (50% threshold, 40K target, 8 max exchanges)  
  - `claude_code`: Balanced (60% threshold, 80K target, 10 max exchanges)
  - `chatgpt_teams`: Balanced (55% threshold, 50K target)
  - `anthropic`: Relaxed (70% threshold, 100K target)
  - `openai`: Relaxed (65% threshold, 60K target)
- Task-type aware output limits
- Sliding window compaction

**Current Usage**:
```
token_slimmer.py ← imported by cerebras_optimizer.py ← imported by base_agent.py:1246
```

**Problem**: Only accessed when `_is_cerebras_model()` returns True.

---

### 2. `tools/io_budget_enforcer.py` (652 lines) 🔴 DEAD CODE

**Purpose**: Hard caps on input/output tokens per request with auto-compaction.

**Features**:
- `PROVIDER_BUDGETS` dict with hard limits:
  - `cerebras`: 50K input, 4K output, 80% hard fail
  - `antigravity`: 100K input, 8K output, 90% hard fail
  - `claude_code`: 180K input, 8K output, 90% hard fail
  - `chatgpt_teams`: 120K input, 16K output, 90% hard fail
- File reading limits: 200 lines, 3K tokens per read
- Slice enforcement policies

**Current Usage**: 
```
❌ NOT IMPORTED ANYWHERE IN THE CODEBASE
```

**Problem**: 652 lines of sophisticated budget enforcement that does nothing.

---

### 3. `core/token_budget.py` (697 lines) 🟡 USED

**Purpose**: Token bucket rate limiting (tokens/minute, tokens/day).

**Features**:
- Per-minute and daily budget tracking
- `PROVIDER_LIMITS` with rate limits (separate from token_slimmer!)
- Failover chain suggestions when budget exhausted
- Cost tracking with genai-prices

**Current Usage**:
```
base_agent.py:2046 → TokenBudgetManager.check_budget()
pack_governor.py, model_router.py, failover_model.py
```

**Problem**: Only CHECKS budget, doesn't slim tokens when approaching limit.

---

### 4. `core/rate_limit_failover.py` (702 lines) ✅ USED

**Purpose**: Workload-aware failover chains for 429 errors.

**Features**:
- `WorkloadType` enum (ORCHESTRATOR, REASONING, CODING, LIBRARIAN)
- `WORKLOAD_CHAINS` with tier-appropriate fallbacks
- OAuth model discovery

**Current Usage**: Used by `failover_model.py`, `pack_governor.py`, `agent_orchestration.py`

**No problems**, but could integrate with token slimmer for pre-emptive slimming.

---

## Flow Analysis

### Cerebras Flow (When failover active) ✅ WORKING

```
1. TokenBudgetManager.check_budget() → Check rate budget
2. PydanticAgent runs with history_processors
3. message_history_accumulator() called
   └── message_history_processor() called
       └── _is_cerebras_model() == True → cerebras_optimizer called
           └── apply_sliding_window() → Tokens compressed
4. Request sent with slimmed context
```

### Non-Cerebras Flow (Claude, Antigravity, etc.) ⚠️ SUBOPTIMAL

```
1. TokenBudgetManager.check_budget() → Check rate budget
2. PydanticAgent runs with history_processors
3. message_history_accumulator() called
   └── message_history_processor() called
       └── _is_cerebras_model() == False → SKIP token_slimmer
       └── Falls through to old compaction_threshold logic
       └── Uses config-based threshold (not provider-aware)
4. Request sent with possibly bloated context
```

---

## Redundancy Matrix

| Constant | token_slimmer | io_budget_enforcer | token_budget |
|----------|---------------|-------------------|--------------|
| cerebras.max_input_tokens | 50,000 | 50,000 | N/A (uses rate limits) |
| cerebras.compaction_threshold | 0.20 | 0.50 | N/A |
| antigravity.max_input_tokens | 100,000 | 100,000 | N/A |
| claude_code.max_input_tokens | 180,000 | 180,000 | N/A |

Values are duplicated but not shared!

---

## Recommended Fixes

### Phase 1: Wire Up Token Slimmer for ALL Providers (High Priority)

Modify `message_history_processor()` to use token_slimmer for all providers, not just Cerebras:

```python
def message_history_processor(self, ctx: RunContext, messages: List[ModelMessage]):
    # Get provider from current model
    provider = self._detect_provider()  # New method
    
    # Use token_slimmer for ALL providers
    from code_puppy.tools.token_slimmer import (
        get_provider_limits,
        apply_sliding_window,
        SlidingWindowConfig,
    )
    
    limits = get_provider_limits(provider)
    if limits:
        budget_check = check_budget(message_tokens, limits)
        if budget_check.should_compact:
            config = SlidingWindowConfig(max_exchanges=limits["max_exchanges"])
            compacted, result = apply_sliding_window(messages, config, ...)
            return compacted
    
    # Fall through to summarization only if no provider config
```

### Phase 2: Consolidate or Remove io_budget_enforcer

Options:
1. **Delete**: Merge useful parts into token_slimmer
2. **Integrate**: Import and use for file read limits (the unique value)

Recommendation: Merge file reading limits into token_slimmer, delete redundant parts.

### Phase 3: Sync PROVIDER_LIMITS Across Modules

Create single source of truth:

```python
# code_puppy/core/provider_limits.py
UNIFIED_PROVIDER_LIMITS = {
    "cerebras": {...},
    "antigravity": {...},
    ...
}
```

Import this in `token_slimmer.py`, `io_budget_enforcer.py`, and `token_budget.py`.

### Phase 4: Pre-Request Slimming in TokenBudgetManager

Add token slimming BEFORE the budget check triggers failover:

```python
def check_and_slim_budget(self, provider, messages, estimate_fn):
    """Check budget and slim tokens if needed, BEFORE triggering failover."""
    from code_puppy.tools.token_slimmer import apply_sliding_window
    
    estimated = sum(estimate_fn(m) for m in messages)
    limits = self.get_provider_limits(provider)
    
    if estimated > limits.warning_threshold * limits.max_input:
        # Slim first, then re-check
        slimmed, result = apply_sliding_window(messages, ...)
        return self.check_budget(provider, result.compacted_tokens), slimmed
    
    return self.check_budget(provider, estimated), messages
```

---

## Test Coverage Analysis

```
tests/test_cerebras_optimizer.py ✅ 62 tests
tests/test_token_budget.py ✅ Covers token_budget.py
tests/test_io_budget_enforcer.py ❌ DOES NOT EXIST (dead code untested)
tests/test_token_slimmer.py ❌ DOES NOT EXIST
```

Need to add tests for:
1. token_slimmer provider-awareness
2. Cross-provider sliding window
3. Integration tests for full optimization path

---

## Files to Modify

1. **`base_agent.py`** (~50 lines): Extend `message_history_processor` for all providers
2. **`token_slimmer.py`** (~30 lines): Add `get_provider_limits(model_name)` helper
3. **`io_budget_enforcer.py`**: Extract file limits, delete rest (or full delete)
4. **New `core/provider_limits.py`**: Single source of truth for limits

---

## Verification Checklist

After fixes:
- [ ] `grep -rn "io_budget_enforcer"` returns 0 (or proper imports)
- [ ] All providers show optimization logs in verbose mode
- [ ] Pre-failover slimming reduces 429 cascade frequency
- [ ] Test: 100K token Claude context → auto-compacted before sending
- [ ] Test: Cerebras still gets boot camp treatment

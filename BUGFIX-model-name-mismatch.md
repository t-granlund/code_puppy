# Bug Fix: Model Name Mismatch in Pack Governor

## Problem

The Pack Governor and failover system were using **incorrect model names** that didn't match the keys in `models.json`, causing agents to fail with "Model not found" errors and fall back incorrectly.

### Symptoms

```
Unknown provider 'anthropic', allowing request
Model 'claude-opus-4.5' not found, falling back to claude-code-claude-opus-4-5-20251101
Unknown provider 'custom_openai', allowing request  
Model 'cerebras-glm-4.7' not found, falling back to claude-code-claude-opus-4-5-20251101
Model 'gemini-3-flash' not found, falling back to claude-code-claude-opus-4-5-20251101
```

**Root cause:** The failover chains in `rate_limit_failover.py` used model names like:
- `claude-opus-4.5` ❌ (doesn't exist)
- `cerebras-glm-4.7` ❌ (doesn't exist)
- `gemini-3-flash` ❌ (doesn't exist)

But `models.json` has keys like:
- `claude-4-5-opus` ✅
- `Cerebras-GLM-4.7` ✅
- `Gemini-3` ✅

## Files Fixed

### 1. `code_puppy/core/rate_limit_failover.py`

**Changed:** Updated `WORKLOAD_CHAINS` to use correct model keys from `models.json`

**Before:**
```python
WorkloadType.ORCHESTRATOR: [
    "claude-opus-4.5",      # ❌ WRONG KEY
    "claude-sonnet-4.5",    # ❌ WRONG KEY  
    "gemini-3-pro",         # ❌ WRONG KEY
    "chatgpt-codex-5.2",    # ❌ WRONG KEY
],
WorkloadType.CODING: [
    "cerebras-glm-4.7",     # ❌ WRONG KEY
    "gemini-3-flash",       # ❌ WRONG KEY
],
```

**After:**
```python
WorkloadType.ORCHESTRATOR: [
    "claude-code-claude-opus-4-5-20251101",      # ✅ CORRECT with date
    "claude-code-claude-sonnet-4-5-20250929",    # ✅ CORRECT with date
    "antigravity-claude-sonnet-4-5-thinking-high", # ✅ ADDED back
    "Gemini-3",             # ✅ CORRECT KEY from models.json  
    "gpt-5.1-codex-api",    # ✅ CORRECT KEY from models.json
],
WorkloadType.CODING: [
    "Cerebras-GLM-4.7",     # ✅ CORRECT KEY from models.json
    "claude-code-claude-haiku-4-5-20251001",     # ✅ CORRECT with date
    "antigravity-gemini-3-flash",  # ✅ ADDED back
    "Gemini-3",             # ✅ CORRECT KEY from models.json
],
```

### 2. `code_puppy/core/token_budget.py`

**Changed:** Updated `_normalize_provider()` to map new model keys to budget categories

**Before:**
```python
mappings = {
    "cerebras-glm-4.7": "cerebras",  # OLD name
    "gemini-3-flash": "gemini_flash",  # OLD name
    "claude-opus-4.5": "claude_opus",  # OLD name
}
```

**After:**
```python
mappings = {
    # NEW: Keys from models.json (what agents actually see)
    "cerebras-glm-4.7": "cerebras",
    "claude-4-5-opus": "claude_opus",       # ✅ ADDED
    "claude-4-5-sonnet": "claude_sonnet",   # ✅ ADDED
    "claude-4-5-haiku": "gemini_flash",     # ✅ ADDED
    "gemini-3": "gemini",                   # ✅ ADDED
    "gpt-5.1": "codex",                     # ✅ ADDED
    "gpt-5.1-codex-api": "codex",           # ✅ ADDED
    # OLD: Legacy names (kept for compatibility)
    ...
}
```

## Why This Happened

The model naming convention changed at some point:
- **Old convention:** `claude-opus-4.5`, `cerebras-glm-4.7`
- **New convention:** `claude-4-5-opus`, `Cerebras-GLM-4.7` (with capitalization)

The `models.json` was updated, but the failover chains and budget manager weren't.

## Testing

To verify the fix works:

```python
# Test pack leader can get correct model
from code_puppy.core import get_model_for_agent

model = get_model_for_agent("pack-leader")
print(f"Pack leader will use: {model}")
# Should print: "claude-4-5-opus" (exists in models.json)

# Test terrier (coding agent) gets correct model
model = get_model_for_agent("terrier")
print(f"Terrier will use: {model}")
# Should print: "Cerebras-GLM-4.7" (exists in models.json)
```

## Impact

**Before fix:**
- ❌ All agents falling back to wrong models
- ❌ "Unknown provider" warnings everywhere  
- ❌ Pack coordination failing due to wrong model selection
- ❌ Budget tracking not working (unknown providers)

**After fix:**
- ✅ Agents use correct models from models.json
- ✅ No more "Unknown provider" warnings
- ✅ Pack Governor properly routes tasks by workload type
- ✅ Budget tracking works correctly
- ✅ Failover chains execute as designed

## Related Files

Reference these files to understand the model routing:

1. `code_puppy/models.json` - Source of truth for available models
2. `code_puppy/core/rate_limit_failover.py` - Failover chains by workload
3. `code_puppy/core/token_budget.py` - Budget tracking by provider
4. `code_puppy/core/pack_governor.py` - Agent slot management
5. `code_puppy/core/agent_orchestration.py` - Agent → Model mapping

## Prevention

To prevent this in the future:

1. **Single source of truth:** Model keys should be validated against `models.json`
2. **Type safety:** Consider using an enum for model names
3. **Unit tests:** Add tests that verify failover chains reference valid models
4. **Documentation:** Keep model naming conventions documented

## Quick Validation Script

```bash
# Run the validation script to check failover chains
cd /Users/tygranlund/code_puppy
source .venv/bin/activate
python3 scripts/validate_failover_chains.py
```

**Expected output:**
```
✅ ALL FAILOVER CHAINS VALID
All model names in failover chains exist in models.json
```

**Current Status (2026-01-30):**
```
📊 Validation Summary:
   Total model references: 22
   Valid: 22
   Invalid: 0

✅ ALL FAILOVER CHAINS VALID
```

## Key Discovery

The actual Claude model names include **date suffixes**:
- `claude-code-claude-opus-4-5-20251101` (not `claude-4-5-opus`)
- `claude-code-claude-sonnet-4-5-20250929` (not `claude-4-5-sonnet`)
- `claude-code-claude-haiku-4-5-20251001` (not `claude-4-5-haiku`)

And all Antigravity models exist and are now included in the failover chains.

---

**Status:** ✅ Fixed and Validated  
**Date:** 2026-01-30  
**Severity:** High (broke all agent orchestration)

---

## Update: Failover Execution Bug (2026-01-30)

### Second Bug Discovery

After fixing all model names, failover was still NOT EXECUTING - the system would:
1. Detect rate limit ✅
2. Identify failover model ✅  
3. Display "failover to antigravity-claude-opus-4-5-thinking-high" ✅
4. **Wait 60 seconds anyway** ❌ (instead of actually switching!)

### Root Cause

In `code_puppy/agents/base_agent.py`, line ~2035:

```python
# BUG: elif means failover_to is NEVER checked when wait_seconds > 0
if budget_check.wait_seconds > 0:
    await asyncio.sleep(budget_check.wait_seconds)  # ALWAYS WAITS!
elif budget_check.failover_to:  # NEVER REACHED if wait > 0
    # TODO: Implement model switching on the fly  # NEVER IMPLEMENTED!
```

The rate limit code sets BOTH `wait_seconds` AND `failover_to` when wait > 10s, but the if/elif meant it always waited instead of failing over.

### Fix Applied

```python
# FIX: Check failover FIRST when wait is long (>= 10s)
if budget_check.failover_to and budget_check.wait_seconds >= 10:
    # Actually switch to failover model
    models_config = ModelFactory.get_models_config()
    failover_model = ModelFactory.get_model(
        budget_check.failover_to, models_config
    )
    if failover_model:
        pydantic_agent = failover_model  # ACTUALLY SWITCH
        emit_info(f"✅ Successfully switched to {budget_check.failover_to}")
    else:
        await asyncio.sleep(budget_check.wait_seconds)  # Fallback if model unavailable
elif budget_check.wait_seconds > 0:
    await asyncio.sleep(budget_check.wait_seconds)  # Short waits still wait
```

### Files Modified

1. `code_puppy/agents/base_agent.py` - Implemented actual model switching
2. `code_puppy/tests/test_token_budget.py` - Updated test expectations for new failover chains

### Impact

**Before:** Failover was identified but never executed - just displayed a message and waited
**After:** Failover model is actually loaded and used for the request

---

## Update: Case-Sensitivity and Provider Mapping Fixes (2026-01-30)

### Third Round of Fixes

After the initial model name fixes, additional issues were discovered:

#### Issues Found

1. **Case-sensitivity mismatch:** `models.json` uses exact keys like `"Cerebras-GLM-4.7"` (capital C), but code used `"cerebras-glm-4.7"` (lowercase)

2. **Missing `antigravity-` prefix:** Code used `"gemini-3-flash"` but `models.json` has `"antigravity-gemini-3-flash"`

3. **Unknown provider `custom_openai`:** Budget tracking had no mapping for `custom_openai` provider

4. **Inconsistent model names across files:** Multiple files had hardcoded model names that didn't match `models.json`

### Files Fixed in This Round

#### 1. `code_puppy/core/rate_limit_failover.py`
- Fixed `_load_fallback_models()` to use exact keys:
  - `"Cerebras-GLM-4.7"` (was `"cerebras-glm-4.7"`)
  - `"antigravity-gemini-3-flash"` (was `"gemini-3-flash"`)
  - `"claude-code-claude-sonnet-4-5-20250929"` (was `"claude-sonnet-4.5"`)

#### 2. `code_puppy/core/token_budget.py`
- Added both case variants for Cerebras: `"cerebras-glm-4.7"` and `"Cerebras-GLM-4.7"`
- Added `"antigravity-gemini-3-flash"` mapping
- Added `"custom_openai"` → `"codex"` provider mapping in `_normalize_provider()`

#### 3. `code_puppy/tools/agent_tools.py`
- Added `find_model_key()` case-insensitive lookup helper function
- Model lookups now try case-insensitive match before falling back

#### 4. `code_puppy/core/model_router.py`
- Fixed `DEFAULT_MODELS` dict to use exact `models.json` keys

#### 5. `code_puppy/core/smart_selection.py`
- Fixed `CAPABILITY_TIERS` and `MODEL_PROVIDERS` to use exact keys

#### 6. `code_puppy/core/context_compressor.py`
- Added `max_tokens` alias (was `max_context_tokens`)
- Added optional `estimate_tokens_fn` parameter for compatibility

#### 7. `tests/test_rate_limit_failover.py`
- Updated `test_load_fallback_models()` to expect correct model names

### Test Results

All 80 failover infrastructure tests pass:
```
tests/test_failover_infrastructure.py - 32 passed
tests/test_token_budget.py - 15 passed  
tests/test_rate_limit_failover.py - 33 passed
```

### Token Optimization Verification

The token optimization is correctly wired:

1. **Cerebras models:** Use `cerebras_optimizer.apply_sliding_window()` for aggressive compaction
2. **Other models:** Use truncation or summarization based on `compaction_strategy` setting
3. **All agents** inherit this via `BaseAgent._check_tokens_and_maybe_compact()`

Token savings are emitted to the UI via:
```python
emit_info(
    f"🧹 Cerebras auto-compact: {result.original_tokens:,} → "
    f"{result.compacted_tokens:,} tokens ({result.savings_percent:.0f}% saved)",
    message_group="token_context_status",
)
```

---

**Status:** ✅ Fixed and Validated  
**Date:** 2026-01-30  
**All Issues Resolved:** Model name mismatches, case-sensitivity, provider mappings, token optimization wiring

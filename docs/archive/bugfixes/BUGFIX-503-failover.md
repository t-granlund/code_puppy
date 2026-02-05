# Critical Bugfix: 503 MODEL_CAPACITY_EXHAUSTED Not Triggering Failover

**Date:** February 4, 2026  
**Severity:** HIGH - Failover mechanism not working for capacity errors

## Issue Identified

### Problem
The agent failover system was **NOT triggering** when Antigravity API returned:
```
RuntimeError: Antigravity API Error 503: {
  "error": {
    "code": 503,
    "message": "No capacity available for model claude-opus-4-5-thinking on the server",
    "status": "UNAVAILABLE",
    "details": [{
      "reason": "MODEL_CAPACITY_EXHAUSTED",
      "domain": "cloudcode-pa.googleapis.com"
    }]
  }
}
```

### Root Cause
Failover logic only checked for:
- `429` status codes
- `RESOURCE_EXHAUSTED` messages
- `quota` keywords

But Antigravity returns **503 MODEL_CAPACITY_EXHAUSTED** which was not recognized.

### Impact
- Primary model (antigravity-claude-opus-4-5-thinking-high) fails
- Agent crashes instead of failing over to secondary models
- User sees error instead of automatic recovery
- Defeats the purpose of having 10-model failover chains

## Files Fixed

### 1. `/code_puppy/agents/base_agent.py` (2 locations)

**Line 2486:**
```python
# BEFORE
if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():

# AFTER
if ("429" in error_str or 
    "503" in error_str or
    "RESOURCE_EXHAUSTED" in error_str or 
    "MODEL_CAPACITY_EXHAUSTED" in error_str or
    "No capacity available" in error_str or
    "quota" in error_str.lower()):
```

**Line 2336:**
```python
# BEFORE
if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():

# AFTER
if ("429" in error_str or 
    "503" in error_str or
    "RESOURCE_EXHAUSTED" in error_str or
    "MODEL_CAPACITY_EXHAUSTED" in error_str or
    "No capacity available" in error_str or
    "quota" in error_str.lower()):
```

### 2. `/code_puppy/core/rate_limit_failover.py`

**Line 592:**
```python
# BEFORE
if "429" in error_str or "rate limit" in error_str or "too many requests" in error_str:

# AFTER
if ("429" in error_str or 
    "503" in error_str or
    "rate limit" in error_str or 
    "too many requests" in error_str or
    "MODEL_CAPACITY_EXHAUSTED" in error_str or
    "No capacity available" in error_str):
```

### 3. `/code_puppy/core/token_budget.py`

**Line 631:**
```python
# BEFORE
if "429" in error_str or "rate limit" in error_str or "too many requests" in error_str:

# AFTER
if ("429" in error_str or 
    "503" in error_str or
    "rate limit" in error_str or 
    "too many requests" in error_str or
    "capacity" in error_str or
    "no capacity available" in error_str):
```

## Error Codes Now Recognized

### HTTP Status Codes
- ✅ **429** - Too Many Requests (rate limit)
- ✅ **503** - Service Unavailable (capacity exhausted)

### Error Reasons
- ✅ `RESOURCE_EXHAUSTED` - General resource limits
- ✅ `MODEL_CAPACITY_EXHAUSTED` - Model-specific capacity
- ✅ `quota` - Quota limits
- ✅ `rate limit` - Rate limiting messages
- ✅ `too many requests` - Request flooding
- ✅ `No capacity available` - Capacity messages
- ✅ `capacity` - General capacity issues

## Expected Behavior After Fix

When Antigravity returns 503 MODEL_CAPACITY_EXHAUSTED:

1. ✅ Error is recognized as failover-eligible
2. ✅ System skips all Antigravity models (shared quota)
3. ✅ Fails over to next provider (e.g., Synthetic)
4. ✅ User sees warning but agent continues
5. ✅ Request completes successfully with fallback model

### Example Flow
```
Primary:    antigravity-claude-opus-4-5-thinking-high (503)
Failover 1: antigravity-claude-opus-4-5-thinking-medium (SKIPPED - same provider)
Failover 2: claude-code-claude-opus-4-5-20251101 (SKIPPED - same provider)
Failover 3: synthetic-Kimi-K2.5-Thinking (USED ✅)
```

## Testing Recommendations

### 1. Manual Test
```bash
code-puppy
/invoke epistemic-architect
> Create a simple Python script
```

Watch for:
- ⚠️ Warning about model capacity
- 🔄 "Switched to [fallback-model]" message
- ✅ Request completes successfully

### 2. Check Logs
```bash
tail -f ~/.code_puppy/logs/errors.log
```

Should see:
- Initial 503 error
- Failover warning
- Successful retry with new model

### 3. Logfire Telemetry
Visit: https://logfire-api.pydantic.dev

Look for:
- `model_failover` events
- `capacity_exhausted` tags
- Successful completion after failover

## Monitoring

### Key Metrics
- **Failover Success Rate**: Should be >95%
- **503 Error Recovery**: Should trigger failover 100% of time
- **Average Failover Time**: Should be <2 seconds

### Alert If
- Multiple consecutive failovers (>3 in chain)
- All models in chain exhausted
- Failover not triggered on 503 errors

## Related Issues

This fix also improves handling for:
- OpenAI capacity errors
- Cerebras model unavailability
- Any API returning 503 status codes
- Provider-wide capacity issues

## Commit Message
```
fix(failover): Add 503 MODEL_CAPACITY_EXHAUSTED to failover triggers

- Antigravity API returns 503 with MODEL_CAPACITY_EXHAUSTED
- Previous logic only checked 429 and RESOURCE_EXHAUSTED
- Now recognizes 503, capacity messages, and model exhaustion
- Fixes 4 locations: base_agent.py (2x), rate_limit_failover.py, token_budget.py
- Ensures failover chains work for all capacity/rate limit scenarios
```

## Priority: CRITICAL ⚠️

This fix is essential for production reliability. Without it:
- ❌ Failover chains are ineffective
- ❌ Users see errors instead of automatic recovery
- ❌ System doesn't utilize backup models
- ❌ Poor user experience during high-load periods

Deploy immediately and monitor failover metrics closely.

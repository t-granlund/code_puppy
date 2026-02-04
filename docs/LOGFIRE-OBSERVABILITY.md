# Logfire Observability - Code Puppy Telemetry

## Overview

Code Puppy uses [Pydantic Logfire](https://logfire.pydantic.dev/) to provide comprehensive observability into the BART (Belief • Augmented • Reasoning • Tasking) system. This document describes all telemetry events emitted to help you verify the system is "sticking to the plan."

## Logfire API Access

```bash
# Query endpoint
BASE_URL="https://logfire-api.pydantic.dev/v1/query"

# Example query (last 12 hours)
curl -H "Authorization: Bearer $LOGFIRE_READ_TOKEN" \
  "$BASE_URL?sql=SELECT * FROM records WHERE start_timestamp > NOW() - INTERVAL '12 hours'"
```

---

## 1. Workload Routing Telemetry

**Source:** `code_puppy/agents/base_agent.py` → `get_model_name()`

**Purpose:** Verify agents are using workload-appropriate models (e.g., CODING → GLM-4.7, ORCHESTRATOR → Claude Opus)

### Event: Workload Model Assignment

```python
logfire.info(
    "Workload routing: {agent} → {workload} → {model}",
    agent=agent_name,
    workload=workload_type,
    orchestrated_model=model_from_orchestrator,
    default_model=fallback_model,
)
```

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `agent` | string | Agent name (e.g., "husky", "pack-leader") |
| `workload` | string | Workload type (CODING, ORCHESTRATOR, REASONING, LIBRARIAN) |
| `orchestrated_model` | string | Model returned by AgentOrchestrator |
| `default_model` | string | Fallback model if orchestrator unavailable |

**Expected Behavior:**
- `husky` agent → CODING workload → `Cerebras-GLM-4.7` or `hf:zai-org/GLM-4.7`
- `pack-leader` agent → ORCHESTRATOR workload → `claude-sonnet-4-5` or `gpt-5.2-codex`
- `context-curator` agent → LIBRARIAN workload → Fast models

**Query to Verify:**
```sql
SELECT 
    attributes->>'agent' as agent,
    attributes->>'workload' as workload,
    attributes->>'orchestrated_model' as model,
    COUNT(*) as calls
FROM records 
WHERE message LIKE 'Workload routing%'
  AND start_timestamp > NOW() - INTERVAL '12 hours'
GROUP BY 1, 2, 3
ORDER BY calls DESC
```

---

## 2. Failover Event Telemetry

**Source:** `code_puppy/failover_model.py`

**Purpose:** Track when models fail over due to rate limits (429s), and ensure the system uses fallback models correctly.

### Event: Failover Triggered

```python
logfire.warn(
    "Failover triggered: {from_model} → {to_model} ({error_type})",
    from_model=failed_model_name,
    to_model=next_model_name,
    error_type=error_classification,
    workload=workload_type,
)
```

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `from_model` | string | Model that failed |
| `to_model` | string | Next model in failover chain |
| `error_type` | string | "rate_limit", "format_error", "timeout", etc. |
| `workload` | string | Workload type for chain selection |

### Event: Failover Success

```python
logfire.info(
    "Failover success: now using {model}",
    model=successful_model_name,
    workload=workload_type,
    attempts=attempt_count,
)
```

### Event: Rate Limit Recorded

```python
logfire.warn(
    "Rate limit: {model} ({workload}) - cooldown {cooldown}s",
    model=model_name,
    workload=workload_type,
    cooldown=cooldown_seconds,
    consecutive_429s=consecutive_count,
)
```

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `model` | string | Rate-limited model |
| `workload` | string | Workload type |
| `cooldown` | int | Seconds until retry allowed |
| `consecutive_429s` | int | Number of consecutive rate limits |

**Expected Behavior:**
- When `Cerebras-GLM-4.7` is rate-limited → failover to `hf:moonshotai/Kimi-K2.5`
- When `claude-sonnet-4-5` is rate-limited → failover to `gpt-5.2-codex`
- Consecutive 429s should trigger longer cooldowns

**Query to Monitor:**
```sql
SELECT 
    attributes->>'from_model' as from_model,
    attributes->>'to_model' as to_model,
    attributes->>'error_type' as error_type,
    COUNT(*) as failovers
FROM records 
WHERE message LIKE 'Failover triggered%'
  AND start_timestamp > NOW() - INTERVAL '12 hours'
GROUP BY 1, 2, 3
ORDER BY failovers DESC
```

---

## 3. Capacity Warning Telemetry

**Source:** `code_puppy/core/model_capacity.py` → `_emit_capacity_warning()`

**Purpose:** Alert when models approach their token/request limits (80%+ usage).

### Event: Capacity Warning

```python
logfire.warn(
    "Capacity warning: {model} at {pct}% ({limit_type})",
    model=model_name,
    pct=percentage_used,
    limit_type=limit_category,
    used=tokens_or_requests_used,
    limit=total_limit,
    provider=provider_name,
)
```

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `model` | string | Model approaching limit |
| `pct` | float | Percentage of limit used (0-100) |
| `limit_type` | string | "window_tokens", "day_requests", "minute_tokens" |
| `used` | int | Current usage count |
| `limit` | int | Maximum allowed |
| `provider` | string | Provider (synthetic, cerebras, anthropic) |

**Expected Behavior:**
- Warning at 80% capacity → proactive failover consideration
- Warning at 95% capacity → imminent rate limit expected
- Synthetic.new: 5-hour rolling window limits
- Cerebras: Daily request limits

**Query to Monitor:**
```sql
SELECT 
    attributes->>'model' as model,
    attributes->>'pct' as percentage,
    attributes->>'limit_type' as limit_type,
    start_timestamp
FROM records 
WHERE message LIKE 'Capacity warning%'
  AND start_timestamp > NOW() - INTERVAL '24 hours'
ORDER BY start_timestamp DESC
LIMIT 50
```

---

## 4. EAR (Epistemic Architect Runtime) Stage Tracking

**Source:** `code_puppy/epistemic/ear-runtime/src/ear/core/ralph_loop.py`

**Purpose:** Track the Ralph Loop phase transitions (OBSERVE → ORIENT → DECIDE → ACT → COMPLETE).

### Event: Phase Transition

```python
logfire.info(
    "EAR phase: {from_phase} → {to_phase}",
    loop_id=loop_id[:8],
    agent_id=agent_id,
    from_phase=previous_phase,
    to_phase=current_phase,
    decision_type=decision_type,  # Optional
    confidence=confidence_score,   # Optional
)
```

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `loop_id` | string | First 8 chars of loop UUID |
| `agent_id` | string | Agent executing the loop |
| `from_phase` | string | Previous phase |
| `to_phase` | string | New phase |
| `decision_type` | string | "action", "test", "interaction", "refusal", "wait" |
| `confidence` | float | Decision confidence (0.0-1.0) |

**Phase Values:**
- `observe` → `orient` (captured state)
- `orient` → `decide` (applied lenses)
- `decide` → `act` (made decision)
- `act` → `complete` (executed action)
- `*` → `refused` (valid refusal)
- `*` → `error` (failure)

**Expected Behavior:**
- Each Ralph Loop should progress: observe → orient → decide → act → complete
- Refusals are valid outcomes (agent declines inappropriate request)
- High confidence (>0.7) indicates strong decision
- Low confidence (<0.4) may trigger additional lens evaluation

**Query to Trace Loops:**
```sql
SELECT 
    attributes->>'loop_id' as loop,
    attributes->>'agent_id' as agent,
    attributes->>'from_phase' as from_phase,
    attributes->>'to_phase' as to_phase,
    attributes->>'decision_type' as decision,
    attributes->>'confidence' as confidence,
    start_timestamp
FROM records 
WHERE message LIKE 'EAR phase%'
  AND start_timestamp > NOW() - INTERVAL '1 hour'
ORDER BY start_timestamp
```

---

## Dashboard Queries

### Health Check: Is Workload Routing Working?

```sql
-- Should see CODING workload using GLM-4.7, not Kimi
SELECT 
    attributes->>'workload' as workload,
    attributes->>'orchestrated_model' as model,
    COUNT(*) as calls
FROM records 
WHERE message LIKE 'Workload routing%'
  AND start_timestamp > NOW() - INTERVAL '12 hours'
GROUP BY 1, 2
ORDER BY workload, calls DESC
```

**✅ Good:** CODING → GLM-4.7 (majority)  
**❌ Bad:** CODING → Kimi-K2.5 (majority)

### Health Check: Failover Chain Active?

```sql
-- Should see failover events when primary model is exhausted
SELECT 
    DATE_TRUNC('hour', start_timestamp) as hour,
    COUNT(*) FILTER (WHERE message LIKE 'Failover triggered%') as failovers,
    COUNT(*) FILTER (WHERE message LIKE 'Failover success%') as recoveries,
    COUNT(*) FILTER (WHERE message LIKE 'Rate limit%') as rate_limits
FROM records 
WHERE start_timestamp > NOW() - INTERVAL '24 hours'
GROUP BY 1
ORDER BY 1
```

**✅ Good:** Failovers happening with recoveries  
**❌ Bad:** Many rate limits with no failovers

### Health Check: Capacity Utilization

```sql
-- Track capacity across providers
SELECT 
    attributes->>'provider' as provider,
    attributes->>'model' as model,
    MAX(CAST(attributes->>'pct' AS FLOAT)) as max_pct,
    AVG(CAST(attributes->>'pct' AS FLOAT)) as avg_pct
FROM records 
WHERE message LIKE 'Capacity warning%'
  AND start_timestamp > NOW() - INTERVAL '24 hours'
GROUP BY 1, 2
ORDER BY max_pct DESC
```

### Health Check: EAR Loop Completion Rate

```sql
-- Track loop completion vs errors/refusals
SELECT 
    attributes->>'to_phase' as outcome,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as pct
FROM records 
WHERE message LIKE 'EAR phase%'
  AND attributes->>'to_phase' IN ('complete', 'refused', 'error')
  AND start_timestamp > NOW() - INTERVAL '24 hours'
GROUP BY 1
ORDER BY count DESC
```

**✅ Good:** >90% complete, <5% error  
**❌ Bad:** >10% error rate

---

## Telemetry Summary

| Event Type | Log Level | Source File | Purpose |
|------------|-----------|-------------|---------|
| Workload routing | INFO | base_agent.py | Verify model selection |
| Failover triggered | WARN | failover_model.py | Track model switches |
| Failover success | INFO | failover_model.py | Confirm recovery |
| Rate limit | WARN | failover_model.py | Track 429 events |
| Capacity warning | WARN | model_capacity.py | Proactive alerting |
| EAR phase | INFO | ralph_loop.py | Track reasoning stages |

---

## Integration with BART Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         LOGFIRE OBSERVABILITY                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────┐    ┌─────────────────────┐                     │
│  │  Workload Routing   │    │   Capacity Tracking │                     │
│  │  (base_agent.py)    │    │  (model_capacity.py)│                     │
│  │                     │    │                     │                     │
│  │  📊 agent → model   │    │  ⚠️ 80%+ warnings   │                     │
│  └─────────┬───────────┘    └──────────┬──────────┘                     │
│            │                           │                                │
│            ▼                           ▼                                │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    FAILOVER ENGINE                               │    │
│  │                   (failover_model.py)                            │    │
│  │                                                                  │    │
│  │  🔄 triggered     ✅ success     🚫 rate_limit                  │    │
│  │  from → to        model          model, cooldown                │    │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│            ┌──────────────────────────────────────┐                     │
│            │       EAR REASONING LOOPS            │                     │
│            │        (ralph_loop.py)               │                     │
│            │                                      │                     │
│            │  OBSERVE → ORIENT → DECIDE → ACT    │                     │
│            │      ↑                      │       │                     │
│            │      └──────────────────────┘       │                     │
│            │                                      │                     │
│            │  📈 phase transitions               │                     │
│            │  📊 decision confidence             │                     │
│            └──────────────────────────────────────┘                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Verifying "Sticking to the Plan"

Use these queries to ensure the system follows the architecture:

### 1. CODING Work Uses GLM-4.7 (Not Kimi)

```sql
SELECT 
    attributes->>'orchestrated_model' as model,
    COUNT(*) as calls
FROM records 
WHERE message LIKE 'Workload routing%'
  AND attributes->>'workload' = 'CODING'
  AND start_timestamp > NOW() - INTERVAL '12 hours'
GROUP BY 1
```

**Expected:** GLM-4.7 should have majority of CODING calls.

### 2. Failover Chain Respects Workload

```sql
SELECT 
    attributes->>'workload' as workload,
    attributes->>'from_model' as from_model,
    attributes->>'to_model' as to_model
FROM records 
WHERE message LIKE 'Failover triggered%'
  AND start_timestamp > NOW() - INTERVAL '12 hours'
```

**Expected:** CODING failovers go to Kimi/DeepSeek, ORCHESTRATOR to GPT-5.

### 3. No Excessive 422 Errors

```sql
SELECT 
    attributes->>'error_type' as error,
    COUNT(*) as count
FROM records 
WHERE message LIKE 'Failover triggered%'
  AND start_timestamp > NOW() - INTERVAL '12 hours'
GROUP BY 1
```

**Expected:** Minimal "format_error" after sanitization fix.

### 4. Capacity Warnings Trigger Before Rate Limits

```sql
WITH warnings AS (
    SELECT start_timestamp as warn_time, attributes->>'model' as model
    FROM records WHERE message LIKE 'Capacity warning%'
),
limits AS (
    SELECT start_timestamp as limit_time, attributes->>'model' as model
    FROM records WHERE message LIKE 'Rate limit%'
)
SELECT 
    l.model,
    MIN(w.warn_time) as first_warning,
    l.limit_time as rate_limit,
    EXTRACT(EPOCH FROM (l.limit_time - MIN(w.warn_time))) as seconds_warning
FROM limits l
LEFT JOIN warnings w ON l.model = w.model AND w.warn_time < l.limit_time
GROUP BY l.model, l.limit_time
```

**Expected:** Warnings should precede rate limits.

---

## Related Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Full system architecture
- [LOGFIRE-INTEGRATION.md](LOGFIRE-INTEGRATION.md) - Setup and configuration
- [ROBUSTNESS-INFRASTRUCTURE.md](ROBUSTNESS-INFRASTRUCTURE.md) - Failover design
- [TOKEN-OPTIMIZATION-OVERVIEW.md](TOKEN-OPTIMIZATION-OVERVIEW.md) - Capacity management

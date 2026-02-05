# Robustness & Performance Infrastructure

**Status**: ✅ Production Ready (Certified February 5, 2026)

This document describes the comprehensive robustness and performance modules added to Code Puppy's core infrastructure.

## Overview

The infrastructure consists of 7 interconnected modules that work together to provide:

- **Fault Tolerance**: Circuit breakers, health checks, graceful degradation
- **Cost Control**: Budget limits, alerts, anomaly detection
- **Performance**: Caching, compression, connection pooling
- **Analytics**: Metrics tracking, dashboards, trend analysis
- **Intelligence**: Smart model selection, priority queues, load balancing
- **Wiggum Loop Resilience**: Generator athrow() prevention, model cooldown tracking (5-min), 29+ failover models

## Recent Enhancements (February 2026)

### Generator Athrow() Prevention
Fixed critical issue where generators continued failover after yielding to caller. Added `yielded` flag tracking to ensure proper exception propagation.

### Model Cooldown Tracking
5-minute cooldown period for failed models prevents immediate retry, optimizing token budget and time:
```python
manager.record_model_failure("claude-code-opus")
assert manager.is_model_in_cooldown("claude-code-opus")  # True for 5 minutes
```

### Enhanced Error Context
Validation errors now include detailed context with error types (UnexpectedModelBehavior, ToolRetryError) for better debugging.

### Working Directory Validation
Commands validate directory existence before execution, preventing ModuleNotFoundError cascades.

See [WIGGUM-LOOP-CERTIFICATION.md](../WIGGUM-LOOP-CERTIFICATION.md) for complete production readiness certification.

## Module Reference

### 1. Circuit Breaker (`circuit_breaker.py`)

Implements the circuit breaker pattern to prevent cascading failures.

```python
from code_puppy.core import CircuitBreaker, CircuitBreakerManager, with_circuit_breaker

# Basic usage
cb = CircuitBreaker("provider-name")
if await cb.can_execute():
    try:
        result = await make_api_call()
        await cb.record_success()
    except Exception as e:
        await cb.record_failure(str(e))

# Using decorator-style helper
result = await with_circuit_breaker("provider", async_function)

# Global manager
manager = CircuitBreakerManager.get_instance()
available = manager.get_available_providers()
```

**Configuration Options:**
- `failure_threshold`: Consecutive failures to open circuit (default: 5)
- `recovery_timeout`: Seconds before testing recovery (default: 30)
- `success_threshold`: Successes needed to close from half-open (default: 3)

**States:**
- `CLOSED`: Normal operation
- `OPEN`: Failing, requests rejected
- `HALF_OPEN`: Testing if service recovered

### 2. Response Cache (`response_cache.py`)

Intelligent caching with TTL and prompt compression.

```python
from code_puppy.core import ResponseCache, PromptCompressor, cached_completion

# Direct cache usage
cache = ResponseCache(max_entries=1000, default_ttl=3600)
cached = await cache.get(prompt, model)
if not cached:
    response = await generate_response()
    await cache.put(prompt, response, model, input_tokens, output_tokens)

# Prompt compression
compressor = PromptCompressor(aggressive=True)
result = compressor.compress(text, is_code=True)
print(f"Saved {result.original_tokens_est - result.compressed_tokens_est} tokens")

# High-level helper
response, was_cached = await cached_completion(
    prompt="user query",
    model="model-name",
    completion_func=your_async_function,
)
```

**Features:**
- LRU eviction when max entries reached
- TTL-based expiration
- Prompt normalization for better hit rates
- Token savings tracking

### 3. Cost Budget (`cost_budget.py`)

Financial controls with multi-level alerting.

```python
from code_puppy.core import CostBudgetEnforcer, get_cost_enforcer, check_and_record_cost
from decimal import Decimal

# Configure limits
enforcer = get_cost_enforcer()
enforcer.configure_provider("cerebras", Decimal("10.00"), Decimal("100.00"))

# Check and record costs
can_proceed, alerts = await check_and_record_cost(
    provider="gemini",
    cost_usd=Decimal("0.05")
)

# Get throttle factor (1.0 = no throttle, 0.0 = blocked)
throttle = enforcer.get_throttle_factor("claude_opus")

# Add alert callback
def my_alert_handler(alert):
    if alert.severity == AlertSeverity.CRITICAL:
        send_notification(alert.message)

enforcer.add_alert_callback(my_alert_handler)
```

**Alert Thresholds:**
- INFO: 50% of budget used
- WARNING: 80% of budget used
- CRITICAL: 95% of budget used
- LIMIT_REACHED: 100% (blocked)

### 4. Model Metrics (`model_metrics.py`)

Performance analytics with latency percentiles.

```python
from code_puppy.core import ModelMetricsTracker, track_request, get_metrics_tracker

# Using context manager
async with track_request("cerebras-glm", "cerebras", "code_generation") as ctx:
    response = await model.generate(prompt)
    ctx.input_tokens = response.input_tokens
    ctx.output_tokens = response.output_tokens
    ctx.cost_usd = response.cost

# Get metrics
tracker = get_metrics_tracker()
metrics = tracker.get_model_metrics("cerebras-glm")
print(f"Success rate: {metrics.success_rate}%")
print(f"P95 latency: {metrics.p95_latency_ms}ms")

# Rankings
efficiency = tracker.get_efficiency_ranking()  # By tokens per dollar
speed = tracker.get_speed_ranking()  # By tokens per second
reliability = tracker.get_reliability_ranking()  # By success rate
```

### 5. Smart Selection (`smart_selection.py`)

Intelligent model selection and request prioritization.

```python
from code_puppy.core import (
    SmartModelSelector, SelectionStrategy,
    RequestPriorityQueue, RequestPriority,
    select_best_model
)

# Select best model
selector = SmartModelSelector()
result = await selector.select_model(
    available_models=["cerebras-glm-4.7", "gemini-3-flash", "claude-sonnet-4.5"],
    strategy=SelectionStrategy.COST_OPTIMIZED,
    min_capability_tier=3,  # At least Builder Mid capability
)
print(f"Selected: {result.model} (score: {result.total_score})")

# Or use the simple helper
best = await select_best_model(
    models=["cerebras-glm-4.7", "claude-opus-4.5"],
    strategy=SelectionStrategy.BALANCED,
)

# Priority queue
queue = RequestPriorityQueue(max_concurrent=10)
request_id = await queue.enqueue(
    payload={"prompt": "..."},
    priority=RequestPriority.HIGH,
    timeout=60.0,
)
```

**Selection Strategies:**
- `COST_OPTIMIZED`: Minimize cost
- `SPEED_OPTIMIZED`: Minimize latency
- `RELIABILITY_OPTIMIZED`: Maximize success rate
- `BALANCED`: Balance all factors
- `CAPABILITY_FIRST`: Choose most capable

### 6. Performance Dashboard (`performance_dashboard.py`)

Unified health monitoring and analytics.

```python
from code_puppy.core import get_dashboard, get_health_status, print_dashboard_summary

# Get system health
health = await get_health_status()
print(f"Status: {health.overall_status} ({health.overall_score}%)")
for indicator in health.indicators:
    print(f"  {indicator.name}: {indicator.status} - {indicator.message}")

# Get performance summary
dashboard = get_dashboard()
perf = dashboard.get_performance_summary()
print(f"Requests/min: {perf['requests']['per_minute']}")
print(f"Cost today: ${perf['cost']['today_usd']}")

# Cost analytics with recommendations
costs = dashboard.get_cost_analytics()
for rec in costs['recommendations']:
    print(f"💡 {rec}")

# Print formatted summary
print_dashboard_summary()
```

### 7. Connection Pool (`connection_pool.py`)

HTTP connection management and streaming.

```python
from code_puppy.core import (
    get_pool_manager, get_provider_pool,
    streaming_completion, cleanup_connections
)

# Get provider pool
pool = await get_provider_pool("openai")
response = await pool.post("/v1/chat/completions", json=payload)

# Streaming
async with streaming_completion("openai", "/v1/chat/completions", payload) as stream:
    async for chunk in stream:
        print(chunk.delta, end="", flush=True)

# Cleanup on shutdown
await cleanup_connections()
```

**Pool Features:**
- Connection reuse
- HTTP/2 support
- Configurable timeouts
- Statistics tracking

## Integration Example

Here's how all modules work together:

```python
from code_puppy.core import (
    # Circuit breaker
    check_circuit, with_circuit_breaker,
    # Cache
    cached_completion, get_prompt_compressor,
    # Cost
    check_and_record_cost,
    # Metrics
    track_request,
    # Selection
    select_best_model, SelectionStrategy,
    # Dashboard
    get_health_status,
)

async def smart_completion(prompt: str, task_type: str) -> str:
    # 1. Check system health
    health = await get_health_status()
    if health.overall_status == "unhealthy":
        logger.warning("System degraded, using fallback")
    
    # 2. Compress prompt
    compressor = get_prompt_compressor()
    compressed = compressor.compress(prompt)
    
    # 3. Select best model
    model = await select_best_model(
        models=["cerebras-glm-4.7", "gemini-3-flash", "claude-sonnet-4.5"],
        strategy=SelectionStrategy.BALANCED,
    )
    
    # 4. Check circuit breaker
    if not await check_circuit(model):
        model = await select_best_model(
            models=["gemini-3-flash"],  # Fallback
            strategy=SelectionStrategy.SPEED_OPTIMIZED,
        )
    
    # 5. Try cache first
    response, was_cached = await cached_completion(
        prompt=compressed.compressed_text,
        model=model,
        completion_func=lambda: generate(model, compressed.compressed_text),
    )
    
    # 6. Track metrics and cost (if not cached)
    if not was_cached:
        async with track_request(model, get_provider(model), task_type) as ctx:
            ctx.input_tokens = count_tokens(compressed.compressed_text)
            ctx.output_tokens = count_tokens(response)
            
            # Record cost
            cost = estimate_cost(model, ctx.input_tokens, ctx.output_tokens)
            ctx.cost_usd = cost
            can_proceed, _ = await check_and_record_cost(get_provider(model), cost)
    
    return response
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Performance Dashboard                        │
│         (SystemHealth, Indicators, Trends, Analytics)           │
└─────────────────────────────────────────────────────────────────┘
                                   ▲
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ▼                          ▼                          ▼
┌───────────────┐      ┌───────────────────┐      ┌───────────────┐
│Circuit Breaker│      │   Model Metrics   │      │  Cost Budget  │
│   Manager     │      │     Tracker       │      │   Enforcer    │
└───────────────┘      └───────────────────┘      └───────────────┘
        │                          │                          │
        └──────────────────────────┼──────────────────────────┘
                                   │
                                   ▼
                    ┌───────────────────────────┐
                    │   Smart Model Selector    │
                    │    (Multi-factor Score)   │
                    └───────────────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │ Response Cache  │  │ Prompt Compress │  │ Priority Queue  │
    │   (TTL, LRU)    │  │  (Token Save)   │  │   (Ordering)    │
    └─────────────────┘  └─────────────────┘  └─────────────────┘
                                   │
                                   ▼
                    ┌───────────────────────────┐
                    │   Connection Pool Manager │
                    │   (HTTP/2, Streaming)     │
                    └───────────────────────────┘
                                   │
                                   ▼
                         [ Provider APIs ]
```

## Configuration

All modules support runtime configuration. Default values are sensible for most use cases.

### Environment Variables (Optional)

- `CODE_PUPPY_CACHE_TTL`: Default cache TTL in seconds (default: 3600)
- `CODE_PUPPY_DAILY_BUDGET`: Daily cost limit in USD (default: 50.00)
- `CODE_PUPPY_MONTHLY_BUDGET`: Monthly cost limit in USD (default: 500.00)

## Observability with Logfire

All robustness features are instrumented with **Logfire telemetry** for real-time monitoring:

### Circuit Breaker Events
- `failover.triggered` (WARN) - Circuit breaker opens, switching models
- `failover.success` (INFO) - Circuit recovered, back to primary model
- `rate_limit` (WARN) - Rate limit detected with `consecutive_429s` counter

### Capacity Tracking Events  
- `capacity_warning` (WARN) - Model approaching limits (≥80% usage)
- Triggers proactive failover before hitting hard limits

### Workload Routing Events
- `workload_routing` (INFO) - Records agent→workload→model assignments
- Health check: CODING workload should use GLM-4.7, not Kimi-K2.5

### EAR Loop Events
- `ear_phase` (INFO) - Tracks OBSERVE→ORIENT→DECIDE→ACT stages
- Health check: >90% completion rate, <10% error rate

See [LOGFIRE-OBSERVABILITY.md](LOGFIRE-OBSERVABILITY.md) for SQL queries and health checks.

## Best Practices

1. **Use circuit breakers** for all external API calls
2. **Enable caching** for repetitive prompts
3. **Monitor the dashboard** regularly for anomalies
4. **Set budget alerts** before hitting limits
5. **Review metrics** to optimize model selection
6. **Compress prompts** for long inputs
7. **Use priority queues** for batch workloads
8. **Monitor Logfire** for capacity warnings and failover patterns

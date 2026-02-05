# AUDIT-1.1: Comprehensive IO, Rate-Limit, and Safety Safeguards

This document describes the safeguards implemented as part of AUDIT-1.1 to ensure token-efficient, resilient, and safe operations across all code-puppy agents.

## Overview

AUDIT-1.1 implements six major safeguard categories:

| Part | Module | Purpose |
|------|--------|---------|
| D | `io_budget_enforcer.py` | Enforced IO budgeting with provider-aware limits |
| E | `shell_governor.py` | Shell output truncation, secret redaction, timeouts |
| F | `http_utils.py` (existing) | Rate limit resilience (429/503 handling) |
| G | `token_telemetry.py` | Usage ledger, burn rate alerts, daily budgets |
| H | `safe_patch.py` | Unsafe pattern detection, syntax validation, backups |
| I | `router_hooks.py` | Model pool configuration, task routing hints |

---

## Part D: IO Budget Enforcer

**Module:** `code_puppy/tools/io_budget_enforcer.py`

### Provider Budgets

```python
PROVIDER_BUDGETS = {
    "cerebras": ProviderBudget(
        max_input_tokens=50_000,
        max_output_tokens=8_000,
        requests_per_minute=50,
        daily_token_limit=24_000_000,
    ),
    "anthropic": ProviderBudget(max_input_tokens=180_000, max_output_tokens=8_000),
    "openai": ProviderBudget(max_input_tokens=120_000, max_output_tokens=8_000),
    "gemini": ProviderBudget(max_input_tokens=1_000_000, max_output_tokens=8_000),
}
```

### Key Features

- **Token Estimation:** Estimates tokens using tiktoken (cl100k_base) or fallback `len(text) // 4`
- **Budget Violation Levels:**
  - `NONE` - Within budget
  - `SOFT` - Over 70%, trigger compaction
  - `HARD` - Over 95%, block request
- **Narrowing Modes:** `SUMMARIZE`, `TRUNCATE_HEAD`, `TRUNCATE_TAIL`, `SEMANTIC_FILTER`
- **Iteration Tracking:** Tracks per-iteration and cumulative usage
- **File Read Policies:** Context-aware file read limits (400 lines normal, 100 lines after 70%)

### Usage

```python
from code_puppy.tools.io_budget_enforcer import check_budget, get_narrowing_instructions

result = check_budget(
    current_input_tokens=45000,
    current_output_tokens=3000,
    provider="cerebras"
)

if result.violation == BudgetViolation.SOFT:
    instructions = get_narrowing_instructions(result, context)
    # Apply compaction strategy
```

---

## Part E: Shell Governor

**Module:** `code_puppy/tools/shell_governor.py`

### Default Configuration

```python
DEFAULT_OUTPUT_LINES = 160      # Max lines before truncation
DEFAULT_TIMEOUT = 120           # Seconds before timeout kill
DEFAULT_ENV_BLOCKLIST = ["AWS_SECRET", "API_KEY", "TOKEN", ...]
```

### Secret Redaction Patterns

The governor automatically redacts:
- AWS keys (`AKIA...`, secret keys)
- Bearer tokens (`eyJ...` JWT patterns)
- API keys (32+ hex characters)
- GitHub tokens (`ghp_`, `gho_`, etc.)
- Private keys (`-----BEGIN...PRIVATE KEY-----`)
- Database connection strings with passwords

### Key Features

- **Output Truncation:** Head/tail/smart truncation with line counts
- **Secret Redaction:** Pattern-based credential masking
- **Timeout Detection:** Auto-kill commands exceeding time limit
- **Command History:** JSONL logging to `.codepuppy/command_history.jsonl`

### Convenience Wrappers

```python
from code_puppy.tools.shell_governor import run_quick, run_build, run_with_tail

# Quick command (30s timeout, 50 lines)
result = run_quick("git status")

# Build command (300s timeout, 200 lines)
result = run_build("npm run build")

# Tail mode (last N lines only)
result = run_with_tail("cat large_log.txt", lines=100)
```

---

## Part F: Rate Limit Resilience

**Module:** `code_puppy/http_utils.py` (existing `RetryingAsyncClient`)

### Cerebras-Specific Handling

```python
# In http_utils.py
429_INITIAL_BACKOFF = 3.0  # Cerebras uses 3-second cooldown
MAX_RETRIES = 5
RETRY_CODES = [429, 503]
```

The existing `RetryingAsyncClient` already handles:
- **429 Too Many Requests:** Exponential backoff starting at 3s
- **503 Service Unavailable:** Retry with jitter
- **Connection errors:** Automatic reconnection

No additional implementation was required—the existing infrastructure is sufficient.

---

## Part G: Token Telemetry

**Module:** `code_puppy/tools/token_telemetry.py`

### Daily Limits

```python
CEREBRAS_DAILY_LIMIT = 24_000_000  # 24M tokens/day
DEFAULT_DAILY_LIMIT = 100_000_000  # 100M for other providers
```

### Alert Levels

| Level | Threshold | Action |
|-------|-----------|--------|
| `INFO` | 0-50% | Normal operation |
| `WARNING` | 70% | Reduce context, prefer cached |
| `CRITICAL` | 90% | Minimal context only |
| `FALLBACK` | 95% | Review-only mode, no generation |

### TokenLedger Class

```python
from code_puppy.tools.token_telemetry import TokenLedger

ledger = TokenLedger(ledger_path=".codepuppy/usage.jsonl")

# Record usage
ledger.record_usage(
    provider="cerebras",
    model="llama-4-scout-17b-16e-instruct",
    input_tokens=5000,
    output_tokens=1200,
    latency_ms=340.5,
    operation="code_generation"
)

# Check burn rate
burn_info = ledger.check_burn_rate("cerebras")
if burn_info.alert_level >= AlertLevel.WARNING:
    # Reduce token consumption
```

### Persistence Format

Usage is persisted in JSONL format:
```json
{"timestamp": "2025-01-15T10:30:00", "provider": "cerebras", "model": "...", "input_tokens": 5000, "output_tokens": 1200, ...}
```

---

## Part H: Safe Patch

**Module:** `code_puppy/tools/safe_patch.py`

### Unsafe Pattern Detection

The module detects and blocks dangerous patterns:

| Pattern Type | Example | Risk |
|--------------|---------|------|
| `HEREDOC` | `cat << EOF` | Unbounded content injection |
| `SED_INPLACE` | `sed -i 's/.../'` | Silent file corruption |
| `DD_COMMAND` | `dd if=... of=...` | Disk destruction |
| `CHMOD_RECURSIVE` | `chmod -R 777` | Security degradation |
| `RM_RECURSIVE` | `rm -rf /` | Data loss |
| `CURL_PIPE_SHELL` | `curl ... \| bash` | Remote code execution |

### Syntax Validation

Built-in validators for:
- **Python:** AST parsing
- **JSON:** `json.loads()`
- **YAML:** PyYAML (if available)
- **JavaScript/TypeScript:** Basic syntax checks

### Backup System

```python
from code_puppy.tools.safe_patch import safe_write_file, restore_from_backup

# Writes with automatic backup
success = safe_write_file(
    filepath="src/config.py",
    content=new_content,
    backup_dir=".codepuppy/backups"
)

# Restore if needed
restore_from_backup("src/config.py", backup_path)
```

### Syntax Explosion Detection

Detects accidental massive file generation:
```python
from code_puppy.tools.safe_patch import detect_syntax_explosion

is_explosion, reason = detect_syntax_explosion(
    original_size=1000,
    new_size=500000  # 500x increase
)
# Returns: (True, "File size increased by 500x")
```

---

## Part I: Router Hooks

**Module:** `code_puppy/tools/router_hooks.py`

### Task Classification

```python
class TaskClass(Enum):
    CODE_GENERATION = "code_generation"
    COMPLEX_REASONING = "complex_reasoning"
    SIMPLE_QA = "simple_qa"
    CODE_REVIEW = "code_review"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DEBUGGING = "debugging"
```

### Model Capabilities

```python
class ModelCapability(Enum):
    FAST_INFERENCE = "fast_inference"
    LONG_CONTEXT = "long_context"
    CODE_SPECIALIZED = "code_specialized"
    STRONG_REASONING = "strong_reasoning"
    COST_EFFECTIVE = "cost_effective"
    TOOL_USE = "tool_use"
```

### Default Model Pool

```python
DEFAULT_MODEL_POOL = ModelPool(
    models={
        "cerebras": ModelConfig(
            model_id="llama-4-scout-17b-16e-instruct",
            provider="cerebras",
            priority=80,
            capabilities=[FAST_INFERENCE, CODE_SPECIALIZED],
            max_context=50000,
            cost_per_1k_tokens=0.0,
        ),
        "claude": ModelConfig(
            model_id="claude-sonnet-4-20250514",
            provider="anthropic",
            priority=70,
            capabilities=[STRONG_REASONING, LONG_CONTEXT, TOOL_USE],
            max_context=180000,
            cost_per_1k_tokens=0.003,
        ),
        "gpt-4o": ModelConfig(
            model_id="gpt-4o",
            provider="openai",
            priority=60,
            capabilities=[STRONG_REASONING, TOOL_USE],
            max_context=120000,
            cost_per_1k_tokens=0.005,
        ),
    }
)
```

### Routing Hints

```python
from code_puppy.tools.router_hooks import RoutingHint, TaskClass

hint = RoutingHint(
    task_class=TaskClass.CODE_GENERATION,
    estimated_tokens=30000,
    requires_tool_use=True,
    prefer_fast=True
)

recommended = hint.get_recommended_models(DEFAULT_MODEL_POOL)
# Returns models sorted by suitability
```

---

## Test Coverage

All modules have comprehensive test suites:

| Module | Test File | Tests |
|--------|-----------|-------|
| io_budget_enforcer | `test_io_budget_enforcer.py` | 35 |
| shell_governor | `test_shell_governor.py` | 35 |
| token_telemetry | `test_token_telemetry.py` | 30 |
| safe_patch | `test_safe_patch.py` | 30 |
| router_hooks | `test_router_hooks.py` | 29 |

**Total: 159 tests, all passing**

Run tests:
```bash
pytest tests/test_io_budget_enforcer.py tests/test_shell_governor.py \
       tests/test_token_telemetry.py tests/test_safe_patch.py \
       tests/test_router_hooks.py -v
```

---

## Integration Points

### Agent Base Class

Wire `io_budget_enforcer` into agent message handling:
```python
# In agents/base.py or similar
from code_puppy.tools.io_budget_enforcer import check_budget

async def send_message(self, messages, provider):
    result = check_budget(estimate_tokens(messages), 0, provider)
    if result.violation == BudgetViolation.HARD:
        raise BudgetExceededError(result.message)
    if result.violation == BudgetViolation.SOFT:
        messages = apply_compaction(messages, result.narrowing_mode)
```

### Command Runner

Wire `shell_governor` into command execution:
```python
# In tools/command_runner.py
from code_puppy.tools.shell_governor import run_governed_command

async def run_command(cmd, cwd):
    return await run_governed_command_async(cmd, cwd=cwd)
```

### LLM Client

Wire `token_telemetry` into response handling:
```python
# In LLM client wrappers
from code_puppy.tools.token_telemetry import TokenLedger

ledger = TokenLedger()

async def complete(self, messages):
    response = await self._client.complete(messages)
    ledger.record_usage(
        provider=self.provider,
        model=self.model,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens
    )
    return response
```

---

## Configuration

Environment variables for customization:

```bash
# IO Budget
CODEPUPPY_BUDGET_SOFT_THRESHOLD=0.70
CODEPUPPY_BUDGET_HARD_THRESHOLD=0.95

# Shell Governor
CODEPUPPY_SHELL_MAX_LINES=160
CODEPUPPY_SHELL_TIMEOUT=120

# Token Telemetry
CODEPUPPY_TELEMETRY_PATH=.codepuppy/usage.jsonl
CODEPUPPY_DAILY_LIMIT=24000000

# Safe Patch
CODEPUPPY_BACKUP_DIR=.codepuppy/backups
CODEPUPPY_MAX_SIZE_INCREASE=10
```

---

## Summary

AUDIT-1.1 provides a comprehensive safety net for token-efficient agent operations:

1. **IO Budgets** prevent runaway token consumption with provider-aware limits
2. **Shell Governor** protects against secret leaks and output explosion
3. **Rate Resilience** handles API throttling gracefully
4. **Token Telemetry** enables burn rate monitoring and budget enforcement
5. **Safe Patch** prevents file corruption and dangerous operations
6. **Router Hooks** enable intelligent model selection based on task requirements

These safeguards work together to ensure code-puppy agents operate efficiently, safely, and within defined resource constraints.

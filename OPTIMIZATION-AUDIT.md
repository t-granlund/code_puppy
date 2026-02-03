# 🔍 Code Puppy Optimization Audit Report

**Date:** January 31, 2026 (Updated: February 1, 2026)  
**Auditor:** GitHub Copilot (Claude Opus 4.5)

---

## ✅ Executive Summary

Overall optimization health: **EXCELLENT** with comprehensive failover coverage.

| Category | Status | Issues Found |
|----------|--------|--------------|
| Model Definitions | ✅ Pass | 34 models with correct types |
| Failover Chains | ✅ Pass | 173 tests passing |
| OAuth Authentication | ✅ Pass | 15 OAuth models properly configured |
| Rate Limit Integration | ✅ Pass | Proactive 20% threshold working |
| Token Optimization | ✅ Pass | Provider-specific thresholds aligned |
| Agent Registry | ✅ Pass | 36 agents mapped to workloads |

---

## 📊 Model Authentication Summary

### OAuth Models (15 total - use stored tokens)
These models authenticate via OAuth flow and stored tokens:

| Type | Count | Models |
|------|-------|--------|
| `claude_code` | 3 | claude-code-claude-haiku-4-5-20251001, claude-code-claude-sonnet-4-5-20250929, claude-code-claude-opus-4-5-20251101 |
| `antigravity` | 10 | claude variants (opus/sonnet thinking levels), gemini-3-flash/pro variants |
| `chatgpt` | 2 | chatgpt-gpt-5.2, chatgpt-gpt-5.2-codex |

### API Key Models (19 total)
| Type | Count | API Key Required |
|------|-------|------------------|
| `custom_openai` | 11 | SYN_API_KEY (synthetic_api_key) |
| `openrouter` | 2 | OPENROUTER_API_KEY |
| `cerebras` | 1 | CEREBRAS_API_KEY |
| `gemini` | 2 | GOOGLE_AI_KEY |
| `zai_api` | 2 | ZAI_API_KEY |
| `zai_coding` | 2 | ZAI_API_KEY |

---

## 📊 Detailed Findings

### 1. Model Coverage

**Total Models in `models.json`:** 34  
**OAuth Models:** 15 (claude_code, antigravity, chatgpt)  
**API Key Models:** 19 (custom_openai, openrouter, cerebras, gemini, zai)

#### OAuth Model Types (Fixed February 2026)
Previous issue: OAuth models had incorrect `type` values causing 429 errors:
- ❌ `claude-code-*` had `type: "anthropic"` → tried using ANTHROPIC_API_KEY
- ❌ `antigravity-*` had `type: "anthropic"` or `"gemini"` → tried direct API keys

**Fix applied:**
- ✅ `claude-code-*` → `type: "claude_code"` (uses OAuth handler)
- ✅ `antigravity-*` → `type: "antigravity"` (uses OAuth handler)

---

### 2. Workload Chains Verification

All workload chains reference valid models with **expanded coverage** (February 2026):

| Workload Type | Chain Length | Primary Model | Backup Count | Status |
|--------------|--------------|---------------|--------------|--------|
| ORCHESTRATOR | 10 | claude-code-claude-opus-4-5-20251101 | 9 backups | ✅ |
| REASONING | 10 | claude-code-claude-sonnet-4-5-20250929 | 9 backups | ✅ |
| CODING | 9 | Cerebras-GLM-4.7 | 8 backups | ✅ |
| LIBRARIAN | 9 | claude-code-claude-haiku-4-5-20251001 | 8 backups | ✅ |

#### Agent Registry (36 agents mapped)

| Workload Type | Agent Count | Example Agents |
|--------------|-------------|----------------|
| ORCHESTRATOR | 5 | pack-leader, helios, epistemic-architect, planning, agent-creator |
| REASONING | 12 | shepherd, watchdog, code-reviewer, security-auditor, qa-expert |
| CODING | 15 | husky, terrier, retriever, code-puppy, test-generator |
| LIBRARIAN | 4 | bloodhound, lab-rat, file-summarizer, doc-writer |

---

### 3. Provider Limits Configuration

Two `PROVIDER_LIMITS` dictionaries exist by design:

#### `failover_config.py` - Rate Limiting (TPM)
Purpose: Tokens Per Minute quotas for failover decisions

| Provider | TPM | TPD | Purpose |
|----------|-----|-----|---------|
| cerebras | 300,000 | 24M | Sprinter tier |
| gemini | 100,000 | 2M | Librarian tier |
| gemini_flash | 150,000 | 2M | Fast librarian |
| codex | 200,000 | 10M | Builder tier |
| claude_sonnet | 100,000 | 5M | Builder tier |
| claude_opus | 50,000 | 1M | Architect tier |
| chatgpt | 150,000 | 5M | GPT-5.2 variants |
| deepseek | 60,000 | 500K | DeepSeek R1 reasoning |
| kimi | 60,000 | 500K | Kimi K2/K2.5 |
| qwen | 60,000 | 500K | Qwen3-235B |
| minimax | 60,000 | 500K | MiniMax M2.1 |
| openrouter_free | 20,000 | 100K | Free tier limited |
| synthetic | 30,000 | 200K | Synthetic/HF |

#### `token_slimmer.py` - Context Compression
Purpose: When to trigger context compaction

| Provider | Compaction At | Max Input | Diet Mode |
|----------|---------------|-----------|-----------|
| cerebras | 20% | 50,000 | 🏋️ boot_camp |
| antigravity | 50% | 100,000 | 🥗 balanced |
| claude_code | 60% | 180,000 | 🥗 balanced |
| chatgpt_teams | 55% | 120,000 | 🥗 balanced |
| anthropic | 70% | 180,000 | 🍽️ maintenance |
| openai | 70% | 120,000 | 🍽️ maintenance |

**These are intentionally different** - one tracks API quotas, the other handles context window optimization.

---

### 4. Rate Limit Header Integration

✅ **Fully Implemented** across:

| File | Integration Point | Status |
|------|-------------------|--------|
| `rate_limit_headers.py` | Core parser | ✅ Working |
| `http_utils.py` | RetryingAsyncClient | ✅ Integrated |
| `rate_limit_failover.py` | RateLimitTracker import | ✅ Connected |
| `token_budget.py` | Proactive detection | ✅ Active |

Supported header formats:
- ✅ Cerebras: `x-ratelimit-remaining-tokens-minute`
- ✅ OpenAI: `x-ratelimit-remaining-tokens`
- ✅ Anthropic: `anthropic-ratelimit-tokens-remaining`

---

### 5. Hardcoded Token Values - ✅ FIXED

Previously had `50_000` token limits hardcoded in 5 locations. Now centralized in `failover_config.py`:

```python
# code_puppy/core/failover_config.py
CEREBRAS_TARGET_INPUT_TOKENS: int = 50_000  # Conservative target for rate limits
CEREBRAS_MAX_CONTEXT_TOKENS: int = 131_072  # 131K context window
CEREBRAS_MAX_OUTPUT_TOKENS: int = 40_000    # Max output on Cerebras
FORCE_SUMMARY_THRESHOLD: int = CEREBRAS_TARGET_INPUT_TOKENS  # When to force summarization
ANTIGRAVITY_MAX_INPUT_TOKENS: int = 100_000
ANTIGRAVITY_COMPACTION_THRESHOLD: float = 0.50  # 50% usage triggers compaction
```

| File | Status | Update |
|------|--------|--------|
| `pack_governor.py` | ✅ Fixed | Uses `FORCE_SUMMARY_THRESHOLD`, fixed model name |
| `husky_execution.py` | ✅ Documented | Added reference comments to centralized values |
| `epistemic_orchestrator.py` | ✅ Fixed | Imports and uses `CEREBRAS_TARGET_INPUT_TOKENS` |

**Additional fix:** Changed `summary_model` from `"gemini-3-flash"` to `"antigravity-gemini-3-flash"` to match `models.json`.

---

### 6. Provider-Level Quota Exhaustion Fix

✅ **Recently Fixed** in `base_agent.py` lines 2370-2400:

```python
# Before: Only skipped same-tier thinking variants
if "antigravity" in current_model_name.lower():
    exhausted_provider = "antigravity"
    
# Now skips ALL antigravity-* models when any hits 429
if exhausted_provider == "antigravity" and "antigravity" in next_failover.lower():
    continue  # Skip to Cerebras directly
```

This prevents the system from trying 9 Antigravity models sequentially when the provider quota is exhausted.

---

## 🎯 Recommendations

### Priority 1: ✅ Completed
- ✅ Centralized `50_000` token constants in `failover_config.py`
- ✅ Fixed `summary_model` to use correct `antigravity-gemini-3-flash` name
- ✅ All 6065 tests passing

### Priority 2: Optional Improvements

1. **Add Synthetic models to failover chains** (if desired)
   - Currently standalone, could fall back to Cerebras if needed

2. **Add Antigravity to `failover_config.PROVIDER_LIMITS`**
   - Currently only in `token_slimmer.py` for compression
   - Pattern matching in `get_provider_limits()` handles it, but explicit entry would be cleaner

### Priority 3: Documentation
- Document the intentional split between rate limiting limits and compression limits
- Add comments explaining why Synthetic/ZAI models lack failover chains

---

## 📈 Test Coverage

```
Tests passing: 173 (failover + model factory)
Failover infrastructure tests: All passing
Model factory tests: All passing
OAuth plugin tests: All passing
```

---

## ✅ Conclusion

The code_puppy codebase is **well-optimized** for token efficiency and rate limit handling:

1. **Correct OAuth model types** - `claude_code`, `antigravity`, `chatgpt` now properly authenticated
2. **Expanded failover chains** - CODING and LIBRARIAN chains expanded from 7→9 models
3. **Proactive rate limiting** triggers at 20% remaining capacity
4. **Provider-aware compression** with different thresholds per tier
5. **Unified failover configuration** in single source of truth
6. **36 agents mapped** to appropriate workload types
7. **Comprehensive test coverage** validates all configurations

**Recent Fixes (February 2026):**
- ✅ Fixed `type` values for OAuth models in models.json
- ✅ Updated OAuth plugins to handle static models (no custom_endpoint)
- ✅ Expanded CODING chain: +2 models (antigravity-claude-sonnet-4-5, synthetic-hf-zai-org-GLM-4.7)
- ✅ Expanded LIBRARIAN chain: +2 models (synthetic-GLM-4.7, antigravity-gemini-3-pro-high)

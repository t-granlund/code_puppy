# GitHub Models API Integration

**Status**: ✅ Production Ready (February 5, 2026)

## Overview

Code Puppy now integrates with the [GitHub Models API](https://docs.github.com/en/github-models), providing access to 8 additional AI models through your GitHub Copilot subscription. These models are automatically available when you have `gh` CLI authenticated.

## Available Models

| Model Name | Provider | Tier | Primary Use Case |
|------------|----------|------|------------------|
| `github-grok-3` | xAI | 2 (Builder High) | Complex reasoning, orchestration |
| `github-deepseek-r1` | DeepSeek | 2 (Builder High) | Deep reasoning, analysis |
| `github-gpt-4.1` | OpenAI | 2 (Builder High) | Strong coding, refactoring |
| `github-grok-3-mini` | xAI | 3 (Builder Mid) | Fast reasoning, review |
| `github-gpt-4.1-mini` | OpenAI | 3 (Builder Mid) | Fast coding tasks |
| `github-gpt-4o` | OpenAI | 3 (Builder Mid) | Balanced coding |
| `github-gpt-4o-mini` | OpenAI | 4 (Librarian) | Search, docs, context |
| `github-phi-4` | Microsoft | 4 (Librarian) | Lightweight tasks |

## Authentication

GitHub Models use automatic authentication via `gh` CLI:

```bash
# No manual setup needed if you have gh CLI authenticated:
gh auth status  # Check if logged in

# If not authenticated:
gh auth login
```

The system automatically:
1. Checks `GH_TOKEN` environment variable
2. Falls back to `gh auth token` command
3. Uses the token for all GitHub Models API calls

## Failover Integration

### Workload Chain Placement

GitHub Models are integrated into workload-specific failover chains:

#### ORCHESTRATOR (Pack Leader, Planning)
```
antigravity-claude-opus-4-5-thinking-high
  → antigravity-gemini-3-pro-high
  → synthetic-Kimi-K2.5-Thinking
  → synthetic-hf-Qwen-Qwen3-235B-A22B-Thinking-2507
  → github-grok-3                    ← GitHub Models (Tier 2)
  → chatgpt-gpt-5.2-codex
  → github-deepseek-r1               ← GitHub Models (Tier 2)
  → synthetic-hf-deepseek-ai-DeepSeek-R1-0528
  → synthetic-Kimi-K2-Thinking
  → github-gpt-4.1                   ← GitHub Models (Tier 2)
  → synthetic-MiniMax-M2.1
  → Cerebras-GLM-4.7
```

#### REASONING (Code Review, Security Audit)
```
antigravity-claude-sonnet-4-5-thinking-medium
  → antigravity-gemini-3-pro-low
  → github-grok-3                    ← GitHub Models (Tier 2)
  → github-deepseek-r1               ← GitHub Models (Tier 2)
  → synthetic-hf-deepseek-ai-DeepSeek-R1-0528
  → synthetic-Kimi-K2-Thinking
  → github-gpt-4.1                   ← GitHub Models (Tier 2)
  → chatgpt-gpt-5.2-codex
  → github-grok-3-mini               ← GitHub Models (Tier 3)
  → synthetic-MiniMax-M2.1
  → chatgpt-gpt-5.2
  → Cerebras-GLM-4.7
```

#### CODING (Main Code Generation)
```
Cerebras-GLM-4.7
  → antigravity-gemini-3-flash
  → synthetic-GLM-4.7
  → zai-glm-4.7-coding
  → github-gpt-4.1-mini              ← GitHub Models (Tier 3)
  → chatgpt-gpt-5.2-codex
  → github-grok-3-mini               ← GitHub Models (Tier 3)
  → antigravity-claude-sonnet-4-5
  → github-gpt-4o                    ← GitHub Models (Tier 3)
  → synthetic-MiniMax-M2.1
  → synthetic-hf-MiniMaxAI-MiniMax-M2.1
  → synthetic-hf-zai-org-GLM-4.7
```

#### LIBRARIAN (Search, Docs, Context)
```
antigravity-gemini-3-flash
  → Gemini-3
  → github-gpt-4o-mini               ← GitHub Models (Tier 4)
  → github-phi-4                     ← GitHub Models (Tier 4)
  → Gemini-3-Long-Context
  → Cerebras-GLM-4.7
  → synthetic-GLM-4.7
  → synthetic-hf-zai-org-GLM-4.7
  → openrouter-arcee-ai-trinity-large-preview-free
  → openrouter-stepfun-step-3.5-flash-free
```

### Linear Failover Chain

GitHub Models also have their own failover progression:

```
github-grok-3 → github-deepseek-r1 → github-gpt-4.1 → github-grok-3-mini
  → github-gpt-4.1-mini → github-gpt-4o → github-gpt-4o-mini → github-phi-4
  → Cerebras-GLM-4.7 (emergency fallback)
```

## Rate Limits

| Provider | Tokens/Minute | Tokens/Day | Tier |
|----------|---------------|------------|------|
| github_models | 150,000 | 5,000,000 | Free |

## Technical Details

### API Endpoint

All GitHub Models use the same base endpoint:
```
https://models.github.ai/inference/
```

### models.json Configuration

```json
{
  "github-grok-3": {
    "model": "xai/grok-3",
    "type": "custom_openai",
    "custom_endpoint": {
      "url": "https://models.github.ai/inference/",
      "api_key": "$GH_TOKEN"
    }
  }
}
```

### Credential Detection

```python
from code_puppy.core.credential_availability import has_valid_credentials

# Check if GitHub models have credentials
has_valid_credentials("github-grok-3")  # Returns True if gh CLI authenticated
```

## Testing GitHub Models

```bash
# Verify authentication
gh auth status

# Test a GitHub model directly
python -c "
from code_puppy.core.credential_availability import has_valid_credentials
print(has_valid_credentials('github-grok-3'))
"

# Run failover simulation
python -c "
from code_puppy.core.failover_config import WORKLOAD_CHAINS, WorkloadType
for wt in WorkloadType:
    print(f'{wt.name}: {len(WORKLOAD_CHAINS[wt])} models')
    github_models = [m for m in WORKLOAD_CHAINS[wt] if m.startswith('github-')]
    if github_models:
        print(f'  GitHub: {github_models}')
"
```

## Changelog

- **2026-02-05**: Initial integration with 8 GitHub Models
- **2026-02-05**: Auto-authentication via `gh auth token` fallback
- **2026-02-05**: Integrated into all workload failover chains

# Code Puppy Authentication Reference

Complete reference for authentication across all model providers.

## Authentication Methods

Code Puppy supports two authentication methods:

1. **API Keys** - Set via environment variables or `/set` commands
2. **OAuth** - Browser-based authentication flow

---

## API Key Providers

Configure these by setting environment variables or using `/set <key_name> = "value"` in Code Puppy:

| Provider | Environment Variable | Where to Get It | Models |
|----------|---------------------|-----------------|---------|
| **Cerebras** | `CEREBRAS_API_KEY` | https://cloud.cerebras.ai/ | Cerebras-GLM-4.7 |
| **Synthetic.new** | `SYN_API_KEY` | https://synthetic.new/ | GLM-4.7, MiniMax M2.1, Kimi K2.5, DeepSeek R1 |
| **OpenAI** | `OPENAI_API_KEY` | https://platform.openai.com/ | GPT-4, GPT-4o, GPT-5.2-Codex |
| **Anthropic** | `ANTHROPIC_API_KEY` | https://console.anthropic.com/ | Claude 3.5/4.5 Sonnet/Opus via API |
| **Google Gemini** | `GEMINI_API_KEY` | https://aistudio.google.com/ | Gemini 3 Pro/Flash |
| **ZAI** | `ZAI_API_KEY` | https://zai.org/ | GLM-4.6/4.7 (coding/api variants) |
| **Azure OpenAI** | `AZURE_OPENAI_API_KEY` | https://portal.azure.com/ | GPT models via Azure |
| **OpenRouter** | `OPENROUTER_API_KEY` | https://openrouter.ai/ | Various models via OpenRouter |
| **Logfire** | `LOGFIRE_TOKEN` | https://logfire.pydantic.dev/ | Telemetry (write token) |

### Setting API Keys

**Option 1: Environment Variables**
```bash
export CEREBRAS_API_KEY="your-key-here"
export SYN_API_KEY="your-key-here"
```

**Option 2: In Code Puppy CLI**
```
/set cerebras_api_key = "your-key-here"
/set syn_api_key = "your-key-here"
```

**Option 3: .env File**
```bash
# .env file in project root
CEREBRAS_API_KEY=your-key-here
SYN_API_KEY=your-key-here
```

---

## OAuth Providers

These require browser-based authentication flows:

| Provider | Command | Token Location | Models |
|----------|---------|----------------|---------|
| **Claude Code** | `/claude-code-auth` | `~/.cache/code-puppy/claude_code_token.json` | Claude Opus 4.5, Sonnet 4.5, Haiku 4.5 |
| **ChatGPT** | `/chatgpt-auth` | `~/.cache/code-puppy/chatgpt_token.json` | GPT-5.2-Codex via subscription |
| **Antigravity** | Manual config | `~/.config/code_puppy/antigravity.json` | Claude Opus/Sonnet, Gemini Pro/Flash |

### OAuth Setup Instructions

#### Claude Code
1. In Code Puppy, run `/claude-code-auth`
2. Browser opens to Claude authentication page
3. Log in with your Claude account
4. Grant access to Code Puppy
5. Token saved automatically

**Requirements:** Claude Code Pro/Max subscription

#### ChatGPT
1. In Code Puppy, run `/chatgpt-auth`
2. Browser opens to ChatGPT authentication page
3. Log in with your OpenAI account
4. Grant access to Code Puppy
5. Token saved automatically

**Requirements:** ChatGPT Plus/Pro/Max subscription

#### Antigravity
1. Create `~/.config/code_puppy/antigravity.json`:
```json
{
  "api_key": "your-antigravity-api-key",
  "endpoint": "https://api.antigravity.com/v1"
}
```

**Requirements:** Antigravity subscription with Claude + Gemini access

---

## Model Catalog by Authentication

### Cerebras API Key Models
```
Cerebras-GLM-4.7
```

### Synthetic API Key Models
```
synthetic-GLM-4.7
synthetic-MiniMax-M2.1
synthetic-Kimi-K2-Thinking
synthetic-Kimi-K2.5-Thinking
synthetic-hf-moonshotai-Kimi-K2.5
synthetic-hf-deepseek-ai-DeepSeek-R1-0528
synthetic-hf-alibaba-Qwen3-235B-Instruct
```

### Claude Code OAuth Models
```
claude-code-claude-haiku-4-5-20251001
claude-code-claude-sonnet-4-5-20250929
claude-code-claude-opus-4-5-20251101
```

### ChatGPT OAuth Models
```
gpt-5.2-codex (via ChatGPT subscription)
```

### Antigravity OAuth Models
```
antigravity-claude-opus-4-5-thinking-low
antigravity-claude-opus-4-5-thinking-medium
antigravity-claude-opus-4-5-thinking-high
antigravity-claude-sonnet-4-5
antigravity-claude-sonnet-4-5-thinking-low/medium/high
antigravity-gemini-3-pro-low
antigravity-gemini-3-pro-high
antigravity-gemini-3-flash
```

### ZAI API Key Models
```
zai-glm-4.6-coding
zai-glm-4.6-api
zai-glm-4.7-coding
zai-glm-4.7-api
```

---

## Checking Authentication Status

Run the authentication checker script:

```bash
python scripts/check_auth_status.py
```

This shows:
- ✅ Configured API keys (with masked values)
- ✅ Authenticated OAuth providers
- ❌ Missing authentication
- 💡 Setup instructions for missing providers

**Example Output:**
```
🔐 Code Puppy Authentication Status

================================================================================

📦 API Key Providers:

  Cerebras             CEREBRAS_API_KEY          ✅ csk_live...x7Vq
  Synthetic.new        SYN_API_KEY               ✅ syn_test...k2mP
  OpenAI               OPENAI_API_KEY            ❌ Not set
  ...

🔐 OAuth Providers:

  Claude Code          OAuth                     ✅ Authenticated
  ChatGPT              OAuth                     ❌ Not authenticated
  Antigravity          OAuth                     ❌ Not configured

================================================================================

📊 Summary:
  • API Key Providers: 2/9 configured
  • OAuth Providers: 1/3 authenticated
  • Total: 3/12 ready
```

---

## Workload-Specific Authentication Requirements

| Workload | Primary Model | Auth Required | Fallback Model | Fallback Auth |
|----------|--------------|---------------|----------------|---------------|
| **CODING** | Cerebras-GLM-4.7 | `CEREBRAS_API_KEY` | Kimi K2.5 | `SYN_API_KEY` |
| **PLANNING** | Claude Opus 4.5 | Claude Code OAuth | Kimi K2.5 | `SYN_API_KEY` |
| **REASONING** | Claude Opus 4.5 | Claude Code OAuth | DeepSeek R1 | `SYN_API_KEY` |
| **RETRIEVAL** | Gemini 3 Pro | `GEMINI_API_KEY` | Claude Haiku | Claude Code OAuth |
| **REVIEW** | Claude Sonnet 4.5 | Claude Code OAuth | GPT-5.2-Codex | ChatGPT OAuth |

---

## Security Best Practices

### API Keys
- ✅ **DO** use environment variables or .env files
- ✅ **DO** add .env to .gitignore
- ✅ **DO** use `/set` for per-session configuration
- ❌ **DON'T** commit API keys to git
- ❌ **DON'T** share API keys in logs or screenshots

### OAuth Tokens
- ✅ Tokens stored in `~/.cache/code-puppy/` with 0600 permissions
- ✅ Auto-refresh handled by Code Puppy
- ✅ Revoke access via provider dashboard if compromised
- ⚠️ **Never** commit OAuth token files to git

---

## Troubleshooting

### "No API key configured for provider X"
**Solution:** Set the API key via environment variable or `/set` command.

### "OAuth token expired or invalid"
**Solution:** Re-run the OAuth flow (`/claude-code-auth` or `/chatgpt-auth`).

### "Rate limit exceeded"
**Solution:** Check Logfire telemetry for `rate_limit` events. Failover should trigger automatically.

### "Model not found"
**Solution:** Check that the model name matches exactly (case-sensitive). Use `/models` to list available models.

---

## Quick Start Checklist

For minimal setup (CODING workload only):

- [ ] Get Cerebras API key from https://cloud.cerebras.ai/
- [ ] Set `CEREBRAS_API_KEY` environment variable
- [ ] (Optional) Set `SYN_API_KEY` for failover to Kimi K2.5
- [ ] Run `python scripts/check_auth_status.py` to verify
- [ ] Test with `/model Cerebras-GLM-4.7` in Code Puppy

For full setup (all workloads):

- [ ] Cerebras API key (`CEREBRAS_API_KEY`)
- [ ] Synthetic API key (`SYN_API_KEY`)
- [ ] Claude Code OAuth (`/claude-code-auth`)
- [ ] Gemini API key (`GEMINI_API_KEY`)
- [ ] (Optional) ChatGPT OAuth (`/chatgpt-auth`)
- [ ] (Optional) Logfire token (`LOGFIRE_TOKEN`)

---

## See Also

- [LOGFIRE-OBSERVABILITY.md](LOGFIRE-OBSERVABILITY.md) - Telemetry health checks
- [ARCHITECTURE-COMPLETE.md](ARCHITECTURE-COMPLETE.md) - System architecture
- [CEREBRAS.md](CEREBRAS.md) - Cerebras-specific configuration

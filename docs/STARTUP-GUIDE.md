# What to Expect When Running Code Puppy

## Current Status (February 4, 2026)

### ⚠️ Authentication Required

Based on the authentication check, **you currently have NO providers configured**. This means:

- ❌ No API keys set
- ❌ No OAuth authentication completed
- ❌ Code Puppy will **NOT** be able to execute any AI model calls

### What Will Happen on Startup

When you run `code-puppy`, here's what you'll experience:

#### 1. **Initial Startup** ✅
- Code Puppy will launch successfully
- CLI interface will appear
- Default agent: `code-puppy` will be loaded
- You'll see the welcome screen

#### 2. **First Interaction** ❌
When you try to send a message or command that requires AI:
```
❌ Error: No API key configured for provider 'cerebras'
❌ Error: Model 'Cerebras-GLM-4.7' is not available
```

This will happen because the default agent tries to use models that require authentication.

---

## Minimum Setup Required (For Your Control-Tower Project)

To work on projects in `~/dev/Control-Tower*`, you need **at least ONE** of these:

### Option 1: Cerebras (Recommended for Coding) ⚡
```bash
# Get API key from: https://cloud.cerebras.ai/
export CEREBRAS_API_KEY="csk_live_xxxxxxxxxxxxx"
```

**Why Cerebras?**
- Primary model for CODING workload (Cerebras-GLM-4.7)
- 1500+ tokens/second
- 200K context window
- Best for rapid iteration

### Option 2: Claude Code (Recommended for Planning) 🧠
```bash
# Start code-puppy first
code-puppy

# Then inside Code Puppy:
/claude-code-auth
```

**Why Claude Code?**
- Best for PLANNING workload (Claude Opus 4.5)
- OAuth - no API key needed
- Requires Claude Code Pro/Max subscription

### Option 3: Synthetic.new (Fallback + Multi-Model) 🔄
```bash
# Get API key from: https://synthetic.new/
export SYN_API_KEY="syn_test_xxxxxxxxxxxxx"
```

**Why Synthetic?**
- Provides access to multiple models (GLM-4.7, Kimi K2.5, MiniMax, DeepSeek R1)
- Good failover option when Cerebras is rate-limited
- Single API key for multiple models

---

## Recommended Setup Sequence

### 1. Set Cerebras API Key (Primary)
```bash
export CEREBRAS_API_KEY="your-cerebras-key"
```

### 2. Set Synthetic API Key (Failover)
```bash
export SYN_API_KEY="your-synthetic-key"
```

### 3. Start Code Puppy
```bash
code-puppy
```

### 4. (Optional) Configure Claude Code
```
/claude-code-auth
```

### 5. Verify Setup
```
/models
```

You should see available models listed.

---

## What Will Work After Minimal Setup

With **Cerebras** configured:

✅ **CODING workload**
- Code generation
- Test writing
- Linting fixes
- File editing

✅ **Basic agents**
- `code-puppy` (main coder)
- `code-reviewer` agents
- `qa-expert`

❌ **What WON'T work without additional auth:**
- `pack-leader` (needs Claude or Codex for planning)
- `epistemic-architect` (needs Claude Opus for reasoning)
- `bloodhound` (needs Gemini for retrieval)

---

## Working with Control-Tower Projects

### Expected Workflow

1. **Navigate to project:**
```bash
cd ~/dev/Control-Tower-YourProject
code-puppy
```

2. **Start with the right agent:**
```
# For coding tasks
/agent code-puppy

# For planning (requires Claude)
/agent pack-leader

# For epistemic planning (requires Claude Opus)
/agent epistemic-architect
```

3. **Verify workload routing:**
The system will automatically route:
- CODING tasks → Cerebras GLM-4.7
- PLANNING tasks → Claude Opus 4.5 (if configured)
- RETRIEVAL tasks → Gemini (if configured)

### Logfire Telemetry (Optional but Recommended)

To verify the system is routing correctly:

```bash
# Set Logfire token (optional)
export LOGFIRE_TOKEN="pylf_v1_us_xxxxx"

# Inside Code Puppy, check routing
# Telemetry events will show:
# - workload_routing: agent→workload→model
# - capacity_warning: when approaching limits
# - failover.triggered: when switching models
```

---

## Troubleshooting Common Issues

### Issue 1: "No API key configured"
**Solution:** Export the required API key before starting:
```bash
export CEREBRAS_API_KEY="your-key"
code-puppy
```

### Issue 2: "Model not found"
**Cause:** Model requires authentication you don't have configured.

**Solution:** Either:
1. Configure the required provider
2. Switch to a model you have access to: `/model Cerebras-GLM-4.7`
3. Pin a different model for that agent: `/pin_model agent-name model-name`

### Issue 3: "Rate limit exceeded"
**Behavior:** 
- Circuit breaker activates
- Auto-failover to backup model (if configured)
- Logfire emits `rate_limit` and `failover.triggered` events

**Solution:**
- Configure fallback providers (Synthetic for Cerebras failover)
- Monitor `capacity_warning` events to predict rate limits

### Issue 4: Agent uses wrong model
**Check workload routing:**
```
# View current routing
/config

# Should show:
# CODING → Cerebras-GLM-4.7
# PLANNING → Claude Opus 4.5
```

**Fix routing:**
```
/pin_model agent-name model-name
```

---

## Session State & Persistence

### What Gets Saved
- `.puppy_session_memory.json` - Session context
- `~/.config/code_puppy/settings.toml` - User settings
- `~/.cache/code_puppy/claude_code_token.json` - OAuth tokens
- `.codepuppy/usage.jsonl` - Token usage history

### What Resets on Restart
- Message history (unless using `/save`)
- Active agent (resets to default)
- Temporary context

---

## Testing Your Setup

### 1. Basic Functionality Test
```bash
# Start Code Puppy
code-puppy

# Send simple test
> Hello, can you help me with Python?

# Expected: Response from configured model
# If error: Check authentication
```

### 2. Workload Routing Test
```
# Test coding workload (should use Cerebras)
> Write a Python function to reverse a string

# Check which model responded
/status

# Should show: model=Cerebras-GLM-4.7
```

### 3. Authentication Status
```
# Run checker script
python scripts/check_auth_status.py

# Expected output shows configured providers
```

---

## Quick Start Checklist

For working on Control-Tower projects, do this:

- [ ] Export `CEREBRAS_API_KEY` environment variable
- [ ] (Optional) Export `SYN_API_KEY` for failover
- [ ] Start `code-puppy` from your project directory
- [ ] Verify models available with `/models`
- [ ] Use `/agent code-puppy` for coding tasks
- [ ] Use `/pin_model` if you need specific models
- [ ] Run `python scripts/check_auth_status.py` to verify setup

---

## Advanced: Full Multi-Provider Setup

If you want ALL features enabled:

```bash
# API Keys
export CEREBRAS_API_KEY="..."      # CODING workload
export SYN_API_KEY="..."            # Failover + multi-model
export GEMINI_API_KEY="..."         # RETRIEVAL workload
export LOGFIRE_TOKEN="..."          # Telemetry (optional)

# OAuth (run these inside Code Puppy)
/claude-code-auth                   # PLANNING + REASONING
/chatgpt-auth                       # GPT-5.2-Codex access

# Start
code-puppy
```

This gives you:
- ✅ All workloads covered (CODING, PLANNING, REASONING, RETRIEVAL)
- ✅ Complete failover chains
- ✅ Telemetry and observability
- ✅ All 20+ agents available

---

## Summary

**Right Now:** Code Puppy will start but **won't work** without authentication.

**Minimum to work:** Set `CEREBRAS_API_KEY` → gives you coding capabilities

**Recommended:** Set `CEREBRAS_API_KEY` + `SYN_API_KEY` → gives you coding + failover

**Full setup:** All API keys + OAuth → gives you everything (planning, reasoning, retrieval, telemetry)

**For Control-Tower projects:** Minimum setup is fine for coding tasks. Add Claude Code OAuth if you need planning/architecture work.

---

## Next Steps

1. **Choose your setup level** (minimum vs full)
2. **Export required environment variables**
3. **Run `code-puppy`**
4. **Test with `/models` and simple query**
5. **Check docs/AUTHENTICATION.md for detailed instructions**

Good luck with your Control-Tower projects! 🐶

# Quick Start for Control-Tower Development

## Your Current Workflow

```bash
cd /Users/tygranlund/code_puppy
source .venv/bin/activate
python -m code_puppy
# Then inside Code Puppy:
/cd /Users/tygranlund/dev/control-tower
```

---

## ⚠️ **Current Status: NO Authentication Configured**

You currently have:
- ❌ No API keys in environment
- ❌ No .env file in the code_puppy directory
- ❌ No OAuth tokens in cache

**This means Code Puppy will start but can't execute AI tasks yet.**

---

## 🚀 **Getting It Working (3 Options)**

### Option 1: Environment Variables (Recommended)
Set these before starting Code Puppy:

```bash
cd /Users/tygranlund/code_puppy

# Set API keys
export CEREBRAS_API_KEY="csk_live_xxxxxxxxxxxxx"
export SYN_API_KEY="syn_test_xxxxxxxxxxxxx"  # Optional failover

# Start Code Puppy
source .venv/bin/activate
python -m code_puppy
```

**Inside Code Puppy:**
```
/cd /Users/tygranlund/dev/control-tower
> Start coding...
```

---

### Option 2: Create .env File (Persistent)
Create a `.env` file in the code_puppy directory:

```bash
cd /Users/tygranlund/code_puppy
cat > .env << 'EOF'
CEREBRAS_API_KEY=csk_live_xxxxxxxxxxxxx
SYN_API_KEY=syn_test_xxxxxxxxxxxxx
GEMINI_API_KEY=your_gemini_key  # Optional
LOGFIRE_TOKEN=pylf_v1_us_xxxx   # Optional
EOF

chmod 600 .env  # Secure it
```

**Add to .gitignore (IMPORTANT!):**
```bash
echo ".env" >> .gitignore
```

Now just start normally:
```bash
source .venv/bin/activate
python -m code_puppy
```

The `.env` file will be auto-loaded!

---

### Option 3: Use /set Commands (Session-Only)
Start Code Puppy first, then configure inside:

```bash
source .venv/bin/activate
python -m code_puppy
```

**Inside Code Puppy:**
```
# Set API keys (session only - won't persist)
/set cerebras_api_key = "csk_live_xxxxxxxxxxxxx"
/set syn_api_key = "syn_test_xxxxxxxxxxxxx"

# Verify
/models

# Navigate to project
/cd /Users/tygranlund/dev/control-tower

# Start working
> Write a function to...
```

---

## 🎯 **Recommended Setup for Control-Tower**

### Step 1: Get API Keys

**Cerebras (Primary):**
1. Go to https://cloud.cerebras.ai/
2. Sign up / Log in
3. Get API key: `csk_live_xxxxxxxxxxxxx`

**Synthetic (Failover):**
1. Go to https://synthetic.new/
2. Sign up
3. Get API key: `syn_test_xxxxxxxxxxxxx`

### Step 2: Create .env File
```bash
cd /Users/tygranlund/code_puppy
nano .env
```

Add:
```
CEREBRAS_API_KEY=csk_live_xxxxxxxxxxxxx
SYN_API_KEY=syn_test_xxxxxxxxxxxxx
```

Save (Ctrl+O, Enter, Ctrl+X)

### Step 3: Secure It
```bash
chmod 600 .env
echo ".env" >> .gitignore
git status  # Verify .env is ignored
```

### Step 4: Test
```bash
source .venv/bin/activate
python -m code_puppy
```

**Inside Code Puppy:**
```
# Verify models
/models

# Should see:
# ✅ Cerebras-GLM-4.7
# ✅ synthetic-Kimi-K2.5
# ✅ synthetic-GLM-4.7
# ... etc

# Navigate to project
/cd /Users/tygranlund/dev/control-tower

# Check current directory
/pwd

# Start coding
> Help me implement authentication for Control-Tower
```

---

## 📋 **Typical Session Workflow**

```bash
# Terminal 1: Start Code Puppy
cd /Users/tygranlund/code_puppy
source .venv/bin/activate
python -m code_puppy
```

**Inside Code Puppy:**
```
# Navigate to your project
/cd /Users/tygranlund/dev/control-tower

# Or a specific subdirectory
/cd /Users/tygranlund/dev/control-tower-api

# Check where you are
/pwd

# List files
> List all Python files in the current directory

# Start working
> Review the authentication module and suggest improvements

# Check token usage
/status

# Save session if needed
/save control-tower-auth-refactor
```

---

## 🔍 **Verifying Your Setup**

### Test 1: Check Authentication
```bash
cd /Users/tygranlund/code_puppy
source .venv/bin/activate
python scripts/check_auth_status.py
```

**Expected output:**
```
✅ Cerebras             CEREBRAS_API_KEY          csk_live...
✅ Synthetic.new        SYN_API_KEY               syn_test...
```

### Test 2: Check Models in Code Puppy
```
/models
```

**Should show:**
```
Available models:
  Cerebras-GLM-4.7 (cerebras)
  synthetic-GLM-4.7 (custom_openai)
  synthetic-Kimi-K2.5-Thinking (custom_openai)
  ...
```

### Test 3: Simple Coding Task
```
/cd /Users/tygranlund/dev/control-tower
> Write a simple hello world function in Python

# Should get a response from Cerebras-GLM-4.7
```

---

## 🛠️ **Troubleshooting**

### Issue: "No API key configured"
**Check:**
```bash
# In terminal BEFORE starting code-puppy
echo $CEREBRAS_API_KEY

# Or check .env file
cat /Users/tygranlund/code_puppy/.env
```

**Fix:**
- If env var not set: `export CEREBRAS_API_KEY="your-key"`
- If .env missing: Create it (see Option 2 above)
- Restart Code Puppy after setting keys

### Issue: /cd doesn't work
**Verify path:**
```bash
ls /Users/tygranlund/dev/control-tower
```

**Inside Code Puppy:**
```
/cd /Users/tygranlund/dev/control-tower
/pwd  # Should show new directory
/ls   # Should list files in control-tower
```

### Issue: Model not found
**Check workload routing:**
```
/config

# Should show:
# default_agent: code-puppy
# model: Cerebras-GLM-4.7
```

**Fix if wrong model:**
```
/model Cerebras-GLM-4.7
# Or
/pin_model code-puppy Cerebras-GLM-4.7
```

### Issue: Rate limits / 429 errors
**Expected behavior:**
- Logfire emits `rate_limit` event
- Circuit breaker activates
- Auto-failover to synthetic-Kimi-K2.5

**To verify:**
```
/status
# Check if failover happened
```

**To add failover protection:**
Set `SYN_API_KEY` in your .env file.

---

## 💡 **Tips for Control-Tower Development**

### 1. Use Agent Pinning
```
# For heavy coding tasks
/agent code-puppy
/pin_model code-puppy Cerebras-GLM-4.7

# For architecture/planning (requires Claude)
/agent pack-leader
```

### 2. Save Your Sessions
```
# Save before major changes
/save control-tower-pre-refactor

# Load later
/load control-tower-pre-refactor
```

### 3. Manage Context
```
# Check token usage
/status

# Truncate if getting too large
/truncate 6

# Or compact
/compact
```

### 4. Multi-Project Workflow
```
# Project 1
/cd /Users/tygranlund/dev/control-tower-api
> Work on API...

# Switch to Project 2
/cd /Users/tygranlund/dev/control-tower-frontend
> Work on frontend...

# Back to Project 1
/cd /Users/tygranlund/dev/control-tower-api
```

### 5. Use Logfire Telemetry
```bash
# Optional: Set Logfire token for telemetry
export LOGFIRE_TOKEN="pylf_v1_us_xxxxx"
```

This gives you real-time visibility into:
- Workload routing (CODING → GLM-4.7)
- Capacity warnings (80%+ usage)
- Failover events
- EAR loop tracking

---

## 📚 **Reference Files**

- [STARTUP-GUIDE.md](STARTUP-GUIDE.md) - General startup guide
- [docs/AUTHENTICATION.md](docs/AUTHENTICATION.md) - All authentication methods
- [scripts/check_auth_status.py](scripts/check_auth_status.py) - Auth checker
- [docs/LOGFIRE-OBSERVABILITY.md](docs/LOGFIRE-OBSERVABILITY.md) - Telemetry queries

---

## ✅ **Your Next Steps**

1. **Get Cerebras API key** (5 minutes)
   - Visit https://cloud.cerebras.ai/
   - Create account
   - Copy API key

2. **Create .env file** (1 minute)
   ```bash
   cd /Users/tygranlund/code_puppy
   echo 'CEREBRAS_API_KEY=your-key-here' > .env
   chmod 600 .env
   echo ".env" >> .gitignore
   ```

3. **Test it** (1 minute)
   ```bash
   source .venv/bin/activate
   python -m code_puppy
   # Then: /cd /Users/tygranlund/dev/control-tower
   ```

4. **Start coding!** 🚀
   ```
   > Help me build Control-Tower
   ```

---

**That's it! You're ready to work on Control-Tower with Code Puppy.** 🐶

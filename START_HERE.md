# 🐶 Code Puppy Quick Start

## 🚀 Start Code Puppy

```bash
# Install the local package first (one-time setup):
cd ~/code_puppy
pip install -e .

# Then from anywhere:
code-puppy

# Or with uv:
cd ~/code_puppy
uv run code-puppy

# Or run directly as Python module:
cd ~/code_puppy
python -m code_puppy
```

## ✅ Verify It's Your Local Version

```bash
# In Code Puppy, run:
/version

# You should see your custom fork info
```

## 🔐 Test OAuth Models

```bash
# Try Antigravity OAuth:
/antigravity_auth
/model antigravity-sonnet-3.7

# Try Claude Code OAuth:
/claude_auth
/model claude-code-sonnet-4.6

# Check which model you're using:
/model
```

## 🆘 If You Forget This

```bash
# Read this file:
cat ~/code_puppy/START_HERE.md

# Or the full contributing guide:
cat ~/code_puppy/CONTRIBUTING.md
```

## 💡 Pro Tips

- `/help` - See all commands
- `/clear` - Start fresh conversation
- `/yolo true` - Skip confirmations (dangerous but fast)
- `/exit` - Peace out ✌️

---

**You're all set! Now go make some magic happen.** ✨

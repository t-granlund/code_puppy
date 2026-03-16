# Local vs PyPI Installation Guide 🐕

> **TL;DR:** Confused whether you're running the PyPI version or your local fork?  
> Run `python scripts/diagnostic.py` to find out instantly.

---

## Table of Contents

1. [The Core Difference](#the-core-difference)
2. [Quick Decision Tree](#quick-decision-tree)
3. [How to Switch Between Versions](#how-to-switch-between-versions)
4. [Pros & Cons Breakdown](#pros--cons-breakdown)
5. [Keeping Your Fork Updated](#keeping-your-fork-updated)
6. [Recommended Workflows](#recommended-workflows)
7. [Troubleshooting](#troubleshooting)

---

## The Core Difference

### 🌐 PyPI Installation (`uvx code-puppy`)

```bash
uvx code-puppy
```

**What's happening:**
- Downloads the **official release** from PyPI (Python Package Index)
- Runs in an **isolated virtual environment** managed by `uv`
- Uses whatever version is published (e.g., `0.2.1`, `0.3.0`, etc.)
- Your **local code changes don't affect it** at all
- Auto-updates when a new version is published

**File location:** Somewhere deep in `uv`'s cache (you don't need to care)

---

### 💻 Local Installation (Editable Mode)

```bash
# From your cloned fork directory
pip install -e .
# or
uv pip install -e .
```

**What's happening:**
- Installs from **your local directory** (the one you're in right now)
- Runs in **editable mode** — changes to `.py` files take effect immediately
- Uses your **fork's code**, including any modifications, plugins, or experiments
- You control when/how to update (via `git pull`)

**File location:** Right here in this directory

---

## Quick Decision Tree

```
┌─────────────────────────────────────────┐
│ What do you want to do?                │
└─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
   Just use it            Develop/customize
   (stable, official)     (plugins, experiments)
        │                       │
        ▼                       ▼
  uvx code-puppy          pip install -e .
  (PyPI version)          (Local editable)
        │                       │
        │                       ▼
        │              Need upstream updates?
        │                       │
        │              git pull upstream main
        │                 (see section 5)
        │                       │
        └───────────────────────┘
                    │
                    ▼
              Run diagnostic to verify:
              python scripts/diagnostic.py
```

---

## How to Switch Between Versions

### ✅ Check Which Version You're Running

**The foolproof way:**

```bash
python scripts/diagnostic.py
```

**Output tells you everything:**
- ✅ Running from local directory with editable install
- ❌ Running from PyPI (uvx) - local changes ignored
- Installation paths, version info, plugin locations

---

### 🔄 Switch to PyPI Version

**1. Uninstall any local installation:**

```bash
# If you used pip
pip uninstall code-puppy

# If you used uv
uv pip uninstall code-puppy
```

**2. Run via uvx:**

```bash
uvx code-puppy
```

**3. Verify:**

```bash
python scripts/diagnostic.py
# Should show: "Running from PyPI (uvx)"
```

---

### 🔧 Switch to Local Editable Install

**1. Make sure you're in your forked repo:**

```bash
cd ~/path/to/your/code-puppy-fork
```

**2. Install in editable mode:**

```bash
# Using pip
pip install -e .

# OR using uv (recommended)
uv pip install -e .
```

**3. Run directly (no uvx):**

```bash
code-puppy
# or
python -m code_puppy.command_line.main
```

**4. Verify:**

```bash
python scripts/diagnostic.py
# Should show: "✅ Running from local directory"
```

---

### 🧹 Clean Slate (Remove Everything)

```bash
# Remove PyPI version
uvx cache clean code-puppy

# Remove local installs
pip uninstall code-puppy
uv pip uninstall code-puppy

# Verify nothing is installed
which code-puppy
# Should return nothing
```

---

## Pros & Cons Breakdown

### 🌐 PyPI Version (`uvx code-puppy`)

#### ✅ Pros
- **Stability** — Official tested releases only
- **Zero setup** — Just run `uvx code-puppy`, no git clone needed
- **Auto-isolation** — Doesn't pollute your system Python
- **Simple updates** — New versions auto-download on next `uvx` run
- **Consistency** — Same version across all machines

#### ❌ Cons
- **No customization** — Can't modify core code
- **Plugin limitations** — User plugins only (in `~/.code_puppy/plugins/`)
- **Slower updates** — Wait for official releases
- **No bleeding-edge features** — Stuck with stable releases
- **Local changes ignored** — Your fork's code doesn't matter

#### 🎯 Best For
- Daily driver usage
- Production environments
- Team consistency (everyone on same version)
- Users who don't need custom core modifications

---

### 💻 Local Editable Install (`pip install -e .`)

#### ✅ Pros
- **Full control** — Modify any file, takes effect immediately
- **Plugin development** — Build plugins in `code_puppy/plugins/`
- **Bleeding edge** — Use unreleased features from `main` branch
- **Experimentation** — Try ideas, break things, learn
- **Custom workflows** — Tailor to your exact needs
- **Contribute upstream** — Test changes before submitting PRs

#### ❌ Cons
- **Stability risk** — You might break things
- **Manual updates** — Need to `git pull` to get new features
- **Merge conflicts** — When pulling upstream changes
- **More setup** — Clone repo, install dependencies, etc.
- **Dependency management** — You own the virtual environment

#### 🎯 Best For
- Plugin development
- Core code modifications
- Contributing to Code Puppy
- Experimenting with new features
- Learning how Code Puppy works

---

## Keeping Your Fork Updated

### Initial Setup (One-Time)

**1. Add upstream remote:**

```bash
cd ~/path/to/your/code-puppy-fork

git remote add upstream https://github.com/TypingKoala/code-puppy.git
git remote -v
# Should show:
# origin    https://github.com/YOUR_USERNAME/code-puppy.git (your fork)
# upstream  https://github.com/TypingKoala/code-puppy.git (original)
```

---

### Regular Update Workflow

**Option A: Merge (Preserves History)**

```bash
# Fetch latest from upstream
git fetch upstream

# Merge into your main branch
git checkout main
git merge upstream/main

# Push to your fork
git push origin main
```

**✅ Pros:** Clean history, safe, easy to understand  
**❌ Cons:** Creates merge commits

---

**Option B: Rebase (Clean History)**

```bash
# Fetch latest from upstream
git fetch upstream

# Rebase your changes on top of upstream
git checkout main
git rebase upstream/main

# Force-push to your fork (if needed)
git push origin main --force-with-lease
```

**✅ Pros:** Linear history, looks cleaner  
**❌ Cons:** Rewrites history (use `--force-with-lease` carefully)

---

### Handling Merge Conflicts

If you get conflicts during merge/rebase:

```bash
# See which files have conflicts
git status

# Edit conflicting files (look for <<<<<<< markers)
# Choose which changes to keep

# After resolving:
git add <resolved-files>

# For merge:
git commit

# For rebase:
git rebase --continue

# If things go wrong, abort:
git merge --abort   # or
git rebase --abort
```

---

### Pro Tip: Test Upstream Changes Before Merging

```bash
# Create a test branch from upstream
git fetch upstream
git checkout -b test-upstream upstream/main

# Install and test
pip install -e .
code-puppy

# If it works, merge into your main
git checkout main
git merge test-upstream
git branch -d test-upstream
```

---

## Recommended Workflows

### 🏃 Daily Driver (Just Want to Use It)

```bash
# Install once
uvx code-puppy

# Run anytime
uvx code-puppy

# Update (automatic on next run if new version exists)
uvx code-puppy
```

**Customization:** Use user plugins in `~/.code_puppy/plugins/`

---

### 🔧 Plugin Developer

```bash
# One-time setup
git clone https://github.com/YOUR_USERNAME/code-puppy.git
cd code-puppy
pip install -e .

# Daily workflow
# 1. Edit plugins in code_puppy/plugins/your_plugin/
# 2. Run to test
code-puppy

# 3. Changes take effect immediately (restart Code Puppy)

# Keep updated weekly
git fetch upstream
git merge upstream/main
```

---

### 🚀 Core Contributor

```bash
# One-time setup
git clone https://github.com/YOUR_USERNAME/code-puppy.git
cd code-puppy
pip install -e .
git remote add upstream https://github.com/TypingKoala/code-puppy.git

# Feature development
git checkout -b feature/my-cool-feature
# ... make changes ...
code-puppy  # test locally

# Before submitting PR
git fetch upstream
git rebase upstream/main
git push origin feature/my-cool-feature
# Open PR on GitHub

# Keep main branch synced
git checkout main
git fetch upstream
git merge upstream/main
git push origin main
```

---

### 🧪 Experimental Fork

```bash
# Fork diverges significantly from upstream
git clone https://github.com/YOUR_USERNAME/code-puppy.git
cd code-puppy
pip install -e .

# Work on your own branch
git checkout -b tyler-custom-edition

# Pull upstream selectively
git fetch upstream
git cherry-pick <specific-commit-hash>
# or merge specific features
git merge upstream/main --no-commit
git reset HEAD <files-you-dont-want>
git commit
```

---

## Troubleshooting

### ❓ "Which version am I running?"

```bash
python scripts/diagnostic.py
```

**Look for:**
- ✅ "Running from local directory with editable install" → Local version
- ❌ "Running from PyPI" → PyPI version via uvx

---

### ❓ "I modified code but nothing changed"

**Cause:** You're running the PyPI version via `uvx code-puppy`

**Fix:**

```bash
# Switch to local install
pip install -e .

# Run without uvx
code-puppy
```

---

### ❓ "I'm getting import errors"

**Cause:** Dependency mismatch or incomplete install

**Fix:**

```bash
# Reinstall dependencies
pip install -e .

# Or with uv
uv pip install -e .

# Nuclear option (clean slate)
pip uninstall code-puppy
rm -rf ~/.cache/uv
pip install -e .
```

---

### ❓ "My user plugins aren't loading"

**Plugins work with BOTH versions!**

User plugins in `~/.code_puppy/plugins/` are loaded by both PyPI and local installs.

**Check:**

```bash
ls -la ~/.code_puppy/plugins/

# Plugin structure should be:
# ~/.code_puppy/plugins/my_plugin/
#   ├── __init__.py
#   └── register_callbacks.py
```

**Debug:**

```bash
# Run with debug logging
code-puppy --verbose
# Watch for plugin loading messages
```

---

### ❓ "Git says I have conflicts"

**Cause:** You modified files that upstream also changed

**Fix:**

```bash
# See what's conflicting
git status

# Decide: keep your changes, take upstream, or mix both
# Edit files with <<<<<<< markers

# After resolving
git add <file>
git commit
```

**Pro tip:** Keep your custom code in plugins to avoid core conflicts!

---

### ❓ "How do I contribute back to upstream?"

**Workflow:**

1. Make sure you're on an updated branch:
   ```bash
   git fetch upstream
   git checkout -b feature/my-feature upstream/main
   ```

2. Make your changes, test locally:
   ```bash
   code-puppy
   ```

3. Commit and push to YOUR fork:
   ```bash
   git push origin feature/my-feature
   ```

4. Open a PR from your fork to upstream on GitHub

5. After PR is merged, update your main:
   ```bash
   git checkout main
   git pull upstream main
   git push origin main
   ```

---

## Summary Cheat Sheet

| Task | Command |
|------|---------|
| **Check which version** | `python scripts/diagnostic.py` |
| **Run PyPI version** | `uvx code-puppy` |
| **Install local editable** | `pip install -e .` |
| **Uninstall local** | `pip uninstall code-puppy` |
| **Update from upstream** | `git fetch upstream && git merge upstream/main` |
| **Create feature branch** | `git checkout -b feature/name` |
| **List installed packages** | `pip list \| grep code-puppy` |
| **Clean uv cache** | `uvx cache clean code-puppy` |
| **Run from source** | `python -m code_puppy.command_line.main` |

---

## Final Recommendations

### For Tyler (Plugin Developer) 🔧

**Install locally in editable mode:**

```bash
cd ~/code-puppy-fork
pip install -e .
code-puppy
```

**Why?**
- Immediate feedback on plugin changes
- Full control over core modifications
- Can contribute back easily
- Learn by breaking things safely

**Update weekly:**

```bash
git fetch upstream
git merge upstream/main
```

---

### For Regular Users 🏃

**Use PyPI via uvx:**

```bash
uvx code-puppy
```

**Why?**
- Zero maintenance
- Stable releases only
- Auto-updates
- Just works™

**Customize via:** `~/.code_puppy/plugins/` for user plugins

---

### The Golden Rule 🌟

> **When in doubt, run the diagnostic:**
> ```bash
> python scripts/diagnostic.py
> ```
> 
> It will tell you exactly what you're running and where it's coming from.

---

## Questions?

Ask Richard! 🐶

```
Hey Richard, am I running the local version or PyPI?
```

Or just run the diagnostic. It's your friend.

**Happy coding!** 🚀

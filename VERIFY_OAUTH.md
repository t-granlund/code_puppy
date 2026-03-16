# 🐶 Claude Code OAuth Verification Tool

Quick verification script to check if your Claude Code OAuth setup is working correctly.

## What It Does

This script performs 4 comprehensive checks:

1. **📁 Token File Check** - Verifies that OAuth tokens exist on disk
2. **✅ Structure Validation** - Checks that all required token fields are present
3. **⏰ Expiry Check** - Validates token hasn't expired and warns if expiring soon
4. **🧪 API Tests** - Makes real API calls to both `claude-opus-4-6` and `claude-sonnet-4-6`

## Usage

```bash
python verify_oauth_fix.py
```

That's it! The script will walk you through each check and report success/failure with helpful emojis.

## When To Use

Run this script whenever you:

- ✅ First authenticate with `/claude_code_login`
- ✅ Verify OAuth authentication is working properly
- ✅ Experience 401 errors with Claude Code models
- ✅ Want to verify tokens are still valid
- ✅ Suspect OAuth issues after updates

## Sample Output

```
🐶 Richard's Claude Code OAuth Verification Tool

This script will check if your OAuth setup is working correctly.

============================================================
  Step 1: Token File Check
============================================================

📁 Looking for tokens at: /Users/you/.code_puppy/claude_code_oauth.json
✅ Token file exists

============================================================
  Step 2: Token Structure Validation
============================================================

✅ All required fields present
✅ Access token format looks valid

============================================================
  Step 3: Token Expiry Check
============================================================

✅ Token is valid for 446.7 more minutes

============================================================
  Step 4: API Call Tests
============================================================

🧪 Testing claude-opus-4-6...
✅ claude-opus-4-6 works perfectly!

🧪 Testing claude-sonnet-4-6...
✅ claude-sonnet-4-6 works perfectly!

────────────────────────────────────────────────────────────
✅ All models tested successfully!

============================================================
  🎉 Success!
============================================================

Your Claude Code OAuth setup is working perfectly!

You can now use opus-4-6 and sonnet-4-6 with Code Puppy!

💡 Switch models with: /model claude-code-opus-4-6
```

## Common Issues & Fixes

### ❌ Token file not found
**Fix:** Run `/claude_code_login` in Code Puppy to authenticate

### ❌ Token is expired
**Fix:** Run `/claude_code_login` to refresh your authentication

### ❌ API calls return 401
**Possible causes:**
- Token is invalid (re-authenticate with `/claude_code_login`)
- OAuth flow didn't complete properly
- Network/firewall blocking Anthropic API
- Token has been revoked

### ⚠️ Token expires soon
**Action:** Consider re-authenticating proactively to avoid interruptions

## Technical Details

The script uses the CORRECT OAuth authentication format:

```python
headers = {
    "Authorization": f"Bearer {access_token}",  # ✅ OAuth uses Bearer token
    "Content-Type": "application/json",
    "anthropic-version": "2023-06-01",
    "anthropic-beta": "oauth-2025-04-20",  # ✅ Required for OAuth
    "User-Agent": "claude-cli/2.0.61 (external, cli)",
    "x-app": "cli",
}
```

**Important:** OAuth tokens use `Authorization: Bearer` format, NOT `x-api-key`!
- `x-api-key` is for direct API keys (e.g., `sk-ant-api03-...`)
- `Authorization: Bearer` is for OAuth tokens

This matches the official Anthropic API authentication format for Claude Code OAuth flows.

## Dependencies

- `requests` library (install with: `pip install requests`)
- Code Puppy with Claude Code OAuth plugin

## Exit Codes

- `0` - All checks passed ✅
- `1` - One or more checks failed ❌
- `130` - User cancelled (Ctrl+C)

---

Made with 🐾 by Richard, your loyal code puppy!

# Claude Code OAuth Authentication Research

**Investigation Period**: March 2026  
**Research Team**: Solutions Architect (solutions-architect-2cb0ce)  
**Status**: Research Complete - Implementation Validated  

---

## Overview

This research directory contains comprehensive documentation on OAuth authentication for Claude Code (Anthropic API) with specific focus on the Claude 4-6 model series (Opus 4-6, Sonnet 4-6).

The research was conducted through **forensic analysis of the Code Puppy production codebase**, specifically the `claude_code_oauth` plugin implementation, which has been validated in production use.

---

## Contents

### 📄 [RESEARCH.md](./RESEARCH.md)
Complete research findings including:
- Authentication header format and requirements
- Model naming conventions for 4-6 series
- Token refresh strategies and best practices
- Extended thinking/effort parameter support
- Common Cloudflare 400 error causes
- STRIDE threat analysis
- Codebase evidence references

**Key Finding**: Cloudflare 400 errors are caused by missing or incorrect `anthropic-beta` header flags and incorrect User-Agent strings at the edge layer.

### 📋 [ADR-001-oauth-authentication-architecture.md](./ADR-001-oauth-authentication-architecture.md)
Architecture Decision Record documenting:
- Chosen authentication architecture
- Header requirements and token refresh strategy
- Security considerations and STRIDE analysis
- Implementation plan and phases
- Alternative approaches considered
- Fitness functions for validation
- Complete working examples

**Status**: Accepted - Production-validated implementation

---

## Quick Reference

### Required Headers for API Requests

```python
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "anthropic-beta": "oauth-2025-04-20,interleaved-thinking-2025-05-14",
    "anthropic-version": "2023-06-01",
    "x-app": "cli",
    "User-Agent": "claude-cli/2.0.61 (external, cli)",
}
```

### Model Names (4-6 Series)

- `claude-opus-4-6` (**no date suffix**)
- `claude-sonnet-4-6` (**no date suffix**)

### Token Refresh Strategy

- **Proactive refresh**: 5 minutes before expiry (not reactive to 401 errors)
- **Adaptive buffer**: 10% of token lifetime (min 30s, max 300s)
- **Formula**: `refresh_when = expires_at - min(300, max(30, expires_in * 0.1))`

---

## Key Evidence Sources

1. **`code_puppy/plugins/claude_code_oauth/utils.py`**
   - Token refresh logic (lines 149-260)
   - Header configuration (lines 230, 400, 514, 575)
   - Model naming (lines 470-480)
   - Effort parameter support (lines 560-565)

2. **`code_puppy/plugins/claude_code_oauth/config.py`**
   - OAuth endpoints and client configuration
   - Model context lengths and beta flags

3. **`SONNET_46_FEATURE.md`**
   - Model capabilities documentation
   - Extended thinking parameter support

4. **`tests/plugins/test_claude_oauth_utils.py`**
   - Header validation test cases
   - OAuth beta flag requirements

---

## Critical Requirements

### ✅ Must Have (Prevents 400 Errors)

1. `anthropic-beta: oauth-2025-04-20` - OAuth flow recognition
2. `anthropic-beta: oauth-2025-04-20,interleaved-thinking-2025-05-14` - Extended thinking support
3. `User-Agent: claude-cli/2.0.61 (external, cli)` - OAuth client signature
4. `x-app: cli` - Client type identifier
5. `anthropic-version: 2023-06-01` - API version

### ⚠️ Security Considerations

- Tokens stored in `~/.code_puppy/claude_code_oauth.json` (plaintext)
- File permissions: `0o700` (owner only)
- **Recommendation**: Implement encryption for token storage
- **Recommendation**: Add audit logging for token usage

---

## Common Issues & Solutions

### Issue: Cloudflare 400 Bad Request

**Symptoms**:
- Error occurs at edge layer (before reaching Anthropic API)
- Valid OAuth token but request rejected
- Generic "Bad Request" with no detailed error message

**Root Causes**:
1. Missing `anthropic-beta: oauth-2025-04-20` header
2. Incorrect beta flag value (case-sensitive)
3. Generic User-Agent (e.g., `python-requests/2.31.0`)
4. Missing `x-app: cli` header

**Solution**:
Use exact headers from production implementation (see Quick Reference above)

### Issue: Token Expiry During Long Sessions

**Symptoms**:
- 401 Unauthorized errors mid-session
- Token valid at start but expires during execution

**Root Cause**:
- Reactive refresh (only on 401 errors)
- No buffer for token refresh timing

**Solution**:
Implement proactive refresh with 5-minute buffer (see Token Refresh Strategy above)

### Issue: Extended Thinking Not Working

**Symptoms**:
- `effort` parameter ignored
- Extended thinking responses not generated

**Root Cause**:
- Missing `interleaved-thinking-2025-05-14` in `anthropic-beta` header
- Using non-4-6 model (effort only supported on Opus 4-6 and Sonnet 4-6)

**Solution**:
- Add `interleaved-thinking-2025-05-14` to beta header
- Use `claude-opus-4-6` or `claude-sonnet-4-6` model

---

## Security Analysis Summary

### STRIDE Threat Model

| Threat | Risk | Status |
|--------|------|--------|
| Information Disclosure | **High** | ⚠️ Plaintext token storage |
| Elevation of Privilege | **Medium** | ⚠️ Indefinite refresh token lifetime |
| Spoofing | Medium | ✅ File permissions (0o700) |
| Tampering | Low | ✅ HTTPS for all operations |
| Repudiation | Low | ⚠️ No audit logging |
| Denial of Service | Low | ✅ Backend rate limiting |

### Planned Security Enhancements

1. Encrypt token storage using `cryptography` library
2. Implement token usage audit logging
3. Add client-side rate limiting (max 10 refresh/min)
4. Periodic refresh token rotation

---

## Implementation Checklist

### OAuth Authentication Setup

- [ ] Obtain OAuth tokens via console.anthropic.com flow
- [ ] Store tokens in secure location (`~/.code_puppy/claude_code_oauth.json`)
- [ ] Set file permissions to `0o700`
- [ ] Implement proactive token refresh logic
- [ ] Add all required headers to API requests
- [ ] Use correct model names (`claude-opus-4-6`, `claude-sonnet-4-6`)
- [ ] Test with minimal API request
- [ ] Validate 200 OK response (not 400 or 401)

### Production Readiness

- [ ] Implement error handling for token refresh failures
- [ ] Add retry logic with exponential backoff
- [ ] Monitor 400 error rates
- [ ] Track token refresh success rates
- [ ] Implement token storage encryption
- [ ] Add audit logging for token usage
- [ ] Set up alerts for OAuth API changes

---

## Testing

### Minimal Test Request

```python
import requests

# Assumes valid tokens already obtained
response = requests.post(
    "https://api.anthropic.com/v1/messages",
    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "anthropic-beta": "oauth-2025-04-20,interleaved-thinking-2025-05-14",
        "anthropic-version": "2023-06-01",
        "x-app": "cli",
        "User-Agent": "claude-cli/2.0.61 (external, cli)",
    },
    json={
        "model": "claude-sonnet-4-6",
        "max_tokens": 100,
        "messages": [{"role": "user", "content": "Hello"}],
    },
)

assert response.status_code == 200, f"Expected 200, got {response.status_code}"
print("✅ OAuth authentication successful!")
```

### Fitness Functions

See [ADR-001 Appendix B](./ADR-001-oauth-authentication-architecture.md#appendix-b-fitness-functions) for complete pytest test suite.

---

## Related Documentation

- [Code Puppy OAuth Plugin](../../code_puppy/plugins/claude_code_oauth/)
- [Sonnet 4-6 Feature Documentation](../../SONNET_46_FEATURE.md)
- [Contributing Guide](../../CONTRIBUTING.md)

---

## Changelog

### 2026-03 (v1.0)
- Initial research document created
- ADR-001 documented and accepted
- Production implementation validated
- STRIDE analysis completed
- Fitness functions defined

---

## Contact

For questions or issues related to this research:

1. **Code Puppy GitHub Issues**: [File a bug report](https://github.com/your-org/code_puppy/issues)
2. **Security Concerns**: Contact Security Auditor
3. **Implementation Questions**: Review ADR-001 and production codebase

---

**Last Updated**: March 2026  
**Maintained by**: Solutions Architect Team  
**Review Frequency**: Quarterly (or when Anthropic updates OAuth API)

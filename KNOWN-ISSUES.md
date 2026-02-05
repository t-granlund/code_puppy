# Known Issues

## ~~Antigravity Claude Models - Tool Usage Bug~~ (RESOLVED)

**Status:** ✅ RESOLVED - Fix Implemented  
**Date Discovered:** 2026-02-04  
**Date Resolved:** 2026-02-04  
**Priority:** ~~HIGH~~ → N/A  
**Affects:** ~~All Antigravity Claude models with tool/function calls~~ (Fixed)

### Resolution

The tool format mismatch bug was **fixed** by implementing `_sanitize_tool_format_in_parts()` in [antigravity_model.py](code_puppy/plugins/antigravity_oauth/antigravity_model.py).

**Fix Details:**
- Added sanitization that converts leaked Claude `tool_use` format back to Gemini `function_call` format
- Tests added in [test_antigravity_sanitization.py](tests/test_antigravity_sanitization.py) - all passing
- Antigravity Claude models restored as primary in workload chains

**Current Workload Chain Status:**
- `ORCHESTRATOR`: Starts with `antigravity-claude-opus-4-5-thinking-high` ✅
- `REASONING`: Starts with `antigravity-claude-sonnet-4-5-thinking-medium` ✅
- `CODING`: Uses `Cerebras-GLM-4.7` primary, Antigravity as backup ✅
- `LIBRARIAN`: Uses `claude-code-claude-haiku` primary ✅

---

### Original Issue (For Reference)

Antigravity Claude models failed with 400 errors when using tools in conversations with existing history:

```
RuntimeError: Antigravity API Error 400: {
  "error": {
    "message": "messages.0.content.2.tool_use.id: String should match pattern '^[a-zA-Z0-9_-]+$'"
  }
}
```

**Root Cause:** Antigravity API internally converts Gemini message format to Claude format. The conversion sometimes leaked Claude `tool_use` format into Gemini parts.

**Solution:** Sanitize all message parts before sending to ensure consistent Gemini format (`function_call` instead of `tool_use`)
   - Automatic failover routes around them

### Alternative Models

**For Orchestrator/Reasoning (Tier 1):**
- ✅ `synthetic-Kimi-K2.5-Thinking` - 1T MoE, excellent for planning
- ✅ `synthetic-hf-Qwen-Qwen3-235B-A22B-Thinking-2507` - Math/reasoning leader
- ✅ `chatgpt-gpt-5.2-codex` - Agentic coding, strong reasoning

**For Builder/Coding (Tier 2-3):**
- ✅ `synthetic-hf-deepseek-ai-DeepSeek-R1-0528` - 671B reasoning model
- ✅ `synthetic-Kimi-K2-Thinking` - 1T MoE thinking
- ✅ `Cerebras-GLM-4.7` - Fastest, agentic coding

### Manual Selection Risk

⚠️ **Warning:** If you manually select Antigravity Claude models via `/m antigravity-claude-*`, you may encounter this bug in multi-turn tool conversations. The system will NOT automatically failover from manual selection.
---

## No Active Issues

All previously known issues have been resolved. See above for historical reference.

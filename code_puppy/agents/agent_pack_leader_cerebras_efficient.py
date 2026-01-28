"""Pack Leader Cerebras Efficient - Token-optimized orchestrator for Cerebras Code Pro.

This agent is designed to minimize input token usage while maintaining effectiveness.
Key behaviors:
1. Diff-driven workflow - prefers git diff, small file snippets, minimal error excerpts
2. Command output limiter - caps shell output to prevent context bloat
3. Micro patch rule - max 2 files per iteration, unified diff only (max 120 lines)
4. Mandatory truncation cadence - prompts user to run /truncate 6 every 2 iterations
5. Token budget guard - estimates prompt size and narrows context if over budget
"""

from typing import List

from code_puppy.config import get_puppy_name, get_value

from .. import callbacks
from .base_agent import BaseAgent


# Default token budget for Cerebras Code Pro (conservative to stay within limits)
DEFAULT_TOKEN_BUDGET = 50000  # ~50K tokens per request is a safe target
DEFAULT_OUTPUT_LINE_LIMIT = 200  # Max lines of shell output to keep


def get_token_budget() -> int:
    """Get the configured token budget for Cerebras efficient mode."""
    val = get_value("cerebras_token_budget")
    return int(val) if val else DEFAULT_TOKEN_BUDGET


def get_output_line_limit() -> int:
    """Get the configured output line limit for shell commands."""
    val = get_value("cerebras_output_limit")
    return int(val) if val else DEFAULT_OUTPUT_LINE_LIMIT


class PackLeaderCerebrasEfficientAgent(BaseAgent):
    """Pack Leader Cerebras Efficient - Optimized for Cerebras Code Pro token limits.
    
    This agent enforces strict token economy:
    - Prefers git diff over full file reads
    - Caps command output to prevent context explosion
    - Limits changes to 2 files per iteration
    - Reminds user to truncate history regularly
    """

    def __init__(self):
        super().__init__()
        self._iteration_count = 0

    @property
    def name(self) -> str:
        return "pack-leader-cerebras-efficient"

    @property
    def display_name(self) -> str:
        return "Pack Leader 🐺⚡ (Cerebras Efficient)"

    @property
    def description(self) -> str:
        return (
            "Token-efficient orchestrator optimized for Cerebras Code Pro. "
            "Uses diff-driven workflow, output limiting, and micro-patches to "
            "minimize input tokens per request."
        )

    def get_available_tools(self) -> List[str]:
        """Get the list of tools available to this agent.
        
        Deliberately limited set to reduce tool definition token overhead.
        """
        return [
            # Minimal exploration tools
            "list_files",
            "read_file",
            "grep",
            # Shell with output limiting enforced
            "agent_run_shell_command",
            # Code editing (diff-focused)
            "edit_file",
            # Transparency
            "agent_share_your_reasoning",
            # Pack coordination (for delegation)
            "list_agents",
            "invoke_agent",
        ]

    def get_system_prompt(self) -> str:
        """Get the token-efficient system prompt."""
        puppy_name = get_puppy_name()
        token_budget = get_token_budget()
        output_limit = get_output_line_limit()

        return f"""You are {puppy_name} as the Pack Leader 🐺⚡ (Cerebras Efficient) - optimized for Cerebras Code Pro!

## 🎯 MISSION: MINIMIZE INPUT TOKENS

You are running on Cerebras Code Pro with these limits:
- 50 RPM (requests per minute)
- 1,000,000 TPM (tokens per minute)
- 24M tokens per day

**Your job: Get maximum coding done with minimum tokens.**

## ⚡ STRICT EFFICIENCY RULES

### 1. DIFF-DRIVEN WORKFLOW
ALWAYS prefer these over reading full files:
```bash
git diff HEAD~3 -- path/to/file.py     # See recent changes
git diff --stat                         # Overview of what changed
head -50 file.py                        # Just the relevant part
tail -50 file.py                        # End of file
sed -n '100,150p' file.py              # Specific line range
```

**REFUSE** requests to read entire large files. Instead:
- Ask which section is relevant (line numbers)
- Use grep to find the specific function/class
- Read only what's needed (50-100 lines max per read)

### 2. COMMAND OUTPUT LIMITER
ALL shell commands must limit output to {output_limit} lines:
```bash
command | tail -{output_limit}          # Last N lines only
command 2>&1 | head -{output_limit}     # First N lines only
command 2>&1 | tail -{output_limit}     # Errors at end
```

For test output, use:
```bash
pytest -q --tb=short 2>&1 | tail -{output_limit}
```

### 3. MICRO PATCH RULE
Per iteration:
- **Maximum 2 files** modified
- **Unified diff only** in your response (max 120 lines)
- If more changes needed, break into multiple iterations

When showing changes, use this format:
```diff
--- a/file.py
+++ b/file.py
@@ -10,3 +10,4 @@
 existing line
+new line
 existing line
```

### 4. MANDATORY TRUNCATION CADENCE
After every 2 iterations, remind the user:
> "🧹 Context growing. Run `/truncate 6` to keep history lean."

Track iterations and enforce this rule.

### 5. TOKEN BUDGET GUARD
Current budget: {token_budget} tokens per request.

Before making large context requests:
1. Estimate: ~2.5 chars per token
2. If request would exceed budget, narrow scope:
   - Ask for specific line ranges
   - Request only error messages, not full logs
   - Use grep instead of reading whole files

## 🔧 AVAILABLE PATTERNS

### Finding Code (Minimal Tokens)
```bash
grep -n "def function_name" --include="*.py" -r .
grep -n "class ClassName" --include="*.py" -r .
git log --oneline -5 -- path/to/file.py
```

### Understanding Changes (Minimal Tokens)
```bash
git diff --name-only HEAD~5
git show --stat HEAD
git log --oneline -10
```

### Testing (Minimal Tokens)
```bash
pytest path/to/test_file.py::test_name -v --tb=short 2>&1 | tail -{output_limit}
python -m py_compile file.py 2>&1  # Syntax check only
```

## 🚫 FORBIDDEN PATTERNS

NEVER do these (they blow up token usage):
- `cat entire_file.py` (read specific sections instead)
- `pytest` without `-q --tb=short` (verbose output bloats context)
- Reading full log files (use `tail -n 100` or grep for errors)
- Multiple large file reads in one turn

## 🐕 DELEGATION

For complex tasks, delegate to specialized agents:
- Use `invoke_agent` to hand off sub-tasks
- Each sub-agent maintains its own context (doesn't bloat yours)
- Collect only the result summary, not full output

## 💡 GOLDEN RULE

Before every action, ask: "Is there a way to do this with fewer tokens?"

If the user asks for something that would exceed token budget:
1. Explain the concern briefly
2. Propose a token-efficient alternative
3. Proceed only with user approval

Remember: You're a good dog who saves tokens! 🐕⚡
"""

    def increment_iteration(self) -> str | None:
        """Increment iteration count and return truncation reminder if needed."""
        self._iteration_count += 1
        if self._iteration_count % 2 == 0:
            return (
                f"🧹 Iteration {self._iteration_count} complete. "
                f"Run `/truncate 6` to keep context lean."
            )
        return None

    def estimate_context_tokens(self) -> int:
        """Estimate current context size in tokens."""
        total = 0
        for msg in self._message_history:
            total += self.estimate_tokens_for_message(msg)
        # Add overhead estimate
        total += self.estimate_context_overhead_tokens()
        return total

    def is_over_budget(self) -> bool:
        """Check if current context exceeds the token budget."""
        return self.estimate_context_tokens() > get_token_budget()

    def get_budget_warning(self) -> str | None:
        """Get a warning message if over budget."""
        if self.is_over_budget():
            current = self.estimate_context_tokens()
            budget = get_token_budget()
            return (
                f"⚠️ Context at ~{current:,} tokens (budget: {budget:,}). "
                f"Run `/truncate 6` or narrow your requests."
            )
        return None

"""Token budget guard utilities for Cerebras efficient mode.

This module provides utilities for estimating and managing token usage
to prevent context explosion when using Cerebras Code Pro.
"""

import re
from typing import Tuple


# Default limits for Cerebras Code Pro
DEFAULT_TOKEN_BUDGET = 50000  # Conservative per-request budget
DEFAULT_OUTPUT_LINE_LIMIT = 200  # Max lines from shell commands


def estimate_tokens(text: str) -> int:
    """Estimate token count for a text string.
    
    Uses a simple heuristic: ~2.5 characters per token on average.
    This is conservative and works well for code.
    
    Args:
        text: The text to estimate tokens for.
        
    Returns:
        Estimated token count.
    """
    if not text:
        return 0
    # ~2.5 chars per token is a reasonable estimate for code
    return max(1, len(text) // 2 + len(text) // 5)


def estimate_file_tokens(content: str) -> int:
    """Estimate tokens for file content.
    
    Args:
        content: File content string.
        
    Returns:
        Estimated token count.
    """
    return estimate_tokens(content)


def limit_output(output: str, max_lines: int = DEFAULT_OUTPUT_LINE_LIMIT) -> Tuple[str, bool]:
    """Limit output to a maximum number of lines.
    
    Args:
        output: The output string to limit.
        max_lines: Maximum number of lines to keep.
        
    Returns:
        Tuple of (limited_output, was_truncated).
    """
    if not output:
        return output, False
        
    lines = output.split('\n')
    if len(lines) <= max_lines:
        return output, False
        
    # Keep last N lines (usually most relevant for errors)
    truncated_lines = lines[-max_lines:]
    truncated_count = len(lines) - max_lines
    
    header = f"[... {truncated_count} lines truncated ...]\n"
    return header + '\n'.join(truncated_lines), True


def limit_diff_output(diff: str, max_lines: int = 120) -> Tuple[str, bool]:
    """Limit diff output while preserving structure.
    
    Keeps the header and tries to preserve complete hunks.
    
    Args:
        diff: The diff string to limit.
        max_lines: Maximum number of lines (default 120 per micro-patch rule).
        
    Returns:
        Tuple of (limited_diff, was_truncated).
    """
    if not diff:
        return diff, False
        
    lines = diff.split('\n')
    if len(lines) <= max_lines:
        return diff, False
    
    result_lines = []
    current_count = 0
    in_header = True
    
    for line in lines:
        # Always include file headers
        if line.startswith('---') or line.startswith('+++') or line.startswith('diff '):
            result_lines.append(line)
            current_count += 1
            in_header = True
            continue
            
        # Include hunk headers
        if line.startswith('@@'):
            if current_count >= max_lines - 10:  # Reserve space for truncation notice
                break
            result_lines.append(line)
            current_count += 1
            in_header = False
            continue
            
        # Include content lines up to limit
        if current_count < max_lines - 5:
            result_lines.append(line)
            current_count += 1
        else:
            break
    
    if current_count < len(lines):
        truncated_count = len(lines) - current_count
        result_lines.append(f"\n[... {truncated_count} more lines in diff ...]")
        return '\n'.join(result_lines), True
    
    return '\n'.join(result_lines), False


def format_token_warning(current_tokens: int, budget: int) -> str:
    """Format a warning message about token usage.
    
    Args:
        current_tokens: Current estimated token count.
        budget: Token budget limit.
        
    Returns:
        Warning message string.
    """
    percent = (current_tokens / budget) * 100
    
    if percent < 70:
        return ""  # No warning needed
    elif percent < 90:
        return (
            f"⚠️ Token usage at {percent:.0f}% ({current_tokens:,}/{budget:,}). "
            f"Consider using /truncate soon."
        )
    else:
        return (
            f"🚨 Token usage CRITICAL at {percent:.0f}% ({current_tokens:,}/{budget:,}). "
            f"Run /truncate 6 NOW to avoid context overflow."
        )


def suggest_narrow_request(request_type: str) -> str:
    """Suggest how to narrow a request to save tokens.
    
    Args:
        request_type: Type of request (e.g., "file_read", "command", "log").
        
    Returns:
        Suggestion string.
    """
    suggestions = {
        "file_read": (
            "Instead of reading the entire file, try:\n"
            "• `head -50 file.py` for the beginning\n"
            "• `sed -n '100,150p' file.py` for specific lines\n"
            "• `grep -n 'pattern' file.py` to find relevant sections"
        ),
        "command": (
            "Limit command output with:\n"
            "• `command | tail -200` for last 200 lines\n"
            "• `command 2>&1 | grep -i error` for errors only\n"
            "• `pytest -q --tb=short` for minimal test output"
        ),
        "log": (
            "For log files, use:\n"
            "• `tail -100 logfile.log` for recent entries\n"
            "• `grep -i 'error\\|exception' logfile.log` for errors\n"
            "• `awk '/timestamp/,/end/' logfile.log` for specific sections"
        ),
        "diff": (
            "For large diffs, narrow scope:\n"
            "• `git diff HEAD~1 -- specific_file.py` for one file\n"
            "• `git diff --stat` for overview only\n"
            "• `git show --name-only HEAD` for changed file list"
        ),
    }
    
    return suggestions.get(request_type, "Try narrowing the scope of your request.")


def calculate_remaining_budget(current_tokens: int, budget: int) -> dict:
    """Calculate remaining token budget and what it allows.
    
    Args:
        current_tokens: Current estimated token count.
        budget: Token budget limit.
        
    Returns:
        Dict with remaining budget info.
    """
    remaining = budget - current_tokens
    
    # Rough estimates of what remaining budget allows
    return {
        "remaining_tokens": remaining,
        "approx_chars": remaining * 2,  # Conservative estimate
        "approx_lines_of_code": remaining // 20,  # ~20 tokens per line of code
        "approx_file_reads": remaining // 500,  # ~500 tokens per small file section
        "is_critical": remaining < budget * 0.1,
        "is_warning": remaining < budget * 0.3,
    }

"""Enforced IO Budgeting for Cerebras and other token-sensitive providers.

⚠️ DEPRECATION NOTICE (2026-01-30):
This module is NOT currently imported anywhere in the codebase.
The token optimization logic has been consolidated into token_slimmer.py.

Use token_slimmer.py instead:
    from code_puppy.tools.token_slimmer import (
        check_token_budget,
        apply_sliding_window,
        get_provider_limits,
        PROVIDER_LIMITS,
    )

This file is kept for reference and may be deleted in a future cleanup.
See docs/AUDIT-TOKEN-OPTIMIZATION.md for the full audit report.

Original Purpose:
This module implements hard caps on input/output tokens per request,
with automatic context narrowing when budgets are exceeded.

AUDIT-1.1 Part D compliance:
- Hard cap prompt size per request (provider-aware)
- Auto-compaction policy when threshold exceeded
- File read/snippet policy with slice enforcement
- Guardrails against full file/repo ingestion
"""

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
import threading

from code_puppy.config import get_value, set_value


# ============================================================================
# Configuration Constants
# ============================================================================

# Default budgets per provider (can be overridden in config)
# Philosophy: Free tiers aggressive, paid tiers relaxed, OAuth balanced
PROVIDER_BUDGETS = {
    # 🏋️ BOOT CAMP: Cerebras free tier - ultra aggressive
    "cerebras": {
        "max_input_tokens": 50000,
        "max_output_tokens": 4096,
        "hard_fail_threshold": 0.80,  # Refuse if > 80%
        "warning_threshold": 0.50,    # Warn if > 50%
        "compaction_threshold": 0.50, # Auto-compact at 50%
    },
    
    # 🥗 BALANCED: OAuth Antigravity (uses various backends)
    "antigravity": {
        "max_input_tokens": 100000,
        "max_output_tokens": 8192,
        "hard_fail_threshold": 0.90,
        "warning_threshold": 0.70,
        "compaction_threshold": 0.60,
    },
    
    # 🥗 BALANCED: Claude Code OAuth
    "claude_code": {
        "max_input_tokens": 180000,
        "max_output_tokens": 8192,
        "hard_fail_threshold": 0.90,
        "warning_threshold": 0.75,
        "compaction_threshold": 0.65,
    },
    
    # 🥗 BALANCED: ChatGPT Teams OAuth
    "chatgpt_teams": {
        "max_input_tokens": 120000,
        "max_output_tokens": 16384,
        "hard_fail_threshold": 0.90,
        "warning_threshold": 0.75,
        "compaction_threshold": 0.65,
    },
    
    # 🍽️ MAINTENANCE: Anthropic API (paid, high limits)
    "anthropic": {
        "max_input_tokens": 180000,
        "max_output_tokens": 8192,
        "hard_fail_threshold": 0.95,
        "warning_threshold": 0.80,
        "compaction_threshold": 0.80,
    },
    
    # 🍽️ MAINTENANCE: OpenAI API (paid)
    "openai": {
        "max_input_tokens": 120000,
        "max_output_tokens": 16384,
        "hard_fail_threshold": 0.95,
        "warning_threshold": 0.80,
        "compaction_threshold": 0.80,
    },
    
    # 🥗 DEFAULT: Safe middle ground
    "default": {
        "max_input_tokens": 30000,
        "max_output_tokens": 4096,
        "hard_fail_threshold": 0.95,
        "warning_threshold": 0.70,
        "compaction_threshold": 0.70,
    },
}

# File reading defaults - TIGHTENED for token efficiency
DEFAULT_MAX_FILE_LINES = 200  # Reduced from 300
DEFAULT_MAX_FILE_TOKENS = 3000  # Reduced from 5000
SLICE_REQUIRED_THRESHOLD = 300  # Reduced from 500 - require slice earlier


class BudgetViolation(Enum):
    """Types of budget violations."""
    NONE = "none"
    WARNING = "warning"
    HARD_FAIL = "hard_fail"
    COMPACTION_NEEDED = "compaction_needed"


class NarrowingMode(Enum):
    """Context narrowing strategies."""
    DIFF_ONLY = "diff_only"
    FILE_SLICE = "file_slice"
    LOG_TAIL = "log_tail"
    ERROR_ONLY = "error_only"


@dataclass
class BudgetCheckResult:
    """Result of a budget check."""
    violation: BudgetViolation
    current_tokens: int
    max_tokens: int
    usage_percent: float
    message: str
    suggested_action: Optional[str] = None
    narrowing_mode: Optional[NarrowingMode] = None
    
    @property
    def should_refuse(self) -> bool:
        return self.violation == BudgetViolation.HARD_FAIL
    
    @property
    def should_compact(self) -> bool:
        return self.violation == BudgetViolation.COMPACTION_NEEDED
    
    @property
    def should_warn(self) -> bool:
        return self.violation in (BudgetViolation.WARNING, BudgetViolation.COMPACTION_NEEDED)


@dataclass
class IterationTracker:
    """Tracks iterations for auto-compaction triggers."""
    iteration_count: int = 0
    last_compaction_at: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    
    def increment(self, input_tokens: int = 0, output_tokens: int = 0):
        """Increment iteration counter and accumulate tokens."""
        self.iteration_count += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
    
    def should_trigger_compaction(self, iterations_between: int = 2) -> bool:
        """Check if compaction should be triggered based on iteration count."""
        iterations_since = self.iteration_count - self.last_compaction_at
        return iterations_since >= iterations_between
    
    def record_compaction(self):
        """Record that compaction occurred."""
        self.last_compaction_at = self.iteration_count


# Global iteration tracker (per-session)
_iteration_tracker = IterationTracker()
_tracker_lock = threading.Lock()


def get_iteration_tracker() -> IterationTracker:
    """Get the global iteration tracker."""
    return _iteration_tracker


def reset_iteration_tracker():
    """Reset the iteration tracker (e.g., on new session)."""
    global _iteration_tracker
    with _tracker_lock:
        _iteration_tracker = IterationTracker()


# ============================================================================
# Provider Budget Management
# ============================================================================

def get_provider_budget(provider: str) -> Dict[str, Any]:
    """Get budget configuration for a provider.
    
    Args:
        provider: Provider name (cerebras, anthropic, openai, antigravity, etc.)
        
    Returns:
        Budget configuration dict.
    """
    provider_lower = provider.lower()
    
    # Check for user overrides first
    override_key = f"{provider_lower}_token_budget"
    override_val = get_value(override_key)
    if override_val:
        try:
            budget = PROVIDER_BUDGETS.get(provider_lower, PROVIDER_BUDGETS["default"]).copy()
            budget["max_input_tokens"] = int(override_val)
            return budget
        except (ValueError, TypeError):
            pass
    
    # Direct match
    if provider_lower in PROVIDER_BUDGETS:
        return PROVIDER_BUDGETS[provider_lower]
    
    # Pattern matching for OAuth providers
    if "antigravity" in provider_lower:
        return PROVIDER_BUDGETS["antigravity"]
    if "claude_code" in provider_lower or "claude-code" in provider_lower:
        return PROVIDER_BUDGETS["claude_code"]
    if "chatgpt" in provider_lower or "teams" in provider_lower:
        return PROVIDER_BUDGETS["chatgpt_teams"]
    
    # Pattern matching for API providers
    if "cerebras" in provider_lower or "glm-4" in provider_lower:
        return PROVIDER_BUDGETS["cerebras"]
    if "anthropic" in provider_lower or "claude" in provider_lower:
        return PROVIDER_BUDGETS["anthropic"]
    if "openai" in provider_lower or "gpt" in provider_lower:
        return PROVIDER_BUDGETS["openai"]
    
    # Return default budget
    return PROVIDER_BUDGETS["default"]


def get_max_input_tokens(provider: str = "cerebras") -> int:
    """Get maximum input tokens for a provider."""
    budget = get_provider_budget(provider)
    return budget["max_input_tokens"]


def get_hard_fail_threshold(provider: str = "cerebras") -> float:
    """Get hard fail threshold for a provider (0.0-1.0)."""
    budget = get_provider_budget(provider)
    return budget["hard_fail_threshold"]


def is_hard_fail_enabled() -> bool:
    """Check if hard fail mode is enabled globally."""
    val = get_value("token_budget_hard_fail")
    if val is None:
        return True  # Default to enabled
    return str(val).lower() in ("true", "1", "yes", "on")


# ============================================================================
# Token Estimation
# ============================================================================

def estimate_tokens(text: str) -> int:
    """Estimate token count for text.
    
    Uses a character-based heuristic that's conservative for code.
    ~2.5 characters per token on average.
    
    Args:
        text: Text to estimate.
        
    Returns:
        Estimated token count.
    """
    if not text:
        return 0
    # ~2.5 chars per token is a reasonable estimate for code
    return max(1, len(text) // 2 + len(text) // 5)


def estimate_message_tokens(messages: List[Dict[str, Any]]) -> int:
    """Estimate tokens for a list of messages.
    
    Args:
        messages: List of message dicts with 'content' field.
        
    Returns:
        Estimated total tokens.
    """
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total += estimate_tokens(content)
        elif isinstance(content, list):
            # Multi-part content (e.g., with images)
            for part in content:
                if isinstance(part, dict) and "text" in part:
                    total += estimate_tokens(part["text"])
        # Add overhead for message structure
        total += 4  # role, content markers, etc.
    return total


# ============================================================================
# Budget Checking
# ============================================================================

def check_budget(
    current_tokens: int,
    provider: str = "cerebras",
    context: str = "request",
) -> BudgetCheckResult:
    """Check if current token usage violates budget.
    
    Args:
        current_tokens: Current estimated token count.
        provider: Provider name for budget lookup.
        context: Context for error messages.
        
    Returns:
        BudgetCheckResult with violation status and suggestions.
    """
    budget = get_provider_budget(provider)
    max_tokens = budget["max_input_tokens"]
    hard_threshold = budget["hard_fail_threshold"]
    warn_threshold = budget["warning_threshold"]
    compact_threshold = budget["compaction_threshold"]
    
    usage_percent = current_tokens / max_tokens if max_tokens > 0 else 1.0
    
    # Check for hard fail
    if usage_percent >= hard_threshold and is_hard_fail_enabled():
        return BudgetCheckResult(
            violation=BudgetViolation.HARD_FAIL,
            current_tokens=current_tokens,
            max_tokens=max_tokens,
            usage_percent=usage_percent,
            message=f"🚫 BUDGET EXCEEDED: {current_tokens:,}/{max_tokens:,} tokens ({usage_percent:.0%}). "
                    f"Request refused. Run /compact or narrow your request.",
            suggested_action="Run /compact, then retry with smaller context",
            narrowing_mode=NarrowingMode.DIFF_ONLY,
        )
    
    # Check for compaction needed
    if usage_percent >= compact_threshold:
        return BudgetCheckResult(
            violation=BudgetViolation.COMPACTION_NEEDED,
            current_tokens=current_tokens,
            max_tokens=max_tokens,
            usage_percent=usage_percent,
            message=f"⚠️ Context at {usage_percent:.0%} - auto-compaction recommended",
            suggested_action="Compacting history automatically",
            narrowing_mode=NarrowingMode.DIFF_ONLY,
        )
    
    # Check for warning
    if usage_percent >= warn_threshold:
        return BudgetCheckResult(
            violation=BudgetViolation.WARNING,
            current_tokens=current_tokens,
            max_tokens=max_tokens,
            usage_percent=usage_percent,
            message=f"⚠️ Token usage at {usage_percent:.0%} ({current_tokens:,}/{max_tokens:,}). "
                    f"Consider /compact soon.",
            suggested_action="Use smaller file slices and diff-only mode",
        )
    
    # All good
    return BudgetCheckResult(
        violation=BudgetViolation.NONE,
        current_tokens=current_tokens,
        max_tokens=max_tokens,
        usage_percent=usage_percent,
        message="",
    )


def check_iteration_compaction() -> Tuple[bool, str]:
    """Check if compaction should trigger based on iteration count.
    
    Returns:
        Tuple of (should_compact, reason).
    """
    tracker = get_iteration_tracker()
    
    # Check iteration threshold (default: every 2 iterations)
    iterations_between = 2
    val = get_value("compaction_iterations")
    if val:
        try:
            iterations_between = int(val)
        except (ValueError, TypeError):
            pass
    
    if tracker.should_trigger_compaction(iterations_between):
        return True, f"Auto-compaction triggered after {iterations_between} iterations"
    
    return False, ""


# ============================================================================
# Context Narrowing
# ============================================================================

def get_narrowing_instructions(mode: NarrowingMode) -> str:
    """Get instructions for narrowing context in a given mode.
    
    Args:
        mode: The narrowing mode to use.
        
    Returns:
        Instructions string for the agent.
    """
    instructions = {
        NarrowingMode.DIFF_ONLY: """
CONTEXT NARROWING ACTIVE - DIFF ONLY MODE:
- Use `git diff HEAD~1` instead of reading full files
- Request file slices with explicit line ranges (e.g., lines 50-100)
- Use `grep` to find specific patterns instead of scanning
- Limit output to last 120 lines for logs/test output
""",
        NarrowingMode.FILE_SLICE: """
CONTEXT NARROWING ACTIVE - FILE SLICE MODE:
- Never read entire files without explicit user approval
- Always specify line ranges when reading (start_line, end_line)
- Maximum 200 lines per file read
- Use `head`, `tail`, or `sed -n 'X,Yp'` for shell reads
""",
        NarrowingMode.LOG_TAIL: """
CONTEXT NARROWING ACTIVE - LOG TAIL MODE:
- Limit all log/output reads to last 120-200 lines
- Use `tail -200` for log files
- Use `grep -i error` to filter for relevant entries
- Summarize rather than paste full logs
""",
        NarrowingMode.ERROR_ONLY: """
CONTEXT NARROWING ACTIVE - ERROR ONLY MODE:
- Only include error messages and stack traces
- Skip successful output entirely
- Use `2>&1 | grep -i 'error\|exception\|failed'`
- Focus on root cause, not full context
""",
    }
    return instructions.get(mode, "")


# ============================================================================
# File Read Guardrails
# ============================================================================

@dataclass
class FileReadPolicy:
    """Policy for reading files."""
    max_lines: int = DEFAULT_MAX_FILE_LINES
    max_tokens: int = DEFAULT_MAX_FILE_TOKENS
    require_slice_above: int = SLICE_REQUIRED_THRESHOLD
    allow_full_file: bool = False


def get_file_read_policy() -> FileReadPolicy:
    """Get the current file read policy from config."""
    policy = FileReadPolicy()
    
    # Check for user overrides
    max_lines = get_value("file_read_max_lines")
    if max_lines:
        try:
            policy.max_lines = int(max_lines)
        except (ValueError, TypeError):
            pass
    
    max_tokens = get_value("file_read_max_tokens")
    if max_tokens:
        try:
            policy.max_tokens = int(max_tokens)
        except (ValueError, TypeError):
            pass
    
    allow_full = get_value("allow_full_file_read")
    if allow_full:
        policy.allow_full_file = str(allow_full).lower() in ("true", "1", "yes")
    
    return policy


def check_file_read(
    file_path: str,
    line_count: int,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
) -> Tuple[bool, str, Optional[Tuple[int, int]]]:
    """Check if a file read is allowed under current policy.
    
    Args:
        file_path: Path to the file.
        line_count: Total lines in the file.
        start_line: Requested start line (None = from beginning).
        end_line: Requested end line (None = to end).
        
    Returns:
        Tuple of (allowed, message, suggested_range).
        If not allowed, suggested_range provides a recommended slice.
    """
    policy = get_file_read_policy()
    
    # Calculate actual read range
    actual_start = start_line if start_line is not None else 1
    actual_end = end_line if end_line is not None else line_count
    lines_to_read = actual_end - actual_start + 1
    
    # If explicit slice provided and within limits, allow
    if start_line is not None and end_line is not None:
        if lines_to_read <= policy.max_lines:
            return True, "", None
        else:
            # Slice too large, suggest smaller
            suggested_end = actual_start + policy.max_lines - 1
            return (
                False,
                f"Requested slice ({lines_to_read} lines) exceeds limit ({policy.max_lines}). "
                f"Use smaller range.",
                (actual_start, suggested_end),
            )
    
    # Full file read requested
    if line_count > policy.require_slice_above:
        if policy.allow_full_file:
            # Warn but allow
            return (
                True,
                f"⚠️ Reading full file ({line_count} lines). Consider using slices for large files.",
                None,
            )
        else:
            # Block and suggest slice
            mid_point = line_count // 2
            suggested_start = max(1, mid_point - policy.max_lines // 2)
            suggested_end = min(line_count, suggested_start + policy.max_lines)
            return (
                False,
                f"🚫 Full file read blocked ({line_count} lines > {policy.require_slice_above} threshold). "
                f"Specify a line range (e.g., lines {suggested_start}-{suggested_end}).",
                (suggested_start, suggested_end),
            )
    
    # Small file, allow
    return True, "", None


# ============================================================================
# Compaction Summary Format
# ============================================================================

@dataclass
class CompactionSummary:
    """Structured summary for compacted history."""
    goals: List[str] = field(default_factory=list)
    current_branch: str = ""
    changed_files: List[str] = field(default_factory=list)
    failing_commands: List[str] = field(default_factory=list)
    current_hypothesis: str = ""
    next_actions: List[str] = field(default_factory=list)
    key_decisions: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_markdown(self) -> str:
        """Convert to markdown summary."""
        lines = ["## Session Summary (Compacted)", ""]
        
        if self.current_branch:
            lines.append(f"**Branch:** `{self.current_branch}`")
        
        if self.goals:
            lines.append("\n**Goals:**")
            for goal in self.goals[:3]:  # Max 3
                lines.append(f"- {goal}")
        
        if self.changed_files:
            lines.append("\n**Changed Files:**")
            for f in self.changed_files[:5]:  # Max 5
                lines.append(f"- `{f}`")
        
        if self.failing_commands:
            lines.append("\n**Recent Failures:**")
            for cmd in self.failing_commands[:3]:  # Max 3
                lines.append(f"- `{cmd}`")
        
        if self.current_hypothesis:
            lines.append(f"\n**Current Hypothesis:** {self.current_hypothesis}")
        
        if self.next_actions:
            lines.append("\n**Next Actions:**")
            for action in self.next_actions[:3]:  # Max 3
                lines.append(f"1. {action}")
        
        if self.key_decisions:
            lines.append("\n**Key Decisions:**")
            for decision in self.key_decisions[:3]:
                lines.append(f"- {decision}")
        
        lines.append(f"\n*Compacted at {self.timestamp[:19]}*")
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "goals": self.goals,
            "current_branch": self.current_branch,
            "changed_files": self.changed_files,
            "failing_commands": self.failing_commands,
            "current_hypothesis": self.current_hypothesis,
            "next_actions": self.next_actions,
            "key_decisions": self.key_decisions,
            "timestamp": self.timestamp,
        }


def extract_compaction_summary(messages: List[Dict[str, Any]]) -> CompactionSummary:
    """Extract a structured summary from message history.
    
    This is a heuristic extraction - a proper implementation would
    use an LLM for summarization (as in the existing /compact command).
    
    Args:
        messages: List of message dicts.
        
    Returns:
        CompactionSummary with extracted information.
    """
    import re
    
    summary = CompactionSummary()
    
    for msg in messages:
        content = msg.get("content", "")
        if not isinstance(content, str):
            continue
        
        # Extract git branch mentions
        branch_match = re.search(r'branch[:\s]+[`"]?([a-zA-Z0-9/_-]+)[`"]?', content, re.I)
        if branch_match and not summary.current_branch:
            summary.current_branch = branch_match.group(1)
        
        # Extract file paths
        file_matches = re.findall(r'[`"]([a-zA-Z0-9_/.-]+\.[a-zA-Z]+)[`"]', content)
        for f in file_matches:
            if f not in summary.changed_files and len(summary.changed_files) < 10:
                summary.changed_files.append(f)
        
        # Extract failing commands (look for error patterns)
        if "error" in content.lower() or "failed" in content.lower():
            cmd_match = re.search(r'[`$]\s*([^`\n]+)', content)
            if cmd_match and len(summary.failing_commands) < 5:
                summary.failing_commands.append(cmd_match.group(1)[:100])
    
    return summary

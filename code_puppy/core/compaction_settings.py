"""Context Compaction Settings - Aligned with pydantic-ai #4137 proposal.

This module implements the CompactionSettings API proposed in:
https://github.com/pydantic/pydantic-ai/issues/4137

Key features:
- Token threshold-based compaction triggering
- Protected tokens to preserve recent context
- Pre/post compaction hooks
- Tool call pairing preservation
- First user prompt protection
- ThinkingPart preservation (per @mpfaffenberger's suggestions)
"""

from __future__ import annotations

import hashlib
import logging
import warnings
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol, Set, Tuple

from pydantic import BaseModel, Field, model_validator

logger = logging.getLogger(__name__)


class CompactionStrategy(str, Enum):
    """Strategy for message history compaction."""

    SUMMARIZATION = "summarization"  # Use LLM to summarize old context
    TRUNCATION = "truncation"  # Simple head/tail truncation
    HYBRID = "hybrid"  # Summarize old, truncate middle


class CompactionHook(Protocol):
    """Protocol for compaction hooks."""

    async def __call__(
        self,
        context: "CompactionContext",
        messages: List[Any],
    ) -> List[Any]:
        """Process messages before/after compaction.
        
        Args:
            context: Current compaction context with usage info
            messages: Messages to process
            
        Returns:
            Processed messages
        """
        ...


@dataclass
class ToolCallPair:
    """A paired tool call and its response.
    
    These should be kept together during compaction to maintain context.
    """

    call_id: str
    tool_name: str
    call_message_idx: int
    return_message_idx: int
    is_protected: bool = False  # If True, never compact this pair


@dataclass
class CompactionContext:
    """Context provided to compaction hooks and processors."""

    # Current usage
    current_tokens: int
    threshold_tokens: int
    protected_tokens: int
    
    # Model info
    model_name: str
    model_context_limit: int
    
    # Tool call tracking
    tool_call_pairs: List[ToolCallPair] = field(default_factory=list)
    
    # Metrics
    compaction_count: int = 0  # How many times compaction has run
    tokens_saved_total: int = 0  # Total tokens saved across all compactions
    
    @property
    def utilization(self) -> float:
        """Current context utilization as percentage."""
        if self.model_context_limit == 0:
            return 0.0
        return self.current_tokens / self.model_context_limit
    
    @property
    def should_compact(self) -> bool:
        """Whether compaction should be triggered."""
        return self.current_tokens >= self.threshold_tokens
    
    @property
    def tokens_to_free(self) -> int:
        """How many tokens need to be freed."""
        if not self.should_compact:
            return 0
        # Free enough to get below threshold with some buffer
        target = int(self.threshold_tokens * 0.7)
        return max(0, self.current_tokens - target)


class CompactionSettings(BaseModel):
    """Context compaction settings following pydantic-ai #4137 proposal.
    
    This provides first-class support for automatic context compaction
    when token usage exceeds thresholds.
    
    Example:
        ```python
        settings = CompactionSettings(
            token_threshold=80_000,
            protected_tokens=30_000,
            summarization_model="anthropic:claude-haiku-4-5",
        )
        
        agent = Agent(
            model="anthropic:claude-sonnet-4-5",
            compaction=settings,
        )
        ```
    """

    # Core settings
    enabled: bool = Field(
        default=True,
        description="Whether compaction is enabled",
    )
    
    token_threshold: int = Field(
        default=80_000,
        ge=10_000,
        description="Token count that triggers compaction",
    )
    
    protected_tokens: int = Field(
        default=30_000,
        ge=5_000,
        description="Number of recent tokens protected from compaction",
    )
    
    # Strategy
    strategy: CompactionStrategy = Field(
        default=CompactionStrategy.SUMMARIZATION,
        description="Compaction strategy to use",
    )
    
    # Model for summarization
    summarization_model: Optional[str] = Field(
        default=None,
        description="Model to use for summarization (defaults to main model)",
    )
    
    summary_prompt: Optional[str] = Field(
        default=None,
        description="Custom prompt for summarization",
    )
    
    # Safety settings (per @mpfaffenberger's suggestions)
    preserve_first_user_prompt: bool = Field(
        default=True,
        description="Never summarize the initial user context",
    )
    
    preserve_thinking_parts: bool = Field(
        default=True,
        description="Preserve ThinkingPart signatures from Claude/GPT",
    )
    
    preserve_tool_call_pairs: bool = Field(
        default=True,
        description="Keep tool calls paired with their responses",
    )
    
    protected_tool_types: List[str] = Field(
        default_factory=lambda: ["edit_file", "create_file", "run_command"],
        description="Tool types that should be protected from compaction",
    )
    
    max_protected_tool_calls: int = Field(
        default=10,
        ge=1,
        description="Maximum number of recent tool calls to protect",
    )

    @model_validator(mode="after")
    def validate_thresholds(self) -> "CompactionSettings":
        """Validate that settings are sensible."""
        if self.token_threshold <= self.protected_tokens:
            raise ValueError(
                f"token_threshold ({self.token_threshold}) must be > "
                f"protected_tokens ({self.protected_tokens})"
            )
        
        ratio = self.token_threshold / self.protected_tokens
        if ratio < 1.5:
            warnings.warn(
                f"Ratio of threshold:protected ({ratio:.2f}) is < 1.5, "
                "may cause frequent compaction",
                UserWarning,
            )
        
        return self
    
    def create_context(
        self,
        current_tokens: int,
        model_name: str,
        model_context_limit: int,
    ) -> CompactionContext:
        """Create a compaction context for current state."""
        return CompactionContext(
            current_tokens=current_tokens,
            threshold_tokens=self.token_threshold,
            protected_tokens=self.protected_tokens,
            model_name=model_name,
            model_context_limit=model_context_limit,
        )


class MessageCompactor:
    """Handles the actual compaction of message history.
    
    This class processes messages according to CompactionSettings,
    preserving protected content while compacting older messages.
    """

    def __init__(
        self,
        settings: CompactionSettings,
        pre_compaction_hook: Optional[CompactionHook] = None,
        post_compaction_hook: Optional[CompactionHook] = None,
    ):
        self.settings = settings
        self.pre_compaction_hook = pre_compaction_hook
        self.post_compaction_hook = post_compaction_hook
        self._message_hashes: Set[str] = set()  # Track compacted messages
    
    def _hash_message(self, message: Any) -> str:
        """Generate hash for a message."""
        content = str(message)
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _find_tool_call_pairs(
        self,
        messages: List[Any],
    ) -> List[ToolCallPair]:
        """Find paired tool calls and responses in message history.
        
        This ensures tool calls are never separated from their responses
        during compaction, maintaining semantic coherence.
        """
        pairs = []
        pending_calls: Dict[str, Tuple[int, str]] = {}  # call_id -> (idx, tool_name)
        
        for idx, msg in enumerate(messages):
            # Check for tool call parts
            if hasattr(msg, "parts"):
                for part in msg.parts:
                    if hasattr(part, "tool_call_id"):
                        # This is a tool call
                        call_id = part.tool_call_id
                        tool_name = getattr(part, "tool_name", "unknown")
                        pending_calls[call_id] = (idx, tool_name)
                    elif hasattr(part, "tool_return_id"):
                        # This is a tool return
                        return_id = part.tool_return_id
                        if return_id in pending_calls:
                            call_idx, tool_name = pending_calls.pop(return_id)
                            # Check if this tool type is protected
                            is_protected = tool_name in self.settings.protected_tool_types
                            pairs.append(ToolCallPair(
                                call_id=return_id,
                                tool_name=tool_name,
                                call_message_idx=call_idx,
                                return_message_idx=idx,
                                is_protected=is_protected,
                            ))
        
        return pairs
    
    def _identify_protected_indices(
        self,
        messages: List[Any],
        context: CompactionContext,
    ) -> Set[int]:
        """Identify message indices that should be protected from compaction."""
        protected = set()
        
        # Always protect first message (system prompt)
        if messages:
            protected.add(0)
        
        # Protect first user prompt if setting enabled
        if self.settings.preserve_first_user_prompt:
            for idx, msg in enumerate(messages):
                if hasattr(msg, "role") and msg.role == "user":
                    protected.add(idx)
                    break
        
        # Protect recent messages within protected_tokens budget
        # Start from end, accumulate until we hit budget
        token_count = 0
        for idx in range(len(messages) - 1, -1, -1):
            # Estimate tokens (rough: 4 chars per token)
            msg_tokens = len(str(messages[idx])) // 4
            if token_count + msg_tokens <= self.settings.protected_tokens // 4:
                protected.add(idx)
                token_count += msg_tokens
            else:
                break
        
        # Protect tool call pairs
        if self.settings.preserve_tool_call_pairs:
            pairs = self._find_tool_call_pairs(messages)
            # Protect recent pairs up to max
            recent_pairs = sorted(
                pairs,
                key=lambda p: p.return_message_idx,
                reverse=True,
            )[:self.settings.max_protected_tool_calls]
            
            for pair in recent_pairs:
                protected.add(pair.call_message_idx)
                protected.add(pair.return_message_idx)
                # Also protect messages in between
                for idx in range(pair.call_message_idx, pair.return_message_idx + 1):
                    protected.add(idx)
        
        # Store pairs in context for hooks
        context.tool_call_pairs = self._find_tool_call_pairs(messages)
        
        return protected
    
    async def compact(
        self,
        messages: List[Any],
        context: CompactionContext,
        summarize_fn: Optional[Callable[[List[Any]], str]] = None,
    ) -> List[Any]:
        """Compact messages according to settings.
        
        Args:
            messages: Message history to compact
            context: Current compaction context
            summarize_fn: Optional function to summarize messages
            
        Returns:
            Compacted message list
        """
        if not self.settings.enabled or not context.should_compact:
            return messages
        
        logger.info(
            f"Compacting messages: {context.current_tokens} tokens, "
            f"threshold: {context.threshold_tokens}"
        )
        
        # Pre-compaction hook
        if self.pre_compaction_hook:
            messages = await self.pre_compaction_hook(context, messages)
        
        # Identify protected indices
        protected_indices = self._identify_protected_indices(messages, context)
        
        # Separate protected and compactable messages
        protected_messages = []
        compactable_messages = []
        
        for idx, msg in enumerate(messages):
            if idx in protected_indices:
                protected_messages.append((idx, msg))
            else:
                # Skip if already compacted
                msg_hash = self._hash_message(msg)
                if msg_hash not in self._message_hashes:
                    compactable_messages.append((idx, msg))
                    self._message_hashes.add(msg_hash)
        
        # Apply compaction strategy
        if self.settings.strategy == CompactionStrategy.TRUNCATION:
            # Simple: drop middle messages
            result = self._truncate_messages(
                protected_messages,
                compactable_messages,
                context,
            )
        elif self.settings.strategy == CompactionStrategy.SUMMARIZATION:
            # Summarize old messages
            result = await self._summarize_messages(
                protected_messages,
                compactable_messages,
                context,
                summarize_fn,
            )
        else:  # HYBRID
            # Summarize oldest, truncate middle
            result = await self._hybrid_compact(
                protected_messages,
                compactable_messages,
                context,
                summarize_fn,
            )
        
        # Post-compaction hook
        if self.post_compaction_hook:
            result = await self.post_compaction_hook(context, result)
        
        # Update metrics
        context.compaction_count += 1
        saved = context.current_tokens - (len(str(result)) // 4)
        context.tokens_saved_total += saved
        
        logger.info(
            f"Compaction complete: saved ~{saved} tokens, "
            f"total saved: {context.tokens_saved_total}"
        )
        
        return result
    
    def _truncate_messages(
        self,
        protected: List[Tuple[int, Any]],
        compactable: List[Tuple[int, Any]],
        context: CompactionContext,
    ) -> List[Any]:
        """Truncate compactable messages, keeping head and tail."""
        # Sort by original index
        all_msgs = sorted(protected + compactable, key=lambda x: x[0])
        
        # If we need to drop messages, drop from middle of compactable
        tokens_to_free = context.tokens_to_free
        tokens_freed = 0
        
        # Find middle range to drop
        comp_indices = [idx for idx, _ in compactable]
        if not comp_indices:
            return [msg for _, msg in all_msgs]
        
        # Drop from the middle third
        start_drop = len(comp_indices) // 3
        end_drop = 2 * len(comp_indices) // 3
        
        drop_set = set()
        for i in range(start_drop, end_drop):
            if tokens_freed >= tokens_to_free:
                break
            idx = comp_indices[i]
            drop_set.add(idx)
            # Estimate tokens freed
            tokens_freed += len(str(compactable[i][1])) // 4
        
        # Rebuild without dropped messages
        result = []
        for idx, msg in all_msgs:
            if idx not in drop_set:
                result.append(msg)
        
        return result
    
    async def _summarize_messages(
        self,
        protected: List[Tuple[int, Any]],
        compactable: List[Tuple[int, Any]],
        context: CompactionContext,
        summarize_fn: Optional[Callable],
    ) -> List[Any]:
        """Summarize old compactable messages."""
        if not summarize_fn or not compactable:
            return self._truncate_messages(protected, compactable, context)
        
        # Get oldest half of compactable messages to summarize
        half = len(compactable) // 2
        to_summarize = [msg for _, msg in compactable[:half]]
        to_keep = compactable[half:]
        
        # Summarize
        try:
            summary = await summarize_fn(to_summarize)
            # Create summary message
            from pydantic_ai.messages import ModelRequest, TextPart
            summary_msg = ModelRequest(parts=[TextPart(content=f"[Previous context summary]: {summary}")])
        except Exception as e:
            logger.warning(f"Summarization failed: {e}, falling back to truncation")
            return self._truncate_messages(protected, compactable, context)
        
        # Rebuild: protected + summary + kept compactable
        protected_sorted = sorted(protected, key=lambda x: x[0])
        to_keep_sorted = sorted(to_keep, key=lambda x: x[0])
        
        result = [msg for _, msg in protected_sorted[:1]]  # System prompt first
        result.append(summary_msg)  # Then summary
        result.extend([msg for _, msg in protected_sorted[1:]])  # Rest of protected
        result.extend([msg for _, msg in to_keep_sorted])  # Kept compactable
        
        return result
    
    async def _hybrid_compact(
        self,
        protected: List[Tuple[int, Any]],
        compactable: List[Tuple[int, Any]],
        context: CompactionContext,
        summarize_fn: Optional[Callable],
    ) -> List[Any]:
        """Hybrid: summarize oldest third, truncate middle third."""
        if not compactable:
            return [msg for _, msg in sorted(protected, key=lambda x: x[0])]
        
        third = len(compactable) // 3
        
        # Summarize oldest third
        to_summarize = compactable[:third]
        # Drop middle third
        to_drop = compactable[third:2*third]
        # Keep newest third
        to_keep = compactable[2*third:]
        
        # Summarize if possible
        summary_msg = None
        if summarize_fn and to_summarize:
            try:
                summary = await summarize_fn([msg for _, msg in to_summarize])
                from pydantic_ai.messages import ModelRequest, TextPart
                summary_msg = ModelRequest(parts=[TextPart(content=f"[Context summary]: {summary}")])
            except Exception as e:
                logger.warning(f"Summarization failed in hybrid: {e}")
        
        # Rebuild
        protected_sorted = sorted(protected, key=lambda x: x[0])
        to_keep_sorted = sorted(to_keep, key=lambda x: x[0])
        
        result = [msg for _, msg in protected_sorted[:1]]  # System prompt
        if summary_msg:
            result.append(summary_msg)
        result.extend([msg for _, msg in protected_sorted[1:]])
        result.extend([msg for _, msg in to_keep_sorted])
        
        return result


# Default settings instance
DEFAULT_COMPACTION_SETTINGS = CompactionSettings()


def get_compaction_settings() -> CompactionSettings:
    """Get compaction settings from environment/config."""
    from code_puppy.config import (
        get_compaction_strategy,
        get_compaction_threshold,
        get_protected_token_count,
    )
    
    strategy_str = get_compaction_strategy()
    try:
        strategy = CompactionStrategy(strategy_str)
    except ValueError:
        strategy = CompactionStrategy.SUMMARIZATION
    
    threshold = get_compaction_threshold()
    protected = get_protected_token_count()
    
    # Convert threshold ratio to absolute tokens
    # Assume 128k context as baseline
    token_threshold = int(128_000 * threshold)
    
    return CompactionSettings(
        strategy=strategy,
        token_threshold=token_threshold,
        protected_tokens=protected,
    )

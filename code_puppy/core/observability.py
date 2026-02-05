"""Observability utilities for consistent Logfire logging.

This module provides centralized logging utilities that ensure:
- Config key (our model name) is always logged alongside API model name
- Model selection, failover, and execution events are properly tracked
- Consistent naming and formatting across the codebase
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Try to import logfire, but don't fail if not available
try:
    import logfire
    LOGFIRE_AVAILABLE = True
except ImportError:
    LOGFIRE_AVAILABLE = False
    logfire = None


@dataclass
class ModelContext:
    """Context for model usage logging.
    
    Attributes:
        config_key: Our configuration key (e.g., "synthetic-Kimi-K2.5-Thinking")
        api_model_name: The actual API model name (e.g., "hf:moonshotai/Kimi-K2.5")
        workload: The workload type (e.g., "ORCHESTRATOR")
        agent_name: The agent using this model
    """
    config_key: str
    api_model_name: Optional[str] = None
    workload: Optional[str] = None
    agent_name: Optional[str] = None
    
    def __post_init__(self):
        # If api_model_name not provided, try to look it up
        if not self.api_model_name:
            self.api_model_name = get_api_model_name(self.config_key)


# Cache for config key -> API model name mappings
_model_name_cache: dict[str, str] = {}


def get_api_model_name(config_key: str) -> str:
    """Get the underlying API model name for a config key.
    
    Args:
        config_key: Our configuration key (e.g., "synthetic-Kimi-K2.5-Thinking")
        
    Returns:
        The API model name (e.g., "hf:moonshotai/Kimi-K2.5") or config_key if not found
    """
    if config_key in _model_name_cache:
        return _model_name_cache[config_key]
    
    try:
        from code_puppy.model_factory import ModelFactory
        config = ModelFactory.load_config()
        model_config = config.get(config_key, {})
        api_name = model_config.get("name", config_key)
        _model_name_cache[config_key] = api_name
        return api_name
    except Exception:
        return config_key


def clear_model_name_cache():
    """Clear the model name cache (useful for testing)."""
    _model_name_cache.clear()


# =============================================================================
# MODEL SELECTION LOGGING
# =============================================================================

def log_model_selected(
    config_key: str,
    agent_name: str,
    workload: str,
    reason: str = "workload_routing",
    **extra_fields: Any,
) -> None:
    """Log when a model is selected for an agent.
    
    Args:
        config_key: Our configuration key for the model
        agent_name: Name of the agent
        workload: Workload type (ORCHESTRATOR, REASONING, CODING, LIBRARIAN)
        reason: Why this model was selected
        **extra_fields: Additional fields to log
    """
    if not LOGFIRE_AVAILABLE:
        return
    
    api_model_name = get_api_model_name(config_key)
    
    try:
        logfire.info(
            "Model selected: {agent} → {config_key} (API: {api_model})",
            agent=agent_name,
            config_key=config_key,
            api_model=api_model_name,
            workload=workload,
            reason=reason,
            **extra_fields,
        )
    except Exception as e:
        logger.debug(f"Failed to log model selection: {e}")


def log_model_fallback(
    from_config_key: str,
    to_config_key: str,
    agent_name: str,
    reason: str,
    **extra_fields: Any,
) -> None:
    """Log when falling back from one model to another.
    
    Args:
        from_config_key: Config key of the model that failed
        to_config_key: Config key of the fallback model
        agent_name: Name of the agent
        reason: Why the fallback happened
        **extra_fields: Additional fields to log
    """
    if not LOGFIRE_AVAILABLE:
        return
    
    from_api = get_api_model_name(from_config_key)
    to_api = get_api_model_name(to_config_key)
    
    try:
        logfire.warn(
            "Model fallback: {from_key} → {to_key} ({reason})",
            agent=agent_name,
            from_key=from_config_key,
            from_api=from_api,
            to_key=to_config_key,
            to_api=to_api,
            reason=reason,
            **extra_fields,
        )
    except Exception as e:
        logger.debug(f"Failed to log model fallback: {e}")


# =============================================================================
# FAILOVER LOGGING
# =============================================================================

def log_failover_triggered(
    from_model: str,
    to_model: str,
    workload: str,
    error_type: str,
    attempt: int,
    backoff_delay: float = 0.0,
    **extra_fields: Any,
) -> None:
    """Log when a failover is triggered.
    
    Args:
        from_model: Model that failed (may be config key or API name)
        to_model: Model being failed over to
        workload: Workload type
        error_type: Type of error that triggered failover
        attempt: Attempt number
        backoff_delay: Delay before retry
        **extra_fields: Additional fields to log
    """
    if not LOGFIRE_AVAILABLE:
        return
    
    try:
        logfire.warn(
            "Failover: {from_model} → {to_model} ({error_type})",
            from_model=from_model,
            to_model=to_model,
            workload=workload,
            error_type=error_type,
            attempt=attempt,
            backoff_delay=backoff_delay,
            **extra_fields,
        )
    except Exception as e:
        logger.debug(f"Failed to log failover: {e}")


def log_failover_success(
    model: str,
    workload: str,
    attempt: int,
    **extra_fields: Any,
) -> None:
    """Log when a failover succeeds.
    
    Args:
        model: Model that succeeded
        workload: Workload type
        attempt: Attempt number
        **extra_fields: Additional fields to log
    """
    if not LOGFIRE_AVAILABLE:
        return
    
    try:
        logfire.info(
            "Failover success: {model} ({workload}) - attempt {attempt}",
            model=model,
            workload=workload,
            attempt=attempt,
            **extra_fields,
        )
    except Exception as e:
        logger.debug(f"Failed to log failover success: {e}")


def log_rate_limit(
    model: str,
    workload: str,
    cooldown_seconds: float,
    consecutive_429s: int = 0,
    **extra_fields: Any,
) -> None:
    """Log when a model hits rate limit.
    
    Args:
        model: Model that was rate limited
        workload: Workload type
        cooldown_seconds: How long the model is in cooldown
        consecutive_429s: Number of consecutive 429 errors
        **extra_fields: Additional fields to log
    """
    if not LOGFIRE_AVAILABLE:
        return
    
    try:
        logfire.warn(
            "Rate limit: {model} ({workload}) - cooldown {cooldown}s",
            model=model,
            workload=workload,
            cooldown=cooldown_seconds,
            consecutive_429s=consecutive_429s,
            **extra_fields,
        )
    except Exception as e:
        logger.debug(f"Failed to log rate limit: {e}")


# =============================================================================
# AGENT DELEGATION LOGGING
# =============================================================================

def log_agent_delegation(
    invoker: str,
    target: str,
    ooda_phase: str,
    workload: str,
    session_id: Optional[str] = None,
    is_new_session: bool = True,
    **extra_fields: Any,
) -> None:
    """Log when one agent delegates to another.
    
    Args:
        invoker: Name of the invoking agent
        target: Name of the target agent
        ooda_phase: OODA loop phase (OBSERVE, ORIENT, DECIDE, ACT)
        workload: Target agent's workload type
        session_id: Session ID for the delegation
        is_new_session: Whether this is a new session
        **extra_fields: Additional fields to log
    """
    if not LOGFIRE_AVAILABLE:
        return
    
    try:
        logfire.info(
            "OODA Delegation: {invoker} → {target} ({phase}, {workload})",
            invoker=invoker,
            target=target,
            phase=ooda_phase,
            workload=workload,
            session_id=session_id,
            is_new_session=is_new_session,
            **extra_fields,
        )
    except Exception as e:
        logger.debug(f"Failed to log agent delegation: {e}")


def log_agent_delegation_complete(
    invoker: str,
    target: str,
    success: bool,
    duration_seconds: Optional[float] = None,
    error: Optional[str] = None,
    **extra_fields: Any,
) -> None:
    """Log when an agent delegation completes.
    
    Args:
        invoker: Name of the invoking agent
        target: Name of the target agent
        success: Whether the delegation succeeded
        duration_seconds: How long the delegation took
        error: Error message if failed
        **extra_fields: Additional fields to log
    """
    if not LOGFIRE_AVAILABLE:
        return
    
    try:
        if success:
            logfire.info(
                "Delegation complete: {invoker} ← {target} (success)",
                invoker=invoker,
                target=target,
                success=True,
                duration_seconds=duration_seconds,
                **extra_fields,
            )
        else:
            logfire.warn(
                "Delegation failed: {invoker} ← {target} ({error})",
                invoker=invoker,
                target=target,
                success=False,
                duration_seconds=duration_seconds,
                error=error,
                **extra_fields,
            )
    except Exception as e:
        logger.debug(f"Failed to log delegation completion: {e}")


# =============================================================================
# REQUEST LOGGING
# =============================================================================

def log_request_start(
    agent_name: str,
    config_key: str,
    prompt_preview: str = "",
    **extra_fields: Any,
) -> None:
    """Log when an agent request starts.
    
    Args:
        agent_name: Name of the agent
        config_key: Config key of the model being used
        prompt_preview: First ~100 chars of the prompt
        **extra_fields: Additional fields to log
    """
    if not LOGFIRE_AVAILABLE:
        return
    
    api_model = get_api_model_name(config_key)
    
    try:
        logfire.info(
            "Request start: {agent} using {config_key}",
            agent=agent_name,
            config_key=config_key,
            api_model=api_model,
            prompt_preview=prompt_preview[:100] if prompt_preview else "",
            **extra_fields,
        )
    except Exception as e:
        logger.debug(f"Failed to log request start: {e}")


def log_request_complete(
    agent_name: str,
    config_key: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    duration_seconds: Optional[float] = None,
    **extra_fields: Any,
) -> None:
    """Log when an agent request completes.
    
    Args:
        agent_name: Name of the agent
        config_key: Config key of the model used
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        duration_seconds: Request duration
        **extra_fields: Additional fields to log
    """
    if not LOGFIRE_AVAILABLE:
        return
    
    api_model = get_api_model_name(config_key)
    
    try:
        logfire.info(
            "Request complete: {agent} ({input_tokens} in, {output_tokens} out)",
            agent=agent_name,
            config_key=config_key,
            api_model=api_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_seconds=duration_seconds,
            **extra_fields,
        )
    except Exception as e:
        logger.debug(f"Failed to log request complete: {e}")

"""FallbackModel configuration and event logging (OPT-006).

Provides:
- Configurable fallback chains per agent
- Structured fallback event logging with full context
- Foundation for future Pydantic AI FallbackModel integration

Audit finding (OPT-006-A): Pydantic AI FallbackModel is NOT currently
used. The existing fallback mechanism is manual sequential candidate
selection in base_agent._load_model_with_fallback(). max_retries is
only set for Azure clients (default 2) with no conflicts.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# In-memory fallback event log for the current session
_fallback_events: List[Dict[str, Any]] = []

# Cache for fallback chain config
_fallback_chains_cache: Optional[Dict[str, List[str]]] = None
_fallback_chains_loaded: bool = False


def _get_fallback_config_file() -> Path:
    """Get path to fallback chain configuration file."""
    from code_puppy.config import CONFIG_DIR

    return Path(CONFIG_DIR) / "fallback_chains.json"


def load_fallback_chains() -> Dict[str, List[str]]:
    """Load configured fallback chains.

    File format (~/.code_puppy/fallback_chains.json):
    {
        "default": ["openai:gpt-5.2", "anthropic:claude-sonnet-4-6"],
        "code-reviewer": ["anthropic:claude-sonnet-4-6", "openai:gpt-5.2"]
    }

    Returns:
        Dict mapping agent names (or "default") to ordered model lists.
    """
    global _fallback_chains_cache, _fallback_chains_loaded

    if _fallback_chains_loaded:
        return _fallback_chains_cache or {}

    _fallback_chains_loaded = True
    config_file = _get_fallback_config_file()

    if not config_file.exists():
        _fallback_chains_cache = {}
        return {}

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            logger.warning(
                "fallback_chains.json must be a JSON object, got %s",
                type(data).__name__,
            )
            _fallback_chains_cache = {}
            return {}
        # Validate each entry is a list of strings
        validated = {}
        for key, chain in data.items():
            if isinstance(chain, list) and all(isinstance(m, str) for m in chain):
                validated[key] = chain
            else:
                logger.warning(
                    "Invalid fallback chain for '%s' — must be a list of model name strings",
                    key,
                )
        _fallback_chains_cache = validated
        logger.debug("Loaded fallback chains for %d agents", len(validated))
        return validated
    except json.JSONDecodeError as e:
        logger.warning("Failed to parse fallback_chains.json: %s", e)
        _fallback_chains_cache = {}
        return {}
    except Exception as e:
        logger.warning("Failed to read fallback_chains.json: %s", e)
        _fallback_chains_cache = {}
        return {}


def get_fallback_chain(agent_name: str) -> List[str]:
    """Get the fallback chain for an agent.

    Checks agent-specific chain first, then "default" chain.

    Args:
        agent_name: Name of the agent.

    Returns:
        Ordered list of model names to try. Empty if no chain configured.
    """
    chains = load_fallback_chains()
    return chains.get(agent_name, chains.get("default", []))


def log_fallback_event(
    source_model: str,
    target_model: str,
    error_reason: str,
    agent_name: str = "unknown",
) -> None:
    """Log a fallback activation event with full context (OPT-006-C).

    Args:
        source_model: The model that failed.
        target_model: The model being fallen back to.
        error_reason: Why the source model failed.
        agent_name: Name of the agent experiencing the fallback.
    """
    event = {
        "timestamp": time.time(),
        "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "agent_name": agent_name,
        "source_model": source_model,
        "target_model": target_model,
        "error_reason": str(error_reason),
    }
    _fallback_events.append(event)

    logger.warning(
        "Model fallback: '%s' → '%s' for agent '%s' (reason: %s)",
        source_model,
        target_model,
        agent_name,
        error_reason,
    )


def get_fallback_events() -> List[Dict[str, Any]]:
    """Get all fallback events from the current session.

    Returns:
        List of fallback event dicts with timestamp, models, reason.
    """
    return list(_fallback_events)


def get_primary_unavailable_duration() -> Optional[float]:
    """Check if the primary model has been unavailable for an extended period.

    Returns:
        Duration in seconds since last primary model failure, or None if no failures.
    """
    if not _fallback_events:
        return None

    # Find the most recent fallback event
    latest = _fallback_events[-1]
    return time.time() - latest["timestamp"]


def clear_events() -> None:
    """Clear fallback event log (for testing)."""
    _fallback_events.clear()


def clear_cache() -> None:
    """Clear fallback chain config cache (for testing)."""
    global _fallback_chains_cache, _fallback_chains_loaded
    _fallback_chains_cache = None
    _fallback_chains_loaded = False

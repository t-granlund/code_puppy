"""Model capability registry for tool-calling validation (OPT-004-B).

Provides a simple capability lookup for models, supporting:
1. Built-in defaults inferred from model type/provider
2. User overrides via ~/.code_puppy/model_capabilities.json
3. Extensible without code changes

Usage:
    from code_puppy.model_capabilities import supports_tool_calling, get_model_capabilities

    if not supports_tool_calling("my-model"):
        print("This model doesn't support tool calling!")
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Default capabilities by model type (from models.json "type" field)
_TYPE_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "openai": {"tool_calling": True},
    "anthropic": {"tool_calling": True},
    "google": {"tool_calling": True},
    "groq": {"tool_calling": True},
    "custom_openai": {"tool_calling": True},
    "mistral": {"tool_calling": True},
    "cerebras": {"tool_calling": True},
    "xai": {"tool_calling": True},
    "antigravity": {"tool_calling": True},
    "claude_code": {"tool_calling": True},
    "chatgpt": {"tool_calling": True},
    "gemini": {"tool_calling": True},
    "ollama": {"tool_calling": False},
}

# Cache for user overrides
_user_overrides_cache: Optional[Dict[str, Dict[str, Any]]] = None
_user_overrides_loaded: bool = False


def _get_capabilities_file() -> Path:
    """Get path to user model capabilities override file."""
    from code_puppy.config import CONFIG_DIR

    return Path(CONFIG_DIR) / "model_capabilities.json"


def _load_user_overrides() -> Dict[str, Dict[str, Any]]:
    """Load user capability overrides from config file.

    File format:
    {
        "my-custom-model": {"tool_calling": true},
        "ollama-llama3": {"tool_calling": false}
    }

    Returns:
        Dict mapping model names to capability dicts.
    """
    global _user_overrides_cache, _user_overrides_loaded

    if _user_overrides_loaded:
        return _user_overrides_cache or {}

    _user_overrides_loaded = True
    cap_file = _get_capabilities_file()

    if not cap_file.exists():
        _user_overrides_cache = {}
        return {}

    try:
        with open(cap_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            logger.warning(
                "model_capabilities.json must be a JSON object, got %s",
                type(data).__name__,
            )
            _user_overrides_cache = {}
            return {}
        _user_overrides_cache = data
        logger.debug("Loaded model capabilities for %d models", len(data))
        return data
    except json.JSONDecodeError as e:
        logger.warning("Failed to parse model_capabilities.json: %s", e)
        _user_overrides_cache = {}
        return {}
    except Exception as e:
        logger.warning("Failed to read model_capabilities.json: %s", e)
        _user_overrides_cache = {}
        return {}


def _get_model_type(model_name: str) -> Optional[str]:
    """Look up the model type from models.json config.

    Returns:
        Model type string (e.g. "openai", "anthropic") or None.
    """
    try:
        from code_puppy.model_factory import ModelFactory

        config = ModelFactory.load_config()
        model_config = config.get(model_name, {})
        return model_config.get("type")
    except Exception:
        return None


def get_model_capabilities(model_name: str) -> Dict[str, Any]:
    """Get capabilities for a model.

    Lookup order:
    1. User overrides (~/.code_puppy/model_capabilities.json)
    2. Built-in defaults by model type
    3. Empty dict if unknown

    Args:
        model_name: Name of the model to look up.

    Returns:
        Dict of capabilities (e.g. {"tool_calling": True}).
    """
    # Check user overrides first
    overrides = _load_user_overrides()
    if model_name in overrides:
        return overrides[model_name]

    # Infer from model type
    model_type = _get_model_type(model_name)
    if model_type and model_type in _TYPE_DEFAULTS:
        return _TYPE_DEFAULTS[model_type].copy()

    # Unknown model — return empty capabilities
    logger.debug(
        "No capability info for model '%s' (type=%s) — "
        "add to ~/.code_puppy/model_capabilities.json to configure",
        model_name,
        model_type or "unknown",
    )
    return {}


def supports_tool_calling(model_name: str) -> Optional[bool]:
    """Check if a model supports tool calling.

    Returns:
        True if supported, False if not, None if unknown.
    """
    caps = get_model_capabilities(model_name)
    return caps.get("tool_calling")


def validate_agent_model_compatibility(
    agent_name: str,
    model_name: str,
    requires_tool_calling: bool,
) -> tuple[bool, str]:
    """Validate that a model is compatible with an agent's requirements.

    Args:
        agent_name: Name of the agent.
        model_name: Name of the model being assigned.
        requires_tool_calling: Whether the agent requires tool calling.

    Returns:
        Tuple of (is_compatible, message). If incompatible, message explains why.
    """
    if not requires_tool_calling:
        return True, ""

    tool_support = supports_tool_calling(model_name)

    if tool_support is False:
        return False, (
            f"Model '{model_name}' does not support tool calling, "
            f"but agent '{agent_name}' requires it. "
            f"Choose a tool-calling capable model or set "
            f"requires_tool_calling: false in the agent config."
        )
    elif tool_support is None:
        logger.info(
            "Tool-calling support unknown for model '%s' assigned to agent '%s'. "
            "Add to ~/.code_puppy/model_capabilities.json to suppress this warning.",
            model_name,
            agent_name,
        )
        return True, ""  # Allow but log

    return True, ""


def clear_cache() -> None:
    """Clear the user overrides cache (for testing)."""
    global _user_overrides_cache, _user_overrides_loaded
    _user_overrides_cache = None
    _user_overrides_loaded = False

"""Credential Availability Checker - Model Filtering by Authentication Status.

This module checks whether models have valid credentials (API keys or OAuth tokens)
before including them in failover chains or round-robin selection.

Models without valid credentials are automatically excluded from:
- Failover chains
- Round-robin rotation
- Smart model selection
- Capacity-aware routing

Supported credential types:
- API Keys: Environment variables or config values
- OAuth Tokens: Stored tokens with valid access_token and refresh capability

Provider to credential mapping:
- claude_code: OAuth (Claude Code OAuth plugin)
- antigravity: OAuth (Antigravity OAuth plugin)
- chatgpt: OAuth (ChatGPT OAuth plugin)
- gemini: API key (GEMINI_API_KEY)
- cerebras: API key (CEREBRAS_API_KEY)
- synthetic: API key (SYN_API_KEY)
- openrouter: API key (OPENROUTER_API_KEY)
- zai: API key (ZAI_API_KEY)
- openai: API key (OPENAI_API_KEY)
- anthropic: API key (ANTHROPIC_API_KEY)
"""

import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# CREDENTIAL TYPE DEFINITIONS
# =============================================================================

class CredentialType:
    """Types of credentials supported."""
    API_KEY = "api_key"
    OAUTH = "oauth"


# Provider to credential type and key mapping
# For API keys, can specify multiple alternative names as a tuple
PROVIDER_CREDENTIALS: Dict[str, Tuple[str, str | tuple]] = {
    # (credential_type, env_var_or_oauth_plugin)
    # For API keys, can be a single string or tuple of alternatives
    
    # OAuth-based providers
    "claude_code": (CredentialType.OAUTH, "claude_code_oauth"),
    "antigravity": (CredentialType.OAUTH, "antigravity_oauth"),
    "chatgpt": (CredentialType.OAUTH, "chatgpt_oauth"),
    
    # API key providers (with alternative names for /set command compatibility)
    "gemini": (CredentialType.API_KEY, ("GEMINI_API_KEY", "gemini_api_key")),
    "cerebras": (CredentialType.API_KEY, ("CEREBRAS_API_KEY", "cerebras_api_key")),
    "synthetic": (CredentialType.API_KEY, ("SYN_API_KEY", "synthetic_api_key", "syn_api_key")),
    "openrouter": (CredentialType.API_KEY, ("OPENROUTER_API_KEY", "openrouter_api_key")),
    "zai": (CredentialType.API_KEY, ("ZAI_API_KEY", "zai_api_key")),
    "openai": (CredentialType.API_KEY, ("OPENAI_API_KEY", "openai_api_key")),
    "anthropic": (CredentialType.API_KEY, ("ANTHROPIC_API_KEY", "anthropic_api_key")),
    "azure_openai": (CredentialType.API_KEY, ("AZURE_OPENAI_API_KEY", "azure_openai_api_key")),
}


# Model name to provider mapping (extends smart_selection.py)
# This is authoritative - all models must be mapped here
MODEL_TO_PROVIDER: Dict[str, str] = {
    # Claude Code (OAuth)
    "claude-code-claude-opus-4-5-20251101": "claude_code",
    "claude-code-claude-sonnet-4-5-20250929": "claude_code",
    "claude-code-claude-haiku-4-5-20251001": "claude_code",
    
    # Antigravity (OAuth proxy)
    "antigravity-claude-opus-4-5-thinking-low": "antigravity",
    "antigravity-claude-opus-4-5-thinking-medium": "antigravity",
    "antigravity-claude-opus-4-5-thinking-high": "antigravity",
    "antigravity-claude-sonnet-4-5": "antigravity",
    "antigravity-claude-sonnet-4-5-thinking-low": "antigravity",
    "antigravity-claude-sonnet-4-5-thinking-medium": "antigravity",
    "antigravity-claude-sonnet-4-5-thinking-high": "antigravity",
    "antigravity-gemini-3-pro-low": "antigravity",
    "antigravity-gemini-3-pro-high": "antigravity",
    "antigravity-gemini-3-flash": "antigravity",
    
    # ChatGPT (OAuth)
    "chatgpt-gpt-5.2": "chatgpt",
    "chatgpt-gpt-5.2-codex": "chatgpt",
    
    # Gemini (API key)
    "Gemini-3": "gemini",
    "Gemini-3-Long-Context": "gemini",
    
    # Cerebras (API key)
    "Cerebras-GLM-4.7": "cerebras",
    
    # Synthetic (API key)
    "synthetic-GLM-4.7": "synthetic",
    "synthetic-MiniMax-M2.1": "synthetic",
    "synthetic-Kimi-K2-Thinking": "synthetic",
    "synthetic-Kimi-K2.5-Thinking": "synthetic",
    "synthetic-Kimi-K2.5-Thinking": "synthetic",
    "synthetic-Kimi-K2-Thinking": "synthetic",
    "synthetic-hf-deepseek-ai-DeepSeek-R1-0528": "synthetic",
    "synthetic-hf-MiniMaxAI-MiniMax-M2.1": "synthetic",
    "synthetic-hf-Qwen-Qwen3-235B-A22B-Thinking-2507": "synthetic",
    "synthetic-hf-zai-org-GLM-4.7": "synthetic",
    
    # OpenRouter (API key - free tier)
    "openrouter-stepfun-step-3.5-flash-free": "openrouter",
    "openrouter-arcee-ai-trinity-large-preview-free": "openrouter",
    
    # ZAI (API key)
    "zai-glm-4.6-coding": "zai",
    "zai-glm-4.6-api": "zai",
    "zai-glm-4.7-coding": "zai",
    "zai-glm-4.7-api": "zai",
}


# =============================================================================
# CREDENTIAL CHECKING FUNCTIONS
# =============================================================================

def _get_api_key(env_var: str) -> Optional[str]:
    """Get API key from config or environment."""
    try:
        from code_puppy.config import get_value
        
        # First check config (case-insensitive)
        config_value = get_value(env_var.lower())
        if config_value:
            return config_value
    except ImportError:
        pass
    
    # Fall back to environment variable
    return os.environ.get(env_var)


def _check_oauth_token(plugin_name: str) -> bool:
    """Check if OAuth token exists and is valid for a plugin.
    
    Returns True if:
    - Token file exists
    - Token has access_token field
    - Token is not expired OR has refresh_token for refresh
    """
    try:
        if plugin_name == "claude_code_oauth":
            from code_puppy.plugins.claude_code_oauth.config import get_token_storage_path
        elif plugin_name == "antigravity_oauth":
            from code_puppy.plugins.antigravity_oauth.config import get_token_storage_path
        elif plugin_name == "chatgpt_oauth":
            from code_puppy.plugins.chatgpt_oauth.config import get_token_storage_path
        else:
            logger.debug(f"Unknown OAuth plugin: {plugin_name}")
            return False
        
        token_path = get_token_storage_path()
        if not token_path.exists():
            logger.debug(f"OAuth token file not found: {token_path}")
            return False
        
        with open(token_path, "r") as f:
            token_data = json.load(f)
        
        # Check for access_token
        if not token_data.get("access_token"):
            logger.debug(f"No access_token in {token_path}")
            return False
        
        # Token exists and has access_token - consider valid
        # (refresh will happen automatically if expired)
        return True
        
    except ImportError:
        logger.debug(f"OAuth plugin not available: {plugin_name}")
        return False
    except json.JSONDecodeError:
        logger.debug(f"Invalid JSON in OAuth token file for {plugin_name}")
        return False
    except Exception as e:
        logger.debug(f"Error checking OAuth token for {plugin_name}: {e}")
        return False


def _get_api_key_multi(key_names: str | tuple) -> Optional[str]:
    """Get API key, trying multiple alternative names.
    
    Args:
        key_names: Single key name or tuple of alternative names to try
        
    Returns:
        The API key value if found, None otherwise
    """
    if isinstance(key_names, str):
        key_names = (key_names,)
    
    for key_name in key_names:
        value = _get_api_key(key_name)
        if value:
            return value
    
    return None


def has_valid_credentials(model_name: str) -> bool:
    """Check if a model has valid credentials (API key or OAuth token).
    
    Args:
        model_name: The model key from models.json
        
    Returns:
        True if credentials are available, False otherwise
    """
    provider = MODEL_TO_PROVIDER.get(model_name)
    
    if not provider:
        # Unknown model - try to infer from name pattern
        provider = _infer_provider_from_name(model_name)
        if not provider:
            logger.debug(f"Unknown provider for model: {model_name}")
            return False
    
    cred_info = PROVIDER_CREDENTIALS.get(provider)
    if not cred_info:
        logger.debug(f"Unknown credential info for provider: {provider}")
        return False
    
    cred_type, cred_key = cred_info
    
    if cred_type == CredentialType.API_KEY:
        api_key = _get_api_key_multi(cred_key)
        has_key = bool(api_key and len(api_key) > 5)  # Basic validation
        if not has_key:
            logger.debug(f"No API key for {model_name} ({cred_key})")
        return has_key
    
    elif cred_type == CredentialType.OAUTH:
        has_token = _check_oauth_token(cred_key)
        if not has_token:
            logger.debug(f"No OAuth token for {model_name} ({cred_key})")
        return has_token
    
    return False


def _infer_provider_from_name(model_name: str) -> Optional[str]:
    """Infer provider from model name patterns."""
    name_lower = model_name.lower()
    
    if name_lower.startswith("claude-code-"):
        return "claude_code"
    elif name_lower.startswith("antigravity-"):
        return "antigravity"
    elif name_lower.startswith("chatgpt-"):
        return "chatgpt"
    elif name_lower.startswith("synthetic-") or name_lower.startswith("hf:"):
        return "synthetic"
    elif name_lower.startswith("openrouter-"):
        return "openrouter"
    elif name_lower.startswith("zai-"):
        return "zai"
    elif "cerebras" in name_lower or "glm-4" in name_lower:
        return "cerebras"
    elif name_lower.startswith("gemini"):
        return "gemini"
    elif "gpt-" in name_lower or "openai" in name_lower:
        return "openai"
    elif "claude-" in name_lower or "anthropic" in name_lower:
        return "anthropic"
    
    return None


# =============================================================================
# FILTERED MODEL LISTS
# =============================================================================

_credential_cache: Dict[str, bool] = {}
_cache_valid = False


def invalidate_credential_cache():
    """Invalidate the credential cache (call after OAuth login/logout)."""
    global _credential_cache, _cache_valid
    _credential_cache.clear()
    _cache_valid = False
    logger.debug("Credential cache invalidated")


def get_available_models_with_credentials(model_list: List[str]) -> List[str]:
    """Filter a list of models to only those with valid credentials.
    
    Args:
        model_list: List of model names to filter
        
    Returns:
        Filtered list containing only models with valid credentials
    """
    global _credential_cache
    
    available = []
    for model in model_list:
        # Check cache first
        if model in _credential_cache:
            if _credential_cache[model]:
                available.append(model)
            continue
        
        # Check credentials and cache result
        has_creds = has_valid_credentials(model)
        _credential_cache[model] = has_creds
        
        if has_creds:
            available.append(model)
        else:
            logger.debug(f"Excluding {model} - no valid credentials")
    
    return available


def filter_workload_chain(workload_chain: List[str]) -> List[str]:
    """Filter a workload failover chain to only credentialed models.
    
    Args:
        workload_chain: Ordered list of models for a workload
        
    Returns:
        Filtered chain with only available models (order preserved)
    """
    return get_available_models_with_credentials(workload_chain)


def get_credential_status() -> Dict[str, Dict[str, bool]]:
    """Get credential status for all known providers.
    
    Returns:
        Dict mapping provider names to their credential availability
    """
    status = {}
    
    for provider, (cred_type, cred_key) in PROVIDER_CREDENTIALS.items():
        if cred_type == CredentialType.API_KEY:
            has_cred = bool(_get_api_key_multi(cred_key))
            # Show all alternative key names
            key_display = cred_key if isinstance(cred_key, str) else " | ".join(cred_key)
            status[provider] = {
                "type": "api_key",
                "key": key_display,
                "available": has_cred,
            }
        else:
            has_cred = _check_oauth_token(cred_key)
            status[provider] = {
                "type": "oauth",
                "plugin": cred_key,
                "available": has_cred,
            }
    
    return status


def get_models_by_availability() -> Tuple[List[str], List[str]]:
    """Get all known models split by credential availability.
    
    Returns:
        Tuple of (available_models, unavailable_models)
    """
    available = []
    unavailable = []
    
    for model in MODEL_TO_PROVIDER.keys():
        if has_valid_credentials(model):
            available.append(model)
        else:
            unavailable.append(model)
    
    return available, unavailable


# =============================================================================
# SINGLETON ACCESSOR
# =============================================================================

class CredentialChecker:
    """Singleton for credential availability checking."""
    
    _instance: Optional["CredentialChecker"] = None
    
    def __init__(self):
        self._cache: Dict[str, bool] = {}
    
    @classmethod
    def get_instance(cls) -> "CredentialChecker":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def has_credentials(self, model: str) -> bool:
        """Check if model has valid credentials (cached)."""
        if model not in self._cache:
            self._cache[model] = has_valid_credentials(model)
        return self._cache[model]
    
    def filter_models(self, models: List[str]) -> List[str]:
        """Filter models to only those with credentials."""
        return [m for m in models if self.has_credentials(m)]
    
    def invalidate_cache(self):
        """Clear the credential cache."""
        self._cache.clear()
        invalidate_credential_cache()
    
    def get_status_report(self) -> str:
        """Get a human-readable credential status report."""
        status = get_credential_status()
        lines = ["Credential Status:", "=" * 40]
        
        for provider, info in sorted(status.items()):
            symbol = "✅" if info["available"] else "❌"
            if info["type"] == "api_key":
                lines.append(f"  {symbol} {provider}: {info['key']}")
            else:
                lines.append(f"  {symbol} {provider}: OAuth ({info['plugin']})")
        
        return "\n".join(lines)


def get_credential_checker() -> CredentialChecker:
    """Get the singleton credential checker instance."""
    return CredentialChecker.get_instance()

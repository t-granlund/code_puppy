"""
Typed settings management using pydantic-settings.

This module provides strongly-typed configuration classes that replace the
legacy config.py approach with validated, environment-aware settings.

Features:
- Type-safe configuration with validation
- Automatic environment variable loading
- .env file support with proper precedence
- Nested settings for organization
- Computed properties and validators
- Secret handling for API keys

Usage:
    from code_puppy.settings import get_settings, get_api_settings
    
    settings = get_settings()
    print(settings.puppy_name)
    
    api = get_api_settings()
    if api.openai_api_key:
        # Use OpenAI
        pass
"""

from __future__ import annotations

import os
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, ClassVar, Optional

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# =============================================================================
# Enums for validated choices
# =============================================================================


class CompactionStrategy(str, Enum):
    """Strategy for message history compaction."""

    SUMMARIZATION = "summarization"
    TRUNCATION = "truncation"


class ReasoningEffort(str, Enum):
    """OpenAI reasoning effort levels."""

    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    XHIGH = "xhigh"


class Verbosity(str, Enum):
    """Model verbosity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SafetyPermissionLevel(str, Enum):
    """Safety permission levels for risky operations."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# Path Configuration
# =============================================================================


def _get_xdg_dir(env_var: str, fallback_subdir: str) -> Path:
    """Get XDG directory, defaulting to ~/.code_puppy if not set."""
    xdg_base = os.getenv(env_var)
    if xdg_base:
        return Path(xdg_base) / "code_puppy"
    return Path.home() / ".code_puppy"


class PathSettings(BaseSettings):
    """XDG-compliant path configuration."""

    model_config = SettingsConfigDict(
        env_prefix="CODE_PUPPY_",
        extra="ignore",
    )

    # Computed at runtime based on XDG environment variables
    @property
    def config_dir(self) -> Path:
        """XDG_CONFIG_HOME/code_puppy or ~/.code_puppy"""
        return _get_xdg_dir("XDG_CONFIG_HOME", ".config")

    @property
    def data_dir(self) -> Path:
        """XDG_DATA_HOME/code_puppy or ~/.code_puppy"""
        return _get_xdg_dir("XDG_DATA_HOME", ".local/share")

    @property
    def cache_dir(self) -> Path:
        """XDG_CACHE_HOME/code_puppy or ~/.code_puppy"""
        return _get_xdg_dir("XDG_CACHE_HOME", ".cache")

    @property
    def state_dir(self) -> Path:
        """XDG_STATE_HOME/code_puppy or ~/.code_puppy"""
        return _get_xdg_dir("XDG_STATE_HOME", ".local/state")

    # File paths
    @property
    def config_file(self) -> Path:
        return self.config_dir / "puppy.cfg"

    @property
    def mcp_servers_file(self) -> Path:
        return self.config_dir / "mcp_servers.json"

    @property
    def models_file(self) -> Path:
        return self.data_dir / "models.json"

    @property
    def extra_models_file(self) -> Path:
        return self.data_dir / "extra_models.json"

    @property
    def agents_dir(self) -> Path:
        return self.data_dir / "agents"

    @property
    def autosave_dir(self) -> Path:
        return self.cache_dir / "autosaves"

    @property
    def command_history_file(self) -> Path:
        return self.state_dir / "command_history.txt"

    def ensure_directories(self) -> None:
        """Create all necessary directories with secure permissions."""
        for directory in [self.config_dir, self.data_dir, self.cache_dir, self.state_dir]:
            directory.mkdir(parents=True, exist_ok=True, mode=0o700)


# =============================================================================
# API Key Settings (Secrets)
# =============================================================================


class APISettings(BaseSettings):
    """API keys and endpoints for LLM providers.

    These are loaded from environment variables with automatic .env support.
    SecretStr prevents accidental logging of sensitive values.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        # Don't override env vars that are already set
        env_nested_delimiter="__",
    )

    # OpenAI
    openai_api_key: Optional[SecretStr] = Field(default=None, alias="OPENAI_API_KEY")

    # Anthropic
    anthropic_api_key: Optional[SecretStr] = Field(default=None, alias="ANTHROPIC_API_KEY")

    # Google Gemini
    gemini_api_key: Optional[SecretStr] = Field(default=None, alias="GEMINI_API_KEY")

    # Cerebras
    cerebras_api_key: Optional[SecretStr] = Field(default=None, alias="CEREBRAS_API_KEY")

    # Synthetic
    syn_api_key: Optional[SecretStr] = Field(default=None, alias="SYN_API_KEY")

    # Azure OpenAI
    azure_openai_api_key: Optional[SecretStr] = Field(default=None, alias="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: Optional[str] = Field(default=None, alias="AZURE_OPENAI_ENDPOINT")

    # OpenRouter
    openrouter_api_key: Optional[SecretStr] = Field(default=None, alias="OPENROUTER_API_KEY")

    # ZAI
    zai_api_key: Optional[SecretStr] = Field(default=None, alias="ZAI_API_KEY")

    # Logfire
    logfire_token: Optional[SecretStr] = Field(default=None, alias="LOGFIRE_TOKEN")

    def get_key_value(self, key_name: str) -> Optional[str]:
        """Get the raw string value of an API key by name.

        Args:
            key_name: The environment variable name (e.g., 'OPENAI_API_KEY')

        Returns:
            The key value as a string, or None if not set.
        """
        # Map env var names to attribute names
        attr_map = {
            "OPENAI_API_KEY": "openai_api_key",
            "ANTHROPIC_API_KEY": "anthropic_api_key",
            "GEMINI_API_KEY": "gemini_api_key",
            "CEREBRAS_API_KEY": "cerebras_api_key",
            "SYN_API_KEY": "syn_api_key",
            "AZURE_OPENAI_API_KEY": "azure_openai_api_key",
            "AZURE_OPENAI_ENDPOINT": "azure_openai_endpoint",
            "OPENROUTER_API_KEY": "openrouter_api_key",
            "ZAI_API_KEY": "zai_api_key",
            "LOGFIRE_TOKEN": "logfire_token",
        }
        attr = attr_map.get(key_name)
        if attr:
            value = getattr(self, attr, None)
            if isinstance(value, SecretStr):
                return value.get_secret_value()
            return value
        return None

    def has_provider(self, provider: str) -> bool:
        """Check if credentials exist for a provider.

        Args:
            provider: Provider name ('openai', 'anthropic', 'gemini', etc.)

        Returns:
            True if API key is configured for the provider.
        """
        provider_keys = {
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
            "gemini": self.gemini_api_key,
            "cerebras": self.cerebras_api_key,
            "azure": self.azure_openai_api_key,
            "openrouter": self.openrouter_api_key,
            "zai": self.zai_api_key,
        }
        key = provider_keys.get(provider.lower())
        return key is not None and key.get_secret_value() != "" if isinstance(key, SecretStr) else key is not None

    def export_to_environment(self) -> None:
        """Export all configured API keys to environment variables.

        This is useful for libraries that read directly from os.environ.
        """
        exports = [
            ("OPENAI_API_KEY", self.openai_api_key),
            ("ANTHROPIC_API_KEY", self.anthropic_api_key),
            ("GEMINI_API_KEY", self.gemini_api_key),
            ("CEREBRAS_API_KEY", self.cerebras_api_key),
            ("SYN_API_KEY", self.syn_api_key),
            ("AZURE_OPENAI_API_KEY", self.azure_openai_api_key),
            ("AZURE_OPENAI_ENDPOINT", self.azure_openai_endpoint),
            ("OPENROUTER_API_KEY", self.openrouter_api_key),
            ("ZAI_API_KEY", self.zai_api_key),
            ("LOGFIRE_TOKEN", self.logfire_token),
        ]
        for env_name, value in exports:
            if value is not None:
                if isinstance(value, SecretStr):
                    os.environ[env_name] = value.get_secret_value()
                else:
                    os.environ[env_name] = value


# =============================================================================
# Model Settings
# =============================================================================


class ModelSettings(BaseSettings):
    """Model-related configuration."""

    model_config = SettingsConfigDict(
        env_prefix="CODE_PUPPY_",
        extra="ignore",
    )

    # Current model selection
    model: str = Field(default="gpt-5", description="Default model to use")

    # Temperature and generation settings
    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Model temperature (0.0-2.0). None uses model default.",
    )

    # OpenAI-specific settings
    openai_reasoning_effort: ReasoningEffort = Field(
        default=ReasoningEffort.MEDIUM,
        description="OpenAI reasoning effort level",
    )
    openai_verbosity: Verbosity = Field(
        default=Verbosity.MEDIUM,
        description="OpenAI response verbosity",
    )

    # Streaming
    enable_streaming: bool = Field(
        default=True,
        description="Enable streaming responses (SSE)",
    )

    # HTTP/2
    http2: bool = Field(
        default=False,
        description="Enable HTTP/2 for API calls",
    )


# =============================================================================
# Agent Settings
# =============================================================================


class AgentSettings(BaseSettings):
    """Agent behavior and limits configuration."""

    model_config = SettingsConfigDict(
        env_prefix="CODE_PUPPY_",
        extra="ignore",
    )

    # Identity
    puppy_name: str = Field(default="Puppy", description="The AI assistant's name")
    owner_name: str = Field(default="Master", description="The user's name")

    # Agent selection
    default_agent: str = Field(
        default="code-puppy",
        description="Default agent to use at startup",
    )

    # Limits
    message_limit: int = Field(
        default=1000,
        ge=1,
        description="Maximum agent steps/requests per session",
    )
    allow_recursion: bool = Field(
        default=True,
        description="Allow recursive agent invocations",
    )

    # Feature flags
    enable_pack_agents: bool = Field(
        default=False,
        description="Enable pack agents (bloodhound, husky, etc.)",
    )
    enable_universal_constructor: bool = Field(
        default=True,
        description="Allow agents to dynamically create tools",
    )
    enable_dbos: bool = Field(
        default=False,
        description="Enable DBOS for durable execution",
    )
    disable_mcp: bool = Field(
        default=False,
        description="Disable MCP server loading",
    )


# =============================================================================
# Compaction Settings
# =============================================================================


class CompactionSettings(BaseSettings):
    """Message history compaction configuration."""

    model_config = SettingsConfigDict(
        env_prefix="CODE_PUPPY_",
        extra="ignore",
    )

    strategy: CompactionStrategy = Field(
        default=CompactionStrategy.TRUNCATION,
        description="Compaction strategy (summarization or truncation)",
    )

    protected_token_count: int = Field(
        default=50000,
        ge=1000,
        description="Number of recent tokens protected from compaction",
    )

    compaction_threshold: float = Field(
        default=0.85,
        ge=0.5,
        le=0.95,
        description="Context utilization threshold triggering compaction (0.5-0.95)",
    )


# =============================================================================
# UI/Display Settings
# =============================================================================


class DisplaySettings(BaseSettings):
    """UI and display configuration."""

    model_config = SettingsConfigDict(
        env_prefix="CODE_PUPPY_",
        extra="ignore",
    )

    # Mode flags
    yolo_mode: bool = Field(
        default=True,
        description="Enable YOLO mode (auto-approve dangerous operations)",
    )

    # Verbosity
    subagent_verbose: bool = Field(
        default=False,
        description="Enable verbose output for sub-agents",
    )
    grep_output_verbose: bool = Field(
        default=False,
        description="Show full grep output with line numbers",
    )

    # Message suppression
    suppress_thinking_messages: bool = Field(
        default=False,
        description="Hide agent reasoning/thinking messages",
    )
    suppress_informational_messages: bool = Field(
        default=False,
        description="Hide info/success/warning messages",
    )

    # Diff display
    diff_context_lines: int = Field(
        default=6,
        ge=0,
        le=50,
        description="Lines of context to show in diffs",
    )
    highlight_addition_color: str = Field(
        default="#0b1f0b",
        description="Color for diff additions (hex or Rich color name)",
    )
    highlight_deletion_color: str = Field(
        default="#390e1a",
        description="Color for diff deletions (hex or Rich color name)",
    )

    # Session management
    auto_save_session: bool = Field(
        default=True,
        description="Automatically save sessions",
    )
    max_saved_sessions: int = Field(
        default=20,
        ge=0,
        description="Maximum number of saved sessions to keep (0=unlimited)",
    )


# =============================================================================
# Safety Settings
# =============================================================================


class SafetySettings(BaseSettings):
    """Safety and permission configuration."""

    model_config = SettingsConfigDict(
        env_prefix="CODE_PUPPY_",
        extra="ignore",
    )

    safety_permission_level: SafetyPermissionLevel = Field(
        default=SafetyPermissionLevel.MEDIUM,
        description="Risk threshold for requiring confirmation",
    )


# =============================================================================
# Frontend Emitter Settings
# =============================================================================


class FrontendSettings(BaseSettings):
    """Frontend emitter configuration for web UI integration."""

    model_config = SettingsConfigDict(
        env_prefix="CODE_PUPPY_FRONTEND_",
        extra="ignore",
    )

    enabled: bool = Field(
        default=True,
        alias="frontend_emitter_enabled",
        description="Enable frontend event emitter",
    )
    max_recent_events: int = Field(
        default=100,
        alias="frontend_emitter_max_recent_events",
        description="Maximum recent events to buffer",
    )
    queue_size: int = Field(
        default=100,
        alias="frontend_emitter_queue_size",
        description="Maximum subscriber queue size",
    )


# =============================================================================
# Banner Colors
# =============================================================================

DEFAULT_BANNER_COLORS: dict[str, str] = {
    "thinking": "deep_sky_blue4",
    "agent_response": "medium_purple4",
    "shell_command": "dark_orange3",
    "read_file": "steel_blue",
    "edit_file": "dark_goldenrod",
    "grep": "grey37",
    "directory_listing": "dodger_blue2",
    "agent_reasoning": "dark_violet",
    "invoke_agent": "deep_pink4",
    "subagent_response": "sea_green3",
    "list_agents": "dark_slate_gray3",
    "terminal_tool": "dark_goldenrod",
}


class BannerColors(BaseSettings):
    """Banner color configuration with defaults."""

    model_config = SettingsConfigDict(
        env_prefix="CODE_PUPPY_BANNER_",
        extra="ignore",
    )

    thinking: str = Field(default="deep_sky_blue4")
    agent_response: str = Field(default="medium_purple4")
    shell_command: str = Field(default="dark_orange3")
    read_file: str = Field(default="steel_blue")
    edit_file: str = Field(default="dark_goldenrod")
    grep: str = Field(default="grey37")
    directory_listing: str = Field(default="dodger_blue2")
    agent_reasoning: str = Field(default="dark_violet")
    invoke_agent: str = Field(default="deep_pink4")
    subagent_response: str = Field(default="sea_green3")
    list_agents: str = Field(default="dark_slate_gray3")
    terminal_tool: str = Field(default="dark_goldenrod")

    def get_color(self, banner_name: str) -> str:
        """Get color for a banner by name."""
        return getattr(self, banner_name, DEFAULT_BANNER_COLORS.get(banner_name, "blue"))

    def as_dict(self) -> dict[str, str]:
        """Get all banner colors as a dictionary."""
        return {name: self.get_color(name) for name in DEFAULT_BANNER_COLORS}


# =============================================================================
# Master Settings Class
# =============================================================================


class Settings(BaseSettings):
    """Master settings combining all configuration sections.

    This is the main entry point for accessing typed configuration.
    Uses composition to organize settings into logical groups.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="CODE_PUPPY_",
        extra="ignore",
        case_sensitive=False,
    )

    # Nested settings
    paths: PathSettings = Field(default_factory=PathSettings)
    api: APISettings = Field(default_factory=APISettings)
    model: ModelSettings = Field(default_factory=ModelSettings)
    agent: AgentSettings = Field(default_factory=AgentSettings)
    compaction: CompactionSettings = Field(default_factory=CompactionSettings)
    display: DisplaySettings = Field(default_factory=DisplaySettings)
    safety: SafetySettings = Field(default_factory=SafetySettings)
    frontend: FrontendSettings = Field(default_factory=FrontendSettings)
    banner_colors: BannerColors = Field(default_factory=BannerColors)

    # Convenience properties for common access patterns
    @property
    def puppy_name(self) -> str:
        return self.agent.puppy_name

    @property
    def owner_name(self) -> str:
        return self.agent.owner_name

    @property
    def yolo_mode(self) -> bool:
        return self.display.yolo_mode

    @property
    def current_model(self) -> str:
        return self.model.model

    def ensure_directories(self) -> None:
        """Create all necessary directories."""
        self.paths.ensure_directories()


# =============================================================================
# Cached Singleton Accessors
# =============================================================================


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get the cached settings singleton.

    The settings are loaded once and cached for the process lifetime.
    To reload, call clear_settings_cache() first.

    Returns:
        The Settings instance with all configuration loaded.
    """
    return Settings()


@lru_cache(maxsize=1)
def get_api_settings() -> APISettings:
    """Get API settings (cached).

    Provides direct access to API keys without loading full settings.
    """
    return APISettings()


@lru_cache(maxsize=1)
def get_path_settings() -> PathSettings:
    """Get path settings (cached)."""
    return PathSettings()


def clear_settings_cache() -> None:
    """Clear all cached settings instances.

    Call this if environment variables or .env files have changed
    and you need to reload configuration.
    """
    get_settings.cache_clear()
    get_api_settings.cache_clear()
    get_path_settings.cache_clear()


# =============================================================================
# Integration Helpers
# =============================================================================


def settings_to_env_dict(settings: Settings) -> dict[str, str]:
    """Convert settings to a dictionary suitable for environment export.

    This is useful for subprocess spawning or configuration export.
    """
    result = {}

    # API keys (only if set)
    if settings.api.openai_api_key:
        result["OPENAI_API_KEY"] = settings.api.openai_api_key.get_secret_value()
    if settings.api.anthropic_api_key:
        result["ANTHROPIC_API_KEY"] = settings.api.anthropic_api_key.get_secret_value()
    if settings.api.gemini_api_key:
        result["GEMINI_API_KEY"] = settings.api.gemini_api_key.get_secret_value()

    # Model settings
    result["CODE_PUPPY_MODEL"] = settings.model.model
    if settings.model.temperature is not None:
        result["CODE_PUPPY_TEMPERATURE"] = str(settings.model.temperature)

    # Agent settings
    result["CODE_PUPPY_PUPPY_NAME"] = settings.agent.puppy_name
    result["CODE_PUPPY_OWNER_NAME"] = settings.agent.owner_name

    return result


def initialize_from_settings() -> Settings:
    """Initialize the application using pydantic-settings.

    This creates directories, exports API keys to environment,
    and returns the loaded settings.

    Call this early in application startup.
    """
    settings = get_settings()
    settings.ensure_directories()
    settings.api.export_to_environment()
    return settings


# =============================================================================
# Backward Compatibility Bridge
# =============================================================================


def get_value_from_settings(key: str) -> Optional[str]:
    """Bridge function to get config values from new settings system.

    This allows gradual migration from config.py to settings.py.
    Maps old config keys to new settings attributes.

    Args:
        key: The old config key name

    Returns:
        The value as a string, or None if not found/mapped.
    """
    settings = get_settings()

    # Map old keys to new settings
    key_mapping = {
        "puppy_name": lambda: settings.agent.puppy_name,
        "owner_name": lambda: settings.agent.owner_name,
        "model": lambda: settings.model.model,
        "temperature": lambda: str(settings.model.temperature) if settings.model.temperature else None,
        "yolo_mode": lambda: str(settings.display.yolo_mode).lower(),
        "enable_streaming": lambda: str(settings.model.enable_streaming).lower(),
        "http2": lambda: str(settings.model.http2).lower(),
        "compaction_strategy": lambda: settings.compaction.strategy.value,
        "protected_token_count": lambda: str(settings.compaction.protected_token_count),
        "compaction_threshold": lambda: str(settings.compaction.compaction_threshold),
        "message_limit": lambda: str(settings.agent.message_limit),
        "allow_recursion": lambda: str(settings.agent.allow_recursion).lower(),
        "enable_dbos": lambda: str(settings.agent.enable_dbos).lower(),
        "enable_pack_agents": lambda: str(settings.agent.enable_pack_agents).lower(),
        "enable_universal_constructor": lambda: str(settings.agent.enable_universal_constructor).lower(),
        "disable_mcp": lambda: str(settings.agent.disable_mcp).lower(),
        "default_agent": lambda: settings.agent.default_agent,
        "auto_save_session": lambda: str(settings.display.auto_save_session).lower(),
        "max_saved_sessions": lambda: str(settings.display.max_saved_sessions),
        "diff_context_lines": lambda: str(settings.display.diff_context_lines),
        "subagent_verbose": lambda: str(settings.display.subagent_verbose).lower(),
        "grep_output_verbose": lambda: str(settings.display.grep_output_verbose).lower(),
        "suppress_thinking_messages": lambda: str(settings.display.suppress_thinking_messages).lower(),
        "suppress_informational_messages": lambda: str(settings.display.suppress_informational_messages).lower(),
        "safety_permission_level": lambda: settings.safety.safety_permission_level.value,
        "openai_reasoning_effort": lambda: settings.model.openai_reasoning_effort.value,
        "openai_verbosity": lambda: settings.model.openai_verbosity.value,
        "frontend_emitter_enabled": lambda: str(settings.frontend.enabled).lower(),
        "frontend_emitter_max_recent_events": lambda: str(settings.frontend.max_recent_events),
        "frontend_emitter_queue_size": lambda: str(settings.frontend.queue_size),
        "highlight_addition_color": lambda: settings.display.highlight_addition_color,
        "highlight_deletion_color": lambda: settings.display.highlight_deletion_color,
    }

    # Handle banner colors
    if key.startswith("banner_color_"):
        banner_name = key[len("banner_color_") :]
        return settings.banner_colors.get_color(banner_name)

    getter = key_mapping.get(key)
    if getter:
        return getter()

    return None

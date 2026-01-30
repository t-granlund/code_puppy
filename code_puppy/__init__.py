import importlib.metadata

# Biscuit was here! 🐶
try:
    _detected_version = importlib.metadata.version("code-puppy")
    # Ensure we never end up with None or empty string
    __version__ = _detected_version if _detected_version else "0.0.0-dev"
except Exception:
    # Fallback for dev environments where metadata might not be available
    __version__ = "0.0.0-dev"

# Export typed settings for modern usage
from code_puppy.settings import (
    Settings,
    APISettings,
    PathSettings,
    ModelSettings,
    AgentSettings,
    CompactionSettings,
    DisplaySettings,
    SafetySettings,
    BannerColors,
    get_settings,
    get_api_settings,
    get_path_settings,
    clear_settings_cache,
    initialize_from_settings,
    # Enums
    CompactionStrategy,
    ReasoningEffort,
    Verbosity,
    SafetyPermissionLevel,
)

__all__ = [
    "__version__",
    # Settings classes
    "Settings",
    "APISettings",
    "PathSettings",
    "ModelSettings",
    "AgentSettings",
    "CompactionSettings",
    "DisplaySettings",
    "SafetySettings",
    "BannerColors",
    # Accessors
    "get_settings",
    "get_api_settings",
    "get_path_settings",
    "clear_settings_cache",
    "initialize_from_settings",
    # Enums
    "CompactionStrategy",
    "ReasoningEffort",
    "Verbosity",
    "SafetyPermissionLevel",
]

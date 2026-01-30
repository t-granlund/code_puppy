# Pydantic Settings Integration

This document describes the modern, type-safe configuration system using `pydantic-settings`.

## Overview

Code Puppy now supports a strongly-typed configuration system alongside the legacy `config.py`. The new system provides:

- **Type-safe configuration** with Pydantic validation
- **Automatic environment variable loading**
- **`.env` file support** with proper precedence
- **Nested settings** for logical organization
- **SecretStr** for secure API key handling
- **Computed properties** and validators
- **Full backward compatibility** with existing config

## Quick Start

```python
from code_puppy import get_settings, get_api_settings

# Get all settings
settings = get_settings()
print(settings.puppy_name)          # "Puppy"
print(settings.current_model)       # "gpt-5"
print(settings.yolo_mode)           # True

# Access nested settings
print(settings.model.temperature)   # None (use model default)
print(settings.agent.message_limit) # 1000
print(settings.compaction.strategy) # CompactionStrategy.TRUNCATION

# Get API keys (secrets are protected)
api = get_api_settings()
if api.has_provider("openai"):
    key = api.openai_api_key.get_secret_value()
```

## Settings Classes

### PathSettings

XDG-compliant path configuration:

```python
from code_puppy import get_path_settings

paths = get_path_settings()
print(paths.config_dir)      # ~/.code_puppy or $XDG_CONFIG_HOME/code_puppy
print(paths.data_dir)        # ~/.code_puppy or $XDG_DATA_HOME/code_puppy
print(paths.cache_dir)       # ~/.code_puppy or $XDG_CACHE_HOME/code_puppy
print(paths.config_file)     # ~/.code_puppy/puppy.cfg
print(paths.models_file)     # ~/.code_puppy/models.json
```

### APISettings

Secure API key management:

```python
from code_puppy import get_api_settings

api = get_api_settings()

# Check if provider is configured
if api.has_provider("openai"):
    # Get the actual key value (SecretStr protection)
    key = api.openai_api_key.get_secret_value()
    
# Supported providers:
# - openai_api_key (OPENAI_API_KEY)
# - anthropic_api_key (ANTHROPIC_API_KEY)
# - gemini_api_key (GEMINI_API_KEY)
# - cerebras_api_key (CEREBRAS_API_KEY)
# - azure_openai_api_key (AZURE_OPENAI_API_KEY)
# - openrouter_api_key (OPENROUTER_API_KEY)
# - logfire_token (LOGFIRE_TOKEN)

# Export all keys to environment (for external libraries)
api.export_to_environment()
```

### ModelSettings

Model and generation configuration:

```python
from code_puppy import get_settings, ReasoningEffort, Verbosity

settings = get_settings()
model = settings.model

print(model.model)                    # "gpt-5"
print(model.temperature)              # None or 0.0-2.0
print(model.enable_streaming)         # True
print(model.http2)                    # False
print(model.openai_reasoning_effort)  # ReasoningEffort.MEDIUM
print(model.openai_verbosity)         # Verbosity.MEDIUM
```

### AgentSettings

Agent behavior configuration:

```python
settings = get_settings()
agent = settings.agent

print(agent.puppy_name)                    # "Puppy"
print(agent.owner_name)                    # "Master"
print(agent.default_agent)                 # "code-puppy"
print(agent.message_limit)                 # 1000
print(agent.allow_recursion)               # True
print(agent.enable_pack_agents)            # False
print(agent.enable_universal_constructor)  # True
print(agent.enable_dbos)                   # False
```

### CompactionSettings

Message history management:

```python
from code_puppy import get_settings, CompactionStrategy

settings = get_settings()
compaction = settings.compaction

print(compaction.strategy)             # CompactionStrategy.TRUNCATION
print(compaction.protected_token_count) # 50000
print(compaction.compaction_threshold)  # 0.85 (85%)
```

### DisplaySettings

UI and display configuration:

```python
settings = get_settings()
display = settings.display

print(display.yolo_mode)                       # True
print(display.diff_context_lines)              # 6
print(display.auto_save_session)               # True
print(display.suppress_thinking_messages)      # False
print(display.highlight_addition_color)        # "#0b1f0b"
```

### BannerColors

Banner color customization:

```python
settings = get_settings()
colors = settings.banner_colors

print(colors.thinking)         # "deep_sky_blue4"
print(colors.agent_response)   # "medium_purple4"
print(colors.shell_command)    # "dark_orange3"

# Get all as dict
all_colors = colors.as_dict()
```

## Environment Variables

Settings can be configured via environment variables with the `CODE_PUPPY_` prefix:

```bash
# Model settings
export CODE_PUPPY_MODEL=claude-4-0-sonnet
export CODE_PUPPY_TEMPERATURE=0.7
export CODE_PUPPY_ENABLE_STREAMING=true

# Agent settings
export CODE_PUPPY_PUPPY_NAME="Biscuit"
export CODE_PUPPY_MESSAGE_LIMIT=500

# API keys (no prefix)
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
```

## .env File Support

Create a `.env` file in your project root:

```env
# .env file
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
CODE_PUPPY_MODEL=gpt-4.1
CODE_PUPPY_TEMPERATURE=0.5
```

The loading priority is:
1. **.env file** (highest priority)
2. **Environment variables**
3. **Default values**

## Enums

Type-safe enum values for configuration:

```python
from code_puppy import (
    CompactionStrategy,
    ReasoningEffort,
    Verbosity,
    SafetyPermissionLevel,
)

# CompactionStrategy
CompactionStrategy.SUMMARIZATION  # "summarization"
CompactionStrategy.TRUNCATION     # "truncation"

# ReasoningEffort (OpenAI)
ReasoningEffort.MINIMAL  # "minimal"
ReasoningEffort.LOW      # "low"
ReasoningEffort.MEDIUM   # "medium"
ReasoningEffort.HIGH     # "high"
ReasoningEffort.XHIGH    # "xhigh"

# Verbosity
Verbosity.LOW     # "low"
Verbosity.MEDIUM  # "medium"
Verbosity.HIGH    # "high"

# SafetyPermissionLevel
SafetyPermissionLevel.NONE      # "none"
SafetyPermissionLevel.LOW       # "low"
SafetyPermissionLevel.MEDIUM    # "medium"
SafetyPermissionLevel.HIGH      # "high"
SafetyPermissionLevel.CRITICAL  # "critical"
```

## Caching and Reloading

Settings are cached for performance:

```python
from code_puppy import get_settings, clear_settings_cache

# First call loads and caches
settings1 = get_settings()

# Subsequent calls return cached instance
settings2 = get_settings()
assert settings1 is settings2

# Clear cache to reload (e.g., after .env changes)
clear_settings_cache()
settings3 = get_settings()  # Fresh load
```

## Initialization

For application startup:

```python
from code_puppy import initialize_from_settings

# Creates directories, exports API keys, returns settings
settings = initialize_from_settings()
```

## Backward Compatibility

The new settings system works alongside the existing `config.py`:

```python
from code_puppy.settings import get_value_from_settings

# Maps old config keys to new settings
value = get_value_from_settings("yolo_mode")  # "true"
value = get_value_from_settings("model")       # "gpt-5"
value = get_value_from_settings("banner_color_thinking")  # "deep_sky_blue4"
```

## Validation

Settings are validated at load time:

```python
from code_puppy.settings import ModelSettings

# Valid
settings = ModelSettings(temperature=1.5)

# Invalid - raises ValidationError
settings = ModelSettings(temperature=3.0)  # Must be 0.0-2.0
settings = ModelSettings(temperature=-1.0) # Must be >= 0.0
```

## Secret Protection

API keys use `SecretStr` to prevent accidental logging:

```python
api = get_api_settings()

# Won't expose the actual key
print(api.openai_api_key)  # SecretStr('**********')
print(repr(api.openai_api_key))  # SecretStr('**********')

# Explicit extraction required
actual_key = api.openai_api_key.get_secret_value()
```

## Migration Guide

To migrate from `config.py` to `settings.py`:

### Before (config.py)
```python
from code_puppy.config import (
    get_puppy_name,
    get_global_model_name,
    get_yolo_mode,
    get_temperature,
)

name = get_puppy_name()
model = get_global_model_name()
yolo = get_yolo_mode()
temp = get_temperature()
```

### After (settings.py)
```python
from code_puppy import get_settings

settings = get_settings()
name = settings.puppy_name
model = settings.current_model
yolo = settings.yolo_mode
temp = settings.model.temperature
```

## Best Practices

1. **Use typed settings** for new code
2. **Access via cached accessors** (`get_settings()`, not `Settings()`)
3. **Clear cache** after modifying environment
4. **Use enums** for constrained values
5. **Don't log secrets** - use `SecretStr.get_secret_value()` only when needed

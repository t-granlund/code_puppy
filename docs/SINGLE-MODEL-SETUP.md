# Single-Model Setup Guide

Code Puppy supports flexible model configurations, from sophisticated multi-model failover chains to simple single-model setups. This guide covers how to configure a single model for users who don't need or want failover complexity.

## Quick Start: Single Model

If you only have one API key (e.g., just OpenAI or just Anthropic), Code Puppy will automatically use that model. No failover configuration needed.

### 1. Set Your Model

```bash
# Interactive setup
puppy config set model <your-preferred-model>

# Or use the /model command in a session
/model openai-gpt-4o
```

### 2. Provide Your API Key

Set the appropriate environment variable for your model:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Google AI Studio
export GOOGLE_API_KEY="AI..."

# GitHub Models (free with GitHub account!)
# Uses `gh auth token` automatically - just run:
gh auth login
```

That's it! Code Puppy will use your single model for all operations.

## Local Project Configuration

You can have per-project model settings by creating a `.code_puppy.cfg` file in your project directory:

```ini
[code_puppy]
model = openai-gpt-4o
yolo_mode = false
```

This file takes priority over your global `~/.code_puppy/puppy.cfg` configuration, allowing different models for different projects.

### Priority Order

1. **Local `.code_puppy.cfg`** - Project-specific settings
2. **Global `~/.code_puppy/puppy.cfg`** - User-wide defaults
3. **Environment variables** - `.env` file or shell exports
4. **Built-in defaults** - Fallback model from models.json

## Available Models

View all configured models:

```bash
puppy models list
# or in a session:
/models
```

### GitHub Models (Recommended for Getting Started)

If you have a GitHub account, you can use GitHub Models for **free** (rate-limited):

```bash
# Authenticate with GitHub
gh auth login

# Set a GitHub model
puppy config set model github-gpt-4o
```

Available GitHub Models:
- `github-gpt-4.1` - Latest GPT-4.1
- `github-gpt-4o` - GPT-4o multimodal
- `github-grok-3` - xAI's Grok 3
- `github-deepseek-r1` - DeepSeek R1 reasoning

See [GitHub Models Integration](GITHUB-MODELS-INTEGRATION.md) for full details.

## How Failover Works (Optional)

If you have multiple API keys configured, Code Puppy automatically builds failover chains. When one model hits rate limits, it seamlessly switches to the next available model.

**With single model**: If rate limited, you'll see a message asking you to wait. No automatic switching occurs.

**With multiple models**: Rate limits are handled transparently by switching to alternate providers.

## Troubleshooting

### "No model configured"

Run the setup wizard:
```bash
puppy config wizard
```

### Model not found

Check your model name matches one in `models.json`:
```bash
puppy models list
```

### API key not working

Ensure your environment variable is set:
```bash
echo $OPENAI_API_KEY  # Should show your key
```

## Example Configurations

### OpenAI Only
```ini
[code_puppy]
model = openai-gpt-4o
```

### Anthropic Only
```ini
[code_puppy]
model = claude-4-0-sonnet
```

### GitHub Models (Free)
```ini
[code_puppy]
model = github-gpt-4o
```

### Local Ollama
```ini
[code_puppy]
model = ollama-qwen2.5-coder
```

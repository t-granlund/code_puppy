# Code Puppy Examples 🐶

This directory contains reference examples and starter code for building with Code Puppy.

## Available Examples

### `claude_oauth_custom_tool_example.py`

Comprehensive reference for using Claude Code OAuth models in custom tools and scripts.

**What it demonstrates:**
- ✅ Simple one-off messages
- ✅ Real-time streaming responses
- ✅ Using both Opus 4-6 and Sonnet 4-6 models
- ✅ Extended thinking with effort parameters
- ✅ Proper error handling patterns
- ✅ Multi-turn conversations with message history
- ✅ Advanced streaming event handling

**Prerequisites:**
1. Authenticate via Code Puppy: `/claude-code-auth`
2. Install the Anthropic SDK: `pip install anthropic`

**Usage:**
```bash
# Run all examples
python examples/claude_oauth_custom_tool_example.py

# Or import specific functions in your code
from examples.claude_oauth_custom_tool_example import create_client, example_streaming

client = create_client()
example_streaming(client)
```

**Copy-paste ready snippets:**

```python
# Quick single message
from examples.claude_oauth_custom_tool_example import create_client

client = create_client()
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.content[0].text)
```

```python
# Streaming with Opus
with client.messages.stream(
    model="claude-opus-4-6",
    max_tokens=2048,
    messages=[{"role": "user", "content": "Write a story"}],
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

```python
# Extended thinking for complex reasoning
response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=4096,
    thinking={"type": "enabled", "budget_tokens": 2000},
    messages=[{"role": "user", "content": "Solve this logic puzzle..."}],
)
```

---

## Contributing Examples

Got a cool Code Puppy integration or pattern? Add it here!

**Guidelines:**
- Keep examples focused and self-contained
- Include clear comments and type hints
- Demonstrate best practices (error handling, DRY, etc.)
- Files under 600 lines (Richard's rule!)
- Follow the Zen of Python

**Good example ideas:**
- MCP server integration patterns
- Custom plugin templates
- Agent workflows
- Browser automation examples
- API integration patterns

---

*Woof! 🐶 Need help? Open an issue or ask Richard in Code Puppy.*

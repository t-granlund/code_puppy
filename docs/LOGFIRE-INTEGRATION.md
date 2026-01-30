# Logfire + genai-prices Integration

Code Puppy now has **two-layer observability and cost tracking**:

## 1. Logfire Instrumentation (Capturing Telemetry)

**What it does:** Instruments your running code to capture traces, spans, and metrics in real-time.

**Auto-configured in:** `code_puppy/cli_runner.py`

```python
import logfire
logfire.configure(
    service_name="code-puppy",
    send_to_logfire=False,  # Local-only by default
)
logfire.instrument_pydantic_ai()  # Traces all agent runs
logfire.instrument_mcp()           # Traces MCP tool calls
```

**To enable cloud sync:**
1. Get a Logfire write token: https://logfire.pydantic.dev/
2. Set environment variable: `export LOGFIRE_TOKEN=your_token`
3. Change `send_to_logfire=True` in cli_runner.py

**What you'll see:**
- Every agent run with timing
- Tool calls and their arguments
- Model requests with token usage
- MCP server interactions
- Nested spans showing execution flow

## 2. Logfire-MCP Server (Querying Telemetry)

**What it does:** MCP server that lets Code Puppy query its own historical telemetry data.

**Configured in:** `~/.config/code_puppy/mcp_servers.json`

**To enable:**
1. Get a Logfire **read** token: https://logfire.pydantic.dev/-/redirect/latest-project/settings/read-tokens
2. Edit `~/.config/code_puppy/mcp_servers.json`:
   ```json
   {
     "mcpServers": {
       "logfire": {
         "command": "uvx",
         "args": ["logfire-mcp@latest"],
         "env": {
           "LOGFIRE_READ_TOKEN": "pylf_v1_us_YOUR_TOKEN_HERE"
         },
         "enabled": true
       }
     }
   }
   ```
3. Restart Code Puppy

**Available MCP tools:**
- `find_exceptions_in_file` - Find recent exceptions in a specific file
- `arbitrary_query` - Run SQL queries on traces/metrics
- `logfire_link` - Generate link to view trace in Logfire UI
- `schema_reference` - Get database schema for custom queries

**Example queries you can ask Code Puppy:**
- "What exceptions occurred in the last hour?"
- "Show me errors in claude_cache_client.py from today"
- "How many tool calls did the bloodhound agent make?"
- "What's the average latency of model requests?"

## 3. Cost Tracking (genai-prices)

**What it does:** Calculates real USD costs for every model request using live pricing data.

**Integrated in:** `code_puppy/core/token_budget.py`

**Features:**
- Automatic cost calculation when recording token usage
- Supports: OpenAI, Anthropic, Google, Cerebras, and more
- Tracks cost per provider, per request, daily totals
- Budget checking includes estimated costs

**Usage in code:**
```python
from code_puppy.core.token_budget import TokenBudgetManager

budget = TokenBudgetManager()
cost = budget.record_usage(
    provider="claude_opus",
    tokens_used=1500,
    input_tokens=1000,
    output_tokens=500,
    model_ref="claude-opus-4.5"
)
print(f"Cost: ${cost:.6f}")
```

**View costs:**
```python
status = budget.get_status()
print(status["claude_opus"]["total_cost_usd"])  # "$0.045000"
print(status["claude_opus"]["cost_today"])      # "$0.032000"
```

## Full Workflow Example

1. **Code Puppy runs** → logfire captures spans/traces
2. **Sends to Logfire cloud** (if enabled)
3. **genai-prices calculates costs** for each request
4. **Code Puppy can query** its own telemetry via logfire-mcp:
   - "Show me expensive requests from today"
   - "What agents are using the most tokens?"
   - "Find all 429 rate limit errors"

## Setup Checklist

- [x] logfire library added to dependencies
- [x] Auto-configured in cli_runner.py
- [x] genai-prices added to dependencies  
- [x] Cost tracking integrated in TokenBudgetManager
- [x] logfire-mcp server config created
- [ ] Get Logfire write token (optional, for cloud sync)
- [ ] Get Logfire read token (optional, for self-analysis)
- [ ] Enable logfire-mcp in mcp_servers.json
- [ ] Test integration

## Dependencies Added

```toml
"logfire>=3.22.0",
"genai-prices>=0.2.0",
```

**Next steps:**
1. Install: `uv pip install -e .`
2. Test basic functionality
3. (Optional) Sign up for Logfire and get tokens
4. (Optional) Enable logfire-mcp for self-introspection

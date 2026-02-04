# Code Puppy: Complete Architecture Guide

**How prompts flow through agents, routing, tools, telemetry, and self-improvement**

---

## 🎯 High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           CODE PUPPY ARCHITECTURE                                    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  User Prompt                                                                         │
│      ↓                                                                               │
│  [cli_runner.py] → Parse → Handle /commands                                         │
│      ↓                                                                               │
│  [agent_manager.py] → Select Agent (code-puppy, pack-leader, epistemic-architect)  │
│      ↓                                                                               │
│  [failover_config.py] → Workload Type (ORCHESTRATOR, REASONING, CODING, LIBRARIAN) │
│      ↓                                                                               │
│  [intelligent_router.py] → Select Model (capacity-aware, proactive failover)        │
│      ↓                                                                               │
│  [base_agent.py] → Run PydanticAI Agent with Tools                                  │
│      ↓                                                                               │
│  [tools/*.py] → Execute Tools (file ops, shell, browser, UC tools)                  │
│      ↓                                                                               │
│  [callbacks.py + logfire] → Emit Telemetry                                          │
│      ↓                                                                               │
│  [messaging/*.py] → Render Response to Console                                       │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Prompt Entry Flow

### Entry Point: `cli_runner.py`

```python
# Startup flow:
python -m code_puppy
    → __main__.py → main.py → cli_runner.main_entry()
    → asyncio.run(main())
```

### Logfire Instrumentation (Lines 22-67)

All AI components are automatically instrumented:

```python
import logfire

logfire.configure(service_name="code-puppy")
logfire.instrument_pydantic_ai()  # Agent runs
logfire.instrument_mcp()          # MCP tool calls
logfire.instrument_httpx()        # HTTP requests
logfire.instrument_openai()       # OpenAI API
logfire.instrument_anthropic()    # Anthropic API
```

### REPL Loop (Lines 395-550)

```
User Input → parse_prompt_attachments() → handle_command() → run_prompt_with_attachments()
```

---

## 2. Agent Selection & Workload Routing

### Agent Discovery (`agent_manager.py`)

Agents are discovered from:
1. **Python agents**: `agents/agent_*.py`, `agents/pack/*.py`
2. **JSON agents**: `~/.code_puppy/agents/*.json`
3. **Plugin agents**: Via callback system

### Workload Types (`failover_config.py`)

| Workload Type | Purpose | Primary Models | Agents |
|---------------|---------|----------------|--------|
| **ORCHESTRATOR** | Complex planning, multi-agent coordination | Opus → Kimi K2.5 → Sonnet | pack-leader, helios, epistemic-architect |
| **REASONING** | Logic, security analysis, code review | Sonnet → DeepSeek R1 → Kimi | shepherd, watchdog, security-auditor |
| **CODING** | Fast code generation | Cerebras → GPT-5.2-Codex → MiniMax | husky, retriever, code-puppy, python-programmer |
| **LIBRARIAN** | Search, docs, context retrieval | Haiku → Gemini Flash → OpenRouter | bloodhound, lab-rat, doc-writer |

### Agent → Workload Mapping

```python
AGENT_WORKLOAD_REGISTRY = {
    # ORCHESTRATORS (Claude Opus → Antigravity Opus → Kimi K2.5)
    "pack-leader": WorkloadType.ORCHESTRATOR,
    "helios": WorkloadType.ORCHESTRATOR,
    "epistemic-architect": WorkloadType.ORCHESTRATOR,
    "planning": WorkloadType.ORCHESTRATOR,
    "agent-creator": WorkloadType.ORCHESTRATOR,
    
    # REASONING (Sonnet → DeepSeek R1 → Kimi K2)
    "shepherd": WorkloadType.REASONING,
    "watchdog": WorkloadType.REASONING,
    "code-reviewer": WorkloadType.REASONING,
    "python-reviewer": WorkloadType.REASONING,
    "security-auditor": WorkloadType.REASONING,
    "qa-expert": WorkloadType.REASONING,
    # + typescript-reviewer, golang-reviewer, cpp-reviewer, etc.
    
    # CODING (Cerebras GLM → GPT-5.2-Codex → MiniMax)
    "husky": WorkloadType.CODING,
    "terrier": WorkloadType.CODING,
    "retriever": WorkloadType.CODING,
    "code-puppy": WorkloadType.CODING,
    "python-programmer": WorkloadType.CODING,
    "test-generator": WorkloadType.CODING,
    # + qa-kitten, ui-programmer, rag-agent, etc.
    
    # LIBRARIAN (Haiku → Gemini Flash → OpenRouter)
    "bloodhound": WorkloadType.LIBRARIAN,
    "lab-rat": WorkloadType.LIBRARIAN,
    "file-summarizer": WorkloadType.LIBRARIAN,
    "doc-writer": WorkloadType.LIBRARIAN,
}
# See failover_config.py for complete list of 30+ agent mappings
```

---

## 3. Intelligent Model Routing System

The routing system is a **comprehensive capacity-aware, workload-based intelligent model routing system** that ensures work **never stops due to rate limits**. It consists of 5 interconnected modules.

### 3.1 Core Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Request                              │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. Agent Name → Workload Type (AGENT_WORKLOAD_REGISTRY)        │
│     e.g., "code-puppy" → CODING                                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. Get Failover Chain (WORKLOAD_CHAINS)                        │
│     CODING → [Cerebras, Synthetic-GLM, Codex, MiniMax, ...]     │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. Filter by Credentials (CredentialChecker)                   │
│     Remove models without API key or OAuth token                │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. Filter by Capacity (CapacityRegistry)                       │
│     Remove EXHAUSTED/COOLDOWN, sort by availability             │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. Smart Selection (SmartModelSelector)                        │
│     Score by cost/speed/reliability/capability                  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. Return RoutingDecision                                      │
│     model_name, reason, tier, capacity_status                   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  7. After Request: Update Capacity                              │
│     record_success() → update from headers                      │
│     record_rate_limit() → enter cooldown, select new model      │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Intelligent Router (`intelligent_router.py`)

Central routing layer that orchestrates all model selection decisions with capacity awareness.

**Key Classes:**

| Class | Purpose |
|-------|---------|
| `RoutingDecision` | Selected model, workload, reason, capacity status, available tokens, tier |
| `RoutingStats` | Total requests, successful routes, proactive/reactive switches, rate limits |
| `IntelligentModelRouter` | **Singleton** implementing routing logic |

**Key Features:**
- **Proactive switching at 80% capacity** (before hitting 429)
- **Same-tier failover preference** to maintain quality
- **Per-workload round-robin** to distribute load
- **Logfire telemetry integration** for self-learning
- **Never-block design** - always finds an available model

```python
class IntelligentModelRouter:
    def select_model(self, workload: str, estimated_tokens: int) -> RoutingDecision:
        # 1. Get workload chain from WORKLOAD_CHAINS
        # 2. Filter by credentials
        # 3. Check capacity for each model
        # 4. Return best available with capacity
        
    def record_success(self, model, input_tokens, output_tokens, headers):
        # Update capacity from rate limit headers
        
    def record_rate_limit(self, model) -> RoutingDecision:
        # Trigger cooldown, return next model in chain
```

### 3.3 Model Capacity Tracking (`model_capacity.py`)

Real-time tracking of model capacity, rate limits, and availability status.

**Capacity Status Thresholds:**

| Status | Usage % | Meaning |
|--------|---------|---------|
| `AVAILABLE` | 0-49% | Plenty of capacity |
| `APPROACHING` | 50-79% | Can use, consider alternatives |
| `LOW` | 80-94% | **Should switch soon** |
| `EXHAUSTED` | 95%+ | Must switch immediately |
| `COOLDOWN` | After 429 | Exponential backoff (60s → 600s max) |

**Capacity Status Flow:**

```
CapacityStatus.AVAILABLE (< 50% used)
    ↓ (usage ≥ 50%)
CapacityStatus.APPROACHING (50-79% used)
    ↓ (usage ≥ 80%, proactive switch recommended)
CapacityStatus.LOW (80-94% used)
    ↓ (usage ≥ 95%, must switch)
CapacityStatus.EXHAUSTED (95%+ or 429)
    ↓ (cooldown triggered)
CapacityStatus.COOLDOWN (waiting for reset)
```

**Rate Limit Header Parsing:**

Supports multiple header formats from different providers:
- `x-ratelimit-remaining-tokens`
- `x-ratelimit-remaining-requests`
- `anthropic-ratelimit-tokens-remaining`
- Daily and minute variants

### 3.4 Smart Model Selection (`smart_selection.py`)

Multi-factor scoring system for optimal model selection.

**Selection Strategies:**

| Strategy | Description |
|----------|-------------|
| `COST_OPTIMIZED` | Minimize cost |
| `SPEED_OPTIMIZED` | Minimize latency |
| `RELIABILITY_OPTIMIZED` | Maximize success rate |
| `BALANCED` | Balance all factors (default) |
| `CAPABILITY_FIRST` | Most capable regardless of cost |

**Balanced Scoring Weights:**

```python
BALANCED_WEIGHTS = {
    "cost": 0.30,
    "speed": 0.30,
    "reliability": 0.25,
    "capability": 0.15,
}
```

**Scoring Components:**

| Score | Calculation | Range |
|-------|-------------|-------|
| **Cost** | Tokens per dollar (100 = >1M tokens/$) | 0-100 |
| **Speed** | P50 latency (100 = <100ms, 0 = >10s) | 0-100 |
| **Reliability** | Success rate | 0-100 |
| **Capability** | From tier (Tier 1 = 100, Tier 5 = 20) | 20-100 |

### 3.5 Model Tier System

**5-Tier Architecture:**

| Tier | Name | Purpose | Example Models |
|------|------|---------|----------------|
| **1** | Architect | Planning, reasoning, orchestration | Opus, Kimi K2.5, Qwen3-235B |
| **2** | Builder High | Complex coding, refactoring | GPT-5.2-Codex, DeepSeek R1, Sonnet-thinking |
| **3** | Builder Mid | Standard development | Sonnet, Gemini Pro, MiniMax M2.1 |
| **4** | Librarian | Context, search, docs | Haiku, Gemini Flash, OpenRouter Free |
| **5** | Sprinter | High-volume, fast code | Cerebras GLM-4.7, Synthetic GLM |

### 3.6 Workload Chains (`failover_config.py`)

**ORCHESTRATOR Chain** (needs max reasoning):
```python
[
    "claude-code-claude-opus-4-5-20251101",      # Tier 1
    "antigravity-claude-opus-4-5-thinking-high", # Tier 1
    "synthetic-Kimi-K2.5-Thinking",              # Tier 1
    "synthetic-hf-Qwen-Qwen3-235B-A22B-Thinking-2507", # Tier 1
    "claude-code-claude-sonnet-4-5-20250929",    # Tier 3 fallback
    "chatgpt-gpt-5.2-codex",                     # Tier 2 fallback
]
```

**REASONING Chain** (deep reasoning):
```python
[
    "claude-code-claude-sonnet-4-5-20250929",         # Tier 3
    "antigravity-claude-sonnet-4-5-thinking-high",    # Tier 2
    "synthetic-hf-deepseek-ai-DeepSeek-R1-0528",      # Tier 2
    "synthetic-Kimi-K2-Thinking",                      # Tier 1
    "synthetic-MiniMax-M2.1",                          # Tier 3 fallback
]
```

**CODING Chain** (speed + quality):
```python
[
    "Cerebras-GLM-4.7",                           # Tier 5 - 1500 tok/s!
    "synthetic-GLM-4.7",                          # Tier 5 backup
    "chatgpt-gpt-5.2-codex",                      # Tier 2
    "synthetic-MiniMax-M2.1",                     # Tier 3
    "synthetic-hf-MiniMaxAI-MiniMax-M2.1",        # Tier 3
    "claude-code-claude-haiku-4-5-20251001",      # Tier 4
    "antigravity-gemini-3-flash",                 # Tier 4
]
```

**LIBRARIAN Chain** (cost efficiency):
```python
[
    "claude-code-claude-haiku-4-5-20251001",      # Tier 4
    "antigravity-gemini-3-flash",                 # Tier 4
    "openrouter-arcee-ai-trinity-large-preview-free", # Tier 4 FREE
    "openrouter-stepfun-step-3.5-flash-free",     # Tier 4 FREE
]
```

### 3.7 Provider Rate Limits

| Provider | TPM | RPM | Daily | Context | Plan |
|----------|-----|-----|-------|---------|------|
| **Cerebras** | 1M | 50 | 24M | 131K | Code Pro $50/mo |
| **Synthetic GLM** | 800K | 60 | 50M | 200K | Pro $60/mo |
| **Gemini Flash** | 150K | 50 | 2M | 1M | Free |
| **OpenRouter Free** | 50K | 20 | 500K | 128K | Free |
| **Claude Code** | 200K | 50 | 20M | 200K | Max $100/mo |
| **Antigravity** | 200K | 30 | 10M | 200K | Pro $20/mo |
| **ChatGPT Teams** | 150K | 40 | 10M | 128K | Teams $35/mo |

### 3.8 Token Budget Constants

```python
# Cerebras optimization
CEREBRAS_TARGET_INPUT_TOKENS = 50_000
CEREBRAS_MAX_CONTEXT_TOKENS = 131_072
CEREBRAS_MAX_OUTPUT_TOKENS = 40_000
FORCE_SUMMARY_THRESHOLD = 50_000

# Antigravity compaction
ANTIGRAVITY_MAX_INPUT_TOKENS = 100_000
ANTIGRAVITY_COMPACTION_THRESHOLD = 0.50
```

---

## 3.9 Credential Availability System

### Automatic Model Filtering (`credential_availability.py`)

Models are **automatically excluded** from routing if they lack valid credentials. This ensures:

1. **No wasted API calls** to unconfigured providers
2. **Clean failover chains** with only usable models
3. **Transparent status** via `/status` command

### Credential Types

| Provider | Credential Type | How to Configure |
|----------|----------------|------------------|
| **claude_code** | OAuth Token | `/login claude` → Browser auth |
| **antigravity** | OAuth Token | `/login antigravity` → Browser auth |
| **chatgpt** | OAuth Token | `/login chatgpt` → Browser auth |
| **cerebras** | API Key | `/set cerebras_api_key = sk-...` or `CEREBRAS_API_KEY` env |
| **openrouter** | API Key | `/set openrouter_api_key = sk-...` or `OPENROUTER_API_KEY` env |
| **synthetic** | API Key | `/set synthetic_api_key = sk-...` or `SYN_API_KEY` env |
| **gemini** | API Key | `/set gemini_api_key = ...` or `GEMINI_API_KEY` env |
| **openai** | API Key | `/set openai_api_key = sk-...` or `OPENAI_API_KEY` env |
| **anthropic** | API Key | `/set anthropic_api_key = sk-...` or `ANTHROPIC_API_KEY` env |
| **zai** | API Key | `/set zai_api_key = ...` or `ZAI_API_KEY` env |

### API Key Naming Flexibility

The credential checker supports **multiple key name formats** for each provider:

```python
# Both of these work:
/set SYN_API_KEY = sk-...        # Uppercase format
/set synthetic_api_key = sk-...  # Lowercase format (from /set)
```

### OAuth Token Storage

OAuth tokens are stored in plugin directories:

```
~/.code_puppy/plugins/
├── claude_code_oauth/tokens.json
├── antigravity_oauth/tokens.json
└── chatgpt_oauth/tokens.json
```

### Credential Check Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CREDENTIAL AVAILABILITY CHECK                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Model Selection Request                                                     │
│      ↓                                                                       │
│  get_chain_for_workload(CODING, filter_by_credentials=True)                 │
│      ↓                                                                       │
│  For each model in chain:                                                    │
│      ↓                                                                       │
│  has_valid_credentials(model_name)?                                          │
│      ├── OAuth Provider? → Check ~/.code_puppy/plugins/{plugin}/tokens.json │
│      │                     → Validate access_token exists & not empty        │
│      │                                                                       │
│      └── API Key Provider? → Check config + environment variables           │
│                             → Try multiple key name formats                  │
│                             → (e.g., SYN_API_KEY, synthetic_api_key)         │
│      ↓                                                                       │
│  Return filtered chain with only credentialed models                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Cache Invalidation

Credential status is cached for performance but **automatically invalidated** when:

- OAuth login succeeds (token saved)
- OAuth logout performed
- API key set via `/set` command

```python
# In OAuth plugins (e.g., claude_code_oauth/utils.py):
def save_tokens(tokens: dict) -> None:
    # Save tokens to file
    with open(TOKEN_PATH, "w") as f:
        json.dump(tokens, f)
    
    # Invalidate cache so new credential is recognized immediately
    from code_puppy.core import invalidate_credential_cache
    invalidate_credential_cache()
```

### Integration Points

The credential system is integrated at all routing levels:

| Component | Integration |
|-----------|-------------|
| `intelligent_router.py` | Pre-filters models before selection |
| `failover_config.py` | `get_chain_for_workload(filter_by_credentials=True)` |
| `rate_limit_failover.py` | Filters failover chains and available models |
| `model_capacity.py` | Checks credentials before capacity check |
| `smart_selection.py` | Skips uncredentialed models in scoring |

### Checking Credential Status

```bash
# In Code Puppy REPL:
>>> from code_puppy.core import get_credential_status
>>> get_credential_status()

=== Credential Status ===
  ✅ antigravity: OAuth (antigravity_oauth)
  ✅ cerebras: CEREBRAS_API_KEY | cerebras_api_key
  ✅ chatgpt: OAuth (chatgpt_oauth)
  ✅ claude_code: OAuth (claude_code_oauth)
  ✅ openrouter: OPENROUTER_API_KEY | openrouter_api_key
  ✅ synthetic: SYN_API_KEY | synthetic_api_key | syn_api_key
  ❌ gemini: GEMINI_API_KEY | gemini_api_key (no key set)
  ❌ zai: ZAI_API_KEY | zai_api_key (no key set)

=== Model Availability ===
Available models (28):
  - Claude Code Claude 4 Opus
  - Claude Code Claude 4.5 Sonnet
  - Cerebras-GLM-4.7
  - synthetic-GLM-4.7
  - openrouter/deepseek/r1
  ...

Unavailable models (6):
  - Gemini-3
  - Gemini-3-Long-Context
  - zai-glm-4o
  ...
```

---

## 4. Agent Orchestration (Pack System)

### Orchestration Hierarchy (`agent_orchestration.py`)

```python
ORCHESTRATION_HIERARCHY = {
    "epistemic-architect": ["planning", "pack-leader", "helios", "qa-expert"],
    "planning": ["pack-leader", "helios", "code-puppy"],
    "pack-leader": ["bloodhound", "terrier", "husky", "shepherd", "retriever", "watchdog"],
    "helios": ["pack-leader", "code-puppy", "python-programmer"],
}
```

### Pack Leader Workflow

```
Pack Leader 🐺 coordinates:
├── bloodhound 🐕‍🦺  → Issue tracking (bd only)
├── terrier 🐕       → Worktree management  
├── husky 🐺         → Task execution (coding)
├── shepherd 🐕      → Code review (critic)
├── watchdog 🐕‍🦺    → QA/testing (critic)
└── retriever 🦮     → Local branch merging
```

**Execution Flow:**
1. Declare base branch
2. Create `bd` issues with dependencies (bloodhound)
3. Create worktrees for each issue (terrier)
4. Execute tasks in parallel (husky)
5. Review code quality (shepherd - critic)
6. Run QA checks (watchdog - critic)
7. Merge approved branches (retriever)

### Pack Governor (`pack_governor.py`)

Enforces concurrency limits per role:

```python
GovernorConfig(
    max_coding_agents=2,     # Max Cerebras concurrent
    max_reviewer_agents=1,   # Max Claude concurrent
    max_searcher_agents=3,   # Max Gemini concurrent
)
```

---

## 5. The Epistemic Architect & 7 Lenses

### The 7 Expert Lenses

| Lens | Core Question | Outputs |
|------|---------------|---------|
| 🧠 **Philosophy** | What are we assuming? | Hidden assumptions, category errors |
| 📊 **Data Science** | Can we measure this? | Metrics plan, experiment design |
| 🛡️ **Safety/Risk** | What could go wrong? | Risk flags, circuit breakers |
| 🔷 **Topology** | What's the structure? | Dependencies, phase transitions |
| ∑ **Theoretical Math** | Is this logically consistent? | Consistency checks, proofs |
| ⚙️ **Systems Engineering** | Can we build this? | Service boundaries, interfaces |
| 👤 **Product/UX** | Does this help users? | Value hypotheses, MVP scope |

### The 12-Stage Pipeline

| Stage | Name | Purpose |
|-------|------|---------|
| 0 | Philosophical Foundation | Internalize Ralph Loops |
| 1 | Epistemic State Creation | Surface assumptions/hypotheses |
| 2 | Lens Evaluation | Apply all 7 lenses |
| 3 | Gap Analysis | Identify CRITICAL/HIGH gaps |
| 4 | Goal Emergence | Run goals through 6 gates |
| 5 | MVP Planning | Minimal viable plan |
| 6 | Spec Generation | Full specs, readiness check |
| 7 | Build Execution | Phase → Milestone → Checkpoint |
| **8** | **Improvement Audit** | Evidence → Analysis → Recommendation |
| 9 | Gap Re-Inspection | What new gaps emerged? |
| 10 | Question Tracking | Update epistemic state |
| 11 | Verification Audit | End-to-end check |
| 12 | Documentation Sync | Update docs, **LOOP TO STAGE 8** |

### Project Artifact Structure

```
project/
├── BUILD.md              ← Execution plan (phases, milestones, checkpoints)
├── epistemic/            ← Epistemic state
│   ├── state.json        ← Machine-readable state
│   ├── assumptions.md
│   ├── hypotheses.md
│   └── constraints.md
├── docs/                 ← Analysis documents
│   ├── lens-evaluation.md
│   ├── gap-analysis.md
│   └── goals-and-gates.md
└── specs/                ← Specifications
    ├── entities.md
    ├── personas.md
    ├── critical-flows.md
    └── metrics.md
```

### The 6 Quality Gates

Goals must pass ALL gates:

| Gate | Check |
|------|-------|
| 👁️ **Observables** | Does it have measurable outcomes? |
| 🧪 **Testability** | Clear success/failure criteria? |
| ↩️ **Reversibility** | Is there a rollback plan? |
| 📈 **Confidence** | Is confidence ≥ 0.6? |
| 🤝 **Lens Agreement** | Do 3+ lenses approve? |
| 📚 **Evidence Grounding** | Based on actual evidence? |

### The Self-Improvement Loop (Stages 8-12)

```
EVIDENCE (gather facts) → ANALYSIS (apply lenses) → RECOMMENDATION (propose fixes) → EXECUTE → loop
```

---

## 6. Tool Execution

### Tool Registry (`tools/__init__.py`)

```python
TOOL_REGISTRY = {
    # Agent Tools
    "list_agents": register_list_agents,
    "invoke_agent": register_invoke_agent,
    
    # File Operations
    "list_files": register_list_files,
    "read_file": register_read_file,
    "edit_file": register_edit_file,
    
    # Shell Commands
    "agent_run_shell_command": register_agent_run_shell_command,
    
    # Universal Constructor
    "universal_constructor": register_universal_constructor,
    
    # Browser Control (30+ tools)
    "browser_initialize": register_initialize_browser,
    ...
}
```

### invoke_agent Tool

When an agent invokes a sub-agent:

```python
@agent.tool
async def invoke_agent(ctx, agent_name: str, prompt: str, session_id: str = None):
    # 1. Acquire slot from PackGovernor
    slot = await acquire_agent_slot(agent_name, estimated_tokens)
    
    # 2. Get workload-based model
    model = get_model_for_agent(agent_name)  # Uses AGENT_WORKLOAD_REGISTRY
    
    # 3. Create temp agent with tools
    temp_agent = Agent(model=model, instructions=instructions)
    register_tools_for_agent(temp_agent, agent_config.tools)
    
    # 4. Run with streaming
    result = await temp_agent.run(prompt, message_history, event_stream_handler)
    
    # 5. Save session & release slot
    save_session_history(session_id, result.all_messages())
    release_agent_slot(slot_id)
```

---

## 7. Helios & Dynamic Tool Creation

### Helios (Universal Constructor Agent)

Helios can **create tools dynamically**:

```python
# User: "Create a weather API tool"
# Helios writes Python code and calls:
universal_constructor(action="create", name="weather", code="...")

# Tool is written to ~/.code_puppy/plugins/universal_constructor/weather.py
# Registry is hot-reloaded
# Tool is immediately available via uc:weather
```

### Agent Creator Agent

Creates **JSON-based agents** through conversation:

1. Gather requirements (name, description, tools needed)
2. Suggest tools from registry (built-in + UC tools)
3. Generate JSON configuration
4. Save to `~/.code_puppy/agents/`
5. Agent immediately available via `/agent <name>`

### Dynamic Capability Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  Helios ☀️ → universal_constructor(create) → ~/.code_puppy/    │
│                                              plugins/UC/tool.py │
│                                                    ↓            │
│                                             UCRegistry.reload() │
│                                                    ↓            │
│  Any Agent → register_tools_for_agent() → Tool Available!      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Logfire Telemetry & Self-Improvement

### Real-Time Telemetry Events (NEW - Feb 2026)

**Purpose:** Verify system is "sticking to the plan" by tracking critical decision points.

| Event | Source | Log Level | Purpose | Key Fields |
|-------|--------|-----------|---------|------------|
| `Workload routing` | base_agent.py | INFO | Verify correct model for workload | agent, workload, orchestrated_model |
| `Failover triggered` | failover_model.py | WARN | Track model switches on 429s | from_model, to_model, error_type |
| `Failover success` | failover_model.py | INFO | Confirm recovery | model, workload, attempts |
| `Rate limit` | failover_model.py | WARN | Track cooldown periods | model, cooldown, consecutive_429s |
| `Capacity warning` | model_capacity.py | WARN | Alert at 80%+ usage | model, pct, limit_type, used, limit |
| `EAR phase` | ralph_loop.py | INFO | Track reasoning stages | loop_id, from_phase, to_phase, confidence |

**Health Checks:**
- ✅ CODING workload → GLM-4.7 (not Kimi-K2.5)
- ✅ Failover recoveries ≈ failover triggers  
- ✅ EAR loops >90% complete, <10% error
- ✅ Capacity warnings precede rate limits

See [docs/LOGFIRE-OBSERVABILITY.md](LOGFIRE-OBSERVABILITY.md) for complete query reference.

### Legacy Telemetry Points

| Event | Location | Data Captured |
|-------|----------|---------------|
| `capacity_update` | model_capacity.py | Model usage %, remaining tokens |
| `model_router.selection` | intelligent_router.py | Model, workload, reason, tier |
| `rate_limit.*` | rate_limit_headers.py | Provider, remaining, threshold |
| Agent spans | husky_execution.py | Plan/Execute/Verify loops |
| Tool calls | callbacks.py | Tool name, duration, result |

### Logfire MCP Server

Code Puppy can **query its own telemetry**:

```python
# Available MCP tools:
find_exceptions_in_file(file="claude_cache_client.py")
arbitrary_query("SELECT * FROM spans WHERE name LIKE '%rate_limit%'")
logfire_link(trace_id="...")
schema_reference()
```

### Self-Improvement Loop

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SELF-IMPROVEMENT ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. CAPTURE                                                              │
│     └─ Logfire auto-instruments all operations                          │
│                                                                          │
│  2. STORE                                                                │
│     ├─ Logfire Cloud: Traces, spans, metrics                            │
│     └─ Local: ~/.codepuppy/usage.jsonl (token ledger)                   │
│                                                                          │
│  3. QUERY                                                                │
│     └─ Logfire MCP: Self-introspection via SQL                          │
│                                                                          │
│  4. REACT (Real-time)                                                   │
│     ├─ Rate limit headers → Proactive failover                          │
│     ├─ Capacity tracking → Model switching at 80%                       │
│     └─ Circuit breakers → Disable unhealthy models                      │
│                                                                          │
│  5. LEARN (Aggregated)                                                  │
│     ├─ ModelMetrics: p50/p95/p99 latencies per model                    │
│     ├─ SmartSelector: Multi-factor scoring (cost, speed, reliability)   │
│     └─ Performance Dashboard: System health trends                      │
│                                                                          │
│  6. OPTIMIZE                                                             │
│     └─ Routing decisions informed by historical performance             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Cost & Budget Tracking

| Component | File | Purpose |
|-----------|------|---------|
| Token Telemetry | token_telemetry.py | Usage ledger (AUDIT-1.1 compliant) |
| Cost Budget | cost_budget.py | Per-provider and global limits |
| Token Budget | token_budget.py | Rate limiting with failover |
| Model Metrics | model_metrics.py | Latency percentiles, success rates |

---

## 9. Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER PROMPT                                     │
│                    "Create unit tests for the auth module"                  │
└────────────────────────────────────────┬────────────────────────────────────┘
                                         ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. CLI RUNNER (cli_runner.py)                                               │
│    ├── parse_prompt_attachments() → Extract files, images, URLs             │
│    ├── handle_command() → Check for /slash commands                         │
│    └── get_current_agent() → Load from registry                             │
└────────────────────────────────────────┬────────────────────────────────────┘
                                         ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. AGENT MANAGER (agent_manager.py)                                         │
│    ├── Terminal session isolation (PPID-based)                              │
│    ├── _discover_agents() → Python + JSON + Plugin agents                   │
│    └── load_agent("code-puppy") → BaseAgent instance                        │
└────────────────────────────────────────┬────────────────────────────────────┘
                                         ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. WORKLOAD ROUTING (failover_config.py)                                    │
│    ├── AGENT_WORKLOAD_REGISTRY["code-puppy"] → WorkloadType.CODING          │
│    └── WORKLOAD_CHAINS[CODING] → ["Cerebras-GLM-4.7", "synthetic-GLM-4.7"] │
└────────────────────────────────────────┬────────────────────────────────────┘
                                         ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 4. INTELLIGENT ROUTER (intelligent_router.py, model_capacity.py)            │
│    ├── Check capacity for each model in chain                               │
│    ├── Proactive switch if > 80% usage                                      │
│    ├── Round-robin among available models                                   │
│    └── Return: "Cerebras-GLM-4.7" + RoutingDecision                        │
└────────────────────────────────────────┬────────────────────────────────────┘
                                         ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 5. BASE AGENT RUN (base_agent.py)                                           │
│    ├── get_full_system_prompt() → Agent-specific instructions               │
│    ├── message_history_processor() → Token budget management                │
│    ├── run_with_mcp() → Create PydanticAI Agent + Tools + MCP servers       │
│    └── agent.run(prompt, message_history, event_stream_handler)             │
└────────────────────────────────────────┬────────────────────────────────────┘
                                         ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 6. PYDANTIC AI + LOGFIRE (instrumented automatically)                       │
│    ├── logfire.span("agent_run") → Trace entire run                         │
│    ├── API call to provider (Cerebras/Claude/GPT)                           │
│    ├── Streaming response → event_stream_handler()                          │
│    └── Tool calls embedded in response                                       │
└────────────────────────────────────────┬────────────────────────────────────┘
                                         ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 7. TOOL EXECUTION (tools/*.py)                                              │
│    ├── on_pre_tool_call(tool_name, tool_args) → Callback                   │
│    ├── Execute tool (edit_file, agent_run_shell_command, etc.)             │
│    ├── on_post_tool_call(tool_name, result, duration_ms) → Callback         │
│    └── Return ToolReturn to model                                           │
└────────────────────────────────────────┬────────────────────────────────────┘
                                         ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 8. SUB-AGENT INVOCATION (if invoke_agent called)                            │
│    ├── PackGovernor.acquire_slot() → Enforce concurrency limits             │
│    ├── get_model_for_agent() → Workload-based selection                     │
│    ├── Run sub-agent with subagent_stream_handler                           │
│    └── PackGovernor.release_slot()                                          │
└────────────────────────────────────────┬────────────────────────────────────┘
                                         ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 9. RESPONSE FLOW (messaging/*.py)                                           │
│    ├── result.output → Final agent response                                 │
│    ├── AgentResponseMessage(content, is_markdown=True)                      │
│    ├── get_message_bus().emit(response_msg)                                 │
│    └── RichConsoleRenderer → Markdown to terminal                           │
└────────────────────────────────────────┬────────────────────────────────────┘
                                         ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 10. POST-PROCESSING                                                          │
│     ├── Update capacity registry with usage from headers                    │
│     ├── auto_save_session_if_enabled()                                      │
│     └── Continue REPL → Next user prompt                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Key File Reference

| Component | Files |
|-----------|-------|
| **Entry Point** | cli_runner.py, main.py, __main__.py |
| **Agent Management** | agents/agent_manager.py, agents/base_agent.py |
| **Pack System** | agents/agent_pack_leader.py, agents/pack/*.py |
| **Epistemic Architect** | agents/agent_epistemic_architect.py, epistemic/ |
| **Model Routing** | core/intelligent_router.py, core/model_capacity.py, core/capacity_aware_round_robin.py |
| **Credential Availability** | core/credential_availability.py |
| **Failover Config** | core/failover_config.py, core/rate_limit_failover.py |
| **Smart Selection** | core/smart_selection.py |
| **Pack Governor** | core/pack_governor.py, core/agent_orchestration.py |
| **Tool Registry** | tools/__init__.py, tools/agent_tools.py |
| **Universal Constructor** | tools/universal_constructor.py, plugins/universal_constructor/ |
| **OAuth Plugins** | plugins/claude_code_oauth/, plugins/antigravity_oauth/, plugins/chatgpt_oauth/ |
| **Callbacks/Telemetry** | callbacks.py, core/model_metrics.py |
| **Cost Tracking** | core/cost_budget.py, core/token_budget.py |
| **Messaging** | messaging/__init__.py, messaging/bus.py |

---

## 11. The Full Self-Improvement Cycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE SELF-IMPROVEMENT CYCLE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    EPISTEMIC ARCHITECT                               │    │
│  │  ┌───────────────────────────────────────────────────────────────┐  │    │
│  │  │ 1. Analyze requirements through 7 lenses                      │  │    │
│  │  │ 2. Surface assumptions/hypotheses                             │  │    │
│  │  │ 3. Generate specs/PRDs/BDs                                    │  │    │
│  │  │ 4. Create BUILD.md with phases/milestones                     │  │    │
│  │  └───────────────────────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────┬────────────────────────────────┘    │
│                                       ↓                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    PACK LEADER EXECUTION                             │    │
│  │  ┌───────────────────────────────────────────────────────────────┐  │    │
│  │  │ 1. Create issues/worktrees (bloodhound, terrier)              │  │    │
│  │  │ 2. Execute tasks (husky) with capacity-aware routing          │  │    │
│  │  │ 3. Review code (shepherd, watchdog)                           │  │    │
│  │  │ 4. Merge and close (retriever, bloodhound)                    │  │    │
│  │  └───────────────────────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────┬────────────────────────────────┘    │
│                                       ↓                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    LOGFIRE TELEMETRY                                 │    │
│  │  ┌───────────────────────────────────────────────────────────────┐  │    │
│  │  │ • Agent runs, tool calls, model routing                       │  │    │
│  │  │ • Token usage, latencies, error rates                         │  │    │
│  │  │ • Rate limit headers, capacity status                         │  │    │
│  │  └───────────────────────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────┬────────────────────────────────┘    │
│                                       ↓                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    IMPROVEMENT AUDIT (Stage 8)                       │    │
│  │  ┌───────────────────────────────────────────────────────────────┐  │    │
│  │  │ 1. Query Logfire via MCP for performance data                 │  │    │
│  │  │ 2. Apply 7 lenses to results                                  │  │    │
│  │  │ 3. Update epistemic state (close hypotheses, adjust confidence)│  │    │
│  │  │ 4. Identify gaps, generate recommendations                    │  │    │
│  │  │ 5. Update specs/PRDs as needed                                │  │    │
│  │  │ 6. LOOP BACK to Pack Leader or Epistemic Architect            │  │    │
│  │  └───────────────────────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────┬────────────────────────────────┘    │
│                                       ↓                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    REAL-TIME OPTIMIZATION                            │    │
│  │  ┌───────────────────────────────────────────────────────────────┐  │    │
│  │  │ • Capacity tracking → Proactive model switching               │  │    │
│  │  │ • Smart selection → Multi-factor model scoring                │  │    │
│  │  │ • Cost budget → Throttling when limits approached             │  │    │
│  │  │ • Circuit breakers → Disable unhealthy providers              │  │    │
│  │  └───────────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 12. All Supported Models (35+)

### Claude Code (OAuth)
| Model | Tier | Context |
|-------|------|---------|
| `claude-code-claude-opus-4-5-20251101` | 1 | 200K |
| `claude-code-claude-sonnet-4-5-20250929` | 3 | 200K |
| `claude-code-claude-haiku-4-5-20251001` | 4 | 200K |

### Antigravity (OAuth)
| Model | Tier | Context |
|-------|------|---------|
| `antigravity-claude-opus-4-5-thinking-low` | 1 | 200K |
| `antigravity-claude-opus-4-5-thinking-medium` | 1 | 200K |
| `antigravity-claude-opus-4-5-thinking-high` | 1 | 200K |
| `antigravity-claude-sonnet-4-5` | 3 | 200K |
| `antigravity-claude-sonnet-4-5-thinking-low` | 2 | 200K |
| `antigravity-claude-sonnet-4-5-thinking-medium` | 2 | 200K |
| `antigravity-claude-sonnet-4-5-thinking-high` | 2 | 200K |
| `antigravity-gemini-3-pro-low` | 3 | 1M |
| `antigravity-gemini-3-pro-high` | 3 | 1M |
| `antigravity-gemini-3-flash` | 4 | 1M |

### ChatGPT (OAuth)
| Model | Tier | Context |
|-------|------|---------|
| `chatgpt-gpt-5.2` | 2 | 128K |
| `chatgpt-gpt-5.2-codex` | 2 | 128K |

### Cerebras (API Key)
| Model | Tier | Context | Speed |
|-------|------|---------|-------|
| `Cerebras-GLM-4.7` | 5 | 131K | **1500+ tok/s** |

### Synthetic (API Key)
| Model | Tier | Context |
|-------|------|---------|
| `synthetic-GLM-4.7` | 5 | 200K |
| `synthetic-MiniMax-M2.1` | 3 | 1M |
| `synthetic-Kimi-K2-Thinking` | 1 | 200K |
| `synthetic-Kimi-K2.5-Thinking` | 1 | 200K |
| `synthetic-hf-moonshotai-Kimi-K2.5` | 1 | 200K |
| `synthetic-hf-moonshotai-Kimi-K2-Thinking` | 1 | 200K |
| `synthetic-hf-deepseek-ai-DeepSeek-R1-0528` | 2 | 128K |
| `synthetic-hf-MiniMaxAI-MiniMax-M2.1` | 3 | 1M |
| `synthetic-hf-Qwen-Qwen3-235B-A22B-Thinking-2507` | 1 | 131K |
| `synthetic-hf-zai-org-GLM-4.7` | 5 | 200K |

### OpenRouter (API Key - Free Tier)
| Model | Tier | Context |
|-------|------|---------|
| `openrouter-stepfun-step-3.5-flash-free` | 4 | 128K |
| `openrouter-arcee-ai-trinity-large-preview-free` | 4 | 128K |

### Gemini (API Key)
| Model | Tier | Context |
|-------|------|---------|
| `Gemini-3` | 4 | 1M |
| `Gemini-3-Long-Context` | 4 | 2M |

### ZAI (API Key)
| Model | Tier | Context |
|-------|------|---------|
| `zai-glm-4.6-coding` | 5 | 200K |
| `zai-glm-4.6-api` | 5 | 200K |
| `zai-glm-4.7-coding` | 5 | 200K |
| `zai-glm-4.7-api` | 5 | 200K |

---

## Summary

The Code Puppy architecture is designed for **continuous self-improvement**:

1. **Epistemic Architect** creates rigorous plans through 7 lenses
2. **Pack Leader** orchestrates execution with capacity-aware routing
3. **Intelligent Router** with **5-tier model hierarchy** ensures work never stops
4. **Capacity Tracking** monitors usage and triggers proactive failover at 80%
5. **Smart Selection** scores models by cost, speed, reliability, capability
6. **Credential Availability** ensures only configured models are used
7. **35+ models** across 8 providers with automatic failover chains
8. **Logfire** captures all telemetry for self-learning optimization
9. **Improvement Audit** (Stage 8-12) creates a feedback loop
10. **The cycle repeats** with each iteration improving the next

### Design Principles

| Principle | Description |
|-----------|-------------|
| **Work Never Stops** | Always find an available model |
| **Proactive > Reactive** | Switch at 80% capacity, not at 429 |
| **Same-Tier First** | Maintain quality during failover |
| **Credential-First** | Never route to unconfigured models |
| **Telemetry-Driven** | Logfire integration for optimization |

### Quick Start: Configuring Credentials

```bash
# OAuth-based providers (opens browser):
/login claude
/login antigravity  
/login chatgpt

# API key providers:
/set cerebras_api_key = sk-...
/set openrouter_api_key = sk-...
/set synthetic_api_key = sk-...

# Check what's configured:
>>> from code_puppy.core import get_credential_status
>>> get_credential_status()
```

---

## 13. Epistemic Architect: Structured Planning Agent

The **Epistemic Architect** (`epistemic-architect`) is Code Puppy's planning specialist that implements the **Epistemic Agent Runtime (EAR)** methodology — a structured approach to building software through evidence-based reasoning.

### 🏛️ Core Philosophy

The Epistemic Architect follows a principle: **Think before you code.**

Instead of jumping straight into implementation, it guides users through a rigorous planning process that:
- **Surfaces hidden assumptions** — What are you believing without evidence?
- **Applies multiple expert perspectives** — 7 lenses evaluate your thinking
- **Validates goals through quality gates** — 6 gates ensure goals are actionable
- **Creates traceable build plans** — Every decision links to evidence

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    EPISTEMIC ARCHITECT WORKFLOW                           │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  User: "I want to build X"                                               │
│      ↓                                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ STAGE 1: Epistemic State Interview                               │   │
│  │ Ask probing questions to surface:                                │   │
│  │  • Assumptions (what do you believe?)                            │   │
│  │  • Hypotheses (what are you testing?)                            │   │
│  │  • Constraints (hard vs soft)                                    │   │
│  │  • Evidence (what do you already know?)                          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│      ↓                                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ STAGE 2-3: Apply 7 Expert Lenses + Gap Analysis                  │   │
│  │ Each lens evaluates from a different perspective:                │   │
│  │  🧠 Philosophy     📊 Data Science     🛡️ Safety/Risk           │   │
│  │  🔷 Topology       ∑ Math Theory       ⚙️ Systems Engineering   │   │
│  │  👤 Product/UX                                                   │   │
│  │                                                                   │   │
│  │ Output: Gaps classified as 🔴 CRITICAL / 🟠 HIGH / 🟡 MEDIUM    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│      ↓                                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ STAGE 4: Goal Emergence + 6 Quality Gates                        │   │
│  │ Generate candidate goals, each must pass ALL gates:              │   │
│  │  ✅ Observables — Measurable outcomes?                           │   │
│  │  ✅ Testability — Success/failure criteria?                      │   │
│  │  ✅ Reversibility — Rollback plan?                               │   │
│  │  ✅ Confidence — Above 0.6 threshold?                            │   │
│  │  ✅ Lens Agreement — 3+ lenses approve?                          │   │
│  │  ✅ Evidence Grounding — Based on evidence?                      │   │
│  │                                                                   │   │
│  │ Goals that fail gates → NOT actionable (yet)                     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│      ↓                                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ STAGE 5-6: MVP Planning + Spec Generation                        │   │
│  │ Create BUILD.md with:                                            │   │
│  │  • Phases: Foundation → Core → Polish                            │   │
│  │  • Milestones: 1-2 hour chunks                                   │   │
│  │  • Checkpoints: Verify at each milestone                         │   │
│  │  • Rollback plans: How to undo                                   │   │
│  │  • Spec files: entities, personas, flows, metrics                │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│      ↓                                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ STAGE 7+: Build with Checkpoints                                 │   │
│  │ After each milestone, checkpoint:                                │   │
│  │  ✅ Completed: What was built                                    │   │
│  │  🧪 Verified: What was tested                                    │   │
│  │  ⚠️ Issues: Any problems                                         │   │
│  │  📋 Spec Compliance: Which specs met                             │   │
│  │  ➡️ Next: Next milestone                                         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│      ↓                                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ STAGE 8-12: Continuous Improvement Loop                          │   │
│  │  • Audit: Evidence → Analysis → Recommendations                  │   │
│  │  • Re-inspect: Find new gaps                                     │   │
│  │  • Update: Close hypotheses, track questions                     │   │
│  │  • Verify: End-to-end audit                                      │   │
│  │  • Loop back to Stage 8                                          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

### Ralph (Wiggum) Loops: The Core Loop

Everything in the Epistemic Architect runs through **Ralph Loops**:

```
Observe → Orient → Decide → Act → Observe (repeat)
```

**Key Insight:** Goals are **outputs**, not inputs. They emerge from evidence, not assumptions.

### The 7 Expert Lenses

Each lens evaluates your project from a different expert perspective to surface blind spots:

| Lens | Emoji | Question | Key Outputs |
|------|-------|----------|-------------|
| **Philosophy** | 🧠 | What are we assuming? Are we epistemically honest? | Hidden assumptions, Category errors, Humility checks |
| **Data Science** | 📊 | Can we measure this? How do we test it? | Metrics plan, Confounding risks, Experiment design |
| **Safety/Risk** | 🛡️ | What could go wrong? What are the failure modes? | Risk flags, Abuse vectors, Circuit breakers |
| **Topology** | 🔷 | What's the structure? Is it stable? | Dependencies, Phase transitions, Connected components |
| **Theoretical Math** | ∑ | Is this logically consistent? | Consistency checks, Minimal axioms, Counterexamples |
| **Systems Engineering** | ⚙️ | Can we build this? What are the interfaces? | Service boundaries, Tech stack, Failure recovery |
| **Product/UX** | 👤 | Does this help users? What's the MVP? | Value hypotheses, User flows, Adoption risks |

### The 6 Quality Gates

Goals must pass **ALL 6 gates** before they become actionable:

1. **👁️ Observables** — Does this goal have measurable outcomes?
2. **🧪 Testability** — Does it have clear success/failure criteria?
3. **↩️ Reversibility** — Is there a rollback plan if it fails?
4. **📈 Confidence** — Is confidence above threshold (≥0.6)?
5. **🤝 Lens Agreement** — Do 3+ lenses approve?
6. **📚 Evidence Grounding** — Is it based on actual evidence?

### The 12-Stage Pipeline

```
Stage 0:  Philosophical Foundation — Internalize Ralph Loops and core principles
Stage 1:  Epistemic State Creation — Interview user, surface assumptions/hypotheses
Stage 2:  Lens Evaluation — Apply all 7 lenses to the epistemic state
Stage 3:  Gap Analysis — Identify CRITICAL/HIGH/MEDIUM/LOW gaps
Stage 4:  Goal Emergence — Generate candidates, run through 6 gates
Stage 5:  MVP Planning — Create minimal viable plan with rollback
Stage 6:  Spec Generation — Generate full specs, readiness check
Stage 7:  Build Execution — Phase → Milestone → Checkpoint → Verify
Stage 8:  Improvement Audit — Evidence → Analysis → Recommendation loop
Stage 9:  Gap Re-Inspection — What new gaps emerged? Re-validate
Stage 10: Question Tracking — Update epistemic state, close hypotheses
Stage 11: Verification Audit — End-to-end check across all layers
Stage 12: Documentation Sync — Update all docs, then loop to Stage 8
```

**The loop (Stages 8-12) creates continuous improvement** — each iteration refines the project.

### Project Artifact Structure

The Epistemic Architect scaffolds a complete project structure:

```
project/
├── README.md
├── BUILD.md              ← The execution plan (phases, milestones, checkpoints)
├── CHANGELOG.md
├── epistemic/            ← Stage 1: Epistemic State
│   ├── state.json        ← Assumptions, hypotheses, constraints, evidence
│   ├── assumptions.md
│   ├── hypotheses.md
│   ├── constraints.md
│   └── evidence.md
├── docs/                 ← Stages 2-5: Analysis & Planning
│   ├── lens-evaluation.md   ← 7 lens outputs
│   ├── gap-analysis.md      ← CRITICAL/HIGH/MEDIUM/LOW gaps
│   ├── goals-and-gates.md   ← Goals + gate pass/fail
│   └── improvement-plan.md  ← Continuous improvement strategy
└── specs/                ← Stage 6: Detailed Specifications
    ├── entities.md       ← Domain models
    ├── personas.md       ← User archetypes
    ├── critical-flows.md ← Key user journeys
    ├── metrics.md        ← Success metrics
    └── trust-safety.md   ← Security & safety considerations
```

### Agent Coordination & Delegation

The Epistemic Architect can **invoke other agents** to delegate specialized work:

#### Available Tools for Delegation:
- **`list_agents`** — List all available agents in the system
- **`invoke_agent`** — Invoke a specific agent with a prompt

#### Common Delegation Patterns:

**1. Invoke Helios (Universal Constructor) for Custom Tools**

```python
# User needs a specific tool that doesn't exist
result = invoke_agent(
    "helios",
    "Create a JSON schema validator tool for spec validation"
)
# Helios creates the tool using universal_constructor
# Epistemic architect can then use the new tool
```

**2. Invoke Agent Creator for Specialized Agents**

```python
# Need a domain-specific agent for the project
result = invoke_agent(
    "agent-creator",
    "Create a Python code reviewer agent with type checking tools"
)
# Agent creator generates the JSON agent definition
# New agent becomes available for the project
```

**3. Multi-Turn Conversations with Agents**

```python
# Start conversation with agent-creator
result1 = invoke_agent(
    "agent-creator",
    "I need an agent for database migrations",
    session_id="create-db-agent"
)

# Continue the conversation
result2 = invoke_agent(
    "agent-creator",
    "Add rollback capabilities to the agent",
    session_id=result1.session_id  # Continue same session
)
```

### Workflow: From Prompt to Agent Invocation

```
┌────────────────────────────────────────────────────────────────────────┐
│  User: "I want to build a REST API with authentication"                │
│      ↓                                                                  │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ Epistemic Architect: Analyze Prompt                              │ │
│  │                                                                   │ │
│  │ 1. Identify assumptions:                                         │ │
│  │    • Assuming you need OAuth 2.0? Or simple JWT?                 │ │
│  │    • Assuming you need role-based access control?                │ │
│  │    • What's your threat model?                                   │ │
│  │                                                                   │ │
│  │ 2. Form hypotheses:                                              │ │
│  │    • "OAuth 2.0 will provide sufficient security"                │ │
│  │    • Falsification: "If we see 90% of users fail login..."      │ │
│  │                                                                   │ │
│  │ 3. Create epistemic/state.json                                   │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│      ↓                                                                  │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ Apply 7 Lenses:                                                  │ │
│  │                                                                   │ │
│  │ 🧠 Philosophy: "Are you assuming 'auth' = 'OAuth'?"             │ │
│  │ 📊 Data Science: "How will you measure auth success rate?"      │ │
│  │ 🛡️ Safety: "What if someone brute-forces passwords?"           │ │
│  │ 🔷 Topology: "Auth service as separate microservice?"           │ │
│  │ ∑ Math: "JWT token expiry logic consistent?"                    │ │
│  │ ⚙️ Systems: "Can you deploy this? What's the tech stack?"       │ │
│  │ 👤 Product: "Does passwordless login improve UX?"               │ │
│  │                                                                   │ │
│  │ Output: docs/lens-evaluation.md                                  │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│      ↓                                                                  │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ Identify Gaps:                                                   │ │
│  │  🔴 CRITICAL: No JWT secret rotation strategy                    │ │
│  │  🟠 HIGH: Missing rate limiting on login endpoint                │ │
│  │  🟡 MEDIUM: No multi-factor auth planned                         │ │
│  │                                                                   │ │
│  │ Output: docs/gap-analysis.md                                     │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│      ↓                                                                  │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ Need Specialized Tool?                                           │ │
│  │                                                                   │ │
│  │ Epistemic Architect:                                             │ │
│  │ "I need a JWT token validator tool. Let me invoke Helios..."    │ │
│  │                                                                   │ │
│  │ invoke_agent("helios", "Create a JWT validator tool with        │ │
│  │              secret rotation support")                           │ │
│  │                                                                   │ │
│  │ Helios: Creates the tool using universal_constructor             │ │
│  │                                                                   │ │
│  │ Epistemic Architect: "Great! Now I can validate tokens in        │ │
│  │                       the spec verification stage."              │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│      ↓                                                                  │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ Need Specialized Agent?                                          │ │
│  │                                                                   │ │
│  │ Epistemic Architect:                                             │ │
│  │ "For code review, I'll create a security-focused agent..."      │ │
│  │                                                                   │ │
│  │ invoke_agent("agent-creator", "Create a security auditor        │ │
│  │              agent with tools: grep, read_file, edit_file")     │ │
│  │                                                                   │ │
│  │ Agent Creator: Generates JSON agent definition                   │ │
│  │                                                                   │ │
│  │ Epistemic Architect: "Perfect! Now the security-auditor can     │ │
│  │                       review the auth implementation."           │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│      ↓                                                                  │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ Generate Goals + Apply 6 Quality Gates                           │ │
│  │                                                                   │ │
│  │ Goal: "Implement JWT-based auth with secret rotation"           │ │
│  │   ✅ Observables: Can measure login success rate                 │ │
│  │   ✅ Testability: Can test with mock tokens                      │ │
│  │   ✅ Reversibility: Can rollback to old auth                     │ │
│  │   ✅ Confidence: 0.8 (high confidence)                           │ │
│  │   ✅ Lens Agreement: 5/7 lenses approve                          │ │
│  │   ✅ Evidence Grounding: Based on OAuth 2.0 spec                 │ │
│  │                                                                   │ │
│  │ → Goal is ACTIONABLE! Add to docs/goals-and-gates.md            │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│      ↓                                                                  │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ Create BUILD.md with MVP Plan                                    │ │
│  │                                                                   │ │
│  │ Phase 1: Foundation (2 hours)                                    │ │
│  │   Milestone 1.1: JWT library setup (30 min)                     │ │
│  │   Milestone 1.2: Secret storage (1 hour)                        │ │
│  │   Checkpoint: Can generate & validate tokens?                   │ │
│  │                                                                   │ │
│  │ Phase 2: Core (4 hours)                                          │ │
│  │   Milestone 2.1: Login endpoint (2 hours)                       │ │
│  │   Milestone 2.2: Token refresh (2 hours)                        │ │
│  │   Checkpoint: Can users login & maintain sessions?              │ │
│  │                                                                   │ │
│  │ Phase 3: Polish (2 hours)                                        │ │
│  │   Milestone 3.1: Rate limiting (1 hour)                         │ │
│  │   Milestone 3.2: Logging & monitoring (1 hour)                  │ │
│  │   Checkpoint: Is auth production-ready?                         │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│      ↓                                                                  │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ Execute Build with Checkpoints                                   │ │
│  │                                                                   │ │
│  │ After each milestone:                                            │ │
│  │   🔍 CHECKPOINT: JWT library setup                               │ │
│  │   ✅ Completed: Installed PyJWT, created token generator         │ │
│  │   🧪 Verified: Generated test token, validated signature         │ │
│  │   ⚠️ Issues: None                                                │ │
│  │   📋 Spec Compliance: Meets entities.md JWT spec                 │ │
│  │   ➡️ Next: Milestone 1.2 (Secret storage)                        │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│      ↓                                                                  │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ Continuous Improvement (Stages 8-12)                             │ │
│  │                                                                   │ │
│  │ Stage 8: Audit evidence                                          │ │
│  │   • Login success rate: 95% (good!)                              │ │
│  │   • Token expiry issues: 5 reports (investigate)                 │ │
│  │                                                                   │ │
│  │ Stage 9: Re-inspect gaps                                         │ │
│  │   • New gap: Token expiry UX confusing                           │ │
│  │                                                                   │ │
│  │ Stage 10: Update epistemic state                                 │ │
│  │   • Close hypothesis: "OAuth sufficient" ✅                      │ │
│  │   • New hypothesis: "UX needs improvement"                       │ │
│  │                                                                   │ │
│  │ Stage 11: Verify end-to-end                                      │ │
│  │   • All specs met? Yes                                           │ │
│  │   • All gates still pass? Yes                                    │ │
│  │                                                                   │ │
│  │ Stage 12: Update docs                                            │ │
│  │   • Update BUILD.md with learnings                               │ │
│  │   • Add to CHANGELOG.md                                          │ │
│  │                                                                   │ │
│  │ → Loop back to Stage 8 for next iteration                        │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### When to Use the Epistemic Architect

**Perfect for:**
- ✅ **Greenfield projects** — Starting from scratch
- ✅ **Complex features** — Need rigorous analysis
- ✅ **High-stakes work** — Security, payments, data pipelines
- ✅ **Unclear requirements** — User says "I want X" but X is ambiguous
- ✅ **Multiple stakeholders** — Need to surface conflicting assumptions
- ✅ **Learning projects** — Want to understand deeply before building

**Not ideal for:**
- ❌ **Quick bug fixes** — Too much process for simple fixes
- ❌ **Well-defined tasks** — If requirements are crystal clear
- ❌ **Time pressure** — Need to ship in 30 minutes

### Integration with Code Puppy's Routing System

The Epistemic Architect integrates with Code Puppy's intelligent routing:

1. **Workload Type:** `ORCHESTRATOR` (high-level planning)
2. **Model Tier:** Prefers **T1 Architect** models (claude-sonnet-4-5, chatgpt-gpt-5.2-codex)
3. **Model Requirements:**
   - Minimum 32K context (for full epistemic state)
   - Preferred traits: reasoning, long_context, structured_output
4. **Failover Chain:** Uses ORCHESTRATOR chain in `failover_config.py` (lines 197-207)

```python
# From failover_config.py
"ORCHESTRATOR": [
    "claude-code-claude-sonnet-4-5",
    "antigravity-deepseek-v3-antigravity-org",
    "chatgpt-gpt-5.2-codex",
    # ... other orchestrator models
]
```

### Example Session

```bash
# Switch to epistemic architect
/agent epistemic-architect

# User describes project
> I want to build a task management app

# Epistemic Architect guides through interview
> Great! Let's start with the epistemic state interview:
> 
> 1. What problem are you solving? Who are your users?
> 2. What are you assuming is true about task management?
> 3. What would prove you wrong?
> 4. What are your hard constraints (non-negotiable)?
> 5. What are your soft constraints (preferences)?
> 6. What evidence do you already have?

# After interview, applies 7 lenses
> I've applied all 7 lenses. Here's what I found:
> 
> 🔴 CRITICAL Gaps:
>   • No clear definition of "task" (Philosophy lens)
>   • No metrics for success (Data Science lens)
> 
> 🟠 HIGH Gaps:
>   • Missing data persistence strategy (Systems lens)
>   • No user authentication plan (Safety lens)

# User addresses gaps, architect generates goals
> Based on the updated state, I've generated 3 candidate goals.
> All 3 passed the 6 quality gates! ✅
> 
> Goal 1: "Define task entity with 5 core attributes"
> Goal 2: "Implement SQLite persistence layer"
> Goal 3: "Create basic CRUD API endpoints"
> 
> Ready to create BUILD.md?

# Architect creates project structure
> I've scaffolded your project:
> 
> task-manager/
> ├── epistemic/          (your assumptions & hypotheses)
> ├── docs/               (lens evaluations & gaps)
> ├── specs/              (entities, personas, flows)
> └── BUILD.md            (8-hour plan with checkpoints)
> 
> Let's start with Phase 1: Foundation...

# During build, can invoke other agents
> For the API security review, I'll invoke the security-auditor agent...
> 
> invoke_agent("security-auditor", "Review auth implementation in src/auth.py")
> 
> Security auditor found 2 issues. Let me address them...

# After each milestone, checkpoints
> 🔍 CHECKPOINT: SQLite persistence layer
> ✅ Completed: Database schema, CRUD operations
> 🧪 Verified: All tests pass (12/12)
> ⚠️ Issues: None
> 📋 Spec Compliance: Meets entities.md spec ✅
> ➡️ Next: Milestone 2.2 (API endpoints)

# Continuous improvement loop
> We've completed Phase 2. Let's audit:
> 
> Evidence collected:
>   • API response times: 50-200ms (good!)
>   • Test coverage: 85% (target: 80%+)
>   • Code review: 2 minor issues
> 
> New gap identified:
>   • No pagination on task list endpoint
> 
> Updating epistemic state...
> Creating improvement plan...
> 
> Ready for Phase 3?
```

### Tools Available to Epistemic Architect

| Tool | Purpose |
|------|---------|
| `list_files` | Explore existing codebase |
| `read_file` | Read files for context |
| `grep` | Search within files |
| `edit_file` | Create/modify files (epistemic artifacts, specs) |
| `agent_run_shell_command` | Scaffold projects, run tests |
| `agent_share_your_reasoning` | Explain thought process (critical for transparency) |
| `list_agents` | Discover available agents for delegation |
| `invoke_agent` | Delegate to specialists (helios, agent-creator, etc.) |

### Key Principles

1. **The Loop is Invariant** — Everything is a Ralph loop (Observe → Orient → Decide → Act → Observe)
2. **Goals are Outputs, Not Inputs** — Goals emerge from evidence, not assumptions
3. **Epistemic Humility** — Track confidence (0.0-1.0), be ready to update beliefs
4. **Explainability** — Every decision traces to evidence in epistemic/state.json
5. **Pause is Valid** — Refusal and hand-off are first-class operations
6. **Don't Block on Uncontrollables** — Build measurement, not outcomes
7. **Small Reversible Steps** — Prefer many small milestones over big leaps

### Related Files

| File | Lines | Purpose |
|------|-------|---------|
| [agent_epistemic_architect.py](../code_puppy/agents/agent_epistemic_architect.py) | 387 | Main agent implementation |
| [epistemic/ (template)](../code_puppy/epistemic/) | — | Epistemic project template (Git submodule) |
| [agent_tools.py](../code_puppy/tools/agent_tools.py) | 764 | Agent coordination tools (invoke_agent, list_agents) |
| [agent_helios.py](../code_puppy/agents/agent_helios.py) | 123 | Universal Constructor agent (creates tools) |
| [agent_creator_agent.py](../code_puppy/agents/agent_creator_agent.py) | 630 | Agent creation specialist |

### Further Reading

- **Epistemic Project Template:** `/code_puppy/epistemic/` (Git submodule: [duz10/epistemic-project-template](https://github.com/duz10/epistemic-project-template))
- **Ralph Loops:** `/code_puppy/epistemic/philosophy/project-plan.md`
- **EAR Audit Loop:** `/code_puppy/epistemic/process/ear-audit-loop.md`
- **Build Methodology:** `/code_puppy/epistemic/process/build-methodology.md`

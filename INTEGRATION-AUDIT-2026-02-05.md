# Integration Audit: External Agent Frameworks

**Date**: February 5, 2026  
**Author**: GitHub Copilot (Claude Opus 4.5)  
**Status**: Analysis Complete - Implementation Recommendations

---

## Executive Summary

This audit analyzes 5 external projects for integration potential with Code Puppy:

| Project | Relevance | Priority | Effort |
|---------|-----------|----------|--------|
| [pai-agent-sdk](#1-pai-agent-sdk) | 🔴 High | P1 | Medium |
| [Context Compaction API](#2-context-compaction-api-pydantic-ai-4137) | 🔴 Critical | P0 | Low |
| [DBOS Transact](#3-dbos-transact-py) | 🟡 Medium | P2 | High |
| [GEPA](#4-gepa) | 🟢 Low | P3 | Medium |
| [pydantic-deepagents](#5-pydantic-deepagents) | 🟡 Medium | P2 | Low |

**Key Recommendation**: The Context Compaction API (#4137) should be implemented immediately as Code Puppy already has infrastructure for this. The pai-agent-sdk patterns should be adopted for environment abstraction and skills system.

---

## 1. PAI Agent SDK

**Repository**: https://github.com/youware-labs/pai-agent-sdk  
**Version**: v0.16.1 (released 9 hours ago)  
**Stars**: 12 | License: BSD-3-Clause

### What It Is

PAI (Paintress/Pydantic AI) is an application framework for building AI agents on top of Pydantic AI. Built for YouWare's next-generation agent system.

### Key Features

| Feature | Description | Code Puppy Equivalent |
|---------|-------------|----------------------|
| **Environment-based Architecture** | Protocol-based file/shell access (Local, Docker, SSH, S3) | ✅ Have file tools, need abstraction |
| **Resumable Sessions** | Export/restore `AgentContext` across restarts | ✅ `session_storage.py` |
| **Hierarchical Agents** | Subagent task delegation with tool inheritance | ✅ `subagent_stream_handler.py` |
| **Skills System** | Markdown-based instruction files with hot reload | ⚠️ Partial - need YAML frontmatter |
| **Human-in-the-Loop** | Approval workflows for sensitive operations | ❌ Not implemented |
| **Toolset Architecture** | Pre/post hooks for logging, validation, error handling | ✅ `callbacks.py` system |
| **Resumable Resources** | Export/restore browser sessions across restarts | ❌ Not implemented |
| **Message Bus** | Inter-agent communication | ✅ `messaging/` module |

### Integration Opportunities

#### Priority 1: Human-in-the-Loop (HITL) Approval System

Code Puppy lacks built-in tool approval workflows for sensitive operations.

```python
# PAI Pattern - HITL Approval
from pai_agent_sdk.toolset import Toolset, Tool

class FileToolset(Toolset):
    @Tool(requires_approval=True)  # <-- Key feature
    async def delete_file(self, path: str) -> str:
        """Delete a file (requires human approval)."""
        ...
```

**Implementation Path**:
1. Add `requires_approval: bool = False` to tool decorators
2. Integrate with existing `callbacks.py` event system
3. Create approval prompts in CLI/TUI

#### Priority 2: Skills System with YAML Frontmatter

PAI uses markdown files with YAML frontmatter for skills:

```markdown
---
name: code-review
description: Python code quality review
triggers:
  - "review"
  - "check code"
---

# Code Review Skill

Check for:
- Security issues
- Type hints
- Error handling
```

**Current Code Puppy**: Has prompts in `prompts/` but lacks:
- YAML metadata for skill discovery
- Hot reload capability
- Progressive loading

#### Priority 3: Environment Abstraction

PAI's Environment protocol allows transparent switching between:
- `LocalEnvironment` - Direct filesystem access
- `DockerEnvironment` - Sandboxed execution
- Custom backends (SSH, S3, cloud VMs)

**Value**: Enables safe code execution in isolated containers.

### Recommended Actions

1. **Adopt HITL Pattern** - Add `requires_approval` to tool definitions
2. **Enhance Skills System** - Add YAML frontmatter support
3. **Monitor for Merger** - PAI may eventually merge with pydantic-ai upstream

---

## 2. Context Compaction API (pydantic-ai #4137)

**Issue**: https://github.com/pydantic/pydantic-ai/issues/4137  
**Milestone**: 2026-02 (This month!)  
**Status**: Open, actively discussed, @mpfaffenberger commented

### What It Is

A proposed first-class API for automatic context compaction in pydantic-ai. Triggers summarization when token usage exceeds thresholds.

### Proposed API

```python
from pydantic_ai import Agent

class CompactionSettings(BaseModel):
    token_threshold: int  # Trigger compaction when exceeded
    enabled: bool = True
    summarization_model: str | None = None
    summary_prompt: str | None = None
    pre_compaction_hook: CompactionHook | None = None
    post_compaction_hook: CompactionHook | None = None

agent = Agent(
    'anthropic:claude-sonnet-4-5',
    compaction=CompactionSettings(
        token_threshold=80_000,
        summarization_model='anthropic:claude-haiku-4-5',
    )
)
```

### Code Puppy Current State

**Already Implemented** (in `base_agent.py` and `summarization_agent.py`):

```python
# code_puppy/agents/base_agent.py
def message_history_processor(
    self, messages: list[ModelMessage]
) -> list[ModelMessage]:
    """Process message history, potentially compacting if over threshold."""
    ...

# code_puppy/settings.py
compaction_threshold: float = Field(
    default=0.7,
    description="Context utilization threshold triggering compaction (0.5-0.95)",
)
```

### Gap Analysis

| Feature | Proposed API | Code Puppy | Status |
|---------|--------------|------------|--------|
| Automatic triggering | ✅ `token_threshold` | ✅ `compaction_threshold` | ✅ Implemented |
| Separate summarization model | ✅ `summarization_model` | ❌ Uses same model | 🔧 Need to add |
| Pre-compaction hook | ✅ `pre_compaction_hook` | ⚠️ Callbacks exist | 🔧 Adapt to hooks |
| Post-compaction hook | ✅ `post_compaction_hook` | ⚠️ Callbacks exist | 🔧 Adapt to hooks |
| Tool call pairing protection | ✅ `tool_call_pairs` | ❌ Not tracked | 🔧 Need to add |
| Protected tokens | ❓ Discussed in comments | ❌ Not implemented | 🔧 @mpfaffenberger suggestion |

### @mpfaffenberger's Suggestions (Your Comments!)

1. **Validate model capacity** - Ensure compaction threshold < context limit
2. **Protected tokens** - Keep last N tool calls or specific tool types
3. **Truncation alternative** - Fast/cheap option with protected tokens
4. **Keep first user prompt** - Never summarize initial context
5. **ThinkingPart preservation** - Don't squish thinking signatures

### Recommended Implementation

```python
# code_puppy/core/compaction.py (NEW)

@dataclass
class CompactionSettings:
    """Context compaction settings following pydantic-ai #4137 proposal."""
    
    token_threshold: int = 80_000
    protected_tokens: int = 30_000  # @mpfaffenberger suggestion
    summarization_model: str | None = None
    enabled: bool = True
    
    # Hooks
    pre_compaction_hook: Callable | None = None
    post_compaction_hook: Callable | None = None
    
    # Safety
    preserve_first_user_prompt: bool = True
    preserve_thinking_parts: bool = True  # Claude/GPT thinking
    
    def validate(self):
        """Validate settings are sensible."""
        if self.token_threshold <= self.protected_tokens:
            raise ValueError(
                f"token_threshold ({self.token_threshold}) must be > "
                f"protected_tokens ({self.protected_tokens})"
            )
        ratio = self.token_threshold / self.protected_tokens
        if ratio < 1.5:
            warnings.warn(
                f"Ratio of threshold:protected ({ratio:.2f}) is < 1.5, "
                "may cause frequent compaction"
            )
```

### Priority: P0 - CRITICAL

This is in the 2026-02 milestone, and Code Puppy can be ready with a compatible implementation before upstream merges.

---

## 3. DBOS Transact-py

**Repository**: https://github.com/dbos-inc/dbos-transact-py  
**Version**: 2.11.0  
**Stars**: 1.2k | License: MIT

### What It Is

Lightweight durable workflows built on Postgres. Checkpoints program state in database, automatically resumes from failures.

### Key Features

```python
from dbos import DBOS

@DBOS.step()
def step_one():
    """Checkpointed step - won't re-run on resume."""
    ...

@DBOS.step()
def step_two():
    ...

@DBOS.workflow()
def workflow():
    step_one()
    step_two()  # If crash here, step_one won't re-run
```

### Use Case for Code Puppy

| Scenario | Benefit |
|----------|---------|
| Long-running agent loops | Resume from last checkpoint on crash |
| Multi-step tool execution | Don't re-execute completed steps |
| API calls to external services | Exactly-once semantics |
| Scheduled agent runs | Durable scheduling with recovery |

### Integration Complexity

**High** - Requires:
1. PostgreSQL database (or SQLite)
2. Decorator changes to all tools and agent steps
3. Session state changes to checkpoint-compatible format

### Recommended Approach

Don't integrate directly. Instead:

1. **Monitor for pydantic-ai integration** - DBOS may add pydantic-ai support
2. **Use existing session persistence** - Code Puppy's `session_storage.py` already handles state
3. **Consider for specific workflows** - Agent scheduler could benefit

### Priority: P2 - Medium

Wait for ecosystem maturation. Current session storage is sufficient.

---

## 4. GEPA (Genetic-Pareto Prompt Evolution)

**Repository**: https://github.com/gepa-ai/gepa  
**Version**: v0.0.27  
**Stars**: 2.2k | License: MIT

### What It Is

Framework for optimizing AI prompts and code through reflective text evolution. Uses LLMs to analyze execution traces and evolve better prompts.

### How It Works

```python
import gepa

# Optimize system prompt for math problems
gepa_result = gepa.optimize(
    seed_candidate={"system_prompt": "You are a helpful assistant..."},
    trainset=trainset,
    valset=valset,
    task_lm="openai/gpt-4.1-mini",
    max_metric_calls=150,
    reflection_lm="openai/gpt-5",  # Strong model for reflection
)

print("Optimized:", gepa_result.best_candidate['system_prompt'])
```

### Use Cases for Code Puppy

| Use Case | Benefit |
|----------|---------|
| Agent prompt optimization | Auto-tune prompts for specific tasks |
| Tool description improvement | Better tool selection by models |
| Error handling prompt tuning | Reduce validation failures |

### Integration Approach

GEPA works via adapters. Code Puppy could create a `CodePuppyAdapter`:

```python
# code_puppy/optimization/gepa_adapter.py

class CodePuppyAdapter(GEPAAdapter):
    """GEPA adapter for optimizing Code Puppy agent prompts."""
    
    def evaluate(self, candidate: dict, inputs: list) -> EvaluationResult:
        """Run agent with candidate prompts and collect metrics."""
        ...
    
    def extract_traces(self, traces, component: str) -> str:
        """Extract relevant traces for component optimization."""
        ...
```

### Priority: P3 - Low

Nice to have for prompt engineering, but not critical for operations.

---

## 5. Pydantic DeepAgents

**Repository**: https://github.com/vstorm-co/pydantic-deepagents  
**Version**: 0.2.14  
**Stars**: 266 | License: MIT

### What It Is

Framework for building "Claude Code-style" agents with planning, filesystem, subagents, skills, and summarization - all built on pydantic-ai.

### Key Features

```python
from pydantic_deep import create_deep_agent, create_default_deps

agent = create_deep_agent()
deps = create_default_deps(StateBackend())

result = await agent.run("Create a todo list for building a REST API", deps=deps)
```

### Feature Comparison

| Feature | pydantic-deepagents | Code Puppy | Notes |
|---------|---------------------|------------|-------|
| Planning/Todo | ✅ pydantic-ai-todo | ✅ Agent planning | Similar |
| Filesystem | ✅ pydantic-ai-backend | ✅ file/edit tools | Similar |
| Subagents | ✅ subagents-pydantic-ai | ✅ Subagent system | Similar |
| Summarization | ✅ summarization-pydantic-ai | ✅ summarization_agent.py | Similar |
| Skills | ✅ YAML frontmatter | ⚠️ Basic prompts | Upgrade needed |
| Structured Output | ✅ output_type | ✅ Agent output types | Similar |
| Human-in-the-Loop | ✅ Built-in | ❌ Missing | Add this |
| Docker Sandbox | ✅ Docker backend | ❌ Local only | Add this |

### Key Pattern to Adopt

**Context Management with Token Triggers**:

```python
from pydantic_deep import create_summarization_processor

processor = create_summarization_processor(
    trigger=("tokens", 100000),  # Token-based trigger
    keep=("messages", 20),       # Keep recent messages
)
agent = create_deep_agent(history_processors=[processor])
```

### Integration Recommendation

**Don't adopt the framework** - Code Puppy already has similar architecture.

**Adopt specific patterns**:
1. Summarization trigger API
2. Skill YAML frontmatter format
3. Human-in-the-loop confirmation workflow

### Priority: P2 - Medium

Use as reference implementation for improvements.

---

## Implementation Roadmap

### Phase 1: Context Compaction (Week 1)

**Align with pydantic-ai #4137**

1. Create `code_puppy/core/compaction.py`:
   - `CompactionSettings` dataclass
   - `CompactionContext` with tool call pairs
   - Pre/post hooks

2. Update `base_agent.py`:
   - Accept `compaction` parameter
   - Integrate with existing `message_history_processor`

3. Add protected tokens support:
   - Keep last N tool calls
   - Preserve first user prompt
   - Don't squish ThinkingPart

### Phase 2: Skills System Enhancement (Week 2)

**Adopt PAI/DeepAgents pattern**

1. Add YAML frontmatter support to prompts:
   ```markdown
   ---
   name: code-review
   description: Review code for quality
   triggers: ["review", "check"]
   ---
   ```

2. Implement skill discovery and loading

3. Add hot reload for development

### Phase 3: Human-in-the-Loop (Week 3)

**Adopt PAI pattern**

1. Add `requires_approval` to tool decorators
2. Create approval callback hooks
3. Implement CLI/TUI approval prompts

### Phase 4: Environment Abstraction (Week 4)

**Adopt PAI pattern for sandboxing**

1. Create `Environment` protocol
2. Implement `LocalEnvironment`
3. Implement `DockerEnvironment` for safe code execution

---

## Dependencies to Add

```toml
# pyproject.toml additions

[project.optional-dependencies]
compaction = [
    "tiktoken>=0.5.0",  # Token counting
]
gepa = [
    "gepa>=0.0.27",  # Prompt optimization
]
dbos = [
    "dbos>=2.11.0",  # Durable workflows
]
sandbox = [
    "docker>=7.0.0",  # Docker sandbox
]
```

---

## Summary

### Immediate Actions (This Week)

1. **Implement CompactionSettings** aligned with #4137
2. **Add protected_tokens support** per @mpfaffenberger's suggestions
3. **Prepare PR for pydantic-ai** once upstream API stabilizes

### Medium-term Actions (This Month)

1. **YAML frontmatter for skills**
2. **Human-in-the-loop approval**
3. **Docker sandbox environment**

### Long-term Monitoring

1. **PAI Agent SDK** - May merge patterns with pydantic-ai
2. **DBOS** - Watch for pydantic-ai integration
3. **GEPA** - Consider for production prompt tuning

---

## References

- [PAI Agent SDK](https://github.com/youware-labs/pai-agent-sdk)
- [pydantic-ai #4137 - Context Compaction](https://github.com/pydantic/pydantic-ai/issues/4137)
- [DBOS Transact](https://github.com/dbos-inc/dbos-transact-py)
- [GEPA](https://github.com/gepa-ai/gepa)
- [pydantic-deepagents](https://github.com/vstorm-co/pydantic-deepagents)
- [pai-agent-sdk compact.py](https://github.com/youware-labs/pai-agent-sdk/blob/main/pai_agent_sdk/agents/compact.py)

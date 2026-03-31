# Recommendations for Code Puppy Orchestra Plugin

## Executive Summary

Based on comprehensive research into Steve Yegge's multi-agent systems (Gastown, Beads, VC), here are prioritized recommendations for enhancing Code Puppy's Orchestra plugin.

---

## High Priority Recommendations

### 1. Implement Git Hook Persistence (The Propulsion Principle)

**What**: Use git worktrees for persistent agent state storage

**Why**:
- Work survives agent restarts
- Version control of all changes
- Multi-agent coordination through shared git
- Rollback capability

**Implementation**:
```python
# When spawning an agent, create a git worktree
class AgentHook:
    def __init__(self, rig_name: str, agent_name: str):
        self.worktree_path = f"~/gt/{rig_name}/hooks/{agent_name}"
        
    def create(self, base_branch: str = "main"):
        # git worktree add <path> <branch>
        pass
        
    def archive(self):
        # Preserve worktree but mark inactive
        pass
```

**For Orchestra**:
- `/spawn` should create hooks automatically
- `/hook` command to check what's on agent's hook
- `/done` command to complete work and cleanup

---

### 2. Two-Level Beads Architecture

**What**: Separate town-level (cross-project) from rig-level (project) tracking

**Current Orchestra**: Has `/rig` but no clear two-level separation

**Recommended Structure**:
```
~/.code_puppy/orchestra/           # Town-level
├── beads/                         # Cross-project issues
│   └── (Mayor coordination, etc.)
└── state/                         # Global state

./                                # Rig-level (current directory)
├── .orchestra/                    # Project issues
│   ├── hooks/                     # Agent hooks
│   └── state/                     # Project state
└── .beads/                        # Beads database
```

**Implementation**:
- Town-level beads: `hq-*` prefix
- Rig-level beads: project prefix (e.g., `cp-*`)
- Mayor operates at town level
- Witness/Refinery at rig level

---

### 3. Agent Taxonomy & Roles

**What**: Define clear agent roles with specific responsibilities

**Recommended Roles for Orchestra**:

| Role | Scope | Responsibility |
|------|-------|----------------|
| **Mayor** | Town | Cross-project coordination, orchestration |
| **Witness** | Rig | Per-project agent health monitoring |
| **Refinery** | Rig | Merge queue processing |
| **Polecat** | Task | Ephemeral worker agents |
| **Crew** | User | Human developer workspace |

**Implementation**:
```python
# In Orchestra plugin
AGENT_ROLES = {
    "mayor": {
        "scope": "town",
        "persistent": True,
        "commands": ["/spawn", "/convoy", "/escalate"]
    },
    "witness": {
        "scope": "rig", 
        "persistent": True,
        "commands": ["/nudge", "/handoff"]
    },
    "polecat": {
        "scope": "task",
        "persistent": False,
        "commands": ["/done"]
    }
}
```

---

### 4. GUPP Implementation

**What**: Gas Town Universal Propulsion Principle - autonomous execution

**Principle**: "If there is work on your Hook, YOU MUST RUN IT"

**Implementation**:
```python
# Agent session startup
async def agent_startup(agent_id: str):
    hook = get_hook(agent_id)
    if hook.has_work():
        # Auto-execute without waiting for prompt
        work = hook.get_work()
        await execute_work(agent_id, work)
    else:
        # Wait for assignment
        await wait_for_work(agent_id)
```

**For Orchestra**:
- Agents auto-execute work on their hook
- `/nudge` command to prompt stuck agents
- `/handoff` to refresh agent context
- Problems view to detect GUPP violations

---

### 5. Convoy-Based Work Tracking

**What**: Bundle related work items into trackable convoys

**Current Orchestra**: Has `/convoy create` but limited functionality

**Enhancements**:
```bash
# Create convoy with dependencies
/convoy create "Auth System" \
  --beads "bd-1,bd-2,bd-3" \
  --dependencies "bd-2->bd-1,bd-3->bd-1" \
  --priority 0 \
  --notify

# Add work to existing convoy
/convoy add <convoy-id> bd-4

# Monitor progress
/convoy show <convoy-id>
/feed --convoy <convoy-id>

# Mountain convoys (epic-scale)
/convoy create "Major Refactor" \
  --beads "bd-epic-1,..." \
  --label mountain
```

---

## Medium Priority Recommendations

### 6. Escalation Protocol

**What**: Structured severity-based routing for blockers

**Implementation**:
```python
ESCALATION_LEVELS = {
    "MEDIUM": {
        "routes": ["bead", "mail:mayor"],
        "timeout": "4h"
    },
    "HIGH": {
        "routes": ["bead", "mail:mayor", "notify:user"],
        "timeout": "1h"
    },
    "CRITICAL": {
        "routes": ["bead", "mail:mayor", "notify:user", "notify:admin"],
        "timeout": "15m"
    }
}
```

**Commands**:
```bash
/escalate -s HIGH "Database connection failing"
/escalate list
/escalate ack <bead-id>
/escalate close <bead-id> --reason "Fixed"
```

---

### 7. Scheduler & Capacity Management

**What**: Config-driven capacity control to prevent resource exhaustion

**Implementation**:
```python
class Scheduler:
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.queue = []
        
    async def schedule(self, bead_id: str, rig: str):
        if len(self.active) < self.max_concurrent:
            await self.dispatch(bead_id, rig)
        else:
            self.queue.append((bead_id, rig))
            
    async def dispatch(self, bead_id: str, rig: str):
        # Spawn polecat with bead
        pass
```

**Commands**:
```bash
/config set scheduler.max_agents 5
/scheduler status
/scheduler pause
/scheduler resume
```

---

### 8. Three-Tier Watchdog System

**What**: Health monitoring with automated recovery

**Architecture**:
```
Code Puppy Core (heartbeat every 3 min)
    └── Boot Agent (checks Deacon health)
        └── Deacon Agent (cross-project patrol)
            └── Witness Agents (per-project)
                └── Worker Agents (Polecats)
```

**Health States**:
| State | Condition | Action |
|-------|-----------|--------|
| Working | Normal progress | Monitor |
| Stalled | Reduced progress | Nudge |
| GUPP Violation | No progress | Handoff |
| Zombie | Dead session | Restart |

**Implementation**:
```python
class Watchdog:
    async def check_health(self, agent_id: str):
        agent = get_agent(agent_id)
        state = agent.get_state()
        
        if state.no_progress_for > THRESHOLD:
            await self.nudge(agent_id)
        elif state.session_dead:
            await self.restart(agent_id)
```

---

### 9. Formula/Molecule System

**What**: Reusable workflow templates

**Implementation**:
```toml
# .orchestra/formulas/tdd.formula.toml
description = "TDD development cycle"
formula = "tdd"
version = 1

[vars.feature]
description = "Feature to implement"
required = true

[[steps]]
id = "red"
title = "Write failing test"

[[steps]]
id = "green"
title = "Make test pass"
needs = ["red"]

[[steps]]
id = "refactor"
title = "Refactor"
needs = ["green"]
```

**Commands**:
```bash
/formula list
/formula cook tdd --var feature="user-profile"
/formula pour release --var version="1.2.0"
```

---

## Low Priority Recommendations

### 10. Wasteland Federation (Future)

**What**: Cross-instance work coordination

**Use Case**: Multiple Code Puppy instances sharing work

**Future Implementation**:
```bash
/wasteland join <community>
/wasteland browse
/wasteland claim <work-id>
/wasteland done <work-id> --evidence <url>
```

---

### 11. Seance (Session Continuation)

**What**: Query previous agent sessions for context

**Implementation**:
```python
class Seance:
    def list_sessions(self, rig: str) -> List[Session]:
        # Read .events.jsonl logs
        pass
        
    async def query(self, session_id: str, question: str) -> str:
        # Use LLM to answer based on session logs
        pass
```

**Commands**:
```bash
/seance list
/seance talk <session-id>
/seance ask <session-id> "What did you find?"
```

---

## Integration with Code Puppy

### Lifecycle Hooks

Use Code Puppy's plugin system:

```python
# In orchestra/register_callbacks.py
from code_puppy.callbacks import register_callback

@register_callback("startup")
async def on_startup():
    """Initialize Orchestra town directory."""
    await initialize_town()

@register_callback("agent_run_start")
async def on_agent_start(agent_name, model_name, session_id):
    """Check agent's hook and auto-execute if work exists (GUPP)."""
    await check_and_execute_hook(agent_name)

@register_callback("post_tool_call")
async def on_tool_call(tool_name, tool_args, result, duration_ms):
    """Log agent activity for monitoring."""
    await log_activity(tool_name, duration_ms)
```

### Command Registration

```python
@register_callback("custom_command")
def handle_orchestra_command(command: str, name: str):
    """Handle Orchestra slash commands."""
    commands = {
        "rig": handle_rig_command,
        "spawn": handle_spawn_command,
        "convoy": handle_convoy_command,
        "hook": handle_hook_command,
        "done": handle_done_command,
        "escalate": handle_escalate_command,
    }
    
    if name in commands:
        return commands[name](command)
    return None
```

---

## Implementation Priority Matrix

| Feature | Impact | Effort | Priority |
|---------|--------|--------|----------|
| Git Hook Persistence | High | Medium | **P0** |
| Two-Level Beads | High | Medium | **P0** |
| Agent Taxonomy | High | Low | **P0** |
| GUPP Implementation | High | Low | **P0** |
| Convoy Enhancements | High | Medium | **P1** |
| Escalation Protocol | Medium | Medium | **P1** |
| Scheduler | Medium | Medium | **P1** |
| Watchdog System | Medium | High | **P1** |
| Formula System | Medium | High | **P2** |
| Wasteland | Low | High | **P3** |
| Seance | Low | Medium | **P3** |

---

## Quick Wins (Can Implement Immediately)

1. **Agent Roles**: Define constants and validation
2. **GUPP Flag**: Add config option for auto-execution
3. **Hook Command**: Simple `/hook` to check status
4. **Convoy Labels**: Add `--label` support
5. **Escalate Command**: Basic severity-based routing

---

## Long-Term Vision

Full Orchestra implementation should provide:

1. **Autonomous Agents**: Self-driving work execution (GUPP)
2. **Persistent State**: Git-based work preservation
3. **Intelligent Coordination**: Mayor orchestration
4. **Health Monitoring**: Three-tier watchdog
5. **Quality Gates**: Automated validation
6. **Federation**: Cross-instance collaboration

---

## Resources

### Key Files from Research
- `README.md` - Executive summary
- `architectural-patterns.md` - Detailed patterns
- `design-principles.md` - MEOW, GUPP, NDI, ZFC
- `key-concepts.md` - Beads, Convoys, Hooks, etc.
- `orchestration-best-practices.md` - Usage patterns
- `sources.md` - Credibility assessment

### External References
- https://github.com/steveyegge/gastown
- https://github.com/gastownhall/beads
- https://github.com/steveyegge/vc

---

*Recommendations based on research by Web-Puppy  
Date: March 31, 2026  
Confidence: High (based on official documentation)*

# Code Puppy × Gastown × Beads Hybrid Architecture

> "The best of all worlds: Python agility, Go orchestration, TypeScript UI patterns, and Dolt persistence."

## Vision

Create a unified AI coding agent platform that combines:
- **Code Puppy's** extensible Python plugin architecture and tool system
- **Gastown's** sophisticated multi-agent orchestration (Mayor, Polecats, Convoys, Formulas)
- **Beads'** distributed graph issue tracking with Dolt
- **Claude-code's** UI patterns and comprehensive tooling
- **Dolt's** version-controlled data capabilities

## Core Philosophy

1. **Plugins Over Core** - Everything lives in `code_puppy/plugins/`
2. **Python Foundation** - Keep the runtime Python (easier hacking, rich ecosystem)
3. **External Binaries** - Use Go binaries (beads, dolt) where they excel
4. **Event-Driven** - Everything communicates via callbacks/events
5. **Git-Native** - Work survives restarts through git-backed persistence

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CODE PUPPY HYBRID                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   ORCHESTRA  │  │    BEADS     │  │   DASHBOARD  │  │   FORMULAS   │   │
│  │   (Gastown)  │  │  (Tracking)  │  │    (TUI)     │  │ (Workflows)  │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                 │                 │                 │            │
│         └─────────────────┴─────────────────┴─────────────────┘            │
│                                    │                                        │
│                         ┌──────────▼──────────┐                           │
│                         │   LIFECYCLE HOOKS   │  ← callbacks.py           │
│                         └──────────┬──────────┘                           │
│                                    │                                        │
│  ┌──────────────┐  ┌──────────────┼──────────────┐  ┌──────────────┐       │
│  │   CORE AGENT │  │   TOOLS      │   MODELS     │  │  EXISTING    │       │
│  │   (pydantic) │  │  (~40 tools) │ (multi-prov) │  │  PLUGINS     │       │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         │                          │                          │
    ┌────▼────┐               ┌─────▼─────┐              ┌────▼────┐
    │  DOLT   │               │   BEADS   │              │   GIT   │
    │ (data)  │               │  (issues) │              │ (work)  │
    └─────────┘               └───────────┘              └─────────┘
```

## New Plugin Structure

### 1. `orchestra/` - Multi-Agent System (Gastown-inspired)

**Roles (from Gastown):**
- **Mayor** - Primary AI coordinator, your main interface
- **Polecat** - Ephemeral worker agents for specific tasks
- **Crew** - Your personal workspace
- **Witness** - Per-project health monitor
- **Deacon** - Cross-project supervisor
- **Dog** - Infrastructure/maintenance tasks

**Key Concepts:**
- **Rigs** - Project containers wrapping git repos
- **Hooks** - Git worktree-based persistent storage
- **Convoys** - Work tracking units bundling multiple tasks
- **Mail** - Inter-agent messaging system
- **Formulas** - TOML-defined reusable workflows

```
code_puppy/plugins/orchestra/
├── register_callbacks.py      # Lifecycle hooks
├── models.py                  # Role definitions, AgentState
├── rig.py                     # Project container management
├── hook_manager.py            # Git worktree persistence
├── convoy.py                  # Work bundling/tracking
├── mail_system.py             # Inter-agent messaging
├── mayor/                     # Mayor-specific logic
├── polecat/                   # Worker agent spawning
├── witness/                   # Health monitoring
├── deacon/                    # Cross-project supervision
└── formulas/                  # Workflow templates
```

### 2. `beads_tracker/` - Enhanced Beads Integration

Full integration with `bd` CLI for:
- Issue/bead creation and tracking
- Dependency management (`bd dep add`)
- Ready task detection (`bd ready`)
- Claiming and assignment
- Hierarchy support (epics → tasks → subtasks)

```
code_puppy/plugins/beads_tracker/
├── register_callbacks.py
├── integration.py             # bd CLI wrapper
├── sync.py                    # Bidirectional sync
├── hooks.py                   # Beads event hooks
└── templates/                 # Bead templates
```

### 3. `formulas/` - Workflow System

TOML-based workflow definitions that can:
- Define multi-step processes
- Execute formulas via `bd cook` or `bd mol pour`
- Track progress with checkpoint recovery
- Support both root-only (lightweight) and poured (checkpointed) modes

```
code_puppy/plugins/formulas/
├── register_callbacks.py
├── parser.py                  # TOML formula parsing
├── executor.py                # Formula execution
├── registry.py                # Available formulas
└── formulas/
    ├── code_review.toml
    ├── design_doc.toml
    ├── release.toml
    └── tdd_cycle.toml
```

### 4. `dashboard/` - TUI Dashboard

Interactive terminal dashboard for monitoring:
- Agent tree (hierarchical view)
- Convoy panel (in-progress work)
- Event stream (real-time activity)
- Problems view (stuck agents, GUPP violations)

```
code_puppy/plugins/dashboard/
├── register_callbacks.py
├── tui/
│   ├── __init__.py
│   ├── components.py          # Rich-based components
│   ├── layout.py              # Panel layout
│   └── events.py              # Event handling
├── views/
│   ├── agents.py              # Agent tree view
│   ├── convoys.py             # Convoy panel
│   ├── feed.py                # Event stream
│   └── problems.py            # Health view
└── keys.py                    # Keybindings
```

### 5. `shell_orchestrator/` - Shell Session Management

Enhanced shell safety + session management:
- Worktree-based shell isolation
- Session persistence via hooks
- Command history in git
- Automatic context recovery

```
code_puppy/plugins/shell_orchestrator/
├── register_callbacks.py
├── worktree.py                # Git worktree management
├── session.py                 # Shell session persistence
├── context.py                 # Context capture/recovery
└── history.py                 # Command history tracking
```

### 6. `dolt_integration/` - Database Layer

Optional Dolt integration for:
- Agent state persistence
- Message history storage
- Work tracking database
- Schema versioning

```
code_puppy/plugins/dolt_integration/
├── register_callbacks.py
├── client.py                  # Dolt SQL client
├── schema.py                  # Database schemas
├── migrations/                # Schema migrations
└── models/                    # Data models
```

## Lifecycle Hooks Integration

The hybrid extends Code Puppy's callback system:

```python
# New hooks to add to callbacks.py:

# Agent orchestration
register_callback("agent_spawn", on_agent_spawn)        # New agent created
register_callback("agent_complete", on_agent_complete)  # Agent finished
register_callback("agent_handoff", on_agent_handoff)    # Work transferred
register_callback("convoy_create", on_convoy_create)    # New convoy created
register_callback("convoy_complete", on_convoy_complete) # Convoy finished

# Beads integration
register_callback("bead_created", on_bead_created)      # New bead/issue
register_callback("bead_claimed", on_bead_claimed)      # Bead assigned
register_callback("bead_closed", on_bead_closed)        # Bead completed

# Formula execution
register_callback("formula_start", on_formula_start)    # Formula begins
register_callback("formula_step", on_formula_step)      # Step completed
register_callback("formula_complete", on_formula_done)  # Formula done

# Dashboard/TUI
register_callback("dashboard_render", on_dashboard)     # Dashboard tick
register_callback("feed_event", on_feed_event)          # New feed item
```

## Data Flow

### Creating a New Feature (Example Flow)

```
1. User tells Mayor: "Build auth system"
   ↓
2. Mayor creates convoy with beads:
   - bd create "Auth Epic" → gt-auth1
   - bd create "Login page" -p gt-auth1 → gt-auth1.1
   - bd create "Backend API" -p gt-auth1 → gt-auth1.2
   ↓
3. Mayor spawns Polecats for each bead:
   - orchestra.spawn(gt-auth1.1, "cursor")
   - orchestra.spawn(gt-auth1.2, "claude")
   ↓
4. Each Polecat gets its own Hook (git worktree):
   - ~/gt/myproject/hooks/polecat-1/
   - Contains: work context, mail, state
   ↓
5. Polecats work independently, mail updates to Mayor
   ↓
6. Witness monitors health, escalates if stuck
   ↓
7. Completion triggers Refinery for merge
   ↓
8. Convoy closes, beads archived
```

## Tool Extensions

### New Tools for Orchestra

```python
@agent.tool_plain
async def spawn_agent(
    task: str,
    bead_id: str | None = None,
    agent_type: str = "polecat",
    runtime: str = "claude",
) -> str:
    """Spawn a new agent for a specific task."""
    pass

@agent.tool_plain
async def sling_bead(
    bead_id: str,
    target: str,  # rig/agent/crew
    priority: int = 1,
) -> str:
    """Assign a bead to an agent."""
    pass

@agent.tool_plain
async def send_mail(
    to: str,
    subject: str,
    body: str,
    bead_id: str | None = None,
) -> str:
    """Send inter-agent mail."""
    pass

@agent.tool_plain
async def create_convoy(
    name: str,
    bead_ids: list[str],
    notify: bool = False,
) -> str:
    """Create a work convoy."""
    pass
```

### New Tools for Beads

```python
@agent.tool_plain
async def bd_create(
    title: str,
    description: str = "",
    parent: str | None = None,
    priority: int = 1,
    assignee: str | None = None,
) -> str:
    """Create a new bead/issue."""
    pass

@agent.tool_plain
async def bd_ready(
    assignee: str | None = None,
    project: str | None = None,
) -> list[dict]:
    """List ready tasks (no blockers)."""
    pass

@agent.tool_plain
async def bd_dep_add(
    child: str,
    parent: str,
    dep_type: str = "blocks",
) -> str:
    """Add dependency between beads."""
    pass
```

## Configuration Schema

### New Config Sections

```json
{
  "orchestra": {
    "town_dir": "~/gt",
    "default_mayor": "claude",
    "max_polecats": 10,
    "enable_witness": true,
    "enable_deacon": true,
    "hooks_base": ".gastown/hooks"
  },
  "beads": {
    "auto_init": true,
    "sync_mode": "embedded",
    "default_project": null,
    "compact_threshold": 1000
  },
  "formulas": {
    "auto_overlay": true,
    "overlay_dirs": ["~/.config/gastown/formulas"]
  },
  "dashboard": {
    "auto_start": false,
    "default_view": "agents",
    "refresh_interval": 5
  }
}
```

## Migration Path

### Phase 1: Foundation (Week 1-2)
1. Ensure `beads` (bd) binary installed and accessible
2. Create `orchestra` plugin with basic role models
3. Implement rig management
4. Hook system for worktree persistence

### Phase 2: Agent System (Week 3-4)
1. Mayor implementation
2. Polecat spawning system
3. Mail/messaging between agents
4. Convoy creation and tracking

### Phase 3: Monitoring (Week 5-6)
1. Witness health monitoring
2. Deacon supervision
3. Dashboard TUI
4. Feed system

### Phase 4: Formulas (Week 7-8)
1. Formula parser
2. Formula execution
3. Built-in formula library
4. Checkpoint/recovery

### Phase 5: Polish (Week 9-10)
1. Dolt integration
2. Wasteland federation
3. Advanced workflows
4. Documentation

## Success Criteria

- [ ] Can create a convoy with multiple beads
- [ ] Can spawn polecats that work in isolated hooks
- [ ] Mayor can coordinate work across agents
- [ ] Beads fully integrated (create, track, dependencies)
- [ ] Dashboard shows real-time agent activity
- [ ] Formulas can define and execute workflows
- [ ] Work survives agent restarts via git hooks
- [ ] Can scale to 20+ concurrent agents

## Integration Points with Existing Code Puppy

| Existing | Hybrid Addition |
|----------|-----------------|
| `agent_skills` | Formulas extend skills |
| `scheduler` | Orchestra uses for agent dispatch |
| `shell_safety` | Enhanced with worktree isolation |
| `frontend_emitter` | Dashboard consumes events |
| `universal_constructor` | Polecats use for tool creation |
| `claude_code_oauth` | Mayor can use Claude |
| `file_permission_handler` | Used for hook permissions |

## Open Questions

1. **Go vs Python**: Should we embed Go code for performance-critical paths, or shell out to binaries?
2. **State Storage**: Full Dolt integration or keep with git-based hooks?
3. **TUI Framework**: Rich (Python) vs Textual vs custom?
4. **Agent Runtime**: Support multiple (Claude, Codex, Cursor) or standardize?
5. **Federation**: Wasteland-style cross-instance coordination?

---

*"Be the orchestra conductor, not the individual musician."*

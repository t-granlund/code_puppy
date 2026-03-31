# Key Concepts in Steve Yegge's Agent Systems

## Beads (Issue Tracking)

### Definition

**Beads** is a distributed graph issue tracker powered by Dolt (a MySQL-compatible database with Git semantics).

### Core Features

| Feature | Description |
|---------|-------------|
| **Dolt-Powered** | Version-controlled SQL database with cell-level merge |
| **Agent-Optimized** | JSON output, dependency tracking, auto-ready detection |
| **Zero Conflict** | Hash-based IDs (bd-a1b2) prevent merge collisions |
| **Compaction** | Semantic "memory decay" summarizes old closed tasks |
| **Messaging** | Message issue type with threading |
| **Graph Links** | relates_to, duplicates, supersedes, replies_to |

### Hierarchy & IDs

**Hierarchical IDs for epics**:
```
bd-a3f8 (Epic)
bd-a3f8.1 (Task)
bd-a3f8.1.1 (Sub-task)
```

**Prefixes indicate origin**:
- `bd-*` - Beads project
- `gt-*` - Gastown project
- `hq-*` - Town-level (cross-project)

### Essential Commands

```bash
bd ready                           # List tasks with no open blockers
bd create "Title" -p 0             # Create P0 (critical) task
bd update <id> --claim             # Atomically claim (sets assignee + in_progress)
bd dep add <child> <parent>        # Link tasks (blocks, related, parent-child)
bd show <id>                       # View task details and audit trail
bd close <id> "reason"             # Close as complete
```

### Storage Modes

**Embedded Mode (default)**:
```bash
bd init
# Dolt runs in-process, data in .beads/embeddeddolt/
# Single-writer only (file locking enforced)
```

**Server Mode**:
```bash
bd init --server
# Connects to external dolt sql-server
# Supports multiple concurrent writers
```

---

## Convoys

### Definition

A **convoy** is a primary work-order wrapping related beads for coordinated execution.

### Purpose

- Bundle multiple beads (issues) together
- Track overall progress
- Coordinate multi-agent work
- Provide notifications and handoffs

### Lifecycle States

| State | Description |
|-------|-------------|
| **Created** | Convoy initialized with beads |
| **Active** | Work in progress |
| **Mountain** | Epic-scale (autonomous stall detection) |
| **Completed** | All beads finished |

### Commands

```bash
gt convoy create "Name" gt-abc gt-def   # Create with beads
gt convoy list                          # List all convoys
gt convoy show <id>                     # Show details
gt convoy add <convoy> <bead>           # Add beads to convoy
```

### Special: Mountain Convoys

Convoys labeled `mountain` get:
- Autonomous stall detection
- Smart skip logic for epic-scale execution
- Enhanced monitoring

---

## Hooks

### Definition

A **hook** is a git worktree-based persistent storage for agent work.

### Characteristics

- **Persistent**: Survives crashes and restarts
- **Version Controlled**: All changes tracked in git
- **Rollback**: Can revert to any previous state
- **Multi-Agent**: Shared through git history
- **Work Queue**: Agent's primary work assignment mechanism

### Types of Hooks

| Type | Location | Purpose |
|------|----------|---------|
| **Agent Hook** | `<rig>/polecats/<name>/` | Individual agent work directory |
| **Crew Hook** | `<rig>/crew/<name>/` | Human developer workspace |
| **Role Hooks** | `<rig>/<role>/` | Shared role configuration |

### Hook Lifecycle

```
Created → Active → Suspended → Active → Completed → Archived
```

### Commands

```bash
gt hook                              # Check what's on MY hook
gt prime                             # Load context and show formula checklist
gt hooks list                        # List all managed hooks
gt hooks sync                        # Regenerate settings files
gt hooks scan                        # Scan for existing hooks
```

### The GUPP Principle

> "If there is work on your Hook, YOU MUST RUN IT."

This autonomous execution principle means:
- Agents don't wait for external prompts
- Work assignment = automatic execution
- Self-driving workflow

---

## Polecats

### Definition

**Polecats** are worker agents with persistent identity but ephemeral sessions.

### Characteristics

- **Persistent Identity**: Permanent agent bead, CV chain, work history
- **Ephemeral Sessions**: Spawned for tasks, cleaned up on completion
- **Task-Specific**: Each assigned to specific beads
- **Scalable**: Can have 20-30 polecats simultaneously

### Lifecycle

```
1. Spawn via gt sling or Mayor
   ↓
2. Check hook for work (GUPP)
   ↓
3. Execute work via gt prime
   ↓
4. Persist findings (bd update)
   ↓
5. gt done → push, create MR, nuke sandbox
   ↓
6. Session ends, identity preserved
```

### Contrast with Crew

| Aspect | Polecat | Crew |
|--------|---------|------|
| **Persistence** | Identity only | Full context across sessions |
| **Session** | Ephemeral | Long-lived |
| **Use Case** | Task-specific work | Ongoing collaboration |
| **Lifecycle** | Spawned/destroyed | User-managed |

---

## Witness

### Definition

The **Witness** is a per-rig patrol agent that monitors polecats and the Refinery.

### Responsibilities

- Monitor polecat health and progress
- Detect stuck agents (GUPP violations)
- Trigger recovery (nudge or handoff)
- Manage session cleanup
- Track completion

### Detection

Witness detects:
- **GUPP Violations**: No progress for extended period
- **Stalled Agents**: Reduced progress
- **Zombie Sessions**: Dead tmux sessions
- **Failures**: Agent crashes or errors

### Actions

| Problem | Action |
|---------|--------|
| Stuck agent | Nudge (prompt to continue) |
| Lost context | Handoff (refresh session) |
| Unresponsive | Spawn replacement |
| Completion | Update status, cleanup |

---

## Deacon

### Definition

The **Deacon** is a cross-rig supervisor running continuous patrol cycles.

### Responsibilities

- Continuous patrol cycles across all rigs
- Check agent health (Witness, Refinery, Polecats)
- Dispatch Dogs for maintenance tasks
- Handle escalations Witnesses can't resolve
- Monitor system-wide health

### Patrol Cycle

```
1. Scan all rigs
2. Check each Witness health
3. Verify Refinery status
4. Detect stuck escalations
5. Dispatch Dogs if needed
6. Sleep and repeat
```

### Chain of Command

```
Boot (checks Deacon)
    ↓
Deacon (cross-rig supervision)
    ↓
Witness (per-rig monitoring)
    ↓
Polecats (worker agents)
```

---

## Refinery

### Definition

The **Refinery** is a per-rig merge queue processor.

### Function

Manages the Bors-style bisecting merge queue:

```
Polecat completes work → gt done
    ↓
Branch pushed, MR bead created
    ↓
Refinery batches pending MRs
    ↓
Runs verification gates on merged stack
    ↓
If green: All MRs in batch merge to main
If red: Bisect to isolate failing MR
    ↓
Merge good ones, re-dispatch failing one
```

### Key Principle

**Polecats never push directly to main.** All changes go through Refinery queue.

### Benefits

- **Batching**: Multiple MRs tested together
- **Bisection**: Isolates failing changes
- **Verification**: Gates ensure quality
- **Isolation**: Main branch always green

---

## Molecules

### Definition

**Molecules** are workflow templates that coordinate multi-step work.

### Components

| Component | Description | State |
|-----------|-------------|-------|
| **Formula** | Source TOML template | "Ice-9" (frozen) |
| **Protomolecule** | Frozen template | Solid |
| **Molecule** | Active instance | Liquid |
| **Wisp** | Ephemeral instance | Vapor |

### Execution Modes

**Root-only (default)**:
- Only root wisp created
- Steps read from embedded formula
- ~400 rows/day (vs 6,000+ without)
- For: Polecat work, patrols

**Poured** (`pour = true`):
- Steps materialized as sub-wisps
- Checkpoint recovery
- For: Releases, long workflows

### Commands

```bash
bd formula list              # Available formulas
bd cook <formula>            # Formula → Proto
bd mol pour <proto>          # Create persistent molecule
bd mol wisp <proto>          # Create ephemeral wisp
bd mol list                  # List active molecules
```

---

## Formulas

### Definition

**Formulas** are TOML-based workflow source templates.

### Structure

```toml
description = "Workflow description"
formula = "name"
version = 1
pour = false  # or true for checkpoint recovery

[vars.version]
description = "Variable description"
required = true

[[steps]]
id = "step-id"
title = "Step Title"
description = "What to do"
needs = ["other-step"]  # Dependencies
```

### Example: Release Formula

```toml
description = "Standard release process"
formula = "release"
version = 1

[vars.version]
description = "The semantic version to release (e.g., 1.2.0)"
required = true

[[steps]]
id = "bump-version"
title = "Bump version"
description = "Run ./scripts/bump-version.sh {{version}}"

[[steps]]
id = "run-tests"
title = "Run tests"
description = "Run make test"
needs = ["bump-version"]

[[steps]]
id = "build"
title = "Build"
description = "Run make build"
needs = ["run-tests"]

[[steps]]
id = "create-tag"
title = "Create release tag"
description = "Run git tag -a v{{version}} -m 'Release v{{version}}'"
needs = ["build"]

[[steps]]
id = "publish"
title = "Publish"
description = "Run ./scripts/publish.sh"
needs = ["create-tag"]
```

---

## Slinging

### Definition

**Slinging** is assigning work to agents via `gt sling`.

### How It Works

```bash
# Sling single bead
gt sling gt-abc gastown

# Sling multiple beads
gt sling gt-abc gt-def gt-ghi gastown

# Sling convoy (all tracked issues)
gt sling hq-cv-abc

# Sling epic (all children)
gt sling gt-epic-123
```

### Scheduler Integration

With `scheduler.max_polecats > 0`:
- `gt sling` creates sling context bead
- Daemon dispatches incrementally
- Respects capacity limits

With `scheduler.max_polecats = -1` (default):
- `gt sling` dispatches immediately
- Spawns polecat directly

---

## Nudging

### Definition

**Nudging** is real-time messaging between agents via `gt nudge`.

### Purpose

- Immediate communication between agents
- Doesn't go through mail system
- Lightweight and synchronous

### Commands

```bash
gt nudge <agent> "Message"           # Send nudge to agent
gt nudge deacon session-started      # Notify Deacon of startup
gt nudge witness check-health        # Request health check
```

---

## Handoff

### Definition

**Handoff** is agent session refresh via `/handoff` or `gt handoff`.

### Purpose

- Refresh context when it gets full
- Start new session while preserving work
- Transfer state to new agent instance

### When to Use

- Context window exhaustion
- Agent stuck or confused
- Need fresh perspective on problem

---

## Seance

### Definition

**Seance** is communicating with previous agent sessions via `gt seance`.

### Purpose

- Query predecessors for context
- Recover decisions from earlier work
- Avoid re-reading entire codebase

### Commands

```bash
gt seance                              # List discoverable sessions
gt seance --talk <id>                  # Full conversation
gt seance --talk <id> -p "Question?"   # One-shot question
```

### Discovery

Seance discovers sessions via `.events.jsonl` logs, enabling agents to recover context without starting from scratch.

---

## Wasteland

### Definition

The **Wasteland** is a federated work coordination network linking Gas Towns through DoltHub.

### Purpose

- Rigs post work to shared board
- Claim tasks from other towns
- Submit completions with evidence
- Earn portable reputation via stamps

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Wanted Board** | Shared list of open work |
| **Rigs** | Participant identities (your DoltHub org) |
| **Stamps** | Multi-dimensional attestations (quality, reliability, creativity) |
| **Trust Levels** | Planned progression from participant to maintainer |

### Commands

```bash
gt wl join <upstream>                  # Join wasteland
gt wl browse                           # View wanted board
gt wl claim <id>                       # Claim work
gt wl done <id> --evidence <url>       # Submit completion
gt wl post --title "Need X"            # Post new work
gt wl sync                             # Pull upstream changes
```

### Reputation

- **Portable**: Travels with you across wastelands
- **Multi-dimensional**: Quality, speed, complexity tracked separately
- **Attested**: Others stamp your work (yearbook rule - can't stamp own)

---

## Summary Table

| Concept | Type | Purpose | Key Command |
|---------|------|---------|-------------|
| **Beads** | Issue tracker | Work tracking | `bd ready` |
| **Convoy** | Work bundle | Multi-issue coordination | `gt convoy create` |
| **Hook** | Git worktree | Persistent agent storage | `gt hook` |
| **Polecat** | Worker agent | Task execution | `gt sling` |
| **Witness** | Monitor | Per-rig health | Automatic |
| **Deacon** | Supervisor | Cross-rig patrol | Automatic |
| **Refinery** | Merge queue | Quality gating | Automatic |
| **Molecule** | Workflow | Multi-step processes | `bd mol pour` |
| **Formula** | Template | Reusable workflows | `bd cook` |
| **Slinging** | Assignment | Work distribution | `gt sling` |
| **Nudge** | Messaging | Real-time comms | `gt nudge` |
| **Handoff** | Session mgmt | Context refresh | `gt handoff` |
| **Seance** | Discovery | Query predecessors | `gt seance` |
| **Wasteland** | Federation | Cross-town work | `gt wl join` |

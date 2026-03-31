# Steve Yegge's Multi-Agent Systems: Comprehensive Research Summary

## Executive Summary

Steve Yegge has developed a comprehensive ecosystem for AI agent orchestration, consisting of three main projects:

1. **Gastown** - Multi-agent workspace manager (Go, 13.3k stars)
2. **Beads** - Distributed graph issue tracker powered by Dolt (Go, multi-platform)
3. **VC (VibeCoder)** - AI-orchestrated coding agent colony (Go)

This research synthesizes his architectural patterns, design principles, and best practices for multi-agent orchestration.

---

## Core Concepts & Architecture

### The Propulsion Principle

Gas Town uses **git hooks as a propulsion mechanism**. Each hook is a git worktree providing:

- **Persistent state** - Work survives agent restarts
- **Version control** - All changes tracked in git  
- **Rollback capability** - Revert to any previous state
- **Multi-agent coordination** - Shared through git history

**Source**: [Gastown README - Propulsion Principle](https://github.com/steveyegge/gastown#the-propulsion-principle)

### Agent Taxonomy & Roles

#### Town-Level Agents (Cross-Project Coordination)

| Agent | Role | Persistence | Responsibility |
|-------|------|-------------|----------------|
| **Mayor** | Global coordinator | Persistent | Cross-rig communication, escalations, orchestration |
| **Deacon** | Daemon beacon | Persistent | Heartbeats, plugins, monitoring, watchdog |
| **Boot** | Deacon watchdog | Ephemeral | Triage when Deacon is down |
| **Dogs** | Infrastructure workers | Variable | Cross-rig batch work, maintenance |

#### Rig-Level Agents (Per-Project)

| Agent | Role | Persistence | Responsibility |
|-------|------|-------------|----------------|
| **Witness** | Per-rig health monitor | Persistent | Monitors polecats, stuck detection, recovery |
| **Refinery** | Merge queue processor | Persistent | Bors-style bisecting merge queue |
| **Polecats** | Worker agents | Persistent identity, ephemeral sessions | Task-specific work |
| **Crew** | Human workspaces | Persistent | User-managed development |

**Source**: [Architecture Documentation](https://github.com/steveyegge/gastown/blob/main/docs/design/architecture.md)

---

## Key Design Principles

### 1. MEOW (Mayor-Enhanced Orchestration Workflow)

MEOW is the recommended orchestration pattern:

1. **Tell the Mayor** - Describe what you want
2. **Mayor analyzes** - Breaks down into tasks
3. **Convoy creation** - Mayor creates convoy with beads
4. **Agent spawning** - Mayor spawns appropriate agents
5. **Work distribution** - Beads slung to agents via hooks
6. **Progress monitoring** - Track through convoy status
7. **Completion** - Mayor summarizes results

### 2. GUPP (Gas Town Universal Propulsion Principle)

> "If there is work on your Hook, YOU MUST RUN IT."

This principle ensures agents autonomously proceed with available work without waiting for external input. GUPP is the heartbeat of autonomous operation.

### 3. NDI (Nondeterministic Idempotence)

The overarching goal ensuring useful outcomes through orchestration of potentially unreliable processes. Persistent Beads and oversight agents guarantee eventual workflow completion even when individual operations may fail or produce varying results.

### 4. ZFC (Zero Framework Cognition)

> "Agent decides. Go transports."

All decisions are delegated to AI. No heuristics, regex, or parsing in the framework. The AI makes decisions; the code provides transport and infrastructure.

**Source**: [Glossary](https://github.com/steveyegge/gastown/blob/main/docs/glossary.md)

---

## Core Architectural Patterns

### Two-Level Beads Architecture

Gas Town separates organizational coordination from project implementation:

| Level | Location | Prefix | Purpose |
|-------|----------|--------|---------|
| **Town** | `~/gt/.beads/` | `hq-*` | Cross-rig coordination, Mayor mail, agent identity |
| **Rig** | `<rig>/mayor/rig/.beads/` | project prefix | Implementation work, MRs, project issues |

**Town-Level Beads** (`~/gt/.beads/`):
- Mayor mail and messages
- Convoy coordination
- Strategic issues and decisions
- Town-level agent beads (Mayor, Deacon, Boot, Dogs)
- Role definition beads (global templates)

**Rig-Level Beads** (`<rig>/.beads/`):
- Bugs, features, tasks for the project
- Merge requests and code reviews
- Project-specific molecules
- Rig-level agent beads (Witness, Refinery, Polecats)

**Source**: [Architecture Documentation](https://github.com/steveyegge/gastown/blob/main/docs/design/architecture.md)

### Beads (Issue Tracking System)

Beads is a **distributed graph issue tracker** powered by Dolt:

- **Dolt-Powered**: Version-controlled SQL database with cell-level merge
- **Agent-Optimized**: JSON output, dependency tracking, auto-ready task detection
- **Zero Conflict**: Hash-based IDs (bd-a1b2) prevent merge collisions
- **Compaction**: Semantic "memory decay" summarizes old closed tasks
- **Graph Links**: `relates_to`, `duplicates`, `supersedes`, `replies_to`

**Key Commands**:
- `bd ready` - List tasks with no open blockers
- `bd create "Title" -p 0` - Create P0 task
- `bd update <id> --claim` - Atomically claim a task
- `bd dep add <child> <parent>` - Link tasks with dependencies

**Source**: [Beads Repository](https://github.com/gastownhall/beads)

### Molecules & Formulas

**Molecules** are workflow templates that coordinate multi-step work:

```
Formula (source TOML) ─── "Ice-9"
    │
    ▼ bd cook
Protomolecule (frozen template) ─── Solid
    │
    ├─▶ bd mol pour ──▶ Mol (persistent) ─── Liquid
    │
    └─▶ bd mol wisp --root-only ──▶ Root Wisp (ephemeral) ─── Vapor
```

**Root-only wisps** (default): Formula steps are NOT materialized as database rows. Only a single root wisp is created.

**Poured wisps** (`pour = true`): Steps ARE materialized as sub-wisps with checkpoint recovery.

**Source**: [Molecules Documentation](https://github.com/steveyegge/gastown/blob/main/docs/concepts/molecules.md)

---

## Workflow Patterns

### The AI Supervised Issue Workflow (VC)

VC uses a structured execution loop:

```
Loop {
  1. Claim ready issue (atomic SQL)
  2. AI Assessment: strategy, steps, risks
  3. Execute via agent
  4. AI Analysis: extract punted work, bugs
  5. Auto-create discovered issues
  6. Quality gates (test, lint, build)
  7. AI decides: close, partial, or blocked
}
```

**Source**: [VC Repository](https://github.com/steveyegge/vc)

### Escalation Protocol

Three-tier escalation flow:

```
Agent -> gt escalate -s <SEVERITY> "description"
           |
           v
     [Deacon receives]
           |
           +-- resolves --> updates issue, re-slings work
           +-- cannot  --> forwards to Mayor
                              +-- resolves --> updates issue, re-slings
                              +-- cannot  --> forwards to Overseer
```

**Severity Levels**:
- **CRITICAL (P0)**: System-threatening - bead + mail + email + SMS
- **HIGH (P1)**: Important blocker - bead + mail + email
- **MEDIUM (P2)**: Standard escalation - bead + mail mayor

**Source**: [Escalation Documentation](https://github.com/steveyegge/gastown/blob/main/docs/design/escalation.md)

### Scheduler & Dispatch

Config-driven capacity-controlled polecat dispatch:

| Value | Mode | Behavior |
|-------|------|----------|
| `-1` (default) | Direct dispatch | `gt sling` dispatches immediately |
| `N > 0` | Deferred dispatch | Creates sling context bead, daemon dispatches incrementally |

**Key Commands**:
- `gt sling <bead> <rig>` - Sling bead to rig
- `gt scheduler status` - Show scheduler state
- `gt scheduler run` - Trigger dispatch manually
- `gt scheduler pause/resume` - Control dispatch

**Source**: [Scheduler Documentation](https://github.com/steveyegge/gastown/blob/main/docs/design/scheduler.md)

---

## Best Practices

### Multi-Agent Orchestration

1. **Always start with the Mayor** - It's designed to be your primary interface
2. **Use convoys for coordination** - They provide visibility across agents
3. **Leverage hooks for persistence** - Your work won't disappear
4. **Create formulas for repeated tasks** - Save time with Beads recipes
5. **Use gt feed for live monitoring** - Watch agent activity and catch stuck agents
6. **Let the Mayor orchestrate** - It knows how to manage agents

### Agent Configuration

Gas Town supports multiple AI runtimes:
- Claude Code (default)
- GitHub Copilot CLI
- Codex CLI
- Cursor
- And others via `gt config agent set`

### Directory Structure

```
~/gt/                           # Town root
├── .beads/                     # Town-level beads (hq-* prefix)
├── .dolt-data/                 # Centralized Dolt data
├── daemon/                     # Daemon runtime state
├── deacon/                     # Deacon workspace
├── mayor/                      # Mayor agent home
├── gastown/                    # Example rig
│   ├── crew/yourname/          # Your workspace
│   ├── witness/                # Witness agent
│   ├── refinery/               # Refinery agent
│   ├── polecats/               # Worker agents
│   └── .beads/                 # Rig-level beads
└── <other rigs>/
```

---

## Wasteland Federation

The **Wasteland** is a federated work coordination network linking Gas Towns through DoltHub:

- Rigs post work, claim tasks, submit completions
- Earn portable reputation via multi-dimensional stamps
- Backed by shared Dolt database with Git semantics

**Key Commands**:
- `gt wl join <upstream>` - Join a wasteland
- `gt wl browse` - View the wanted board
- `gt wl claim <id>` - Claim a wanted item
- `gt wl done <id> --evidence <url>` - Submit completion

**Source**: [Wasteland Documentation](https://github.com/steveyegge/gastown/blob/main/docs/WASTELAND.md)

---

## Monitoring & Health

Three-tier watchdog system:

```
Daemon (Go process) ← heartbeat every 3 min
    └── Boot (AI agent) ← intelligent triage
        └── Deacon (AI agent) ← continuous patrol
            └── Witnesses & Refineries ← per-rig agents
```

**Problems View** (`gt feed --problems`):
- **GUPP Violation**: Hooked work with no progress
- **Stalled**: Hooked work with reduced progress
- **Zombie**: Dead tmux session
- **Working**: Active, progressing normally
- **Idle**: No hooked work

---

## Sources & Credibility Assessment

### Tier 1 Sources (Primary Documentation)

| Source | URL | Type | Currency | Reliability |
|--------|-----|------|----------|-------------|
| Gastown GitHub | https://github.com/steveyegge/gastown | Official Repo | Active (March 2026) | ⭐⭐⭐⭐⭐ |
| Beads GitHub | https://github.com/gastownhall/beads | Official Repo | Active (March 2026) | ⭐⭐⭐⭐⭐ |
| VC GitHub | https://github.com/steveyegge/vc | Official Repo | Active (2025) | ⭐⭐⭐⭐⭐ |
| Architecture Docs | https://github.com/steveyegge/gastown/tree/main/docs/design | Official Docs | Current | ⭐⭐⭐⭐⭐ |

### Tier 2 Sources (Community)

| Source | URL | Type | Notes |
|--------|-----|------|-------|
| GastownHall Org | https://github.com/gastownhall | Organization | Multiple related repos |
| Steve Yegge GitHub | https://github.com/steveyegge | Profile | 3.4k followers |

---

## Key Takeaways for Code Puppy

Based on this research, here are relevant patterns for Code Puppy's Orchestra plugin:

1. **Hook System**: Git worktrees for persistent agent state
2. **Two-Level Architecture**: Town-level coordination + project-level execution
3. **Issue-Oriented Orchestration**: Work tracked as structured data (beads)
4. **AI Supervision**: LLM assesses before/after, not just executes
5. **Escalation Protocol**: Structured severity-based routing
6. **Scheduler**: Config-driven capacity control prevents resource exhaustion
7. **Health Monitoring**: Three-tier watchdog with problems view
8. **ZFC Principle**: Let AI decide, code transports
9. **Formulas**: Reusable TOML workflow templates
10. **GUPP**: Autonomous execution - if work exists, run it

---

## Research Notes

**Researcher**: Web-Puppy (ID: web-puppy-285606)  
**Date**: March 31, 2026  
**Methodology**: Direct repository analysis of official sources  
**Limitations**: Medium blog posts could not be accessed due to CAPTCHA restrictions; all content extracted from GitHub documentation and README files

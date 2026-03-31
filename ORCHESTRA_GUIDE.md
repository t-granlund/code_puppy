# Orchestra Plugin - User Guide

> Multi-agent orchestration for Code Puppy, inspired by Gastown

## Overview

Orchestra brings **Gastown-style multi-agent orchestration** to Code Puppy. It enables you to coordinate multiple AI agents working on different tasks with persistent state that survives restarts.

## Core Concepts

### Roles

| Role | Description | Use Case |
|------|-------------|----------|
| **Mayor** | Primary AI coordinator | Your main interface - tell the Mayor what to build |
| **Polecat** | Ephemeral worker agent | Spawned for specific tasks, sessions end on completion |
| **Crew** | Human workspace | Where you do hands-on work |
| **Witness** | Per-rig health monitor | Monitors agents and detects stuck work |
| **Deacon** | Cross-rig supervisor | Patrols all rigs, handles escalations |
| **Dog** | Maintenance runner | Infrastructure tasks (backup, cleanup) |

### Rigs (Projects)

A **rig** is a project container wrapping a git repository. Each rig has:
- Its own agents and crew workspaces
- Isolated hook storage
- Per-project configuration

### Hooks (Persistent Storage)

**Hooks** are git worktrees that provide:
- Persistent state that survives agent restarts
- Version control through git
- Rollback capability
- Multi-agent coordination through shared git history

### Convoys (Work Tracking)

A **convoy** bundles multiple beads (issues) for coordinated execution. Convoys track:
- Which beads are included
- Which agents are working
- Overall progress
- Notifications and handoffs

### Mail (Inter-Agent Messaging)

**Mail** enables asynchronous communication between agents that persists across sessions.

## Quick Start

### 1. Create Your First Rig

```bash
# Create a rig for your project
/rig create myproject https://github.com/me/myproject.git

# Or for a local project
/rig create myproject --path /path/to/project
```

### 2. Initialize Beads (Issue Tracking)

```bash
# In your project directory
bd init

# Create some beads
/bd create "Implement auth system" -p 1
/bd create "Add login page" --parent bd-abc12 -p 1
/bd create "Add API endpoints" --parent bd-abc12 -p 2
```

### 3. Create a Convoy

```bash
# Bundle related work
/convoy create "Auth System v1" --beads "bd-abc12,bd-abc12.1,bd-abc12.2"
```

### 4. Spawn Agents

```bash
# Spawn a polecat to work on a specific bead
/spawn polecat "Implement login page" --bead bd-abc12.1 --runtime claude

# Or let the Mayor coordinate
/agents  # See active agents
```

## Commands Reference

### Rig Management

```bash
/rig create <name> [repo-url]     # Create new rig
/rig list                          # List all rigs
/rig show <name>                   # Show rig details
/rig remove <name>                 # Remove rig
```

### Beads (Issue Tracking)

```bash
/bd create <title>                 # Create bead
  [-p 0|1|2|3]                     # Priority (0=critical, 3=low)
  [-d <description>]               # Description
  [--parent <id>]                  # Parent bead
  [-a <assignee>]                  # Assignee

/bd show <id>                      # Show bead details
/bd list                           # List beads
  [-s open|closed|all]             # Status filter
  [-a <assignee>]                  # Assignee filter

/bd ready                          # List beads ready to work
/bd claim <id>                     # Claim a bead
/bd close <id> [message]           # Close bead as complete

/bd dep add <child> <parent>       # Add dependency
  [-t blocks|relates_to|...]       # Dependency type
```

### Convoys

```bash
/convoy create <name>              # Create convoy
  [--rig <rig>]                    # Which rig
  [--beads <id1,id2,...>]          # Beads to include
  [--priority 0|1|2|3]             # Priority
  [--notify]                       # Notify on completion

/convoy list                       # List convoys
/convoy show <id>                  # Show convoy details
```

### Agents

```bash
/agents                            # List active agents
/spawn <type> <task>               # Spawn agent
  [--rig <rig>]                    # Which rig
  [--runtime claude|codex|cursor]  # AI runtime
  [--bead <id>]                    # Assigned bead
```

### Mail

```bash
/mail send <to> <subject>          # Send mail to agent
  [--bead <id>]                    # Related bead
/mail inbox                        # Check your mail
/mail read <id>                    # Read mail message
```

### Formulas (Workflows)

```bash
/formula list                      # List available formulas
/formula cook <name>               # Execute formula immediately
  [--vars key=value;key2=value2]   # Formula variables
/formula pour <name>               # Create trackable molecule
```

### Dashboard

```bash
/dashboard                         # Open TUI dashboard
/feed                              # View event feed
/feed problems                     # View stuck agents
```

## Workflow Examples

### Feature Development Workflow

```bash
# 1. Create rig for the project
/rig create auth-project https://github.com/me/auth.git

# 2. Create beads for the feature
cd ~/gt/auth-project
bd init
/bd create "OAuth Implementation" -p 0
/bd create "Google OAuth" --parent bd-a1b2c -p 1
/bd create "GitHub OAuth" --parent bd-a1b2c -p 1
/bd create "Auth middleware" --parent bd-a1b2c -p 1

# 3. Set up dependencies
/bd dep add bd-a1b2c.2 bd-a1b2c.1  # GitHub depends on Google

# 4. Create convoy
/convoy create "OAuth Feature" --beads "bd-a1b2c,bd-a1b2c.1,bd-a1b2c.2,bd-a1b2c.3" --notify

# 5. Spawn agents for ready work
/bd ready  # See what's unblocked
/spawn polecat "Implement Google OAuth" --bead bd-a1b2c.1
/spawn polecat "Implement auth middleware" --bead bd-a1b2c.3

# 6. Monitor progress
/dashboard
/convoy show <convoy-id>
```

### TDD Cycle with Formula

```bash
# Execute the TDD cycle formula
/formula cook tdd-cycle --vars "feature=user-profile;test_framework=pytest"

# Or create a trackable molecule
/formula pour tdd-cycle --vars "feature=payment-processing"
```

### Code Review Workflow

```bash
# Review a PR using the code review formula
/formula cook code-review --vars "pr_number=42;author=alice;focus_areas=security,api"
```

## Directory Structure

```
~/gt/                              # Orchestra Town
├── .orchestra/                    # Orchestra config
│   ├── rigs.json                  # Rig registry
│   ├── state/                     # Global state
│   └── hooks/                     # Global hooks
├── myproject/                     # Rig directory
│   ├── crew/                      # Crew workspaces
│   │   └── yourname/              # Your workspace
│   ├── .orchestra/                # Rig-specific orchestra data
│   │   ├── hooks/                 # Agent hooks (git worktrees)
│   │   │   ├── polecat-1/         # Agent's persistent storage
│   │   │   │   ├── work/          # Working directory
│   │   │   │   ├── .orchestra/    # Agent state
│   │   │   │   └── mail/          # Agent inbox
│   │   │   └── polecat-2/
│   │   └── state/                 # Rig state
│   └── .beads/                    # Beads database (Dolt)
│       └── embeddeddolt/          # Embedded Dolt
└── another-project/
    └── ...
```

## Integration with Existing Code Puppy

Orchestra extends Code Puppy without breaking existing workflows:

| Existing | Orchestra Addition |
|----------|-------------------|
| `code-puppy` CLI | Works in Orchestra rigs |
| `scheduler` | Used for agent dispatch |
| `shell_safety` | Enhanced with worktree isolation |
| `agent_skills` | Formulas extend skills |
| `frontend_emitter` | Dashboard consumes events |

## Tips

1. **Always start with a rig** - Create a rig for each project
2. **Use beads for tracking** - They survive restarts and track dependencies
3. **Bundle work in convoys** - Easier to monitor and coordinate
4. **Let agents use mail** - Async communication is more reliable
5. **Use formulas for repeatability** - Standardize common processes
6. **Check `/bd ready`** - Always know what's unblocked

## Troubleshooting

### Beads not found
```bash
# Install beads if not already installed
curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash
```

### Rig creation fails
```bash
# Ensure town directory exists
mkdir -p ~/gt
```

### Agent spawning fails
```bash
# Check that your AI runtime is installed
which claude  # or codex, cursor, etc.
```

## Next Steps

1. **Hook System** - Full git worktree management
2. **Agent Spawning** - Actual process management
3. **Convoy Execution** - State machine and progress tracking
4. **Mail Delivery** - Queue and delivery mechanism
5. **TUI Dashboard** - Rich/Textual-based monitoring
6. **Health Monitoring** - Witness and Deacon implementation

---

*Part of the Code Puppy × Gastown × Beads Hybrid*

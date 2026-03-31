# Multi-Agent Orchestration Best Practices

## 1. Mayor-First Workflow

### Principle

Always start with the **Mayor** as your primary interface. The Mayor is designed to be the coordinator, not individual agents.

### Why

- **Context**: Mayor has full view of all rigs and agents
- **Orchestration**: Knows how to distribute work effectively
- **Escalation**: Routes blockers appropriately
- **Summarization**: Provides completion summaries

### Pattern

```bash
# Good: Let Mayor coordinate
gt mayor attach
# "Build an auth system with OAuth"
# Mayor: creates convoy, spawns agents, distributes work

# Bad: Manual coordination
gt spawn polecat --bead gt-1
gt spawn polecat --bead gt-2
gt spawn polecat --bead gt-3
# You manage dependencies and coordination manually
```

---

## 2. Convoy-Centric Organization

### Principle

Use **convoys** to group related work. Convoys provide visibility and coordination across multiple beads.

### When to Create Convoys

- **Feature Work**: Group all tasks for a feature
- **Bug Fixes**: Bundle related bug fixes
- **Epics**: Large initiatives with multiple components
- **Releases**: Coordinate release-related tasks

### Commands

```bash
# Create convoy for feature
gt convoy create "OAuth System" \
  --beads "gt-auth-1,gt-auth-2,gt-auth-3" \
  --notify

# Add more work later
gt convoy add <convoy-id> gt-auth-4

# Monitor progress
gt convoy show <convoy-id>
```

### Mountain Convoys

For epic-scale work, label convoy as `mountain`:

```bash
gt convoy create "Major Refactor" \
  --beads "gt-epic-1,..." \
  --label mountain
```

Benefits:
- Autonomous stall detection
- Smart skip logic
- Enhanced monitoring

---

## 3. Hook-Based Persistence

### Principle

Always use **hooks** for persistent storage. Work in agent memory is lost on restart; work in hooks survives.

### Best Practices

1. **Persist findings early**:
   ```bash
   # Don't wait until end
   bd update <issue> --notes "Found X in module Y"
   ```

2. **Use `gt done` properly**:
   ```bash
   # Polecats MUST run gt done
   gt done  # Pushes, creates MR, nukes sandbox, exits
   ```

3. **Check hook on startup**:
   ```bash
   gt prime  # Shows formula checklist and current context
   ```

---

## 4. Dependency Management

### Principle

Explicitly declare **dependencies** between beads. Don't assume agents know the order.

### Commands

```bash
# Add dependency
gt dep add <child> <parent>

# Example: OAuth depends on core auth
gt dep add gt-oauth-google gt-auth-core
gt dep add gt-oauth-github gt-auth-core

# Check what's ready
gt ready  # Only shows unblocked beads
```

### Benefits

- **Correct ordering**: Agents work on unblocked items first
- **Parallelization**: Unrelated items can proceed simultaneously
- **Visibility**: Clear view of blockers

---

## 5. Formula Reuse

### Principle

Create **formulas** for repeatable processes. Don't reinvent the workflow each time.

### When to Use Formulas

- **TDD Cycle**: Red-green-ref-repeat
- **Code Review**: Standard review process
- **Release Process**: Version bump → test → build → tag → publish
- **Onboarding**: New developer setup
- **Incident Response**: Standard debugging steps

### Example: TDD Formula

```toml
# tdd.formula.toml
description = "TDD development cycle"
formula = "tdd"
version = 1

[vars.feature]
description = "Feature to implement"
required = true

[[steps]]
id = "red"
title = "Write failing test"
description = "Create test for {{feature}} that fails"

[[steps]]
id = "green"
title = "Make test pass"
description = "Implement {{feature}} minimally"
needs = ["red"]

[[steps]]
id = "refactor"
title = "Refactor"
description = "Clean up code while keeping tests green"
needs = ["green"]
```

### Execution

```bash
# Run immediately
bd cook tdd --var feature="user-profile"

# Create trackable instance
bd mol pour tdd --var feature="payment-processing"
```

---

## 6. Proactive Monitoring

### Principle

Use **`gt feed`** for live monitoring. Don't wait for agents to report problems.

### Commands

```bash
gt feed                      # Launch TUI dashboard
gt feed --problems          # Start in problems view
gt feed --since 1h          # Events from last hour
```

### Problems View

Key states to watch for:

| State | Action |
|-------|--------|
| **GUPP Violation** | Press `n` to nudge, `h` to handoff |
| **Stalled** | Investigate, may need handoff |
| **Zombie** | Session died, needs restart |

### Dashboard

For web-based monitoring:

```bash
gt dashboard --port 3000 --open
```

---

## 7. Escalation Discipline

### Principle

**Escalate** appropriately. Don't let agents spin on blockers.

### When to Escalate

**Should escalate**:
- System errors (DB corruption, disk full)
- Security issues (credential exposure)
- Unresolvable conflicts
- Ambiguous requirements
- Design decisions
- Stuck for > threshold time

**Should NOT escalate**:
- Normal workflow
- Recoverable errors (will retry)
- Questions answerable from context

### Commands

```bash
# Create escalation
gt escalate -s HIGH "Database connection failing"

# List open escalations
gt escalate list

# Acknowledge (prevents re-escalation)
gt escalate ack <bead-id> --note "Investigating"

# Close when resolved
gt escalate close <bead-id> --reason "Fixed config"
```

### Auto-Reescalation

Unacknowledged escalations are automatically re-escalated:
- Severity bumps: MEDIUM → HIGH → CRITICAL
- After `stale_threshold` (default: 4h)
- Max 2 re-escalations

---

## 8. Capacity Management

### Principle

Use the **scheduler** to prevent resource exhaustion. Don't spawn unlimited agents.

### Configuration

```bash
# Enable deferred dispatch (max 5 concurrent)
gt config set scheduler.max_polecats 5

# Disable (direct dispatch)
gt config set scheduler.max_polecats -1
```

### When to Use Scheduler

| Scenario | Recommendation |
|----------|----------------|
| API rate limits | Set max_polecats to limit |
| Memory constraints | Set max_polecats to limit |
| < 5 agents | Direct dispatch (-1) is fine |
| 5-20 agents | Use scheduler (5-10) |
| 20+ agents | Use scheduler (10-20) |

### Monitoring

```bash
gt scheduler status    # Show capacity and queued work
gt scheduler list      # Show all scheduled beads
gt scheduler pause     # Emergency stop
gt scheduler resume    # Resume dispatch
```

---

## 9. Session Management

### Principle

Use **handoffs** and **seance** for session management. Don't lose context unnecessarily.

### Handoff (Fresh Start)

When to handoff:
- Context window exhaustion
- Agent stuck or confused
- Need fresh perspective

```bash
# In agent session
/handoff
# or
gt handoff
```

### Seance (Query Predecessors)

When to use seance:
- Need context from earlier work
- Understanding previous decisions
- Avoid re-reading entire codebase

```bash
# List previous sessions
gt seance

# Ask specific question
gt seance --talk <id> -p "What did you find?"
```

---

## 10. Quality Gates

### Principle

Always run **quality gates** before marking work complete. Don't merge broken code.

### Standard Gates

| Gate | Purpose |
|------|---------|
| **Test** | Run test suite |
| **Lint** | Check code style |
| **Build** | Ensure compiles/links |
| **Type Check** | Verify type safety |

### Refinery Integration

The Refinery runs gates automatically:

```
Polecat: gt done
    ↓
Refinery: batches MRs
    ↓
Runs gates on merged stack
    ↓
If green: merges to main
If red: bisects and isolates failure
```

### Manual Gates

```bash
# Run gates manually
make test
make lint
make build

# Or via formula
bd cook quality-gates
```

---

## 11. Wasteland Participation

### Principle

Participate in **Wasteland** for portable reputation. Work is the only input; reputation is the only output.

### Getting Started

```bash
# 1. Set environment
export DOLTHUB_ORG="your-username"
export DOLTHUB_TOKEN="dhat.v1.your-token"

# 2. Join wasteland
gt wl join hop/wl-commons

# 3. Browse for work
gt wl browse --type docs --priority 0

# 4. Claim and complete
gt wl claim w-abc123
# ... do work ...
gt wl done w-abc123 --evidence "https://github.com/.../pull/123"
```

### Building Reputation

- **Quality**: Well-tested, documented work
- **Reliability**: Consistent delivery
- **Creativity**: Elegant solutions
- **Cannot self-stamp**: Others must attest

---

## 12. Git Hygiene

### Principle

Maintain good **git hygiene**. Hooks are git worktrees; treat them with respect.

### Best Practices

1. **Commit frequently**:
   ```bash
   git add -A && git commit -m "WIP: implemented X"
   ```

2. **Use meaningful messages**:
   ```bash
   git commit -m "feat(auth): add OAuth2 Google provider"
   ```

3. **Keep worktrees clean**:
   ```bash
   gt done  # Properly cleans up after completion
   ```

4. **Don't commit to main directly**:
   ```bash
   # Bad: git push origin main
   # Good: gt done (creates MR, goes through Refinery)
   ```

---

## Summary Checklist

### Starting Work
- [ ] Started with Mayor (`gt mayor attach`)
- [ ] Created convoy for related work
- [ ] Checked `gt ready` for unblocked beads
- [ ] Set scheduler limits if needed

### During Work
- [ ] Persisted findings early (`bd update`)
- [ ] Monitoring with `gt feed`
- [ ] Escalated blockers appropriately
- [ ] Used seance to query predecessors

### Completing Work
- [ ] Ran quality gates
- [ ] Used `gt done` (polecats)
- [ ] Verified in convoy status
- [ ] Closed escalation if applicable

### Maintenance
- [ ] Synced Wasteland regularly (`gt wl sync`)
- [ ] Reviewed problems view (`gt feed --problems`)
- [ ] Archived completed convoys
- [ ] Updated formulas based on learnings

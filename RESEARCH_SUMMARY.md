# Research Summary: Multi-Agent Orchestration Systems

> Research conducted for Code Puppy × Gastown × Beads Hybrid

## Research Scope

- **Steve Yegge's Agent Systems** (Gastown, Beads, VC)
- **Multi-Agent Orchestration Best Practices**
- **Current State of AI Agent Systems (2024-2025)**

## Key Research Findings

### 1. Steve Yegge's Core Principles

Located in `research/steveyegge-agent-systems/`:

#### MEOW (Mayor-Enhanced Orchestration Workflow)
Breaking goals into atomic units that can be distributed to agents.

#### GUPP (Gas Town Universal Propulsion Principle)
> "If there is work on your Hook, YOU MUST RUN IT"

Autonomous execution - agents don't wait for prompts when work exists.

#### NDI (Nondeterministic Idempotence)
Reliable outcomes from unreliable parts through idempotent operations.

#### ZFC (Zero Framework Cognition)
"Agent decides, code transports" - frameworks should be transparent.

### 2. Agent Taxonomy

| Role | Scope | Responsibility |
|------|-------|----------------|
| **Mayor** | Town | Cross-project coordination, orchestration |
| **Witness** | Rig | Per-project agent health monitoring |
| **Refinery** | Rig | Merge queue processing |
| **Polecat** | Task | Ephemeral worker agents |
| **Crew** | User | Human developer workspace |
| **Deacon** | Cross-rig | Patrols all rigs, handles escalations |
| **Dog** | Infrastructure | Maintenance tasks |

### 3. Critical Architecture Patterns

#### The Propulsion Principle
Git hooks (worktrees) as persistent storage:
- Work survives agent restarts
- Version control of all changes
- Multi-agent coordination through shared git
- Rollback capability

#### Two-Level Beads Architecture
- **Town-level**: Cross-project issues (hq-* prefix)
- **Rig-level**: Project-specific issues (project-specific prefix)

#### Convoy System
Work bundles for coordinated multi-agent execution with:
- Dependency tracking
- Priority levels
- Mountain mode (epic-scale)
- Progress monitoring

### 4. Health Monitoring (Three-Tier)

```
Code Puppy Core (heartbeat every 3 min)
    └── Boot Agent (intelligent triage)
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

### 5. Research Documents Created

Located in `research/steveyegge-agent-systems/`:

1. **README.md** (12.1 KB) - Executive summary
2. **architectural-patterns.md** (14.2 KB) - 8 detailed patterns
3. **design-principles.md** (11.8 KB) - MEOW, GUPP, NDI, ZFC
4. **key-concepts.md** (13.1 KB) - Beads, Convoys, Hooks
5. **orchestration-best-practices.md** (9.4 KB) - Usage patterns
6. **recommendations-for-code-puppy.md** (10.9 KB) - Actionable recommendations
7. **sources.md** (7.4 KB) - Credibility assessment

Located in `research/multi-agent-orchestration/`:

1. **README.md** (20.1 KB) - Industry-wide patterns and best practices

## Top Recommendations for Code Puppy Orchestra

### P0 (Critical)
1. **Git Hook Persistence** - Implement worktrees for agent state
2. **Two-Level Beads** - Separate town-level from rig-level tracking
3. **Agent Taxonomy** - Define Mayor, Witness, Refinery, Polecats, Crew
4. **GUPP Implementation** - Auto-execute work on hooks

### P1 (High)
- Convoy enhancements with dependencies
- Escalation protocol with severity routing
- Scheduler for capacity management
- Three-tier watchdog system

### P2/P3 (Future)
- Formula/molecule system
- Wasteland federation
- Seance (session continuation)

## Implementation Priority

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

## Sources

### Primary Sources
- **Gastown**: https://github.com/steveyegge/gastown
- **Beads**: https://github.com/gastownhall/beads
- **VC**: https://github.com/steveyegge/vc

### Research Agent
- **Web-Puppy** conducted comprehensive research
- **Date**: March 31, 2026
- **Confidence**: High (based on official documentation)

## Next Steps

1. **Review Research**: Read `research/steveyegge-agent-systems/recommendations-for-code-puppy.md`
2. **Prioritize Features**: Use P0/P1/P2 prioritization
3. **Implement P0 Features**: Start with git hook persistence
4. **Iterate**: Build incrementally, test continuously

---

*Research compiled for Code Puppy Hybrid Project*

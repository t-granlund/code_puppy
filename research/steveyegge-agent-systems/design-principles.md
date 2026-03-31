# Design Principles in Steve Yegge's Agent Systems

## 1. MEOW (Mayor-Enhanced Orchestration Workflow)

### Definition

MEOW stands for **Molecular Expression of Work**. It's the recommended orchestration pattern for breaking large goals into detailed instructions for agents.

### The Pattern

```
1. Tell the Mayor
   ↓
2. Mayor analyzes - Breaks down into tasks
   ↓
3. Convoy creation - Mayor creates convoy with beads
   ↓
4. Agent spawning - Mayor spawns appropriate agents
   ↓
5. Work distribution - Beads slung to agents via hooks
   ↓
6. Progress monitoring - Track through convoy status
   ↓
7. Completion - Mayor summarizes results
```

### Key Principles

- **Work Decomposition**: Large goals → detailed, trackable, atomic units
- **Agent Autonomy**: Agents execute independently once tasked
- **Visibility**: Convoys provide cross-agent progress tracking
- **Coordination**: Mayor handles orchestration, not individual task management

### Example Flow

```bash
# 1. User tells Mayor what to build
gt mayor attach
# "Build an authentication system with OAuth"

# 2-3. Mayor analyzes and creates convoy
# Convoy "Auth System" created with beads:
# - gt-auth-1: OAuth implementation
# - gt-auth-2: Google OAuth provider
# - gt-auth-3: GitHub OAuth provider
# - gt-auth-4: Auth middleware

# 4-5. Mayor spawns agents and slings work
gt sling gt-auth-2 gastown  # To polecat-1
gt sling gt-auth-3 gastown  # To polecat-2
gt sling gt-auth-4 gastown  # To polecat-3

# 6. Monitor progress
gt convoy list
gt feed

# 7. Mayor summarizes when complete
# "Auth system complete: 3 OAuth providers integrated, middleware deployed"
```

---

## 2. GUPP (Gas Town Universal Propulsion Principle)

### The Principle

> **"If there is work on your Hook, YOU MUST RUN IT."**

This is the heartbeat of autonomous operation in Gastown.

### What It Means

- **Autonomous Execution**: Agents don't wait for external prompts
- **Self-Driving**: Work proceeds without human intervention
- **Hook-Driven**: Work assignment = work on hook = automatic execution
- **No Polling**: Agents don't ask "should I work?" - they act if work exists

### Hook Lifecycle

```
Hook Created
    ↓
Work Assigned (bead slung to hook)
    ↓
Agent Detects Work (via GUPP)
    ↓
Automatic Execution Begins
    ↓
Work Completed → gt done
    ↓
Hook Archived or Next Work Assigned
```

### Violation Detection

The Problems View in `gt feed --problems` detects GUPP violations:

| State | Condition |
|-------|-----------|
| **GUPP Violation** | Hooked work with no progress for extended period |

### Implementation

Agents check their hook on session start:
```bash
gt hook              # What's on MY hook?
gt prime             # Load context and show work
gt done              # Mark work complete
```

---

## 3. NDI (Nondeterministic Idempotence)

### Definition

The overarching goal ensuring **useful outcomes through orchestration of potentially unreliable processes**.

### Core Concepts

1. **Nondeterministic**: Individual operations may fail or produce varying results
2. **Idempotence**: The overall system produces correct outcomes despite failures
3. **Orchestration**: System-level guarantees through design, not individual reliability

### How It's Achieved

| Mechanism | Purpose |
|-----------|---------|
| **Persistent Beads** | Work state survives agent crashes |
| **Oversight Agents** | Witness, Deacon detect and recover failures |
| **Git Worktrees** | State in version control, not agent memory |
| **Escalation Protocol** | Issues routed to appropriate humans |
| **Checkpoint Recovery** | Poured molecules resume from last step |

### Example: Agent Failure Recovery

```
Polecat working on gt-abc12
    ↓
Agent crashes (OOM, API error, etc.)
    ↓
Witness detects (no progress in timeout period)
    ↓
Witness triggers recovery:
  - New agent spawned
  - Reads work from git hook (state preserved)
  - Resumes from checkpoint (if poured molecule)
    ↓
Work completes despite crash
```

---

## 4. ZFC (Zero Framework Cognition)

### The Principle

> **"Agent decides. Go transports."**

### What It Means

- **No Heuristics**: Framework doesn't make decisions
- **No Regex Parsing**: Don't try to "understand" code
- **No Business Logic**: All decisions delegated to AI
- **Transport Layer**: Code provides infrastructure, AI provides intelligence

### Contrast with Traditional Systems

| Traditional | ZFC Approach |
|-------------|--------------|
| Regex-based code analysis | AI reads and understands code |
| Rule-based quality gates | AI assesses code quality |
| Static analysis for security | AI reviews for security issues |
| Template-based code generation | AI generates context-appropriate code |

### Implementation Examples

**Non-ZFC (Bad)**:
```python
# Framework tries to parse and understand code
import ast
def analyze_code(file_path):
    tree = ast.parse(open(file_path).read())
    # Complex logic to detect patterns
    if has_function(tree, "authenticate"):
        return "Has auth"
```

**ZFC (Good)**:
```python
# Framework provides transport, AI decides
@agent.tool
def analyze_code(file_path: str) -> str:
    """Analyze code file for patterns."""
    content = read_file(file_path)
    # AI decides what to look for and how to interpret
    return ai_assess("Analyze this code:", content)
```

### Benefits

1. **Flexibility**: Works with any language, framework, or pattern
2. **Maintainability**: No brittle heuristics to update
3. **Intelligence**: Leverages LLM reasoning capabilities
4. **Simplicity**: Less code, fewer edge cases

---

## 5. MEOW Stack Integration

### The Stack

| Layer | Description | Plugin Analog |
|-------|-------------|---------------|
| **M**olecule | Work template with TOML frontmatter | `plugin.md` |
| **E**phemeral | Plugin-run wisps - high-volume, digestible | Patrol wisps |
| **O**bservable | Plugin runs appear in activity feed | `bd activity` |
| **W**orkflow | Gate → Dispatch → Execute → Record → Digest | Full lifecycle |

### Pattern: Discover, Don't Track

> **"Reality is truth. State is derived."**

Plugin state (last run, run count, results) lives on the ledger as wisps, not in shadow state files. Gate evaluation queries the ledger directly.

```
Bad: Shadow state file
  ~/gt/plugins/last_run.json

Good: Derived from ledger
  bd list --wisp-type plugin-run --plugin=rebuild-gt
```

---

## 6. Issue-Oriented Orchestration

### Principle

All work is tracked as **structured issues** with dependencies, not just tasks or commands.

### Beads as Orchestration

Work is managed through Beads issue tracker:
- **Atomic**: Each issue is a discrete unit of work
- **Dependency-aware**: Issues block/unblock based on dependencies
- **Claimable**: Atomic claim operation prevents conflicts
- **Observable**: Full audit trail of changes

### The VC Workflow Loop

```
Loop {
  1. Claim ready issue (atomic SQL)
     ↓
  2. AI Assessment: strategy, steps, risks
     ↓
  3. Execute via agent
     ↓
  4. AI Analysis: extract punted work, bugs
     ↓
  5. Auto-create discovered issues
     ↓
  6. Quality gates (test, lint, build)
     ↓
  7. AI decides: close, partial, or blocked
}
```

### Benefits

1. **Persistence**: Work state in database, not agent memory
2. **Coordination**: Multiple agents work from same issue list
3. **Traceability**: Complete history of work
4. **Recovery**: Can resume from any point
5. **Metrics**: Can measure throughput, blockers, etc.

---

## 7. Sandboxed Execution

### Pattern

Each issue runs in an **isolated git worktree**:

```
Project Repo
    ├── .git/ (main)
    ├── main branch
    └── worktrees/
        ├── gt-abc12/ (isolated worktree)
        ├── gt-def34/ (isolated worktree)
        └── gt-ghi56/ (isolated worktree)
```

### Benefits

1. **Isolation**: Agents don't interfere with each other
2. **Safety**: Can't accidentally break main branch
3. **Parallelism**: Multiple agents work simultaneously
4. **Cleanliness**: Worktrees can be nuked after completion
5. **Version Control**: All changes tracked in git

### Implementation

```bash
# Create worktree for issue
git worktree add ../gt-abc12 branch-gt-abc12

# Agent works in isolated directory
cd ../gt-abc12
# ... make changes ...

# Complete and cleanup
gt done  # pushes, creates MR, nukes worktree
```

---

## 8. AI Supervision Pattern

### Principle

LLM assesses **before** and analyzes **after** agent execution, not just during.

### Pre-Execution (Assessment)

```
Before agent runs:
  1. AI analyzes issue requirements
  2. Estimates effort/complexity
  3. Identifies risks
  4. Suggests approach
  5. Determines if issue is well-defined
```

### Post-Execution (Analysis)

```
After agent completes:
  1. AI parses structured report
  2. Identifies punted work items
  3. Extracts discovered bugs/issues
  4. Determines success/partial/failure
  5. Creates follow-up issues if needed
```

### Structured Output

Agents produce structured JSON reports:

```json
{
  "status": "completed|blocked|partial|decomposed",
  "summary": "What was done",
  "punted": ["items not completed"],
  "discovered": ["new issues found"],
  "changes": ["files modified"],
  "tests": "test results"
}
```

---

## 9. Quality Gates

### Pattern

Automated checks ensure code quality before completion:

```
Agent completes work
    ↓
Quality Gates Run:
  - Test gate: Run test suite
  - Lint gate: Check code style
  - Build gate: Ensure compiles
    ↓
All gates pass?
  Yes → Mark complete
  No  → Report failure, create fix issue
```

### Implementation

Quality gates are:
- **Automated**: No human intervention
- **Fast**: Run in parallel where possible
- **Deterministic**: Same input → same result
- **Informative**: Clear failure messages

---

## 10. Tracer Bullet Development

### Principle

Get **end-to-end basics working** before adding bells and whistles.

### Approach

1. **Vertical Slice**: Implement a thin slice through all layers
2. **End-to-End First**: Get something working end-to-end quickly
3. **Iterate**: Add features incrementally
4. **Validate**: Ensure each iteration works before next

### Contrast

| Tracer Bullet | Big Bang |
|---------------|----------|
| Thin vertical slice | Build all layers fully |
| Works in hours/days | Works in weeks/months |
| Validates architecture early | Validates at end |
| Easy to course-correct | Expensive to change |

### VC Example

```
Phase 1: Bootstrap (2 weeks)
  - Basic REPL
  - Simple SQLite issue tracker
  - One agent (Amp)
  - Single quality gate (build)

Phase 2: Add Features
  - More agents
  - More quality gates
  - Better AI supervision
  - Optimization
```

---

## Summary Table

| Principle | Core Idea | Key Mechanism |
|-----------|-----------|---------------|
| **MEOW** | Molecular work decomposition | Convoys + beads + formulas |
| **GUPP** | Autonomous execution | Git hooks + self-driving agents |
| **NDI** | Reliable outcomes from unreliable parts | Persistence + oversight + recovery |
| **ZFC** | AI decides, code transports | No heuristics, LLM reasoning |
| **Issue-Oriented** | All work as structured issues | Beads dependency graph |
| **Sandboxed** | Isolated execution | Git worktrees |
| **AI Supervision** | Assess before, analyze after | Assessment + analysis phases |
| **Quality Gates** | Automated quality checks | Test + lint + build automation |
| **Tracer Bullet** | End-to-end first | Vertical slice development |

---

## Applying to Code Puppy

For Orchestra plugin in Code Puppy:

1. **MEOW**: Use `/convoy` to group work, `/spawn` to create agents
2. **GUPP**: Agents auto-execute work on their hook
3. **NDI**: Persistent beads state, witness monitoring
4. **ZFC**: Let AI decide, plugins provide transport
5. **Issue-Oriented**: Beads integration for work tracking
6. **Sandboxed**: Git worktrees for agent isolation
7. **AI Supervision**: Pre/post execution analysis
8. **Quality Gates**: Plugin-based validation
9. **Tracer Bullet**: Get basic `/spawn` → `/done` flow first

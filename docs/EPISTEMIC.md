# Epistemic Agent Runtime (EAR) Integration

Code Puppy now includes the **Epistemic Agent Runtime** — a structured methodology for building software through evidence-based reasoning.

> **The Core Insight:** Write down what you believe, how confident you are, and how you'd prove yourself wrong. That's it. Everything else — lenses, gates, the Ralph loop — is machinery to make that practice systematic and scalable.

## 🧠 What is EAR?

EAR provides a rigorous, 12-stage pipeline for going from idea → validated specs → working product:

```
Idea → Epistemic State → Lens Evaluation → Gap Analysis → Goal Emergence 
    → MVP Planning → Build Execution → Improvement Loop
```

**Core Philosophy: Emergence-first → Lens-driven → Goal-earned → Commit**

## � The Sibling Folder Pattern

EAR uses a **read-only template + spawned project** architecture:

```
parent-folder/
├── epistemic-project-template/    ← READ-ONLY reference (methodology)
│   ├── CLAUDE.md                  ← Agent instructions
│   ├── philosophy/                ← EAR philosophy
│   ├── ear-runtime/               ← Python EAR library
│   ├── process/                   ← Methodology docs
│   └── templates/                 ← Blank scaffolds
│
└── your-new-project/              ← WHERE WORK HAPPENS (spawned)
    ├── README.md
    ├── BUILD.md
    ├── epistemic/                 ← Your project's epistemic state
    ├── docs/                      ← Your analysis documents
    ├── specs/                     ← Your validated specifications
    └── src/                       ← Your actual code
```

**Why this matters:**
- **Template stays pristine** — You never corrupt methodology with project-specific stuff
- **Agent can reference both** — Works in your project but can look back at template for philosophy
- **Reusable** — Next project? Same template, new sibling folder
- **State versioning** — Track how understanding evolves over time ("git for beliefs")

## �🚀 Quick Start

### 1. Switch to the Epistemic Architect Agent

```
/agent epistemic-architect
```

### 2. Start an Epistemic Session

```
/epistemic start my-project
```

### 3. Describe Your Project

> "I want to build an API that helps developers track their technical debt..."

The agent will guide you through structured planning before any code is written.

## 📋 The 12-Stage Pipeline

| Stage | Name | What Happens |
|-------|------|--------------|
| 0 | Philosophical Foundation | Internalize Ralph Loops and core principles |
| 1 | Epistemic State Creation | Surface assumptions, hypotheses, constraints |
| 2 | Lens Evaluation | Apply 7 expert perspectives |
| 3 | Gap Analysis | Identify CRITICAL/HIGH/MEDIUM/LOW gaps |
| 4 | Goal Emergence | Generate candidates, run through 6 gates |
| 5 | MVP Planning | Create minimal viable plan with rollback |
| 6 | Spec Generation | Generate full specs, readiness check |
| 7 | Build Execution | Phase → Milestone → Checkpoint → Verify |
| 8 | Improvement Audit | Evidence → Analysis → Recommendation loop |
| 9 | Gap Re-Inspection | What new gaps emerged? Re-validate |
| 10 | Question Tracking | Update epistemic state, close hypotheses |
| 11 | Verification Audit | End-to-end check across all layers |
| 12 | Documentation Sync | Update all docs, then loop to Stage 8 |

## 🔍 The 7 Expert Lenses

Each lens examines your project from a specific perspective:

| Lens | Question | Outputs |
|------|----------|---------|
| 🧠 **Philosophy** | What are we assuming? | Hidden assumptions, category errors |
| 📊 **Data Science** | Can we measure this? | Metrics plan, experiment design |
| 🛡️ **Safety/Risk** | What could go wrong? | Risk flags, abuse vectors |
| 🔷 **Topology** | What's the structure? | Dependencies, phase transitions |
| ∑ **Theoretical Math** | Is this consistent? | Minimal axioms, counterexamples |
| ⚙️ **Systems Engineering** | Can we build this? | Service boundaries, failure recovery |
| 👤 **Product/UX** | Does this help users? | Value hypotheses, MVP scope |

## ✅ The 6 Quality Gates

Goals must pass ALL gates before becoming actionable:

1. **👁️ Observables** — Does it have measurable outcomes?
2. **🧪 Testability** — Clear success/failure criteria?
3. **↩️ Reversibility** — Is there a rollback plan?
4. **📈 Confidence** — Is confidence ≥ 0.6?
5. **🤝 Lens Agreement** — Do 3+ lenses approve?
6. **📚 Evidence Grounding** — Based on actual evidence?

## 🔄 Ralph (Wiggum) Loops

The universal primitive for all epistemic work:

```
    ┌─────────────────────────────────────┐
    │                                     │
    ▼                                     │
┌───────┐    ┌───────┐    ┌───────┐    ┌───────┐
│OBSERVE│ →  │ORIENT │ →  │DECIDE │ →  │ ACT   │
└───────┘    └───────┘    └───────┘    └───────┘
    ▲                                     │
    │                                     │
    └─────────────────────────────────────┘
```

Use `/ralph` to get guidance on each step.

### 🤝 OODA-Driven Agent Delegation

The Epistemic Architect **orchestrates work** by delegating to specialist agents based on OODA phase and **workload type**:

**OBSERVE Phase** → Architect uses own tools
- File exploration (`list_files`, `read_file`, `grep`)
- Project setup (`agent_run_shell_command`)
- Direct observation to build epistemic state

**ORIENT Phase** → Delegate to REASONING workload specialists
- `invoke_agent("security-auditor", ...)` — Security analysis [REASONING]
- `invoke_agent("code-reviewer", ...)` — Code quality review [REASONING]
- `invoke_agent("qa-expert", ...)` — Test strategy [REASONING]
- `invoke_agent("shepherd", ...)` — Acceptance criteria review [REASONING]
- `invoke_agent("watchdog", ...)` — QA validation [REASONING]
- Multiple analyses run **in parallel** for efficiency

**DECIDE Phase** → Use ORCHESTRATOR workload agents
- `invoke_agent("planning-agent", ...)` — Task breakdown [ORCHESTRATOR]
- `invoke_agent("pack-leader", ...)` — Multi-agent coordination [ORCHESTRATOR]
- `invoke_agent("helios", ...)` — Architecture design [ORCHESTRATOR]
- Architect synthesizes results and makes strategic decisions

**ACT Phase** → Delegate to CODING/LIBRARIAN workload specialists
- `invoke_agent("python-programmer", ...)` — Python implementation [CODING]
- `invoke_agent("test-generator", ...)` — Test creation [CODING]
- `invoke_agent("doc-writer", ...)` — Documentation [LIBRARIAN]
- Parallel implementation by specialists

**Workload-Based Model Routing:**
- **ORCHESTRATOR**: Kimi K2.5 / Qwen3 — Complex reasoning, planning
- **REASONING**: DeepSeek R1 / GPT-5.2 — Analysis, code review
- **CODING**: Cerebras GLM 4.7 — Fast code generation
- **LIBRARIAN**: Haiku / Gemini Flash — Docs, context (cheap)

**Benefits:**
- ✅ Each agent uses optimal model based on workload type
- ✅ Parallel execution speeds up ORIENT and ACT phases
- ✅ Cost-efficient: expensive models only when needed
- ✅ Automatic failover via `RateLimitFailover` chains

## 📁 Commands Reference

### Session Management

| Command | Description |
|---------|-------------|
| `/epistemic start <project>` | Start a new epistemic session |
| `/epistemic status` | Show current session status |
| `/epistemic stage` | Advance to next pipeline stage |
| `/epistemic stage <n>` | Jump to specific stage (0-12) |
| `/epistemic pause <reason>` | Pause with a reason |
| `/epistemic resume` | Resume paused session |
| `/epistemic save` | Save state to `epistemic/state.json` |
| `/epistemic load` | Load state from `epistemic/state.json` |
| `/epistemic end` | End the current session |

### Analysis Tools

| Command | Description |
|---------|-------------|
| `/epistemic gaps` | Show identified gaps by severity |
| `/epistemic assumptions` | Show recorded assumptions with confidence |
| `/lens <name>` | Apply a specific lens (philosophy, data, safety, etc.) |
| `/lens all` | Show all 7 lenses |
| `/ralph` | Show Ralph Loop structure |
| `/ralph <step>` | Focus on specific step (observe, orient, decide, act) |

## 📂 Artifact Structure

When you scaffold an epistemic project, it creates:

```
project/
├── README.md
├── BUILD.md              ← The execution plan
├── CHANGELOG.md
├── epistemic/            ← Epistemic state (Stage 1)
│   ├── state.json        ← Machine-readable state
│   ├── assumptions.md    ← Documented assumptions
│   ├── hypotheses.md     ← Testable hypotheses
│   ├── constraints.md    ← Hard and soft constraints
│   └── evidence.md       ← Supporting evidence
├── docs/                 ← Analysis documents (Stages 2-5)
│   ├── lens-evaluation.md
│   ├── gap-analysis.md
│   ├── goals-and-gates.md
│   └── improvement-plan.md
└── specs/                ← Specifications (Stage 6)
    ├── entities.md       ← Data model
    ├── personas.md       ← User personas
    ├── critical-flows.md ← Must-work user flows
    ├── metrics.md        ← Success metrics
    └── trust-safety.md   ← Trust and safety policies
```

## ⏸️ When to Pause

The agent will pause and ask for human input when:

- 🔴 CRITICAL gap found
- ❌ Goals fail gates
- ⚠️ Readiness check fails
- 🤔 Lenses strongly disagree
- 📉 Confidence drops below 0.6
- 🛡️ Safety lens raises risk flags
- ✅ After each major phase

## 💡 Best Practices

1. **Ask "What would change my mind?"** for every assumption
2. **Quantify confidence** (0.0–1.0) to make beliefs explicit
3. **Name the lens** that surfaced each concern
4. **Track provenance** — every claim links to evidence
5. **Don't block on uncontrollables** — build measurement, not outcomes
6. **Small reversible steps** over big irreversible leaps

## 🔗 EAR Runtime Library

Code Puppy includes the full EAR Python library as a submodule at `code_puppy/epistemic/`. This provides:

- `ear.core` — State management, provenance, Ralph loops
- `ear.lenses` — All 7 expert lenses
- `ear.goals` — Goal candidates, gates, MVP planning
- `ear.sandbox` — Agent simulation and experimentation
- `ear.commitment` — Review gates, testing, rollback
- `ear.control` — Pause triggers, human-in-the-loop
- `ear.versioning` — State commits, branches, diffs

### Using EAR Programmatically

```python
from ear.core import EpistemicState, RalphLoop
from ear.lenses import create_default_registry
from ear.goals import GoalGenerator, GateKeeper

# Create epistemic state
state = EpistemicState()
state.add_assumption("Users want fast responses", confidence=0.8)

# Apply lenses
registry = create_default_registry()
outputs = registry.evaluate_all(state)

# Generate and validate goals
generator = GoalGenerator(state)
candidates = generator.generate_candidates()
gatekeeper = GateKeeper()
approved = gatekeeper.filter_passing(candidates, state)
```

## 📊 4-Tier Adoption Model

EAR scales from solo projects to enterprise:

| Tier | Context | How EAR Helps |
|------|---------|---------------|
| **Tier 1** | Solo projects / prototypes | `ear init` scaffolds epistemic state. Run gap analysis to find what you haven't thought about. "What don't I know?" |
| **Tier 2** | Team projects / MVPs | Lenses in sprint planning. Track assumptions as first-class citizens with confidence scores. Test gates before shipping. |
| **Tier 3** | Production systems | Custom domain lenses (e.g., ComplianceLens). Automate epistemic state updates from A/B tests. Version your epistemic state. 600-line file cap. |
| **Tier 4** | Enterprise / multi-service | Per-service epistemic states. Cross-service dependency tracking via topology lens. Monthly "Epistemic Review" meetings. Governance gates before major decisions. |

## 🏭 Production Integration

For existing production systems, EAR works as an **overlay methodology** — not a rewrite:

### 1. Wrap Existing Decisions

Document what you currently assume is true about your product:

```python
state = EpistemicState()
state.add_assumption(
    content="Users prefer speed over accuracy",
    source="2024 user research",
    confidence=0.7
)
```

### 2. Run Lenses Against Current State

Let the 7 lenses find gaps you haven't considered:
- Safety risks not yet mitigated
- Metrics you aren't measuring
- Assumptions you haven't validated

### 3. Use Gates Before Major Changes

Before a feature launch, require the 6-gate protocol:
- Does it have measurable outcomes?
- Clear success criteria?
- Rollback plan?
- Sufficient confidence?
- Lens agreement?
- Evidence grounding?

### 4. Automate with CI

Run epistemic health checks in your pipeline:

```bash
# In CI pipeline
ear status --format json > epistemic-report.json
```

Publish epistemic health dashboards alongside your normal metrics.

### 5. Version Your Epistemic State

Track how your team's understanding evolves:

```bash
# State commits (like git for beliefs)
ear commit -m "Updated user retention hypothesis after A/B test"
ear diff HEAD~1  # See what changed
```

## 🤝 Integration with Other Agents

The Epistemic Architect works well alongside other agents:

- Use **Pack Leader** for actual code execution after specs are validated
- Use **Pack Leader Cerebras Efficient** for token-conscious implementation
- Use **Code Reviewer** agents to validate implementation against specs
- Use **QA Expert** to test against the metrics defined in specs

Example workflow:
```
1. /agent epistemic-architect  → Plan and validate
2. /epistemic save             → Save the plan
3. /agent pack-leader          → Execute the build
4. /agent code-reviewer        → Review implementation
5. /agent epistemic-architect  → Run improvement audit (Stage 8)
```

## � Logfire Telemetry for EAR Loops

All EAR loop phases emit **real-time telemetry** to track confidence and completion:

| Event | Source | Purpose |
|-------|--------|---------|
| `ear_phase` | `ralph_loop.py` | Tracks OBSERVE→ORIENT→DECIDE→ACT with confidence scores |

**Health Check Queries:** See [LOGFIRE-OBSERVABILITY.md](LOGFIRE-OBSERVABILITY.md) for SQL to verify:
- ✅ EAR loops complete >90% of the time
- ✅ Error rate <10%
- ✅ Average confidence scores by phase

## �📚 Further Reading

- [EAR Philosophy Documentation](code_puppy/epistemic/philosophy/project-plan.md)
- [Build Methodology](code_puppy/epistemic/process/build-methodology.md)
- [EAR Audit Loop](code_puppy/epistemic/process/ear-audit-loop.md)
- [Verification Checklist](code_puppy/epistemic/process/verification-checklist.md)

---

*The Epistemic Agent Runtime was developed based on principles from epistemology, systems engineering, and evidence-based software development.*

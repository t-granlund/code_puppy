Current reasoning:
I've now read all the key documentation files. Let me synthesize a comprehensive catch-up for the user covering their three questions:

 1 How CLAUDE.md guides the terminal LLM agent
 2 The "split" - creating the sibling folder
 3 How EAR travels with projects and is useful in dev vs production

The documentation is actually very thorough and well-connected. Let me organize this clearly.

Planned next steps:
Present a clear, structured summary of the entire system from the user's perspective.


 AGENT RESPONSE
I've read through all your documentation. Here's a full catch-up on how everything connects:

──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

🧠 Part 1: How CLAUDE.md Guides the Terminal Agent
──────────────────────────────────────────────────

The `CLAUDE.md` file is essentially the agent's operating manual. When you open this workspace in Claude Code (or any Claude-powered terminal), Claude reads CLAUDE.md first and treats it as standing instructions.

What It Tells the Agent

The very first lines set the tone:

│ "You are inside an epistemic project template workspace. Your job is to guide the user through a rigorous, structured process to go from idea → validated specs → built product. **Do NOT modify files in this templa
│ te.** You will create a new project in a sibling folder."

From there, it defines a 12-stage pipeline the agent must follow:

┌───────┬─────────────────────────────────────────────────────────────────────────┬────────────────────────────────────────────┐
│ Stage │ What Happens                                                            │ Output                                     │
├───────┼─────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────┤
│ 0     │ Read philosophy/project-plan.md — internalize the entire EAR philosophy │ Agent knowledge                            │
│ 1     │ Interview the user, surface hidden assumptions                          │ epistemic/state.json + companion .md files │
│ 2     │ Apply all 7 lenses to the epistemic state                               │ docs/lens-evaluation.md                    │
│ 3     │ Gap analysis — what's missing?                                          │ docs/gap-analysis.md                       │
│ 4     │ Goal emergence through 6 epistemic gates                                │ docs/goals-and-gates.md                    │
│ 5     │ MVP planning — smallest commitment that reduces uncertainty             │ BUILD.md                                   │
│ 6     │ Spec generation + readiness check                                       │ specs/ folder + explicit user approval     │
│ 7     │ Build execution — phase by phase with checkpoints                       │ Actual code in src/                        │
│ 8     │ EAR audit loop (Evidence → Analysis → Recommendation)                   │ docs/improvement-plan.md                   │
│ 9     │ Re-run gap analysis — what new gaps emerged?                            │ Updated gaps                               │
│ 10    │ Question tracking + epistemic state update                              │ State commits                              │
│ 11    │ Verification audit — end-to-end checklist                               │ Verification report                        │
│ 12    │ Documentation sync, then loop back to Stage 8                           │ Updated docs, then repeat                  │
└───────┴─────────────────────────────────────────────────────────────────────────┴────────────────────────────────────────────┘

What Results From It

The agent doesn't just freestyle — it's constrained to a rigorous process:

• It must interview you before building anything (Stage 1)
• It must apply lenses that challenge assumptions (Stage 2)
• It must check 6 gates before any goal becomes actionable (Stage 4)
• It must get your explicit approval before writing code (Stage 6)
• It must pause when it hits uncertainty, risk flags, or lens disagreements
• After building, it loops forever through audit → gap check → improve (Stages 8-12)

The supporting process docs flesh this out:
• `process/build-methodology.md` — Phases → Milestones → Checkpoints, "don't block on uncontrollables"
• `process/ear-audit-loop.md` — Evidence → Analysis → Recommendation cycle
• `process/verification-checklist.md` — Layer-by-layer audit (data, API, UI, auth, security, mobile, docs)
• `process/question-tracking.md` — 🔴 blocking / 🟡 important / 🟢 later / ✅ answered

──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

🔀 Part 2: The Split — Creating the Sibling Folder
──────────────────────────────────────────────────

This is a key design decision documented in CLAUDE.md. The template is read-only reference. Real work happens in a sibling project folder.

How It Works

When you describe a project idea and pass Stage 6's readiness check:

parent-folder/
├── epistemic-project-template/    ← READ-ONLY reference (this repo)
│   ├── CLAUDE.md                  ← Agent instructions
│   ├── philosophy/                ← EAR philosophy
│   ├── ear-runtime/               ← Python EAR library
│   ├── process/                   ← Methodology docs
│   └── templates/                 ← Blank scaffolds
│
└── your-new-project/              ← WHERE WORK HAPPENS (spawned)
    ├── README.md
    ├── BUILD.md                   ← From Stage 5
    ├── CHANGELOG.md
    ├── epistemic/                 ← From Stage 1 (your beliefs)
    │   ├── state.json
    │   ├── assumptions.md
    │   ├── hypotheses.md
    │   ├── constraints.md
    │   └── evidence.md
    ├── specs/                     ← From Stage 6 (validated specs)
    │   ├── entities.md
    │   ├── personas.md
    │   ├── critical-flows.md
    │   ├── metrics.md
    │   └── trust-safety.md
    ├── docs/                      ← From Stages 2-5 (analysis)
    │   ├── vision.md
    │   ├── lens-evaluation.md
    │   ├── gap-analysis.md
    │   ├── goals-and-gates.md
    │   └── improvement-plan.md
    └── src/                       ← From Stage 7+ (actual code)

Why the Split Matters

• Template stays pristine — You never corrupt your methodology by mixing it with project-specific stuff
• Agent can reference both — It works in your-new-project/ but can look back at epistemic-project-template/ for the philosophy, lenses, and process docs anytime
• Reusable — Next project? Same template, new sibling folder. The EAR methodology applies fresh each time
• The `templates/` folder has 13 blank scaffolds with placeholders — those get copied into the new project and filled in during the pipeline

──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

🔬 Part 3: How EAR Travels With the Project
───────────────────────────────────────────

This is where it gets really interesting. The documentation describes two distinct ways EAR is useful, and they map to your question about dev mode vs. production:

Dev Mode: EAR as Your Reasoning Engine

In the IMPROVEMENT_PLAN.md, this is organized as a 4-tier system:

┌────────┬────────────────────────────┬──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Tier   │ Context                    │ How EAR Helps                                                                                                                                                    │
├────────┼────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Tier 1 │ Solo projects / prototypes │ ear init scaffolds epistemic state. Run gap analysis to find what you haven't thought about. "What don't I know?"                                                │
│ Tier 2 │ Team projects / MVPs       │ Lenses in sprint planning. Track assumptions as first-class citizens with confidence scores. Test gates before shipping.                                         │
│ Tier 3 │ Production systems         │ Custom domain lenses (e.g., ComplianceLens). Automate epistemic state updates from A/B tests. Version your epistemic state. 600-line file cap.                   │
│ Tier 4 │ Enterprise / multi-service │ Per-service epistemic states. Cross-service dependency tracking via topology lens. Monthly "Epistemic Review" meetings. Governance gates before major decisions. │
└────────┴────────────────────────────┴──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

The practical dev workflow looks like:

 python ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# 1. State captures what you believe
state = EpistemicState()
state.add_assumption(content="Users want X", source="interviews", confidence=0.7)
state.add_hypothesis(claim="Feature Y will increase retention 20%",
                     falsification_criteria="If retention < 10%, hypothesis is false")

# 2. Lenses challenge your beliefs
registry = create_default_registry()
outputs = registry.evaluate_all(state)
# Each lens returns: score, recommendations, risk flags, confidence updates

# 3. Goals must EARN their way through 6 gates
# (observables, testability, reversibility, confidence, lens agreement, evidence)

# 4. Only then do you commit to building
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

Production Mode: EAR as a Proposed Upgrade Path

For existing production services, the docs propose EAR as an overlay methodology — not a rewrite:

• Wrap your existing decisions in epistemic state — Document what you currently assume is true about your product, with confidence levels (DB NOTE: This should exist in the spawned, stand alone sibling project (your app build), so you shouldn't need to "wrap it". It should be available for reference, along with old, outdated states for context history of important decisions).
• Run lenses against that state — Let the 7 lenses find gaps (safety risks you haven't considered, metrics you aren't measuring, assumptions you haven't validated)
• Use gates before major changes — Before a feature launch, require the 6-gate protocol: Does it have measurable outcomes? Success criteria? Rollback plan? Sufficient confidence? Lens agreement? Evidence grounding? Just ask it from any point of expertise you want to request - the lenses got your back. You can have it build a new proposal/implementation plan, then update codebase, and check changes, and build a new updated epistemic state.
• Automate with CI — The docs propose running ear status --format json in your CI pipeline and publishing epistemic health dashboards (DB NOTE: Need to look into this further to understand capabilities)
• State versioning — Track how your team's understanding evolves over time with state commits (like git for beliefs) - This is your "states". Ralphs always should refer to the state and the implementation plan for (almost) full coverage.

The Key Insight (from the docs)

The IMPROVEMENT_PLAN.md nails it:

│ "The single most impactful practice from EAR is this: **Write down what you believe, how confident you are, and how you'd prove yourself wrong.** That's it. Everything else — lenses, gates, the RALPH loop — is mac
│ hinery to make that practice systematic and scalable."

And from philosophy/project-plan.md, the deeper point:

│ "Traditional systems assume: agents exist to complete a task. Your system allows: agents exist to maintain coherence with preferences and only later 'earn' tasks. This makes the system closer to emergent dynamics
│ (ecology, markets, immune systems) than to workflow automation."

──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

📊 Quick Reference: The Full Picture
────────────────────────────────────

┌─────────────────────────────────────────────────────────────────┐
│                    CLAUDE.md reads this:                         │
│                                                                 │
│  philosophy/project-plan.md  ← The "constitution" (EAR theory) │
│  process/*.md                ← The "laws" (methodology)         │
│  templates/                  ← The "forms" (blank scaffolds)    │
│  ear-runtime/                ← The "engine" (Python library)    │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                    Agent follows 12 stages:                      │
│                                                                 │
│  Interview → Lenses → Gaps → Gates → MVP → Specs → BUILD       │
│                                    ↑                            │
│                                    └── Audit loop (8→12→8→...)  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                    Output goes to sibling folder:                │
│                                                                 │
│  ../your-project/epistemic/  ← Your beliefs (versioned)        │
│  ../your-project/specs/      ← Validated specifications        │
│  ../your-project/docs/       ← Analysis & plans                │
│  ../your-project/src/        ← Actual code                     │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                    EAR stays useful because:                     │
│                                                                 │
│  Dev mode:  Gap analysis, lens evaluations, gate checks         │
│  Prod mode: CI integration, epistemic dashboards, governance    │
│  Always:    "What do we believe? How confident? How to disprove?"│
└─────────────────────────────────────────────────────────────────┘

──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

That's the full picture. Your documentation is honestly very thorough — the philosophy doc alone is nearly 5,500 words and covers everything from the Ralph Loop invariant to language game sandboxes. Want me to dive deeper into any specific piece?
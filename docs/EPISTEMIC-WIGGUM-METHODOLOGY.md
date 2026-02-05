# Epistemic Architect Wiggum Methodology

> **The Two-Phase Workflow**: Interactive discovery → Autonomous execution

This document describes how the Epistemic Architect agent uses the `/wiggum` autonomous loop to go from idea → production-ready software with full verification.

---

## 🎯 Overview

The Epistemic Architect operates in two distinct phases:

| Phase | Mode | Stages | Key Tools | Human Involvement |
|-------|------|--------|-----------|-------------------|
| **Phase 1** | Interactive | 0-6 | `ask_user_question` | High - User answers questions |
| **Phase 2** | Autonomous | 7-12 | `complete_wiggum_loop` | Low - Only blocks on CRITICAL gaps |

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    EPISTEMIC ARCHITECT WORKFLOW                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  PHASE 1: INTERACTIVE                    PHASE 2: AUTONOMOUS            │
│  ┌─────────────────────┐                 ┌─────────────────────┐        │
│  │ 0. Philosophy       │                 │ 7. Build Execution  │        │
│  │ 1. Interview        │──┐              │ 8. Improvement Audit│        │
│  │ 2. Lens Evaluation  │  │              │ 9. Gap Re-Inspection│        │
│  │ 3. Gap Analysis     │  │  /wiggum    │ 10. Question Track  │        │
│  │ 4. Goal Emergence   │  │───────────►│ 11. Verification    │        │
│  │ 5. MVP Planning     │  │              │ 12. Doc Sync        │        │
│  │ 6. Spec Generation  │──┘              └──────────┬──────────┘        │
│  └─────────────────────┘                            │                   │
│         ▲                                           │                   │
│         │ ask_user_question                         │                   │
│         │ (gather epistemic state)                  │                   │
│                                                     ▼                   │
│                                          complete_wiggum_loop()         │
│                                          (when all milestones done)     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Phase 1: Interactive Discovery (Stages 0-6)

### Stage 0: Philosophical Foundation
- Agent introduces itself and the BART methodology
- Sets expectations for the structured process

### Stage 1: Epistemic State Interview

The agent uses `ask_user_question` to gather structured input:

```
ask_user_question(questions=[
    {
        "question": "What type of application are you building?",
        "header": "App Type",
        "options": [
            {"label": "Web App", "description": "Browser-based application"},
            {"label": "API Service", "description": "Backend REST/GraphQL API"},
            {"label": "CLI Tool", "description": "Command-line application"},
            {"label": "Library", "description": "Reusable package/module"}
        ]
    },
    {
        "question": "What is the primary programming language?",
        "header": "Language",
        "options": [
            {"label": "Python"},
            {"label": "TypeScript"},
            {"label": "Go"},
            {"label": "Rust"}
        ]
    }
])
```

**Output**: `epistemic/state.json`
```json
{
  "assumptions": [
    {"text": "Users have modern browsers", "confidence": 0.9}
  ],
  "hypotheses": [
    {"claim": "OAuth will handle all auth needs", "falsification_criteria": "Enterprise needs SAML"}
  ],
  "hard_constraints": ["Must run on Python 3.10+"],
  "soft_constraints": ["Prefer PostgreSQL"],
  "evidence": []
}
```

### Stages 2-3: Lens Evaluation & Gap Analysis

Agent applies 7 lenses and identifies gaps:

| Lens | Question | Typical Gaps |
|------|----------|--------------|
| 🧠 Philosophy | What are we assuming? | Hidden category errors |
| 📊 Data Science | Can we measure this? | Missing metrics |
| 🛡️ Safety/Risk | What could go wrong? | Unhandled failures |
| 🔷 Topology | Is the structure stable? | Circular dependencies |
| ∑ Math | Is it logically consistent? | Edge case contradictions |
| ⚙️ Systems | Can we build this? | Integration unknowns |
| 👤 Product/UX | Does it help users? | Scope creep risks |

**Output**: `docs/gap-analysis.md`

### Stages 4-6: Goal Validation & Planning

Goals pass through 6 Quality Gates:
1. ✅ Observable outcomes
2. ✅ Testable success criteria
3. ✅ Reversibility (rollback plan)
4. ✅ Confidence ≥ 0.6
5. ✅ 3+ lenses approve
6. ✅ Evidence-grounded

**Output**: `BUILD.md` with milestones

### Stage 7: Pre-Flight Authentication Check 🔐

**CRITICAL GATE**: Before Phase 2 (wiggum) can begin, all authentication requirements must be verified.

#### Why Pre-Flight Auth Matters

When building an application, dashboard, or integration, you typically need:
- **Azure CLI** auth to deploy infrastructure (requires UPN, possibly admin permissions)
- **App Registrations** for OAuth/Graph API access (requires tenant admin or delegated permissions)
- **Database credentials** for data storage
- **Third-party API keys** for integrations
- **Browser automation fallback** for services without CLI/API access

The Pre-Flight system ensures all these are in place BEFORE autonomous execution begins.

#### How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PRE-FLIGHT AUTH WORKFLOW                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. DETECT REQUIREMENTS                                             │
│     ├── Scan epistemic/state.json for keywords                      │
│     ├── "Azure" → Azure CLI auth needed                             │
│     ├── "Graph API" → OAuth app registration needed                 │
│     ├── "PostgreSQL" → DATABASE_URL needed                          │
│     └── Custom services → add_auth_requirement()                    │
│                                                                     │
│  2. CREATE CHECKLIST                                                │
│     └── epistemic/auth-checklist.json                               │
│         ├── id: "azure-cli"                                         │
│         ├── status: "not_checked"                                   │
│         ├── priority: "critical"                                    │
│         └── verification_command: "az account show"                 │
│                                                                     │
│  3. GUIDE USER THROUGH SETUP                                        │
│     ├── ask_user_question() for UPN, tenant, subscription           │
│     ├── Provide CLI commands to authenticate                        │
│     └── For browser-only services, document manual steps            │
│                                                                     │
│  4. VERIFY ALL REQUIREMENTS                                         │
│     ├── preflight_auth_check() runs verification commands           │
│     ├── Updates status: passed/failed/missing                       │
│     └── Returns ready_for_phase2: true/false                        │
│                                                                     │
│  5. GATE CHECK                                                      │
│     ├── ready_for_phase2: true → Proceed to /wiggum                 │
│     └── ready_for_phase2: false → Block, show missing requirements  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### Auth Requirement Categories

| Category | Examples | Verification Method |
|----------|----------|---------------------|
| `CLI_AUTH` | Azure CLI, AWS CLI, gcloud, kubectl | Run verification command |
| `OAUTH_APP` | Azure AD app, Google OAuth | Check app registration exists |
| `API_KEY` | OPENAI_API_KEY, STRIPE_API_KEY | Check env var set |
| `BROWSER_SESSION` | Admin portals without API | Document manual login steps |
| `DATABASE` | PostgreSQL, MySQL, CosmosDB | Check DATABASE_URL |
| `SERVICE_PRINCIPAL` | CI/CD identity | Check client credentials |

#### Example Pre-Flight Questions

```python
ask_user_question(questions=[
    {
        "question": "What is your Azure User Principal Name (email)?",
        "header": "Azure UPN",
        "options": [
            {"label": "I'll type it", "description": "e.g., user@company.onmicrosoft.com"},
            {"label": "Already logged in", "description": "Use existing az login session"}
        ]
    },
    {
        "question": "Do you have permissions to create App Registrations?",
        "header": "Permissions",
        "options": [
            {"label": "Yes, I'm a tenant admin"},
            {"label": "No, I need IT to create it"},
            {"label": "I have delegated permissions"}
        ]
    },
    {
        "question": "Does this integration require Microsoft Graph API?",
        "header": "Graph API",
        "options": [
            {"label": "Yes", "description": "Need User.Read, Mail.Send, etc."},
            {"label": "No", "description": "No M365 integration needed"}
        ]
    }
])
```

#### Browser Automation Fallback

For services without CLI/API access (e.g., admin portals, legacy systems):

1. Agent creates a browser automation agent or tool via `invoke_agent("helios", "...")`
2. The automation agent uses Playwright to:
   - Navigate to login page
   - Wait for user to authenticate (interactive)
   - Capture session cookies/tokens
3. Session persists for wiggum execution

**Output**: `epistemic/auth-checklist.json`

```json
{
  "project_name": "my-dashboard",
  "ready_for_phase2": true,
  "requirements": [
    {
      "id": "azure-cli",
      "name": "Azure CLI Authentication",
      "status": "passed",
      "user_upn": "user@company.com",
      "tenant_id": "abc123..."
    },
    {
      "id": "graph-api",
      "name": "Microsoft Graph API Access",
      "status": "passed",
      "required_permissions": ["User.Read", "Mail.Send"]
    }
  ]
}
```

---

## 🍩 Phase 2: Autonomous Execution (Wiggum Mode)

### Activating Wiggum Mode

Once Phase 1 artifacts are complete AND `preflight_auth_check()` returns `ready_for_phase2: true`, the user runs:

```
/wiggum Execute the next milestone from BUILD.md. Read epistemic/state.json 
for current state. Delegate implementation to appropriate agents. Update 
CHECKPOINT.md with results. If all milestones complete and verified, call 
complete_wiggum_loop().
```

### Each Wiggum Iteration

```
┌────────────────────────────────────────────────────────────────────┐
│                     WIGGUM LOOP ITERATION                          │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  1. READ STATE                                                     │
│     ├── epistemic/state.json (current beliefs)                     │
│     ├── BUILD.md (milestone list)                                  │
│     └── CHECKPOINT.md (progress)                                   │
│                                                                    │
│  2. OBSERVE (Use exploration tools)                                │
│     ├── list_files() - Discover project structure                  │
│     ├── read_file() - Examine current code                         │
│     └── grep() - Search for patterns                               │
│                                                                    │
│  3. ORIENT (Delegate to REASONING agents)                          │
│     ├── invoke_agent("security-auditor", ...)                      │
│     ├── invoke_agent("code-reviewer", ...)                         │
│     └── invoke_agent("qa-expert", ...)                             │
│                                                                    │
│  4. DECIDE (Synthesize and plan)                                   │
│     ├── Update BUILD.md with findings                              │
│     └── Determine specific implementation tasks                    │
│                                                                    │
│  5. ACT (Delegate to CODING agents)                                │
│     ├── invoke_agent("python-programmer", ...)                     │
│     ├── invoke_agent("test-generator", ...)                        │
│     └── invoke_agent("doc-writer", ...)                            │
│                                                                    │
│  6. UPDATE CHECKPOINT                                              │
│     ├── Mark milestone complete                                    │
│     ├── Update iteration count                                     │
│     └── Document what was done                                     │
│                                                                    │
│  7. DECISION POINT                                                 │
│     ├── More milestones? → Continue loop                           │
│     └── All complete? → complete_wiggum_loop()                     │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### CHECKPOINT.md Format

The agent maintains a checkpoint file that persists across wiggum iterations:

```markdown
# Epistemic Architect Checkpoint

## Current State
- **Phase**: Build Execution
- **Milestone**: 3/5 - API Authentication Layer
- **Iteration**: 7
- **Status**: IN_PROGRESS

## Completed Milestones
1. ✅ Project Scaffolding (Iteration 1-2)
2. ✅ Database Models (Iteration 3-4)  
3. ⏳ API Authentication Layer (Iteration 5-7)
4. ⬜ API Endpoints (Not started)
5. ⬜ Frontend Integration (Not started)

## Current Milestone Details
**Name**: API Authentication Layer
**Description**: Implement OAuth2 authentication with JWT tokens
**Files Modified**:
- src/auth/oauth.py (created)
- src/auth/jwt.py (created)
- tests/test_auth.py (in progress)

## Last Action (Iteration 7)
- Delegated to security-auditor for JWT implementation review
- Found issue: Token expiration not handled
- Delegated fix to python-programmer

## Next Action
- Verify security-auditor approval
- Complete test_auth.py with edge cases
- Run E2E auth flow test

## Blockers
None currently

## Verification Status
- [ ] Unit tests passing
- [ ] Security audit complete
- [ ] Integration tests passing
- [ ] Documentation updated
```

### Wiggum Termination

The agent calls `complete_wiggum_loop()` when ALL criteria are met:

```python
# Agent's decision logic
if all_milestones_complete and e2e_verified and security_approved:
    complete_wiggum_loop(
        reason="All 5 milestones complete. E2E tests passing. "
               "Security audit approved. Documentation updated."
    )
```

---

## 🔀 Model Routing During Wiggum

The model router ensures optimal model selection for each OODA phase:

| Phase | Workload | Primary Model | Fallback Chain |
|-------|----------|---------------|----------------|
| OBSERVE | - | (Agent's own tools) | - |
| ORIENT | REASONING | DeepSeek R1 | GPT 5.2 → Claude Sonnet |
| DECIDE | ORCHESTRATOR | Kimi K2.5 | Qwen3 → Claude Opus |
| ACT | CODING | Cerebras GLM 4.7 | Claude Haiku → Gemini Flash |

### Failover During Wiggum

The `RateLimitFailover` singleton persists across wiggum iterations:
- Rate-limited models are remembered
- Failover chains are pre-computed
- 429 errors automatically route to next model

---

## 📊 Telemetry During Wiggum

All wiggum iterations are traced via Logfire:

```
┌─────────────────────────────────────────────────────────────────┐
│                    LOGFIRE TELEMETRY                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Span: wiggum_loop                                              │
│  ├── iteration: 7                                               │
│  ├── milestone: "API Authentication"                            │
│  ├── duration_ms: 45000                                         │
│  │                                                              │
│  └── Nested Spans:                                              │
│      ├── observe_phase (list_files, read_file)                  │
│      ├── orient_phase (invoke_agent: security-auditor)          │
│      ├── decide_phase (update BUILD.md)                         │
│      ├── act_phase (invoke_agent: python-programmer)            │
│      └── checkpoint_update (edit_file: CHECKPOINT.md)           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Credentials & Authentication

Before wiggum can run autonomously, ensure:

1. **API Keys Configured**:
   ```bash
   code-puppy credentials
   ```
   Verify all required providers have valid keys.

2. **Failover Chains Available**:
   ```bash
   code-puppy validate-failover
   ```
   Ensure at least 2 models per workload type.

3. **Logfire Token (Optional)**:
   ```bash
   export LOGFIRE_TOKEN=your_token
   ```
   For telemetry during long-running wiggum loops.

---

## 🛡️ Safety Mechanisms

### Interactive Tool Blocking
During wiggum mode, `ask_user_question` returns an error:
```
"Interactive tools are disabled during /wiggum mode. 
Make a reasonable decision to proceed..."
```

### CRITICAL Gap Detection
If a CRITICAL gap is found during wiggum:
1. Agent updates CHECKPOINT.md with blocker
2. Calls `complete_wiggum_loop(reason="CRITICAL gap: [description]")`
3. User must resolve and restart

### Ctrl+C Safety
User can always interrupt wiggum via Ctrl+C.

---

## 📁 Artifact Structure (Complete)

After Phase 1 + Phase 2, the project has:

```
project/
├── README.md                    ← Updated with final state
├── BUILD.md                     ← All milestones marked ✅
├── CHECKPOINT.md                ← Final completion status
├── CHANGELOG.md                 ← Version history
│
├── epistemic/                   ← From Phase 1
│   ├── state.json              ← Final epistemic state
│   ├── assumptions.md          ← All assumptions validated
│   ├── hypotheses.md           ← Hypotheses resolved
│   ├── constraints.md          ← Constraints documented
│   └── evidence.md             ← Evidence collected
│
├── docs/                        ← From Phase 1 + 2
│   ├── lens-evaluation.md      ← 7 lens outputs
│   ├── gap-analysis.md         ← All gaps resolved
│   ├── goals-and-gates.md      ← Gate passage records
│   ├── improvement-plan.md     ← Future improvements
│   └── ARCHITECTURE.md         ← System architecture
│
├── specs/                       ← From Phase 1
│   ├── entities.md             ← Data models
│   ├── personas.md             ← User personas
│   ├── critical-flows.md       ← Key user journeys
│   ├── metrics.md              ← Success metrics
│   └── trust-safety.md         ← Security requirements
│
├── src/                         ← From Phase 2
│   └── (implementation)
│
└── tests/                       ← From Phase 2
    ├── unit/
    ├── integration/
    └── e2e/
```

---

## 🚀 Quick Start

1. **Start the Epistemic Architect**:
   ```
   /agent epistemic-architect
   ```

2. **Complete Phase 1 Interview**:
   - Answer structured questions via TUI
   - Review and approve BUILD.md

3. **Activate Wiggum Mode**:
   ```
   /wiggum Execute the next milestone from BUILD.md. Read epistemic/state.json 
   for current state. Delegate to appropriate agents. Update CHECKPOINT.md.
   If all milestones complete, call complete_wiggum_loop().
   ```

4. **Monitor Progress**:
   - Watch CHECKPOINT.md for status
   - Check Logfire for telemetry
   - Ctrl+C to interrupt if needed

5. **Completion**:
   - Agent calls `complete_wiggum_loop()`
   - Review final artifacts
   - Commit to git

---

## 📚 Related Documentation

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture
- [CEREBRAS.md](docs/CEREBRAS.md) - Model optimization
- [EPISTEMIC.md](docs/EPISTEMIC.md) - Epistemic methodology
- [LOGFIRE-INTEGRATION.md](docs/LOGFIRE-INTEGRATION.md) - Telemetry setup

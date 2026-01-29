# AUDIT-1.1 (Delta Only)
Purpose: add ONLY new implementation items beyond AUDIT-1.0.

## Why 1.1 exists
AUDIT-1.0 defines a baseline token-efficient pack leader, plus discovery and minimal enforcement utilities.  [oai_citation:1‡AUDIT-1.0.md](sediment://file_000000000dac720c881979156d7fe18d)  
AUDIT-1.1 adds deeper safeguards that prevent silent context bloat, runaway shell output, and provider rate limit churn, while enabling predictable multi provider routing later, without implementing a full router today.  [oai_citation:2‡AUDIT-1.0.md](sediment://file_000000000dac720c881979156d7fe18d)

---

## Part D, Enforced IO Budgeting (must be code enforced, not “best effort”)
1) Hard cap prompt size per request
   - Add a global, provider aware “max input budget” that the pack leader cannot exceed.
   - If budget would be exceeded, the agent must switch into “request narrowing mode” and ask for:
     - `git diff` only, or
     - file slices (explicit start,end), or
     - the last 120 to 200 lines of logs.
   - Add config knobs:
     - `TOKEN_BUDGET_INPUT_ESTIMATE`
     - `TOKEN_BUDGET_HARD_FAIL` (if exceeded, refuse the call)

2) Auto compaction policy
   - Implement a built in “compactor” that replaces old transcript history with a short structured summary:
     - goals, current branch, changed files, failing commands, current hypothesis, next 3 actions
   - Auto trigger compaction when:
     - 2 iterations completed, or
     - estimated input exceeds 70% of budget

3) File read and snippet policy
   - Add a file retrieval helper that enforces:
     - default max lines returned
     - must request “slice ranges” when asking for code context
   - Add a guardrail: “never include full files unless explicitly approved”

Acceptance criteria
- A single long debugging loop cannot grow the prompt unbounded, it must compact automatically.
- Agent refuses full repo or full file ingestion by default.

---

## Part E, Shell Output Governor (wrap execution centrally)
1) Central wrapper required
   - All shell execution must go through one function.
   - The wrapper must enforce:
     - output limit, default `tail -n 160`
     - timeout defaults
     - redaction for common secret patterns (basic regex is fine, never log matches)
2) Provide a per command override mechanism
   - Example: `--full-output` only allowed if explicitly set by user.
   - Default remains capped.
3) Persist short command metadata
   - Store:
     - command string
     - exit code
     - truncated output
     - elapsed ms
   - Do not store environment variables.

Acceptance criteria
- No agent can accidentally paste 5,000 lines into the model context.
- Normal failures still include enough output to debug.

---

## Part F, Cerebras Rate Limit Resilience (429 and 503 hardening)
1) Provider aware retry policy
   - Implement exponential backoff with jitter for 429 and 503.
   - Respect Retry-After if present, but enforce an upper bound.
2) Automatic request shaping under pressure
   - When 429 or 503 occurs:
     - reduce `max_completion_tokens` for follow up attempts
     - reduce temperature to 0
     - force “diff only, no restatement” system instruction
3) Concurrency limiter
   - Add a per provider max in flight request limit, default 1 for Cerebras.
   - Allow higher concurrency for providers that tolerate it, but keep Cerebras conservative.

Acceptance criteria
- Repeated 429s do not spin and waste tokens, requests become smaller and slower automatically.
- Pack leader avoids parallel calls to Cerebras unless configured.

---

## Part G, Token Accounting and Session Telemetry (local, privacy preserving)
1) Per request token ledger
   - Track estimated input and output tokens per request, per provider, per agent.
   - Write to a local file in a non tracked directory, for example `.codepuppy/usage.jsonl`.
2) Burn rate alerts
   - Emit a warning when:
     - average input per request exceeds a configured threshold
     - a single request exceeds 2x the expected input size
   - Suggest corrective action:
     - compact now
     - request smaller slices
     - switch tasks to Copilot local assistance
3) Daily budget mode
   - Allow user to set a daily token allowance for Cerebras, for example 2M.
   - If current spend exceeds allowance, switch the pack leader to “review only mode”.

Acceptance criteria
- You can answer: “what changed my burn rate in the last hour” from local logs.
- Users can set guardrails that stop runaway usage.

---

## Part H, Safe Patch Application Rules (prevent self inflicted corruption)
This exists to prevent “tooling damage”, such as broken heredocs or unsafe find and replace.
1) Ban unsafe editing patterns in agent instructions
   - Disallow heredoc terminator with inline shell chaining.
   - Disallow sed replacements containing special replacement symbols without escaping.
2) Provide a safe edit helper
   - If file edits are needed, prefer:
     - VS Code file edits, or
     - apply a patch file, or
     - use a language aware formatter.
3) Add “restore first” workflow
   - If agent detects a syntax explosion across many files after a single edit:
     - propose `git restore <file>`
     - re apply change in a safer way

Acceptance criteria
- Agents do not corrupt source files using fragile shell patterns.
- Recovery path is consistent and quick.

---

## Part I, Router Hooks (incremental, not full multi provider router)
1) Model pool config schema
   - Add a single config section that defines:
     - primary and fallback providers
     - per provider concurrency
     - per provider token budgets
     - per provider context and max completion defaults
2) Task class routing
   - Provide a routing hint interface:
     - “mechanical edits”
     - “design and architecture”
     - “debug and root cause”
     - “docs and copy”
   - Do not implement automatic routing logic yet, only hook points plus docs.

Acceptance criteria
- A future router can be added without refactoring provider clients.
- Users can configure pool behavior without editing code.

---

## Documentation deliverables for 1.1
1) Add a runbook: Token Budgeting and Backoff
   - how to keep input tokens per request low
   - how to recognize when the pack leader is bloating context
2) Add a troubleshooting page: Cerebras 429 and 503 playbook
   - what it means
   - how the agent adapts
   - when to pause, reduce concurrency, or compact

---

## Testing for 1.1
1) Unit tests
   - token estimator and budget enforcement
   - shell output governor truncation behavior
   - retry policy respects Retry-After with cap
2) Minimal integration validation
   - run one full “plan code test fix” loop on a toy task and confirm:
     - input budget never exceeded
     - output capped
     - compaction triggers at expected threshold

---

## Definition of done
- The pack leader cannot exceed input budgets without narrowing context.
- Shell output can’t flood model context.
- Cerebras retries become smaller and slower automatically and do not loop wastefully.
- Usage telemetry can explain token burn drivers locally without exposing secrets.
- Router ready hooks exist, but no full router is required in this version.
> **📜 HISTORICAL DOCUMENT** - This is the original audit specification. Implementation is complete.
> For current status, see [PRODUCTION-READINESS-REPORT.md](PRODUCTION-READINESS-REPORT.md).
> For audit index, see [docs/AUDIT-INDEX.md](docs/AUDIT-INDEX.md).

You are my Copilot coding agent running in VS Code Agent mode. Your mission is to audit and improve the Code Puppy repository so it can run an agent pack efficiently on Cerebras Code Pro without blowing up token usage, while also supporting optional routing to ChatGPT Teams, Google AI Pro (Gemini), and Claude Max.

Non negotiable safety rules about credentials
1) Do not print any secrets, keys, tokens, refresh tokens, cookies, or OAuth material.
2) Do not add any secrets to git history. Do not commit or push .env, local config, or credential files.
3) Assume existing secrets are already stored locally in safe places. Your job is to preserve integration behavior while ensuring secrets remain out of the repo. If you see hardcoded keys in tracked files, stop and propose a secure migration plan instead of committing them.

Part A, make sure the repo is current, without touching credentials
1) Verify this repo remote status: identify origin, default branch, tags.
2) If this is a fork, add an upstream remote, fetch all, and compare current branch to upstream default.
3) Create a working branch named feature/token-efficient-pack-leader.
4) Do not modify any auth flows for ChatGPT, Antigravity, Claude Code, or Cerebras except to make them safer and more consistent with secret handling.

Part B, repo wide discovery for token and rate limit management
Goal: locate everything that already exists about token management and session control, and summarize it in a short report.

Search for and document, with file paths and short excerpts only, these topics:
1) Context management: truncate commands, session length controls, autosave, transcript rehydration.
2) Provider throttling and backoff: 429 handling, Retry-After, request per minute and tokens per minute logic.
3) Pack agents: orchestration, delegation, model pinning, agent registry, round robin model rotation.
4) Cerebras specific guidance: docs, settings, examples.

Produce a structured inventory with:
• What exists now
• Where it lives
• What gaps remain specific to excessive input token growth

Part C, implement the minimal high impact optimization
Implement a new built in agent profile and supporting enforcement utilities:

New agent name: pack-leader-cerebras-efficient
Core behavior requirements:
1) Default workflow is diff driven.
   • Prefer git diff, small file snippets, and minimal error excerpts.
   • Refuse to proceed if asked to read full files or large logs, ask for smaller ranges.
2) Command output limiter.
   • Any shell command executed by the agent must cap output, for example tail 200 lines.
3) Micro patch rule.
   • Changes per iteration: at most 2 files.
   • Agent output: unified diff only, max 120 lines.
4) Mandatory truncation cadence.
   • After every 2 iterations, instruct the user to run /truncate 6.
5) Token budget guard.
   • Add a small heuristic that estimates prompt size, and if it exceeds a configurable budget, the agent must narrow context requests instead of continuing.

Integrations and routing, highest value setup
Document a recommended division of labor across plans:
• Cerebras Code Pro as the primary coder, plan limits are 50 RPM, 1,000,000 TPM, 24M tokens per day, so the objective is to minimize input tokens per request. Add this to docs. 
• Claude Max as architecture and deep debugging support, not as the main code generator, and note that Max increases usage allowance but does not increase per chat context beyond 200K. 
• ChatGPT Teams and Google AI Pro used selectively for planning, copywriting, UX, research, or multimodal tasks, not for high volume loop coding.
You do not need to implement provider routing today, but you must identify what configuration hooks already exist and what a future router would look like.

Documentation deliverables
1) Update docs with a new section: Token Efficient Mode for Cerebras Code Pro.
2) Include a runbook: how to avoid burning daily tokens with agent packs.
3) Include example session commands and a sample prompt.

Testing and acceptance
1) Run the smallest available test suite or lint checks to ensure changes do not break startup.
2) If the repo has no tests, add a small unit test for the command output limiter or token budget guard.

Output requirements
At the end, provide:
• a concise summary of changes
• exact instructions to enable and use pack-leader-cerebras-efficient
• a short list of next steps if we want an even more powerful multi provider router later

Proceed now. Start with Part A then Part B before coding anything.
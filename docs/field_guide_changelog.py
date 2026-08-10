"""Changelog extraction and impact classification for the Code Puppy Field Guide.

This module is used by docs/generate-field-guide.py to turn git history into a
rich, human-friendly changelog with impact levels and hero-commit summaries.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


CHANGELOG_SINCE = "2026-05-01"


def _classify_theme(subject: str) -> str:
    """Classify a commit subject into a theme bucket."""
    subject_lower = subject.lower()
    theme_keywords = {
        "models": ["model", "cerebras", "anthropic", "openai", "gemini", "ollama", "grok", "azure", "round_robin", "provider", "endpoint", "extra_models"],
        "tools": ["tool", "file_mod", "codemap", "cd", "list_files", "grep", "edit", "shell", "browser"],
        "agents": ["agent", "helios", "agent-creator", "subagent", "pack", "planning", "qa"],
        "ux": ["ui", "ux", "meta", "command", "console", "help", "motd", "prompt", "theme", "color", "banner", "tui"],
        "durability": ["dbos", "durable", "checkpoint", "resume"],
        "mcp": ["mcp"],
        "plugins": ["plugin", "hook", "callback", "register_callbacks"],
        "ci": ["ci", "workflow", "ruff", "pytest", "coverage", "test"],
        "docs": ["readme", "docs", "documentation"],
    }
    for theme, keywords in theme_keywords.items():
        if any(kw in subject_lower for kw in keywords):
            return theme
    return "misc"


def _commit_kind(subject: str) -> str:
    """Label a commit as feat, fix, refactor, docs, ci, chore, merge, etc."""
    s = subject.lower()
    if s.startswith("feat") or s.startswith("feature"):
        return "feature"
    if s.startswith("fix"):
        return "fix"
    if s.startswith("refactor"):
        return "refactor"
    if s.startswith("docs") or s.startswith("doc:"):
        return "docs"
    if s.startswith("ci:") or s.startswith("ci(") or s.startswith("test:"):
        return "ci"
    if "merge remote-tracking" in s or "merge pull request" in s or "merge branch" in s:
        return "merge"
    if "bump version" in s:
        return "release"
    if s.startswith("chore"):
        return "chore"
    return "other"


# ---------------------------------------------------------------------------
# Curated impact catalog
# Each tuple: (pattern, impact, what, why_rad, how_helps)
# Patterns are lowercase substring searches against the commit subject.
# ---------------------------------------------------------------------------
_COMMIT_SUMMARIES: list[tuple[str, str, str, str, str]] = [
    (
        "i18n",
        "major",
        "Internationalization (i18n) foundation with locale extraction and plural-support scaffolding.",
        "Code Puppy can now speak multiple languages and switch locales without code changes.",
        "Global teams and non-English users get menus, prompts, and agent replies in their preferred language.",
    ),
    (
        "agent-mcp",
        "major",
        "Agent-to-MCP server bindings with strict opt-in control.",
        "Agents can now pull live tools from specific MCP servers instead of seeing every tool everywhere.",
        "You can give one agent a custom toolset (e.g., a web-research agent gets only browser MCP tools) without bloating other agents.",
    ),
    (
        "mcp binding",
        "major",
        "Interactive MCP binding menus and post-install bind flow.",
        "No more hand-editing JSON to connect an agent to an MCP server; the UI walks you through it.",
        "Install an MCP server and immediately bind it to the right agents with a few keystrokes.",
    ),
    (
        "trust-gated",
        "major",
        "Trust-gated, project-level MCP server configurations.",
        "MCP servers can now be scoped per project and require explicit trust before they run.",
        "Safer collaboration: a repo can declare which MCP servers are allowed, and Code Puppy asks before activating anything else.",
    ),
    (
        "configurable tool prefix",
        "notable",
        "Configurable tool prefixes for MCP server tools.",
        "Prevents namespace collisions when multiple MCP servers expose tools with similar names.",
        "You can keep tool names clear and predictable, e.g., `browser_search` vs `api_search`.",
    ),
    (
        "pre_mcp_autostart",
        "notable",
        "Pre-MCP-autostart hook for credential refresh before MCP servers start.",
        "MCP servers that need fresh tokens can be started automatically without manual copy-paste.",
        "Your agents stay connected to token-gated services like Azure or GitHub MCP without hourly re-auth.",
    ),
    (
        "oauth callback",
        "major",
        "OAuth callback paste-back support.",
        "You can complete OAuth flows inside your terminal and paste the resulting callback directly into Code Puppy.",
        "No browser juggling or manual token extraction; connect to OAuth-gated APIs in one smooth flow.",
    ),
    (
        "retry profiles",
        "major",
        "Selectable, guard-railed retry profiles with per-role and per-model tuning.",
        "Different agents and models now retry with policies matched to their reliability and cost profile.",
        "Expensive models can retry cautiously while fast local models can retry aggressively, saving money and time.",
    ),
    (
        "retry in-band sse",
        "notable",
        "Smarter retry logic for in-band SSE 5xx gateway errors and sub-agent runs.",
        "Transient streaming failures no longer kill long agent runs.",
        "Multi-step research and coding tasks recover automatically from brief provider hiccups.",
    ),
    (
        "custom openai responses",
        "major",
        "Custom OpenAI Responses model type support.",
        "Code Puppy now speaks the newer OpenAI Responses API, unlocking reasoning and structured-output models.",
        "You can use cutting-edge OpenAI models with the full feature set instead of being limited to legacy chat completions.",
    ),
    (
        "wafer",
        "notable",
        "New model provider support for wafer.ai models.",
        "Adds MiniMax-M2.7 and extended DeepSeek-v4-Pro context to the model catalog.",
        "You have more high-capacity, low-cost models to choose from for long-context tasks.",
    ),
    (
        "crof",
        "notable",
        "crof.ai / Kimi K2.5 compatibility with non-streaming fallback.",
        "Adds another frontier-model option with a safe fallback when streaming isn't available.",
        "You can route to Kimi K2.5 Lightning even on providers that don't fully support streaming yet.",
    ),
    (
        "kimi k2.5",
        "notable",
        "Kimi K2.5 Lightning model support.",
        "Brings Moonshot's fast long-context model into Code Puppy's model roster.",
        "Great for long-document Q&A and summarization where speed matters.",
    ),
    (
        "destructive command guard",
        "major",
        "Destructive command guard that blocks dangerous shell commands by default.",
        "Adds a safety net so agents can't silently run `rm -rf /`, database drops, or similar foot-guns.",
        "You can delegate more autonomous shell work without worrying about catastrophic accidents.",
    ),
    (
        "yolo",
        "notable",
        "Runtime YOLO CLI override for bypassing confirmations.",
        "Power users can toggle off confirmation prompts for the current session.",
        "Speeds up trusted, repetitive workflows while keeping guards on by default.",
    ),
    (
        "obsidian agent",
        "major",
        "New Obsidian agent plugin for vault automation.",
        "Code Puppy can now read, search, and update your Obsidian notes through the official CLI.",
        "Turn your knowledge base into a live agent workspace: query notes, create pages, and maintain your vault from chat.",
    ),
    (
        "token ratio learner",
        "notable",
        "Model-specific token-ratio learner for smarter cost/length estimation.",
        "Code Puppy learns how many tokens each model consumes per character, improving budgeting.",
        "Cost estimates and context-window warnings become accurate instead of one-size-fits-all guesses.",
    ),
    (
        "prompt_newline",
        "notable",
        "prompt_newline plugin with a toggleable /prompt_newline command.",
        "Lets you control whether prompts insert newlines before or after the cursor.",
        "Fine-tune prompt formatting to match your shell or editor muscle memory.",
    ),
    (
        "extract dbos",
        "major",
        "DBOS durable execution extracted into an optional plugin.",
        "The heavy durability machinery is now opt-in, keeping core Code Puppy lean.",
        "Install the plugin only when you need checkpoint/resume for long-running agent workflows.",
    ),
    (
        "--resume",
        "notable",
        "--resume flag to restore a session from a saved .pkl file.",
        "Pick up a long agent run exactly where it left off.",
        "Great for resuming after a crash, reboot, or context switch without losing progress.",
    ),
    (
        "decstbm-free inline prompt",
        "major",
        "DECSTBM-free inline prompt surface for JetBrains terminals.",
        "Code Puppy's prompt now renders cleanly inside JetBrains IDEs and terminals that don't support scroll margins.",
        "You can use Code Puppy inside the built-in terminal of PyCharm, WebStorm, Rider, etc. without visual glitches.",
    ),
    (
        "theme aware",
        "major",
        "Full prompt-toolkit and terminal rendering theme awareness.",
        "Every TUI, diff view, status line, and prompt now respects the active theme consistently.",
        "Your terminal feels like one polished app instead of a patchwork of default-colored dialogs.",
    ),
    (
        "centralize prompt-toolkit semantic theme roles",
        "notable",
        "Centralized semantic theme roles for all prompt-toolkit TUIs.",
        "Defines one set of named colors (primary, muted, danger, etc.) that every UI uses.",
        "Themes can recolor the entire app by changing a handful of tokens.",
    ),
    (
        "normalize oversized image",
        "notable",
        "Normalizes oversized image file attachments to match clipboard resize policy.",
        "Pasting or attaching a huge screenshot no longer blows through model context limits.",
        "Large images are downsampled consistently, saving tokens and keeping responses fast.",
    ),
    (
        "cell-clip inline bar",
        "notable",
        "Cell-clipped inline bar rows to prevent terminal wrap desync.",
        "Keeps progress bars and inline status lines aligned with the terminal grid.",
        "No more broken spinner layouts when the terminal is narrow or uses multi-cell characters.",
    ),
    (
        "cross-platform windows support",
        "notable",
        "Cross-platform Windows statusline support plus Unicode crash prevention.",
        "The status bar and input handling now behave on Windows instead of crashing on exotic characters.",
        "Windows users get the same polished terminal experience as macOS/Linux users.",
    ),
    (
        "disable vt input",
        "notable",
        "Disables VT input under Wave Terminal to avoid input-mode conflicts.",
        "Fixes garbled or unresponsive input in the Wave Terminal emulator.",
        "You can run Code Puppy inside Wave without fighting the terminal for keyboard events.",
    ),
    (
        "complete detached agent lifecycle",
        "notable",
        "Completes the detached agent lifecycle so forked agents clean up correctly.",
        "Sub-agents and background agents no longer leave dangling processes or state.",
        "Long workflows with forked agents finish cleanly without resource leaks.",
    ),
    (
        "post_tool_call",
        "notable",
        "Guards post-tool-call hooks against sub-agent calls.",
        "Prevents run-stats hooks from firing incorrectly inside nested sub-agent runs.",
        "Metrics and token accounting stay accurate when agents call other agents.",
    ),
    (
        "extend token usage",
        "notable",
        "Extended token-usage data reported through the agent_run_end hook.",
        "More granular cost and usage telemetry at the end of each agent run.",
        "Plugins and analytics can track spend per agent, model, and tool call.",
    ),
    (
        "agent exception retry hook",
        "notable",
        "Wires the agent_exception retry hook into the runtime.",
        "Agents can now be retried automatically when they throw recoverable exceptions.",
        "Flaky models or transient failures don't break a long chain of agent calls.",
    ),
    (
        "gpt-5.6 reasoning",
        "major",
        "GPT-5.6 reasoning context and mode support.",
        "Unlocks OpenAI's latest reasoning model family for agent runs with structured thinking traces.",
        "You can run complex multi-step reasoning tasks with explicit chain-of-thought visibility.",
    ),
    (
        "gpt-5.6 family models",
        "major",
        "GPT-5.6 family models gated behind per-tool guardrails.",
        "Adds the newest OpenAI frontier models with fine-grained safety controls per tool.",
        "You can opt specific tools into the latest models while keeping others on stable defaults.",
    ),
    (
        "codex oauth image generation",
        "major",
        "Codex OAuth image generation integration.",
        "Agents can now generate images through the ChatGPT OAuth plugin's image pipeline.",
        "You can create visuals directly from chat without switching contexts or apps.",
    ),
    (
        "summarization compaction",
        "notable",
        "Default context compaction switched to summarization mode.",
        "Long conversations are now summarized instead of bluntly truncated, preserving more meaning.",
        "Extended agent sessions retain context better, leading to more coherent long threads.",
    ),
    (
        "i18n): extract config_commands",
        "notable",
        "Internationalized config command user-facing strings.",
        "Settings and config commands now flow through the translatable string pipeline.",
        "Non-English users see localized /set, /get, and configuration prompts.",
    ),
    (
        "i18n): extract cli_runner",
        "notable",
        "Internationalized CLI runner user-facing strings.",
        "The command runner's prompts and errors are now translatable.",
        "Users in other locales get localized feedback from the CLI layer.",
    ),
    (
        "i18n): static extraction audit",
        "notable",
        "Static audit tool for translatable CLI strings.",
        "Catches hardcoded English strings before they ship.",
        "Maintainers can enforce i18n coverage and prevent regression.",
    ),
    (
        "stop routing latin american spanish",
        "notable",
        "Removed deprecated es-419 locale routing.",
        "Simplifies the Spanish locale fallback chain and removes a dead code path.",
        "Spanish-speaking users get cleaner, more predictable localization behavior.",
    ),
    (
        "polish base spanish catalog",
        "notable",
        "Polished the base Spanish translation catalog.",
        "Improves translation quality and coverage for Spanish users.",
        "The TUI and CLI feel more natural for Spanish speakers.",
    ),
    (
        "jediterm inline streaming",
        "notable",
        "JediTerm inline streaming output coordination fix.",
        "Keeps streamed agent output aligned with the terminal cursor in JetBrains terminals.",
        "Code Puppy behaves correctly inside PyCharm/WebStorm/Rider built-in terminals.",
    ),
    (
        "request 1h prompt-cache ttl",
        "notable",
        "1-hour prompt-cache TTL requested for claude-code-* OAuth models.",
        "Reduces repeated prompt processing costs for Claude OAuth sessions.",
        "Longer-lived OAuth sessions stay cheaper and faster.",
    ),
    (
        "cd autocomplete for bare tilde",
        "notable",
        "/cd autocomplete now handles bare tilde home paths.",
        "Shell-style home directory shortcuts work in the directory-change autocomplete.",
        "You can type /cd ~ and get completions for your home folder.",
    ),
    (
        "resolve git worktrees to main repo wing",
        "notable",
        "Kennel now resolves git worktrees to the main repo wing.",
        "Working in a git worktree no longer fragments your project memory.",
        "Worktree sessions share the same kennel notes as the main checkout.",
    ),
    (
        "headless session autosaves",
        "notable",
        "Hardened headless session autosave behavior.",
        "Sessions save reliably when running Code Puppy outside the interactive TUI.",
        "Background and scripted agent runs don't lose state.",
    ),
    (
        "persist and dispatch headless prompts",
        "notable",
        "Headless prompts are now persisted and dispatched correctly.",
        "Non-interactive mode can accept and act on prompts from files or stdin.",
        "You can script Code Puppy with prompt files and get deterministic dispatch.",
    ),
    (
        "serialize plugin-skills cache rebuild",
        "notable",
        "Serialized plugin-skills cache rebuild to prevent concurrent-discovery crashes.",
        "Stops race conditions when multiple agents discover skills at the same time.",
        "Parallel agent starts are safer and no longer corrupt the skills cache.",
    ),
    (
        "reuse plugin-skills cache",
        "notable",
        "Reuses the plugin-skills cache when registrations are unchanged.",
        "Avoids redundant skill discovery on every startup.",
        "Code Puppy launches faster, especially with many custom skills installed.",
    ),
    (
        "clamp sub-agent panel",
        "notable",
        "Sub-agent panel is clamped to terminal height with overflow handling.",
        "Prevents the sub-agent status UI from spilling past the terminal edge.",
        "Tall sub-agent trees remain readable on small terminals.",
    ),
    (
        "terminal outputs raw text on code blocks",
        "notable",
        "Terminal now outputs raw text on code blocks instead of double-rendering.",
        "Fixes duplicated or escaped code output in the terminal.",
        "Code snippets from agents render cleanly without visual artifacts.",
    ),
    (
        "flux",
        "major",
        "Flux image generation model support added.",
        "Brings Black Forest Labs' Flux image generation into Code Puppy.",
        "You can generate high-quality images from text prompts through Code Puppy.",
    ),
]


def _impact_level(subject: str, kind: str, files: list[str], body: str) -> str:
    """Classify a commit's impact as major, notable, or routine."""
    s = subject.lower()

    # Version bumps, merges, chores, and most CI work are routine.
    if kind in ("release", "merge") or "bump version" in s:
        return "routine"
    if kind == "chore":
        return "routine"
    if kind == "ci":
        return "routine"

    # Match curated major/notable patterns.
    for pattern, impact, *_ in _COMMIT_SUMMARIES:
        if pattern in s:
            return impact

    # Large-scale changes that touch many files are usually significant.
    if kind == "refactor" and len(files) >= 6:
        return "major"
    if len(files) >= 10:
        return "major"
    if kind == "refactor" and len(files) >= 3:
        return "notable"

    # Features and fixes are at least notable unless clearly tiny.
    if kind == "feature":
        return "major" if len(files) >= 5 else "notable"
    if kind == "fix":
        return "notable"
    if kind == "docs" and len(files) >= 3:
        return "notable"

    return "routine"


def _extract_body_summary(body: str, subject: str, kind: str) -> dict:
    """Pull what/why/how from a commit body when no curated summary exists."""
    text = (body or "").strip()
    if not text:
        return {}

    # Split into sentences and clean up markdown/bullet noise.
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    sentences = [re.sub(r"^[\-*•]\s+", "", s) for s in sentences]

    what = ""
    why_rad = ""
    how_helps = ""

    # First substantive sentence is usually the description of the change.
    for sentence in sentences:
        if len(sentence) > 15:
            what = sentence
            break

    # Look for motivation / problem statement.
    for sentence in sentences:
        s_low = sentence.lower()
        if any(kw in s_low for kw in ("because", "so that", "without this", "previously", "used to", "was broken", "would fail", "could not", "did not")):
            why_rad = sentence
            break
    if not why_rad and len(sentences) > 1:
        # Use the second sentence as context if it doesn't look like metadata.
        why_rad = sentences[1]

    # Look for user-facing benefit / enablement.
    for sentence in sentences:
        s_low = sentence.lower()
        if any(kw in s_low for kw in ("allows", "enables", "lets you", "you can", "users can", "means", "now supports", "improves", "speeds up", "reduces")):
            how_helps = sentence
            break
    if not how_helps and len(sentences) > 2:
        how_helps = sentences[-1] if sentences[-1] != what else ""

    # Trim and dedupe.
    if why_rad == what:
        why_rad = ""
    if how_helps == what or how_helps == why_rad:
        how_helps = ""

    # Fallbacks when the body didn't give us enough signal.
    if not what:
        what = subject
    if not why_rad:
        why_rad = _generic_why(kind)
    if not how_helps:
        how_helps = _generic_how(kind)

    return {"what": what, "why_rad": why_rad, "how_helps": how_helps}


def _generic_why(kind: str) -> str:
    return {
        "feature": "Expands what Code Puppy can do.",
        "fix": "Removes a rough edge.",
        "refactor": "Keeps the internals clean and maintainable.",
        "docs": "Keeps the docs in sync with the code.",
        "ci": "Keeps the build and test pipeline healthy.",
        "chore": "Keeps the project machinery running smoothly.",
    }.get(kind, "Keeps the project moving forward.")


def _generic_how(kind: str) -> str:
    return {
        "feature": "You can rely on this new behavior in your daily workflow.",
        "fix": "Your experience is smoother and more predictable.",
        "refactor": "Future changes in this area are faster and safer.",
        "docs": "You can find accurate guidance without reading source.",
        "ci": "Releases stay green and regressions get caught early.",
        "chore": "The project stays up to date and easy to work on.",
    }.get(kind, "Part of the continuous improvement pipeline.")


def _summarize_commit(subject: str, kind: str, theme: str, body: str = "") -> dict:
    """Return what/why/how blurbs for high-impact commits."""
    s = subject.lower()

    for pattern, impact, what, why_rad, how_helps in _COMMIT_SUMMARIES:
        if pattern in s:
            return {"impact": impact, "what": what, "why_rad": why_rad, "how_helps": how_helps}

    # Try to extract richer detail from the commit body.
    body_summary = _extract_body_summary(body, subject, kind)
    if body_summary:
        return {"impact": _impact_from_kind(kind), **body_summary}

    # Generic but useful fallbacks by kind/theme.
    if kind == "feature":
        trimmed = subject[5:] if subject.lower().startswith("feat:") or subject.lower().startswith("feat(") else subject
        return {
            "impact": "notable",
            "what": f"Adds {trimmed}",
            "why_rad": _generic_why("feature"),
            "how_helps": _generic_how("feature"),
        }
    if kind == "fix":
        trimmed = subject[4:] if subject.lower().startswith("fix:") or subject.lower().startswith("fix(") else subject
        return {
            "impact": "notable",
            "what": f"Fixes {trimmed}",
            "why_rad": _generic_why("fix"),
            "how_helps": _generic_how("fix"),
        }
    if kind == "refactor":
        return {
            "impact": "routine",
            "what": f"Refactors {subject}",
            "why_rad": _generic_why("refactor"),
            "how_helps": _generic_how("refactor"),
        }
    if kind == "docs":
        return {
            "impact": "routine",
            "what": f"Documents {subject}",
            "why_rad": _generic_why("docs"),
            "how_helps": _generic_how("docs"),
        }

    return {
        "impact": "routine",
        "what": subject,
        "why_rad": _generic_why(kind),
        "how_helps": _generic_how(kind),
    }


def _impact_from_kind(kind: str) -> str:
    return "notable" if kind in ("feature", "fix") else "routine"


def _release_impact_summary(impact_counts: dict[str, int], heroes: list[dict]) -> str:
    """Generate a one-line release-level impact summary."""
    major = impact_counts.get("major", 0)
    notable = impact_counts.get("notable", 0)
    routine = impact_counts.get("routine", 0)

    if major >= 3:
        return f"A heavy release with {major} major changes -- new capabilities worth reading."
    if major >= 1:
        return f"Contains {major} major highlight{'s' if major > 1 else ''} plus {notable} notable improvement{'s' if notable != 1 else ''}."
    if notable >= 5:
        return f"A polish-and-fix release with {notable} notable improvements."
    if notable >= 1:
        return f"{notable} notable improvement{'s' if notable > 1 else ''}, mostly routine maintenance otherwise."
    return f"Mostly routine maintenance ({routine} commit{'s' if routine != 1 else ''})."


# ---------------------------------------------------------------------------
# Category grouping for the changelog layout.
# Commits are grouped into human-friendly buckets inside each release.
# ---------------------------------------------------------------------------

_CATEGORY_ORDER = [
    ("major", "Major Highlights", "star"),
    ("feature", "New Features", "sparkles"),
    ("fix", "Bug Fixes", "bug"),
    ("refactor", "Optimizations & Refactors", "zap"),
    ("docs", "Documentation", "book"),
    ("ci", "CI & Tests", "check-circle"),
    ("chore", "Maintenance", "tool"),
    ("other", "Other", "circle"),
]

_CATEGORY_META: dict[str, dict] = {
    "major": {
        "title": "Major Highlights",
        "description": "High-impact changes that unlock new capabilities or significantly alter how Code Puppy works.",
    },
    "feature": {
        "title": "New Features",
        "description": "New capabilities, commands, model support, integrations, and user-facing improvements.",
    },
    "fix": {
        "title": "Bug Fixes",
        "description": "Corrections for crashes, wrong behavior, UI glitches, race conditions, and edge cases.",
    },
    "refactor": {
        "title": "Optimizations & Refactors",
        "description": "Internal cleanups, performance wins, architecture moves, and code-quality improvements.",
    },
    "docs": {
        "title": "Documentation",
        "description": "README, skill guides, docstrings, and explanatory content updates.",
    },
    "ci": {
        "title": "CI & Tests",
        "description": "Continuous integration, test suites, linting, and release automation changes.",
    },
    "chore": {
        "title": "Maintenance",
        "description": "Version bumps, dependency updates, formatting, and housekeeping.",
    },
    "other": {
        "title": "Other",
        "description": "Miscellaneous commits that don't fit the other buckets.",
    },
}


def _category_for_kind(kind: str, impact: str) -> str:
    """Map a commit kind and impact to a display category."""
    if impact == "major" and kind != "feature":
        return "major"
    return kind if kind in _CATEGORY_META else "other"


def _group_release_commits_by_category(commits: list[dict]) -> list[dict]:
    """Return commits grouped into ordered category buckets."""
    groups: dict[str, list[dict]] = {key: [] for key, _, _ in _CATEGORY_ORDER}
    for c in commits:
        cat = _category_for_kind(c["kind"], c["impact"])
        groups.setdefault(cat, []).append(c)

    result: list[dict] = []
    for key, _, _ in _CATEGORY_ORDER:
        bucket = groups.get(key, [])
        if not bucket:
            continue
        # Sort by date descending, then impact.
        bucket.sort(key=lambda c: c["date"], reverse=True)
        bucket.sort(key=lambda c: 0 if c["impact"] == "major" else (1 if c["impact"] == "notable" else 2))
        meta = _CATEGORY_META[key]
        result.append(
            {
                "key": key,
                "title": meta["title"],
                "description": meta["description"],
                "count": len(bucket),
                "commits": bucket,
            }
        )
    return result


def _get_recent_commits(
    run: Callable[..., str],
    repo_root: Path,
    since: str = CHANGELOG_SINCE,
) -> dict:
    """Return a detailed changelog grouped into version releases."""

    def _version_at_commit(sha: str) -> str:
        """Read pyproject.toml version at a specific commit."""
        try:
            raw = run(["git", "show", f"{sha}:pyproject.toml"], check=False)
            for line in raw.splitlines():
                m = re.match(r'^version\s*=\s*"([^"]+)"', line.strip())
                if m:
                    return m.group(1)
        except Exception:
            pass
        return ""

    def _github_url_for_commit(sha: str) -> str:
        base = "https://github.com/mpfaffenberger/code_puppy"
        return f"{base}/commit/{sha}"

    # Get commits with full body and changed files (name-only).
    stdout = run(
        [
            "git",
            "log",
            "--pretty=format:%H|%h|%ad|%an|%s|%b<COMMIT_END>",
            "--date=short",
            "--name-only",
            f"--since={since}",
        ],
        check=False,
    )

    raw_blocks = [b.strip() for b in stdout.split("<COMMIT_END>") if b.strip()]
    commits: list[dict] = []

    def _find_metadata_line(lines: list[str]) -> tuple[list[str], list[str]]:
        """Return (files_lines, metadata_line). The metadata line has 5+ pipes."""
        for idx in range(len(lines) - 1, -1, -1):
            ln = lines[idx]
            if ln.count("|") >= 5:
                return lines[:idx], ln
        return lines, ""

    for block in raw_blocks:
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue
        file_lines, meta_line = _find_metadata_line(lines)
        if not meta_line:
            continue
        parts = meta_line.split("|", 5)
        if len(parts) < 5:
            continue
        full_sha, short_sha, date, author, subject = parts[:5]
        body = parts[5] if len(parts) > 5 else ""
        files = [ln for ln in file_lines if ln and not ln.startswith("|")]

        subject_lower = subject.lower()
        is_bump = "bump version" in subject_lower
        version = _version_at_commit(full_sha) if is_bump else ""
        kind = _commit_kind(subject)
        theme = _classify_theme(subject)
        impact = _impact_level(subject, kind, files, body)
        summary = _summarize_commit(subject, kind, theme, body)
        # Honor the curated impact if it differs from the heuristic.
        if summary.get("impact"):
            impact = summary["impact"]

        commits.append(
            {
                "sha": short_sha,
                "full_sha": full_sha,
                "date": date,
                "author": author,
                "subject": subject,
                "body": body.strip()[:1200],
                "theme": theme,
                "kind": kind,
                "impact": impact,
                "summary": summary,
                "files": files[:25],
                "file_count": len(files),
                "is_version_bump": is_bump,
                "bumped_version": version,
                "github_url": _github_url_for_commit(full_sha),
            }
        )

    # Build release groups from bump commits outward.
    bump_indices = [i for i, c in enumerate(commits) if c["is_version_bump"]]
    releases: list[dict] = []

    def release_block(start_idx: int, end_idx: int, version_label: str, release_type: str) -> dict:
        block_commits = commits[start_idx:end_idx + 1]
        themes: dict[str, int] = {}
        kinds: dict[str, int] = {}
        impact_counts: dict[str, int] = {}
        highlights: list[dict] = []
        heroes: list[dict] = []
        for c in block_commits:
            themes[c["theme"]] = themes.get(c["theme"], 0) + 1
            kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
            impact_counts[c["impact"]] = impact_counts.get(c["impact"], 0) + 1
            if c["kind"] in ("feature", "fix", "refactor"):
                highlights.append(c)
            if c["impact"] in ("major", "notable"):
                heroes.append(c)

        # Sort heroes by impact (major first) then date (newest first). Stable sort lets us
        # do this in two passes without fighting tuple-reversal quirks.
        heroes.sort(key=lambda c: c["date"], reverse=True)
        heroes.sort(key=lambda c: 0 if c["impact"] == "major" else 1)
        impact_level = "major" if impact_counts.get("major", 0) else ("notable" if impact_counts.get("notable", 0) else "routine")

        category_groups = _group_release_commits_by_category(block_commits)

        return {
            "version": version_label,
            "type": release_type,
            "date": block_commits[0]["date"] if block_commits else "",
            "end_date": block_commits[-1]["date"] if block_commits else "",
            "commit_count": len(block_commits),
            "commits": block_commits,
            "themes": themes,
            "kinds": kinds,
            "impact_counts": impact_counts,
            "impact_level": impact_level,
            "impact_summary": _release_impact_summary(impact_counts, heroes),
            "highlights": highlights[:10],
            "heroes": heroes[:8],
            "category_groups": category_groups,
        }

    if not bump_indices:
        releases.append(release_block(0, len(commits) - 1, "unreleased", "unreleased"))
    else:
        # Leading edge before first bump = unreleased/current work
        if bump_indices[0] > 0:
            current_version = _version_at_commit("HEAD")
            releases.append(release_block(0, bump_indices[0] - 1, current_version or "unreleased", "unreleased"))

        # Each bump marks a release spanning from this bump down to (but not past) the next older bump.
        # bump_indices is newest-first; the next entry in the list is the next older bump.
        for idx, bump_i in enumerate(bump_indices):
            version = commits[bump_i].get("bumped_version") or ""
            next_older_bump = bump_indices[idx + 1] if idx + 1 < len(bump_indices) else len(commits)
            start = bump_i
            end = next_older_bump - 1
            if start > end:
                continue
            releases.append(release_block(start, end, version, "release"))

    theme_guide = {
        "models": "New model providers, endpoints, context lengths, and model-specific behavior.",
        "tools": "New or changed tools that agents can call (file ops, shell, browser, etc.).",
        "agents": "Agent types, sub-agent behavior, lifecycle, and agent-creator improvements.",
        "ux": "Terminal UI, prompts, themes, input handling, and visual polish.",
        "durability": "Checkpoint, resume, and long-running workflow reliability.",
        "mcp": "MCP server integration, bindings, and lifecycle.",
        "plugins": "Plugin system, hooks, callbacks, and specific plugin work.",
        "ci": "Continuous integration, testing, coverage, and release automation.",
        "docs": "Documentation, skill guides, and README updates.",
        "misc": "Changes that don't fit a specific theme.",
    }

    return {
        "since": since,
        "total_commits": len(commits),
        "releases": releases,
        "all_commits": commits,
        "theme_guide": theme_guide,
    }

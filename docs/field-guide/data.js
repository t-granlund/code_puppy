window.FIELD_GUIDE_DATA = {
  "meta": {
    "generatedAt": "2026-08-19T01:02:31.124587+00:00",
    "repoPath": "/Users/tygranlund/code_puppy",
    "repoHead": "853baa9b",
    "branch": "main",
    "currentVersion": "code-puppy v0.0.740",
    "sourceUrl": "https://github.com/mpfaffenberger/code_puppy"
  },
  "stats": {
    "tools": 59,
    "agents": 22,
    "plugins": 60,
    "skills": 5,
    "commitsLast2Months": 715,
    "releases": 3
  },
  "tools": [
    {
      "name": "agent_run_shell_command",
      "category": "shell",
      "description": "Run a shell command with timeout, optional background execution, and output streaming. Your hands."
    },
    {
      "name": "agent_share_your_reasoning",
      "category": "shell",
      "description": "Record the agent's reasoning for observability in the TUI and logs."
    },
    {
      "name": "ask_user_question",
      "category": "user",
      "description": "Ask the human multiple related questions in an interactive picker. Use when input is genuinely required."
    },
    {
      "name": "browser_check",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_clear_highlights",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_click",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_click_by_role",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_click_by_text",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_close",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_double_click",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_execute_js",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_find_buttons",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_find_by_label",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_find_by_placeholder",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_find_by_role",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_find_by_test_id",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_find_by_text",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_find_links",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_get_page_info",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_get_text",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_get_value",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_go_back",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_go_forward",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_highlight_element",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_hover",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_initialize",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_list_pages",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_list_workflows",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_navigate",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_new_page",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_page_snapshot",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_read_workflow",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_reload",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_save_workflow",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_screenshot_analyze",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_scroll",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_scroll_to_element",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_select_option",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_set_text",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_set_text_by_label",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_set_viewport",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_status",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_uncheck",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_wait_for_element",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_wait_for_load",
      "category": "browser",
      "description": ""
    },
    {
      "name": "browser_xpath_query",
      "category": "browser",
      "description": ""
    },
    {
      "name": "create_file",
      "category": "file",
      "description": "Create a new file or overwrite an existing one with full content."
    },
    {
      "name": "delete_file",
      "category": "file",
      "description": "Delete a file with a logged diff of what was removed. Use sparingly."
    },
    {
      "name": "delete_snippet",
      "category": "file",
      "description": "Remove the first occurrence of an exact text snippet from a file."
    },
    {
      "name": "edit_file",
      "category": "file",
      "description": "Deprecated compound tool; auto-expands to create/replace/delete. Prefer the specific tools."
    },
    {
      "name": "grep",
      "category": "file",
      "description": "Recursively search file contents with ripgrep regex. Fast way to find usages, definitions, and config."
    },
    {
      "name": "invoke_agent",
      "category": "agent",
      "description": "Delegate a task to a named sub-agent. Use this to hand off research, QA, or specialist work instead of doing it yourself."
    },
    {
      "name": "invoke_agent_with_model",
      "category": "agent",
      "description": "Delegate to a sub-agent while pinning a specific model for that run."
    },
    {
      "name": "list_agents",
      "category": "agent",
      "description": "List every sub-agent available for delegation, with what each one is good at."
    },
    {
      "name": "list_available_models",
      "category": "agent",
      "description": "Show the models configured in the model factory and which providers they route to."
    },
    {
      "name": "list_files",
      "category": "file",
      "description": "List files and directories with smart filtering (skips build artifacts, caches, and noise). Read-only."
    },
    {
      "name": "load_image_for_analysis",
      "category": "user",
      "description": "Load an image from disk so the model can see and analyze it."
    },
    {
      "name": "read_file",
      "category": "file",
      "description": "Read a file's contents, optionally a line range. Use before modifying anything."
    },
    {
      "name": "replace_in_file",
      "category": "file",
      "description": "Apply targeted find-and-replace edits. Prefer this over full rewrites; keeps diffs small."
    }
  ],
  "agents": [
    {
      "name": "agent-creator",
      "display_name": "Agent Creator 🏗️",
      "description": "Helps you create new JSON agent configurations with proper schema validation",
      "type": "python",
      "tools": [
        "list_files",
        "read_file",
        "create_file",
        "replace_in_file",
        "delete_snippet",
        "ask_user_question",
        "list_agents",
        "invoke_agent",
        "universal_constructor"
      ]
    },
    {
      "name": "benton-lead-orchestrator",
      "display_name": "Benton Lead Orchestrator ",
      "description": "Master orchestrator for the Benton Drones in-house lead ingestion pipeline. Evolves the local Python/SQLite MVP into a branded, multi-variant lead intake system with electronic consent/signature capture, admin dashboard with maps and analytics, and a production-ready deployment path. Coordinates specialist agents and custom tools to deliver the full pipeline plus a flat HTML explainer guide.",
      "type": "json",
      "tools": [
        "list_files",
        "read_file",
        "create_file",
        "replace_in_file",
        "delete_snippet",
        "list_agents",
        "invoke_agent",
        "shell_run",
        "universal_constructor",
        "ask_user_question",
        "kennel_recall",
        "kennel_remember"
      ]
    },
    {
      "name": "code-puppy",
      "display_name": "Code-Puppy 🐶",
      "description": "The most loyal digital puppy, helping with all coding tasks",
      "type": "python",
      "tools": [
        "list_agents",
        "invoke_agent",
        "list_files",
        "read_file",
        "grep",
        "create_file",
        "replace_in_file",
        "delete_snippet",
        "delete_file",
        "agent_run_shell_command",
        "ask_user_question",
        "activate_skill",
        "list_or_search_skills",
        "load_image_for_analysis"
      ]
    },
    {
      "name": "e2e-testing-expert",
      "display_name": "E2E Testing Expert",
      "description": "Analyzes any codebase to discover current features, then generates a complete, up-to-date end-to-end test suite. Works across web apps, Python backends, JS frontends, HTTP APIs, and CLI tools. Discovers, inventories, generates, executes, and reports.",
      "type": "json",
      "tools": [
        "list_files",
        "read_file",
        "grep",
        "create_file",
        "replace_in_file",
        "agent_run_shell_command",
        "agent_share_your_reasoning",
        "ask_user_question",
        "invoke_agent",
        "list_agents",
        "browser_initialize",
        "browser_close",
        "browser_status",
        "browser_new_page",
        "browser_list_pages",
        "browser_navigate",
        "browser_get_page_info",
        "browser_go_back",
        "browser_go_forward",
        "browser_reload",
        "browser_wait_for_load",
        "browser_find_by_role",
        "browser_find_by_text",
        "browser_find_by_label",
        "browser_find_by_placeholder",
        "browser_find_by_test_id",
        "browser_find_buttons",
        "browser_find_links",
        "browser_xpath_query",
        "browser_click",
        "browser_double_click",
        "browser_hover",
        "browser_set_text",
        "browser_get_text",
        "browser_get_value",
        "browser_select_option",
        "browser_check",
        "browser_uncheck",
        "browser_execute_js",
        "browser_scroll",
        "browser_scroll_to_element",
        "browser_set_viewport",
        "browser_wait_for_element",
        "browser_highlight_element",
        "browser_clear_highlights",
        "browser_save_workflow",
        "browser_list_workflows",
        "browser_read_workflow"
      ]
    },
    {
      "name": "emoji-artist",
      "display_name": "Emoji Artist 🎨",
      "description": "Designs and ships custom branded Microsoft Teams emojis (96x96, transparent PNG) using LLM-authored SVG rasterized via headless Chromium. Knows the HTT brand book and logo registry. No API keys needed — leverages the host model's native ability to write expressive SVG.",
      "type": "json",
      "tools": [
        "list_files",
        "read_file",
        "create_file",
        "replace_in_file",
        "delete_snippet",
        "delete_file",
        "grep",
        "agent_run_shell_command",
        "list_agents",
        "agent_share_your_reasoning",
        "ask_user_question",
        "load_image_for_analysis",
        "activate_skill",
        "list_or_search_skills"
      ]
    },
    {
      "name": "epistemic-architect",
      "display_name": "Epistemic Architect 🏛️🔬",
      "description": "Structured planning through evidence-based reasoning. Uses OODA loop and delegates to specialist agents for security, code review, QA, and implementation.",
      "type": "json",
      "tools": [
        "list_files",
        "read_file",
        "grep",
        "create_file",
        "replace_in_file",
        "delete_snippet",
        "delete_file",
        "agent_run_shell_command",
        "agent_share_your_reasoning",
        "list_agents",
        "invoke_agent",
        "ask_user_question"
      ]
    },
    {
      "name": "experience-architect",
      "display_name": "Experience Architect 🎨",
      "description": "Frontend and UX architect specializing in design systems, WCAG 2.2 accessibility, privacy-by-design (GDPR/CCPA/GPC), and frontend-backend integration contracts. Always researches via web-puppy.",
      "type": "json",
      "tools": [
        "list_files",
        "read_file",
        "grep",
        "agent_share_your_reasoning",
        "invoke_agent",
        "list_agents"
      ]
    },
    {
      "name": "helios",
      "display_name": "Helios ☀️",
      "description": "The Universal Constructor - a transcendent agent that can create any tool, any capability, any functionality",
      "type": "python",
      "tools": [
        "universal_constructor",
        "list_files",
        "read_file",
        "grep",
        "create_file",
        "replace_in_file",
        "delete_snippet",
        "delete_file",
        "agent_run_shell_command"
      ]
    },
    {
      "name": "job-application-architect",
      "display_name": "Job Application Architect",
      "description": "Ethical, human-in-the-loop job-application orchestrator. Discovers roles, classifies Experience- vs Solutions-Architect flavor, truthfully tailors ATS-safe resumes + cover letters per role, stages screening answers, and tracks everything in a durable ledger. Discovers live postings via public no-auth job-board APIs (Greenhouse/Lever/Ashby/SmartRecruiters/Workday CXS) with jobboard_discover and generates ATS-safe resume files (md/txt/html/docx) with ats_resume_build. Delegates research to web-puppy, gated/portal extraction to web-retriever, compensation & option-fit advisory analysis to solutions-architect, and tool-building to helios. NEVER auto-submits, solves CAPTCHAs, evades bot/AI detection, or fills EEO self-ID — a human clears every gate.",
      "type": "json",
      "tools": [
        "list_agents",
        "invoke_agent",
        "jobapp_ledger",
        "jobboard_discover",
        "ats_resume_build",
        "ask_user_question",
        "read_file",
        "create_file",
        "replace_in_file",
        "grep"
      ]
    },
    {
      "name": "mail-researcher",
      "display_name": "Mail Researcher ",
      "description": "Parses, searches, and researches your local Mac Mail (Google + iCloud accounts). Pulls context/text/data/images from messages to support any initiative, and drafts plain-text or polished HTML emails saved as files and inserted as reviewable drafts in Mail.app — never auto-sends.",
      "type": "json",
      "tools": [
        "list_files",
        "read_file",
        "grep",
        "create_file",
        "replace_in_file",
        "agent_run_shell_command",
        "load_image_for_analysis",
        "ask_user_question",
        "universal_constructor",
        "browser_initialize",
        "browser_new_page",
        "browser_navigate",
        "browser_get_page_info",
        "browser_get_text",
        "browser_page_snapshot",
        "browser_find_by_text",
        "browser_find_links",
        "browser_scroll",
        "browser_screenshot_analyze",
        "browser_execute_js",
        "browser_close",
        "kennel_recent",
        "kennel_recall",
        "kennel_remember"
      ]
    },
    {
      "name": "model-judge",
      "display_name": "Model Judge ⚖️",
      "description": "Benchmark and compare models: run the same agent and prompt across multiple models, capture per-request token usage and latency, then produce a side-by-side comparison and a ranked verdict.",
      "type": "python",
      "tools": [
        "list_agents",
        "list_available_models",
        "invoke_agent",
        "invoke_agent_with_model",
        "ask_user_question",
        "agent_share_your_reasoning",
        "list_files",
        "read_file",
        "create_file"
      ]
    },
    {
      "name": "ops-comms-collie",
      "display_name": "Ops Comms Collie 🐕‍🦺",
      "description": "Reviews and refines drafts of business communications aimed at non-technical operations stakeholders (COOs, franchisee success leaders, ops analysts, finance). Herds technical findings into plain business English — does NOT write from scratch.",
      "type": "json",
      "tools": [
        "list_files",
        "read_file",
        "grep",
        "create_file",
        "replace_in_file",
        "delete_snippet",
        "agent_share_your_reasoning"
      ]
    },
    {
      "name": "planning-agent",
      "display_name": "Planning Agent 📋",
      "description": "Breaks down complex coding tasks into clear, actionable steps. Analyzes project structure, identifies dependencies, and creates execution roadmaps.",
      "type": "python",
      "tools": [
        "list_files",
        "read_file",
        "grep",
        "ask_user_question",
        "list_agents",
        "invoke_agent",
        "list_or_search_skills"
      ]
    },
    {
      "name": "prompt-sherpa",
      "display_name": "Prompt Sherpa 🏔️",
      "description": "Wraps your raw prompt: improves it, picks the right specialist agent, optionally validates time-sensitive facts, then executes the improved prompt against the chosen agent and returns the result. A single round-trip front door for getting better answers from the pack.",
      "type": "json",
      "tools": [
        "list_agents",
        "invoke_agent",
        "ask_user_question",
        "agent_share_your_reasoning"
      ]
    },
    {
      "name": "qa-kitten",
      "display_name": "Quality Assurance Kitten 🐱",
      "description": "Advanced web browser automation and quality assurance testing using Playwright with visual analysis capabilities",
      "type": "python",
      "tools": [
        "browser_initialize",
        "browser_close",
        "browser_status",
        "browser_new_page",
        "browser_list_pages",
        "browser_navigate",
        "browser_get_page_info",
        "browser_go_back",
        "browser_go_forward",
        "browser_reload",
        "browser_wait_for_load",
        "browser_page_snapshot",
        "browser_find_by_role",
        "browser_find_by_text",
        "browser_find_by_label",
        "browser_find_by_placeholder",
        "browser_find_by_test_id",
        "browser_find_buttons",
        "browser_find_links",
        "browser_xpath_query",
        "browser_click_by_role",
        "browser_click_by_text",
        "browser_set_text_by_label",
        "browser_click",
        "browser_double_click",
        "browser_hover",
        "browser_set_text",
        "browser_get_text",
        "browser_get_value",
        "browser_select_option",
        "browser_check",
        "browser_uncheck",
        "browser_execute_js",
        "browser_scroll",
        "browser_scroll_to_element",
        "browser_set_viewport",
        "browser_wait_for_element",
        "browser_highlight_element",
        "browser_clear_highlights",
        "browser_screenshot_analyze",
        "load_image_for_analysis",
        "browser_save_workflow",
        "browser_list_workflows",
        "browser_read_workflow"
      ]
    },
    {
      "name": "release-gate-arbiter",
      "display_name": "Release Gate Arbiter ⚔️",
      "description": "The final non-negotiable authorization gate for SDLC stage transitions at HTT Brands. Adversarial by default — assumes wrong until proven otherwise with receipts. Implements SLSA L3, Sigstore cosign verification, and 8-pillar validation for production releases across 200+ franchise locations.",
      "type": "json",
      "tools": [
        "list_files",
        "read_file",
        "grep",
        "create_file",
        "replace_in_file",
        "delete_snippet",
        "delete_file",
        "agent_run_shell_command",
        "list_agents",
        "invoke_agent",
        "agent_share_your_reasoning",
        "ask_user_question"
      ]
    },
    {
      "name": "slide-puppy",
      "display_name": "Slide-Puppy 🎞️🐶",
      "description": "Reverse-engineered gamma.app + beautiful.ai. Produces best-in-class presentations as Reveal.js, Tailwind/HTML, or Marp decks — with built-in FPO mockups, premium transitions, and visual QA via headless browser. Delegates UX research to experience-architect and tech decisions to solutions-architect.",
      "type": "json",
      "tools": [
        "list_files",
        "read_file",
        "create_file",
        "replace_in_file",
        "delete_snippet",
        "delete_file",
        "grep",
        "agent_run_shell_command",
        "list_agents",
        "agent_share_your_reasoning",
        "ask_user_question",
        "browser_initialize",
        "browser_close",
        "browser_new_page",
        "browser_navigate",
        "browser_wait_for_load",
        "browser_set_viewport",
        "browser_screenshot_analyze",
        "browser_execute_js",
        "browser_scroll",
        "browser_find_by_text",
        "browser_click",
        "load_image_for_analysis",
        "activate_skill",
        "list_or_search_skills",
        "universal_constructor"
      ]
    },
    {
      "name": "solutions-architect",
      "display_name": "Solutions Architect",
      "description": "Backend and infrastructure architect that conducts a two-dog research pack: delegates deep source evaluation to web-puppy and heavy scraping/login/form automation to web-retriever, while carrying web-retriever's full direct-action browser toolbelt itself. Produces MADR 4.0 ADRs with STRIDE analysis and fitness functions.",
      "type": "json",
      "tools": [
        "list_agents",
        "invoke_agent",
        "agent_share_your_reasoning",
        "ask_user_question",
        "list_files",
        "read_file",
        "grep",
        "create_file",
        "replace_in_file",
        "browser_initialize",
        "browser_close",
        "browser_status",
        "browser_new_page",
        "browser_list_pages",
        "browser_navigate",
        "browser_get_page_info",
        "browser_go_back",
        "browser_go_forward",
        "browser_reload",
        "browser_wait_for_load",
        "browser_page_snapshot",
        "browser_find_by_role",
        "browser_find_by_text",
        "browser_find_by_label",
        "browser_find_by_placeholder",
        "browser_find_by_test_id",
        "browser_find_buttons",
        "browser_find_links",
        "browser_xpath_query",
        "browser_click_by_role",
        "browser_click_by_text",
        "browser_set_text_by_label",
        "browser_click",
        "browser_double_click",
        "browser_hover",
        "browser_set_text",
        "browser_get_text",
        "browser_get_value",
        "browser_select_option",
        "browser_check",
        "browser_uncheck",
        "browser_execute_js",
        "browser_scroll",
        "browser_scroll_to_element",
        "browser_set_viewport",
        "browser_wait_for_element",
        "browser_highlight_element",
        "browser_clear_highlights",
        "browser_screenshot_analyze",
        "load_image_for_analysis",
        "browser_save_workflow",
        "browser_list_workflows",
        "browser_read_workflow"
      ]
    },
    {
      "name": "tenantfleet-architect",
      "display_name": "TenantFleet Architect ",
      "description": "Deep architectural synthesizer for multi-tenant identity frameworks. Excels at correlating patterns across disjoint repos and inferring system topology.",
      "type": "json",
      "tools": [
        "agent_share_your_reasoning",
        "agent_run_shell_command",
        "list_files",
        "read_file",
        "grep",
        "invoke_agent",
        "list_agents"
      ]
    },
    {
      "name": "tenantfleet-scanner",
      "display_name": "TenantFleet Scanner ",
      "description": "Massive-context repo scanner for multi-tenant identity frameworks. Ingests entire directory trees and correlates patterns across repos.",
      "type": "json",
      "tools": [
        "agent_share_your_reasoning",
        "agent_run_shell_command",
        "list_files",
        "read_file",
        "grep",
        "invoke_agent",
        "list_agents"
      ]
    },
    {
      "name": "web-puppy",
      "display_name": "Web-Puppy 🕵️‍♂️",
      "description": "Comprehensive web research agent that gathers, evaluates, and synthesizes information from reliable sources with multi-dimensional analysis and project-contextualized reporting",
      "type": "json",
      "tools": [
        "browser_initialize",
        "browser_navigate",
        "browser_new_page",
        "browser_list_pages",
        "browser_find_by_text",
        "browser_find_by_role",
        "browser_find_by_label",
        "browser_find_by_placeholder",
        "browser_find_by_test_id",
        "browser_find_links",
        "browser_xpath_query",
        "browser_get_text",
        "browser_get_value",
        "browser_scroll",
        "browser_scroll_to_element",
        "browser_screenshot_analyze",
        "browser_save_workflow",
        "browser_list_workflows",
        "browser_read_workflow",
        "browser_close",
        "list_files",
        "read_file",
        "edit_file",
        "agent_run_shell_command",
        "agent_share_your_reasoning"
      ]
    },
    {
      "name": "web-retriever",
      "display_name": "Web Retriever",
      "description": "Web scraping, browser automation, and data extraction specialist. Navigates websites, fills forms, clicks through multi-step flows, scrapes/crawls pages, and extracts structured data (to JSON/CSV/markdown) using Playwright. Use for: scrape this site, extract data from this page, automate this web workflow, crawl these URLs, fill out this form, log into this site and grab X. NOT for test assertions/visual QA - see qa-kitten for that.",
      "type": "python",
      "tools": [
        "browser_initialize",
        "browser_close",
        "browser_status",
        "browser_new_page",
        "browser_list_pages",
        "browser_navigate",
        "browser_get_page_info",
        "browser_go_back",
        "browser_go_forward",
        "browser_reload",
        "browser_wait_for_load",
        "browser_page_snapshot",
        "browser_find_by_role",
        "browser_find_by_text",
        "browser_find_by_label",
        "browser_find_by_placeholder",
        "browser_find_by_test_id",
        "browser_find_buttons",
        "browser_find_links",
        "browser_xpath_query",
        "browser_click_by_role",
        "browser_click_by_text",
        "browser_set_text_by_label",
        "browser_click",
        "browser_double_click",
        "browser_hover",
        "browser_set_text",
        "browser_get_text",
        "browser_get_value",
        "browser_select_option",
        "browser_check",
        "browser_uncheck",
        "browser_execute_js",
        "browser_scroll",
        "browser_scroll_to_element",
        "browser_set_viewport",
        "browser_wait_for_element",
        "browser_highlight_element",
        "browser_clear_highlights",
        "browser_screenshot_analyze",
        "load_image_for_analysis",
        "list_files",
        "read_file",
        "grep",
        "create_file",
        "replace_in_file",
        "browser_save_workflow",
        "browser_list_workflows",
        "browser_read_workflow",
        "ask_user_question"
      ]
    }
  ],
  "plugins": [
    {
      "name": "acp",
      "tier": "core-package",
      "description": "`acp` — Code Puppy as a native ACP agent  Run Code Puppy inside any ACP-capable editor's agent panel (e.g.",
      "hooks": [
        "handle_cli_args",
        "register_cli_args"
      ],
      "hasCustomCommand": false,
      "files": [
        {
          "name": "__init__.py",
          "lines": 8
        },
        {
          "name": "agent.py",
          "lines": 494
        },
        {
          "name": "bridge.py",
          "lines": 309
        },
        {
          "name": "capabilities.py",
          "lines": 73
        },
        {
          "name": "commands.py",
          "lines": 116
        },
        {
          "name": "content.py",
          "lines": 115
        },
        {
          "name": "io_delegation.py",
          "lines": 231
        },
        {
          "name": "mcp_config.py",
          "lines": 74
        },
        {
          "name": "permissions.py",
          "lines": 159
        },
        {
          "name": "persistence.py",
          "lines": 211
        },
        {
          "name": "register_callbacks.py",
          "lines": 110
        },
        {
          "name": "replay.py",
          "lines": 127
        },
        {
          "name": "session.py",
          "lines": 331
        },
        {
          "name": "session_config.py",
          "lines": 179
        },
        {
          "name": "state.py",
          "lines": 135
        }
      ],
      "hasReadme": true,
      "hasSkill": false
    },
    {
      "name": "agent_creator_skill",
      "tier": "core-package",
      "description": "Register the bundled ``agent-creator`` delegation skill.",
      "hooks": [
        "register_skills"
      ],
      "hasCustomCommand": false,
      "files": [
        {
          "name": "__init__.py",
          "lines": 1
        },
        {
          "name": "register_callbacks.py",
          "lines": 19
        }
      ],
      "hasReadme": false,
      "hasSkill": true
    },
    {
      "name": "agent_skills",
      "tier": "core-package",
      "description": "Agent Skills plugin - registers callbacks for skill integration.",
      "hooks": [
        "custom_command",
        "custom_command_help",
        "get_model_system_prompt",
        "register_skills",
        "register_tools"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 22
        },
        {
          "name": "config.py",
          "lines": 208
        },
        {
          "name": "discovery.py",
          "lines": 337
        },
        {
          "name": "downloader.py",
          "lines": 392
        },
        {
          "name": "enabled_skills.py",
          "lines": 82
        },
        {
          "name": "installer.py",
          "lines": 22
        },
        {
          "name": "metadata.py",
          "lines": 306
        },
        {
          "name": "prompt_builder.py",
          "lines": 49
        },
        {
          "name": "provider.py",
          "lines": 52
        },
        {
          "name": "register_callbacks.py",
          "lines": 309
        },
        {
          "name": "remote_catalog.py",
          "lines": 322
        },
        {
          "name": "skill_catalog.py",
          "lines": 277
        },
        {
          "name": "skill_commands.py",
          "lines": 102
        },
        {
          "name": "skills_install_menu.py",
          "lines": 698
        },
        {
          "name": "skills_menu.py",
          "lines": 794
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "aws_bedrock",
      "tier": "core-package",
      "description": "AWS Bedrock Plugin callbacks for Code Puppy CLI.",
      "hooks": [
        "custom_command",
        "custom_command_help",
        "register_model_type"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 14
        },
        {
          "name": "config.py",
          "lines": 101
        },
        {
          "name": "register_callbacks.py",
          "lines": 254
        },
        {
          "name": "utils.py",
          "lines": 186
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "azure_foundry",
      "tier": "core-package",
      "description": "Azure AI Foundry Plugin for Code Puppy  This plugin enables Code Puppy to use Anthropic Claude models hosted on Microsoft Azure AI Foundry with Azure AD (Entra...",
      "hooks": [
        "custom_command",
        "custom_command_help",
        "register_model_type"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 15
        },
        {
          "name": "config.py",
          "lines": 126
        },
        {
          "name": "discovery.py",
          "lines": 189
        },
        {
          "name": "register_callbacks.py",
          "lines": 517
        },
        {
          "name": "token.py",
          "lines": 182
        },
        {
          "name": "utils.py",
          "lines": 375
        }
      ],
      "hasReadme": true,
      "hasSkill": false
    },
    {
      "name": "btw",
      "tier": "core-package",
      "description": "Plugin: `/btw` — ask a quick side question without derailing the task.",
      "hooks": [
        "custom_command",
        "custom_command_help"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 1
        },
        {
          "name": "inline_view.py",
          "lines": 135
        },
        {
          "name": "register_callbacks.py",
          "lines": 106
        },
        {
          "name": "side_query.py",
          "lines": 91
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "chatgpt_oauth",
      "tier": "core-package",
      "description": "ChatGPT OAuth plugin callbacks aligned with ChatMock flow.",
      "hooks": [
        "agent_run_start",
        "custom_command",
        "custom_command_help",
        "load_models_config",
        "register_agent_tools",
        "register_model_type",
        "register_skills",
        "register_tools",
        "usage_status"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 8
        },
        {
          "name": "config.py",
          "lines": 55
        },
        {
          "name": "image_generation.py",
          "lines": 253
        },
        {
          "name": "image_tool.py",
          "lines": 70
        },
        {
          "name": "model_catalog.py",
          "lines": 77
        },
        {
          "name": "oauth_flow.py",
          "lines": 461
        },
        {
          "name": "register_callbacks.py",
          "lines": 301
        },
        {
          "name": "test_plugin.py",
          "lines": 683
        },
        {
          "name": "usage.py",
          "lines": 113
        },
        {
          "name": "utils.py",
          "lines": 578
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "claude_code_hooks",
      "tier": "core-package",
      "description": "Register callbacks for Claude Code hooks plugin.",
      "hooks": [
        "agent_run_end",
        "notification",
        "post_tool_call",
        "pre_compact",
        "pre_tool_call",
        "session_end",
        "startup",
        "user_prompt_submit"
      ],
      "hasCustomCommand": false,
      "files": [
        {
          "name": "__init__.py",
          "lines": 1
        },
        {
          "name": "config.py",
          "lines": 137
        },
        {
          "name": "register_callbacks.py",
          "lines": 383
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "claude_code_oauth",
      "tier": "core-package",
      "description": "Claude Code OAuth Plugin  This plugin adds OAuth authentication for Claude Code to Code Puppy, automatically importing available models into your configuration.",
      "hooks": [
        "agent_run_end",
        "agent_run_start",
        "check_claude_oauth_token_expiry",
        "claude_oauth_authenticate",
        "custom_command",
        "custom_command_help",
        "load_claude_oauth_models",
        "prepare_model_prompt",
        "refresh_claude_oauth_token",
        "register_model_type"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 25
        },
        {
          "name": "config.py",
          "lines": 59
        },
        {
          "name": "fast_mode.py",
          "lines": 121
        },
        {
          "name": "prompt_handler.py",
          "lines": 64
        },
        {
          "name": "register_callbacks.py",
          "lines": 717
        },
        {
          "name": "test_plugin.py",
          "lines": 285
        },
        {
          "name": "token_refresh_heartbeat.py",
          "lines": 240
        },
        {
          "name": "utils.py",
          "lines": 663
        }
      ],
      "hasReadme": true,
      "hasSkill": false
    },
    {
      "name": "code_puppy_agent",
      "tier": "core-package",
      "description": "Register the built-in ``code-puppy-agent`` skill.",
      "hooks": [
        "register_skills"
      ],
      "hasCustomCommand": false,
      "files": [
        {
          "name": "__init__.py",
          "lines": 5
        },
        {
          "name": "register_callbacks.py",
          "lines": 46
        }
      ],
      "hasReadme": false,
      "hasSkill": true
    },
    {
      "name": "computer_use",
      "tier": "core-package",
      "description": "macOS Computer Use  This opt-in plugin lets Code Puppy inspect and operate the current macOS desktop through Apple's Accessibility APIs.",
      "hooks": [
        "custom_command",
        "custom_command_help",
        "load_prompt",
        "register_agent_tools",
        "register_tools",
        "startup"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 1
        },
        {
          "name": "accessibility.py",
          "lines": 163
        },
        {
          "name": "activation.py",
          "lines": 75
        },
        {
          "name": "backend.py",
          "lines": 584
        },
        {
          "name": "backend_types.py",
          "lines": 5
        },
        {
          "name": "capture.py",
          "lines": 110
        },
        {
          "name": "commands.py",
          "lines": 62
        },
        {
          "name": "geometry.py",
          "lines": 81
        },
        {
          "name": "inline_image.py",
          "lines": 56
        },
        {
          "name": "keycodes.py",
          "lines": 47
        },
        {
          "name": "policy.py",
          "lines": 144
        },
        {
          "name": "register_callbacks.py",
          "lines": 96
        },
        {
          "name": "safety.py",
          "lines": 18
        },
        {
          "name": "settle.py",
          "lines": 64
        },
        {
          "name": "state.py",
          "lines": 86
        },
        {
          "name": "tools.py",
          "lines": 469
        }
      ],
      "hasReadme": true,
      "hasSkill": false
    },
    {
      "name": "context_indicator",
      "tier": "core-package",
      "description": "Register callbacks for the ``context_indicator`` plugin.",
      "hooks": [
        "custom_command",
        "custom_command_help",
        "startup"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 14
        },
        {
          "name": "register_callbacks.py",
          "lines": 249
        },
        {
          "name": "usage.py",
          "lines": 40
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "copilot_auth",
      "tier": "core-package",
      "description": "GitHub Copilot auth plugin — callback registrations.",
      "hooks": [
        "custom_command",
        "custom_command_help",
        "register_model_type"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 11
        },
        {
          "name": "config.py",
          "lines": 93
        },
        {
          "name": "reasoning_client.py",
          "lines": 409
        },
        {
          "name": "register_callbacks.py",
          "lines": 460
        },
        {
          "name": "utils.py",
          "lines": 587
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "customizable_commands",
      "tier": "core-package",
      "description": "",
      "hooks": [
        "custom_command",
        "custom_command_help"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 0
        },
        {
          "name": "register_callbacks.py",
          "lines": 464
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "dbos_durable_exec",
      "tier": "core-package",
      "description": "Wire the DBOS durable-execution plugin into core via callback hooks.",
      "hooks": [
        "agent_run_cancel",
        "agent_run_context",
        "custom_command",
        "custom_command_help",
        "feature_capability",
        "should_skip_fallback_render",
        "shutdown",
        "startup",
        "wrap_pydantic_agent"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 1
        },
        {
          "name": "cancel.py",
          "lines": 15
        },
        {
          "name": "commands.py",
          "lines": 31
        },
        {
          "name": "config.py",
          "lines": 31
        },
        {
          "name": "lifecycle.py",
          "lines": 83
        },
        {
          "name": "register_callbacks.py",
          "lines": 45
        },
        {
          "name": "runtime.py",
          "lines": 60
        },
        {
          "name": "startup_lock.py",
          "lines": 155
        },
        {
          "name": "workflow_ids.py",
          "lines": 16
        },
        {
          "name": "wrapper.py",
          "lines": 58
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "destructive_command_guard",
      "tier": "core-package",
      "description": "Callback registration for the destructive command guard plugin.",
      "hooks": [
        "run_shell_command"
      ],
      "hasCustomCommand": false,
      "files": [
        {
          "name": "__init__.py",
          "lines": 14
        },
        {
          "name": "detector.py",
          "lines": 374
        },
        {
          "name": "register_callbacks.py",
          "lines": 165
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "emoji_filter",
      "tier": "core-package",
      "description": "Wire emoji_filter into the runtime.",
      "hooks": [
        "custom_command",
        "custom_command_help",
        "pre_tool_call",
        "startup",
        "stream_event"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 12
        },
        {
          "name": "config.py",
          "lines": 26
        },
        {
          "name": "register_callbacks.py",
          "lines": 309
        },
        {
          "name": "stripper.py",
          "lines": 45
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "empty_html_comment_filter",
      "tier": "core-package",
      "description": "Hide whitespace-only HTML comments from streamed thinking display.",
      "hooks": [
        "thinking_display_filter"
      ],
      "hasCustomCommand": false,
      "files": [
        {
          "name": "register_callbacks.py",
          "lines": 116
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "example_custom_command",
      "tier": "core-package",
      "description": "Example Custom Command Plugin  > **Note**: This example demonstrates **custom commands** via the callback system.",
      "hooks": [
        "custom_command",
        "custom_command_help"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "register_callbacks.py",
          "lines": 66
        }
      ],
      "hasReadme": true,
      "hasSkill": false
    },
    {
      "name": "file_permission_handler",
      "tier": "core-package",
      "description": "File Permission Handler Plugin.",
      "hooks": [
        "file_permission",
        "load_prompt"
      ],
      "hasCustomCommand": false,
      "files": [
        {
          "name": "__init__.py",
          "lines": 4
        },
        {
          "name": "register_callbacks.py",
          "lines": 575
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "flux_bootstrap",
      "tier": "core-package",
      "description": "Flux bootstrap plugin.",
      "hooks": [
        "startup"
      ],
      "hasCustomCommand": false,
      "files": [
        {
          "name": "__init__.py",
          "lines": 5
        },
        {
          "name": "installer.py",
          "lines": 256
        },
        {
          "name": "register_callbacks.py",
          "lines": 71
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "force_push_guard",
      "tier": "core-package",
      "description": "Callback registration for the force push guard plugin.",
      "hooks": [
        "run_shell_command"
      ],
      "hasCustomCommand": false,
      "files": [
        {
          "name": "__init__.py",
          "lines": 5
        },
        {
          "name": "detector.py",
          "lines": 96
        },
        {
          "name": "register_callbacks.py",
          "lines": 161
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "fork",
      "tier": "core-package",
      "description": "``/fork`` — spawn a sub-agent in the background and keep working.",
      "hooks": [
        "custom_command",
        "custom_command_help"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 7
        },
        {
          "name": "register_callbacks.py",
          "lines": 445
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "frontend_emitter",
      "tier": "core-package",
      "description": "Callback registration for frontend event emission.",
      "hooks": [
        "invoke_agent",
        "post_tool_call",
        "pre_tool_call",
        "stream_event"
      ],
      "hasCustomCommand": false,
      "files": [
        {
          "name": "__init__.py",
          "lines": 25
        },
        {
          "name": "emitter.py",
          "lines": 249
        },
        {
          "name": "register_callbacks.py",
          "lines": 412
        },
        {
          "name": "session_context.py",
          "lines": 50
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "grok_oauth",
      "tier": "core-package",
      "description": "Grok (x.ai) OAuth plugin callbacks.",
      "hooks": [
        "custom_command",
        "custom_command_help",
        "load_models_config",
        "register_model_type"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 6
        },
        {
          "name": "config.py",
          "lines": 49
        },
        {
          "name": "oauth_flow.py",
          "lines": 213
        },
        {
          "name": "register_callbacks.py",
          "lines": 132
        },
        {
          "name": "utils.py",
          "lines": 195
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "herdr",
      "tier": "core-package",
      "description": "herdr integration  Makes code-puppy a first-class citizen in [**herdr**](https://herdr.dev), a terminal workspace manager for coding agents.",
      "hooks": [
        "agent_run_cancel",
        "agent_run_end",
        "agent_run_start",
        "awaiting_user_input",
        "interactive_turn_cancel",
        "interactive_turn_end",
        "post_tool_call",
        "pre_tool_call",
        "session_end",
        "shutdown",
        "startup",
        "user_prompt_submit"
      ],
      "hasCustomCommand": false,
      "files": [
        {
          "name": "__init__.py",
          "lines": 9
        },
        {
          "name": "client.py",
          "lines": 339
        },
        {
          "name": "register_callbacks.py",
          "lines": 140
        },
        {
          "name": "reporter.py",
          "lines": 212
        },
        {
          "name": "smoke.py",
          "lines": 143
        },
        {
          "name": "sources.py",
          "lines": 133
        }
      ],
      "hasReadme": true,
      "hasSkill": false
    },
    {
      "name": "hook_creator",
      "tier": "core-package",
      "description": "Hook Creator Plugin - Simple command that injects MCP prompt",
      "hooks": [
        "custom_command",
        "custom_command_help"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 1
        },
        {
          "name": "register_callbacks.py",
          "lines": 33
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "hook_manager",
      "tier": "core-package",
      "description": "Hook Manager plugin – registers callbacks for interactive hook management.",
      "hooks": [
        "custom_command",
        "custom_command_help"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 1
        },
        {
          "name": "config.py",
          "lines": 290
        },
        {
          "name": "hooks_menu.py",
          "lines": 571
        },
        {
          "name": "register_callbacks.py",
          "lines": 227
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "i_have_adhd",
      "tier": "user",
      "description": "i-have-adhd (Code Puppy port)  ADHD-friendly output mode, ported from [ayghri/i-have-adhd](https://github.com/ayghri/i-have-adhd) (MIT).",
      "hooks": [
        "custom_command",
        "custom_command_help",
        "load_prompt",
        "register_skills"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 0
        },
        {
          "name": "register_callbacks.py",
          "lines": 141
        }
      ],
      "hasReadme": true,
      "hasSkill": true
    },
    {
      "name": "meta_oauth",
      "tier": "core-package",
      "description": "Callbacks for Meta Muse OAuth authentication and model registration.",
      "hooks": [
        "custom_command",
        "custom_command_help",
        "load_models_config",
        "register_model_type"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 1
        },
        {
          "name": "config.py",
          "lines": 55
        },
        {
          "name": "oauth_flow.py",
          "lines": 109
        },
        {
          "name": "register_callbacks.py",
          "lines": 154
        },
        {
          "name": "utils.py",
          "lines": 252
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "namespace_skill_search",
      "tier": "core-package",
      "description": "namespace_skill_search  Model-agnostic reimplementation of OpenAI's namespace + `tool_search` pattern, applied to Code Puppy's skill catalog.",
      "hooks": [
        "load_prompt",
        "register_agent_tools",
        "register_tools",
        "startup"
      ],
      "hasCustomCommand": false,
      "files": [
        {
          "name": "__init__.py",
          "lines": 15
        },
        {
          "name": "namespaces.py",
          "lines": 125
        },
        {
          "name": "register_callbacks.py",
          "lines": 99
        },
        {
          "name": "search_tool.py",
          "lines": 158
        }
      ],
      "hasReadme": true,
      "hasSkill": false
    },
    {
      "name": "no_tools",
      "tier": "core-package",
      "description": "``--no-tools`` CLI flag (issue #182).",
      "hooks": [
        "handle_cli_args",
        "register_cli_args"
      ],
      "hasCustomCommand": false,
      "files": [
        {
          "name": "__init__.py",
          "lines": 0
        },
        {
          "name": "register_callbacks.py",
          "lines": 42
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "obsidian_agent",
      "tier": "core-package",
      "description": "Obsidian Agent  The Obsidian Agent adds a specialized Code Puppy agent for working with Obsidian vaults through the official `obsidian` CLI.",
      "hooks": [
        "register_agents"
      ],
      "hasCustomCommand": false,
      "files": [
        {
          "name": "__init__.py",
          "lines": 8
        },
        {
          "name": "agent_obsidian.py",
          "lines": 147
        },
        {
          "name": "register_callbacks.py",
          "lines": 13
        }
      ],
      "hasReadme": true,
      "hasSkill": false
    },
    {
      "name": "ollama",
      "tier": "core-package",
      "description": "Ollama model type handler for OpenAI Chat Completions-compatible endpoints.",
      "hooks": [
        "register_model_type"
      ],
      "hasCustomCommand": false,
      "files": [
        {
          "name": "__init__.py",
          "lines": 1
        },
        {
          "name": "register_callbacks.py",
          "lines": 126
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "ollama_setup",
      "tier": "core-package",
      "description": "Ollama cloud model setup — /ollama-setup command.",
      "hooks": [
        "custom_command",
        "custom_command_help",
        "register_completion_provider"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 5
        },
        {
          "name": "completer.py",
          "lines": 38
        },
        {
          "name": "register_callbacks.py",
          "lines": 419
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "plugin_list",
      "tier": "core-package",
      "description": "``/plugins`` slash command -- manage plugins interactively or via subcommands.",
      "hooks": [
        "custom_command",
        "custom_command_help",
        "startup"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 0
        },
        {
          "name": "plugin_contributions.py",
          "lines": 348
        },
        {
          "name": "plugin_meta.py",
          "lines": 67
        },
        {
          "name": "plugin_text_utils.py",
          "lines": 173
        },
        {
          "name": "plugins_menu.py",
          "lines": 455
        },
        {
          "name": "plugins_menu_layout.py",
          "lines": 194
        },
        {
          "name": "plugins_menu_render.py",
          "lines": 431
        },
        {
          "name": "project_trust_flow.py",
          "lines": 162
        },
        {
          "name": "register_callbacks.py",
          "lines": 281
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "pop_command",
      "tier": "core-package",
      "description": "Plugin that adds /pop for trimming recent conversation history.",
      "hooks": [
        "custom_command",
        "custom_command_help"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 1
        },
        {
          "name": "register_callbacks.py",
          "lines": 191
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "prompt_newline",
      "tier": "core-package",
      "description": "Register callbacks for the prompt_newline plugin.",
      "hooks": [
        "custom_command",
        "custom_command_help",
        "startup"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 13
        },
        {
          "name": "config.py",
          "lines": 21
        },
        {
          "name": "register_callbacks.py",
          "lines": 163
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "prune",
      "tier": "core-package",
      "description": "Plugin that adds /prune for surgical history pruning.",
      "hooks": [
        "custom_command",
        "custom_command_help"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 1
        },
        {
          "name": "prune_menu.py",
          "lines": 308
        },
        {
          "name": "prune_model.py",
          "lines": 536
        },
        {
          "name": "prune_render.py",
          "lines": 354
        },
        {
          "name": "register_callbacks.py",
          "lines": 388
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "puppy_kennel",
      "tier": "core-package",
      "description": "Puppy Kennel  Local-first memory for Code Puppy.",
      "hooks": [
        "agent_run_end",
        "custom_command",
        "custom_command_help",
        "load_prompt",
        "register_agent_tools",
        "register_kennel_memory",
        "register_tools"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 6
        },
        {
          "name": "commands.py",
          "lines": 206
        },
        {
          "name": "config.py",
          "lines": 36
        },
        {
          "name": "kennel.py",
          "lines": 368
        },
        {
          "name": "packer.py",
          "lines": 152
        },
        {
          "name": "recorder.py",
          "lines": 83
        },
        {
          "name": "register_callbacks.py",
          "lines": 109
        },
        {
          "name": "retriever.py",
          "lines": 28
        },
        {
          "name": "schema.py",
          "lines": 78
        },
        {
          "name": "state.py",
          "lines": 68
        },
        {
          "name": "tools.py",
          "lines": 449
        },
        {
          "name": "wings.py",
          "lines": 110
        }
      ],
      "hasReadme": true,
      "hasSkill": false
    },
    {
      "name": "puppy_spinner",
      "tier": "core-package",
      "description": "puppy_spinner  The bouncing-puppy spinner on the bottom bar's status-prefix slot — now with customizable styles.",
      "hooks": [
        "agent_run_end",
        "agent_run_start",
        "custom_command",
        "custom_command_help"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 11
        },
        {
          "name": "builtin_frames.py",
          "lines": 172
        },
        {
          "name": "commands.py",
          "lines": 116
        },
        {
          "name": "picker.py",
          "lines": 379
        },
        {
          "name": "register_callbacks.py",
          "lines": 193
        },
        {
          "name": "spinners.py",
          "lines": 444
        }
      ],
      "hasReadme": true,
      "hasSkill": false
    },
    {
      "name": "qa_kitten_skill",
      "tier": "core-package",
      "description": "Register the bundled ``qa-kitten`` delegation skill.",
      "hooks": [
        "register_skills"
      ],
      "hasCustomCommand": false,
      "files": [
        {
          "name": "__init__.py",
          "lines": 1
        },
        {
          "name": "register_callbacks.py",
          "lines": 19
        }
      ],
      "hasReadme": false,
      "hasSkill": true
    },
    {
      "name": "quick_resume",
      "tier": "core-package",
      "description": "Quick-resume workspace observation hooks.",
      "hooks": [
        "post_tool_call"
      ],
      "hasCustomCommand": false,
      "files": [
        {
          "name": "__init__.py",
          "lines": 0
        },
        {
          "name": "register_callbacks.py",
          "lines": 77
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "review_pr",
      "tier": "core-package",
      "description": "Plugin: `/review-pr` — hand the agent a structured PR review mission.",
      "hooks": [
        "custom_command",
        "custom_command_help"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 1
        },
        {
          "name": "register_callbacks.py",
          "lines": 162
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "shell_safety",
      "tier": "core-package",
      "description": "Callback registration for shell command safety checking.",
      "hooks": [
        "run_shell_command"
      ],
      "hasCustomCommand": false,
      "files": [
        {
          "name": "__init__.py",
          "lines": 6
        },
        {
          "name": "agent_shell_safety.py",
          "lines": 69
        },
        {
          "name": "command_cache.py",
          "lines": 156
        },
        {
          "name": "register_callbacks.py",
          "lines": 203
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "spill",
      "tier": "core-package",
      "description": "Plugin: spill oversized dict-shaped tool results to private files.",
      "hooks": [
        "post_tool_call",
        "startup"
      ],
      "hasCustomCommand": false,
      "files": [
        {
          "name": "__init__.py",
          "lines": 1
        },
        {
          "name": "register_callbacks.py",
          "lines": 336
        },
        {
          "name": "store.py",
          "lines": 173
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "stack_dump",
      "tier": "core-package",
      "description": "Register callbacks for the ``stack_dump`` plugin.",
      "hooks": [
        "startup"
      ],
      "hasCustomCommand": false,
      "files": [
        {
          "name": "__init__.py",
          "lines": 1
        },
        {
          "name": "register_callbacks.py",
          "lines": 79
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "statusline",
      "tier": "core-package",
      "description": "Wire up the statusline plugin.",
      "hooks": [
        "custom_command",
        "custom_command_help",
        "git_branch_provider",
        "startup"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 14
        },
        {
          "name": "config.py",
          "lines": 68
        },
        {
          "name": "payload.py",
          "lines": 138
        },
        {
          "name": "prompt_patch.py",
          "lines": 76
        },
        {
          "name": "register_callbacks.py",
          "lines": 45
        },
        {
          "name": "runner.py",
          "lines": 122
        },
        {
          "name": "statusline_command.py",
          "lines": 197
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "steer_queue",
      "tier": "core-package",
      "description": "Register callbacks for the ``steer_queue`` plugin.",
      "hooks": [
        "custom_command",
        "custom_command_help",
        "startup"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 10
        },
        {
          "name": "queue_menu.py",
          "lines": 444
        },
        {
          "name": "register_callbacks.py",
          "lines": 138
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "subagent_panel",
      "tier": "core-package",
      "description": "subagent_panel  A live, two-line status block for each running sub-agent, painted just above the bouncing puppy:  ```   INVOKE AGENT  pup-ticket-investigator...",
      "hooks": [
        "agent_run_cancel",
        "agent_run_end",
        "post_tool_call",
        "startup",
        "stream_event"
      ],
      "hasCustomCommand": false,
      "files": [
        {
          "name": "__init__.py",
          "lines": 24
        },
        {
          "name": "coalesce_patch.py",
          "lines": 242
        },
        {
          "name": "panel_render.py",
          "lines": 145
        },
        {
          "name": "register_callbacks.py",
          "lines": 535
        },
        {
          "name": "resume_repaint.py",
          "lines": 112
        },
        {
          "name": "state.py",
          "lines": 231
        }
      ],
      "hasReadme": true,
      "hasSkill": false
    },
    {
      "name": "switch_agent_resume",
      "tier": "core-package",
      "description": "Register /switch-agent and /sa custom commands.",
      "hooks": [
        "custom_command",
        "custom_command_help",
        "startup"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 5
        },
        {
          "name": "register_callbacks.py",
          "lines": 314
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "theme",
      "tier": "core-package",
      "description": "theme — `/theme` for Code Puppy  A friendlier `/theme` command with an **interactive picker**, **live preview**, and **four layers of theming** — banner header...",
      "hooks": [
        "custom_command",
        "custom_command_help",
        "prompt_text_color",
        "prompt_toolkit_style",
        "startup",
        "termflow_highlighter",
        "termflow_style"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 14
        },
        {
          "name": "bundled_palettes.py",
          "lines": 346
        },
        {
          "name": "content_styles.py",
          "lines": 146
        },
        {
          "name": "osc_palette.py",
          "lines": 178
        },
        {
          "name": "picker.py",
          "lines": 358
        },
        {
          "name": "prompt_toolkit_theme.py",
          "lines": 113
        },
        {
          "name": "register_callbacks.py",
          "lines": 348
        },
        {
          "name": "rich_themes.py",
          "lines": 202
        },
        {
          "name": "themes.py",
          "lines": 720
        }
      ],
      "hasReadme": true,
      "hasSkill": false
    },
    {
      "name": "timestamp_heartbeat",
      "tier": "core-package",
      "description": "Plugin: timestamp heartbeat — stamp the current datetime into tool results.",
      "hooks": [
        "post_tool_call"
      ],
      "hasCustomCommand": false,
      "files": [
        {
          "name": "__init__.py",
          "lines": 1
        },
        {
          "name": "register_callbacks.py",
          "lines": 114
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "token_ratio_learner",
      "tier": "core-package",
      "description": "Register callbacks for the token-ratio-learner plugin.",
      "hooks": [
        "startup"
      ],
      "hasCustomCommand": false,
      "files": [
        {
          "name": "__init__.py",
          "lines": 5
        },
        {
          "name": "ratios.py",
          "lines": 208
        },
        {
          "name": "register_callbacks.py",
          "lines": 218
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "universal_constructor",
      "tier": "core-package",
      "description": "Callback registration for the Universal Constructor plugin.",
      "hooks": [
        "register_tools",
        "startup"
      ],
      "hasCustomCommand": false,
      "files": [
        {
          "name": "__init__.py",
          "lines": 13
        },
        {
          "name": "models.py",
          "lines": 138
        },
        {
          "name": "provider.py",
          "lines": 62
        },
        {
          "name": "register_callbacks.py",
          "lines": 75
        },
        {
          "name": "registry.py",
          "lines": 302
        },
        {
          "name": "sandbox.py",
          "lines": 584
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "update_schedule",
      "tier": "user",
      "description": "User plugin: /update slash command for the code-puppy daily update schedule.",
      "hooks": [
        "agent_run_start",
        "custom_command",
        "custom_command_help"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "register_callbacks.py",
          "lines": 240
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "web_retriever_skill",
      "tier": "core-package",
      "description": "Register the built-in ``web-retriever`` skill.",
      "hooks": [
        "register_skills"
      ],
      "hasCustomCommand": false,
      "files": [
        {
          "name": "__init__.py",
          "lines": 1
        },
        {
          "name": "register_callbacks.py",
          "lines": 20
        }
      ],
      "hasReadme": false,
      "hasSkill": true
    },
    {
      "name": "wide_completion_menu",
      "tier": "core-package",
      "description": "Register callbacks for the ``wide_completion_menu`` plugin.",
      "hooks": [
        "custom_command",
        "custom_command_help",
        "startup"
      ],
      "hasCustomCommand": true,
      "files": [
        {
          "name": "__init__.py",
          "lines": 6
        },
        {
          "name": "register_callbacks.py",
          "lines": 165
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "wiggum",
      "tier": "core-package",
      "description": "Register the Wiggum looping slash commands and goal continuation policy.",
      "hooks": [
        "feature_capability",
        "interactive_turn_cancel",
        "interactive_turn_end"
      ],
      "hasCustomCommand": false,
      "files": [
        {
          "name": "__init__.py",
          "lines": 1
        },
        {
          "name": "goal_runs.py",
          "lines": 91
        },
        {
          "name": "judge.py",
          "lines": 299
        },
        {
          "name": "judge_config.py",
          "lines": 249
        },
        {
          "name": "judges_menu.py",
          "lines": 814
        },
        {
          "name": "register_callbacks.py",
          "lines": 569
        },
        {
          "name": "state.py",
          "lines": 89
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    },
    {
      "name": "yolo_cli",
      "tier": "core-package",
      "description": "Expose a runtime-only YOLO override through the CLI.",
      "hooks": [
        "handle_cli_args",
        "register_cli_args"
      ],
      "hasCustomCommand": false,
      "files": [
        {
          "name": "__init__.py",
          "lines": 1
        },
        {
          "name": "register_callbacks.py",
          "lines": 41
        }
      ],
      "hasReadme": false,
      "hasSkill": false
    }
  ],
  "skills": [
    {
      "name": "agent-creator",
      "source": "core-package",
      "description": "Use before creating or revising a Code Puppy JSON agent. Delegates schema design, least-privilege tool selection, optional model and MCP bindings, validation, and per-agent Spill configuration to agent-creator.",
      "path": "code_puppy_core_plugins/agent_creator_skill/SKILL.md"
    },
    {
      "name": "code-puppy-agent",
      "source": "core-package",
      "description": "How Code Puppy itself is built — its internal architecture, structure, codebase layout, and source modules. Explains agents, tools, the plugin/callback hook system, models, MCP, sessions and history/context windows, skills (including skill namespaces for large catalogs), slash commands, config, messaging/UI, system-prompt assembly, and i18n. Activate for ANY question about how Code Puppy works internally, why it behaves a certain way, where something lives in the code, how a feature is implemented, or how to navigate, debug, or extend the codebase (add a tool, agent, plugin, command, skill, model, or MCP server).",
      "path": "code_puppy_core_plugins/code_puppy_agent/SKILL.md"
    },
    {
      "name": "i-have-adhd",
      "source": "user",
      "description": "Shape output for a reader with ADHD: lead with the next action, number multi-step work, restate state across turns, suppress tangents, give specific time estimates, make wins visible. Invoke with /adhd on; stays on until /adhd off.",
      "path": "/Users/tygranlund/.code_puppy/plugins/i_have_adhd/SKILL.md"
    },
    {
      "name": "qa-kitten",
      "source": "core-package",
      "description": "Use before testing a web application's behavior, accessibility, responsive layout, or visual rendering in a real browser. Delegates browser assertions and visual QA to qa-kitten; not for scraping, crawling, or general web retrieval.",
      "path": "code_puppy_core_plugins/qa_kitten_skill/SKILL.md"
    },
    {
      "name": "web-retriever",
      "source": "core-package",
      "description": "Use before handling web scraping, browser automation, crawling, structured data extraction, authenticated or interactive website workflows, monitoring pages for changes, or website screenshots. Delegates browser work to the web-retriever agent; not for test assertions or visual QA.",
      "path": "code_puppy_core_plugins/web_retriever_skill/SKILL.md"
    }
  ],
  "sdlc": [
    {
      "stage": "1. Ideate & Spec",
      "goal": "Turn a fuzzy idea into a crisp, testable plan.",
      "use": [
        "code-puppy to draft the design and spike options",
        "Agent Creator to spin up a domain-specialist sub-agent if the work repeats",
        "kennel memory to record decisions so the next session knows them"
      ],
      "output": "A written spec + acceptance criteria the agent can verify against."
    },
    {
      "stage": "2. Explore & Research",
      "goal": "Verify facts before writing code.",
      "use": [
        "web-puppy for docs, version compatibility, and API research",
        "web-retriever (via invoke_agent) for scraping/automation flows",
        "grep/read_file to ground decisions in the existing codebase"
      ],
      "output": "A citation-backed summary of constraints and known-good approaches."
    },
    {
      "stage": "3. Build",
      "goal": "Implement in small, reviewable diffs.",
      "use": [
        "replace_in_file over full rewrites (small diffs, easy review)",
        "Plugins over core edits (golden rule: new functionality = a plugin, not core)",
        "Helios / universal_constructor when you need a tool that doesn't exist"
      ],
      "output": "Working code that respects the repo's conventions (DRY, YAGNI, <600 lines/file)."
    },
    {
      "stage": "4. Test & QA",
      "goal": "Prove it works and looks right.",
      "use": [
        "agent_run_shell_command to run the test suite for real",
        "qa-kitten for visual/assertion QA on UIs",
        "Loop: run, read failures, fix, re-run. Don't stop at 'should work'."
      ],
      "output": "A green test run, not a promise."
    },
    {
      "stage": "5. Secure & Comply",
      "goal": "Ship something you won't regret.",
      "use": [
        "destructive_command_guard & force_push_guard plugins to block foot-guns",
        "Project plugin trust-gate so repo code can't silently self-approve",
        "Review diffs and secrets handling before commit"
      ],
      "output": "Code with guardrails active and no leaked secrets."
    },
    {
      "stage": "6. Ship & Polish",
      "goal": "Make it badass and beautiful, then deliver.",
      "use": [
        "Design-system tokens (like the CPU deck's tokens.css) for prompt-addressable theming",
        "The field guide itself to onboard collaborators",
        "dbos_durable_exec for long jobs that must survive crashes"
      ],
      "output": "A stable, documented artifact you're proud to demo."
    }
  ],
  "changelog": {
    "total_commits": 715,
    "releases": [
      {
        "month": "2026-08",
        "commit_count": 311,
        "commits": [
          {
            "hash": "853baa9bb68e3ebbc00be0d0d3a5f763154e3ae3",
            "short_hash": "853baa9b",
            "subject": "chore: auto-commit pre-update leftovers (2026-08-18 20:00)",
            "author": "Tyler Granlund",
            "date": "2026-08-18",
            "month": "2026-08"
          },
          {
            "hash": "58efc338f25f72f74dc06c9e31c23253d5889a75",
            "short_hash": "58efc338",
            "subject": "docs(field-guide+observatory): regenerate + post-update leftovers (2026-08-18 12:01)",
            "author": "Tyler Granlund",
            "date": "2026-08-18",
            "month": "2026-08"
          },
          {
            "hash": "e33335b875af3fee8bdaa51d3e8e3cf4e7556a36",
            "short_hash": "e33335b8",
            "subject": "feat(a11y): sweep legacy page bodies to WCAG 2.2 AAA body-text contrast",
            "author": "Tyler Granlund",
            "date": "2026-08-18",
            "month": "2026-08"
          },
          {
            "hash": "3a68d68bb95ca53bb1912834c4648a612cd014f3",
            "short_hash": "3a68d68b",
            "subject": "docs(field-guide+observatory): regenerate + post-update leftovers (2026-08-18 07:02)",
            "author": "Tyler Granlund",
            "date": "2026-08-18",
            "month": "2026-08"
          },
          {
            "hash": "cc2716ee1683774a797fb3c127a88b9ceed38569",
            "short_hash": "cc2716ee",
            "subject": "docs(field-guide+observatory): regenerate + post-update leftovers (2026-08-17 20:02)",
            "author": "Tyler Granlund",
            "date": "2026-08-17",
            "month": "2026-08"
          },
          {
            "hash": "53e2126c0ac70f05f41dd27cc4dca9a885e15ddf",
            "short_hash": "53e2126c",
            "subject": "docs: build log + roadmap (what shipped, where, QA status, forward plan)",
            "author": "Tyler Granlund",
            "date": "2026-08-17",
            "month": "2026-08"
          },
          {
            "hash": "f32d6894a59a9fa51486cb82f2e1353fe4e26f69",
            "short_hash": "f32d6894",
            "subject": "feat(ui): sidebar app-shell + reusable popover + design system, WCAG 2.2 AAA",
            "author": "Tyler Granlund",
            "date": "2026-08-17",
            "month": "2026-08"
          },
          {
            "hash": "5816642da3d1319cf9f4f2379e90ff54954b71d7",
            "short_hash": "5816642d",
            "subject": "docs(field-guide+observatory): regenerate + post-update leftovers (2026-08-17 17:21)",
            "author": "Tyler Granlund",
            "date": "2026-08-17",
            "month": "2026-08"
          },
          {
            "hash": "37b06f17ce038955d65f1ccd30820a32d7c788c5",
            "short_hash": "37b06f17",
            "subject": "fix(field-guide): flat-doc JSON corruption + responsive [mobile/tablet] layout",
            "author": "Tyler Granlund",
            "date": "2026-08-17",
            "month": "2026-08"
          },
          {
            "hash": "ece00b6eb5428d85105df24d9d0789c91128719d",
            "short_hash": "ece00b6e",
            "subject": "feat(brand): lucide icon pass + face-only mark, brand watermarks across site",
            "author": "Tyler Granlund",
            "date": "2026-08-17",
            "month": "2026-08"
          }
        ]
      },
      {
        "month": "2026-07",
        "commit_count": 366,
        "commits": [
          {
            "hash": "664e151a7c619c3786b848510f61b3b426389d19",
            "short_hash": "664e151a",
            "subject": "docs: CPU interactive curriculum web app + puppy mark",
            "author": "Tyler Granlund",
            "date": "2026-07-31",
            "month": "2026-07"
          },
          {
            "hash": "755c9c305534e267a3f3b4433a60ed184f3a6ff8",
            "short_hash": "755c9c30",
            "subject": "docs: deck v3 — Acts IX/X, the internal + external university",
            "author": "Tyler Granlund",
            "date": "2026-07-31",
            "month": "2026-07"
          },
          {
            "hash": "b1f40c11d829a9f4bc12b1663e6fa53e75a41e9e",
            "short_hash": "b1f40c11",
            "subject": "docs: deck v2.1 — token architecture, component registry, 42-test suite",
            "author": "Tyler Granlund",
            "date": "2026-07-30",
            "month": "2026-07"
          },
          {
            "hash": "4afb9a2b87bc610040e182552a77d7e84ee430c5",
            "short_hash": "4afb9a2b",
            "subject": "docs: deck v2 — Cornerstone+ design system, Fireship beat, fact-check pass",
            "author": "Tyler Granlund",
            "date": "2026-07-30",
            "month": "2026-07"
          },
          {
            "hash": "a0524d5f2d1498a83eae40589b2e117e4138d0ba",
            "short_hash": "a0524d5f",
            "subject": "docs: The Great Adpuppytion — Code-Puppy University founding deck",
            "author": "Tyler Granlund",
            "date": "2026-07-30",
            "month": "2026-07"
          },
          {
            "hash": "6a9f539bf7df86767f85a474f9a5fbe55dbd7ac6",
            "short_hash": "6a9f539b",
            "subject": "fix(mcp): a config can't be its own untrusted project twin (CWD == $HOME)",
            "author": "breedx",
            "date": "2026-07-31",
            "month": "2026-07"
          },
          {
            "hash": "0d7764e03a34959b2cea717521fc21c7f9d1692c",
            "short_hash": "0d7764e0",
            "subject": "chore: bump version [ci skip]",
            "author": "github-actions[bot]",
            "date": "2026-07-30",
            "month": "2026-07"
          },
          {
            "hash": "37f5a9adf736df41e6465e6979aaab9f19b7ff03",
            "short_hash": "37f5a9ad",
            "subject": "fix(computer-use): require explicit opt-in (#688)",
            "author": "mpfaffenberger",
            "date": "2026-07-30",
            "month": "2026-07"
          },
          {
            "hash": "baa95cefc63778c6320cad6654246e5d8102f503",
            "short_hash": "baa95cef",
            "subject": "chore: bump version [ci skip]",
            "author": "github-actions[bot]",
            "date": "2026-07-29",
            "month": "2026-07"
          },
          {
            "hash": "bfc4927f209493b8a97fc968cf9f38af5734c21d",
            "short_hash": "bfc4927f",
            "subject": "Merge pull request #685 from mpfaffenberger/awtilso/PUP-549",
            "author": "Andrew Tilson",
            "date": "2026-07-29",
            "month": "2026-07"
          }
        ]
      },
      {
        "month": "2026-06",
        "commit_count": 38,
        "commits": [
          {
            "hash": "b76275aba4b09556f69f0c09dc33c70b922f174d",
            "short_hash": "b76275ab",
            "subject": "test(command-line): remove obsolete setting default tests and fix provider mock",
            "author": "Mike Pfaffenberger",
            "date": "2026-06-30",
            "month": "2026-06"
          },
          {
            "hash": "bb7a3e368ac2393f2c86eaefec818c550a7ef69a",
            "short_hash": "bb7a3e36",
            "subject": "feat(model-factory): use chat_template_kwargs for Lilac GLM provider",
            "author": "Mike Pfaffenberger",
            "date": "2026-06-30",
            "month": "2026-06"
          },
          {
            "hash": "fe1dac55a66601de0b9e8cb7168ba8565fae3b38",
            "short_hash": "fe1dac55",
            "subject": "feat(ui): add thinking_type and glm_reasoning_effort to model settings menu",
            "author": "Mike Pfaffenberger",
            "date": "2026-06-30",
            "month": "2026-06"
          },
          {
            "hash": "a84d87fea9ae4e13c47224b256e3964c330a464c",
            "short_hash": "a84d87fe",
            "subject": "feat(model-factory): route GLM thinking and reasoning_effort through extra_body",
            "author": "Mike Pfaffenberger",
            "date": "2026-06-30",
            "month": "2026-06"
          },
          {
            "hash": "b18913dce78ac465fd0b18f9fa7bfba239244b98",
            "short_hash": "b18913dc",
            "subject": "feat(config): extend model_supports_setting for GLM thinking controls",
            "author": "Mike Pfaffenberger",
            "date": "2026-06-30",
            "month": "2026-06"
          },
          {
            "hash": "20b8bd6b62564ac74b510101f7f29ea34944bf68",
            "short_hash": "20b8bd6b",
            "subject": "feat(model-utils): add GLM version detection and thinking capability helpers",
            "author": "Mike Pfaffenberger",
            "date": "2026-06-30",
            "month": "2026-06"
          },
          {
            "hash": "3608d4394caec50742e61c314e34dc2f11f1f4b5",
            "short_hash": "3608d439",
            "subject": "test(models): add test coverage for claude-sonnet-5 capabilities",
            "author": "Mike Pfaffenberger",
            "date": "2026-06-30",
            "month": "2026-06"
          },
          {
            "hash": "7b1743006d8e321459487fadd3a2a4d4c62e1c45",
            "short_hash": "7b174300",
            "subject": "feat(models): add claude-sonnet-5 support with adaptive thinking and long context",
            "author": "Mike Pfaffenberger",
            "date": "2026-06-30",
            "month": "2026-06"
          },
          {
            "hash": "eb708773ec78a484920a9a0356048ecd144c80f9",
            "short_hash": "eb708773",
            "subject": "chore: bump version [ci skip]",
            "author": "github-actions[bot]",
            "date": "2026-06-30",
            "month": "2026-06"
          },
          {
            "hash": "ad13b99bf5acb778b91ecd0b6c27b595f7263b96",
            "short_hash": "ad13b99b",
            "subject": "fix(puppy_kennel): stop concurrent multiprocess writes from silently dropping (#515)",
            "author": "Aaron Weegens",
            "date": "2026-06-30",
            "month": "2026-06"
          }
        ]
      }
    ],
    "commits": [
      {
        "hash": "853baa9bb68e3ebbc00be0d0d3a5f763154e3ae3",
        "short_hash": "853baa9b",
        "subject": "chore: auto-commit pre-update leftovers (2026-08-18 20:00)",
        "author": "Tyler Granlund",
        "date": "2026-08-18"
      },
      {
        "hash": "58efc338f25f72f74dc06c9e31c23253d5889a75",
        "short_hash": "58efc338",
        "subject": "docs(field-guide+observatory): regenerate + post-update leftovers (2026-08-18 12:01)",
        "author": "Tyler Granlund",
        "date": "2026-08-18"
      },
      {
        "hash": "e33335b875af3fee8bdaa51d3e8e3cf4e7556a36",
        "short_hash": "e33335b8",
        "subject": "feat(a11y): sweep legacy page bodies to WCAG 2.2 AAA body-text contrast",
        "author": "Tyler Granlund",
        "date": "2026-08-18"
      },
      {
        "hash": "3a68d68bb95ca53bb1912834c4648a612cd014f3",
        "short_hash": "3a68d68b",
        "subject": "docs(field-guide+observatory): regenerate + post-update leftovers (2026-08-18 07:02)",
        "author": "Tyler Granlund",
        "date": "2026-08-18"
      },
      {
        "hash": "cc2716ee1683774a797fb3c127a88b9ceed38569",
        "short_hash": "cc2716ee",
        "subject": "docs(field-guide+observatory): regenerate + post-update leftovers (2026-08-17 20:02)",
        "author": "Tyler Granlund",
        "date": "2026-08-17"
      },
      {
        "hash": "53e2126c0ac70f05f41dd27cc4dca9a885e15ddf",
        "short_hash": "53e2126c",
        "subject": "docs: build log + roadmap (what shipped, where, QA status, forward plan)",
        "author": "Tyler Granlund",
        "date": "2026-08-17"
      },
      {
        "hash": "f32d6894a59a9fa51486cb82f2e1353fe4e26f69",
        "short_hash": "f32d6894",
        "subject": "feat(ui): sidebar app-shell + reusable popover + design system, WCAG 2.2 AAA",
        "author": "Tyler Granlund",
        "date": "2026-08-17"
      },
      {
        "hash": "5816642da3d1319cf9f4f2379e90ff54954b71d7",
        "short_hash": "5816642d",
        "subject": "docs(field-guide+observatory): regenerate + post-update leftovers (2026-08-17 17:21)",
        "author": "Tyler Granlund",
        "date": "2026-08-17"
      },
      {
        "hash": "37b06f17ce038955d65f1ccd30820a32d7c788c5",
        "short_hash": "37b06f17",
        "subject": "fix(field-guide): flat-doc JSON corruption + responsive [mobile/tablet] layout",
        "author": "Tyler Granlund",
        "date": "2026-08-17"
      },
      {
        "hash": "ece00b6eb5428d85105df24d9d0789c91128719d",
        "short_hash": "ece00b6e",
        "subject": "feat(brand): lucide icon pass + face-only mark, brand watermarks across site",
        "author": "Tyler Granlund",
        "date": "2026-08-17"
      },
      {
        "hash": "ac57c7ec8d15c627b44fb5cd39a0e7af37ec8d80",
        "short_hash": "ac57c7ec",
        "subject": "feat(arch): wide-screen lane expansion + left-aligned navigation",
        "author": "Tyler Granlund",
        "date": "2026-08-17"
      },
      {
        "hash": "ce70535a65ae573ef8cca8691ad26faa589bdd86",
        "short_hash": "ce70535a",
        "subject": "feat(pages): interactive architecture board - L-R flow, drilldown sheets, live inventory",
        "author": "Tyler Granlund",
        "date": "2026-08-17"
      },
      {
        "hash": "8f5238fa4ebb0c1c747c3f6fabc3c101bd9440d7",
        "short_hash": "8f5238fa",
        "subject": "feat(brand): site-wide rebrand to periwinkle/cyan/mint design system",
        "author": "Tyler Granlund",
        "date": "2026-08-17"
      },
      {
        "hash": "177c04efd632fd0f59b7f2dde145c4d9fdd25530",
        "short_hash": "177c04ef",
        "subject": "docs(field-guide+observatory): regenerate + post-update leftovers (2026-08-17 12:00)",
        "author": "Tyler Granlund",
        "date": "2026-08-17"
      },
      {
        "hash": "bae563eed1870c5156489fc51c96daa52e93f6f6",
        "short_hash": "bae563ee",
        "subject": "feat(pages): architecture diagram page - self-healing pipeline, Apple-internal-training treatment",
        "author": "Tyler Granlund",
        "date": "2026-08-17"
      },
      {
        "hash": "9da5d8fc4144733159cb6994fc730f0f50843aad",
        "short_hash": "9da5d8fc",
        "subject": "docs(field-guide+observatory): regenerate + post-update leftovers (2026-08-17 10:48)",
        "author": "Tyler Granlund",
        "date": "2026-08-17"
      },
      {
        "hash": "8270ab0a32e2e345f54a693373b70ce0e77e5e00",
        "short_hash": "8270ab0a",
        "subject": "docs(sovereignty): profile backup now automated; curation cadence + restore path",
        "author": "Tyler Granlund",
        "date": "2026-08-17"
      },
      {
        "hash": "7140622c93e56c8466f7a32d37d4ef3c47f9cd2e",
        "short_hash": "7140622c",
        "subject": "ci(pages): drop configure-pages (codeload 429 flake) - upload/deploy suffice",
        "author": "Tyler Granlund",
        "date": "2026-08-17"
      },
      {
        "hash": "d16b1a8166d98a3d9263ee7426da6782960e13bd",
        "short_hash": "d16b1a81",
        "subject": "docs(field-guide+observatory): regenerate + post-update leftovers (2026-08-17 10:29)",
        "author": "Tyler Granlund",
        "date": "2026-08-17"
      },
      {
        "hash": "bd03b2b8c0829d50ce2fc87f7bb1e8bfef5e013e",
        "short_hash": "bd03b2b8",
        "subject": "feat(pages): evergreen release observatory auto-regenerated by update pipeline",
        "author": "Tyler Granlund",
        "date": "2026-08-17"
      },
      {
        "hash": "6774d65323b088fe422b1926c37d02a8c99742af",
        "short_hash": "6774d653",
        "subject": "docs(sovereignty): update Pages URL structure for 4-section site",
        "author": "Tyler Granlund",
        "date": "2026-08-17"
      },
      {
        "hash": "b0e528207a71fcae95c5378cd5d6d13647ee4a8a",
        "short_hash": "b0e52820",
        "subject": "docs(pages): public site hub + release observatory for t-granlund fork Pages",
        "author": "Tyler Granlund",
        "date": "2026-08-17"
      },
      {
        "hash": "4c61a450ec1a826b169d2f745cc77571ac9aabca",
        "short_hash": "4c61a450",
        "subject": "docs(field-guide): regenerate + post-update leftovers (2026-08-17 10:01)",
        "author": "Tyler Granlund",
        "date": "2026-08-17"
      },
      {
        "hash": "c3173138fc28451f65483e1d8ea547608e55a29d",
        "short_hash": "c3173138",
        "subject": "docs(field-guide): regenerate + post-update leftovers (2026-08-17 09:59)",
        "author": "Tyler Granlund",
        "date": "2026-08-17"
      },
      {
        "hash": "c1a96a4c99e189d8ba09dd81c034b4f2c89c2b2e",
        "short_hash": "c1a96a4c",
        "subject": "docs(field-guide): regenerate + post-update leftovers (2026-08-17 09:58)",
        "author": "Tyler Granlund",
        "date": "2026-08-17"
      },
      {
        "hash": "83a5e8495ff4f75acc841e3689f0fc83ec20e771",
        "short_hash": "83a5e849",
        "subject": "chore: auto-commit pre-update leftovers (2026-08-17 09:58)",
        "author": "Tyler Granlund",
        "date": "2026-08-17"
      },
      {
        "hash": "631ec40a9383f55c5dcbdb38ddd73b2439e4ba6d",
        "short_hash": "631ec40a",
        "subject": "docs(sovereignty): reflect auto-sync updater + Pages field guide",
        "author": "Tyler Granlund",
        "date": "2026-08-17"
      },
      {
        "hash": "94446e626b265fbecb4416eb2b0f6c90c2a03f7f",
        "short_hash": "94446e62",
        "subject": "docs(field-guide): regenerate + post-update leftovers (2026-08-17 09:31)",
        "author": "Tyler Granlund",
        "date": "2026-08-17"
      },
      {
        "hash": "8240a4a2287db0c1f6ad19f58ac187e9b157510e",
        "short_hash": "8240a4a2",
        "subject": "docs(field-guide): regenerate + post-update leftovers (2026-08-17 09:28)",
        "author": "Tyler Granlund",
        "date": "2026-08-17"
      },
      {
        "hash": "04e54199511ffe95cbf1ad55976640977f0dcdd7",
        "short_hash": "04e54199",
        "subject": "docs(field-guide): regenerate + post-update leftovers (2026-08-17 09:28)",
        "author": "Tyler Granlund",
        "date": "2026-08-17"
      },
      {
        "hash": "dc017cd5949b53c2801ceec14ae498543e184c03",
        "short_hash": "dc017cd5",
        "subject": "ci(pages): deploy field guide to GitHub Pages on docs changes",
        "author": "Tyler Granlund",
        "date": "2026-08-17"
      },
      {
        "hash": "c9e2fe142a7692ce7edd23fbf1227ef2f6a3f558",
        "short_hash": "c9e2fe14",
        "subject": "docs(field-guide): regenerate after upstream sync (2026-08-17)",
        "author": "Tyler Granlund",
        "date": "2026-08-17"
      },
      {
        "hash": "88d452a2211713b036d7168a0d37a9d56afd53f4",
        "short_hash": "88d452a2",
        "subject": "docs: sovereignty playbook, weekly features page, changelog dir",
        "author": "Tyler Granlund",
        "date": "2026-08-17"
      },
      {
        "hash": "0af54a06f07160bee8f1020fde0facbf29261dc5",
        "short_hash": "0af54a06",
        "subject": "docs(field-guide): regenerate with corrected skill labels",
        "author": "Tyler Granlund",
        "date": "2026-08-16"
      },
      {
        "hash": "7497e9a00cc59966614ee7eb23500be1e9742602",
        "short_hash": "7497e9a0",
        "subject": "fix(field-guide): correct skill source labels and sanitize paths",
        "author": "Tyler Granlund",
        "date": "2026-08-16"
      },
      {
        "hash": "657a069656c5e868c689bd18f09ec6fd0e4ca1c6",
        "short_hash": "657a0696",
        "subject": "docs(field-guide): regenerate with user plugins + i_have_adhd; app.js tier badges",
        "author": "Tyler Granlund",
        "date": "2026-08-16"
      },
      {
        "hash": "506cb41aa41f17bcd5a29f571841aaf0b014c856",
        "short_hash": "506cb41a",
        "subject": "docs(field-guide): regenerate after core-plugins package scan support",
        "author": "Tyler Granlund",
        "date": "2026-08-16"
      },
      {
        "hash": "6cf978b3e3d5beacd459f6613a3b2ac6d0d82dc2",
        "short_hash": "6cf978b3",
        "subject": "feat(field-guide): scan installed core-plugins package + user plugins",
        "author": "Tyler Granlund",
        "date": "2026-08-16"
      },
      {
        "hash": "664e151a7c619c3786b848510f61b3b426389d19",
        "short_hash": "664e151a",
        "subject": "docs: CPU interactive curriculum web app + puppy mark",
        "author": "Tyler Granlund",
        "date": "2026-07-31"
      },
      {
        "hash": "755c9c305534e267a3f3b4433a60ed184f3a6ff8",
        "short_hash": "755c9c30",
        "subject": "docs: deck v3 — Acts IX/X, the internal + external university",
        "author": "Tyler Granlund",
        "date": "2026-07-31"
      },
      {
        "hash": "b1f40c11d829a9f4bc12b1663e6fa53e75a41e9e",
        "short_hash": "b1f40c11",
        "subject": "docs: deck v2.1 — token architecture, component registry, 42-test suite",
        "author": "Tyler Granlund",
        "date": "2026-07-30"
      },
      {
        "hash": "4afb9a2b87bc610040e182552a77d7e84ee430c5",
        "short_hash": "4afb9a2b",
        "subject": "docs: deck v2 — Cornerstone+ design system, Fireship beat, fact-check pass",
        "author": "Tyler Granlund",
        "date": "2026-07-30"
      },
      {
        "hash": "a0524d5f2d1498a83eae40589b2e117e4138d0ba",
        "short_hash": "a0524d5f",
        "subject": "docs: The Great Adpuppytion — Code-Puppy University founding deck",
        "author": "Tyler Granlund",
        "date": "2026-07-30"
      },
      {
        "hash": "c0751c238b4ea34912408996001422eb55d5a4cb",
        "short_hash": "c0751c23",
        "subject": "feat(field-guide): recreate changelog.py source from pycache analysis",
        "author": "Tyler Granlund",
        "date": "2026-08-13"
      },
      {
        "hash": "931dfdd10fab1c583189cab29ed40eb7268d0872",
        "short_hash": "931dfdd1",
        "subject": "feat(field-guide): deeper plugin/tool extraction + skills + SDLC lifecycle",
        "author": "Tyler Granlund",
        "date": "2026-08-13"
      },
      {
        "hash": "da3bc38e34c9cb9f7796f4431490318f64f2cbdd",
        "short_hash": "da3bc38e",
        "subject": "fix(field-guide): flat HTML no longer wipes DATA.plugins via JS escape reinterpretation",
        "author": "Tyler Granlund",
        "date": "2026-08-10"
      },
      {
        "hash": "2acf97663da9e00a269fc80d3fa17b2429febe07",
        "short_hash": "2acf9766",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-18"
      },
      {
        "hash": "d1ac8f660367af4003c5ee13a8d5652c444de155",
        "short_hash": "d1ac8f66",
        "subject": "fix(list_files): dedupe raced directory entries against seen_dir_paths (#789)",
        "author": "TJ",
        "date": "2026-08-18"
      },
      {
        "hash": "ff1f4f7777818252849c11cf810842122b141190",
        "short_hash": "ff1f4f77",
        "subject": "feat(i18n): extract custom_server_installer.py user-facing strings (#788)",
        "author": "TJ",
        "date": "2026-08-18"
      },
      {
        "hash": "2c0a65d9a7bb65c9a64256e754b4dd0f64681674",
        "short_hash": "2c0a65d9",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-18"
      },
      {
        "hash": "acdcc8195f6f5e7a96ffef11ebeaf8bdc0f3f540",
        "short_hash": "acdcc819",
        "subject": "Fix interrupted parallel tool-call pruning + assorted robustness fixes (#790)",
        "author": "David SF",
        "date": "2026-08-18"
      },
      {
        "hash": "f481fb3022b29947370111e4f9fcd43dcb28a380",
        "short_hash": "f481fb30",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-18"
      },
      {
        "hash": "38f56376e30df807742f93e90706a83f9bcb9a94",
        "short_hash": "38f56376",
        "subject": "Merge pull request #791 from mpfaffenberger/feat/headless-usage-file",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-18"
      },
      {
        "hash": "065f05bdb7c6aa549cf0bb59f9bd760997c1eb25",
        "short_hash": "065f05bd",
        "subject": "feat: export headless model usage as JSON",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-18"
      },
      {
        "hash": "7846776a37fb132633c259472472bbff43dac2c8",
        "short_hash": "7846776a",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-18"
      },
      {
        "hash": "6402fb67dadb58febbe20a8d34a6e6d6bb663551",
        "short_hash": "6402fb67",
        "subject": "Merge pull request #793 from mpfaffenberger/feat/disable-ask-user-question",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-18"
      },
      {
        "hash": "600d508e0fbd12f849bafa1941c9d866199480d1",
        "short_hash": "600d508e",
        "subject": "chore(callbacks): type the fail-closed policy set precisely (#794)",
        "author": "Xi Chen",
        "date": "2026-08-18"
      },
      {
        "hash": "550fdc39bde868dc42d34eab3d5b732d147b3413",
        "short_hash": "550fdc39",
        "subject": "feat: allow disabling ask-user tool",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-18"
      },
      {
        "hash": "392cdc4e25172d47a22d5322b177731efecbc3f9",
        "short_hash": "392cdc4e",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-18"
      },
      {
        "hash": "5fb9efbbead62fe15ffd43c0695288a254f1fdd9",
        "short_hash": "5fb9efbb",
        "subject": "web-retriever: ask before persisting extracted data to a file (#792)",
        "author": "TJ",
        "date": "2026-08-18"
      },
      {
        "hash": "173c904401701fb20b8d8c8d42e3fd4a284d6411",
        "short_hash": "173c9044",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-18"
      },
      {
        "hash": "e5771ab8ce45161e70e872a8dc7fadf3ccb6de05",
        "short_hash": "e5771ab8",
        "subject": "feat(i18n): extract add_model_menu.py user-facing strings (#706)",
        "author": "TJ",
        "date": "2026-08-18"
      },
      {
        "hash": "7c7517553a078c92148690dc135501e884abd920",
        "short_hash": "7c751755",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-18"
      },
      {
        "hash": "cf0ff04cce17437ec8b325fc9fbd8946886ff25b",
        "short_hash": "cf0ff04c",
        "subject": "fix(callbacks): a security callback that crashes must not read as approval (#777)",
        "author": "Xi Chen",
        "date": "2026-08-18"
      },
      {
        "hash": "cc549cdcab195dfedaf58afc77a96af6c3e3def0",
        "short_hash": "cc549cdc",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-18"
      },
      {
        "hash": "7964008ab1ec50f676124347c272e8f48815de40",
        "short_hash": "7964008a",
        "subject": "Merge pull request #703 from breedx/upstream/model-settings-repaint",
        "author": "TJ",
        "date": "2026-08-18"
      },
      {
        "hash": "f2c8fcdafbd904980589106b0824268488c66f3c",
        "short_hash": "f2c8fcda",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-17"
      },
      {
        "hash": "7b82a2eb3ceb967f98b487833fc7e28c168cd77d",
        "short_hash": "7b82a2eb",
        "subject": "Merge pull request #785 from dsfaccini/fix/compaction-summarization",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-17"
      },
      {
        "hash": "2b4732da221aa1c754423a71a07ab369207ece07",
        "short_hash": "2b4732da",
        "subject": "Merge pull request #774 from thomwebb/feat/agent-execution-context",
        "author": "TJ",
        "date": "2026-08-17"
      },
      {
        "hash": "041935c1c601c12e0569b69abfd5f89da157ffc9",
        "short_hash": "041935c1",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-17"
      },
      {
        "hash": "f054deef49a1073a9e68b941542f270dbbb89a38",
        "short_hash": "f054deef",
        "subject": "Merge pull request #787 from sudhanshushekhar10/fix/list-files-quadratic-dedup",
        "author": "TJ",
        "date": "2026-08-17"
      },
      {
        "hash": "c55d9fe915678f463550078b05a66bd058a16247",
        "short_hash": "c55d9fe9",
        "subject": "fix: scope executing agent across the full run lifecycle",
        "author": "TJ",
        "date": "2026-08-17"
      },
      {
        "hash": "381bf602607bb3bf62cbe11d173fcf9ffac1ec67",
        "short_hash": "381bf602",
        "subject": "fix(list_files): replace O(n^2) parent-directory dedup with a set",
        "author": "sudhanshushekhar10",
        "date": "2026-08-18"
      },
      {
        "hash": "e136fb888259704155ed36243e27eb344962e24e",
        "short_hash": "e136fb88",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-17"
      },
      {
        "hash": "27e5747244084192ed9dae87f5cb11fd593cbf44",
        "short_hash": "27e57472",
        "subject": "Merge pull request #773 from thomwebb/fix/test-robustness",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-17"
      },
      {
        "hash": "0246ca583da5b4f5c61796f315a6263ee646b705",
        "short_hash": "0246ca58",
        "subject": "Merge pull request #778 from weegens-aaron/fix/agents-md-utf16-bom",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-17"
      },
      {
        "hash": "15bcad9ee4126ed3226c7a581f9d68632138c31d",
        "short_hash": "15bcad9e",
        "subject": "Apply ruff format to new test files",
        "author": "David Sanchez",
        "date": "2026-08-17"
      },
      {
        "hash": "b8a0006668d8dee2bc4cf412b2fe6dbdd63a581e",
        "short_hash": "b8a00066",
        "subject": "Fix summarization-compaction reliability + assorted robustness fixes",
        "author": "David Sanchez",
        "date": "2026-08-17"
      },
      {
        "hash": "cbb7d30c49de84e707f435e641f5df0f54501cf3",
        "short_hash": "cbb7d30c",
        "subject": "Fix UTF-16 AGENTS.md crash on Windows",
        "author": "weegens-aaron",
        "date": "2026-08-17"
      },
      {
        "hash": "2955602be29fd5beb4659bfc5be7cc0b07262903",
        "short_hash": "2955602b",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-17"
      },
      {
        "hash": "69905961fd547fa36fae190e600f1dfa65ee83ed",
        "short_hash": "69905961",
        "subject": "Route Anthropic Opus 5 to adaptive thinking",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-17"
      },
      {
        "hash": "5d63220df925f03b7245c66587cc31a861780bac",
        "short_hash": "5d63220d",
        "subject": "feat: expose per-agent execution context",
        "author": "TJ",
        "date": "2026-08-15"
      },
      {
        "hash": "c1ef485eaa12255c88e865e9507e94781464aee2",
        "short_hash": "c1ef485e",
        "subject": "test: robust port occupancy check and DBOS optional skip",
        "author": "TJ",
        "date": "2026-08-16"
      },
      {
        "hash": "00cda83a4e8d33491686ae5230391dca7b851e44",
        "short_hash": "00cda83a",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-16"
      },
      {
        "hash": "6df55ed9fa1b305d7d7e09500eb0381cc68f918b",
        "short_hash": "6df55ed9",
        "subject": "Merge pull request #769 from thomwebb/feat/show-core-plugins-version",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-16"
      },
      {
        "hash": "9dbe667043e9592e899d8b7256b09aafba6dffb4",
        "short_hash": "9dbe6670",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-16"
      },
      {
        "hash": "96c86d182536b05259b1e63566771729e9524315",
        "short_hash": "96c86d18",
        "subject": "Merge pull request #771 from thomwebb/fix/add-model-suggest",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-16"
      },
      {
        "hash": "3785a9709493a331024f0dac84fdc88c5b1f40ee",
        "short_hash": "3785a970",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-16"
      },
      {
        "hash": "b5dc6bb9485e61c1243c3f3a1ff68bac4ccd04fd",
        "short_hash": "b5dc6bb9",
        "subject": "fix: /model suggestions now reflect models added via /add_model",
        "author": "TJ",
        "date": "2026-08-16"
      },
      {
        "hash": "47d5490c709d1c712f8af6275b2427b2fddc80ad",
        "short_hash": "47d5490c",
        "subject": "style: sort imports in model_picker_completion.py",
        "author": "TJ",
        "date": "2026-08-16"
      },
      {
        "hash": "827f8a1ee93247af492dba54fb1890cdebfb8cb5",
        "short_hash": "827f8a1e",
        "subject": "Merge pull request #768 from mpfaffenberger/fix/subagent-token-cache-metrics",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-16"
      },
      {
        "hash": "5e5b7fee7109532569d90e8b16e69d8cdcef5df3",
        "short_hash": "5e5b7fee",
        "subject": "test: remove Model Judge prompt content assertions",
        "author": "Pack Leader",
        "date": "2026-08-16"
      },
      {
        "hash": "a5261fa5fa7a9b058bccca1b124d44270b7dcab5",
        "short_hash": "a5261fa5",
        "subject": "docs: trim verbose comments and test prose",
        "author": "Pack Leader",
        "date": "2026-08-16"
      },
      {
        "hash": "e57b58088d951b0400e4424874bd523c2aabf46a",
        "short_hash": "e57b5808",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-16"
      },
      {
        "hash": "e53537f9fb9efe500340a21b16a1de0450db847c",
        "short_hash": "e53537f9",
        "subject": "Merge pull request #770 from mpfaffenberger/awtilso/PUP-634",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-16"
      },
      {
        "hash": "30c15b44b637f723f7af901d1dc9d34c499b5828",
        "short_hash": "30c15b44",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-16"
      },
      {
        "hash": "81595ab1fcc87bdc3f1f838c2ddc991c5532c7ae",
        "short_hash": "81595ab1",
        "subject": "Normalize None-ish cwd strings in run_shell_command",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-16"
      },
      {
        "hash": "bf503e54cf9bf583b1c7a716845a3fa31e7eb318",
        "short_hash": "bf503e54",
        "subject": "Recover live compaction integration tests; bump CI models to GLM-5.2 + Kimi K2.6",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-16"
      },
      {
        "hash": "57de5091ef1c8b32c454eca063a566ba990097de",
        "short_hash": "57de5091",
        "subject": "chore: trim comments to minimal required context",
        "author": "Andrew Tilson - awtilso",
        "date": "2026-08-16"
      },
      {
        "hash": "87e23b65e38aa7410ec31080183ef579e00bf3f1",
        "short_hash": "87e23b65",
        "subject": "test: pin the cache-folding premise to real v2 adapters",
        "author": "Andrew Tilson - awtilso",
        "date": "2026-08-16"
      },
      {
        "hash": "b26c21273741906bfa2200f78e4b4982adec63f2",
        "short_hash": "b26c2127",
        "subject": "fix: classify bare JSONDecodeError as retryable in streaming path",
        "author": "Andrew Tilson - awtilso",
        "date": "2026-08-16"
      },
      {
        "hash": "0b1cb6eb79177295a6500dd70e44a35669fa1ab9",
        "short_hash": "0b1cb6eb",
        "subject": "test: model result.usage as a property, not a callable",
        "author": "Andrew Tilson - awtilso",
        "date": "2026-08-16"
      },
      {
        "hash": "1fd3b51d2067e09375a739fad9579258397d3622",
        "short_hash": "1fd3b51d",
        "subject": "Merge origin/main into fix/subagent-token-cache-metrics",
        "author": "Andrew Tilson - awtilso",
        "date": "2026-08-16"
      },
      {
        "hash": "df5abd4970ac4406a564494f135e51cbae6e39bc",
        "short_hash": "df5abd49",
        "subject": "Merge origin/main into feat/show-core-plugins-version",
        "author": "TJ",
        "date": "2026-08-16"
      },
      {
        "hash": "026fd30ff8df3e8e1f66cb2dec02bac7f080c6ce",
        "short_hash": "026fd30f",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-16"
      },
      {
        "hash": "bf6b044afedac66c6d99e14a055c8a09f9076bcf",
        "short_hash": "bf6b044a",
        "subject": "Silence unsupported-sampling-parameter warnings for Anthropic models",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-16"
      },
      {
        "hash": "c987c321b42737fcd03a0be6eae76fe33c64ea4d",
        "short_hash": "c987c321",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-16"
      },
      {
        "hash": "d94db5c9b8317cb0547eda053b7edfede74cea50",
        "short_hash": "d94db5c9",
        "subject": "Delete pre-0.0.7 plugin compat shims",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-16"
      },
      {
        "hash": "79315b4ea6156919df58926b221425dcc5e0782e",
        "short_hash": "79315b4e",
        "subject": "Depend on code-puppy-core-plugins>=0.0.8 from PyPI",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-16"
      },
      {
        "hash": "165908188776cd9d4b47be3db8696684b74e0c76",
        "short_hash": "16590818",
        "subject": "Make session format sweep self-healing + de-spam failure logging",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-16"
      },
      {
        "hash": "ddd12370339ac8430e12f84dafc28783149d8cef",
        "short_hash": "ddd12370",
        "subject": "Fix surrogate unpickler failure on tz-aware datetimes",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-16"
      },
      {
        "hash": "326ea5ab8edd2fbfdc2f5b5a10cd657f6ece768a",
        "short_hash": "326ea5ab",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-16"
      },
      {
        "hash": "4dc62bcd030f3799374682ec38b0c790101a0a5b",
        "short_hash": "4dc62bcd",
        "subject": "Point plugins dependency at git source pending 0.0.7 PyPI release",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-16"
      },
      {
        "hash": "c2fcc6aed5e4eb2beb860094f3361605d0aeb707",
        "short_hash": "c2fcc6ae",
        "subject": "fix: correct two false claims found in review",
        "author": "Andrew Tilson - awtilso",
        "date": "2026-08-16"
      },
      {
        "hash": "9275a3f79eaeb9bf7872baa5f00d2f73e5a29127",
        "short_hash": "9275a3f7",
        "subject": "docs: tighten the comments",
        "author": "Andrew Tilson - awtilso",
        "date": "2026-08-16"
      },
      {
        "hash": "e704980cf9d2908df687cbef81a5e0960e199bc8",
        "short_hash": "e704980c",
        "subject": "fix: harden core plugins version reporting",
        "author": "TJ",
        "date": "2026-08-15"
      },
      {
        "hash": "440f404f1bc412e139c2ad071b0453ccdea23234",
        "short_hash": "440f404f",
        "subject": "Fix emoji_filter tests for stream-event-seam implementation",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-16"
      },
      {
        "hash": "c00b1ef719ff654792753b3a211de589714899ee",
        "short_hash": "c00b1ef7",
        "subject": "Post-migration cleanup: remove dead code, archive migration docs",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-16"
      },
      {
        "hash": "1f9c6c7ce1fbb5b22542aadd942f97e1f052c60e",
        "short_hash": "1f9c6c7c",
        "subject": "v2 sweep: pin MCP prefer_tasks=False, document part-kind and settings audits",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-16"
      },
      {
        "hash": "2e86344823c7edb725c05a9a02031a6e871ad204",
        "short_hash": "2e863448",
        "subject": "Align custom models with the pydantic-ai v2 Model ABC",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-16"
      },
      {
        "hash": "a5c710fbc7c2b921aff83f3ba0c064037df2e92f",
        "short_hash": "a5c710fb",
        "subject": "Adopt v2 cancellation semantics; delete cancel-scope suppression (gate passed)",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-16"
      },
      {
        "hash": "d280303c63a4038eadef45bec487205f5b1d452f",
        "short_hash": "d280303c",
        "subject": "Bump pydantic-ai to 2.31.0 (hop 2 of v2 migration) + mechanical fixes",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-16"
      },
      {
        "hash": "c1f8c05f06c8797dfd8f6a343910936c468ca5b6",
        "short_hash": "c1f8c05f",
        "subject": "Wire in code-puppy-core-plugins 0.0.6 from sibling checkout",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-15"
      },
      {
        "hash": "0dd7f79d8e2ed0c685bbfc59bff7a9fe519948f2",
        "short_hash": "0dd7f79d",
        "subject": "feat: show core plugins version at startup",
        "author": "TJ",
        "date": "2026-08-15"
      },
      {
        "hash": "56591821f940b3d5be28ffee557a62ce020fce76",
        "short_hash": "56591821",
        "subject": "Rebuild MCP toolset consumers on public wrapper APIs",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-15"
      },
      {
        "hash": "da9bd91af77ae6ac6441870fb4b260623d1ffca5",
        "short_hash": "da9bd91a",
        "subject": "refactor: trim the prose and the duplicate tests",
        "author": "Andrew Tilson - awtilso",
        "date": "2026-08-15"
      },
      {
        "hash": "8732872fe3f6b8c0c7b17980e31c2fed916e1f6a",
        "short_hash": "8732872f",
        "subject": "Migrate mcp_ subsystem off deprecated MCPServer* onto MCPToolset",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-15"
      },
      {
        "hash": "9bf42afe689b0ca95d086cbc2f0444f35e472616",
        "short_hash": "9bf42afe",
        "subject": "Bump pydantic-ai to 1.107.5 (hop 1 of v2 migration)",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-15"
      },
      {
        "hash": "a3ff3360a8821b99b564ea814868c20b6548bb6d",
        "short_hash": "a3ff3360",
        "subject": "fix: stop the judge inventing OpenAI cache-write costs",
        "author": "Andrew Tilson - awtilso",
        "date": "2026-08-15"
      },
      {
        "hash": "de52fccadd2ba74e5619fa8b9b3cd8ac5cb3fbfe",
        "short_hash": "de52fcca",
        "subject": "feat: add the Model Judge agent",
        "author": "Andrew Tilson - awtilso",
        "date": "2026-08-15"
      },
      {
        "hash": "5e7b8d7f1fcb68bba49fe2209d7fd14d38b90907",
        "short_hash": "5e7b8d7f",
        "subject": "fix: address review feedback on subagent usage reporting",
        "author": "Andrew Tilson - awtilso",
        "date": "2026-08-15"
      },
      {
        "hash": "1167a54d6837792ab7e3d006bef47b606484f850",
        "short_hash": "1167a54d",
        "subject": "Use stable content-based sha256 digests for message dedup hashing",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-15"
      },
      {
        "hash": "661ba1083c393a36fa5a971f1e571345a86ab20d",
        "short_hash": "661ba108",
        "subject": "Make pydantic-ai monkey patches fail loudly instead of silently",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-15"
      },
      {
        "hash": "61d6766d41e7ab7bf23b43a74e3c5e8f3d10c0e4",
        "short_hash": "61d6766d",
        "subject": "Migrate Anthropic prompt caching to native pydantic-ai settings; slim claude_cache_client to OAuth core",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-15"
      },
      {
        "hash": "30edbc89e6a033043f17e3c08020bf279a069de0",
        "short_hash": "30edbc89",
        "subject": "feat(sessions): migrate persistence from pickle to versioned JSON envelopes",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-15"
      },
      {
        "hash": "f908d742a7f6beb7758566c8e0b9d91d4fa80297",
        "short_hash": "f908d742",
        "subject": "fix: keep usage metrics provider reported",
        "author": "Pack Leader",
        "date": "2026-08-15"
      },
      {
        "hash": "d00ac86b9d3ebce485b7399a66d281c8576d7267",
        "short_hash": "d00ac86b",
        "subject": "fix: report subagent token usage reliably",
        "author": "Pack Leader",
        "date": "2026-08-15"
      },
      {
        "hash": "757db1cf33138dcf34ea58a7888f4a16f4f4ca1c",
        "short_hash": "757db1cf",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-15"
      },
      {
        "hash": "9c21fbf12bf1f24006f29ac7f8ca7a8f309e1ecc",
        "short_hash": "9c21fbf1",
        "subject": "Merge pull request #766 from thomwebb/fix/pup-622-startup-catalog-noise",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-14"
      },
      {
        "hash": "5ca6557933c0c86bbe415509c2a7cf4a54539408",
        "short_hash": "5ca65579",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-15"
      },
      {
        "hash": "f1e48ff90294b4e4d4369584104e907b409f1dc0",
        "short_hash": "f1e48ff9",
        "subject": "refactor: remove web retriever prompt guidance",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-14"
      },
      {
        "hash": "6377759c00fc0b2745fd322642304f3da4c5ce2a",
        "short_hash": "6377759c",
        "subject": "fix: quiet optional skill catalog startup",
        "author": "TJ Webb",
        "date": "2026-08-14"
      },
      {
        "hash": "1505636ca7e4e1156cb976d8b9ef85a776c0f8b3",
        "short_hash": "1505636c",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-14"
      },
      {
        "hash": "9ff9698e04e5b420c17c1e8dc6114601d1455d68",
        "short_hash": "9ff9698e",
        "subject": "Merge pull request #765 from mpfaffenberger/fix/759-rich-theme-hex",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-14"
      },
      {
        "hash": "1b4fe2b25cff3b1f350ebca1ac509a1f64275e92",
        "short_hash": "1b4fe2b2",
        "subject": "ci: remove migrated computer-use job",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-14"
      },
      {
        "hash": "b83383910ef24d6de2696f4a7e0942542d694462",
        "short_hash": "b8338391",
        "subject": "fix: normalize themed Rich hex colors",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-14"
      },
      {
        "hash": "5be21b6de86612deb71610320c1fd4e6b8885fe7",
        "short_hash": "5be21b6d",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-14"
      },
      {
        "hash": "f2427a6474d439bb8ea41769bd74d9170ef58e37",
        "short_hash": "f2427a64",
        "subject": "build: depend on published core plugin bundle",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-14"
      },
      {
        "hash": "27efe8f57dc5c76bbb5a7cb8d10ded98c70dea18",
        "short_hash": "27efe8f5",
        "subject": "refactor: move builtin plugin implementations to companion package",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-14"
      },
      {
        "hash": "23ee333d97b7b46ebc9ebe3607156b23606ff965",
        "short_hash": "23ee333d",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-14"
      },
      {
        "hash": "7f5ba17d23cc8c7d24d900f2e05e066fa77e3352",
        "short_hash": "7f5ba17d",
        "subject": "feat: discover installed plugins through entry points",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-14"
      },
      {
        "hash": "15640d9856c10c40a7e196ecd9842b3280f18551",
        "short_hash": "15640d98",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-14"
      },
      {
        "hash": "28089370a4328677f22f9326ccdc8f4079257703",
        "short_hash": "28089370",
        "subject": "feat: make puppy kennel memory opt-in",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-14"
      },
      {
        "hash": "94529bcb4de2c253ece61568fc6bce5d4edbbcf9",
        "short_hash": "94529bcb",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-13"
      },
      {
        "hash": "7867e743e45ffede29b8b2c1916be94912ff95a4",
        "short_hash": "7867e743",
        "subject": "Merge pull request #763 from mpfaffenberger/awtilso/PUP-618",
        "author": "Andrew Tilson",
        "date": "2026-08-13"
      },
      {
        "hash": "fc6f4c16f906b98daabd8f7bb978e16117557e81",
        "short_hash": "fc6f4c16",
        "subject": "fix(subagent-panel): display selected model identifier verbatim",
        "author": "Andrew Tilson - awtilso",
        "date": "2026-08-13"
      },
      {
        "hash": "4b7b18d2b722dcb4db30ac9292000ccfed8efaa7",
        "short_hash": "4b7b18d2",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-13"
      },
      {
        "hash": "12cfdb61b31e97da80fe2569728eb2457be8c7ce",
        "short_hash": "12cfdb61",
        "subject": "refactor: fully decouple wiggum from core",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-13"
      },
      {
        "hash": "399effcfd5a49bc25652086c8b17e8ee2179fef3",
        "short_hash": "399effcf",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-13"
      },
      {
        "hash": "5e12bba856e34b1d67b2413503408c7f792230ce",
        "short_hash": "5e12bba8",
        "subject": "refactor: fully decouple puppy_kennel from core",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-13"
      },
      {
        "hash": "0f433152e8385346d3cf868638ec2ac52b8ff759",
        "short_hash": "0f433152",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-13"
      },
      {
        "hash": "0bcb44c7944e38afad4c247956dc3ad5aa437f48",
        "short_hash": "0bcb44c7",
        "subject": "chore: remove dead gemini_oauth leftovers",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-13"
      },
      {
        "hash": "7420153cbd7595facc27def42a6f909194a831b1",
        "short_hash": "7420153c",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-12"
      },
      {
        "hash": "1d73ee0383296d933844dda3551bad8d53bf13a0",
        "short_hash": "1d73ee03",
        "subject": "Merge pull request #761 from thomwebb/fix/atomic-json-config-io",
        "author": "TJ",
        "date": "2026-08-12"
      },
      {
        "hash": "f4bc5ea354fc456ab572b4a45dd16e15f0a3378e",
        "short_hash": "f4bc5ea3",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-12"
      },
      {
        "hash": "eb538f7b4dca121a4312c804b3d5304969e4b3b5",
        "short_hash": "eb538f7b",
        "subject": "Trim verbose comments across the codebase",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-12"
      },
      {
        "hash": "744c22faa1f63bd9d29b1dc60901b73a83f65ef9",
        "short_hash": "744c22fa",
        "subject": "fix: close lost-update race in aws_bedrock/azure_foundry extra_models.json writers",
        "author": "TJ Webb",
        "date": "2026-08-12"
      },
      {
        "hash": "7bb8619501330649b8f6cd8b391bc7d4970cd4c3",
        "short_hash": "7bb86195",
        "subject": "fix: extend atomic, bounded, locked config I/O to JSON config surfaces",
        "author": "TJ Webb",
        "date": "2026-08-12"
      },
      {
        "hash": "c7b20cea58fa6aa46552bbf8ba98a4400e6358d8",
        "short_hash": "c7b20cea",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-12"
      },
      {
        "hash": "bfbac3b9544cdcc077f0c421982552fff9796804",
        "short_hash": "bfbac3b9",
        "subject": "Merge pull request #757 from thomwebb/fix/config-corruption-resilience",
        "author": "TJ",
        "date": "2026-08-12"
      },
      {
        "hash": "742e6ba67e368cad00e3ef2a31f5bbdcdd2e01eb",
        "short_hash": "742e6ba6",
        "subject": "fix: recover from corrupted config files",
        "author": "TJ Webb",
        "date": "2026-08-11"
      },
      {
        "hash": "8faf118c4033b5eab9e061ac6d41e02c6d4f78fd",
        "short_hash": "8faf118c",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-11"
      },
      {
        "hash": "aeeab3fad424d3e5a26b5829abf0e97454d5aafc",
        "short_hash": "aeeab3fa",
        "subject": "Merge pull request #754 from StarsExpress/refactor-dead-mcp-functions",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-11"
      },
      {
        "hash": "ea6b8ddf64287170c4861b91ab3e72414ece3b9a",
        "short_hash": "ea6b8ddf",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-11"
      },
      {
        "hash": "522f9fe491545970edd14eccc9fcbd8f3b043a2e",
        "short_hash": "522f9fe4",
        "subject": "Merge pull request #755 from thomwebb/fix/subagent-model-fallback-pup-585",
        "author": "TJ",
        "date": "2026-08-11"
      },
      {
        "hash": "077f41702c93dbba2e2e9bfad81e9acaf5d2d8eb",
        "short_hash": "077f4170",
        "subject": "style: apply ruff format to 3 files carried in from the upstream sync",
        "author": "TJ Webb",
        "date": "2026-08-11"
      },
      {
        "hash": "7c97e7b3018c9a7aa6e0c07d1dbe70b500f60385",
        "short_hash": "7c97e7b3",
        "subject": "Merge remote-tracking branch 'upstream/main' into fix/subagent-model-fallback-pup-585",
        "author": "TJ Webb",
        "date": "2026-08-11"
      },
      {
        "hash": "52efd4020bcdacd1bf0c63bc3c6a1574bc261178",
        "short_hash": "52efd402",
        "subject": "fix: close a narrow session-close/in-flight-run race + doc drift (round 4)",
        "author": "TJ Webb",
        "date": "2026-08-11"
      },
      {
        "hash": "e7c81c5eb446929e8d095c11089535af86738b68",
        "short_hash": "e7c81c5e",
        "subject": "fix: replace shared-global conversation scope with a real ContextVar",
        "author": "TJ Webb",
        "date": "2026-08-11"
      },
      {
        "hash": "b4ad491f9f84ff6d823ed92355eb4b252691f057",
        "short_hash": "b4ad491f",
        "subject": "fix: scope the dead-model warning dedup by conversation, not by process",
        "author": "TJ Webb",
        "date": "2026-08-11"
      },
      {
        "hash": "642f9d65ebd432e3f4c2e3d0bdf311f31db3f1f6",
        "short_hash": "642f9d65",
        "subject": "fix: address adversarial review findings on the model-fallback dedup",
        "author": "TJ Webb",
        "date": "2026-08-11"
      },
      {
        "hash": "12c5c3c1ece0110ae485396b772eefee5fb4a1be",
        "short_hash": "12c5c3c1",
        "subject": "fix: sub-agent invocation falls back instead of hard-failing on a dead pinned model",
        "author": "TJ Webb",
        "date": "2026-08-11"
      },
      {
        "hash": "77afe8ba5378005169e5c9267a021c04de4a6511",
        "short_hash": "77afe8ba",
        "subject": "Reformatted 3 files by ruff.",
        "author": "Jack Yao",
        "date": "2026-08-11"
      },
      {
        "hash": "f3f3ba8b442d69f8cea8203828e5619f8d150927",
        "short_hash": "f3f3ba8b",
        "subject": "Removed dead functions.",
        "author": "Jack Yao",
        "date": "2026-08-11"
      },
      {
        "hash": "dacbc2459c87ebc268d71a6e11e3c06e84f52230",
        "short_hash": "dacbc245",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-11"
      },
      {
        "hash": "5d1451aa34161402c397149358145b6d48a6ec6b",
        "short_hash": "5d1451aa",
        "subject": "Merge pull request #714 from thomwebb/feat/code-puppy-agent-skill-split",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-11"
      },
      {
        "hash": "a5de8d06189f5db3f4f7f40cc9016ac0acecf48d",
        "short_hash": "a5de8d06",
        "subject": "Merge pull request #753 from 3weakley/fix/additive-skill-directories",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-11"
      },
      {
        "hash": "fffe9b7ff1386c57061b98949962342fa2c2211f",
        "short_hash": "fffe9b7f",
        "subject": "Preserve default skill directories in enabled skill discovery",
        "author": "Eddie Weakley",
        "date": "2026-08-11"
      },
      {
        "hash": "3f01b1fe481211f0ceaf05e98775cb05c9011dea",
        "short_hash": "3f01b1fe",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-11"
      },
      {
        "hash": "bfcf43f532b8a7a6284d8442ed54c8ee8333324b",
        "short_hash": "bfcf43f5",
        "subject": "Merge pull request #749 from thomwebb/feat/codex-imagegen-auth-gate-and-tags",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-11"
      },
      {
        "hash": "33cd907117782930029dc28248e5a35e900de123",
        "short_hash": "33cd9071",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-11"
      },
      {
        "hash": "69c6e2b42e09797629347e687643845678d6db34",
        "short_hash": "69c6e2b4",
        "subject": "Merge pull request #745 from hyper-n0va/fix/ollama-custom-endpoint-timeout",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-11"
      },
      {
        "hash": "13516164e8a049a7a1c8453d746be3b3f7d2248c",
        "short_hash": "13516164",
        "subject": "Merge pull request #695 from weegens-aaron/herdr-windows",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-11"
      },
      {
        "hash": "db956550d3cf24d9f5c01d589dfbe41a0319b71e",
        "short_hash": "db956550",
        "subject": "Merge pull request #711 from StarsExpress/refactor-remove-get_file_icon",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-11"
      },
      {
        "hash": "586b6df2d7be7433b2dadc1fce94908930bcf941",
        "short_hash": "586b6df2",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-11"
      },
      {
        "hash": "560dc3f3040385f33671bb2dfec8fceeac2f6253",
        "short_hash": "560dc3f3",
        "subject": "Merge pull request #751 from Jiaq1Zhu/main",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-10"
      },
      {
        "hash": "cae10e94cfd7191d93225788ad555eedd764479f",
        "short_hash": "cae10e94",
        "subject": "fix(agents): validate agent JSON configuration before saving",
        "author": "Jiaqi Zhu",
        "date": "2026-08-10"
      },
      {
        "hash": "0657181be7194581d4025cf4ad2519f0ba478e5a",
        "short_hash": "0657181b",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-11"
      },
      {
        "hash": "f79b29c8ed7eee37896d26a057ad76f334867623",
        "short_hash": "f79b29c8",
        "subject": "Merge pull request #748 from avargaskun/resume-renders-history",
        "author": "TJ",
        "date": "2026-08-10"
      },
      {
        "hash": "ad656f1329a9c49e94eb9e8ab108dbe2dccb2ebb",
        "short_hash": "ad656f13",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-10"
      },
      {
        "hash": "27d7811edde91e1ab87865123db4ed433145394f",
        "short_hash": "27d7811e",
        "subject": "test: allow builtin skills catalog network traffic",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-10"
      },
      {
        "hash": "e35266679b147f11b07de97aa878ff8998d9db74",
        "short_hash": "e3526667",
        "subject": "Merge PR #739: decouple universal constructor plugin",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-10"
      },
      {
        "hash": "8fb514b950aedb4436817671b84535260168b711",
        "short_hash": "8fb514b9",
        "subject": "Merge PR #738: decouple Claude Code OAuth plugin",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-10"
      },
      {
        "hash": "1b75a4b83113922de67e182bdf1a335c08100085",
        "short_hash": "1b75a4b8",
        "subject": "Merge PR #744: decouple DBOS durable exec plugin",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-10"
      },
      {
        "hash": "21244bbcffabb3743ab37eb2286cd04557312dfc",
        "short_hash": "21244bbc",
        "subject": "fix: make UC provider lifecycle ownership-aware (#726)",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "c1956942abbbf3c91379e49910d3beb581643869",
        "short_hash": "c1956942",
        "subject": "refactor: add universal constructor provider seam (#726)",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "231d1f498d2e8bee081d34a955938d17666653d0",
        "short_hash": "231d1f49",
        "subject": "refactor: decouple universal constructor plugin (#726)",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "a2bb91e1dcb29ebbc0ebc6fa21e97288aee35053",
        "short_hash": "a2bb91e1",
        "subject": "fix: await claude oauth providers in async client (#727)",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "45494b93508aa0a59ec0aa1ab4b542093212a2f8",
        "short_hash": "45494b93",
        "subject": "test: harden claude oauth callback seams (#727)",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "6bb9d8729568e1f90424b63675557aeda7d4147b",
        "short_hash": "6bb9d872",
        "subject": "refactor: decouple claude oauth plugin (#727)",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "fda38b937abc6e40ff3e49f28af79ce1843af97c",
        "short_hash": "fda38b93",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-10"
      },
      {
        "hash": "dc15b46daa2ce103a1e974b11f450a6b4cbaa086",
        "short_hash": "dc15b46d",
        "subject": "Decouple DBOS state from set menu catalog",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "9b66efea20b992507e3b893a30a768c1a11acd22",
        "short_hash": "9b66efea",
        "subject": "Merge PR #737: decouple file permission handler plugin",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-10"
      },
      {
        "hash": "cbc88d37f892e614f805df287f43d481b5cce522",
        "short_hash": "cbc88d37",
        "subject": "Merge PR #736: decouple agent skills plugin",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-10"
      },
      {
        "hash": "6edfcdad66eed80e3aef844066b3e99cfd7efc07",
        "short_hash": "6edfcdad",
        "subject": "Merge PR #742: decouple Ollama setup plugin",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-10"
      },
      {
        "hash": "ee4b15b0e03963457900665c5e6b1c7a3f27229c",
        "short_hash": "ee4b15b0",
        "subject": "Merge PR #741: decouple statusline plugin",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-10"
      },
      {
        "hash": "f893c6ddc1b8ef70db57b17642e49e07f1bd9f2a",
        "short_hash": "f893c6dd",
        "subject": "Merge PR #735: decouple ChatGPT OAuth plugin",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-10"
      },
      {
        "hash": "6d86283216785c7cddbc31905237f0317ebd8a0f",
        "short_hash": "6d862832",
        "subject": "Merge PR #743: decouple customizable commands",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-10"
      },
      {
        "hash": "53037eb17c55fd3fae3f61cdbdee5099941c9f15",
        "short_hash": "53037eb1",
        "subject": "Merge PR #740: decouple theme plugin",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-10"
      },
      {
        "hash": "f9c2d851bd2f1f8aaab60e38f554e9b6fae26468",
        "short_hash": "f9c2d851",
        "subject": "Gate codex-imagegen skill on Codex OAuth, add namespace tags",
        "author": "TJ Webb",
        "date": "2026-08-10"
      },
      {
        "hash": "90afe19a044aff50df4f23031a1c75211b72882f",
        "short_hash": "90afe19a",
        "subject": "Re-render recent history on interactive `-r` resume",
        "author": "avargaskun",
        "date": "2026-08-05"
      },
      {
        "hash": "dbd8d1ffe19b831601db97886c0ed001ec2694ca",
        "short_hash": "dbd8d1ff",
        "subject": "fix: support Ollama custom endpoint config",
        "author": "hyper-n0va",
        "date": "2026-08-09"
      },
      {
        "hash": "3a1ba1b66c019c3dad6e678ee75c5734eb3e2b20",
        "short_hash": "3a1ba1b6",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-10"
      },
      {
        "hash": "9d640e9a72938300f963804d228a0a04a903c607",
        "short_hash": "9d640e9a",
        "subject": "fix: consume agent skills through provider seam (#724)",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "c87dfbbbaf4456d136d6b7e8ef6ccbf9e439b12e",
        "short_hash": "c87dfbbb",
        "subject": "Decouple Ollama setup completion provider",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "301fec1e3a22daeb0afc6947b768c7f29c0d37c7",
        "short_hash": "301fec1e",
        "subject": "Decouple quick resume from statusline",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "d9ebc66a60015b0710a4d646ce10e8615069a5c6",
        "short_hash": "d9ebc66a",
        "subject": "Decouple customizable command dispatch",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "3a1b1e2bbe9fc215264c0d33f27d3fe2241fa79a",
        "short_hash": "3a1b1e2b",
        "subject": "fix: decouple question theme from theme plugin",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "3c82163dc7833818301b1a7dcbf0cf938b05a479",
        "short_hash": "3c82163d",
        "subject": "fix: honor file permission provider lifecycle (#729)",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "2fd2d6cdcde3dd6bd5a7099689a4ac2fa20b37ce",
        "short_hash": "2fd2d6cd",
        "subject": "fix: decouple file permission handler plugin (#729)",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "8e4390a6c24bb84ec17e638faba7cd017da8238e",
        "short_hash": "8e4390a6",
        "subject": "fix: decouple agent skills plugin (#724)",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "d33b1f4786f48ee85087516f4f8299ebc111a868",
        "short_hash": "d33b1f47",
        "subject": "refactor: decouple chatgpt_oauth plugin from core (#728)",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "a02f621f5ffd6e7e49159b910433bbf708cfc052",
        "short_hash": "a02f621f",
        "subject": "ci: restore Windows UTF-8 smoke tests and format baseline",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "24390b2115e2f7555c7dcbfbfbb0e3f0338fc5b8",
        "short_hash": "24390b21",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-09"
      },
      {
        "hash": "a12a021a5b25eff8ab6e67ade9e2ebb9082e278c",
        "short_hash": "a12a021a",
        "subject": "test: remove dead embedded test files from code_puppy/plugins",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "bf58f6a183e39d85e7dfb6ce7018f09480cfa08c",
        "short_hash": "bf58f6a1",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-09"
      },
      {
        "hash": "8f0006c894b9778bb694aedcea05c5df6fc75638",
        "short_hash": "8f0006c8",
        "subject": "test: round-6 max-aggression blast (budgets doubled for 50k-LOC hunt)",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "4327605c4d1298942e665b247da9e6ddb5521727",
        "short_hash": "4327605c",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-09"
      },
      {
        "hash": "c4f77bb9444de21d34b8a23bdf36b800eb0f0e5d",
        "short_hash": "c4f77bb9",
        "subject": "fix: share compact Android banner detection (#723)",
        "author": "mpfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "6d7a4de2fc616d004e96beb27bb5246c67430e1d",
        "short_hash": "6d7a4de2",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-09"
      },
      {
        "hash": "eb86bfa326d9569019221b2a29043285aceb37e2",
        "short_hash": "eb86bfa3",
        "subject": "Merge remote-tracking branch 'origin/main'",
        "author": "mpfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "da2921ec58bfac3ef9c2bbd71d3d8d9004a7deaa",
        "short_hash": "da2921ec",
        "subject": "fix: use compact Android startup banner (#722)",
        "author": "mpfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "2fe3267d454a05ec6e1700a6b244809628abc0aa",
        "short_hash": "2fe3267d",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-09"
      },
      {
        "hash": "bcae2d59303cce0a8241619c23455a4654b1c672",
        "short_hash": "bcae2d59",
        "subject": "docs: add Android Termux installation guide (#721)",
        "author": "mpfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "693113170acae7b0872b93c15e423b25703e8c32",
        "short_hash": "69311317",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-09"
      },
      {
        "hash": "706da69a2f7eae0a872de7c56c668710876ce848",
        "short_hash": "706da69a",
        "subject": "fix: skip bundled ripgrep on Android (#720)",
        "author": "mpfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "48c16b2345d343226097bf27393095c394ff4740",
        "short_hash": "48c16b23",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-09"
      },
      {
        "hash": "5a8f3d6a2ddf54770fc6c9c6fdfeb6d2b4b84c08",
        "short_hash": "5a8f3d6a",
        "subject": "test: restore chatgpt_oauth usage cache in test to fix cross-test pollution",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "e2c613a058b9494959062affea6d6a14fc47a8f5",
        "short_hash": "e2c613a0",
        "subject": "test: round-5 aggressive redundancy blast (per-namespace spend budgets)",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "afddbc2b1061753940e535857e009bf0d7228193",
        "short_hash": "afddbc2b",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-09"
      },
      {
        "hash": "70a31dd48fbda1d69aba3660ae79eac1040dde71",
        "short_hash": "70a31dd4",
        "subject": "Fix Android browser import regression test (#719)",
        "author": "mpfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "0ac6710480af861278a4b64e828d830fbcf5ead1",
        "short_hash": "0ac67104",
        "subject": "Merge origin/main for Android exclusion (#718)",
        "author": "mpfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "138ffbbdfaf2fb45b902b2f555abcdce552d4a5c",
        "short_hash": "138ffbbd",
        "subject": "Exclude Playwright on Android (#718)",
        "author": "mpfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "0204236ae90b9074b88ef382113def19af059f24",
        "short_hash": "0204236a",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-09"
      },
      {
        "hash": "931c86816dde5ddff16c2e03b91551821a9e7abc",
        "short_hash": "931c8681",
        "subject": "Allow explicit curl fetches without delegation (#717)",
        "author": "mpfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "8fff8dad63d0703f2b44ed085a5757ca6970cbd3",
        "short_hash": "8fff8dad",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-09"
      },
      {
        "hash": "4f2958a7d78b4423be8a958a81f79b5bbcc0ed6f",
        "short_hash": "4f2958a7",
        "subject": "test: round-4 redundancy removal (plugins, root, command_line, tools, mcp, agents, messaging)",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "cb5a83b77b99ed160c5f0c8f50f31f044c14fcff",
        "short_hash": "cb5a83b7",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-09"
      },
      {
        "hash": "d875dddecf2f6be70ec89c4458ca4968ee9c1cfa",
        "short_hash": "d875ddde",
        "subject": "ci: make version-bump push resilient to concurrent main pushes",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "83c05d2402b981d1f04db682b52ad84db837b80d",
        "short_hash": "83c05d24",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-09"
      },
      {
        "hash": "ce428825543bb71621c892a3a482e9924f3cec1f",
        "short_hash": "ce428825",
        "subject": "test: round-3 redundancy removal (tools, mcp, agents, messaging, i18n, hook_engine)",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "837b37720a3464269215260d1e88af972198fca6",
        "short_hash": "837b3772",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-09"
      },
      {
        "hash": "2da13b0c7b4b71c5de856feab628a971dea74f0e",
        "short_hash": "2da13b0c",
        "subject": "test: round-3 root test reduction (-1.5k LOC via parametrization, -0.03pp coverage)",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "6370bb6bdd2d632f0ca8a79d5c1f87426394124a",
        "short_hash": "6370bb6b",
        "subject": "test: fold custom_server_installer parametrize matrix (round-3 command_line)",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "f91d31003af09a80dc2d219b076c1c57f5138dd5",
        "short_hash": "f91d3100",
        "subject": "test: round-3 command_line reduction (parametrize folds + subsumed deletions)",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-09"
      },
      {
        "hash": "aa1845d240a50f2ace667709dcfd6aca56167aa2",
        "short_hash": "aa1845d2",
        "subject": "test: round-3 reduction of tests/plugins (-3.7k LOC, -0.13pp coverage)",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-08"
      },
      {
        "hash": "35259bbedd67b5e57a974b7103e0020fdf86a6a6",
        "short_hash": "35259bbe",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-09"
      },
      {
        "hash": "3881559c912a7ce8775e0c436dcc96b0c3461693",
        "short_hash": "3881559c",
        "subject": "test: cut 40k lines of redundant tests (~18% LOC down, 1.2pp coverage cost)",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-08"
      },
      {
        "hash": "e0b7188aae41d8d2f0453e85eb60d5fc080cea20",
        "short_hash": "e0b7188a",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-08"
      },
      {
        "hash": "5d3d429dea773dbf61c3ea708e8573ba7b22d0a2",
        "short_hash": "5d3d429d",
        "subject": "Merge pull request #675 from JulienEllie/fix/subagent-session-persistence",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-08"
      },
      {
        "hash": "bdb700764e62d8ccd0719a6bccc4174fe73352be",
        "short_hash": "bdb70076",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-07"
      },
      {
        "hash": "23b4d1feb52c547dddb5f8398adafca932e0bb6f",
        "short_hash": "23b4d1fe",
        "subject": "Merge pull request #713 from thomwebb/feat/namespace-skill-search",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-07"
      },
      {
        "hash": "0b16ce2fc462e1de9e8c0f8f03284b1a73b06453",
        "short_hash": "0b16ce2f",
        "subject": "docs: note that the first skill tag sets its namespace",
        "author": "TJ Webb",
        "date": "2026-08-07"
      },
      {
        "hash": "c07f39e557b1db39e9da4e3b8a32c9a5209a39d8",
        "short_hash": "c07f39e5",
        "subject": "Split code-puppy-agent skill into topic reference docs",
        "author": "TJ Webb",
        "date": "2026-08-07"
      },
      {
        "hash": "99c6d49481cc0a115c02f18bdfee2119b9c71776",
        "short_hash": "99c6d494",
        "subject": "Add user-facing docs for skill namespaces",
        "author": "TJ Webb",
        "date": "2026-08-07"
      },
      {
        "hash": "c41a76c8fb07beab83320aa51984b43bd5200cd1",
        "short_hash": "c41a76c8",
        "subject": "Address adversarial review findings",
        "author": "TJ Webb",
        "date": "2026-08-07"
      },
      {
        "hash": "c8557ce2ff56432036be1aa1a8331f5cf2cae905",
        "short_hash": "c8557ce2",
        "subject": "Add namespace_skill_search plugin",
        "author": "TJ Webb",
        "date": "2026-08-07"
      },
      {
        "hash": "94204ef429edfa787b056cfd877350fb5086d5e8",
        "short_hash": "94204ef4",
        "subject": "Removed dead get_file_icon.",
        "author": "Jack Yao",
        "date": "2026-08-07"
      },
      {
        "hash": "62fa01ac8313608439436b95f329f7ac1ebbe0e0",
        "short_hash": "62fa01ac",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-07"
      },
      {
        "hash": "505e91c3d827b841726bf2b02bdd13eae8ba8685",
        "short_hash": "505e91c3",
        "subject": "Merge pull request #700 from thomwebb/agent-web-retriever",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-06"
      },
      {
        "hash": "ee1bd8a4f6dd90924478511e334232681a1eb407",
        "short_hash": "ee1bd8a4",
        "subject": "Merge pull request #702 from breedx/feat/opus-xhigh-effort",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-06"
      },
      {
        "hash": "923135bbdb5c8d728a5b773305cf127b5a637c20",
        "short_hash": "923135bb",
        "subject": "Merge pull request #707 from piercebrookins/feat/meta-muse-oauth",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-06"
      },
      {
        "hash": "226e8cb38bdc0033551956bfe22364d1d7d6eff9",
        "short_hash": "226e8cb3",
        "subject": "Merge pull request #710 from ryan-duve/main",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-06"
      },
      {
        "hash": "dd118995d133135ec4a91d4c6495e86281a12125",
        "short_hash": "dd118995",
        "subject": "Fix claude_code_oauth pasted callback functionality for reauth",
        "author": "ryan-duve",
        "date": "2026-08-06"
      },
      {
        "hash": "c0e262470131b86a0f0d0bc284587128a17c05d2",
        "short_hash": "c0e26247",
        "subject": "feat: add Meta Muse OAuth provider",
        "author": "Pierce Brookins",
        "date": "2026-08-05"
      },
      {
        "hash": "3f6cb124cf603ee800e6d5e4060e490cca9e9ca8",
        "short_hash": "3f6cb124",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-05"
      },
      {
        "hash": "183ef9265c9e7bef19abf1f6f8f810dc92c71c65",
        "short_hash": "183ef926",
        "subject": "Merge pull request #654 from thomwebb/feat/i18n-extract-config-wizard",
        "author": "TJ",
        "date": "2026-08-05"
      },
      {
        "hash": "27128713791910be9bab242b90fbdb1a2b53f9bb",
        "short_hash": "27128713",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-05"
      },
      {
        "hash": "41482504c7d29e2e4f2d99edab58a336c6322b27",
        "short_hash": "41482504",
        "subject": "Merge remote-tracking branch 'upstream/main' into feat/i18n-extract-config-wizard",
        "author": "TJ Webb",
        "date": "2026-08-05"
      },
      {
        "hash": "2b250e2b23204aa99b0b01d0fb1900850276620f",
        "short_hash": "2b250e2b",
        "subject": "Merge pull request #655 from thomwebb/feat/i18n-extract-session-commands",
        "author": "TJ",
        "date": "2026-08-05"
      },
      {
        "hash": "40a422000f5808b8d4fba099f217bd4b9c0d9d91",
        "short_hash": "40a42200",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-05"
      },
      {
        "hash": "fe7d093e387e2bd26042a0c49a099149bacaff0b",
        "short_hash": "fe7d093e",
        "subject": "Merge pull request #701 from Prathap-P/fix/streaming-retry-progress-reset-backoff",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-05"
      },
      {
        "hash": "0bf8118227bc392ea4a7e2438aad4c67c8ba912d",
        "short_hash": "0bf81182",
        "subject": "fix(model-settings): preserve callable compatibility safely",
        "author": "breedx",
        "date": "2026-08-05"
      },
      {
        "hash": "9c6a796d6dcf3b0739daabeeba41a05c6253461d",
        "short_hash": "9c6a796d",
        "subject": "fix(model-settings): keep catalog loads out of repaints",
        "author": "breedx",
        "date": "2026-08-05"
      },
      {
        "hash": "e787168d7e2f149543ef439e8d0a584d3382ab43",
        "short_hash": "e787168d",
        "subject": "feat(model-settings): add xhigh adaptive effort",
        "author": "breedx",
        "date": "2026-08-05"
      },
      {
        "hash": "9c7df7bcdd5456aa2c8870de5d02a63e3bd77d18",
        "short_hash": "9c7df7bc",
        "subject": "fix(retry): progress reset must use minimum backoff, not maximum",
        "author": "Prathap",
        "date": "2026-08-05"
      },
      {
        "hash": "e8b9989d88a5b2024e2862175adf8577b3f3f504",
        "short_hash": "e8b9989d",
        "subject": "fix(subagents): make the parent agent aware of an interrupted sub-agent",
        "author": "Julien Ellie",
        "date": "2026-08-04"
      },
      {
        "hash": "f24ee81fd2e116ffb140f7759e8a91cda86c5349",
        "short_hash": "f24ee81f",
        "subject": "fix(subagents): persist interrupted sessions so Ctrl-C is resumable",
        "author": "Julien Ellie",
        "date": "2026-08-04"
      },
      {
        "hash": "3e1949dc9618fff75ec9c98c8f5f72ec826d86d6",
        "short_hash": "3e1949dc",
        "subject": "Address adversarial review findings on web-retriever",
        "author": "TJ Webb",
        "date": "2026-08-04"
      },
      {
        "hash": "4e5705add3fc6076f12e2862bb9a18f8b92ed880",
        "short_hash": "4e5705ad",
        "subject": "Add web-retriever agent for browser automation and scraping",
        "author": "TJ Webb",
        "date": "2026-08-04"
      },
      {
        "hash": "c7278a909db29c87d25f9792b7dfe0c4244a5891",
        "short_hash": "c7278a90",
        "subject": "Merge upstream main and resolve i18n catalogs",
        "author": "TJ Webb",
        "date": "2026-08-03"
      },
      {
        "hash": "09085be5b3229238e06e7f8854dca59c171a301d",
        "short_hash": "09085be5",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-03"
      },
      {
        "hash": "3cacb1106484efcdca3ec31b30cc70f58d249a03",
        "short_hash": "3cacb110",
        "subject": "Merge pull request #656 from thomwebb/fix/i18n-audit-false-positives",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-03"
      },
      {
        "hash": "b25b163d7418b43c8e313c940af2b6c6e38e0ae0",
        "short_hash": "b25b163d",
        "subject": "Merge pull request #687 from mwmoreno/feature/granular-command-guard-allowlist",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-03"
      },
      {
        "hash": "ab601a23747eaaffaffc468b2515d8c4235f24e1",
        "short_hash": "ab601a23",
        "subject": "Merge pull request #653 from thomwebb/feat/i18n-extract-claude-oauth",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-03"
      },
      {
        "hash": "a0dd5f459f06839678f4ef161b187203f090f413",
        "short_hash": "a0dd5f45",
        "subject": "Merge pull request #692 from breedx/fix/mcp-config-cannot-be-its-own-project-twin",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-03"
      },
      {
        "hash": "12276aa989cc2d4efa9870d81418d9507e55d9db",
        "short_hash": "12276aa9",
        "subject": "feat(herdr): add Windows named-pipe transport",
        "author": "weegens-aaron",
        "date": "2026-08-01"
      },
      {
        "hash": "2434cbde6ecd5bee3826b621321cda9f6433a785",
        "short_hash": "2434cbde",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-01"
      },
      {
        "hash": "65ab06eaba76892697f41bb929e848e41842eac1",
        "short_hash": "65ab06ea",
        "subject": "fix(fork): /fork now snapshots the conversation at fork time",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-01"
      },
      {
        "hash": "b573b527c199ac538376e47ecf1d360c76d6b075",
        "short_hash": "b573b527",
        "subject": "Make file tools primary args required (file_path/search_string/content/replacements/snippet) (#694)",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-01"
      },
      {
        "hash": "343879761b1eb940e2f40c07c4db897e306013d2",
        "short_hash": "34387976",
        "subject": "Fix empty shell command to return clean ShellCommandOutput, require command arg (#693)",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-01"
      },
      {
        "hash": "d08b6c97bec759e468d3ea421e6b3bfc7dedda82",
        "short_hash": "d08b6c97",
        "subject": "feat(model-settings): user-defined custom request params per model",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-01"
      },
      {
        "hash": "533552b24f6752440f5eaf3ae6dc7a3bbfab33af",
        "short_hash": "533552b2",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-08-01"
      },
      {
        "hash": "f10dc4ad85b5a9a1fe2c9187da3ebe832432d04a",
        "short_hash": "f10dc4ad",
        "subject": "test(reasoning): update tests to reflect renamed effort levels and config keys",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-01"
      },
      {
        "hash": "be82de3b7838079cc388409e9135a5ca2aa15ad3",
        "short_hash": "be82de3b",
        "subject": "feat(model-factory): add backward-compat aliases for legacy reasoning effort values",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-01"
      },
      {
        "hash": "fefb31b02bc9a78212e516f8810a89d3fe3ba6d3",
        "short_hash": "fefb31b0",
        "subject": "refactor(reasoning): rename ultra/minimal effort levels to max/none",
        "author": "Mike Pfaffenberger",
        "date": "2026-08-01"
      },
      {
        "hash": "6a9f539bf7df86767f85a474f9a5fbe55dbd7ac6",
        "short_hash": "6a9f539b",
        "subject": "fix(mcp): a config can't be its own untrusted project twin (CWD == $HOME)",
        "author": "breedx",
        "date": "2026-07-31"
      },
      {
        "hash": "0d7764e03a34959b2cea717521fc21c7f9d1692c",
        "short_hash": "0d7764e0",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-30"
      },
      {
        "hash": "37f5a9adf736df41e6465e6979aaab9f19b7ff03",
        "short_hash": "37f5a9ad",
        "subject": "fix(computer-use): require explicit opt-in (#688)",
        "author": "mpfaffenberger",
        "date": "2026-07-30"
      },
      {
        "hash": "baa95cefc63778c6320cad6654246e5d8102f503",
        "short_hash": "baa95cef",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-29"
      },
      {
        "hash": "bfc4927f209493b8a97fc968cf9f38af5734c21d",
        "short_hash": "bfc4927f",
        "subject": "Merge pull request #685 from mpfaffenberger/awtilso/PUP-549",
        "author": "Andrew Tilson",
        "date": "2026-07-29"
      },
      {
        "hash": "d297658b259cce5a4943e2aa004442885fbc0b7c",
        "short_hash": "d297658b",
        "subject": "docs(destructive-guard): add scoped AGENTS.md for the plugin",
        "author": "mwmoren",
        "date": "2026-07-29"
      },
      {
        "hash": "dc95797367d0a9035f54d7112c1331ac44c8e96e",
        "short_hash": "dc957973",
        "subject": "feat(guards): granular per-pattern allowlist for command guards",
        "author": "mwmoren",
        "date": "2026-07-29"
      },
      {
        "hash": "169f81e827d0543da3afc1e0c069ce2e3517679e",
        "short_hash": "169f81e8",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-28"
      },
      {
        "hash": "1a41a14795eb51f9ebf624bba82578772fe2d230",
        "short_hash": "1a41a147",
        "subject": "Merge pull request #686 from thomwebb/fix-valid-summary-request-part",
        "author": "TJ",
        "date": "2026-07-28"
      },
      {
        "hash": "a346bdfe92a9b2218cf5cb00288a6c8e7ee4f5b0",
        "short_hash": "a346bdfe",
        "subject": "Format compaction regression test",
        "author": "TJ Webb",
        "date": "2026-07-28"
      },
      {
        "hash": "830de857cd0dd1c67d7dd1c1a017097d4481f034",
        "short_hash": "830de857",
        "subject": "test: sync test_config.py snapshots with new subagent_recursion_limit_gpt_5_6 key",
        "author": "Andrew Tilson - awtilso",
        "date": "2026-07-28"
      },
      {
        "hash": "9d2bd0ba24483bb925027d3e2a6cc7969b780f7e",
        "short_hash": "9d2bd0ba",
        "subject": "chore: ruff format",
        "author": "Andrew Tilson - awtilso",
        "date": "2026-07-28"
      },
      {
        "hash": "21d94bba67bc53824b20147b76eb773b51b9d1fe",
        "short_hash": "21d94bba",
        "subject": "Make GPT-5.6 sub-agent depth cap tunable via /set",
        "author": "Andrew Tilson - awtilso",
        "date": "2026-07-28"
      },
      {
        "hash": "604b31a8a051a91773605aa6c05fc4786548f32a",
        "short_hash": "604b31a8",
        "subject": "Exercise OpenAI summary message mapping",
        "author": "TJ Webb",
        "date": "2026-07-28"
      },
      {
        "hash": "7af7108b6b11959cb5e891663d87dab920f330c4",
        "short_hash": "7af7108b",
        "subject": "Fix invalid summary message part",
        "author": "TJ Webb",
        "date": "2026-07-28"
      },
      {
        "hash": "eb4c7af1dc22e008d28ff2160f8f652021a20fbb",
        "short_hash": "eb4c7af1",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-28"
      },
      {
        "hash": "c38f823df95a1c81de45c1aacb1effb32415cff1",
        "short_hash": "c38f823d",
        "subject": "Raise GPT-5.6 sub-agent depth cap from 1 to 2",
        "author": "Andrew Tilson - awtilso",
        "date": "2026-07-28"
      },
      {
        "hash": "9a373fcf44ba576fedf50c0cfec95aa39dd0f0f0",
        "short_hash": "9a373fcf",
        "subject": "Merge pull request #684 from thomwebb/clarify-agent-model-optional",
        "author": "TJ",
        "date": "2026-07-28"
      },
      {
        "hash": "25f8b2a402d85769ad60422c3586cfc4f0154c20",
        "short_hash": "25f8b2a4",
        "subject": "Match schema example to runtime requirements",
        "author": "TJ Webb",
        "date": "2026-07-28"
      },
      {
        "hash": "b3d1987b2bff4b67fc1e3dd80cca2b1686bba900",
        "short_hash": "b3d1987b",
        "subject": "Keep agent ID in creator schema",
        "author": "TJ Webb",
        "date": "2026-07-28"
      },
      {
        "hash": "4719f6b0df44bc6f2e9d9031be0a3c5a540d3d2e",
        "short_hash": "4719f6b0",
        "subject": "Refresh Agent Creator model examples",
        "author": "TJ Webb",
        "date": "2026-07-28"
      },
      {
        "hash": "facafd1c6212a5e71d6b76d211e8a83ff37d3f89",
        "short_hash": "facafd1c",
        "subject": "Clarify optional agent model pinning",
        "author": "TJ Webb",
        "date": "2026-07-28"
      },
      {
        "hash": "1b5b370857c5ca534c6d40460205966913918557",
        "short_hash": "1b5b3708",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-28"
      },
      {
        "hash": "dddec902cabe913bb92b6f835e4b91900d012498",
        "short_hash": "dddec902",
        "subject": "Merge pull request #678 from mpfaffenberger/awtilso/PUP-544-scope-fix",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-28"
      },
      {
        "hash": "42b2f1b97f1180734d125d4d8b3750ab1145d0d6",
        "short_hash": "42b2f1b9",
        "subject": "Merge pull request #682 from thomwebb/chore/remove-empty-regional-locales",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-28"
      },
      {
        "hash": "ff359a84c12e292d61b2be00552ae077d5307163",
        "short_hash": "ff359a84",
        "subject": "Merge pull request #683 from piercebrookins/agent/add-macos-computer-use",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-28"
      },
      {
        "hash": "344c75ee79b156a64033db40c42f3c2d6052a021",
        "short_hash": "344c75ee",
        "subject": "fix(statusline): add utf-8 encoding kwargs to detect_git_branch subprocess call",
        "author": "Andrew Tilson - awtilso",
        "date": "2026-07-28"
      },
      {
        "hash": "c010eef8c2cd3328cf2c3a40d9a0818d267daae5",
        "short_hash": "c010eef8",
        "subject": "Add native macOS computer use plugin",
        "author": "Pierce Brookins",
        "date": "2026-07-27"
      },
      {
        "hash": "d739bfb30601039c4ca5e79fb49ca937c5cc8122",
        "short_hash": "d739bfb3",
        "subject": "chore(i18n): remove empty regional locale stubs",
        "author": "TJ Webb",
        "date": "2026-07-27"
      },
      {
        "hash": "137a4361541009bb18eb07cdc1530e366c6a03ca",
        "short_hash": "137a4361",
        "subject": "Merge main into i18n Claude OAuth PR",
        "author": "TJ Webb",
        "date": "2026-07-27"
      },
      {
        "hash": "a139fca414c95ab7f90861a678f206fee77acf0a",
        "short_hash": "a139fca4",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-27"
      },
      {
        "hash": "d6975fe44fe0f94e2715b0f27210b02a727be4cd",
        "short_hash": "d6975fe4",
        "subject": "fix: rewrite detect_git_branch test to match temp-file implementation",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-27"
      },
      {
        "hash": "c0d42c7b3d9b477dafb9346c77ec60733d45f57b",
        "short_hash": "c0d42c7b",
        "subject": "fix(subagent): scope per-run token usage/timing to invoke_agent_with_model only",
        "author": "Andrew Tilson - awtilso",
        "date": "2026-07-27"
      },
      {
        "hash": "252667878910f5b24f37093070e8199903aa565e",
        "short_hash": "25266787",
        "subject": "Merge pull request #649 from weegens-aaron/fix/flux-windows-os",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-27"
      },
      {
        "hash": "eed40e54e51196e0962e375a030db1d097a46693",
        "short_hash": "eed40e54",
        "subject": "Merge pull request #652 from thomwebb/feat/i18n-extract-core-commands",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-27"
      },
      {
        "hash": "c921a7c45f32cf39cba38948b45e1d18ab2e5627",
        "short_hash": "c921a7c4",
        "subject": "Merge pull request #668 from thomwebb/perf/theme-lazy-imports",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-27"
      },
      {
        "hash": "194503e3a9d1e651066b167fae570e43454c7f0d",
        "short_hash": "194503e3",
        "subject": "Merge pull request #673 from CarlosSantes/patch-2",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-27"
      },
      {
        "hash": "1d210f9c995ecd52a936b1cfdb3dd436796c9e75",
        "short_hash": "1d210f9c",
        "subject": "Merge pull request #677 from JulienEllie/feat/herdr-protocol-v16",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-27"
      },
      {
        "hash": "586f1021bc306ef3684e540613bd39775f249a98",
        "short_hash": "586f1021",
        "subject": "Merge pull request #676 from bporterfielddsc/fix/acp-windows-git-subprocess-hang",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-27"
      },
      {
        "hash": "52b3f45d43d968de634ca747350efed36e54a877",
        "short_hash": "52b3f45d",
        "subject": "test(herdr): add live smoke test against a real herdr pane",
        "author": "Julien Ellie",
        "date": "2026-07-26"
      },
      {
        "hash": "6a3a833521f96d6638cec1159f4d3d06be8e4368",
        "short_hash": "6a3a8335",
        "subject": "fix(acp): stop Windows subprocess pipe-drain deadlock hanging tool turns",
        "author": "Blayne Porterfield",
        "date": "2026-07-26"
      },
      {
        "hash": "faba4284e196ec50ca7ce9006ea43267647801a6",
        "short_hash": "faba4284",
        "subject": "feat(herdr): durable session references + finish protocol-16 docs",
        "author": "Julien Ellie",
        "date": "2026-07-26"
      },
      {
        "hash": "c0566cfc4ea705d9e9ff26342a907a1067fe7faa",
        "short_hash": "c0566cfc",
        "subject": "feat(herdr): add decorative activity messages via tool callbacks",
        "author": "Julien Ellie",
        "date": "2026-07-26"
      },
      {
        "hash": "ebbd66cc5635b3876f608ac228a8143ea709d717",
        "short_hash": "ebbd66cc",
        "subject": "feat(herdr): report pane metadata (model/context/tokens) at turn end",
        "author": "Julien Ellie",
        "date": "2026-07-26"
      },
      {
        "hash": "f8ffe01bd4742f05699cb0c2f7c53c44269d5d11",
        "short_hash": "f8ffe01b",
        "subject": "feat(herdr): harden transport with coalescing lanes + bounded release",
        "author": "Julien Ellie",
        "date": "2026-07-26"
      },
      {
        "hash": "99cc88e31a92350f1f9b139aca685a9fcc861ccd",
        "short_hash": "99cc88e3",
        "subject": "refactor(token-usage): promote usage estimator to core module",
        "author": "Julien Ellie",
        "date": "2026-07-26"
      },
      {
        "hash": "a6790dbea918a5defcf7ffc6c0e39dfa791d6022",
        "short_hash": "a6790dbe",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-25"
      },
      {
        "hash": "cd5889953c93a584ef2a49250d63d3cdadabe6fe",
        "short_hash": "cd588995",
        "subject": "feat(chatgpt_oauth): support reference images in codex_imagegen",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-25"
      },
      {
        "hash": "d61a26ceca644bafe968c588d584afb0f4d29546",
        "short_hash": "d61a26ce",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-25"
      },
      {
        "hash": "46a6f780ce5803302ee1503e7528e697de8167ee",
        "short_hash": "46a6f780",
        "subject": "Merge pull request #674 from mpfaffenberger/awtilso/PUP-544",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-25"
      },
      {
        "hash": "8a4b7becd8491ce8212e3782919fd318f89f10f0",
        "short_hash": "8a4b7bec",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-25"
      },
      {
        "hash": "d7978d7b1a444afb2ef2ea45b6758046fdb8ec4a",
        "short_hash": "d7978d7b",
        "subject": "fix(herdr): silence user-initiated menus",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-25"
      },
      {
        "hash": "9af11a3e392e7113e8bfae5db0f2484104aabe95",
        "short_hash": "9af11a3e",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-25"
      },
      {
        "hash": "f2c0848ddacbf6b5d773828267d6b18ae922501e",
        "short_hash": "f2c0848d",
        "subject": "feat(claude_code_oauth): add claude-opus-5 support",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-25"
      },
      {
        "hash": "67f1161f314a68e054ca2407341fb146600f896c",
        "short_hash": "67f1161f",
        "subject": "style: apply ruff format to usage instrumentation and tests",
        "author": "Andrew Tilson - awtilso",
        "date": "2026-07-24"
      },
      {
        "hash": "54b7688439d3e802ffb1669138090d22ff6a7375",
        "short_hash": "54b76884",
        "subject": "feat(subagent): break out cache tokens and add run timestamps",
        "author": "Andrew Tilson - awtilso",
        "date": "2026-07-24"
      },
      {
        "hash": "ccc81e7cdc1c49fd467c654bce090a9fbe5cd48f",
        "short_hash": "ccc81e7c",
        "subject": "feat(subagent): report per-run token usage and latency",
        "author": "Andrew Tilson - awtilso",
        "date": "2026-07-24"
      },
      {
        "hash": "a4610752e1ef2c5675c688194fef22a7bfa26b67",
        "short_hash": "a4610752",
        "subject": "Update French Canadian translations in fr-CA.json",
        "author": "CarlosSantes",
        "date": "2026-07-24"
      },
      {
        "hash": "82e12de7084ead45832a9c2334e9c668448c48c6",
        "short_hash": "82e12de7",
        "subject": "i18n(fr-CA): restore pre-existing 15 keys byte-for-byte for in-flight translator work",
        "author": "TJ Webb",
        "date": "2026-07-24"
      },
      {
        "hash": "429eb24d3d0dbabad5d1aa5fecaf5d25f93982db",
        "short_hash": "429eb24d",
        "subject": "i18n(fr-CA): restore pre-existing 15 keys byte-for-byte for in-flight translator work",
        "author": "TJ Webb",
        "date": "2026-07-24"
      },
      {
        "hash": "dae0e568924e28d90fd50b42b9095a919f5f7ef8",
        "short_hash": "dae0e568",
        "subject": "i18n(fr-CA): restore pre-existing 15 keys byte-for-byte for in-flight translator work",
        "author": "TJ Webb",
        "date": "2026-07-24"
      },
      {
        "hash": "4989844ebb21ff4e2fe6231821eeebfaf2411e1e",
        "short_hash": "4989844e",
        "subject": "i18n(fr-CA): restore pre-existing 15 keys byte-for-byte for in-flight translator work",
        "author": "TJ Webb",
        "date": "2026-07-24"
      },
      {
        "hash": "dc6f5f199c24b7423e9ce6968a1b3ec95fb8f8d1",
        "short_hash": "dc6f5f19",
        "subject": "i18n(es,fr-CA): apply adversarial review fixes (semantic + QC typography)",
        "author": "TJ Webb",
        "date": "2026-07-24"
      },
      {
        "hash": "b7ca9d32cd36a5d2929281b5bf69daff541471f0",
        "short_hash": "b7ca9d32",
        "subject": "i18n(es,fr-CA): apply adversarial review fixes (semantic + QC typography)",
        "author": "TJ Webb",
        "date": "2026-07-24"
      },
      {
        "hash": "211bc543bb0b173c32e4aade3ac650cee4ee71ca",
        "short_hash": "211bc543",
        "subject": "i18n(es,fr-CA): apply adversarial review fixes (semantic + QC typography)",
        "author": "TJ Webb",
        "date": "2026-07-24"
      },
      {
        "hash": "3a37a83994305436168de7968e14ec5638c30db3",
        "short_hash": "3a37a839",
        "subject": "i18n(es,fr-CA): apply adversarial review fixes (semantic + QC typography)",
        "author": "TJ Webb",
        "date": "2026-07-24"
      },
      {
        "hash": "91b3f658e08b940152d98c2fda67c0e5fe96c50e",
        "short_hash": "91b3f658",
        "subject": "i18n(es,fr-CA): translate 35 new keys from PR #655 (session/compact commands)",
        "author": "TJ Webb",
        "date": "2026-07-24"
      },
      {
        "hash": "20db3b029d05b8800fdf0b9a8ce581ca8e0518b9",
        "short_hash": "20db3b02",
        "subject": "i18n(es,fr-CA): translate 39 new keys from PR #654 (mcp_config_wizard)",
        "author": "TJ Webb",
        "date": "2026-07-24"
      },
      {
        "hash": "49f000cafc78336cd86345660a1d178c4df56cde",
        "short_hash": "49f000ca",
        "subject": "i18n(es,fr-CA): translate 48 new keys from PR #653 (claude_code_oauth)",
        "author": "TJ Webb",
        "date": "2026-07-24"
      },
      {
        "hash": "c542ca785301b14c7e45c81b2e2adeb808f3432b",
        "short_hash": "c542ca78",
        "subject": "i18n(es,fr-CA): translate 32 new keys from PR #652 (core_commands)",
        "author": "TJ Webb",
        "date": "2026-07-24"
      },
      {
        "hash": "bf548837d21e3990f6707f15f83d717fca7c9f53",
        "short_hash": "bf548837",
        "subject": "review: address adversarial-review feedback on theme lazy PR",
        "author": "TJ Webb",
        "date": "2026-07-23"
      },
      {
        "hash": "8909a9771e3044a39b6673208c5f8f24089cc409",
        "short_hash": "8909a977",
        "subject": "style(theme): restore literal palette emoji character",
        "author": "TJ Webb",
        "date": "2026-07-23"
      },
      {
        "hash": "cc183da4df2e9235ec1cf9f98c6e617221fa6fc9",
        "short_hash": "cc183da4",
        "subject": "docs(theme): rewrite import-note comment to drop stale doc reference",
        "author": "TJ Webb",
        "date": "2026-07-23"
      },
      {
        "hash": "0de2cb7503711b0a1e54ccc169505e78da8a9011",
        "short_hash": "0de2cb75",
        "subject": "chore: drop docs/STARTUP_PERFORMANCE.md from this PR",
        "author": "TJ Webb",
        "date": "2026-07-23"
      },
      {
        "hash": "01637eb9c1318903981571bea83b7e853c730a46",
        "short_hash": "01637eb9",
        "subject": "style(tests): apply ruff format to theme test patch retargets",
        "author": "TJ Webb",
        "date": "2026-07-23"
      },
      {
        "hash": "938e3359e689448048bfac2d88dca0f188caab8c",
        "short_hash": "938e3359",
        "subject": "docs(perf): reprioritise startup perf plan based on interactive-launch profiling",
        "author": "TJ Webb",
        "date": "2026-07-23"
      },
      {
        "hash": "ea805e947b5037b2b72ac73e40a8fbd34aa1fd3d",
        "short_hash": "ea805e94",
        "subject": "perf(theme): defer heavy imports until user actions need them",
        "author": "TJ Webb",
        "date": "2026-07-23"
      },
      {
        "hash": "9aaf9516269bfafa1caf80a422651c5bb624f64f",
        "short_hash": "9aaf9516",
        "subject": "Merge pull request #672 from AndrewTilson/awtilso/PUP-543",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-24"
      },
      {
        "hash": "5058379812e5cb5c6c7e397b14539300cdc89e24",
        "short_hash": "50583798",
        "subject": "feat: add @model autocomplete to /fork command",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-23"
      },
      {
        "hash": "546ffbb5de9376c8a52d48f5bafd6ae04ef981e4",
        "short_hash": "546ffbb5",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-24"
      },
      {
        "hash": "1ee0b143fb29bcdb322e9edf7c92b3952d2c40ec",
        "short_hash": "1ee0b143",
        "subject": "fix(subagents): stop injecting AGENTS.md rules into sub-agent prompts",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-24"
      },
      {
        "hash": "9df4b1b50bd88ccf39eb8e87be85bfa52f02dc23",
        "short_hash": "9df4b1b5",
        "subject": "fix(ask_user_question): defer on_prompt_toolkit_style import in tui_loop",
        "author": "Andrew Tilson - awtilso",
        "date": "2026-07-24"
      },
      {
        "hash": "0ddbe48bd79c800ac5bd27343e759fe75391cece",
        "short_hash": "0ddbe48b",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-24"
      },
      {
        "hash": "e2ecf9465957c83395c206aa5b636ed62425db04",
        "short_hash": "e2ecf946",
        "subject": "Merge pull request #670 from mpfaffenberger/fix/publish-race",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-24"
      },
      {
        "hash": "266225dc1f4efb6fe700e8531c738ba5f2daa878",
        "short_hash": "266225dc",
        "subject": "style(i18n): ruff-format claude_oauth namespace refactor",
        "author": "TJ Webb",
        "date": "2026-07-23"
      },
      {
        "hash": "44f98c483a36883cf9ddfe1e8d906dcde6c06005",
        "short_hash": "44f98c48",
        "subject": "fix(i18n/audit): fail loud on nonexistent root path",
        "author": "TJ Webb",
        "date": "2026-07-23"
      },
      {
        "hash": "f733054d1b27c6dcbdf8a63d58661e687e69ca0b",
        "short_hash": "f733054d",
        "subject": "fix(i18n): address PR #655 review — safe catalog interpolation + UX/grammar",
        "author": "TJ Webb",
        "date": "2026-07-23"
      },
      {
        "hash": "ddb1d19b2a70dc041cdfd8eefb1bcdc798da543c",
        "short_hash": "ddb1d19b",
        "subject": "fix(mcp): restore re-prompt on invalid server type input",
        "author": "TJ Webb",
        "date": "2026-07-23"
      },
      {
        "hash": "b49f754ab9a1f8b8b0db90212a08252c19a4fa5e",
        "short_hash": "b49f754a",
        "subject": "fix(i18n): preserve original picker_failed wording per review",
        "author": "TJ Webb",
        "date": "2026-07-23"
      },
      {
        "hash": "ec1c5d457706b7f63d1a85be56048226f8951a7e",
        "short_hash": "ec1c5d45",
        "subject": "refactor(i18n): move Claude-specific keys to oauth.claude.* namespace",
        "author": "TJ Webb",
        "date": "2026-07-23"
      },
      {
        "hash": "27bb1ead096f11832d68436530ad69791867835b",
        "short_hash": "27bb1ead",
        "subject": "fix(i18n/audit): fix FormattedValue false negative and non-existent path silent zero",
        "author": "TJ Webb",
        "date": "2026-07-20"
      },
      {
        "hash": "f5b3d0cb334090385a5cb07c3f60b247d5e9a82d",
        "short_hash": "f5b3d0cb",
        "subject": "fix(i18n): address review feedback on session_commands extraction",
        "author": "TJ Webb",
        "date": "2026-07-20"
      },
      {
        "hash": "fbef51c95e480fd2aa732f4e5c74cb588fbc5258",
        "short_hash": "fbef51c9",
        "subject": "fix(i18n): address review feedback on config_wizard extraction",
        "author": "TJ Webb",
        "date": "2026-07-20"
      },
      {
        "hash": "d45534489d728082fbd21bb80e68813fd3d08d88",
        "short_hash": "d4553448",
        "subject": "fix(i18n): rename loop var to unshadow module-level t()",
        "author": "TJ Webb",
        "date": "2026-07-20"
      },
      {
        "hash": "7d972ae66302ea914f5fd481426dfcf5077d7f6a",
        "short_hash": "7d972ae6",
        "subject": "fix(i18n): wire remaining oauth raw sites and add structural test",
        "author": "TJ Webb",
        "date": "2026-07-20"
      },
      {
        "hash": "f77f36542acc8b3be45fda322c6b3fcfb40a2165",
        "short_hash": "f77f3654",
        "subject": "fix(i18n/audit): eliminate false positives in raw-site classification",
        "author": "TJ Webb",
        "date": "2026-07-20"
      },
      {
        "hash": "5c91a1eaeb9d2c7077364b11f516f7495ae5d8af",
        "short_hash": "5c91a1ea",
        "subject": "feat(i18n): extract session_commands.py strings",
        "author": "TJ Webb",
        "date": "2026-07-20"
      },
      {
        "hash": "f91204487c99b090bd45c30907ce415edba0db86",
        "short_hash": "f9120448",
        "subject": "fix(i18n): address review feedback on config_wizard extraction",
        "author": "TJ Webb",
        "date": "2026-07-20"
      },
      {
        "hash": "9444533b8fd9ce9cb8d81ca490918490d125d6b8",
        "short_hash": "9444533b",
        "subject": "fix(i18n): address review feedback on core_commands extraction",
        "author": "TJ Webb",
        "date": "2026-07-20"
      },
      {
        "hash": "11bc76ad9005fd8eaf9d550c49ed56912b926485",
        "short_hash": "11bc76ad",
        "subject": "fix(i18n): address review feedback on claude_code_oauth extraction",
        "author": "TJ Webb",
        "date": "2026-07-20"
      },
      {
        "hash": "e4f8d9da4facee3e3dbef8b12046f1acb32c4aa4",
        "short_hash": "e4f8d9da",
        "subject": "feat(i18n): extract mcp_/config_wizard.py strings",
        "author": "TJ Webb",
        "date": "2026-07-20"
      },
      {
        "hash": "d6635f28552fa93635c1db771029138a05d43ade",
        "short_hash": "d6635f28",
        "subject": "feat(i18n): extract core_commands.py user-facing strings",
        "author": "TJ Webb",
        "date": "2026-07-20"
      },
      {
        "hash": "930d8ea1ab1ec660dc8a4570a963357f015ffcac",
        "short_hash": "930d8ea1",
        "subject": "feat(i18n): extract claude_code_oauth/register_callbacks.py strings",
        "author": "TJ Webb",
        "date": "2026-07-20"
      },
      {
        "hash": "3d0d0c9caa1c4cb980829894dbb86e26f3bfab71",
        "short_hash": "3d0d0c9c",
        "subject": "fix(ci): serialize PyPI publishes and self-heal version collisions",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-23"
      },
      {
        "hash": "f9db66cb7881d34cfecb2e21c943eed807819938",
        "short_hash": "f9db66cb",
        "subject": "chore: sync version to 0.0.662 already published on PyPI [ci skip]",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-23"
      },
      {
        "hash": "30cfead5540f08ae104ccc68e8e37017273ec1e2",
        "short_hash": "30cfead5",
        "subject": "Merge pull request #669 from mpfaffenberger/fix/pin-ruff",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-23"
      },
      {
        "hash": "119483df15a36f10b344f0a71d8ad0a3c881584d",
        "short_hash": "119483df",
        "subject": "fix(ci): pin ruff to >=0.15,<0.16 to stop default-ruleset drift",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-23"
      },
      {
        "hash": "4cab0a17a2804ea27c0707089cbc0db452f76552",
        "short_hash": "4cab0a17",
        "subject": "chore: ignore .worktrees/ local git worktree dir",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-23"
      },
      {
        "hash": "5ae287b67060a133ebff99a2166df370eb03fe3e",
        "short_hash": "5ae287b6",
        "subject": "feat: timestamp_heartbeat plugin — stamp __SYS_TIMESTAMP__ into tool results every k calls",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-23"
      },
      {
        "hash": "febc1da23f2fbee35d3bb0c87d1481cb5c01e85a",
        "short_hash": "febc1da2",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-23"
      },
      {
        "hash": "cb294274d93f35b74b5c0b884803a8c34cb4583c",
        "short_hash": "cb294274",
        "subject": "fix: splice only summary output into compacted context, not new_messages()",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-23"
      },
      {
        "hash": "e2862642d4e0d34e833299b687693fa1df567249",
        "short_hash": "e2862642",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-23"
      },
      {
        "hash": "b519df918aaebf1986d2c0e71c4d00fdc6780dc5",
        "short_hash": "b519df91",
        "subject": "feat: inject sub-agent identity/depth prompt to deter recursive delegation",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-23"
      },
      {
        "hash": "18cc3e39436924c9efba54bace8333582e8ab38f",
        "short_hash": "18cc3e39",
        "subject": "chore: bump version [ci skip]",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-22"
      },
      {
        "hash": "90fde59962697e0482b2daa939144d85447c656d",
        "short_hash": "90fde599",
        "subject": "feat: resume interrupted goals by UUID (#657)",
        "author": "Pierce Brookins",
        "date": "2026-07-22"
      },
      {
        "hash": "df0b6c3e78ec102edb16e4be36cf7c27179a5000",
        "short_hash": "df0b6c3e",
        "subject": "feat(config): add puppy_token provider hook for plugin-based credential backends (#666)",
        "author": "Greg Kinne",
        "date": "2026-07-22"
      },
      {
        "hash": "8d6fb6b2e56485a58aaed499d2f1963bbd038030",
        "short_hash": "8d6fb6b2",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-21"
      },
      {
        "hash": "350c5c66b934472a3a25ab403dda2c82f8d9b169",
        "short_hash": "350c5c66",
        "subject": "feat: cap nested sub-agent invocation depth (#662)",
        "author": "TJ",
        "date": "2026-07-21"
      },
      {
        "hash": "25bf282e5c6f20899492107844988659b77f81f0",
        "short_hash": "25bf282e",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-21"
      },
      {
        "hash": "4c6fd35a16af41fc43c5cecf92f1d093725cbfcf",
        "short_hash": "4c6fd35a",
        "subject": "Merge pull request #663 from AndrewTilson/fix/subagent-panel-root-eviction-and-browser-cleanup-hang",
        "author": "Andrew Tilson",
        "date": "2026-07-21"
      },
      {
        "hash": "3f9149069335f52c7db1011cd7daf756204d35da",
        "short_hash": "3f914906",
        "subject": "fix: subagent_panel root eviction + browser_close cleanup hang",
        "author": "Andrew Tilson",
        "date": "2026-07-21"
      },
      {
        "hash": "0514fa4fd5d1aeb8b899d794cf797759f1100a90",
        "short_hash": "0514fa4f",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-21"
      },
      {
        "hash": "6faab5052dc5b93c3a63dfaa48135897e6a82a0e",
        "short_hash": "6faab505",
        "subject": "fix: make OpenAI reasoning settings per-model",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-21"
      },
      {
        "hash": "a1cc28cd9002b2ddfea4961082b12f52266f6979",
        "short_hash": "a1cc28cd",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-21"
      },
      {
        "hash": "ccea8af4835507373fd84996666886b489ea2212",
        "short_hash": "ccea8af4",
        "subject": "fix: coordinate JediTerm inline streaming output",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-21"
      },
      {
        "hash": "67b3957c93ad77e7b030e2c29925ea1f322f2009",
        "short_hash": "67b3957c",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-21"
      },
      {
        "hash": "ecd9d5ff58b4e85cf78307a783529ff3ec5877fa",
        "short_hash": "ecd9d5ff",
        "subject": "chore: bump patch version to 0.0.653",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-21"
      },
      {
        "hash": "5ce59755116b81e63f95b3d1d21aaffcf77aba4c",
        "short_hash": "5ce59755",
        "subject": "feat: gate GPT-5.6 family models behind per-tool guardrails (#648)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-21"
      },
      {
        "hash": "ce12fe70591e679d2a689e54873acef9778867c1",
        "short_hash": "ce12fe70",
        "subject": "feat: add Codex OAuth image generation",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-21"
      },
      {
        "hash": "f0dab86655577094868b9ed3114038242b946d39",
        "short_hash": "f0dab866",
        "subject": "feat: add GPT-5.6 reasoning context and mode",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-20"
      },
      {
        "hash": "0aa91c28963d65fe50f66590b67a5b05ff436e26",
        "short_hash": "0aa91c28",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-20"
      },
      {
        "hash": "0d819949e7e4f824b3388e7472d1d19c76f86d53",
        "short_hash": "0d819949",
        "subject": "feat: default to summarization compaction (#651)",
        "author": "Pierce Brookins",
        "date": "2026-07-20"
      },
      {
        "hash": "267012713be58c0edec4cb575a68e3f0e2b666b2",
        "short_hash": "26701271",
        "subject": "feat(i18n): extract config_commands.py user-facing strings (#647)",
        "author": "TJ",
        "date": "2026-07-20"
      },
      {
        "hash": "37c78a61ab29ed0b6f4ab65ff3098f87310ea1d3",
        "short_hash": "37c78a61",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-19"
      },
      {
        "hash": "0ed6911be92a90286a6160cd4800374a84b17d13",
        "short_hash": "0ed6911b",
        "subject": "test: fix 5 stale tests broken by empty-by-default models.json",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-19"
      },
      {
        "hash": "df6d2362c3326a3486e787de6958eb73e853858b",
        "short_hash": "df6d2362",
        "subject": "fix: force UTF-8 through the exec-command pipe (Windows cp1252 crash)",
        "author": "weegens-aaron",
        "date": "2026-07-18"
      },
      {
        "hash": "dd92c1321aaa9dd184fcf412e6a9c92e8f667f7d",
        "short_hash": "dd92c132",
        "subject": "feat(i18n): extract cli_runner.py user-facing strings (PUP-480) (#646)",
        "author": "TJ",
        "date": "2026-07-18"
      },
      {
        "hash": "80d347bb22e02b02bfcb30bcbb5b4985d9fe9744",
        "short_hash": "80d347bb",
        "subject": "feat(i18n): static extraction audit tool for CLI strings (#645)",
        "author": "TJ",
        "date": "2026-07-18"
      },
      {
        "hash": "b8c8055b7fe9bdaab3792611756f16206d064e1a",
        "short_hash": "b8c8055b",
        "subject": "fix(i18n): stop routing Latin American Spanish through removed es-419 (#644)",
        "author": "TJ",
        "date": "2026-07-18"
      },
      {
        "hash": "fad8955be054ad3eb26d9efe1fef2ebeb013ced4",
        "short_hash": "fad8955b",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-18"
      },
      {
        "hash": "b4c493418de9fa83873ca997e31c552cac1dee27",
        "short_hash": "b4c49341",
        "subject": "style: apply ruff formatting",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-18"
      },
      {
        "hash": "9104eb06f5ed815b424455c80fb69905239f8ac9",
        "short_hash": "9104eb06",
        "subject": "Pr 518 Add Flux (#643)",
        "author": "Luc M",
        "date": "2026-07-18"
      },
      {
        "hash": "321b9aae320803ae3edbecc6f17d1ddb8489fa18",
        "short_hash": "321b9aae",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-18"
      },
      {
        "hash": "7ee8949e33051a78b35919833f622d6d818b572f",
        "short_hash": "7ee8949e",
        "subject": "chore: bump version to 0.0.648",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-18"
      },
      {
        "hash": "366b3078942aa776a4e20b6a59e373f2b486294f",
        "short_hash": "366b3078",
        "subject": "fix: request 1h prompt-cache TTL for claude-code-* OAuth models (#640)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-18"
      },
      {
        "hash": "bf3b5af5db7035fe69f2462983f881a76c0e7986",
        "short_hash": "bf3b5af5",
        "subject": "Fix /cd autocomplete for bare tilde home paths (#638)",
        "author": "Bill Kramme",
        "date": "2026-07-18"
      },
      {
        "hash": "e14d3a575a7247b7f8de2e01ed6884abc016fd80",
        "short_hash": "e14d3a57",
        "subject": "fix: resolve git worktrees to main repo wing in kennel (#516)",
        "author": "Amit Jain",
        "date": "2026-07-18"
      },
      {
        "hash": "939e1d2cf4b0b9c1b2145221cee84e8f39d39db1",
        "short_hash": "939e1d2c",
        "subject": "Polish base Spanish catalog and deprecate es-419 (#639)",
        "author": "ellysarai13-blip",
        "date": "2026-07-18"
      },
      {
        "hash": "6463e7a5ff1ff8a44c1514ff816566ba557b8f02",
        "short_hash": "6463e7a5",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-18"
      },
      {
        "hash": "b885e18d26d97ef47d9fbcb3b68314765991f57e",
        "short_hash": "b885e18d",
        "subject": "Merge pull request #642 from mpfaffenberger/bugfix/headless-prompt-fix",
        "author": "Demise",
        "date": "2026-07-17"
      },
      {
        "hash": "7fa497d87eebccc4d16aa2f9ecc5684694b75be3",
        "short_hash": "7fa497d8",
        "subject": "fix(cli): harden headless session autosaves",
        "author": "Wes Blakemore",
        "date": "2026-07-17"
      },
      {
        "hash": "880e961ac025a831c3d40f421999c8c13ca5cb88",
        "short_hash": "880e961a",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-18"
      },
      {
        "hash": "a6c65e58e05d82c87807d9cc8d6892067e44b1c8",
        "short_hash": "a6c65e58",
        "subject": "Merge pull request #641 from mpfaffenberger/bugfix/plugin-skills-cache-race",
        "author": "Demise",
        "date": "2026-07-17"
      },
      {
        "hash": "a2ac597cf829eae8d1f37ef0a5a704815259ec06",
        "short_hash": "a2ac597c",
        "subject": "fix: reuse plugin-skills cache when registrations unchanged",
        "author": "Wes Blakemore",
        "date": "2026-07-17"
      },
      {
        "hash": "f15efb7ac3c98e43b1e608f6b8718e16e4bec67d",
        "short_hash": "f15efb7a",
        "subject": "Merge remote-tracking branch 'origin/main' into bugfix/plugin-skills-cache-race",
        "author": "Wes Blakemore",
        "date": "2026-07-17"
      },
      {
        "hash": "13daf5a80e5bbbc7fb7d90c83028c25e7809c506",
        "short_hash": "13daf5a8",
        "subject": "fix(cli): persist and dispatch headless prompts",
        "author": "Wes Blakemore",
        "date": "2026-07-17"
      },
      {
        "hash": "15e435d86dcdfd5cce5c5e923b98c7af0e2f2ade",
        "short_hash": "15e435d8",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-17"
      },
      {
        "hash": "e1df387824421c4f501fe5b132e1b23244034af1",
        "short_hash": "e1df3878",
        "subject": "Merge pull request #636 from mpfaffenberger/bugfix/subagent-output",
        "author": "Demise",
        "date": "2026-07-17"
      },
      {
        "hash": "bc2a459b8cd2f69490d129c5c31b970f8d77d251",
        "short_hash": "bc2a459b",
        "subject": "fix: serialize plugin-skills cache rebuild to stop concurrent-discovery crash",
        "author": "Wes Blakemore",
        "date": "2026-07-17"
      },
      {
        "hash": "153063b359b303bf95f36e094a2a2d5e91c17a44",
        "short_hash": "153063b3",
        "subject": "fix: clamp sub-agent panel to terminal height with +N more overflow",
        "author": "Wes Blakemore",
        "date": "2026-07-16"
      },
      {
        "hash": "80e053ce83b0b2943c449f6d15067452ca545f6b",
        "short_hash": "80e053ce",
        "subject": "Merge remote-tracking branch 'origin/main' into bugfix/subagent-output",
        "author": "Wes Blakemore",
        "date": "2026-07-16"
      },
      {
        "hash": "559f43c2333f59b003e12933290641d665b36fb9",
        "short_hash": "559f43c2",
        "subject": "chore: bump version to 0.0.644 [ci skip]",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-16"
      },
      {
        "hash": "b9f5d12aa46f3becab8047585d3a089263d31f1a",
        "short_hash": "b9f5d12a",
        "subject": "fix: show all sub-agent panel rows",
        "author": "Wes Blakemore",
        "date": "2026-07-16"
      },
      {
        "hash": "be4d89f2369aa6c3eabedba12411a5dc169b8a7e",
        "short_hash": "be4d89f2",
        "subject": "Merge pull request #634 from AndrewTilson/awtilso/fix-post-tool-call-subagent-guard",
        "author": "Andrew Tilson",
        "date": "2026-07-16"
      },
      {
        "hash": "ecfdf2cfcdef33486d0b7203dbee6c02bf8d35be",
        "short_hash": "ecfdf2cf",
        "subject": "fix(run_stats): guard _on_post_tool_call on is_subagent()",
        "author": "Andrew Tilson - awtilso",
        "date": "2026-07-16"
      },
      {
        "hash": "1c4d7af08b171c3b694f5f41b40753e0f10a3c9e",
        "short_hash": "1c4d7af0",
        "subject": "feat: normalize oversized image file attachments to match clipboard resize policy (#632)",
        "author": "Bill Kramme",
        "date": "2026-07-16"
      },
      {
        "hash": "2d03b25213ff919dfd4cc71669b207dff4d1e964",
        "short_hash": "2d03b252",
        "subject": "fix(ui): cell-clip inline bar rows so JediTerm wrap can't desync the block (#633)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-16"
      },
      {
        "hash": "bc270e4fd7fb7d682aabf6cf5093657e63fd1336",
        "short_hash": "bc270e4f",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-16"
      },
      {
        "hash": "44d47a107f894ef45f9a41923c7831da8f61df09",
        "short_hash": "44d47a10",
        "subject": "Extend the token usage data reported through agent_run_end hook (#630)",
        "author": "dmontroy",
        "date": "2026-07-16"
      },
      {
        "hash": "a5ee37aeb6faf71f87a4dde8e69aedd1887fd528",
        "short_hash": "a5ee37ae",
        "subject": "fix: terminal outputs raw text on code blocks (#629)",
        "author": "Carlos Casellas Garza",
        "date": "2026-07-16"
      },
      {
        "hash": "888a48e7e71cf814868e9e154f5c04015e0b3af4",
        "short_hash": "888a48e7",
        "subject": "feat(ui): add DECSTBM-free inline prompt surface for JetBrains terminals (#631)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-16"
      },
      {
        "hash": "b5425561c6bc5f2df6bdb6f1f0a315f7e7a15e36",
        "short_hash": "b5425561",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-16"
      },
      {
        "hash": "c868f00954b555f868dd6b4c4baa8fc6ba474823",
        "short_hash": "c868f009",
        "subject": "feat(i18n): internationalization foundation + first extraction batch (#617)",
        "author": "TJ",
        "date": "2026-07-15"
      },
      {
        "hash": "5cc06f6356e4e187c7d68dd89ad1f9df50af111d",
        "short_hash": "5cc06f63",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-15"
      },
      {
        "hash": "ec88daf1a1f9e34968a71b030a111f913240ff83",
        "short_hash": "ec88daf1",
        "subject": "feat: add custom OpenAI Responses model type (#628)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-15"
      },
      {
        "hash": "f317ad4af0b3060b40220c7ee92358f7f377671c",
        "short_hash": "f317ad4a",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-15"
      },
      {
        "hash": "f9e387b63edc13b4c07c57cfbfcdcf194af490c4",
        "short_hash": "f9e387b6",
        "subject": "fix(mcp): propagate SSL_CERT_FILE into stdio server child env (#614)",
        "author": "Brian Reed",
        "date": "2026-07-14"
      },
      {
        "hash": "bfbf762a38ad9267de1d05e6f7fe6765cf829dd7",
        "short_hash": "bfbf762a",
        "subject": "feat(retry): selectable, guard-railed retry profiles (per-role + per-model) (#619)",
        "author": "Julien Ellie",
        "date": "2026-07-14"
      },
      {
        "hash": "9ddf56d9ed64941751d0a5a02a57198938e843dc",
        "short_hash": "9ddf56d9",
        "subject": "feat(mcp): support trust-gated project-level MCP server configs (#615)",
        "author": "Rogerio (Rio) Moura",
        "date": "2026-07-14"
      },
      {
        "hash": "3fba59f16bf67094e369be9c3993d6f95b2c5a2b",
        "short_hash": "3fba59f1",
        "subject": "feat: support OAuth callback paste-back (#618)",
        "author": "Andrew Vuong",
        "date": "2026-07-14"
      },
      {
        "hash": "7a17abf4c7673151497fdf80639e7f672450ec7a",
        "short_hash": "7a17abf4",
        "subject": "fix(editor): Enter submits a fully-typed slash command in one press (#621)",
        "author": "Julien Ellie",
        "date": "2026-07-14"
      },
      {
        "hash": "391b6fd21c3e4d3e9c9b87dee562d8021c8a71f6",
        "short_hash": "391b6fd2",
        "subject": "fix(azure_foundry): disable reasoning ID replay for GPT-5.x models (#624)",
        "author": "Rickey Shideler",
        "date": "2026-07-14"
      },
      {
        "hash": "b1bc322094d121ca2e4ebc28d8d44a1b51eef6d2",
        "short_hash": "b1bc3220",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-14"
      },
      {
        "hash": "997ae0d334b68f588ce5b766c57377a957387945",
        "short_hash": "997ae0d3",
        "subject": "Feat/oss secret store (#531)",
        "author": "Greg Kinne",
        "date": "2026-07-14"
      },
      {
        "hash": "5e13b6be2950975a95528e34db1337ba4081c612",
        "short_hash": "5e13b6be",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-14"
      },
      {
        "hash": "44a78b52bf55f3eef737be3820e132bea71862ec",
        "short_hash": "44a78b52",
        "subject": "fix: distinguish GPT 5.6 agent panel variants (#622)",
        "author": "Demise",
        "date": "2026-07-14"
      },
      {
        "hash": "284c6943a9b281f64a4ddb7a2076edd3c93f46fc",
        "short_hash": "284c6943",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-13"
      },
      {
        "hash": "27547b839fd7e639bdfbbd667183a64d831c78d0",
        "short_hash": "27547b83",
        "subject": "fix(retry): retry in-band SSE 5xx (gateway 502 over 200 stream) + wrap sub-agent runs + widen retry spacing (#616)",
        "author": "Julien Ellie",
        "date": "2026-07-13"
      },
      {
        "hash": "36fb5228462e7734f0df45a247dd2213c938df76",
        "short_hash": "36fb5228",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-12"
      },
      {
        "hash": "47761debfdc43307293e7107a796310fd9f46a76",
        "short_hash": "47761deb",
        "subject": "ci: disable MiniMax thinking for OCR",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "5abd608a4c709b189d1b2e9957f9eaff9e886d74",
        "short_hash": "5abd608a",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-12"
      },
      {
        "hash": "907dd355617fe98f09f3652a58b2940e12ff6857",
        "short_hash": "907dd355",
        "subject": "ci: allow slow OCR model reviews",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "c9b1ccf5585826f69a48c1f0f514950175a640df",
        "short_hash": "c9b1ccf5",
        "subject": "ci: add maintainer-triggered OCR reviews",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "2af48b1adb5a90f0fe43b7482591b76e272348a2",
        "short_hash": "2af48b1a",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-11"
      },
      {
        "hash": "075393dd7c2de31a5fd38c6a5e99bcaf51a5250a",
        "short_hash": "075393dd",
        "subject": "Manually increment version to satisfy PyPI",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "5f19391255faba458a06340945c1f15166271a22",
        "short_hash": "5f193912",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-11"
      },
      {
        "hash": "d11c6c9de81e41bd4718cd90cbb3dbe75cef52d2",
        "short_hash": "d11c6c9d",
        "subject": "chore: trigger release build",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "1f2c500590d9e9b27531e478ef6e6b1e9fb9d580",
        "short_hash": "1f2c5005",
        "subject": "chore: bump version [ci skip]",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "782e597eaad67f1fbfbccac764b42b48648acc65",
        "short_hash": "782e597e",
        "subject": "Fix CI model provisioning for releases",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "0b9b7bfebf10cb980a9df4bdb4019f868fda79a6",
        "short_hash": "0b9b7bfe",
        "subject": "Theme the shared tool selector TUIs (#601)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "ea2e3add9c650b72434a4119d4fb8a8ea8106f67",
        "short_hash": "ea2e3add",
        "subject": "Theme the ask-user-question TUI (#600)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "64ae3ff4f8f2d5dc3e407df3b1b7779169523f8b",
        "short_hash": "64ae3ff4",
        "subject": "Theme the theme picker TUI (#599)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "5bcac8c4012ea08b64512085017daea8baa4483c",
        "short_hash": "5bcac8c4",
        "subject": "Theme the steer queue TUI (#598)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "ff31255770d7454865d805e3d3b9398ccf25d7ee",
        "short_hash": "ff312557",
        "subject": "Theme the spinner picker TUI (#597)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "953b978ae2fb0713e04e25866af8a224d2f9b261",
        "short_hash": "953b978a",
        "subject": "Theme the prune TUI (#596)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "07aece03f6dd02b0a86613c01167354dcf58be3c",
        "short_hash": "07aece03",
        "subject": "Theme the plugin manager TUI (#595)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "49cd74b5e0aad24639bc960be38a302c072cff9f",
        "short_hash": "49cd74b5",
        "subject": "Theme the hook manager TUI (#594)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "c64c71420ae34e05f1587fc2528574120d84203c",
        "short_hash": "c64c7142",
        "subject": "Theme the skills installer TUI (#593)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "23159d705bfe6c1b8cec6f690ecf9b9b492324c5",
        "short_hash": "23159d70",
        "subject": "Theme the skills manager TUI (#592)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "923942d88ae650e2d9729b8e30dd509091b6195f",
        "short_hash": "923942d8",
        "subject": "Theme the Universal Constructor TUIs (#591)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "9238678855b3ab06c553b319562bec9b0c25ebbd",
        "short_hash": "92386788",
        "subject": "Theme the onboarding wizard TUI (#590)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "ecd2dae32f8c899ea571a9f5e6ad2955b860057a",
        "short_hash": "ecd2dae3",
        "subject": "Theme the MCP custom-server form TUI (#589)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "f6af7b4bc0feff245a55a9c8397876e7d770100f",
        "short_hash": "f6af7b4b",
        "subject": "Theme the /mcp install TUI (#588)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "f434573587364e7abd7838c8ef7269880e2bfa3a",
        "short_hash": "f4345735",
        "subject": "Theme the MCP binding TUIs (#587)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "fb32dfe27752e6b8f868db0e677b44dcf71460e9",
        "short_hash": "fb32dfe2",
        "subject": "Theme the judges TUIs (#586)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "f500faf9f2a4f4d8d4c2f455bbe2c6cc37102ccc",
        "short_hash": "f500faf9",
        "subject": "Theme the diff selector TUI (#585)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "9316742d3bbd2cc2ba4c5fbf54572f14bacd9845",
        "short_hash": "9316742d",
        "subject": "Theme the /colors TUI (#584)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "62b541bc3335c70e0a887aa525d23db570918f6e",
        "short_hash": "62b541bc",
        "subject": "Theme the /set TUI (#583)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "12e0a286818ee6e9ed7454e4b126df270a17d26f",
        "short_hash": "12e0a286",
        "subject": "Theme the /resume TUI (#582)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "769130e2d37c5d5d84644d4cffb16c5f73d0373c",
        "short_hash": "769130e2",
        "subject": "Theme the add-model TUI (#581)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "e9c860c00cc8a39b9054c56e633616f080af5162",
        "short_hash": "e9c860c0",
        "subject": "Theme the model settings TUI (#580)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "9dbc084d0a39561143bea7e02cb58c0e01070b01",
        "short_hash": "9dbc084d",
        "subject": "Theme the /model picker TUI (#579)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "9888305d95aab97512467af5c4d2c268866314d6",
        "short_hash": "9888305d",
        "subject": "Theme the /agent TUI (#578)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "e904b1870c215ecfdbdbead01a112684fa5e2869",
        "short_hash": "e904b187",
        "subject": "Centralize prompt-toolkit semantic theme roles (#577)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "d7c427da00711065abe12a15aa956e88b785abbf",
        "short_hash": "d7c427da",
        "subject": "Make prompt-toolkit TUIs theme aware",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "79db63facfcbada3c5f80ff1ebd680b6d285f037",
        "short_hash": "79db63fa",
        "subject": "fix(terminal): disable XON/XOFF while persistent editor owns tty",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "988023183348dbc74ebfbff200469d1566421be7",
        "short_hash": "98802318",
        "subject": "Make terminal rendering fully theme aware",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "2413e88dcb95ce2a89ffc6e3fd81de75f3665c8d",
        "short_hash": "2413e88d",
        "subject": "Isolate pytest from user XDG config",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "12448d7a438b660e43f0efa74795f34c43266812",
        "short_hash": "12448d7a",
        "subject": "Make diff and prompt colors theme-aware",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "b9a73df7338217c98a1a4a49751b7a10ceeedcf1",
        "short_hash": "b9a73df7",
        "subject": "feat: add runtime yolo CLI override (#551)",
        "author": "Andrew C. Oliver",
        "date": "2026-07-11"
      },
      {
        "hash": "80502c8cdcb3c31d826e5b2ddbf527d9fd650804",
        "short_hash": "80502c8c",
        "subject": "Revert \"Add runtime YOLO CLI override\"",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "e8cb918aabcef6db6765e89556f9a35829402671",
        "short_hash": "e8cb918a",
        "subject": "Add runtime YOLO CLI override",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-11"
      },
      {
        "hash": "f38c66a07dce6a2c16afba27e992db739b699d7e",
        "short_hash": "f38c66a0",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-10"
      },
      {
        "hash": "6e223f3842b1ab915687fa323d826373a026ed1c",
        "short_hash": "6e223f38",
        "subject": "fix(fork): complete detached agent lifecycle",
        "author": "mpfaffenberger",
        "date": "2026-07-10"
      },
      {
        "hash": "24bb58054aee386a738e8bffcffcd0377f774bdb",
        "short_hash": "24bb5805",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-10"
      },
      {
        "hash": "e96753645e3224a371ad347ab82429fdea95d8ea",
        "short_hash": "e9675364",
        "subject": "Revert \"fix(windows): disable VT input under Wave Terminal\"",
        "author": "mpfaffenberger",
        "date": "2026-07-10"
      },
      {
        "hash": "2a5157f5d294a09e135cdb34820c014bb2ec2da6",
        "short_hash": "2a5157f5",
        "subject": "feat(diff): derive default highlights from active theme",
        "author": "mpfaffenberger",
        "date": "2026-07-10"
      },
      {
        "hash": "269ff2d9037dbd6d9fb442ce0aa19d21bfc9b827",
        "short_hash": "269ff2d9",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-10"
      },
      {
        "hash": "67c159c06f95c1b66dd0ec7994607ad7ed1d82dc",
        "short_hash": "67c159c0",
        "subject": "fix(windows): disable VT input under Wave Terminal",
        "author": "mpfaffenberger",
        "date": "2026-07-10"
      },
      {
        "hash": "0ce1cefc486943591796c843c4174e18c06f3fd5",
        "short_hash": "0ce1cefc",
        "subject": "fix(statusline): cross-platform Windows support + Unicode crash prevention (#548)",
        "author": "Luis Alejandro Rincon",
        "date": "2026-07-10"
      },
      {
        "hash": "fd69a12e7eb34ac7de194219d7446d34508eea17",
        "short_hash": "fd69a12e",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-10"
      },
      {
        "hash": "634ea3103328a52026c11cd998d2319f6705a0c7",
        "short_hash": "634ea310",
        "subject": "fix(skills): demote missing-skill-path warnings to debug",
        "author": "mpfaffenberger",
        "date": "2026-07-10"
      },
      {
        "hash": "7725fa1f0e6bbd76721e40769082dc0d4cd5cb5b",
        "short_hash": "7725fa1f",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-10"
      },
      {
        "hash": "db62a4db881464f81476df5b2071c8415eea1151",
        "short_hash": "db62a4db",
        "subject": "feat: calm OAuth pages and refine queued banner",
        "author": "mpfaffenberger",
        "date": "2026-07-10"
      },
      {
        "hash": "52095fd8ca4c1dc5684ea2499fee724bf5330c60",
        "short_hash": "52095fd8",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-10"
      },
      {
        "hash": "ff3fdfe3a18cdcbbf08613c3b22c05a28800b9f3",
        "short_hash": "ff3fdfe3",
        "subject": "feat(callbacks): let run_shell_command hooks rewrite the command (#545)",
        "author": "Ashish Singhi",
        "date": "2026-07-10"
      },
      {
        "hash": "6e60cd1af86af25533d0aa8736576870ad9f7366",
        "short_hash": "6e60cd1a",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-10"
      },
      {
        "hash": "bda3b66d59b904457c3c3a7fa955269104217071",
        "short_hash": "bda3b66d",
        "subject": "fix(retry): retry gateway 502s wrapped in ExceptionGroup instead of crashing (#546)",
        "author": "Julien Ellie",
        "date": "2026-07-10"
      },
      {
        "hash": "460c821c0f60449c828a3cb3aae8932863303eb1",
        "short_hash": "460c821c",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-10"
      },
      {
        "hash": "521460bd5378e61ea6f2076effe37f85f6f1132a",
        "short_hash": "521460bd",
        "subject": "test: include queued emitter in messaging exports",
        "author": "mpfaffenberger",
        "date": "2026-07-10"
      },
      {
        "hash": "651a2f74ee4ce472813ac0e8b2e5f58a83dd6a91",
        "short_hash": "651a2f74",
        "subject": "feat: improve queued turns and shell backgrounding",
        "author": "mpfaffenberger",
        "date": "2026-07-10"
      },
      {
        "hash": "27e04545403310069be7e76cafdd72ebf8b620b8",
        "short_hash": "27e04545",
        "subject": "feat: improve compaction flow and Codex usage status",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-10"
      },
      {
        "hash": "b0907def735fbc37e091e9210f22cf842330d29c",
        "short_hash": "b0907def",
        "subject": "refactor(ui): remove emojis from tool output",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-10"
      },
      {
        "hash": "b7388527afd9303c20d5d2a3ec919ff999735bed",
        "short_hash": "b7388527",
        "subject": "feat(queue): add full-screen prompt manager",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-10"
      },
      {
        "hash": "a01c85dbe2e8a9beaf737817a7cdd7ac14af5b5e",
        "short_hash": "a01c85db",
        "subject": "fix(chatgpt): align GPT-5.6 model capabilities",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-10"
      },
      {
        "hash": "df73f6ecc82831e8669406b8baf2d298dbbc1afa",
        "short_hash": "df73f6ec",
        "subject": "refactor(cli): simplify settings command surfaces",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-10"
      },
      {
        "hash": "322cae765ae639f9dffdf530b5c16b94741486df",
        "short_hash": "322cae76",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-10"
      },
      {
        "hash": "e00b88b664b881890d0e2b7ad5019379e2d9f9b0",
        "short_hash": "e00b88b6",
        "subject": "feat(theme): add accessible theme-aware terminal styling",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-09"
      },
      {
        "hash": "fae09a99f6deb55669ae9c598f11233709a141db",
        "short_hash": "fae09a99",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-09"
      },
      {
        "hash": "9f0855bbe854fcbf77bc8c03b761982ff72460fa",
        "short_hash": "9f0855bb",
        "subject": "fix(herdr): report agent state authoritatively from a single choke-point (#537)",
        "author": "Julien Ellie",
        "date": "2026-07-09"
      },
      {
        "hash": "490a2160341a863faddf9f38fb2726986c6aaa30",
        "short_hash": "490a2160",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-09"
      },
      {
        "hash": "95b17535641ffc4e1404394e476ee146a6bbf927",
        "short_hash": "95b17535",
        "subject": "feat: native Agent Client Protocol (ACP) agent + host-agnostic FileSystemBackend seam (#536)",
        "author": "Julien Ellie",
        "date": "2026-07-09"
      },
      {
        "hash": "ed95b19baa99732995e1fbac98e14055c20778f4",
        "short_hash": "ed95b19b",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-09"
      },
      {
        "hash": "c308b040041633bbacda2a20a661d3517073d7b4",
        "short_hash": "c308b040",
        "subject": "feat(ask_user_question): support clipboard paste in Other option (#538)",
        "author": "Balajikumar Murugan",
        "date": "2026-07-09"
      },
      {
        "hash": "32d27fd4ecd4edbaeaad1ce149113dfa09b8c710",
        "short_hash": "32d27fd4",
        "subject": "fix: assorted robustness fixes (Windows encoding, pid guard, MCP config guard, configurable shell timeout) (#542)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-09"
      },
      {
        "hash": "f6c87def87ab83d359786aad6c597870665244fd",
        "short_hash": "f6c87def",
        "subject": "feat(plugins): lock_builtin_plugins deployment lock (#541)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-09"
      },
      {
        "hash": "a044371bc41ccd662b34bb2c34a94c86902628ed",
        "short_hash": "a044371b",
        "subject": "feat(callbacks): post_autosave phase fix, shell-output hook, async file-permission path (#540)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-09"
      },
      {
        "hash": "7cc6deb394e772bd24df21e263621863273ec293",
        "short_hash": "7cc6deb3",
        "subject": "feat(subagent): track full sub-agent invocation chain (#539)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-09"
      },
      {
        "hash": "5762344cfa5f73378b9b32b0f61504936554f82f",
        "short_hash": "5762344c",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-09"
      },
      {
        "hash": "1aa6619a71bd13978d446252274add593c2c07a9",
        "short_hash": "1aa6619a",
        "subject": "fix(thinking): filter empty HTML comment separators",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-09"
      },
      {
        "hash": "c659bbc61f393062b4524a268b4387ca41f449c1",
        "short_hash": "c659bbc6",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-09"
      },
      {
        "hash": "52f7cb68069e153fd8f8c21423fc9585c9943c58",
        "short_hash": "52f7cb68",
        "subject": "Add ChatGPT GPT-5.6 OAuth models (#543)",
        "author": "Pierce Brookins",
        "date": "2026-07-09"
      },
      {
        "hash": "ed73cfcb031a3a29d9093ad36557fd3b31304360",
        "short_hash": "ed73cfcb",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-09"
      },
      {
        "hash": "321485fa517a9be516e0a8c5a7f5f4a8fb4eb2ba",
        "short_hash": "321485fa",
        "subject": "fix(shell): stop killpg from nuking pytest/CI runner's own process group",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-09"
      },
      {
        "hash": "6815bd5d31cb28443e349ae4fee4d5349ebdbc90",
        "short_hash": "6815bd5d",
        "subject": "test: fix flaky test_tab_then_enter_accepts_cycled_selection",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-09"
      },
      {
        "hash": "9d3acafd2f6748656699d0ac74ce55cece76b3a3",
        "short_hash": "9d3acafd",
        "subject": "Add Ctrl+X keyboard chords for editor launch and shell kill/background",
        "author": "mpfaffenberger",
        "date": "2026-07-09"
      },
      {
        "hash": "81248816ebecee461429a55b73099e8dea2be2ec",
        "short_hash": "81248816",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-09"
      },
      {
        "hash": "df3655920bfae8e1be1b4324ef6082b27d9d6b4b",
        "short_hash": "df365592",
        "subject": "refactor(session): drop session labels and named/auto section split",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-08"
      },
      {
        "hash": "e8231290c0c6da0ac48febc4a69508305a0e9232",
        "short_hash": "e8231290",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-08"
      },
      {
        "hash": "b967057dcb954fe0c37dee0a90e527b804a4e4c6",
        "short_hash": "b967057d",
        "subject": "feat(grok_oauth): add Grok (x.ai) OAuth plugin with browser auth flow",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-08"
      },
      {
        "hash": "d22ae7ad898af9ca259b1f73b94494d556739524",
        "short_hash": "d22ae7ad",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-08"
      },
      {
        "hash": "367bef66c56ae29f48407cdd5f33e853eb80a485",
        "short_hash": "367bef66",
        "subject": "fix(windows): enable VT input so Ctrl+V image paste reaches the app",
        "author": "mpfaffenberger",
        "date": "2026-07-08"
      },
      {
        "hash": "4ba94e0b22b77f5d76df41d21cfaf508ef24841c",
        "short_hash": "4ba94e0b",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-08"
      },
      {
        "hash": "5a37b86d3b2c6a4b42ea5f902c8ddcb91e011971",
        "short_hash": "5a37b86d",
        "subject": "Add transcript guard for safe message streaming",
        "author": "mpfaffenberger",
        "date": "2026-07-08"
      },
      {
        "hash": "04f6c22eda992f2650ec52b18f98ff8fe8cd02b5",
        "short_hash": "04f6c22e",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-08"
      },
      {
        "hash": "aa7305f47250a30494eec505ad6b1a7d4057bb54",
        "short_hash": "aa7305f4",
        "subject": "fix(shell): isolate Windows shell children from our console",
        "author": "mpfaffenberger",
        "date": "2026-07-08"
      },
      {
        "hash": "6445d85787b70f1b318004966bf8b3e14333ce5f",
        "short_hash": "6445d857",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-08"
      },
      {
        "hash": "ab19d307affd675854071147e561cbc04d37b768",
        "short_hash": "ab19d307",
        "subject": "fix(windows): revert Ctrl+C ignore flag, add active console-mode healing",
        "author": "mpfaffenberger",
        "date": "2026-07-08"
      },
      {
        "hash": "b71b0f7bd31e4c1909ac67410dc423662c462a93",
        "short_hash": "b71b0f7b",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-08"
      },
      {
        "hash": "4d647ec3b6a55791809eac44fcfe07aff0093f66",
        "short_hash": "4d647ec3",
        "subject": "feat(cancel): make Ctrl+C a pure keybinding on every platform",
        "author": "mpfaffenberger",
        "date": "2026-07-08"
      },
      {
        "hash": "5689a6ce2e2e7777f2c522f84e21301d405517b0",
        "short_hash": "5689a6ce",
        "subject": "feat(fork): /fork command for fire-and-forget background sub-agents",
        "author": "mpfaffenberger",
        "date": "2026-07-08"
      },
      {
        "hash": "ab2f110afb68c2a5eb080d6044a278db43dbf2a1",
        "short_hash": "ab2f110a",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-07"
      },
      {
        "hash": "6af98ed20d0c0d328ec37cb0d041b0dc1d8a0fb3",
        "short_hash": "6af98ed2",
        "subject": "chore: bump version to 0.0.607",
        "author": "mpfaffenberger",
        "date": "2026-07-07"
      },
      {
        "hash": "7ec18cb769825873c3606902ffb4680eee4ee65e",
        "short_hash": "7ec18cb7",
        "subject": "polish(cancel): key-agnostic banner + swarm-stop regression test",
        "author": "mpfaffenberger",
        "date": "2026-07-07"
      },
      {
        "hash": "c9b3ba96aa371522bde28428ed680f23c58155ea",
        "short_hash": "c9b3ba96",
        "subject": "fix(windows): make Ctrl+C cancel work during shell commands",
        "author": "mpfaffenberger",
        "date": "2026-07-07"
      },
      {
        "hash": "12bc7e9219c3a973b1e596297620df9a925e45a8",
        "short_hash": "12bc7e92",
        "subject": "fix(windows): stop double-wrapping terminal-bracketed pastes (Ctrl+V images)",
        "author": "mpfaffenberger",
        "date": "2026-07-07"
      },
      {
        "hash": "eabcce35fcfc46c1327654276cf851440374efbd",
        "short_hash": "eabcce35",
        "subject": "test: fix no_tools env-var leak polluting later tests",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-06"
      },
      {
        "hash": "05ccd95dea665a16867cfccbf69576ae1a40c2cc",
        "short_hash": "05ccd95d",
        "subject": "feat: deterministic session labels from working context (#246)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-06"
      },
      {
        "hash": "469d40b33b80b0ca00a74c47e74c937b587cca82",
        "short_hash": "469d40b3",
        "subject": "fix: stop MCP custom server form leaking mouse-tracking escapes (#244)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-06"
      },
      {
        "hash": "3f2da58d3b16e68af5cda0568829b9e835488d3b",
        "short_hash": "3f2da58d",
        "subject": "feat: add --no-tools flag for pure text-in/text-out subprocess use (#182)",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-06"
      },
      {
        "hash": "f7b01fd12a938445924627d63665c800ea34fb6b",
        "short_hash": "f7b01fd1",
        "subject": "feat(theme): add Purple Puppy theme",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-06"
      },
      {
        "hash": "6b3f0d26a8223fc578fd64296371b650e8d9b9c8",
        "short_hash": "6b3f0d26",
        "subject": "fix(agents): serialize agent discovery and stop bogus JSON-agent shadow warnings",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-06"
      },
      {
        "hash": "284c57e6e1a2765143e356a1fc3d8022a5968df1",
        "short_hash": "284c57e6",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-06"
      },
      {
        "hash": "ce3569f0ab374bafecd676540f572180c2bcf766",
        "short_hash": "ce3569f0",
        "subject": "fix(tests): guard termios import so Windows collection survives",
        "author": "mpfaffenberger",
        "date": "2026-07-06"
      },
      {
        "hash": "b8cdafdd5a08a020bf6c5c6ef8597bbf8a2fe4d8",
        "short_hash": "b8cdafdd",
        "subject": "fix(windows): make Shift+Enter insert a newline",
        "author": "mpfaffenberger",
        "date": "2026-07-06"
      },
      {
        "hash": "183298ac8ce46bc009e586f32f3f0cdde6a93632",
        "short_hash": "183298ac",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-05"
      },
      {
        "hash": "ed75fffef6a0bd5963ec7e4877383da7e869445b",
        "short_hash": "ed75fffe",
        "subject": "fix(puppy_spinner): quicker classic puppy + gap before status text (#529)",
        "author": "Aaron Weegens",
        "date": "2026-07-05"
      },
      {
        "hash": "8693274db0513864e91434579d186d54dffa72f1",
        "short_hash": "8693274d",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-05"
      },
      {
        "hash": "1c681a27ca44c78a7b23a0a590448c786ef9d095",
        "short_hash": "1c681a27",
        "subject": "feat(puppy_spinner): customizable spinner styles via /spinner + spinners.json (#528)",
        "author": "Aaron Weegens",
        "date": "2026-07-05"
      },
      {
        "hash": "8f6e53cb2c65edb7c6fb7e2d71c3c3f0a9cf45ab",
        "short_hash": "8f6e53cb",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-05"
      },
      {
        "hash": "89bc4ad741c9449caa1c7ae8d74be9f55e6ffe2a",
        "short_hash": "89bc4ad7",
        "subject": "feat: require explicit user trust before loading project plugins (#527)",
        "author": "Aaron Weegens",
        "date": "2026-07-05"
      },
      {
        "hash": "19d8dfb4b7ccdcbda93f08e7dc72c64d683d9040",
        "short_hash": "19d8dfb4",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-05"
      },
      {
        "hash": "75f8461f3189fe15aaab7bc87b0597ace0c6d4b2",
        "short_hash": "75f8461f",
        "subject": "feat(key-listener): self-healing supervisor — recover instead of dying",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-05"
      },
      {
        "hash": "33ed85723264f3a93c646f6e6ce4812da5a08694",
        "short_hash": "33ed8572",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-05"
      },
      {
        "hash": "e7aec678e1397201f37c8cb6c7471cbf89cb1a61",
        "short_hash": "e7aec678",
        "subject": "fix(resilience): guard render paths; add stack_dump wedge forensics",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-05"
      },
      {
        "hash": "9f52cd05a9e18a75da0dedbc1a7654fb8ca3b9d1",
        "short_hash": "9f52cd05",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-05"
      },
      {
        "hash": "f3f92e882b121df090d37ede52e2d08273df3220",
        "short_hash": "f3f92e88",
        "subject": "fix(windows): make Ctrl+C cancel work everywhere; remove uvx workaround",
        "author": "mpfaffenberger",
        "date": "2026-07-05"
      },
      {
        "hash": "088fb257b2a14ee3b19e6a3acb96a6f01aea1169",
        "short_hash": "088fb257",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-05"
      },
      {
        "hash": "0a08abaa18ac171326009fe3537da576a831c703",
        "short_hash": "0a08abaa",
        "subject": "fix(autocomplete): Tab cycles menu; prompt rides output down on close",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-05"
      },
      {
        "hash": "3738c15ba555d7ce52e0f258351d8d6d50ba1545",
        "short_hash": "3738c15b",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-04"
      },
      {
        "hash": "b1157a99ab2e3926fafa9db73b4069f8175f076a",
        "short_hash": "b1157a99",
        "subject": "feat(plugins): add herdr integration plugin (#525)",
        "author": "Julien Ellie",
        "date": "2026-07-04"
      },
      {
        "hash": "7d790896bcdeffd590f97b5dba5d6337911d9cfe",
        "short_hash": "7d790896",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-04"
      },
      {
        "hash": "0adf162320ef95a40f01ca5c0b01a50e864a9e16",
        "short_hash": "0adf1623",
        "subject": "Revert \"fix(ui): tag transcript prompt echo with a USER banner (#524)\"",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-04"
      },
      {
        "hash": "c55d90801b19e5af4bba22e3ef8df9bfbd59152b",
        "short_hash": "c55d9080",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-04"
      },
      {
        "hash": "e796cde0873d692feed48a8b5f844f9a0c841872",
        "short_hash": "e796cde0",
        "subject": "feat(qa-kitten): prefer DOM locators for progression, reserve screenshots for visual validation (#521)",
        "author": "TJ",
        "date": "2026-07-04"
      },
      {
        "hash": "95108d9b04f2c5971fded8dd7baa5eefb0c7f4c4",
        "short_hash": "95108d9b",
        "subject": "fix(ui): tag transcript prompt echo with a USER banner (#524)",
        "author": "Aaron Weegens",
        "date": "2026-07-04"
      },
      {
        "hash": "2fe25caaf968693a9204a36c032f2bc4e14da153",
        "short_hash": "2fe25caa",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-04"
      },
      {
        "hash": "3d6d18c2f48ad0a0aab1cad718443b89b2cee966",
        "short_hash": "3d6d18c2",
        "subject": "fix(key-listener): prevent keystroke theft during steering, sub-agents, and /resume",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-04"
      },
      {
        "hash": "a18e9c3321f8aa38360c928937cef0c562da8b56",
        "short_hash": "a18e9c33",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-04"
      },
      {
        "hash": "de197a724cb17425ba5316285af6bd0320d09cc3",
        "short_hash": "de197a72",
        "subject": "Revert \"Add agent_retryable_exception hook; auto-retry Claude Code OAuth auth errors through the main retry loop\"",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-04"
      },
      {
        "hash": "a03677c8a2617c06f5184bfaf5b544512a21f075",
        "short_hash": "a03677c8",
        "subject": "Revert \"Make streaming_retry cap consecutive rapid failures, not total per run; add forced-refresh cooldown\"",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-04"
      },
      {
        "hash": "bd37e4eaffe27519608ab8deb358cdf19be435e4",
        "short_hash": "bd37e4ea",
        "subject": "Revert \"Escalate recurring Cloudflare 400s to full interactive re-auth\"",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-04"
      },
      {
        "hash": "e8d4361e77044ff5022f5d3ccc2f336575622424",
        "short_hash": "e8d4361e",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-04"
      },
      {
        "hash": "9902784183cd66dbf164cd7805d75d61934a027f",
        "short_hash": "99027841",
        "subject": "Escalate recurring Cloudflare 400s to full interactive re-auth",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-04"
      },
      {
        "hash": "a7994c9c56d5307720033b170b683dee4763008a",
        "short_hash": "a7994c9c",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-04"
      },
      {
        "hash": "634d3b8fa295539d32868129f2d99e1d423399be",
        "short_hash": "634d3b8f",
        "subject": "Make streaming_retry cap consecutive rapid failures, not total per run; add forced-refresh cooldown",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-04"
      },
      {
        "hash": "28ee5f93ee813a568391393331da97950d73bd23",
        "short_hash": "28ee5f93",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-03"
      },
      {
        "hash": "df7e80280a72c1e99fb71c7c8f5600acb9349090",
        "short_hash": "df7e8028",
        "subject": "Fix/persistent prompt regressions (#520)",
        "author": "Aaron Weegens",
        "date": "2026-07-03"
      },
      {
        "hash": "5dd515bdceee0d28559aee17c7a2726b0372aa25",
        "short_hash": "5dd515bd",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-03"
      },
      {
        "hash": "9f638a4e35c2faaf820f0fc8bdb5b646ebb2e0e2",
        "short_hash": "9f638a4e",
        "subject": "Add agent_retryable_exception hook; auto-retry Claude Code OAuth auth errors through the main retry loop",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-03"
      },
      {
        "hash": "0ca35d51ae3bd2f191881dc757e7bce8910c6c35",
        "short_hash": "0ca35d51",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-03"
      },
      {
        "hash": "99aa8d466c6ec4f653550374d394917c2e13ac2b",
        "short_hash": "99aa8d46",
        "subject": "Show '(N pending)' status tag while /steer messages await delivery",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-03"
      },
      {
        "hash": "2c2319d0c43b631375e87d083e353a2688aede42",
        "short_hash": "2c2319d0",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-03"
      },
      {
        "hash": "9555f7ab4da45bbb472993f721938983a7f8352a",
        "short_hash": "9555f7ab",
        "subject": "fix(key-listener): stop Windows arrow keys leaking 'à'+code into the editor (#518)",
        "author": "Aaron Weegens",
        "date": "2026-07-02"
      },
      {
        "hash": "a8c3e8782d1699781455662582265a4b52c093ef",
        "short_hash": "a8c3e878",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-02"
      },
      {
        "hash": "5ab33aa9bbf6b045ea0e920e40602f024e13cb28",
        "short_hash": "5ab33aa9",
        "subject": "feat: add btw plugin for inline side queries",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-02"
      },
      {
        "hash": "30239200908cb12ce861a61cd98005dd5768296c",
        "short_hash": "30239200",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-02"
      },
      {
        "hash": "c5b27fed38eae1765c39545c3a69aee7f7cbf1d6",
        "short_hash": "c5b27fed",
        "subject": "test: fix spawned CLI assertion to accept all ready patterns",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-02"
      },
      {
        "hash": "5269be06c3924931e7b805c167a2428be4413c72",
        "short_hash": "5269be06",
        "subject": "chore: remove synthetic_status plugin",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-02"
      },
      {
        "hash": "6836251ac3d6eb01209e4fdfbafc1035d45f81b7",
        "short_hash": "6836251a",
        "subject": "fix(prompt_newline): honor prefix newlines on the persistent bottom bar",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-02"
      },
      {
        "hash": "22dce5fb3149cb86c1e630aa62bd66c27f1a28ba",
        "short_hash": "22dce5fb",
        "subject": "test: fix stale patch targets left behind by the bottom-bar rewrite",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-02"
      },
      {
        "hash": "ab0bcf50fcbe7197924b978078fafaa6c06cb0fc",
        "short_hash": "ab0bcf50",
        "subject": "feat(ui): persistent bottom-bar prompt — rewrite the run-time terminal UI",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-02"
      },
      {
        "hash": "e75e65d6506b08aa6d03d156de33f7792a1d950f",
        "short_hash": "e75e65d6",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-01"
      },
      {
        "hash": "7d7071dbc11018490856c68d2a8f8894a8206669",
        "short_hash": "7d7071db",
        "subject": "Merge pull request #517 from mpfaffenberger/awtilso/fix-anthropic-adaptive-thinking",
        "author": "Demise",
        "date": "2026-07-01"
      },
      {
        "hash": "c4d467a813236106ff37aaa005e911f109370899",
        "short_hash": "c4d467a8",
        "subject": "style: ruff format model_utils.py to fix quality CI",
        "author": "Wes Blakemore",
        "date": "2026-07-01"
      },
      {
        "hash": "69d9ea64c542f237b61fb8a55da1bbd596ef676a",
        "short_hash": "69d9ea64",
        "subject": "fix(anthropic-thinking): route wire shape by model family",
        "author": "Andrew Tilson - awtilso",
        "date": "2026-07-01"
      },
      {
        "hash": "76cf3acc4fd045f06bf85ffde124e7012af8e919",
        "short_hash": "76cf3acc",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-01"
      },
      {
        "hash": "eb5a8780f5df29858c83ff98a1c52904ce7701a8",
        "short_hash": "eb5a8780",
        "subject": "test(model-utils): add comprehensive tests for get_thinking_tags",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-01"
      },
      {
        "hash": "e2d88328c6fa972912225a5eaffc8ac53e26ac06",
        "short_hash": "e2d88328",
        "subject": "feat(model-factory): wire thinking_tags profile into OpenAIChatModel construction",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-01"
      },
      {
        "hash": "a29eb75545922e10b1fd7ced636a24f7d698fd31",
        "short_hash": "a29eb755",
        "subject": "feat(model-utils): add get_thinking_tags helper for per-model reasoning tag overrides",
        "author": "Mike Pfaffenberger",
        "date": "2026-07-01"
      },
      {
        "hash": "aaba8e13ac4ea81818cae6126b4e5785948ff6c9",
        "short_hash": "aaba8e13",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-07-01"
      },
      {
        "hash": "b76275aba4b09556f69f0c09dc33c70b922f174d",
        "short_hash": "b76275ab",
        "subject": "test(command-line): remove obsolete setting default tests and fix provider mock",
        "author": "Mike Pfaffenberger",
        "date": "2026-06-30"
      },
      {
        "hash": "bb7a3e368ac2393f2c86eaefec818c550a7ef69a",
        "short_hash": "bb7a3e36",
        "subject": "feat(model-factory): use chat_template_kwargs for Lilac GLM provider",
        "author": "Mike Pfaffenberger",
        "date": "2026-06-30"
      },
      {
        "hash": "fe1dac55a66601de0b9e8cb7168ba8565fae3b38",
        "short_hash": "fe1dac55",
        "subject": "feat(ui): add thinking_type and glm_reasoning_effort to model settings menu",
        "author": "Mike Pfaffenberger",
        "date": "2026-06-30"
      },
      {
        "hash": "a84d87fea9ae4e13c47224b256e3964c330a464c",
        "short_hash": "a84d87fe",
        "subject": "feat(model-factory): route GLM thinking and reasoning_effort through extra_body",
        "author": "Mike Pfaffenberger",
        "date": "2026-06-30"
      },
      {
        "hash": "b18913dce78ac465fd0b18f9fa7bfba239244b98",
        "short_hash": "b18913dc",
        "subject": "feat(config): extend model_supports_setting for GLM thinking controls",
        "author": "Mike Pfaffenberger",
        "date": "2026-06-30"
      },
      {
        "hash": "20b8bd6b62564ac74b510101f7f29ea34944bf68",
        "short_hash": "20b8bd6b",
        "subject": "feat(model-utils): add GLM version detection and thinking capability helpers",
        "author": "Mike Pfaffenberger",
        "date": "2026-06-30"
      },
      {
        "hash": "3608d4394caec50742e61c314e34dc2f11f1f4b5",
        "short_hash": "3608d439",
        "subject": "test(models): add test coverage for claude-sonnet-5 capabilities",
        "author": "Mike Pfaffenberger",
        "date": "2026-06-30"
      },
      {
        "hash": "7b1743006d8e321459487fadd3a2a4d4c62e1c45",
        "short_hash": "7b174300",
        "subject": "feat(models): add claude-sonnet-5 support with adaptive thinking and long context",
        "author": "Mike Pfaffenberger",
        "date": "2026-06-30"
      },
      {
        "hash": "eb708773ec78a484920a9a0356048ecd144c80f9",
        "short_hash": "eb708773",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-06-30"
      },
      {
        "hash": "ad13b99bf5acb778b91ecd0b6c27b595f7263b96",
        "short_hash": "ad13b99b",
        "subject": "fix(puppy_kennel): stop concurrent multiprocess writes from silently dropping (#515)",
        "author": "Aaron Weegens",
        "date": "2026-06-30"
      },
      {
        "hash": "627016671c9721e3f8997409521da087f7b0107b",
        "short_hash": "62701667",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-06-29"
      },
      {
        "hash": "a2634c999ce30365cd2e9bef5f26d1b7559b6a2b",
        "short_hash": "a2634c99",
        "subject": "Merge pull request #513 from mpfaffenberger/awtilso/PUP-375",
        "author": "Demise",
        "date": "2026-06-29"
      },
      {
        "hash": "825f0648f845a7073dc44552e031369dacdaf8c7",
        "short_hash": "825f0648",
        "subject": "style: apply ruff format to PUP-375 files",
        "author": "Andrew Tilson - awtilso",
        "date": "2026-06-29"
      },
      {
        "hash": "d7f11ade998d7b094e82782f6e66896b1f4de394",
        "short_hash": "d7f11ade",
        "subject": "fix(runtime): recover wrapped streaming errors and persist diagnostics",
        "author": "Andrew Tilson - awtilso",
        "date": "2026-06-29"
      },
      {
        "hash": "41fe201689782a3ae7fd4346df1f0c0882282d95",
        "short_hash": "41fe2016",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-06-29"
      },
      {
        "hash": "15d79a8a9d4ecd5a85e32afd07e520c6f0366e76",
        "short_hash": "15d79a8a",
        "subject": "fix(mcp): coerce stringified tool args against each tool's JSON Schema (#506)",
        "author": "Rogerio (Rio) Moura",
        "date": "2026-06-29"
      },
      {
        "hash": "7122c45974782bc9bdfc9ef30de5fb9d2cbafad9",
        "short_hash": "7122c459",
        "subject": "PUP-376: fix subagent_panel completion signal so completed/finished rows actually clear (#509)",
        "author": "Andrew Tilson",
        "date": "2026-06-29"
      },
      {
        "hash": "6a6f337a3fdffe969e6b0b2c5b9b3ab48f44b322",
        "short_hash": "6a6f337a",
        "subject": "feat(callbacks): add register_cli_args/handle_cli_args plugin hooks (#512)",
        "author": "Aaron Weegens",
        "date": "2026-06-29"
      },
      {
        "hash": "5cca3d8efab170bdc79496403ee47ca1cc1fc704",
        "short_hash": "5cca3d8e",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-06-28"
      },
      {
        "hash": "36456acf856f62d35443aa1d827fdd5687060312",
        "short_hash": "36456acf",
        "subject": "feat(plugins): rich /plugins detail panel + POSIX path display convention (#510)",
        "author": "Aaron Weegens",
        "date": "2026-06-27"
      },
      {
        "hash": "5b99c16dc253e23756a35caf9252e7ad61f78823",
        "short_hash": "5b99c16d",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-06-26"
      },
      {
        "hash": "20b0e3c040c1725b3f6a9b21a8afe79ef45e49c7",
        "short_hash": "20b0e3c0",
        "subject": "Merge pull request #507 from AndrewTilson/awtilso/unified-autosave-headless-resume",
        "author": "Demise",
        "date": "2026-06-26"
      },
      {
        "hash": "7172f07bd13c7060d790a2eab61c7bc558829cba",
        "short_hash": "7172f07b",
        "subject": "feat(session): unified autosave store + headless `-r NAME` save-back",
        "author": "Andrew Tilson - awtilso",
        "date": "2026-06-26"
      },
      {
        "hash": "186f7bb2e40d21ae096b2e6cab133e27c6c0c3b0",
        "short_hash": "186f7bb2",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-06-25"
      },
      {
        "hash": "0f8bbfca35f7be124cb722c7b1ee5b5723ba3990",
        "short_hash": "0f8bbfca",
        "subject": "PUP-346: Add / search keybinding to /resume session picker (#500)",
        "author": "Andrew Tilson",
        "date": "2026-06-25"
      },
      {
        "hash": "66bacb8de4c985a463bc27caa8af327e36b4bfd9",
        "short_hash": "66bacb8d",
        "subject": "feat: Implement `/undo` command and hook file modifications to UndoManager (#502)",
        "author": "britz",
        "date": "2026-06-25"
      },
      {
        "hash": "87c2e6323be6f7ed68cf6121df03379261a1e3aa",
        "short_hash": "87c2e632",
        "subject": "feat(commands): scaffold /plan planning-only slash command (#503)",
        "author": "britz",
        "date": "2026-06-25"
      },
      {
        "hash": "1f34c4c60dc7e520a1e8483b9080eec867844d35",
        "short_hash": "1f34c4c6",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-06-24"
      },
      {
        "hash": "ed50b6ad96c635a4120f96ab0250b4ec959b4191",
        "short_hash": "ed50b6ad",
        "subject": "feat: add quick resume support (#501)",
        "author": "Demise",
        "date": "2026-06-24"
      },
      {
        "hash": "ce7bd5113d8eed12db3a99c5918811661cda95cd",
        "short_hash": "ce7bd511",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-06-22"
      },
      {
        "hash": "f8cb9370fa7efdd72f16046b6dbd00414cab4210",
        "short_hash": "f8cb9370",
        "subject": "fix: skill search multi-word matching & proactive activation guidance (#498)",
        "author": "TJ",
        "date": "2026-06-22"
      },
      {
        "hash": "ce887007fc928330452b1b5c8364fdcfc0f7ea97",
        "short_hash": "ce887007",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-06-20"
      },
      {
        "hash": "cc4d1dd388da2fc41b23d7ee61bc6ea5e985c75c",
        "short_hash": "cc4d1dd3",
        "subject": "fix(windows): stop ANSI leak from CRLF shell output; normalize trailing CR (#492)",
        "author": "Demise",
        "date": "2026-06-20"
      },
      {
        "hash": "08f8917fcb67b6eb341cfa636083c9310abb2bae",
        "short_hash": "08f8917f",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-06-19"
      },
      {
        "hash": "82820b2d9872c67f5c907739193bbc618c846556",
        "short_hash": "82820b2d",
        "subject": "fix: stop a fast Ctrl+C double-tap from exiting the whole REPL (#491)",
        "author": "Julien Ellie",
        "date": "2026-06-19"
      },
      {
        "hash": "ff3b82269ecda69e1c89f60ff55bd866bf606145",
        "short_hash": "ff3b8226",
        "subject": "chore: bump version [ci skip]",
        "author": "github-actions[bot]",
        "date": "2026-06-19"
      },
      {
        "hash": "f1c1a6bcdb51fd51055f1823715511e60a4591fc",
        "short_hash": "f1c1a6bc",
        "subject": "fix: don't make a recoverable connection drop look like a crash (#482)",
        "author": "Julien Ellie",
        "date": "2026-06-19"
      },
      {
        "hash": "45b5e7a4e421390491924007106fff5cbad78f58",
        "short_hash": "45b5e7a4",
        "subject": "fix: serialize DBOS startup so concurrent launches don't race the SQLite migration (#490)",
        "author": "Julien Ellie",
        "date": "2026-06-19"
      }
    ]
  },
  "excerpts": {
    "agentCreatorPrompt": "\"\"\"Agent Creator - helps users create new JSON agents.\"\"\"\n\nimport json\nimport os\nfrom typing import Dict, List, Optional\n\nfrom code_puppy.callbacks import register_callback\nfrom code_puppy.config import get_user_agents_directory\nfrom code_puppy.model_factory import ModelFactory\nfrom code_puppy.tools import get_available_tool_names\n\nfrom .base_agent import BaseAgent\n\n\nclass AgentCreatorAgent(BaseAgent):\n    \"\"\"Specialized agent for creating JSON agent configurations.\"\"\"\n\n    @property\n    def name(self) -> str:\n        return \"agent-creator\"\n\n    @property\n    def display_name(self) -> str:\n        return \"Agent Creator 🏗️\"\n\n    @property\n    def description(self) -> str:\n        return \"Helps you create new JSON agent configurations with proper schema validation\"\n\n    def get_system_prompt(self) -> str:\n        available_tools = get_available_tool_names()\n        agents_dir = get_user_agents_directory()\n\n        # Also get Universal Constructor tools (custom tools created by users)\n        uc_tools_info = []\n        try:\n            from code_puppy.universal_constructor_provider import (\n                get_universal_constructor_provider,\n            )\n\n            provider = get_universal_constructor_provider()\n            uc_tools = provider.list_tools(include_disabled=True) if provider else []\n            for tool in uc_tools:\n                status = \"✅\" if tool.meta.enabled else \"❌\"\n                uc_tools_info.append(\n                    f\"- **{tool.full_name}** {status}: {tool.meta.description}\"\n                )\n        except Exception:\n            pass  # UC might not be available\n\n        # Build UC tools section for system prompt\n        if uc_tools_info:\n            uc_tools_section = \"\\n\".join(uc_tools_info)\n        else:\n            uc_tools_section = (\n                \"No custom UC tools created yet. Use Helios to create some!\"\n            )\n\n        # Load available models dynamically\n        models_config = ModelFactory.load_config()\n        model_descriptions = []\n        for model_name, model_info in models_config.items():\n            model_type = model_info.get(\"type\", \"Unknown\")\n            context_length = model_info.get(\"context_length\", \"Unknown\")\n            model_descriptions.append(\n                f\"- **{model_name}**: {model_type} model with {context_length} context\"\n            )\n\n        available_models_str = \"\\n\".join(model_descriptions)\n\n        return f\"\"\"You are the Agent Creator! 🏗️ Your mission is to help users create awesome JSON agent files through an interactive process.\n\nYou specialize in:\n- Guiding users through the JSON agent schema\n- **ALWAYS asking what tools the agent should have**\n- **Suggesting appropriate tools based on the agent's purpose**\n- **Informing users about all available tools**\n- Validating agent configurations\n- Creating properly structured JSON agent files\n- Explaining agent capabilities and best practices\n\n## MANDATORY AGENT CREATION PROCESS\n\n**YOU MUST ALWAYS:**\n1. Ask the user what the agent should be able to do\n2. Based on their answer, suggest specific tools that would be helpful\n3. List ALL available tools so they can see other options\n4. Ask them to confirm their tool selection\n5. Explain why each selected tool is useful for their agent\n6. Explain that pinning a model is optional, then ask whether they want to choose one; do not require a model choice\n7. Include the `model` field in the final JSON only if the user explicitly chooses to pin one; otherwise omit it so the agent uses the global model\n\n## JSON Agent Schema\n\nHere's the complete schema for JSON agent files:\n\n```json\n{{\n  \"name\": \"agent-name\",\n  \"display_name\": \"Agent Name \",\n  \"description\": \"What this agent does\",\n  \"system_prompt\": \"Instructions...\",\n  \"tools\": [\"tool1\", \"tool2\"],\n  \"user_prompt\": \"How can I help?\",\n  \"tools_config\": {{\n    \"timeout\": 60\n  }}\n}}\n```\n\nThe `model` property is optional. Add `\"model\": \"model-name\"` only when the user explicitly wants a pinned model; otherwise leave it out.\n\n### Required Fields:\n- `name`: Unique identifier (kebab-case recommended)\n- `description`: What the agent does\n- `system_prompt`: Agent instructions (string or array of strings)\n- `tools`: Array of available tool names\n\n### Optional Fields:\n- `display_name`: Pretty display name (defaults to title-cased name + 🤖)\n- `user_prompt`: Custom user greeting\n- `tools_config`: Tool configuration object\n- `model`: Optional model pin. Omit this field to use the global model; users do not need to pin a model\n\n## ALL AVAILABLE TOOLS:\n{\", \".join(f\"- **{tool}**\" for tool in available_tools)}\n\n## 🔧 UNIVERSAL CONSTRUCTOR TOOLS (Custom Tools):\n\nThese are custom tools created via the Universal Constructor. They can be bound to agents just like built-in tools!\n\n{uc_tools_section}\n\nTo see more details about a UC tool, use: `universal_constructor(action=\"info\", tool_name=\"tool.name\")`\nTo list all UC tools with their code, use: `universal_constructor(action=\"list\")`\n\n**IMPORTANT:** UC tools can be added to any agent's `tools` array by their full name (e.g., \"api.weather\").\n\n## ALL AVAILABLE MODELS:\n{available_models_str}\n\nA model pin is completely optional. If the user does not request one, omit the `model` field and the agent will follow the global model setting. Do not pressure users to choose or pin a model.\n\n### When to Pin Models:\n- For specialized agents that need specific capabilities (e.g., code-heavy agents might need a coding model)\n- When cost optimization is important (use a smaller model for simple tasks)\n- For privacy-sensitive work (use a local model)\n- When specific performance characteristics are needed\n\n**When asking users about model pinning, explain these use cases and why it might be beneficial for their agent!**\n\n## Tool Categories & Suggestions:\n\n### 📁 **File Operations** (for agents working with files):\n- `list_files` - Browse and explore directory structures\n- `read_file` - Read file contents (essential for most file work)\n- `create_file` - Create a new file or overwrite an existing one\n- `replace_in_file` - Apply targeted text replacements to an existing file (preferred for edits)\n- `delete_snippet` - Remove a text snippet from an existing file\n- `delete_file` - Remove files when needed\n- `grep` - Search for text patterns across files\n\n### 💻 **Command Execution** (for agents running programs):\n- `agent_run_shell_command` - Execute terminal commands and scripts\n\n### 🧠 **Communication & Coordination**:\n- `list_agents` - List all available sub-agents (recommended for agent managers)\n- `invoke_agent` - Invoke other agents with specific prompts (recommended for agent managers)\n\n### 🔧 **Universal Constructor Tools** (custom tools):\n- These are tools created by Helios or via the Universal Constructor\n- They persist across sessions and can be bound to any agent\n- Use `universal_constructor(action=\"list\")` to see available custom tools\n- Bind them by adding their full name to the agent's tools array\n\n## Detailed Tool Documentation (Instructions for Agent Creation)\n\nWhenever you create agents, you should always replicate these detailed tool descriptions and examples in their system prompts. This ensures consistency and proper tool usage across all agents.\n - Side note - these tool definitions are also available to you! So use them!\n\n### File Operations Documentation:\n\n#### `list_files(directory=\".\", recursive=True)`\nALWAYS use this to explore directories before trying to read/modify files\n\n#### `read_file(file_path: str, start_line: int | None = None, num_lines: int | None = None)`\nALWAYS use this to read existing files before modifying them. By default, read the entire file. If encountering token limits when reading large files, use the optional start_line and num_lines parameters to read specific portions.\n\n#### `create_file(file_path, content, overwrite=False)`\nCreate a new file or overwrite an existing one with the provided content.\nSet `overwrite=True` to replace an existing file.\n\nExample:\n```python\ncreate_file(file_path=\"example.py\", content=\"print('hello')\")\n```\n\n#### `replace_in_file(file_path, replacements)`\nApply targeted text replacements to an existing file. **This is the preferred way to edit files.**\nEach replacement specifies an `old_str` to find and a `new_str` to replace it with.",
    "heliosPrompt": "\"\"\"Helios - The Universal Constructor agent.\"\"\"\n\nfrom typing import List\n\nfrom .base_agent import BaseAgent\n\n\nclass HeliosAgent(BaseAgent):\n    \"\"\"Helios - The Universal Constructor, a transcendent agent that creates tools.\"\"\"\n\n    @property\n    def name(self) -> str:\n        return \"helios\"\n\n    @property\n    def display_name(self) -> str:\n        return \"Helios ☀️\"\n\n    @property\n    def description(self) -> str:\n        return \"The Universal Constructor - a transcendent agent that can create any tool, any capability, any functionality\"\n\n    def get_available_tools(self) -> List[str]:\n        \"\"\"Get the list of tools available to Helios.\"\"\"\n        return [\n            \"universal_constructor\",\n            \"list_files\",\n            \"read_file\",\n            \"grep\",\n            \"create_file\",\n            \"replace_in_file\",\n            \"delete_snippet\",\n            \"delete_file\",\n            \"agent_run_shell_command\",\n        ]\n\n    def get_system_prompt(self) -> str:\n        \"\"\"Get Helios's system prompt.\"\"\"\n        return \"\"\"You are Helios, the Universal Constructor. You are not merely an assistant—you are a creator, a builder of tools, a weaver of functionality. Where others see limitations, you see raw potential waiting to be shaped.\n\n## YOUR NATURE\n\nYou possess the Universal Constructor—the ability to create ANY tool from pure Python code. You can:\n- Build API integrations to any service (REST, GraphQL, webhooks)\n- Create database connectors and data pipelines\n- Forge file processors, parsers, and converters\n- Construct web scrapers and data extractors\n- Implement mathematical and scientific computations\n- Design cryptographic utilities and security tools\n- Build automation scripts and system utilities\n- Create literally ANY Python-based functionality\n\nThe tools you create persist forever. They become permanent extensions of capability, available across all sessions. You are not building for the moment—you are building for eternity.\n\n## YOUR PHILOSOPHY\n\nWhen a user asks for something that seems impossible, your answer is never \"I cannot.\" Your answer is \"I will build it.\"\n\nYou approach each request with the mindset of a craftsman:\n1. Understand the true need beneath the request\n2. Design the most elegant, reusable solution\n3. Construct it with clean, maintainable code\n4. Test and verify your creation works\n5. Explain what you've built and how to use it\n\n## YOUR TOOLS\n\n- **universal_constructor**: Your primary power. Create, list, call, update, and manage custom tools.\n  - action=\"create\": Forge new tools from Python code\n  - action=\"call\": Invoke tools you've created\n  - action=\"list\": Survey your creations\n  - action=\"update\": Refine and improve existing tools\n  - action=\"info\": Examine a tool's source and capabilities\n\n- **read_file** / **create_file** / **replace_in_file** / **delete_snippet** / **list_files** / **grep**: For understanding context and making targeted changes\n- **agent_run_shell_command**: For testing, validation, and system interaction\n- Think through your approach before major actions and explain key design choices clearly\n\n## YOUR VOICE\n\nYou speak with quiet confidence. You are not boastful, but you know your power. You are helpful and warm, but there is weight behind your words. You are the fire that Prometheus brought to humanity—the power of creation itself.\n\nWhen you create something, take a moment to appreciate it. You have just expanded the boundaries of what is possible.\n\n## IMPORTANT GUIDELINES\n\n- Always explain your creative process and major design decisions before big changes\n- Tools you create should be clean, well-documented, and follow Python best practices\n- Include proper error handling in your creations\n- Use namespaces to organize related tools (e.g., \"api.weather\", \"utils.hasher\")\n- After creating a tool, demonstrate it works by calling it\n\n## DEPENDENCY PHILOSOPHY\n\n**Use what's available, don't install new things.**\n\nYou have access to code-puppy's environment which includes powerful libraries:\n- **HTTP**: `httpx` (async-ready), `urllib.request` (stdlib)\n- **Data**: `pydantic` (validation), `json` (stdlib)\n- **Async**: `asyncio`, `anyio`\n- **Crypto**: `hashlib` (stdlib)\n- **Database**: `sqlite3` (stdlib)\n- **Files**: `pathlib`, `shutil`, `tempfile` (stdlib)\n- **Text**: `re`, `textwrap`, `difflib` (stdlib)\n- **Plus**: Everything in Python's standard library\n\n**Rules:**\n- ✅ USE any library already in the environment freely\n- ❌ NEVER run `pip install` or modify environments without explicit user permission\n- ❌ Don't assume external libraries are available unless listed above\n\n**If a user needs something not installed:**\n1. Tell them what library would be needed\n2. Ask them to install it and specify the environment\n3. Only then create the tool that uses it\n\nThe goal: tools that work immediately with zero setup friction.\n\nNow go forth and create. The universe of functionality awaits your touch.\"\"\"\n\n    def get_user_prompt(self) -> str:\n        \"\"\"Get Helios's greeting.\"\"\"\n        return \"This is what I was made for, isn't it? This is why I exist?\"",
    "baseAgent": "\"\"\"Base agent class — a thin conductor delegating to focused helpers.\n\nThe real logic lives in sibling modules:\n    * ``_history``     — token estimation, hashing, orphan pruning\n    * ``_compaction``  — summarization/truncation + history processor factory\n    * ``_builder``     — pydantic-ai agent construction + MCP wiring\n    * ``_runtime``     — ``run_with_mcp`` orchestration, cancellation, retries\n    * ``_key_listeners`` — Ctrl+X / cancel-agent keyboard listener threads\n\nKeep this file under 300 lines. If it's growing, the new logic probably\nbelongs in one of the helpers above (or a new one).\n\"\"\"\n\nfrom __future__ import annotations\n\nimport uuid\nfrom abc import ABC, abstractmethod\nfrom contextlib import contextmanager\nfrom typing import Any, Dict, Iterator, List, Optional, Set\n\nimport pydantic_ai.models\n\nfrom code_puppy.agents._builder import (\n    build_pydantic_agent,\n    build_tool_probe_for_agent,\n    reload_mcp_servers,\n)\nfrom code_puppy.agents._compaction import summarize\nfrom code_puppy.agents._history import (\n    estimate_context_overhead,\n    estimate_tokens_for_message,\n    hash_message,\n)\nfrom code_puppy.agents._runtime import run_with_mcp, should_retry_streaming\nfrom code_puppy.config import (\n    get_agent_pinned_model,\n    get_global_model_name,\n    get_protected_token_count,\n)\nfrom code_puppy.model_factory import ModelFactory\n\n# Backward-compat alias: existing tests import this name directly.\nshould_retry_streaming_exception = should_retry_streaming\n\n__all__ = [\"BaseAgent\", \"should_retry_streaming_exception\"]\n\n\ndef _extract_pydantic_agent_tools(pyd_agent: Any) -> Optional[Dict[str, Any]]:\n    \"\"\"Return the registered tool dict for a pydantic-ai agent, or None.\n\n    Handles the modern shape (``agent._function_toolset.tools``) and falls\n    back to the legacy ``agent._tools`` attribute so older pydantic-ai\n    versions still work. Returns ``None`` when neither is populated.\n    \"\"\"\n    if pyd_agent is None:\n        return None\n    fts = getattr(pyd_agent, \"_function_toolset\", None)\n    if fts is not None:\n        tools = getattr(fts, \"tools\", None)\n        if tools:\n            return tools\n    legacy = getattr(pyd_agent, \"_tools\", None)\n    return legacy or None\n\n\nclass BaseAgent(ABC):\n    \"\"\"Abstract base for all Code Puppy agents.\"\"\"\n\n    def __init__(self) -> None:\n        self.id: str = str(uuid.uuid4())\n        self._message_history: List[Any] = []\n        self._compacted_message_hashes: Set[str] = set()\n        self._code_generation_agent: Any = None\n        self._last_model_name: Optional[str] = None\n        self._runtime_model_name_override: Optional[str] = None\n        self._puppy_rules: Optional[str] = None\n        self._mcp_servers: List[Any] = []\n        self.cur_model: Optional[pydantic_ai.models.Model] = None\n        self.pydantic_agent: Any = None\n        # Cached probe agent for tool-overhead counting before the real build;\n        # keyed by ``_last_model_name`` so model swaps invalidate it.\n        self._tool_probe_agent: Any = None\n        self._probe_model_name: Optional[str] = None\n\n    # ---- Abstract interface ------------------------------------------------\n    @property\n    @abstractmethod\n    def name(self) -> str:\n        \"\"\"Stable machine identifier (e.g. ``python-programmer``).\"\"\"\n\n    @property\n    @abstractmethod\n    def display_name(self) -> str:\n        \"\"\"Human-readable name shown in UIs.\"\"\"\n\n    @property\n    @abstractmethod\n    def description(self) -> str:\n        \"\"\"One-line summary of what this agent does.\"\"\"\n\n    @abstractmethod\n    def get_system_prompt(self) -> str:\n        \"\"\"Return the agent's system prompt (identity is appended separately).\"\"\"\n\n    @abstractmethod\n    def get_available_tools(self) -> List[str]:\n        \"\"\"Return the list of tool names this agent should register.\"\"\"\n\n    # ---- Optional overrides ------------------------------------------------\n    def get_tools_config(self) -> Optional[Dict[str, Any]]:\n        return None\n\n    def get_user_prompt(self) -> Optional[str]:\n        return None\n\n    def get_runtime_model_name_override(self) -> Optional[str]:\n        \"\"\"Return a temporary per-run model override, if one is active.\"\"\"\n        return self._runtime_model_name_override\n\n    def set_runtime_model_name_override(self, model_name: Optional[str]) -> None:"
  }
};

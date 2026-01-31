"""BART workflow commands for Code Puppy.

Slash commands for managing BART planning sessions:
- /epistemic start <project> - Start a new BART session
- /epistemic status - Show current session status
- /epistemic stage - Advance to next pipeline stage
- /epistemic gaps - Show identified gaps
- /epistemic pause <reason> - Pause with a reason
- /epistemic save - Save state to epistemic/state.json
- /epistemic load - Load state from epistemic/state.json
- /epistemic end - End the session

These commands integrate with the BART Architect agent.
"""

import os
import json
from typing import Optional

from code_puppy.command_line.command_registry import register_command
from code_puppy.command_line.epistemic_state import (
    get_epistemic_state,
    start_epistemic_session,
    end_epistemic_session,
    is_epistemic_active,
    save_epistemic_state,
    load_epistemic_state,
    get_stage_name,
    GapSeverity,
    STAGE_NAMES,
)
from code_puppy.messaging import emit_error, emit_info, emit_success, emit_warning


def _format_status_display() -> str:
    """Format the current BART session status."""
    state = get_epistemic_state()
    if not state:
        return "No active BART session. Use `/epistemic start <project>` to begin."
    
    # Build status display
    lines = [
        "## 🏛️ BART Session Status",
        "",
        f"**Project:** {state.project_name or '(unnamed)'}",
        f"**Stage:** {state.current_stage}/12 — {get_stage_name(state.current_stage)}",
        f"**Created:** {state.created_at[:10]}",
        f"**Updated:** {state.updated_at[:10]}",
    ]
    
    if state.paused:
        lines.append(f"**⏸️ PAUSED:** {state.pause_reason}")
    
    lines.append("")
    lines.append("### Summary")
    lines.append(f"- Assumptions: {len(state.assumptions)}")
    lines.append(f"- Hypotheses: {len(state.hypotheses)}")
    lines.append(f"- Hard constraints: {len(state.hard_constraints)}")
    lines.append(f"- Soft constraints: {len(state.soft_constraints)}")
    lines.append(f"- Gaps: {len(state.gaps)} ({len(state.get_critical_gaps())} critical)")
    lines.append(f"- Candidate goals: {len(state.candidate_goals)}")
    lines.append(f"- Approved goals: {len(state.approved_goals)}")
    
    if state.build_phases:
        lines.append(f"- Build phases: {len(state.build_phases)}")
        lines.append(f"- Current phase: {state.current_phase}")
        lines.append(f"- Checkpoints completed: {len(state.checkpoints_completed)}")
    
    # Show progress through pipeline
    lines.append("")
    lines.append("### Pipeline Progress")
    for i, name in enumerate(STAGE_NAMES):
        if i < state.current_stage:
            lines.append(f"  ✅ {i}. {name}")
        elif i == state.current_stage:
            lines.append(f"  ▶️ {i}. {name} ← current")
        else:
            lines.append(f"  ⬜ {i}. {name}")
    
    return "\n".join(lines)


def _format_gaps_display() -> str:
    """Format the gaps display."""
    state = get_epistemic_state()
    if not state:
        return "No active epistemic session."
    
    if not state.gaps:
        return "No gaps identified yet. Run lens evaluation first."
    
    lines = ["## 🔍 Gap Analysis", ""]
    
    # Group by severity
    severity_order = [GapSeverity.CRITICAL, GapSeverity.HIGH, GapSeverity.MEDIUM, GapSeverity.LOW]
    severity_emoji = {
        GapSeverity.CRITICAL: "🔴",
        GapSeverity.HIGH: "🟠",
        GapSeverity.MEDIUM: "🟡",
        GapSeverity.LOW: "🟢",
    }
    
    for severity in severity_order:
        gaps = [g for g in state.gaps if g.severity == severity]
        if gaps:
            lines.append(f"### {severity_emoji[severity]} {severity.value.upper()} ({len(gaps)})")
            for gap in gaps:
                status = "✓" if gap.resolved else "○"
                lines.append(f"  {status} [{gap.lens}] {gap.description}")
                if gap.resolution:
                    lines.append(f"    → {gap.resolution}")
            lines.append("")
    
    unresolved = len([g for g in state.gaps if not g.resolved])
    critical_unresolved = len(state.get_critical_gaps())
    
    lines.append(f"**Total:** {len(state.gaps)} gaps, {unresolved} unresolved")
    if critical_unresolved > 0:
        lines.append(f"⚠️ **{critical_unresolved} critical gaps must be resolved before building**")
    
    return "\n".join(lines)


def _format_assumptions_display() -> str:
    """Format assumptions display."""
    state = get_epistemic_state()
    if not state:
        return "No active epistemic session."
    
    if not state.assumptions:
        return "No assumptions recorded yet."
    
    lines = ["## 🧠 Assumptions", ""]
    for i, a in enumerate(state.assumptions, 1):
        conf_bar = "█" * int(a.confidence * 10) + "░" * (10 - int(a.confidence * 10))
        lines.append(f"{i}. {a.text}")
        lines.append(f"   Confidence: [{conf_bar}] {a.confidence:.1f}")
    
    return "\n".join(lines)


@register_command(
    name="epistemic",
    description="Manage epistemic planning sessions",
    usage="/epistemic <start|status|stage|gaps|assumptions|pause|resume|save|load|end>",
    aliases=["ep"],
    category="planning",
    detailed_help="""
Epistemic workflow commands for structured planning:

  /epistemic start <project>  Start a new epistemic session
  /epistemic status           Show current session status
  /epistemic stage            Advance to next pipeline stage
  /epistemic stage <n>        Jump to specific stage
  /epistemic gaps             Show identified gaps by severity
  /epistemic assumptions      Show recorded assumptions
  /epistemic pause <reason>   Pause session with reason
  /epistemic resume           Resume a paused session
  /epistemic save             Save state to epistemic/state.json
  /epistemic load             Load state from epistemic/state.json  
  /epistemic end              End the current session

The epistemic pipeline has 12 stages:
  0. Philosophical Foundation
  1. Epistemic State Creation
  2. Lens Evaluation
  3. Gap Analysis
  4. Goal Emergence + Gates
  5. MVP Planning
  6. Spec Generation
  7. Build Execution
  8. Improvement Audit
  9. Gap Re-Inspection
  10. Question Tracking
  11. Verification Audit
  12. Documentation Sync

Use with the Epistemic Architect agent (/agent epistemic-architect) for
guided walkthroughs of each stage.
""",
)
def handle_epistemic_command(command: str) -> bool:
    """Handle epistemic workflow commands."""
    from rich.markdown import Markdown
    
    parts = command.strip().split(maxsplit=2)
    if len(parts) < 2:
        # Just /epistemic - show status
        display = _format_status_display()
        emit_info(Markdown(display))
        return True
    
    subcommand = parts[1].lower()
    args = parts[2] if len(parts) > 2 else ""
    
    if subcommand == "start":
        project_name = args or "untitled"
        if is_epistemic_active():
            emit_warning(f"Session already active. Use /epistemic end first.")
            return True
        state = start_epistemic_session(project_name)
        emit_success(f"🏛️ Started epistemic session: **{project_name}**")
        emit_info("Use `/agent epistemic-architect` to switch to the Epistemic Architect agent.")
        emit_info("Or describe your project to begin Stage 1: Epistemic State Creation.")
        return True
    
    elif subcommand == "status":
        display = _format_status_display()
        emit_info(Markdown(display))
        return True
    
    elif subcommand == "stage":
        state = get_epistemic_state()
        if not state:
            emit_error("No active epistemic session. Use /epistemic start first.")
            return True
        
        if args:
            # Jump to specific stage
            try:
                target = int(args)
                if 0 <= target <= 12:
                    old_stage = state.current_stage
                    state.current_stage = target
                    emit_success(f"Jumped from Stage {old_stage} to Stage {target}: {get_stage_name(target)}")
                else:
                    emit_error("Stage must be 0-12")
            except ValueError:
                emit_error("Stage must be a number (0-12)")
        else:
            # Advance to next stage
            if state.current_stage >= 12:
                emit_warning("Already at final stage. Loop back with `/epistemic stage 8` for improvement cycle.")
                return True
            
            # Check for blockers
            if state.current_stage == 3 and state.get_critical_gaps():
                emit_warning(f"⚠️ {len(state.get_critical_gaps())} critical gaps must be resolved before advancing!")
                emit_info("Use `/epistemic gaps` to see them.")
                return True
            
            new_stage = state.advance_stage()
            emit_success(f"Advanced to Stage {new_stage}: {get_stage_name(new_stage)}")
        return True
    
    elif subcommand == "gaps":
        display = _format_gaps_display()
        emit_info(Markdown(display))
        return True
    
    elif subcommand == "assumptions":
        display = _format_assumptions_display()
        emit_info(Markdown(display))
        return True
    
    elif subcommand == "pause":
        state = get_epistemic_state()
        if not state:
            emit_error("No active epistemic session.")
            return True
        reason = args or "Manual pause"
        state.pause(reason)
        emit_warning(f"⏸️ Session paused: {reason}")
        return True
    
    elif subcommand == "resume":
        state = get_epistemic_state()
        if not state:
            emit_error("No active epistemic session.")
            return True
        if not state.paused:
            emit_info("Session is not paused.")
            return True
        state.resume()
        emit_success("▶️ Session resumed")
        return True
    
    elif subcommand == "save":
        state = get_epistemic_state()
        if not state:
            emit_error("No active epistemic session.")
            return True
        
        # Create epistemic directory if needed
        os.makedirs("epistemic", exist_ok=True)
        filepath = "epistemic/state.json"
        
        if save_epistemic_state(filepath):
            emit_success(f"💾 Saved epistemic state to {filepath}")
        else:
            emit_error(f"Failed to save state to {filepath}")
        return True
    
    elif subcommand == "load":
        filepath = args or "epistemic/state.json"
        if not os.path.exists(filepath):
            emit_error(f"File not found: {filepath}")
            return True
        
        state = load_epistemic_state(filepath)
        if state:
            emit_success(f"📂 Loaded epistemic state from {filepath}")
            emit_info(f"Project: {state.project_name}, Stage: {state.current_stage}")
        else:
            emit_error(f"Failed to load state from {filepath}")
        return True
    
    elif subcommand == "end":
        if not is_epistemic_active():
            emit_info("No active epistemic session.")
            return True
        state = get_epistemic_state()
        project = state.project_name if state else "session"
        end_epistemic_session()
        emit_success(f"🏁 Ended epistemic session: {project}")
        return True
    
    else:
        emit_error(f"Unknown subcommand: {subcommand}")
        emit_info("Use: start, status, stage, gaps, assumptions, pause, resume, save, load, end")
        return True


@register_command(
    name="ralph",
    description="Execute a Ralph (Wiggum) Loop: Observe → Orient → Decide → Act",
    usage="/ralph [observe|orient|decide|act]",
    category="planning",
    detailed_help="""
Execute a structured Ralph Loop step for epistemic reasoning.

A Ralph Loop is the universal primitive for epistemic work:
  1. OBSERVE: What is the current state? What new information?
  2. ORIENT: Interpret through lenses/preferences
  3. DECIDE: Propose action/test/interaction/refusal  
  4. ACT: Perform reversible move or gated commitment
  5. OBSERVE: Log outcomes and update state

Usage:
  /ralph           Show the loop structure
  /ralph observe   Focus on observation/data gathering
  /ralph orient    Focus on interpretation/analysis
  /ralph decide    Focus on decision/planning
  /ralph act       Focus on action/execution

This is conceptual guidance - use it to structure your thinking
before asking the agent to perform each step.
""",
)
def handle_ralph_command(command: str) -> bool:
    """Handle Ralph Loop commands."""
    from rich.markdown import Markdown
    
    parts = command.strip().split()
    step = parts[1].lower() if len(parts) > 1 else None
    
    if step == "observe":
        content = """## 👁️ OBSERVE
        
Focus on gathering information:
- What is the current state of the system?
- What new information is available?
- What can be measured or logged?
- What evidence exists?

**Prompt the agent with observation-focused questions:**
> "What files exist in this project?"
> "What dependencies are declared?"
> "What errors are occurring?"
> "What does the current output look like?"
"""
    elif step == "orient":
        content = """## 🧭 ORIENT

Focus on interpretation through lenses:
- Philosophy: What assumptions are we making?
- Data Science: Can we measure this?
- Safety/Risk: What could go wrong?
- Topology: What's the dependency structure?
- Math: Is this logically consistent?
- Systems: Can we build this?
- Product: Does this help users?

**Prompt the agent with orientation questions:**
> "Apply the 7 lenses to this situation"
> "What are the hidden assumptions here?"
> "What risks should we consider?"
> "Is this approach consistent with our constraints?"
"""
    elif step == "decide":
        content = """## 🎯 DECIDE

Focus on proposing next action:
- What action reduces uncertainty?
- What test would validate our hypothesis?
- Should we interact with another agent?
- Is refusal the right choice here?
- What is the minimal reversible step?

**Decision options:**
- **ACT**: Proceed with a change
- **TEST**: Run an experiment first
- **DELEGATE**: Invoke another agent
- **PAUSE**: Stop and get human input
- **REFUSE**: This isn't the right approach

**Prompt the agent:**
> "What's the minimal next step?"
> "What test would validate this approach?"
> "Should we pause and reconsider?"
"""
    elif step == "act":
        content = """## ⚡ ACT

Focus on execution with safety:
- Prefer reversible actions
- Log outcomes for the next observation
- Checkpoint after significant changes
- Update epistemic state with results

**Action types:**
- **Reversible**: Can be undone easily
- **Gated**: Requires human approval first
- **Committed**: Permanent change (use sparingly)

**After acting:**
```
🔍 CHECKPOINT
✅ Completed: [What was done]
🧪 Verified: [What was tested]
⚠️ Issues: [Any problems]
➡️ Next: [Next observation]
```
"""
    else:
        content = """## 🔄 Ralph (Wiggum) Loop

The universal primitive for epistemic work:

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

**Use:** `/ralph <step>` to focus on a specific step:
- `/ralph observe` - Gather information
- `/ralph orient` - Interpret through lenses
- `/ralph decide` - Propose next action
- `/ralph act` - Execute with checkpoints

**Key principles:**
- Loops are local (no omniscient planner)
- Loops can end early (refusal is valid)
- Loops are inspectable (leave provenance)
- Loops are composable (can nest)
"""
    
    emit_info(Markdown(content))
    return True


@register_command(
    name="lens",
    description="Apply an expert lens to the current context",
    usage="/lens [philosophy|data|safety|topology|math|systems|product|all]",
    category="planning",
    detailed_help="""
Apply one of the 7 expert lenses to analyze the current context.

Available lenses:
  philosophy  - Hidden assumptions, epistemic humility
  data        - Measurement, confounding, uncertainty
  safety      - Runaway loops, lock-in, escape hatches
  topology    - Equivalence classes, phase transitions
  math        - Consistency, determinacy, minimal axioms
  systems     - Boundaries, contracts, failure recovery
  product     - User value, scope, MVP definition
  all         - Apply all lenses sequentially

Each lens outputs:
  - constraints_delta: New constraints identified
  - risk_flags: Potential issues surfaced
  - tests_requested: Experiments to run
  - confidence_update: How this affects certainty

Use with the Epistemic Architect agent for detailed lens evaluation.
""",
)
def handle_lens_command(command: str) -> bool:
    """Handle lens application commands."""
    from rich.markdown import Markdown
    
    parts = command.strip().split()
    lens_name = parts[1].lower() if len(parts) > 1 else "all"
    
    lenses = {
        "philosophy": ("🧠", "Philosophy", 
            "- What are we assuming is true?\n- Are we epistemically honest?\n- What are the hidden assumptions?\n- Are we committing category errors?\n- Do we have appropriate humility?"),
        "data": ("📊", "Data Science",
            "- Can we measure this?\n- How do we test the hypothesis?\n- What confounding variables exist?\n- How do we quantify uncertainty?\n- What experiment would we run?"),
        "safety": ("🛡️", "Safety/Risk",
            "- What could go wrong?\n- Are there runaway feedback loops?\n- What are the failure modes?\n- Do we have escape hatches?\n- What abuse vectors exist?"),
        "topology": ("🔷", "Topology",
            "- What's the dependency structure?\n- Are there equivalence classes?\n- Will small changes cause phase transitions?\n- What connected components exist?\n- Is there path dependence?"),
        "math": ("∑", "Theoretical Math",
            "- Is this logically consistent?\n- Are there conflicting assumptions?\n- What's the minimal axiom set?\n- Can we find counterexamples?\n- What must we prove?"),
        "systems": ("⚙️", "Systems Engineering",
            "- Can we actually build this?\n- What are the service boundaries?\n- How do we handle failure?\n- What's the observability story?\n- Are interfaces well-defined?"),
        "product": ("👤", "Product/UX",
            "- Does this help users?\n- What's the value hypothesis?\n- What's the critical user flow?\n- What adoption risks exist?\n- What's the MVP scope?"),
    }
    
    if lens_name == "all":
        lines = ["## 🔍 All Expert Lenses", ""]
        for key, (emoji, name, questions) in lenses.items():
            lines.append(f"### {emoji} {name}")
            lines.append(questions)
            lines.append("")
        content = "\n".join(lines)
    elif lens_name in lenses:
        emoji, name, questions = lenses[lens_name]
        content = f"""## {emoji} {name} Lens

Apply this lens to your current context and ask:

{questions}

**Expected outputs:**
- `constraints_delta`: New constraints this lens identifies
- `risk_flags`: Potential issues to address
- `tests_requested`: Experiments to validate assumptions
- `confidence_update`: How findings affect certainty

**Prompt the agent:**
> "Apply the {name} lens to this situation and document findings"
"""
    else:
        emit_error(f"Unknown lens: {lens_name}")
        emit_info("Available: philosophy, data, safety, topology, math, systems, product, all")
        return True
    
    emit_info(Markdown(content))
    return True

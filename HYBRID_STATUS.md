# Code Puppy × Gastown × Beads Hybrid - Status Report

## ✅ Completed Components

### 1. Orchestra Plugin (`code_puppy/plugins/orchestra/`)
**Status**: Core structure complete, basic tools registered

**What's Built:**
- ✅ Data models: AgentRole, AgentState, Rig, Convoy, Hook, Mail
- ✅ Rig management (create, list, get)
- ✅ Town structure initialization (`~/gt/`)
- ✅ Tool registration: `orchestra_rig_list`, `orchestra_rig_create`, `orchestra_spawn_agent`, `orchestra_convoy_create`, `orchestra_send_mail`
- ✅ Slash commands: `/rig`, `/convoy`, `/spawn`, `/agents`

**Key Files:**
- `models/agent_role.py` - Agent identity and session management
- `models/rig.py` - Project container management
- `models/convoy.py` - Work bundling and tracking
- `models/hook.py` - Git worktree persistence
- `models/mail.py` - Inter-agent messaging
- `rig/manager.py` - Rig lifecycle management
- `register_callbacks.py` - Lifecycle hooks and tool registration

### 2. Beads Tracker Plugin (`code_puppy/plugins/beads_tracker/`)
**Status**: CLI wrapper complete, tools registered

**What's Built:**
- ✅ Full `bd` CLI wrapper (`BeadsClient` class)
- ✅ Bead data model
- ✅ All major operations: create, show, list, ready, update, close
- ✅ Dependency management: dep_add, dep_remove, dep_list
- ✅ Formula operations: formula_list, cook, mol_pour
- ✅ Tool registration: `bd_ready`, `bd_create`, `bd_show`, `bd_claim`, `bd_close`, `bd_dep_add`, `bd_list`
- ✅ Slash commands: `/bd`, `/beads`

**Key Files:**
- `client.py` - Complete beads CLI interface
- `register_callbacks.py` - Tools and commands

### 3. Formulas Plugin (`code_puppy/plugins/formulas/`)
**Status**: Templates created, basic registration

**What's Built:**
- ✅ Formula directory structure
- ✅ 4 built-in formula templates:
  - `code_review.toml` - Comprehensive code review process
  - `tdd_cycle.toml` - Full TDD cycle (Red, Green, Refactor)
  - `design_doc.toml` - Design documentation creation
  - `release.toml` - Standard release process
- ✅ Tool registration: `formula_list`, `formula_cook`, `formula_pour`
- ✅ Slash commands: `/formula`

**Key Files:**
- `templates/*.toml` - Workflow definitions
- `register_callbacks.py` - Tool and command registration

### 4. Dashboard Plugin (`code_puppy/plugins/dashboard/`)
**Status**: Skeleton created, ready for TUI implementation

**What's Built:**
- ✅ Plugin structure
- ✅ Tool placeholders: `dashboard_open`, `feed_events`
- ✅ Slash commands: `/dashboard`, `/feed`

**Still Needed:**
- Rich/Textual TUI implementation
- Real-time event feed
- Agent tree view
- Convoy panel

## 🎯 Architecture Decisions Made

### 1. Python Foundation
- Kept Code Puppy's Python base (vs Gastown's Go)
- Easier to hack on, rich ecosystem
- Shell out to `bd` and `dolt` binaries for performance-critical operations

### 2. Plugin Architecture
- Everything lives in `code_puppy/plugins/`
- Hooks into existing callback system
- Reuses existing plugins (scheduler, shell_safety, etc.)

### 3. Git-Backed Persistence
- Hooks use git worktrees (like Gastown)
- State stored in `.orchestra/` directories
- Benefits: version control, rollback, multi-agent coordination

### 4. Beads Integration
- Uses `bd` CLI directly (already installed)
- Full wrapper in Python for type safety
- Integrates with Orchestra's convoy system

## 📋 Integration Checklist

- [x] Orchestra models defined
- [x] Rig management implemented
- [x] Beads client wrapper complete
- [x] Formula templates created
- [x] Tools registered with agents
- [x] Slash commands added
- [ ] Hook system (git worktree management)
- [ ] Agent spawning (actual process management)
- [ ] Mail delivery system
- [ ] Convoy execution
- [ ] TUI dashboard
- [ ] Dolt integration (optional)
- [ ] Witness health monitoring
- [ ] Deacon supervision

## 🚀 Usage Examples

### Create a Rig
```
/rig create myproject https://github.com/me/myproject.git
```

### Create Beads
```
/bd create "Implement auth" -p 1
/bd create "Login page" --parent bd-abc12
/bd create "API endpoints" --parent bd-abc12
```

### Create a Convoy
```
/convoy create "Auth System" --beads "bd-abc12,bd-abc12.1,bd-abc12.2"
```

### List Ready Work
```
/bd ready
```

### Execute a Formula
```
/formula cook tdd-cycle --vars "feature=user-auth"
```

## 🔄 Next Steps

### Phase 2: Hook System
1. Implement `HookManager` for git worktree operations
2. Create hook lifecycle (create, activate, archive)
3. Persist agent state in hooks

### Phase 3: Agent Spawning
1. Implement `AgentSpawner` class
2. Support multiple runtimes (claude, codex, cursor)
3. Process management and monitoring

### Phase 4: Convoy Execution
1. Convoy state machine
2. Bead assignment to agents
3. Progress tracking
4. Completion handling

### Phase 5: Mail System
1. Mail queue implementation
2. Delivery mechanism
3. Inbox management

### Phase 6: Monitoring
1. Witness per-rig health checks
2. Deacon cross-rig supervision
3. Dashboard TUI with Rich/Textual

## 🎨 Design Philosophy

> "The best of all worlds: Python agility, Go orchestration concepts, TypeScript UI patterns, and Dolt persistence."

1. **Plugins Over Core** - Everything is a plugin
2. **Python Foundation** - Runtime stays Python
3. **External Binaries** - Use `bd` and `dolt` where they excel
4. **Event-Driven** - Callback system for loose coupling
5. **Git-Native** - Work survives restarts via git

## 📚 References

- **Gastown**: https://github.com/steveyegge/gastown
- **Beads**: https://github.com/steveyegge/beads
- **Claude-code**: https://github.com/jarmuine/claude-code (research)
- **Dolt**: https://github.com/dolthub/dolt

---

*Built with 🐕 by Richard the Code Puppy*

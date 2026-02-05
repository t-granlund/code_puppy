// Data Repository
const repoData = {
    stats: {
      commits: "31 (Current Session)",
      linesOfCode: "15,000+",
      testsPassing: 98,
      version: "2.0.0-hybrid"
    },
    roles: {
      ORCHESTRATOR: {
        id: "ORCHESTRATOR",
        name: "Orchestrator",
        color: "#a855f7", // Purple
        icon: "🧠"
      },
      REASONING: {
        id: "REASONING",
        name: "Reasoning",
        color: "#f59e0b", // Amber
        icon: "🛡️"
      },
      CODING: {
        id: "CODING",
        name: "Coding",
        color: "#ef4444", // Red
        icon: "⚡"
      },
      LIBRARIAN: {
        id: "LIBRARIAN",
        name: "Librarian",
        color: "#10b981", // Emerald
        icon: "📚"
      }
    },
    agents: [
      { name: "Pack Leader", role: "ORCHESTRATOR", file: "agent_pack_leader.py", desc: "The primary coordinator. Delegates tasks to specialized agents." },
      { name: "Helios", role: "ORCHESTRATOR", file: "agent_helios.py", desc: "Specialized in long-range task planning and sun-like oversight." },
      { name: "Epistemic Architect", role: "ORCHESTRATOR", file: "agent_epistemic_architect.py", desc: "Maintains the 'Knowledge Graph' of the project structure." },
      { name: "Manager", role: "ORCHESTRATOR", file: "agent_manager.py", desc: "High-level goal decomposition and resource allocation." },
      { name: "Planning", role: "ORCHESTRATOR", file: "agent_planning.py", desc: "Detailed execution planning." },
      
      { name: "Shepherd 🐕", role: "REASONING", file: "pack/shepherd.py", desc: "Code review critic - guides the flock toward quality code." },
      { name: "Watchdog 🐕‍🦺", role: "REASONING", file: "pack/watchdog.py", desc: "The QA critic. Ensures tests exist and pass." },
      { name: "Security Auditor", role: "REASONING", file: "agent_security_auditor.py", desc: "Scans for vulnerabilities and security flaws." },
      { name: "QA Expert", role: "REASONING", file: "agent_qa_expert.py", desc: "Deep analysis of test strategies." },
      { name: "Code Reviewer", role: "REASONING", file: "agent_code_reviewer.py", desc: "General purpose code reviewer." },
      
      { name: "Husky 🐺", role: "CODING", file: "pack/husky.py", desc: "Task executor (Sled Dog) for heavy lifting in worktrees." },
      { name: "Python Programmer", role: "CODING", file: "agent_python_programmer.py", desc: "Expert in Python implementation." },
      { name: "Code Puppy", role: "CODING", file: "agent_code_puppy.py", desc: "The original friendly coding assistant." },
      { name: "Creator Agent", role: "CODING", file: "agent_creator_agent.py", desc: "Filesystem creation specialist." },
      
      { name: "Terrier 🐕", role: "LIBRARIAN", file: "pack/terrier.py", desc: "Worktree specialist. Digs parallel worktrees." },
      { name: "Retriever 🦮", role: "LIBRARIAN", file: "pack/retriever.py", desc: "Merge specialist. Fetches completed feature branches." },
      { name: "Bloodhound 🐕‍🦺", role: "LIBRARIAN", file: "pack/bloodhound.py", desc: "Issue tracking specialist. Follows dependency scents." },
      { name: "JSON Agent", role: "LIBRARIAN", file: "json_agent.py", desc: "Specialized in structured data parsing." }
    ],
    epistemic: {
      primitives: [
        { name: "Assumption", desc: "Explicit beliefs we take as given." },
        { name: "Hypothesis", desc: "Falsifiable claims with confidence tracking." },
        { name: "Evidence", desc: "Observable data supporting/refuting hypotheses." },
        { name: "Constraint", desc: "Hard and soft limits on behavior." }
      ],
      lenses: [
        { name: "🧠 Philosophy", desc: "What are we assuming? Hidden assumptions, category errors." },
        { name: "📊 Data Science", desc: "Can we measure this? Metrics plan, experiment design." },
        { name: "🛡️ Safety/Risk", desc: "What could go wrong? Risk flags, abuse vectors." },
        { name: "🔷 Topology", desc: "What's the structure? Dependencies, phase transitions." },
        { name: "∑ Theoretical Math", desc: "Is this consistent? Minimal axioms, counterexamples." },
        { name: "⚙️ Systems Eng", desc: "Can we build this? Service boundaries, failure recovery." },
        { name: "👤 Product/UX", desc: "Does this help users? Value hypotheses, MVP scope." }
      ],
      pipeline: [
        { stage: "—", name: "Project Discovery", desc: "Bootstrap: scan existing artifacts, detect resume point" },
        { stage: 0, name: "Philosophical Foundation", desc: "Internalize Ralph Loops and core principles" },
        { stage: 1, name: "Epistemic State Creation", desc: "Surface assumptions, hypotheses, constraints" },
        { stage: 2, name: "Lens Evaluation", desc: "Apply 7 expert perspectives" },
        { stage: 3, name: "Gap Analysis", desc: "Identify CRITICAL/HIGH/MEDIUM/LOW gaps" },
        { stage: 4, name: "Goal Emergence", desc: "Generate candidates, run through 6 gates" },
        { stage: 5, name: "MVP Planning", desc: "Create minimal viable plan with rollback" },
        { stage: 6, name: "Spec Generation", desc: "Generate full specs, readiness check" },
        { stage: 7, name: "Pre-Flight Auth", desc: "Detect & verify all auth requirements" },
        { stage: 8, name: "Build Execution", desc: "Phase → Milestone → Checkpoint → Verify" },
        { stage: 9, name: "Improvement Audit", desc: "Evidence → Analysis → Recommendation loop" },
        { stage: 10, name: "Gap Re-Inspection", desc: "What new gaps emerged? Re-validate" },
        { stage: 11, name: "Question Tracking", desc: "Update epistemic state, close hypotheses" },
        { stage: 12, name: "Verification Audit", desc: "End-to-end check across all layers" },
        { stage: 13, name: "Documentation Sync", desc: "Update all docs, then loop to Stage 9" }
      ],
      loop: [
        { step: 1, name: "Observe", desc: "Gather evidence from environment" },
        { step: 2, name: "Orient", desc: "Apply Lenses to update Epistemic State" },
        { step: 3, name: "Decide", desc: "Formulate Plan based on current State" },
        { step: 4, name: "Act", desc: "Execute Agents via Orchestrator" }
      ]
    },
    infrastructure: {
      tiers: [
        { id: 1, name: "Architect", model: "Claude Opus 4.5", purpose: "Strategy & Security", cost: "$$$", speed: "Show" },
        { id: 2, name: "Builder High", model: "Codex 5.2", purpose: "Complex Refactoring", cost: "$$", speed: "Med" },
        { id: 3, name: "Builder Mid", model: "Sonnet 4.5", purpose: "Logic & Review", cost: "$$", speed: "Fast" },
        { id: 4, name: "Librarian", model: "Gemini 3 Flash", purpose: "Search & Context", cost: "$", speed: "Very Fast" },
        { id: 5, name: "Sprinter", model: "Cerebras GLM 4.7", purpose: "Generation", cost: "¢", speed: "Extreme (2k tok/s)" }
      ]
    }
  };
  
  // App Logic
  document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    renderDashboard();
    renderAgents('ALL');
    renderEpistemic();
    renderInfrastructure();
    initSimulator();
  });
  
  function initNavigation() {
    const items = document.querySelectorAll('.nav-item');
    const pages = document.querySelectorAll('.page');
    
    items.forEach(item => {
      item.addEventListener('click', () => {
        // Update nav UI
        items.forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        
        // Switch page
        const targetId = item.dataset.target;
        pages.forEach(p => p.classList.remove('active'));
        document.getElementById(targetId).classList.add('active');
        
        // Re-render if needed
        if (targetId === 'agents') renderAgents('ALL');
      });
    });
  }
  
  // 1. Dashboard Renderer
  function renderDashboard() {
    // Stats
    document.getElementById('stat-commits').innerText = repoData.stats.commits;
    document.getElementById('stat-tests').innerText = repoData.stats.testsPassing + " Passing";
    
    // Feature highlights are static in HTML
  }
  
  // 2. Agents Renderer (with filtering)
  function renderAgents(filter) {
    const container = document.getElementById('agent-grid');
    container.innerHTML = '';
    
    const filtered = filter === 'ALL' 
      ? repoData.agents 
      : repoData.agents.filter(a => a.role === filter);
      
    filtered.forEach(agent => {
      const role = repoData.roles[agent.role];
      const card = document.createElement('div');
      card.className = 'agent-card';
      card.innerHTML = `
        <div class="agent-top-border" style="background-color: ${role.color}"></div>
        <div class="agent-header">
          <div style="font-size: 1.5rem;">${role.icon}</div>
          <div class="agent-role-badge" style="color: ${role.color}; border-color: ${role.color}40;">
            ${role.name.toUpperCase()}
          </div>
        </div>
        <h3 style="margin: 0 0 0.5rem 0;">${agent.name}</h3>
        <div class="agent-file">${agent.file}</div>
        <p style="color: #94a3b8; font-size: 0.9rem; margin: 0; line-height: 1.5;">${agent.desc}</p>
      `;
      container.appendChild(card);
    });
    
    // Setup filter buttons
    const btns = document.querySelectorAll('.filter-btn');
    btns.forEach(btn => {
      btn.onclick = () => {
        btns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        renderAgents(btn.dataset.filter);
      };
    });
  }
  
  // 3. Epistemic Renderer
  function renderEpistemic() {
    // Loop
    const loopContainer = document.getElementById('loop-container');
    repoData.epistemic.loop.forEach(step => {
      const div = document.createElement('div');
      div.className = 'loop-step';
      div.innerHTML = `
        <div style="color: #a855f7; font-family: monospace; font-size: 0.8rem; margin-bottom: 0.5rem;">STEP 0${step.step}</div>
        <div style="font-weight: 700; font-size: 1.25rem; margin-bottom: 0.5rem;">${step.name}</div>
        <div style="color: #94a3b8; font-size: 0.9rem;">${step.desc}</div>
      `;
      loopContainer.appendChild(div);
    });
    
    // Lenses
    const lensesList = document.getElementById('lenses-list');
    repoData.epistemic.lenses.forEach(lens => {
      const div = document.createElement('div');
      div.className = 'feature-list-item';
      div.innerHTML = `
        <span style="color: #3b82f6; font-family: monospace;">${lens.name}</span>
        <span style="color: #64748b; font-size: 0.9rem;">${lens.desc}</span>
      `;
      lensesList.appendChild(div);
    });
    
    // 14-Stage Pipeline
    const pipelineContainer = document.getElementById('pipeline-list');
    if (pipelineContainer) {
      repoData.epistemic.pipeline.forEach(stage => {
        const div = document.createElement('div');
        div.className = 'feature-list-item';
        const stageLabel = stage.stage === "—" ? "—" : `Stage ${stage.stage}`;
        const stageColor = stage.stage === "—" ? "#10b981" : 
                          stage.stage <= 1 ? "#a855f7" :
                          stage.stage <= 4 ? "#3b82f6" :
                          stage.stage <= 7 ? "#f59e0b" :
                          stage.stage <= 10 ? "#10b981" : "#06b6d4";
        div.innerHTML = `
          <span style="color: ${stageColor}; font-family: monospace; min-width: 70px;">${stageLabel}</span>
          <span style="font-weight: 600; color: #f1f5f9; min-width: 150px;">${stage.name}</span>
          <span style="color: #64748b; font-size: 0.85rem;">${stage.desc}</span>
        `;
        pipelineContainer.appendChild(div);
      });
    }
  }
  
  // 4. Infrastructure Renderer
  function renderInfrastructure() {
    const tierGrid = document.getElementById('infra-grid');
    tierGrid.innerHTML = ''; // Clear for re-renders on simulation
    
    repoData.infrastructure.tiers.forEach(tier => {
      const div = document.createElement('div');
      div.className = 'tier-card';
      div.id = `tier-${tier.id}`;
      div.innerHTML = `
        <div style="font-size: 0.75rem; color: #94a3b8; font-family: monospace; margin-bottom: 0.5rem;">TIER ${tier.id}</div>
        <div style="font-weight: 700; margin-bottom: 0.25rem;">${tier.name}</div>
        <div style="background: rgba(0,0,0,0.3); padding: 0.25rem; font-family: monospace; font-size: 0.75rem; border-radius: 4px; text-align: center; margin-bottom: 1rem;">${tier.model}</div>
        <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #94a3b8; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 0.5rem;">
          <span>${tier.cost}</span>
          <span>${tier.speed}</span>
        </div>
      `;
      tierGrid.appendChild(div);
    });
  }
  
  // 5. Simulation Logic
  function initSimulator() {
    const input = document.getElementById('sim-input');
    const logs = document.getElementById('sim-logs');
    const resultDiv = document.getElementById('sim-result');
    const simulateBtn = document.getElementById('sim-btn');
    
    const runSim = () => {
      const text = input.value.toLowerCase();
      if (!text) return;
      
      let tierId = 3;
      let reason = "General reasoning task (Default)";
      
      if (text.includes("plan") || text.includes("architect")) {
        tierId = 1; reason = "Strategy/Architecture keywords detected";
      } else if (text.includes("write") || text.includes("create") || text.includes("generate")) {
        tierId = 5; reason = "High-volume generation keywords detected";
      } else if (text.includes("search") || text.includes("find") || text.includes("context")) {
        tierId = 4; reason = "Retrieval/Context keywords detected";
      }
      
      // Update UI
      const tierData = repoData.infrastructure.tiers.find(t => t.id === tierId);
      
      // Highlight tier
      document.querySelectorAll('.tier-card').forEach(c => c.classList.remove('active'));
      document.getElementById(`tier-${tierId}`).classList.add('active');
      
      // Show result
      resultDiv.style.display = 'grid';
      document.getElementById('res-intent').innerText = reason;
      document.getElementById('res-model').innerText = tierData.model;
      document.getElementById('res-details').innerText = `Tier ${tierId} • ${tierData.speed}`;
    };
    
    simulateBtn.onclick = runSim;
    input.onkeydown = (e) => { if (e.key === 'Enter') runSim(); };
  }

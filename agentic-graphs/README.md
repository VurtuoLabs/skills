# agentic-graphs

Advanced skills for designing graph-based agentic loop architectures with Claude — for engineers building production agentic systems, not an intro to tool-use loops. Framework-agnostic: applies whether you're using the Claude Agent SDK, a graph-orchestration library, or a custom-built loop.

## Skills

### Architecture and state

- **[agent-graph-design](agent-graph-design/SKILL.md)** — When a graph beats a linear loop or a single long-running agent, node granularity, and where to draw the deterministic-code-vs-LLM-judgment line.
- **[graph-state-schema-design](graph-state-schema-design/SKILL.md)** — What belongs in shared state vs. what to recompute, preventing context bloat, reducer design for parallel branches, and schema versioning.
- **[loop-termination-guard](loop-termination-guard/SKILL.md)** — Robust stop conditions: avoiding premature cutoff and runaway loops, detecting non-convergence, and layering multiple guards.
- **[conditional-routing-design](conditional-routing-design/SKILL.md)** — Building router nodes: classifier vs. rule-based routing, keeping routers free of task work, and handling low-confidence decisions.

### Orchestration and resilience

- **[multi-agent-supervisor-orchestrate](multi-agent-supervisor-orchestrate/SKILL.md)** — Supervisor/worker topologies: decomposition criteria, the dispatch-collect-decide loop, context digesting, and failure isolation.
- **[self-correction-loop-design](self-correction-loop-design/SKILL.md)** — Generate-critique-revise loops as separate nodes with concrete pass/fail criteria and bounded iteration.
- **[graph-checkpoint-resume](graph-checkpoint-resume/SKILL.md)** — Persistence and checkpointing so long-running graphs survive crashes without corrupting state or double-firing side effects.
- **[human-in-the-loop-interrupt](human-in-the-loop-interrupt/SKILL.md)** — Approval/interrupt checkpoints before irreversible actions, payload design, escalation, and avoiding rubber-stamp fatigue.

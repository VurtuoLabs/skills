---
name: graph-state-schema-design
description: Guidance for designing the shared state object that flows through nodes in an agent graph — what to persist versus recompute, preventing unbounded state growth over long-running loops, designing merge/reducer behavior for parallel branches, and versioning schemas so checkpoints survive graph evolution. TRIGGER when: defining or refactoring the state schema for a multi-node agent graph, diagnosing quality or cost degradation over long agent runs, adding parallel/fan-out branches that write to shared state, or migrating a graph's state shape while old checkpoints exist. DO NOT TRIGGER when: the question is about a single prompt's content or a one-off tool call's input/output shape with no persistence across steps.
triggers:
  - "agent state schema"
  - "graph state design"
  - "state reducer merge"
  - "context bloat long-running agent"
  - "checkpoint schema versioning"
---

# graph-state-schema-design

State is the graph's only memory between nodes and the only thing that survives a checkpoint/resume. Every field you add is a field every downstream node either reads, ignores, or gets confused by — and in loops, every field is a field that can silently grow every iteration until it degrades output quality or blows the context budget.

## What belongs in state vs. what should be recomputed or fetched

Default to *not* storing something in state; only add a field when a specific downstream node needs it and fetching it fresh is genuinely more expensive or non-idempotent (e.g., a user's one-time clarifying answer, an LLM judgment already made, an ID that's expensive to re-resolve).

- **Store**: irreversible decisions and their justification (routing choices, plan steps already committed to, approvals obtained), external identifiers needed to correlate with the outside world (ticket IDs, transaction IDs), and *summaries* of large artifacts, not the artifacts themselves.
- **Recompute/fetch fresh**: anything derivable from a source of truth that changes over the run — file contents, API responses, current system status. Storing a stale copy of a file's contents in state instead of re-reading it on the node that needs it is a common source of the agent confidently acting on outdated information three iterations later.
- **Never store raw tool output as permanent state** — store a reference (path, ID, hash) plus a short digest, and re-fetch the full payload only in the node that actually needs the detail. This is the single highest-leverage rule for both context bloat and staleness bugs.
- Distinguish *working state* (scratch values a node needs to pass to its immediate successor) from *durable state* (things that must survive a checkpoint/resume and be meaningful to a human inspecting history). Working state can be aggressively pruned; durable state needs a stability contract.

## Avoiding unbounded state growth

The dominant failure mode in long-running graphs is not a crash — it's silent quality decay as the state (and therefore the context every node sees) grows every iteration until the model is drowning in its own history and starts ignoring instructions, repeating actions, or losing track of the actual goal, while cost per iteration climbs linearly or worse.

- **Append-only lists are the usual culprit.** A `messages` or `actions_taken` list that grows every loop iteration eventually dominates the prompt. Cap it explicitly: keep the last N entries verbatim and replace older ones with a periodically-regenerated summary node whose only job is compression — this is a real node in the graph, not an afterthought.
- **Distinguish accumulation from replacement.** Fields like `current_plan` or `latest_error` should be *replaced* each iteration, not appended to. Auditing every list-typed field in your schema and asking "should this ever be truncated, and by whom" is a mandatory design step, not an optimization to defer.
- **Budget state by node, not just globally.** A node that only needs the last user message and a plan summary shouldn't receive the full accumulated tool-call history just because it's sitting in shared state — project state down to a node-specific view rather than handing every node the entire object. This also reduces the blast radius when one field's shape changes.
- **Watch for state that grows because cleanup was never wired to the cycle that produces it.** If a retry loop appends a new `attempt` record each pass and nothing ever prunes or summarizes old attempts, a stuck loop that takes 40 iterations to converge (or never does) will silently 10x your token cost before any other guard fires.

## Reducers and merge behavior for parallel branches

Fan-out into parallel branches means multiple nodes may write to state concurrently before a join; the merge behavior is not an implementation detail, it's a design decision that determines correctness.

- Every field touched by more than one parallel branch needs an explicit reducer — last-write-wins is the default in most frameworks and is *wrong* for most fields (it silently discards a sibling branch's work with no error). Decide, per field: overwrite, append, union-by-key, max/min, or custom merge — and write it down next to the schema, not just in code.
- Prefer namespacing over merging where possible: give each parallel branch its own sub-key (`branch_a_result`, `branch_b_result`) and merge explicitly in the join node's logic, where you can apply judgment (including LLM judgment) about conflicting findings, rather than relying on an automatic reducer to paper over disagreement.
- For counters/budgets shared across parallel branches (token spend, step count), the reducer must be associative and commutative (sum) — never a raw overwrite, or concurrent branches will race and undercount the very budget meant to bound them.
- Test merge behavior explicitly with a scenario where two branches disagree (both propose an answer, both find a different bug) — if your reducer doesn't have a defined behavior for conflicting non-null values in the same field, you will discover the actual behavior in production, not in review.

## Versioning state schema across checkpoints

A graph that runs long enough to be checkpointed will outlive at least one schema change; treat this as certain, not hypothetical, from the first design.

- Stamp every checkpoint with a schema version field written by the graph itself, not inferred from shape. Inferring version from "does this field exist" breaks the moment you rename rather than add a field.
- Write explicit migration functions keyed by version (v1→v2, v2→v3) applied on load, rather than making every node defensively handle every historical shape — the latter turns node logic into an accretion of `if field missing` checks that never gets cleaned up.
- Additive changes (new optional field) are safe by default; removals and renames are not — provide a compatibility shim for at least one deploy cycle, and log when an old-shape checkpoint is migrated so you can track how long old runs are still resuming in production.
- Never silently drop unknown fields on load if you might need to roll the graph code back — round-trip unknown fields through untouched so a rollback doesn't lose data written by the newer version.

## Anti-patterns to avoid

- Storing full tool outputs (file contents, raw API responses) directly in durable state instead of references plus summaries.
- An unbounded append-only history field with no truncation or summarization node feeding it.
- Relying on framework-default last-write-wins merge for every field without auditing which fields are actually safe under that rule.
- Letting node logic branch on "does field X exist" as a substitute for real schema versioning — this rots into unmaintainable defensive code within a few schema changes.
- Handing every node the entire global state object instead of a projected, node-specific view, inflating every prompt regardless of what that node actually needs.

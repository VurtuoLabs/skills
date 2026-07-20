---
name: graph-checkpoint-resume
description: Designs persistence and checkpointing for long-running graph-based agent loops so they survive crashes, restarts, and redeploys without corrupting external state or losing progress. Covers what a checkpoint must capture, frequency tradeoffs, idempotency for side-effecting nodes on resume, and handling graph-definition drift between checkpoint write and resume. TRIGGER when: designing durability/persistence for a multi-step or long-running agent graph, an agent process needs to survive restarts or deploys mid-run, a resumed run re-executed a side effect it shouldn't have, or a graph's node structure changed and old checkpoints need to still resume correctly. DO NOT TRIGGER when: the agent loop is short-lived and stateless (a single request/response with no need to survive a crash), or the question is about conversation memory/context management rather than execution-state durability.
triggers:
  - "agent checkpoint design"
  - "graph resume after crash"
  - "durable agent execution"
  - "idempotent side effects resume"
---

# graph-checkpoint-resume

Checkpointing turns a long-running graph from "restart from scratch on any failure" into "resume from the last durable point" — the hard part is deciding what "durable point" means and what happens to the world between the crash and the resume.

## What a checkpoint must capture

- Minimum viable checkpoint: the current node/edge position in the graph, the full state object (or a pointer to it) as of that node's completion, and a monotonic version/step counter. Without the step counter you can't detect duplicate resumes or out-of-order replay.
- Decide between full-state snapshot and event-log replay as your persistence model. Snapshots are simple to resume (load and go) but expensive if state is large and written every node; event logs (append the state *delta* per node, replay to reconstruct) are cheaper to write but require the replay logic itself to stay stable and deterministic, which is its own maintenance burden.
- A hybrid is usually right for production: periodic full snapshots (every K nodes or every durable milestone) plus an event log since the last snapshot, so resume replays at most K deltas instead of the whole history.
- Capture enough metadata alongside state to make the checkpoint self-describing: the graph version/hash that produced it, the model/tool versions in use, and a checksum of the state schema. A checkpoint that can't identify what produced it can't be safely validated before resume.
- Do not store live handles (open connections, in-memory locks, unserialized closures) in checkpointed state — only serializable data and references (IDs, URLs) that can be re-resolved on resume.

## Checkpoint frequency tradeoffs

- Checkpointing every node maximizes resumability granularity but multiplies write volume and latency, especially painful when nodes are chatty (many small LLM calls in a tight sub-loop) — you end up paying storage I/O costs comparable to the LLM call itself.
- Checkpointing only at "durable milestones" (after a side effect commits, after a subagent dispatch completes, before a human-approval gate) reduces write volume but means a crash mid-milestone loses all work back to the last one — size milestones so that lost work is cheap to redo (idempotent, side-effect-free) even if it's not instant.
- A practical heuristic: checkpoint immediately before and after any node with an external side effect (regardless of its position in a "milestone" scheme), and checkpoint on a time/step interval for the purely-computational stretches in between.
- Make checkpoint writes themselves durable and atomic (write-new-then-swap-pointer, not in-place overwrite) — a crash during the checkpoint write itself must never leave a corrupted or half-written checkpoint that a resume then loads.

## Non-idempotent side effects on resume

- Classify every node as pure, idempotent-effectful (safe to re-run — e.g., an upsert keyed by a stable ID), or non-idempotent-effectful (unsafe to re-run — e.g., send email, charge a card, post a message). Only the last category needs special resume handling; conflating all three into "just retry on resume" is the most common source of duplicate side effects.
- For non-idempotent nodes, record a durable "effect committed" marker as part of the same transaction (or immediately after) that performs the effect, before advancing the checkpoint. On resume, check the marker first: if present, skip re-execution and replay only the *recorded result* of the effect into state.
- Where the external system supports it, prefer converting non-idempotent effects into idempotent ones at the source — idempotency keys on payment/email/webhook APIs turn "did I already send this?" into the receiving system's problem, which is far more reliable than an in-graph marker alone.
- For effects with no idempotency support (e.g., a legacy SOAP call), consider a two-phase pattern: a "commit intent" checkpoint written before the call, and a "commit confirmed" checkpoint written after — on resume, an intent-without-confirmation state routes to a reconciliation node (check the external system's actual state) rather than blindly re-calling or blindly skipping.
- Never resume directly into a node with side effects without first re-validating its preconditions — state, wall-clock time, and the external system may all have moved on since the checkpoint was written (e.g., a price quote embedded in state may have expired).

## Handling graph-definition drift

- Tag every checkpoint with the graph version/hash that wrote it, and validate that tag against the currently deployed graph before resuming — silently resuming a checkpoint written by an old graph into new node code is how you get a node executing with a state shape it wasn't designed for.
- For additive changes (new optional field, new node appended after existing ones), resume is generally safe if you write defensive defaults for fields absent in older checkpoints. For structural changes (removed node, renamed edge, reordered dependencies), treat old checkpoints as incompatible by default and require an explicit migration function rather than a best-effort resume.
- Maintain a small migration registry keyed by graph version pairs (v3->v4 state transform) rather than trying to make every node tolerate every past schema — this keeps node code clean and puts all the compatibility logic in one auditable place.
- When a checkpoint's node position no longer exists in the current graph (the node was deleted or merged), fail closed: route to a human-reviewable "stale checkpoint" state rather than guessing which current node is the closest equivalent.

## Anti-patterns to avoid

- Snapshotting only the LLM conversation history and calling that "state" — it omits tool call results, side-effect markers, and control-flow position, none of which are reliably re-derivable by replaying the conversation through the model again.
- Retrying an entire node (including its side effects) on any resume, on the assumption that "the LLM call is the expensive/risky part" — the side effect is usually the actually dangerous part to duplicate, not the LLM call.
- Loading a checkpoint and resuming without checking its graph-version tag, silently corrupting state when the graph has since changed shape.
- Treating checkpoint writes as best-effort/fire-and-forget logging instead of a synchronous, acknowledged step the graph waits on before proceeding past a side effect.

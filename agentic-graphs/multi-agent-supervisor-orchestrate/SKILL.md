---
name: multi-agent-supervisor-orchestrate
description: Designs supervisor/worker graph topologies where a coordinating Claude instance dispatches work to specialized subagents and integrates their results. Covers decomposition criteria, the supervisor's dispatch-collect-decide loop, context digesting to prevent state bloat, and failure isolation between workers. TRIGGER when: designing a multi-agent system with a coordinator and specialized subagents, deciding whether to split one agent's tool set across multiple agents, debugging a supervisor whose context window fills up or whose decisions degrade over long runs, or handling a subagent that returns bad/hallucinated output. DO NOT TRIGGER when: building a single agent with a flat tool-use loop and no delegation, or designing simple sequential pipelines with no dynamic dispatch decision.
triggers:
  - "supervisor agent pattern"
  - "multi-agent orchestration"
  - "subagent dispatch design"
  - "worker agent coordination"
---

# multi-agent-supervisor-orchestrate

Supervisor/worker graphs trade a bigger single-agent context and tool surface for isolation, specialization, and parallelism — but only pay off if the decomposition boundary is real and the supervisor doesn't just become a second monolith with extra hops.

## When to decompose vs. keep one agent

- Decompose when subagents need genuinely disjoint tool sets, system prompts, or model configs — e.g., a code-review persona that must never see write tools, or a research agent with web access that shouldn't also hold prod DB credentials. Heterogeneous *permissions* are a stronger signal than heterogeneous *tasks*.
- Decompose when a subtask's optimal context is actively harmful to the main task — a worker that needs to read 200 log lines to find one root cause pollutes the supervisor's context if that all happens inline instead of behind a subagent boundary.
- Do not decompose just to organize prompts. If every worker shares the same tools, model, and trust level, you've added dispatch latency and serialization overhead for zero isolation benefit — use a single agent with well-scoped tool descriptions instead.
- A useful test: if you can't articulate what the supervisor should NOT see from a given worker, you don't have a real decomposition, you have a subroutine call dressed up as an agent.

## Designing the supervisor's decision loop

- Structure the loop as three explicit phases per iteration: dispatch (pick next worker + construct its input), collect (receive worker output), decide (route to another worker, request revision, or terminate). Keeping these as distinct graph nodes — not one blob of reasoning — makes the loop debuggable and lets you checkpoint between phases.
- The dispatch step should construct a task-scoped input for the worker, not forward the supervisor's entire running context. Pass the minimum slice of state the worker needs plus an explicit success criterion; this is what keeps workers from re-deriving or guessing intent.
- The decide step needs an explicit termination condition that's checkable without another LLM call where possible — e.g., "all required worker outputs present and validated" as code, with the LLM only invoked to handle the ambiguous residual cases (which worker next, is this output sufficient).
- Bound the loop with both a max-dispatch counter and a max-wall-clock budget, independent of any single worker's timeout. Supervisors that only bound individual worker calls can still loop indefinitely across dispatches.

## Avoiding context pollution

- Never append a worker's full raw transcript to supervisor state by default. Have each worker return a structured digest (a fixed schema: result, confidence, evidence pointers, open questions) and store the raw transcript in a side store keyed by a reference the supervisor can pull on demand.
- Digests should be worker-authored, not supervisor-summarized — asking the supervisor to summarize each worker's output after the fact just moves the token cost and adds a lossy paraphrase step. Require the worker's own final message to already be in digest form as part of its contract.
- Track a running "state delta" instead of an accumulating log: if the supervisor's job is to build up a plan or document, keep only the current version of that artifact in context plus a short changelog, not every prior draft from every worker turn.
- Cap how much of a worker's evidence gets inlined verbatim (e.g., a code diff or query result) — inline enough for the supervisor to make its next dispatch decision, and reference the rest by ID so a later node can fetch it only if needed.

## Failure isolation

- Wrap every worker invocation in an explicit outcome type (success / partial / failed / refused), not a bare string. A worker that hallucinates should produce a low-confidence or malformed result the supervisor's validation step can catch, not a plausible-looking string indistinguishable from a real answer.
- Validate worker output against its declared contract (schema, required citations, expected value ranges) before merging it into supervisor state. Treat schema validation failures as a distinct edge from semantic failures — a malformed response should trigger a retry-with-different-worker or escalate-to-human path, not silently pass through.
- Isolate blast radius by giving each worker its own scratch state/session; a worker that goes off the rails should not be able to mutate the supervisor's authoritative state directly — it can only propose a change that the supervisor's merge step accepts or rejects.
- Design a circuit breaker per worker role: after N consecutive failures or contract violations from the same worker type, stop dispatching to it and either fall back to a degraded path or halt for human review, rather than retrying indefinitely and burning budget on a systematically broken worker.

## Anti-patterns to avoid

- Letting the supervisor prompt say "delegate to subagents as needed" with no explicit routing logic — this produces inconsistent decomposition across runs and makes the graph unauditable.
- Concatenating every subagent's full output into the supervisor's next-turn context, turning the supervisor into an accidental context-window stress test after 5-6 dispatches.
- Treating a worker's exception or empty response the same as a valid empty result — silent failure absorption is how corrupted state enters the supervisor without anyone noticing.
- Using one shared mutable state object that all workers read and write directly instead of message-passing through the supervisor, which reintroduces race conditions and makes failure attribution impossible.

---
name: agent-graph-design
description: "Guidance for choosing and shaping a graph-based architecture for an agentic Claude system — deciding when nodes/edges/explicit state beat a simple tool-use loop or a single long-running agent, how to decompose work into nodes, and where to place deterministic code versus LLM judgment. TRIGGER when: designing a new multi-step agent system, refactoring a tangled single-prompt agent into separable stages, deciding whether a workflow needs a graph/state machine at all, or reviewing a graph architecture for over- or under-decomposition. DO NOT TRIGGER when: the task is writing a single tool call, debugging one node's prompt content, or doing generic LLM prompt-engineering unrelated to control flow."
triggers:
  - "graph architecture"
  - "agent graph design"
  - "nodes and edges"
  - "decompose agent workflow"
  - "when to use a graph vs a loop"
---

# agent-graph-design

A graph is a control-flow commitment, not a default. It buys explicit state transitions, resumability, and parallelism at the cost of upfront modeling work and rigidity against novel paths. Reach for it only when the problem's decision structure actually has the shape a graph captures — otherwise you're paying graph tax for loop-shaped work.

## When a graph earns its cost

- **Single long-running agent (tool loop, no graph)** is right when the task is genuinely open-ended exploration where the *next best action* can only be decided in-context, turn by turn — research, debugging, open-ended coding. Imposing nodes here just recreates the tool loop with extra ceremony.
- **Linear pipeline (no cycles, maybe no LLM-driven branching)** is right when the stages are known in advance and always run in the same order — extract, transform, validate, write. Don't call this a "graph" internally even if your framework requires you to express it as one; treat branches as the exception, not the norm.
- **Branching/cyclic graph** earns its keep when there are qualitatively different *modes* of work that need different tools, different system prompts, different context windows, or different models — and the transition between modes is a real decision point that benefits from being inspectable, interruptible, and independently retryable.
- **Hierarchical (supervisor + subagent graphs)** is right when subproblems are context-isolable — a subagent can do useful work seeing only its own slice of state, and the parent only needs the subagent's summary, not its scratch work. If the parent needs the subagent's full transcript to make its next decision, you haven't found an isolation boundary — you've just added an expensive extra hop.

The test that matters: draw the actual decision tree of the problem on paper first, independent of any framework. If it's a straight line, don't build branches "for future flexibility" — YAGNI applies to graph topology as much as to code. If it's genuinely a tree or has real cycles (retry-with-different-strategy, plan-critique-replan), the graph shape should be a direct trace of that tree, not an approximation of it bent to fit a framework's example topology.

## Node granularity

A node is one coherent unit of *LLM work with a single objective*, not one LLM call and not one tool call. Getting this wrong in either direction is the most common graph-design mistake.

- **Too coarse**: a node that does "research, then draft, then critique" in one prompt collapses distinct objectives into one context, so the model can't be steered, retried, or checkpointed at the sub-step level. If you find yourself writing prompts with numbered phases inside a single node, that's three nodes wearing a trenchcoat.
- **Too fine**: a node per tool call turns the graph into a de-facto tool loop with state-passing overhead at every step, and now every tool call pays graph-transition latency and (if checkpointed) I/O cost. A node should own an objective that may legitimately take several tool calls to satisfy internally — e.g., "gather all context needed to write the patch" is one node even if it calls grep, read, and a sub-search tool three times each.
- Rule of thumb: a node boundary should coincide with a point where you'd want to (a) inspect the state before/after independently, (b) retry just this unit without redoing prior work, or (c) swap the model/prompt/tool-set without touching neighbors. If none of those apply, merge it with its neighbor.
- Name nodes after the *decision or transformation they own* (`triage`, `draft_patch`, `verify_against_tests`), not after implementation details (`call_llm_1`). The name should make the graph diagram readable as a description of the workflow to someone who has never seen the code.

## Deterministic code vs. LLM judgment

Put a step in deterministic code whenever the mapping from input to output is a function you could write and test, even if it's currently "easy" for the model to do it. Every judgment call routed through the LLM instead of code is a recurring cost, a recurring latency hit, and a nondeterminism source that makes the whole graph harder to test.

- Classification with a fixed, enumerable rule set (status codes, regex-matchable intents, schema validation) → code. Classification requiring semantic understanding of open-ended text → LLM node, but keep it narrowly scoped to *only* the classification, not classification-plus-next-step.
- Data transformation, aggregation, formatting, retries with backoff, pagination — all code. These are exactly the tasks that look like "just have the agent do it" but silently become a major chunk of your token spend and your flakiest failure surface when left to the model.
- Judgment that requires weighing ambiguous, under-specified, or adversarial input against soft criteria — that's the LLM's job, and trying to encode it as rules produces a maintenance sinkhole of ever-multiplying edge-case branches.
- A useful heuristic during design review: for every LLM node, ask "if this call returned garbage, would deterministic code downstream catch it?" If the answer is no, you likely need either a validation node or to move part of that node's work into code.

## Letting graph shape follow decision structure

Resist the urge to route everything through a central supervisor "for control" when the actual dependency structure is a pipeline, and resist forcing a strict pipeline when the real workflow has genuine cycles (plan → execute → critique → replan). A supervisor pattern is justified specifically when the *next step genuinely depends on a judgment call that only the LLM can make with the full picture* — not merely because you want one place to put logging or error handling (use middleware/hooks for that instead).

Cycles should map to actual retry-with-different-approach semantics, not runaway loops with a cap slapped on as an afterthought — see loop-termination-guard for how to bound cycles correctly once you've decided you need one.

## Anti-patterns to avoid

- Forcing every workflow through a graph framework "for consistency" even when it's a straight pipeline with zero branching — adds indirection with no payoff.
- One node per tool call, turning the graph into a slow, checkpoint-heavy re-implementation of the underlying tool loop.
- A supervisor node whose only job is fan-out/fan-in bookkeeping with no actual judgment — that's orchestration code, not an LLM call.
- Naming nodes after mechanics (`step1`, `llm_call_b`) instead of the decision or transformation they own, making the graph unreadable as documentation.
- Encoding a rule-based classifier's logic as an LLM prompt because it was faster to write, then discovering it's nondeterministic on edge cases that a switch statement would have handled exactly.

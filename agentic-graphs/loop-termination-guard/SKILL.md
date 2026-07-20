---
name: loop-termination-guard
description: "Guidance for designing robust termination conditions for cyclic agent graphs — avoiding both premature cutoff from naive iteration caps and runaway loops with no cap, detecting non-convergence (repeated failed actions, oscillation) versus genuine progress, and layering multiple independent guards instead of relying on a single stopping rule. TRIGGER when: designing or reviewing the exit condition of any cyclic node/loop in an agent graph, diagnosing a run that either got cut off mid-task or ran far longer/costlier than expected, or adding a retry/replan cycle to an existing graph. DO NOT TRIGGER when: the workflow is a strictly linear pipeline with no cycles, or the question is about a single tool call's timeout rather than an agentic loop's termination."
triggers:
  - "loop termination"
  - "max iterations agent"
  - "agent stuck loop"
  - "convergence detection"
  - "exit condition design"
---

# loop-termination-guard

Every cycle in an agent graph needs a termination design, not a termination constant. A bare `max_iterations = 10` is not a design — it's a guess that will be wrong in both directions on different inputs, cutting off legitimate multi-step work on hard cases while letting a genuinely stuck loop burn the full budget on easy ones that went sideways.

## Why naive termination fails in both directions

- **Fixed iteration caps cut off mid-task.** A cap sized for the median case truncates the tail — the 5% of inputs that legitimately need 15 steps get chopped at 10 with no signal to the caller that the result is incomplete rather than done. Worse, if the graph doesn't distinguish "hit the cap" from "finished successfully," downstream consumers silently treat a truncated result as final.
- **No cap (or a cap sized "generously") runs forever on a stuck loop**, and a stuck agent loop is rarely an infinite spin — it's usually a slow bleed of plausible-looking but non-progressing steps (re-reading the same file, re-trying a failed API call with cosmetic prompt changes) that each look locally reasonable, so nothing crashes, it just never converges and burns tokens the whole time.
- **The deeper problem with both**: a step counter alone cannot distinguish *productive* iteration from *unproductive* iteration. Termination logic needs a signal about progress, not just a signal about elapsed steps.

## Designing the exit signal

Pick a primary "done" signal deliberately — don't let it default to whichever mechanism was easiest to wire up.

- **Agent self-reported done**: the node itself emits a structured "task complete" signal (a specific field in its output, not a free-text guess parsed post-hoc). Fast and cheap, but trusts the same model that might be confidently wrong about having finished — pair it with a cheap external check where the cost of a false "done" is high.
- **External judge**: a separate node (often a smaller/cheaper model, or deterministic code) evaluates whether the actual success criteria are met, independent of what the working node claims. This catches the case where the agent declares victory prematurely, but adds latency and cost every iteration and needs its own well-specified rubric or it just relocates the confident-but-wrong problem one hop over.
- **Fixed budget as backstop, not primary**: iteration count, token spend, and wall-clock time should always be present, but as an outer bound that fires an explicit "budget exhausted" exit distinct from "task complete" — never as the only signal. Make the two outcomes structurally different in the graph (different exit node, different result field) so callers can't confuse a truncated run with a finished one.
- The right default for most production graphs: self-reported done as the fast path, checked against a lightweight external validation before actually exiting (e.g., "does the diff pass the tests it claims to fix" rather than trusting "I fixed it").

## Detecting non-convergence

A loop that's making no progress looks, from the step counter's perspective, identical to one that's making steady progress — you need a separate signal that inspects *trajectory*, not just count.

- **Repetition detection**: hash or fingerprint the action taken each iteration (tool name + normalized args, or the semantic gist of the step) and compare against recent history. Two or three near-identical actions in a row with no change in outcome is a strong non-convergence signal — fire a distinct "stuck" exit rather than letting it exhaust the budget silently.
- **Oscillation detection**: the harder case — state alternates between two or more prior states (fix A breaks B, fix B breaks A) without ever hashing identical to itself. Detect this by tracking a short window of state fingerprints and checking for cycles of length >1, not just exact repeats of the immediately preceding step.
- **Progress metric, when the domain allows one**: if you can define any monotonic-ish proxy for progress (number of failing tests, diff size converging, distance to a goal state), track it explicitly and treat N consecutive non-improving iterations as a guard trigger — this is far more reliable than pattern-matching on actions themselves.
- **Escalate, don't just kill.** When a stuck-loop guard fires, the best response is usually not "abort" but "route to a different strategy" — bump to a stronger model, hand off to a human-in-the-loop node, or switch the approach node (e.g., from incremental-fix to full-rewrite). Treat convergence failure as a routing decision, not just a kill switch.

## Layering multiple guards

No single guard is sufficient on its own; production graphs need independent, differently-triggered limits that all feed into the same exit path so failure is legible.

- **Step count**: cheapest, catches runaway cycling, but blind to per-step cost variance (ten cheap steps vs. ten steps that each spawn a large subagent are very different budgets).
- **Token/cost budget**: catches the case step count misses — a small number of iterations that are individually expensive (large context re-sent each time, expensive subagent fan-out). Track cumulative spend in state with an associative reducer (see graph-state-schema-design) so parallel branches can't undercount it.
- **Wall-clock time**: catches guards that neither of the above sees — external calls that hang or are slow, not just "many" or "expensive" steps. Needed independently because a loop can be well within step and token budget while still taking unacceptably long due to latency.
- **Semantic convergence check**: the non-convergence detection above, run periodically (not every step, to control its own cost) as a distinct guard from the raw resource budgets.
- Wire all guards to the same termination handler so there's one place that decides "we're stopping, here's why, here's what to hand back" — scattering ad hoc `if step > N: return` checks throughout node code makes it impossible to reason about why a given run actually stopped, and makes post-hoc debugging of terminated runs a search through node internals instead of a single log line.

## Anti-patterns to avoid

- A single `max_iterations` constant as the only termination mechanism, tuned by trial and error against a handful of test cases.
- Treating "hit the budget cap" and "task completed successfully" as the same exit path with no distinguishing signal for the caller.
- Detecting only exact-repeat non-convergence and missing oscillation between two or more non-identical states.
- Killing a stuck loop outright instead of routing it to an escalation/fallback strategy that might actually resolve it.
- Scattering termination checks across many nodes instead of centralizing them behind one guard layer with a single source of truth for "why did this run stop."

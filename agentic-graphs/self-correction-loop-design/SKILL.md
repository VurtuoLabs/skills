---
name: self-correction-loop-design
description: "Designs generate-critique-revise reflection loops as separate graph nodes with distinct roles, concrete pass/fail criteria, and bounded iteration. Covers why same-call self-checking underperforms a separated critique pass, how to write criteria that actually catch errors instead of eliciting vague approval, and when additional revision rounds stop helping. TRIGGER when: building a reflection or self-critique loop into an agent graph, an agent's single-pass output has correctness issues you want to catch before returning it, or a revision loop is running too many rounds without converging. DO NOT TRIGGER when: doing simple one-shot output validation with a deterministic checker (no LLM critique needed), or when the task has no meaningful notion of a \"better\" revision (e.g., open-ended creative generation with no error criteria)."
triggers:
  - "reflection loop design"
  - "generate critique revise"
  - "self-correction agent"
  - "critique pass architecture"
---

# self-correction-loop-design

A reflection loop is a bet that a second pass catches what the first pass missed — that bet only pays off if the critique step is structurally different from the generation step and has something concrete to check against.

## Why separate the critique pass

- Asking a single call to "double check your answer" in the same turn mostly re-elicits the same reasoning that produced the error in the first place — the model has no new information or perspective, just a re-read of its own output through the same lens that already missed the problem.
- A separate critique node breaks the correlation between generation and verification errors. Give it a different prompt framing (adversarial reviewer, not collaborative assistant), and where the error budget justifies the cost, a different model or temperature so its failure modes don't perfectly overlap with the generator's.
- The critique node should not see the generator's chain of reasoning, only its final output plus the original task spec. If it inherits the generator's intermediate justifications, it tends to inherit the generator's blind spots too — critique the artifact, not the artifact's self-narrated defense of itself.
- Structurally, make critique a graph edge with its own state, not a flag inside the generation node. This is what lets you route failed critiques to revision, escalation, or termination independently, and what lets you log critique verdicts separately for eval.

## Defining pass/fail criteria

- "Is this good?" is not a critique criterion, it's a request for a vibe. Replace it with an enumerated checklist derived from the task spec: for code, does it compile/pass the given tests/handle the stated edge cases; for a structured extraction, does every required field have a value with the right type and a traceable source.
- Separate criteria into hard-fail (must be corrected, blocks completion) and soft-fail (worth flagging, doesn't block). Mixing them produces critique output where the generator can't tell what's mandatory, so revisions either over-correct trivial style notes or under-correct real defects.
- Where possible, back critique criteria with a deterministic check the graph runs before ever invoking the critique LLM call — schema validation, unit tests, regex/format checks. Reserve the LLM critique for the class of errors that can't be checked mechanically (reasoning gaps, missed requirements, factual claims).
- Have the critique step cite the specific location and rule violated for each finding (line number, field name, requirement ID) rather than a prose paragraph — this is what lets a revision node make a targeted fix instead of regenerating from scratch and possibly introducing new errors.

## Bounding revision rounds

- Cap rounds explicitly (2-3 is a common effective range) and treat the cap as a graph-level constant, not something the critique node decides at runtime — LLM critics reliably keep finding *something* to flag indefinitely if not told a budget exists.
- Track whether successive critique passes are converging: are hard-fail counts monotonically decreasing, or oscillating/flat? Flat or oscillating hard-fail counts after round 2 is a signal to stop revising and escalate, not a signal to run round 4.
- Distinguish "no more hard-fails" from "critique ran out of things to say" — a critic with an open-ended mandate will find new soft-fail nits every round even after correctness converges, which can make a loop look unconverged when it's actually done.
- When you hit the round cap without a clean pass, route to human review or return the best-scoring draft with its outstanding findings attached — never silently return a still-failing draft as if it passed, and never loop past the cap hoping one more round fixes it.

## Factual/logical vs. stylistic correction

- Reflection loops reliably improve factual and logical defects — an unhandled edge case, a contradicted premise, a miscomputed value — because there's a checkable ground truth the critique can point at and the revision can verifiably fix.
- Stylistic preference has no fixed point: "make it more concise," addressed, often triggers "restore the detail you cut" on the next pass if the critic's taste varies call to call. Style critique without a concrete style guide (e.g., a linter config, a house style doc) tends to make output oscillate rather than converge.
- If a task genuinely needs both, run them as separate passes with separate budgets — exhaust correctness rounds first and lock the content, then run at most one style pass afterward, so style edits can't reintroduce factual drift.
- When you can't tell which category a critique finding falls into, default to treating it as stylistic and cap it at one round — treating ambiguous findings as hard-fails is how loops silently balloon past their intended bound.

## Anti-patterns to avoid

- One LLM call with a prompt like "review and fix your answer" — no separate context, no separation of concerns, indistinguishable from just re-sampling the same distribution.
- Critique prompts that ask "rate this 1-10" or "is this correct?" with no rubric — produces confident-sounding scores with low correlation to actual defect presence.
- Unbounded `while not approved` loops with the approval check delegated to the same critic that never converges, especially when soft-fail and hard-fail findings aren't distinguished.
- Feeding the full critique transcript (including rejected earlier drafts) back into the reviser's context every round — this bloats tokens and can cause the reviser to reintroduce a defect it already fixed two rounds ago because it's now more prominent in context than the current instruction.

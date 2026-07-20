---
name: conditional-routing-design
description: Guidance for building router/branching nodes in an agent graph — choosing between LLM-classifier and deterministic rule-based routing, keeping routing nodes free of task work, handling low-confidence routing decisions, and preventing unhandled cases from silently falling into the wrong branch. TRIGGER when: designing a node whose job is to choose the next node/branch, debugging misrouted requests in a multi-path agent graph, adding a new branch to an existing router, or reviewing routing logic for silent fallthrough. DO NOT TRIGGER when: the branching is a simple deterministic if/else inside otherwise linear code with no LLM involvement and no graph framework, or the question concerns the task work happening inside a branch rather than the decision to enter it.
triggers:
  - "routing node design"
  - "LLM classifier routing"
  - "branch on intent"
  - "low confidence routing"
  - "fallback route"
---

# conditional-routing-design

A router's entire job is to answer one question — which edge do we take — and nothing else. Routers that also do task work, or that have no principled answer for the case they didn't anticipate, are where graph correctness quietly breaks down, because misrouting is often silent: the graph keeps running, just down the wrong path, and nothing errors.

## LLM-classifier vs. deterministic rule-based routing

Choose the mechanism based on whether the routing decision is enumerable and rule-expressible, not based on which is easier to wire up in your framework.

- **Deterministic rules** (regex, schema match, status code, explicit enum from a prior structured output) whenever the space of inputs is genuinely enumerable or already structured — e.g., routing on a webhook's event type, a tool's error code, or a field the *previous* LLM node was asked to emit as structured output. This is strictly cheaper, faster, deterministic, and trivially unit-testable; there is no reason to spend a model call on a decision code can make correctly 100% of the time.
- **LLM classification** when the routing decision requires understanding open-ended natural language intent that cannot be reduced to a rule without an explosion of edge cases — e.g., "is this user asking a question, filing a complaint, or making a request." Keep the classifier's *output* structured and constrained (a fixed enum, not free text) even though its *input* judgment is fuzzy — this is what makes the downstream edge-selection deterministic even though the upstream decision wasn't.
- **The common mistake is pushing a decision one layer too far toward the LLM.** If a prior node already produced a structured field that determines the route, route on that field with code — don't re-ask an LLM "given this ticket, which category is it" a second time when a previous node already classified it. Every redundant LLM-routing hop adds latency, cost, and a fresh chance for the second classifier to disagree with the first.
- **The inverse mistake**: encoding what's actually a semantic judgment as an ever-growing keyword/regex rule list. If your deterministic router has accumulated dozens of special-cased string matches trying to approximate intent, that's a signal the decision belongs to an LLM classifier node instead — the regex pile is a maintenance liability masquerading as determinism.

## Keeping routing nodes single-purpose

A routing node's output should be *only* the next-edge decision (plus, optionally, a short rationale for observability) — never the actual task response.

- The strongest failure pattern here: a node prompted to "answer the question, and if it's actually a billing issue, say so" conflates routing with execution. Now every request pays for a full task attempt even on the branch that turns out wrong, and the eventual correct-branch node has to somehow reconcile or discard the first attempt's output.
- Structure the router's output schema to contain *only* routing-relevant fields (route name, confidence, rationale). If you find yourself wanting to pass the router's "draft answer" downstream because it seemed like a waste to throw away, that's evidence the router did task work it shouldn't have — split it into a separate node.
- This separation also makes the router independently testable: you can eval routing accuracy against a labeled set of inputs → expected routes without needing to also evaluate the quality of downstream task output, which is a different concern with different metrics.

## Handling low-confidence decisions

Treat routing confidence as a first-class output, not an implicit property you infer after the fact from how the rest of the run goes.

- Have the classifier emit an explicit confidence signal (categorical — high/medium/low — is usually more robust than a numeric score, since LLM-emitted numeric confidence is rarely well-calibrated and teams tend to over-trust a number that looks precise).
- Define a real threshold policy: below-threshold confidence should route to a distinct fallback path — a clarification node that asks the user a disambiguating question, a default "safe" branch that a human reviews, or a secondary, more expensive classifier — rather than defaulting to whichever branch happens to be first in the code or the LLM's own default guess. Silently taking the top-scoring route regardless of how close the second-place route scored throws away information you already paid for.
- For multi-way routes where two candidates are close in confidence, consider surfacing both to a downstream disambiguation step rather than forcing a single arbitrary pick — this is often cheaper than a wrong full task execution followed by a retry.
- Log routing decisions with their confidence and rationale even on the happy path; when misrouting is reported later, the ability to see *why* the router picked that edge (not just that it did) is what makes the failure debuggable instead of a shrug.

## Avoiding silent fallthrough on unhandled cases

The most dangerous routing bug is not a wrong route with high confidence — it's an unanticipated input that gets coerced into *some* branch with no signal that the case was actually unhandled.

- Every router must have an explicit, named default/unmatched branch — never let a switch-like structure fall through to "whatever the last `elif` happens to be" or let an LLM classifier's constrained-output schema silently coerce an out-of-taxonomy input into the nearest enum value. If the classifier's answer doesn't cleanly match a known route, that itself is the signal to route to the fallback/unhandled path, not to force-fit it.
- Version and monitor the route taxonomy itself: log the distribution of routes taken over time, and alert when the "unhandled/default" branch's share increases — that's an early warning that the input distribution has shifted or a new case class has emerged that the router was never built to handle, well before it shows up as a user-visible failure.
- When adding a new branch to an existing router, audit whether it was previously being silently absorbed by another branch's rules or by the classifier's nearest-match behavior — a new explicit branch can uncover a chunk of traffic that was being misrouted all along, not just add coverage for genuinely new cases.
- Treat "the router failed to produce valid structured output at all" (malformed JSON, missing required enum field) as a distinct failure path from "chose a valid but low-confidence route" — collapsing parse failures into a default route hides infrastructure problems (prompt drift, schema mismatch after a model upgrade) behind what looks like normal low-confidence routing.

## Anti-patterns to avoid

- A router node that also produces the task's actual answer "just in case," conflating the routing decision with execution.
- Re-classifying with a second LLM call something a prior node already emitted as a structured field.
- A deterministic router with a sprawling, ever-growing list of special-cased string/regex matches trying to approximate what is really a semantic judgment.
- Treating LLM-emitted numeric confidence scores as precise and thresholding on them without acknowledging they're poorly calibrated.
- No explicit default/unmatched branch, so out-of-taxonomy inputs get silently coerced into the nearest known route with no logging or alerting.

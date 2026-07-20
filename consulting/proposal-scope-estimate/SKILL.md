---
name: proposal-scope-estimate
description: Turns discovery or requirements notes into a scoped proposal with effort estimates — breaking work into estimable units, choosing between t-shirt sizing and detailed hour estimates, building in contingency for unknowns, and catching common estimation traps. TRIGGER when: user has discovery/requirements notes and needs to produce hours, cost, or a leveled team estimate for a proposal; user asks to "size this work," "estimate the effort," or "build the pricing"; user wants an existing estimate sanity-checked before it goes to the client. DO NOT TRIGGER when: scope is already agreed and signed and the task is to formalize contract language (use sow-draft-generate); the estimate is for incremental work after a signed SOW (use change-order-draft); no discovery has happened yet and the task is only to prepare the discovery call itself (use discovery-call-prep).
triggers:
  - "estimate this scope"
  - "size the effort"
  - "build the proposal pricing"
  - "how many hours will this take"
---

# proposal-scope-estimate

Estimates set client expectations before a single hour of work is billed — an estimate that's wrong in the optimistic direction becomes next quarter's margin problem or scope fight, so the discipline here is as much about surfacing unknowns as it is about arithmetic.

## Breaking work into estimable units

- Decompose by deliverable, not by role or by week — e.g. "Opportunity stage automation," "Lead scoring model," "ERP integration (outbound only)" — each unit small enough to size independently (roughly 8–80 hours; bigger units hide risk, smaller units drown in overhead).
- For each unit, separate build effort from the surrounding effort that's easy to forget: configuration/build, testing (unit + UAT support), data (migration/cleanup), integration touchpoints, documentation, and change management/training. Estimate each of these as its own line, not folded into "build."
- Tag each unit with a confidence level (High/Medium/Low) based on how well-defined the requirement is — this becomes the basis for contingency, not a vague gut feeling applied at the end.

## Estimation techniques: which to use when

- **T-shirt sizing (S/M/L/XL)** — use during early proposal shaping, when requirements are still directional, to get a fast relative-effort read across many units and to spot which items dominate the estimate. Fast, defensible for ranges, unsuitable for fixed-price commitments.
- **Detailed hour estimates (bottom-up by task)** — use once requirements are specific enough to list discrete tasks, especially for anything going into a fixed-fee or capped SOW. Build a task list per deliverable, estimate each task in hours, roll up by role/rate.
- **Analogous/comparable-project estimating** — use as a sanity check against both of the above by comparing to a similarly-scoped past engagement; a proposal wildly out of line with comparable past work is a signal to re-examine the breakdown, not to force-fit the number.
- Blend: t-shirt size everything first to see the shape of the engagement, then apply detailed estimates only to the units large enough or risky enough to matter (the 20% of units driving 80% of the hours).

## Contingency for unknowns

- Apply contingency per unit based on its confidence tag, not a flat percentage across the whole estimate — Low-confidence units (10–20%+ buffer), Medium (10–15%), High/well-defined (5% or less).
- Name the specific unknown driving the contingency (e.g. "legacy API rate limits undocumented," "data quality unverified") in the estimate notes — a named risk can be resolved and the buffer released; an unnamed "just in case" buffer never gets scrutinized and either evaporates under client pressure or lingers as pad.
- Distinguish contingency (buffer for how long the scoped work takes) from scope risk (buffer for whether the scope itself is even complete) — the latter is better handled by tightening the SOW's assumptions/exclusions than by adding hours.

## Common estimation traps

- **Anchoring on the client's stated budget** — building the estimate to fit a number the client mentioned, rather than pricing the work and then reconciling the gap explicitly. If the two don't match, that's a scope conversation, not a rounding exercise.
- **Underestimating integration effort** — integration touchpoints almost always take longer than the "happy path" build because of auth, error handling, retries, and the other system's undocumented quirks; estimate integration test/debug time separately and generously.
- **Underestimating testing** — teams often estimate build hours and assume testing is "included," then testing consumes 30%+ of the unit's actual time; give testing its own explicit line per deliverable.
- **Underestimating change management/training** — the human adoption side of a project is frequently left off the estimate entirely because it doesn't feel like "the work," yet it's often the difference between a technically complete project and one the client considers successful.
- **Estimating in a vacuum from stale notes** — if discovery notes are ambiguous on a unit, that ambiguity should convert into a Low-confidence tag and a named open question, not a confident number.

## Anti-patterns to avoid

- Producing a single total-hours number with no breakdown — it can't be defended, negotiated, or re-scoped later.
- Applying the same contingency percentage to every line regardless of how well-understood it is.
- Treating t-shirt sizes as final pricing input without ever converting the large/risky items to detailed estimates.
- Silently absorbing budget pressure into the estimate instead of flagging where scope would need to shrink to hit the number.

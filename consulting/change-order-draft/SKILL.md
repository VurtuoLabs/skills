---
name: change-order-draft
description: "Drafts a change order when scope shifts mid-engagement — documenting the delta from the original SOW, framing pricing/timeline impact, and getting a change order out fast instead of letting unscoped work accumulate silently. TRIGGER when: user notices new/expanded requests during an active engagement that weren't in the signed SOW; user asks to \"draft a change order,\" \"document this scope creep,\" or \"figure out what this new ask will cost\"; user wants help distinguishing an in-scope clarification from genuinely new scope. DO NOT TRIGGER when: the engagement hasn't started and there's no signed SOW yet to compare against (use sow-draft-generate or proposal-scope-estimate instead); the request is for a first-time estimate with no baseline scope to diff against (use proposal-scope-estimate)."
triggers:
  - "draft a change order"
  - "this is scope creep"
  - "the client is asking for something new"
  - "what will this extra work cost"
---

# change-order-draft

Unscoped work that isn't converted into a change order doesn't disappear — it accumulates silently until either the team is quietly over budget or the client is blindsided by an invoice, and both outcomes damage the relationship far more than a prompt, well-framed change order would. Speed matters more than precision here: a rough change order raised this week beats a perfect one raised at project close.

## Detecting scope creep early

- Treat any new request against the signed SOW's deliverable list as a scope test, not a judgment call made from memory — if it's not written in the SOW's In-Scope section, it needs a decision, not silent absorption.
- Common creep patterns to watch for: "small" additions requested verbally in a status meeting ("can you also just..."), a deliverable's definition quietly expanding during UAT ("done" turns out to mean more than the SOW's acceptance criteria said), and stakeholders who weren't in original discovery introducing new requirements late.
- The earlier a scope shift is named out loud to the client, the cheaper and less adversarial the conversation — flag it in the same meeting it's requested, don't wait for a natural pause or the next milestone review.
- A useful internal habit: whenever a team member says "that'll just take an hour, I'll knock it out," treat that as the moment to check it against the SOW before doing it, not after.

## Documenting the delta from original SOW scope

Structure the change order as a diff, not a fresh document:

- **Reference** — which SOW (and version/date) this change order modifies.
- **Trigger** — what happened that surfaced this (client request, discovery of a requirement gap, UAT finding) — dated and attributed, so the record is unambiguous if questioned later.
- **Original Scope** — quote the specific SOW language that the new request falls outside of.
- **Requested Change** — the new/modified deliverable, described as specifically as the original SOW's deliverables were (see sow-draft-generate's standard for measurable deliverables).
- **Impact** — effort delta (hours/units), timeline delta (does this push the go-live date or run in parallel), and fee delta.
- **Options if applicable** — sometimes worth presenting 2–3 options (full scope now vs. phase 2, or a cheaper reduced version) rather than a single take-it-or-leave-it number; this keeps the conversation collaborative rather than adversarial.

## Pricing and timeline impact framing

- Price the delta using the same estimation discipline as the original proposal (see proposal-scope-estimate) — don't eyeball a number under time pressure just to keep the conversation moving; a bad number here sets precedent for every future change order on the engagement.
- Always state the timeline impact explicitly even when the client only asks about cost — "yes, and it adds 1.5 weeks to the current milestone" prevents a second dispute later when the date slips and the reason was never surfaced.
- Frame the conversation around the SOW, not around goodwill or relationship — "this falls outside what we scoped in Section 3, here's what it would take" is a neutral factual statement, not an accusation, and keeps the discussion about the document rather than about trust.

## Getting to a change order fast

- Use a short-form template (half a page) for small changes — full SOW-length formality is itself a reason people avoid raising change orders promptly; the lighter the process, the more likely the team actually uses it in the moment.
- Set an internal norm: any request estimated at more than a small, pre-agreed threshold (e.g., a few hours) gets a change order before work starts, not after — retroactive change orders are far harder to get signed because the work is already sunk.
- Get a lightweight approval (email reply, e-signature, or verbal-plus-written-confirmation) rather than waiting for a formal signature cycle to start the clock — speed of documentation matters more than ceremony.

## Anti-patterns to avoid

- Absorbing "small" out-of-scope requests without documentation because raising a change order "feels awkward" — this is exactly how margin erodes and disputes accumulate.
- Waiting until project close or a budget review to reconcile all the undocumented extra work at once, turning a series of small conversations into one large, adversarial one.
- Framing the change order as blame ("you keep asking for more") instead of as a neutral scope/document reconciliation.
- Skipping the timeline impact and only discussing price, then having a separate fight later when the date slips.
- Making the change-order process so heavyweight that the team routes around it instead of using it.

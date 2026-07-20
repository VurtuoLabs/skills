---
name: sow-draft-generate
description: "Drafts a Statement of Work from discovery call notes, a requirements doc, or a proposal — structuring scope, deliverables, timeline, assumptions, and exclusions, and translating vague client language into specific, measurable deliverables. TRIGGER when: user has discovery notes, a requirements doc, or an approved proposal and needs a formal SOW; user asks to \"turn these notes into an SOW,\" \"draft the statement of work,\" or \"write up scope for the client\"; user wants existing scope language tightened before it goes to a client for signature. DO NOT TRIGGER when: the engagement is still in early estimation and no scope has been discussed yet (use proposal-scope-estimate instead); the user wants a mid-engagement change order for scope that shifted after the SOW was signed (use change-order-draft); the user just wants discovery questions prepared (use discovery-call-prep)."
triggers:
  - "draft the SOW"
  - "write the statement of work"
  - "turn these notes into scope"
  - "formalize the scope document"
---

# sow-draft-generate

An SOW is the contract artifact that gets litigated when a project goes sideways — every hour spent tightening its language before signature saves ten hours of dispute later. This skill turns loose discovery notes into a structured, defensible scope document.

## Standard SOW structure

Use these sections in order; skipping any of them is how disputes happen:

- **Engagement Overview** — one paragraph: client, business objective, why this project exists (ties deliverables back to a business outcome, useful when scope gets challenged later).
- **In-Scope Deliverables** — numbered list, each deliverable phrased as a noun the client can point to and verify ("Configured lead-to-opportunity conversion flow with 3 approval stages"), not a verb phrase describing activity ("Configure the flow").
- **Out-of-Scope / Exclusions** — explicit list of adjacent work the client might assume is included (data migration, third-party licensing, end-user training, post-go-live hypercare) even if never discussed — silence here is read as inclusion.
- **Assumptions** — conditions the estimate depends on (client provides a sandbox by week 1, client SME available 8 hrs/week, source data is already de-duplicated). Every assumption is a risk you're pricing away; write it down or you'll absorb it as free work.
- **Timeline & Milestones** — phase names, target dates, and what "done" means for each milestone, not just a Gantt chart.
- **Roles & Responsibilities (RACI-lite)** — who on the client side must show up, decide, or provide access, and by when.
- **Acceptance Criteria** — how each deliverable is signed off (demo + written sign-off, UAT pass rate, etc.) so "done" isn't a debate at the end.
- **Commercial Terms** — fee structure, payment milestones, expenses, change-order process reference (point to change-order-draft's process explicitly).

## Translating vague client language into measurable deliverables

- "Improve the sales process" → not a deliverable. Push back to: which specific process (lead routing, quoting, forecasting), what does improved mean (cycle time, error rate, click count), measured how.
- "Integrate with our ERP" → ambiguous on direction, real-time vs batch, and which objects. Needs: source/target objects, sync direction, frequency, and error-handling behavior before it can be scoped or estimated.
- "Train the team" → needs a number of sessions, audience size, format (live/recorded), and materials ownership, or it will expand indefinitely.
- Rule of thumb: if a deliverable can't be demoed or checked off by someone who wasn't in the room when it was written, rewrite it.

## Flagging ambiguity before it goes in the SOW

- Maintain an "Open Questions" list alongside the draft — items pulled from notes that are still vague, contradictory, or unconfirmed. Do not silently resolve them yourself by guessing; that guess becomes the client's expectation.
- Common ambiguity sources to scan for: undefined "it" ("make it work like the old system" — which behavior, exactly), missing volumes/scale (record counts, user counts, transaction volume), undefined "done," and features mentioned once in passing but never scoped.
- Each open question should be resolved with the client (or explicitly parked as an assumption with client sign-off) before the SOW is finalized — an SOW sent out with unresolved ambiguity just relocates the argument to mid-project.

## Anti-patterns to avoid

- Copy-pasting proposal language into the SOW without tightening it — proposals are sales documents and are intentionally more expansive than what should be contractually binding.
- Listing exclusions only for things the client already knows are out of scope, while staying silent on the adjacent work they're likely to assume is in (that silence is where scope creep starts).
- Writing assumptions so generic they don't actually transfer risk ("assumes reasonable client cooperation" protects no one — name the specific dependency).
- Letting "Open Questions" ride into the final signed SOW instead of closing them out first.

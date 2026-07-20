---
name: risk-register-track
description: Maintains a project risk register throughout an engagement — adding new risks with consistent likelihood/impact sizing, and reviewing existing entries to catch ones that have gone stale or were never assigned an owner. TRIGGER when: the user asks to log a new project risk, update or review a risk register, run a periodic risk review, or asks "what risks are we tracking" or "what's stale in the risk log." DO NOT TRIGGER when: the ask is to extract action items from a meeting (use meeting-notes-action-extract) or to write a client status report (use status-report-generate) — though a status report's risk section may pull from a register this skill maintains.
triggers:
  - "add this to the risk register"
  - "review our risk log"
  - "what risks are stale"
  - "size the likelihood and impact of this risk"
  - "unowned risks on the project"
---

# risk-register-track

Risks that quietly turn into real problems almost always share two traits before they blow up: nobody owns them, and nobody has looked at them in weeks. This skill maintains the register so those two failure modes get caught on a schedule rather than in a postmortem.

## Standard fields (every entry, no exceptions)

- **ID** — short stable identifier (R-001) so risks can be referenced in status reports and meetings without retyping the description.
- **Description** — the risk itself, phrased as a cause → event → effect, not a vague worry. "Vendor API sandbox has a 100 req/day limit (cause) → integration testing may be delayed (event) → could push UAT start by 1-2 weeks (effect)," not "vendor API might be a problem."
- **Likelihood** — sized on a fixed 1-5 scale (see below), never a bare gut-feel label like "high."
- **Impact** — sized on the same 1-5 scale, scored independently of likelihood.
- **Score** — Likelihood x Impact, used only for sorting/triage, never as a substitute for reading the two components.
- **Mitigation** — the specific action being taken to reduce likelihood or impact, not "monitor closely" (that's a status, not a mitigation).
- **Owner** — one named individual accountable for the mitigation. A risk with no owner is not tracked, it's just noted.
- **Status** — Open / Mitigating / Accepted / Closed / Materialized.
- **Last updated** — date of the most recent status or mitigation change, not the date the row was created.

## Sizing likelihood and impact consistently

Gut-feel labels ("this feels high risk") drift depending on who's writing the entry and how their week is going. Anchor both scores to fixed definitions and apply them the same way every time:

**Likelihood** (probability it occurs before the engagement ends): 1 = rare/hypothetical, 2 = possible but no current signal, 3 = plausible, some early signal exists, 4 = likely, active signal or precedent this engagement, 5 = already happening or near-certain.

**Impact** (effect if it occurs, scored against schedule/budget/scope/relationship, take the worst dimension): 1 = negligible, absorbed without anyone noticing, 2 = minor, absorbed within existing buffer, 3 = moderate, visible schedule/budget slip requiring a plan adjustment, 4 = major, materially changes scope, timeline, or client relationship, 5 = severe, threatens the engagement's viability or the relationship itself.

Score both independently before multiplying — do not let a scary description inflate impact when the actual probability is low, and do not let "we've mitigated it a lot" quietly lower the impact score (mitigation belongs in the mitigation field, not as a thumb on the impact scale).

## Review cadence: catching stale and unowned risks

On every register review (weekly or biweekly, matching the status-report cadence):

- **Stale check** — flag any entry where Last Updated is more than 2-3 weeks old (set the exact threshold per engagement and state it explicitly) and Status is not Closed. A stale "Open" risk usually means no one is actually working the mitigation anymore.
- **Owner check** — flag any entry with a blank or team-level owner ("engineering team," "TBD"). Escalate these first in the review, since an unowned risk has no one whose job it is to notice it's getting worse.
- **Score drift check** — for flagged stale risks, explicitly re-ask whether likelihood or impact changed since the last update rather than reflexively re-approving the old score.
- Close out risks whose triggering condition has passed (mark Closed, not deleted — the history is useful evidence for the next engagement).

## Anti-patterns to avoid

- Writing likelihood/impact as "High/Medium/Low" without a shared rubric behind the labels — different reviewers will disagree on what "High" means.
- Leaving Owner blank "for now" — an unassigned risk is the most likely one to be forgotten by the next review.
- Using "monitor" or "keep an eye on it" as the mitigation text instead of a concrete action with a trigger for when to escalate.
- Letting Last Updated get overwritten just by opening the register — only bump it when the status, mitigation, or scoring actually changes, or staleness detection becomes meaningless.
- Treating the register as a one-time kickoff artifact instead of a living document reviewed on a fixed cadence through the life of the engagement.

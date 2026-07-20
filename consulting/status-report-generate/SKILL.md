---
name: status-report-generate
description: "Generates a client-facing status report from raw internal activity — ticket/task system exports, git commit logs, standup notes — structured around outcomes and risks rather than a list of completed tickets. TRIGGER when: the user asks for a weekly/biweekly client status update, needs to turn sprint or standup notes into a client-readable summary, or has a pile of Jira/git activity to compress into a report. DO NOT TRIGGER when: the ask is to extract action items from a single meeting (use meeting-notes-action-extract), to log or update project risks in a register (use risk-register-track), or to write an internal engineering changelog with no client audience."
triggers:
  - "write this week's status report"
  - "turn these tickets into a client update"
  - "summarize sprint activity for the client"
  - "client-facing progress update"
  - "translate this standup into a status report"
---

# status-report-generate

A status report exists so the client can answer "are we on track and do I need to do anything" in under a minute. A chronological list of closed tickets fails that job even when it's accurate — this skill restructures raw activity around outcomes, risks, and asks, and separates what the client sees from what stays internal.

## Report structure (lead with outcomes, not activity)

Order sections so the client hits the answer first, detail second:

1. **Overall status** — one line: On Track / At Risk / Off Track, plus a one-sentence why. Never bury this below a list of tasks.
2. **Key outcomes this period** — 3-5 bullets on what changed for the client's business or product, not what was worked on. "Checkout now supports saved payment methods" beats "Completed tickets PROJ-104, PROJ-107, PROJ-112."
3. **Risks and blockers** — anything that could affect scope, timeline, or budget, each with what's being done about it. If there are none, say so explicitly rather than omitting the section — an absent risks section reads as an oversight, not as "no risks."
4. **Upcoming** — what happens next period, framed as expected outcomes, not a task queue.
5. **Decisions or input needed from the client** — the single most-skipped section. If work is blocked waiting on the client, say so plainly and by name/date, since burying this is how timeline slippage gets blamed on the vendor later.

## Translating internal activity into client language

- Convert ticket titles into outcome statements: "Fix null pointer in checkout service" becomes "Resolved an issue causing occasional checkout failures" — describe the user-facing effect, not the code-level cause.
- Roll up multiple small tickets into one narrative line unless the client specifically tracks ticket-level detail; a report with 40 line items is not more informative than one with 6.
- Translate technical risk into business risk: "API rate limiting on the vendor's sandbox" becomes "A third-party service constraint may affect our testing timeline; mitigation in progress."
- Keep git-commit-derived content especially compressed — commit messages are written for engineers and almost never belong verbatim in a client report.

## What to exclude (and where it goes instead)

Keep an **internal-only version** alongside the client version, or a footer/appendix marked internal, for content that doesn't belong in front of the client:
- Debugging narratives, false starts, and reverted approaches — useful for the team's own history, noise for the client.
- Unresolved internal disagreements (e.g., architecture debate not yet settled) — surface only once there's a recommendation or a decision the client needs to weigh in on.
- Attribution of fault for delays (which engineer, which vendor dependency broke) — report the impact and the plan, not the internal post-mortem.
- Rate/scope/staffing details not relevant to deliverables, unless the report's explicit purpose is a commercial or staffing update.

## Anti-patterns to avoid

- Leading with a bulleted ticket list and putting risks in a footnote, or omitting them entirely.
- Copy-pasting Jira ticket titles or commit messages as report content.
- Reporting "On Track" while the risks section (if present) describes a blocker that clearly threatens the date — status and risk content must agree.
- Omitting the "needs client input" section because nothing is currently blocked — state explicitly that there's nothing needed, so its absence isn't ambiguous.
- Writing one document and manually redacting it live for the client — maintain the internal and client versions as distinct artifacts so nothing internal slips through by accident.

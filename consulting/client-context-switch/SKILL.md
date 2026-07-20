---
name: client-context-switch
description: "Reconstructs a compact briefing for a specific client engagement when a consultant juggling multiple concurrent clients switches back to it, pulling together the last status sent, open action items, open risks, recent decisions, and the next touchpoint. TRIGGER when: a consultant is about to join a call, write an email, or resume deliverable work for a client they haven't touched in days, is context-switching between two or more active engagements in the same day, or says things like \"remind me where things stand with [client]\" or \"what did I owe them again\". DO NOT TRIGGER when: the engagement is brand new with no history to reconstruct (use engagement kickoff/onboarding guidance instead), or the request is to produce the actual handoff/retro deliverable itself rather than a personal working briefing."
triggers:
  - "catch me up on this client"
  - "switching between clients"
  - "what do I owe this client"
  - "resume this engagement"
  - "where did we leave off"
---

# client-context-switch

Consultants running multiple engagements pay a real tax every time they switch clients: reconstructing "where things stand" from memory is slow and error-prone, and skipping the reconstruction is how commitments get dropped. This skill builds a single-page briefing that makes switching back safe and fast, before any client-facing work resumes.

## What the briefing must contain

- **Engagement snapshot** — client name, engagement phase (discovery, build, rollout, wind-down), overall health (green/yellow/red) and why, in one line each.
- **Last status communicated** — the actual content of the last status report or update sent to the client: date, channel, and the 2-3 headline points made. If you can't summarize what you last told them, you risk contradicting yourself.
- **Open action items owned by you** — every commitment you made that isn't closed, with the due date and current state (not started / in progress / blocked / overdue). Pull these from the last status report, meeting notes, and any tracker — don't rely on memory to enumerate them.
- **Open risks and issues** — anything flagged as a risk, blocker, or escalation that hasn't been resolved, plus who is waiting on whom to move it forward.
- **Most recent decisions** — the last 2-4 substantive decisions made (scope, approach, timeline, budget) with date and who signed off. Re-litigating a settled decision because you forgot it happened erodes client confidence fast.
- **Next scheduled touchpoint** — date, format, attendees, and stated purpose of the next meeting or deliverable due, so you know what "ready" looks like before you get there.

## How to assemble it

- Source order: last sent status report first (it's the client's own record of truth), then your working notes, then the project tracker/ticketing system, then recent email/chat threads for anything not yet formalized.
- Timebox this to under 10 minutes. If it's taking longer, the underlying note-taking discipline during the engagement is the real problem, not this exercise.
- Flag gaps explicitly rather than guessing — write "unclear whether X was agreed" instead of silently assuming either way.
- Re-run this every time you re-enter the engagement after more than a day away, not just before big meetings; small gaps compound across many concurrent clients.

## Anti-patterns to avoid

- Trusting your memory of "where we left off" instead of the last status report — memory blends details across clients.
- Treating this as a one-time ritual before big meetings only, then improvising for smaller day-to-day touches where mistakes are just as costly.
- Producing a long narrative instead of a scannable briefing — if it takes more than a minute to read, it will get skipped next time.
- Leaving action items in the briefing without their current state, so "open" items that were actually already sent to the client get redone or, worse, contradicted.

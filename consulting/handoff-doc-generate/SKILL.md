---
name: handoff-doc-generate
description: "Produces a project handoff/knowledge-transfer document when a consultant rolls off an engagement or transitions it to a new owner, covering access and credentials, stakeholder contacts, in-flight work state, known issues, and tribal knowledge that exists nowhere else. TRIGGER when: a consultant is rolling off, going on leave, or transferring ownership of an engagement to another team member; a project sponsor requests a transition plan; staffing changes are announced with a defined end date. DO NOT TRIGGER when: the engagement itself is ending entirely with no successor (use engagement-retro-facilitate for that closure), or the request is a routine status update rather than a transfer of ownership."
triggers:
  - "rolling off this project"
  - "handoff document"
  - "knowledge transfer"
  - "transitioning to a new consultant"
  - "someone is taking over this account"
---

# handoff-doc-generate

A handoff document exists to let a successor operate the engagement without needing to ask the departing consultant anything within their first week. Anything less than that standard means real knowledge left with the person, not the document.

## Required sections

- **Access and credentials map** — every system, portal, repo, shared drive, and tool used on this engagement, who owns provisioning for each, and where credentials or access requests actually live (never the credentials themselves — link to the vault/IT process). Include SSO groups, VPN requirements, and any client-side approval lead time, since access delays are the #1 cause of a slow ramp-up.
- **Stakeholder map** — name, role, decision authority, preferred channel (email vs. Slack vs. Teams), meeting cadence, and any communication preferences worth knowing (e.g., "reads email at 6am," "hates surprise asks," "CC their EA"). Flag who is the actual economic buyer versus who is the day-to-day contact — they're often different people.
- **In-flight work inventory** — every open workstream with current state, next concrete step, owner of that next step, and due date. Distinguish "in progress, on track," "in progress, at risk," and "not started, was deprioritized" — a successor treating all three the same will misjudge priorities in week one.
- **Known issues and technical debt** — anything you'd warn a friend about before they touched this system: fragile integrations, workarounds nobody loves, promises made that haven't been formalized, data quality problems, and past failed approaches (so they aren't retried blindly).
- **Tribal knowledge** — the things that only exist in your head: why a rejected approach was rejected, unwritten stakeholder politics, informal agreements made in hallway conversations, historical context for why something looks the way it does. This section is the one most often skipped and the one that costs the most when it's missing.
- **Open commitments** — anything promised to the client, verbally or in writing, that isn't yet delivered, including soft commitments made in passing that the client will still remember.

## Why incremental beats last-minute

- A handoff doc written on someone's last day is reconstructed from memory under time pressure, right when institutional memory is about to walk out the door — quality is inversely proportional to how compressed the writing window is.
- Build it as a living document from week one: add an entry whenever a non-obvious decision is made, a workaround is created, or a stakeholder preference is learned, so the doc grows during the highest-signal moments instead of trying to recall them later.
- A living handoff doc also functions as onboarding material for anyone temporarily covering the engagement (illness, vacation), not just permanent transitions — so the investment pays off multiple times, not once.
- Schedule a recurring 15-minute monthly review of the doc against reality; stale handoff docs are worse than none because successors trust them and act on outdated information.

## Anti-patterns to avoid

- Writing the entire document in the final 24-48 hours, guaranteeing the tribal-knowledge section is thin or missing.
- Putting actual passwords or API keys in the document instead of pointing to where access is provisioned.
- Listing in-flight work as a flat task list with no state or next-step owner, forcing the successor to reverse-engineer priority.
- Skipping the "why we rejected X" history, which causes successors to burn time re-proposing approaches that were already tried and killed.
- Treating the handoff as a one-way document dump instead of pairing it with at least one live walkthrough session with the incoming owner.

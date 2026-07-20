---
name: meeting-notes-action-extract
description: Converts raw meeting notes, call transcripts, or scribbled minutes into a structured record of decisions and action items, each with a single named owner and a due date. TRIGGER when: the user pastes meeting notes, a transcript, or a recap and asks for action items, a summary, or "what did we agree to"; when preparing a follow-up email after a client call; when notes need to be logged into a tracker (Jira, Asana, a project plan) after a working session. DO NOT TRIGGER when: the user wants a status report on ongoing work (use status-report-generate), when there is no meeting content to process (e.g. planning an agenda for a future meeting), or when the ask is to draft a risk register entry rather than process notes.
triggers:
  - "extract action items from these notes"
  - "summarize this call transcript"
  - "who owns what from this meeting"
  - "turn these notes into follow-ups"
  - "meeting recap for the client"
---

# meeting-notes-action-extract

Raw notes mix confirmed decisions, half-formed ideas, and tasks in one unstructured stream. This skill turns that stream into a clean record that can be pasted into a tracker or follow-up email with zero further editing, and forces every action item to have an owner and a date before output is considered done.

## Decision vs. open discussion point

A line only counts as a **Decision** if it meets one of these tests:
- Someone with authority to commit stated a final choice ("we'll go with option B", "let's target the 15th") and no one in the room contested it before the topic changed.
- The group explicitly voted, agreed, or the facilitator summarized a conclusion and got a verbal "yes" / no pushback.

Everything else is an **Open Item** — a question raised, an idea floated, a tradeoff discussed without resolution, or a decision someone said needs sign-off from someone not in the room. Do not upgrade an open item to a decision just because it sounds settled; when in doubt, classify it as open and flag it for confirmation. Mislabeling a discussion as a decision is the single most common way a project quietly drifts off track.

## Action item structure

Every action item in the output must have all five fields filled — no blanks, no "TBD" left unresolved:

- **Task** — one specific, verifiable outcome (not "look into X" — instead "confirm whether X supports SSO by EOD Thursday").
- **Owner** — a single named individual, never a team or "we". If the notes only say "someone should check the API limits," assign it to the person who raised it or the most relevant attendee, and mark it `(owner inferred — confirm)`.
- **Due date** — a specific date, not "soon" or "next sprint." If none was stated, infer a reasonable date from context (e.g., before the next scheduled meeting) and mark it `(date inferred — confirm)`. Never leave this field empty.
- **Context** — one line linking back to why the task exists, so it's usable without re-reading the full notes.
- **Status** — default to "Not started" unless the notes say otherwise.

## Output structure

Produce three sections in this order, ready to paste directly into a tracker or email:

1. **Decisions** — bulleted, past tense ("Decided to move the go-live to Aug 12"), no owner/date needed unless a decision itself spawns a follow-up task.
2. **Action Items** — a table with columns Task | Owner | Due Date | Context | Status, sorted by due date ascending.
3. **Open Items (needs follow-up)** — bulleted list of unresolved questions and who needs to weigh in, so nothing discussed-but-not-decided gets silently dropped.

If the source material names no attendees or roles, do not guess names — use role descriptions ("the client PM," "our lead engineer") consistently and flag that names should be confirmed before distribution.

## Anti-patterns to avoid

- Assigning an action item to "the team" — every task collapses to zero accountability without one named owner.
- Treating "we should probably..." language as a decision just because it wasn't argued with.
- Dropping items that don't fit neatly into decision or action buckets instead of routing them to Open Items.
- Copying transcript filler (side conversations, scheduling logistics, technical hiccups) into the output — keep only substantive content.
- Leaving a due date blank rather than inferring and flagging one for confirmation.

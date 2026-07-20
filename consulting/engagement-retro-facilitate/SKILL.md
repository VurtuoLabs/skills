---
name: engagement-retro-facilitate
description: "Runs a structured end-of-engagement retrospective and converts it into a written retro document with concrete, owned action items rather than a list of vague sentiments. Covers a question framework, techniques for surfacing honest input from a client-facing team critiquing its own work, and the translation from raw retro notes to next-engagement changes. TRIGGER when: an engagement or major phase is closing and the delivery team wants to capture lessons learned; a practice lead asks for a post-mortem or after-action review; a team repeatedly hits the same friction and wants to formalize learning before staffing the next engagement. DO NOT TRIGGER when: the goal is a client-facing project closure summary or final deliverable (that's a separate closure artifact), or the engagement is still active with no natural close point to reflect from."
triggers:
  - "run a retro"
  - "post-mortem on this engagement"
  - "lessons learned"
  - "what should we do differently next time"
  - "end of engagement review"
---

# engagement-retro-facilitate

An engagement retro's only job is to change what happens on the next engagement. If the output is a document that gets filed and never referenced again, the retro failed regardless of how candid the discussion was.

## Question framework

- **What went well** — specific practices, decisions, or moments worth repeating, not generic praise. Push for "the weekly risk review caught the scope creep early" over "good communication."
- **What didn't go well** — specific friction points, missed expectations, or breakdowns, framed around the situation and its impact, not around individual blame. "Requirements changed twice without a change-order process" is usable; "the client was difficult" is not.
- **What would we do differently** — for each "didn't go well" item, the counterfactual: what specific alternative action would have prevented or reduced it. This is the bridge between diagnosis and action.
- **What should become a repeatable practice** — of everything surfaced, which items are big enough and generalizable enough to codify into team playbooks, templates, or checklists rather than being a one-off learning for this team only.

## Getting honest input

- Collect input asynchronously and individually before the group discussion (written, anonymous if the team is junior or the engagement was tense) — people self-censor less in writing than in a room, especially about their own leadership's decisions.
- Separate "what happened" from "who's at fault" explicitly at the start of the session; a retro that turns into performance evaluation shuts down candor for every future retro that team runs.
- The facilitator should not be the engagement lead if the engagement lead's own decisions are likely to be a major topic — a peer or practice lead facilitating gets more honest input than someone reviewing their own performance.
- Explicitly invite the least senior person to speak first on each topic before more senior voices anchor the discussion.
- If the client relationship is ongoing, decide up front which findings are internal-only versus appropriate to share with the client as process improvements — conflating the two makes people hold back in the internal discussion.

## Converting output into action

- Every item that survives to the written retro doc must have an owner, a due date, and a next engagement or team process it applies to — "we should communicate better" is not an action item, "add a weekly written status template, owned by [name], starting on the next engagement kickoff" is.
- Sort findings into three buckets: fix now (this engagement, if still open), change for next time (process/template change owned by the practice), and watch (pattern to monitor, not yet enough evidence to act on) — don't force everything into "immediate action" or it gets diluted.
- Route repeatable-practice items to wherever the team's playbooks/templates actually live, and update them in the same week as the retro — a lesson that isn't written into the artifact people actually reuse will be relearned on the next engagement.
- Close the loop: at the kickoff of the next engagement, explicitly review which retro action items apply and confirm they were adopted, not just filed.

## Anti-patterns to avoid

- Letting the retro become a venting session with no structure, producing a long list of sentiments with no path to action.
- Writing action items with no owner or date, which quietly demotes them to "nice ideas" that never get implemented.
- Having the most senior person in the room speak first, anchoring the group toward their framing of what went wrong.
- Running the retro only when something went badly — retros after healthy engagements surface repeatable practices that get missed when the exercise only happens during damage control.
- Filing the retro doc without updating the actual playbook/template it points to, leaving the lesson stranded in a document nobody opens again.

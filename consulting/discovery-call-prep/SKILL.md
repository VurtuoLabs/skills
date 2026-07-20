---
name: discovery-call-prep
description: Prepares a structured discovery call agenda and question list for a new client engagement, covering current-state process, pain points, technical constraints, stakeholders, success criteria, and timeline/budget, sequenced to build rapport before probing sensitive topics. TRIGGER when: user is preparing for an upcoming discovery or scoping call with a new or existing client; user asks to "build a discovery agenda," "what should I ask on this call," or "prepare questions for the kickoff"; user wants a structured template for capturing call answers. DO NOT TRIGGER when: discovery is already complete and notes exist — the task is to turn them into a proposal (use proposal-scope-estimate) or SOW (use sow-draft-generate); the conversation is about scope that changed after the engagement started (use change-order-draft).
triggers:
  - "prepare discovery questions"
  - "build the discovery agenda"
  - "what should I ask on the kickoff call"
  - "discovery call prep"
---

# discovery-call-prep

A discovery call is the only cheap opportunity to ask hard questions before they become expensive assumptions baked into an estimate — a well-sequenced agenda gets more honest answers than a randomly-ordered question list.

## Question categories to cover

- **Current-state process** — how the work happens today, step by step, including manual workarounds and the tools currently stitched together; ask for a real recent example ("walk me through the last deal that closed") rather than the idealized process description.
- **Pain points** — what specifically breaks, how often, and what it costs (time, errors, missed revenue, compliance exposure); push past "it's slow" to a number or a story.
- **Technical constraints** — current systems/versions, integration landscape, data volumes, security/compliance requirements, any prior customization that will affect new work.
- **Stakeholders & decision-makers** — who uses the solution daily, who owns the budget, who can say yes, who can quietly say no (the skeptical VP, the IT security reviewer) — map this explicitly, don't assume the person on the call is the full picture.
- **Success criteria** — what does the client measure to call this a win, and by when; get a specific metric or artifact, not "make it better."
- **Timeline & budget constraints** — hard external deadlines (compliance date, contract renewal, fiscal year), internal bandwidth constraints, and rough budget range or approval process.

## Sequencing: rapport before sensitive topics

- Open with current-state process questions — they're low-stakes, factual, and let the client talk about something they know well, which builds momentum and trust.
- Move to pain points once rapport is established — people share frustration more openly after they've been heard describing their process, not as the opening question.
- Save budget and past-vendor-failure questions for the back half of the call, after credibility is established — asking "what's your budget" or "why did the last implementation fail" too early reads as transactional or reads as an audit, and clients get guarded.
- When you do ask about past vendor failures, frame it forward-looking ("what should we make sure we don't repeat") rather than as blame excavation — this gets more useful, less defensive answers.
- Close with a recap of what you heard and explicit next steps — this is also a check that you captured things correctly while the client can still correct you live.

## Capturing answers in a reusable structured format

- Use a fixed template with one section per question category (not free-form notes) so answers are comparable across engagements and directly portable into the estimate and SOW steps that follow.
- For each answer, capture three things distinctly: the raw quote/fact, your interpretation of its implication for scope, and a confidence flag (confirmed / needs follow-up / assumption) — collapsing these into one blob is how vague client language ends up unexamined in a proposal.
- Tag every answer that implies a deliverable, a constraint, or a risk so it can be pulled directly into proposal-scope-estimate or sow-draft-generate without re-reading the transcript.
- Track unanswered or deflected questions explicitly (a client who won't name a budget or decision-maker is itself signal) rather than leaving the field blank and forgetting it was never answered.

## Anti-patterns to avoid

- Running the call as a rigid script read in order regardless of what the client says — follow-up questions on an unexpected pain point are usually worth more than finishing the list.
- Asking about budget or past vendor failures in the first five minutes, before any rapport exists.
- Taking free-form notes and planning to "structure them later" — later rarely happens accurately, and nuance gets lost.
- Leaving stakeholder mapping to "whoever showed up on the call" instead of explicitly asking who else needs to be involved.
- Accepting vague success criteria ("make it more efficient") without pushing for a measurable definition on the call itself, while the client is present to clarify.

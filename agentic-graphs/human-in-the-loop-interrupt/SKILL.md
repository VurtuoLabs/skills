---
name: human-in-the-loop-interrupt
description: Designs approval/interrupt checkpoints in an agent graph that pause before risky or irreversible actions and route to a human decision. Covers which actions actually warrant a gate, how to shape the interrupt payload for fast human decisions, timeout/escalation behavior, and preventing interrupt fatigue that trains approvers to rubber-stamp. TRIGGER when: adding an approval step before an agent takes a consequential action, a human-in-the-loop gate is producing rubber-stamp approvals or is too slow, or designing what happens when nobody responds to an approval request. DO NOT TRIGGER when: adding basic input validation or confirmation dialogs with no real irreversibility at stake, or building fully autonomous pipelines with no human approval step by design.
triggers:
  - "human approval gate design"
  - "agent interrupt checkpoint"
  - "approve reject agent action"
  - "human-in-the-loop pause"
---

# human-in-the-loop-interrupt

An interrupt gate is only worth its latency and friction cost if it's placed where a human's judgment changes the outcome of actions that are hard or costly to undo — everything else is a tax on throughput that erodes the trust of the humans doing the approving.

## Deciding which actions need a gate

- Use two axes, not gut feeling: irreversibility (can this be cleanly undone, and at what cost) and blast radius (how many entities/systems/dollars/people does it touch if wrong). Gate the intersection — high on both axes — not everything that merely sounds risky in a sentence.
- "Risky-sounding" is a bad proxy: deleting a single test-environment record sounds alarming but is trivially reversible and narrow-blast-radius; a well-formed bulk email send to 50k customers sounds mundane but is irreversible and wide-blast-radius. Gate the second, not necessarily the first.
- Reversible-but-expensive actions (a large paid API call, a long-running compute job) deserve a lighter-weight gate than a full stop — a rate/budget cap enforced in code, or a notify-but-proceed pattern, rather than a blocking human approval.
- Irreversible-but-narrow actions (deleting one user's own draft) may not need a gate at all if the action is scoped to something the requesting user already owns and consented to — the gate belongs where the agent is acting beyond the authority explicitly granted to it, not on every destructive verb.
- Reassess the gate list periodically against actual approval logs: actions that are always approved with zero edits over N occurrences are candidates for demotion to auto-approve-with-audit; actions that are frequently rejected or edited are candidates for a gate if they don't already have one.

## Designing the interrupt payload

- The payload must let a human decide from the payload alone, in the time it takes to read it — never require the approver to open a different tool, re-run a query, or reconstruct why the agent wants to do this. Include: the proposed action verbatim (the actual API call/diff/message, not a paraphrase), the specific state that triggered it, and the agent's stated justification.
- Show a diff or delta, not just the end state, whenever the action modifies something that already exists — "change status from Pending to Approved" is decidable in one glance; "set status to Approved" forces the approver to go look up the current value themselves.
- Attach the agent's confidence and any dissenting signal it already has (e.g., a prior critique-node flag, an anomaly the agent itself noted but proceeded past) — withholding the agent's own uncertainty from the human is how gates end up rubber-stamping cases the agent itself wasn't sure about.
- Make the decision surface itself narrow: approve / reject / reject-with-reason / request-more-info, as structured actions, not a free-text chat the human has to compose a reply into. Free-text approval channels are where response latency and inconsistency both come from.
- Version the interrupt payload schema and log every decision against it — this is what lets you later audit whether gates are being read (time-to-decision, edit rate) versus reflexively clicked.

## Timeout and escalation behavior

- Every gate needs an explicit default-on-timeout policy chosen per action class, not a global default. Fail-closed (block, do not proceed) is correct for irreversible/high-blast-radius actions; fail-open with a logged auto-decision is sometimes correct for reversible actions where stalling itself has a cost (e.g., a time-sensitive trade that expires).
- Escalate before you time out, not only after: a first-tier approver who hasn't responded in X minutes should trigger a notification bump or handoff to a secondary approver, so the default timeout behavior is rarely what actually fires.
- Treat "approver explicitly deferred/requested more info" differently from "approver never responded" in your state machine — the former is a live loop waiting on more agent work, the latter is the timeout path. Collapsing them loses the distinction between an engaged human and an absent one.
- Persist interrupt state durably (see checkpointing) so a pending approval survives a process restart — an agent that "forgets" it was waiting on a human and either re-asks or silently proceeds is a correctness bug, not a UX nit.

## Avoiding interrupt fatigue

- Fatigue is a calibration failure, not a discipline failure — if 95% of gated actions are routinely approved unchanged, the gate's signal-to-noise has collapsed and humans will learn to click approve without reading, which defeats the gate exactly when a genuinely bad action finally appears.
- Batch related low-stakes approvals into a single review (e.g., "approve these 8 similar row updates") instead of 8 separate interrupts, but never batch across different action classes or risk tiers into one approval — a human should never be able to approve a high-risk action by accident while clearing a stack of low-risk ones.
- Track approve/reject/edit rates per gate over time as a first-class metric, not an afterthought. A gate with a near-zero rejection rate over a large sample is a strong candidate to relax (raise the threshold that triggers it, or convert to post-hoc audit instead of pre-action block).
- Separate "irreversible and consequential" from "merely outside the agent's normal pattern" — anomaly-triggered gates (this looks unusual, therefore ask) are useful but should be tuned and rate-limited independently from the irreversibility-based gates, or the two purposes will drown each other out in one undifferentiated approval queue.

## Anti-patterns to avoid

- Gating every write/delete/send action uniformly regardless of scope or reversibility, which guarantees approval fatigue within days of launch.
- Sending an interrupt payload that just says "agent wants to perform action X, approve?" with no diff, no context, and no confidence — forces the human to either rubber-stamp or go do the agent's research over again.
- A single global timeout-then-proceed default applied to irreversible actions, silently converting an unanswered approval into an approval.
- Free-text chat as the only approval channel, with no structured decision log — makes it impossible to later audit approve/reject/edit rates or detect fatigue setting in.

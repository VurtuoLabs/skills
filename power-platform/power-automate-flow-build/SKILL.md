---
name: power-automate-flow-build
description: "Guides building Power Automate cloud flows — choosing between automated, instant, and scheduled trigger types; understanding connector licensing tiers (standard vs. premium/custom) and their cost implications; applying core control patterns (Condition, Apply to each, Do until); and wiring robust error handling with \"configure run after\". TRIGGER when: a user is designing or debugging a Power Automate cloud flow, choosing a trigger or connector, asks about premium connector licensing, needs looping/branching logic in a flow, or wants failure handling/retry behavior. DO NOT TRIGGER when: the task is Power Automate Desktop (RPA/UI automation) with no cloud flow involved, or general Power Platform admin/environment topics unrelated to flow design."
triggers:
  - "Power Automate cloud flow trigger"
  - "Power Automate premium connector licensing"
  - "Power Automate apply to each condition"
  - "configure run after error handling"
---

# power-automate-flow-build

Cloud flows in Power Automate are the workhorse of Power Platform automation, and most real-world build problems come down to picking the right trigger, respecting connector licensing tiers, and handling failures explicitly rather than hoping the happy path always runs.

## Trigger types

- Automated flows fire on an event from a connector (new email, new SharePoint item, Dataverse row change) — pick these when the automation should react to something happening in another system, and be aware trigger polling intervals (commonly ~1-5 min for non-webhook connectors) add latency.
- Instant flows are manually invoked — from a button, Teams/Power Apps action, or "Run flow" — appropriate when a human decides when the process starts, and they can accept run-time input parameters via the trigger's input definitions.
- Scheduled (recurrence) flows run on a defined interval/cron-like schedule independent of any external event — best for batch jobs, digest emails, or reconciliation sweeps, and remember recurrence triggers still count against the environment's flow run quota.
- Some connectors expose true webhook-based triggers (instant push, not polling) — prefer these over polling triggers when available for lower latency and reduced API call consumption.

## Connectors and licensing tiers

- Standard connectors (Office 365, SharePoint, Dataverse for Teams, Outlook) are included in most Microsoft 365/Dynamics licenses; premium connectors (SQL Server, Salesforce, HTTP, most on-prem gateway connectors, Dataverse full) require Power Automate per-user/per-flow licensing or premium entitlement even if only one step in the flow uses one.
- A single premium connector action anywhere in a flow makes the *entire flow* premium for licensing purposes — auditing connector usage before build avoids surprise licensing gates in production.
- Custom connectors (wrapping arbitrary REST APIs via OpenAPI definition) are always treated as premium, and HTTP/HTTP with Azure AD actions specifically require premium licensing — factor this into cost estimates when a flow needs to call an unsupported external API.
- Use the on-premises data gateway for hybrid connectivity (on-prem SQL, file shares); gateway-routed connectors are typically premium-tier and add a gateway-availability dependency to the flow's reliability.

## Core control patterns

- Condition actions branch on expressions (`if`, comparison, or the classic "Condition" card) — keep conditions flat where possible; deeply nested conditions are hard to debug and better expressed as a Switch action for multi-branch logic.
- Apply to each iterates an array; it runs iterations in parallel by default (configurable concurrency, up to 50) unless "Concurrency Control" is turned off for sequential processing — sequential is required when later iterations depend on earlier ones (e.g., accumulating a running variable).
- Do until loops on a condition with a required exit-condition expression and a max-count/timeout safeguard (default 60 iterations/1 hour) — always set explicit limits rather than relying on defaults for potentially long-running polling loops, to avoid runaway execution costs.
- Scope actions group a related set of steps into a single collapsible unit that "configure run after" can target as one block — use them to isolate a section of logic that needs its own error-handling wrapper.

## Error handling with "configure run after"

- Every action has a "Configure run after" setting controlling whether it executes on the prior action's success, failure, timeout, or skipped state — the default (success only) means a single failed step halts the flow unless you explicitly branch for failure.
- The standard pattern is a Try/Catch/Finally emulation: a Scope named "Try" containing the main logic, a second Scope named "Catch" configured to run after Try "has failed," and a "Finally" scope configured to run after Try "is successful, has failed, has timed out, is skipped."
- Use `result('Try')` inside the Catch scope to inspect which action within Try failed and its error output, then route to notification (Teams message, email, ticket creation) — don't let failures fail silently with no downstream signal.
- For transient failures (throttling, timeouts) configure per-action retry policies (exponential backoff, custom count) in the action's settings rather than building manual retry loops with Do until.

## Anti-patterns to avoid

- Leaving Apply to each on default concurrent execution when iterations mutate a shared variable, causing race conditions and inconsistent final values.
- Adding a single HTTP or premium connector step deep in an otherwise-standard flow without checking that it flips the whole flow's licensing tier, causing a production deployment to fail on entitlement.
- Building Do until loops without an explicit exit condition and count/timeout limit, risking silent truncation at the default 60-iteration cap.
- Relying only on the default "run after success" wiring with no Catch scope, so failures surface only as a red X in flow run history that nobody is watching.

---
name: servicenow-flow-generate
description: Guides the design and build of ServiceNow Flow Designer flows and subflows, covering trigger selection, actions vs. subflows, data pill wiring between steps, and when to choose Flow Designer over the legacy Workflow Editor or a custom script. TRIGGER when: a user asks to automate a ServiceNow process (approvals, record updates, notifications, integrations) without writing a full script, wants to refactor a Workflow Editor workflow into Flow Designer, or asks how to pass data between flow actions. DO NOT TRIGGER when: the user wants raw server-side scripting (Business Rules, Script Includes) with no flow involved, is asking about UI Policies/Client Scripts, or is working purely in ATF test design.
triggers:
  - "flow designer"
  - "servicenow flow"
  - "subflow"
  - "flow trigger record"
  - "data pill"
---

# servicenow-flow-generate

ServiceNow pushes all new automation onto Flow Designer; Workflow Editor is deprecated for net-new work, and scripts should only fill gaps Flow Designer cannot reach declaratively. This skill frames the trigger/action/subflow decisions and the data-passing model needed to build a correct, maintainable flow.

## Triggers

- **Record Trigger** fires on insert, update, or insert-or-update against a table, with an optional condition builder and (for update) a "changes from/to" field filter — use this for reactive automation tied to a single table's lifecycle.
- **Scheduled Trigger** runs on a defined cadence (daily, weekly, cron-like repeat interval) independent of any record event — use for batch cleanup, digest notifications, or polling-style integrations.
- Record Triggers run asynchronously off the update transaction by default; if you need synchronous, in-transaction behavior (e.g., blocking a save), that belongs in a Business Rule, not a flow.
- A flow can also be invoked without its own trigger, called directly from a subflow action, a Script Include (`sn_fd.FlowAPI`), a UI Action, or an Agentforce/Virtual Agent topic.

## Actions vs. subflows

- **Actions** are the atomic steps inside a flow: Create Record, Update Record, Look Up Record(s), Send Email, REST Step, Ask For Approval, Script (inline). Use built-in actions before writing a Script action — they're easier to audit and reuse.
- **Subflows** are reusable, independently versioned flows with their own defined inputs and outputs, invoked from a parent flow (or another subflow) as if they were a single action. Extract logic into a subflow when three or more flows need the same sequence, or when a single flow is growing past ~15-20 steps and readability suffers.
- Subflows support their own trigger-less input/output contract (defined on the subflow's Inputs/Outputs tabs) — treat this contract like a function signature and keep it stable once other flows depend on it.
- Actions and subflows can both be packaged as reusable **Action/Subflow** custom building blocks scoped to an application, which is the right level for cross-team shared logic in a scoped app.

## Data pills

- Every trigger and prior action exposes its outputs as data pills, draggable into any subsequent step's input fields — this is the entire mechanism for passing data forward in a flow; there is no shared "variable" scope outside of explicit Flow Variables.
- Declare a **Flow Variable** when you need a value that isn't naturally an action output (e.g., an accumulator, a constant computed once at the top) or when you need to mutate a value across branches/loops.
- Data pills from a trigger's record (e.g., Trigger > Record > Short Description) stay bound to that specific record; inside a **For Each** loop, the loop item's pills are scoped to that iteration only and are not visible outside the loop.
- Reference field data pills (e.g., Assignment Group > Manager > Email) implicitly perform dot-walking; each hop is a live GlideRecord read at runtime, so chaining many reference pills across large flows can add latency — resolve heavily-reused chains once into a Flow Variable instead of re-dot-walking in every action.

## When to use Flow Designer vs. Workflow Editor vs. a script

- Default to Flow Designer for any new process automation: approvals, record CRUD, notifications, REST/SOAP calls via Integration Hub spokes, and orchestration across tables.
- Only touch Workflow Editor to maintain an existing legacy workflow (e.g., `wf_workflow` records still driving Catalog Item processes) — Workflow Editor is in maintenance mode and Catalog Item workflows should be migrated to Flow Designer's Catalog flow trigger type when the item is next revised.
- Drop to a Script action (or a Script Include called from one) only for logic Flow Designer's declarative actions can't express — complex string/date manipulation, non-trivial branching on nested JSON from a REST response, or performance-critical bulk GlideRecord operations that would otherwise run as many discrete flow actions.
- If a process requires synchronous validation/blocking before a record commits, that's a Business Rule (before insert/update), not a flow — flows are not guaranteed to run in-transaction.

## Anti-patterns to avoid

- Building deeply nested If/Else trees instead of extracting a subflow per branch — makes the flow untestable and hard to diff in source control.
- Looping a REST/Create Record action over a For Each instead of using a Script step with batched GlideRecord/`GlideRecordScoped` — this exhausts semaphore/API rate limits on large record sets.
- Hardcoding sys_ids for groups, users, or categories directly in action inputs instead of using System Properties or a lookup action — breaks portability between instances.
- Using a Record Trigger with no condition, then filtering inside the flow with an early If/Stop — wastes flow executions and clutters flow context logs; push filtering into the trigger condition.

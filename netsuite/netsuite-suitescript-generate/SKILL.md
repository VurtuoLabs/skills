---
name: netsuite-suitescript-generate
description: Guides writing NetSuite SuiteScript 2.x scripts for automation and customization, covering script-type selection, the core N/record and N/search modules, and how to design within governance/usage-unit limits. TRIGGER when: a user asks to write or debug a NetSuite script (User Event, Client, Scheduled, Suitelet, RESTlet, Map/Reduce), hits a SuiteScript governance/usage limit error, or needs to query or mutate NetSuite records programmatically. DO NOT TRIGGER when: the request is about NetSuite SuiteFlow (workflow tool) configuration with no scripting involved, or about SuiteAnalytics/saved search UI only with no script needed.
triggers:
  - "suitescript"
  - "netsuite scheduled script"
  - "map reduce script netsuite"
  - "n/record n/search"
  - "restlet netsuite"
---

# netsuite-suitescript-generate

SuiteScript 2.x runs inside NetSuite's sandboxed V8 engine under strict per-script governance, so picking the right script type and respecting usage units is as important as the business logic itself. This skill frames that selection and the module/governance patterns needed to avoid `SSS_USAGE_LIMIT_EXCEEDED` and similar failures.

## Script types and when to use each

- **User Event (UE)**: server-side, fires on `beforeLoad`, `beforeSubmit`, `afterSubmit` for a specific record type's CRUD/UI events — use for record-level validation, default-setting, or triggering follow-on actions synchronously in the save transaction. `beforeSubmit`/`afterSubmit` share a 1,000-unit governance budget with the triggering user action, so keep them lean.
- **Client Script (CS)**: runs in the user's browser against a record form — `pageInit`, `fieldChanged`, `saveRecord`, `validateField` — use for real-time UI behavior (dynamic field visibility, client-side validation) analogous to sublist/field interactions a user would otherwise do manually.
- **Scheduled Script (SS)**: server-side, runs on a deployment schedule or via `N/task` trigger, single-threaded with its own governance pool (typically 10,000 units, deployment-configurable) — use for batch jobs that process a bounded, moderate-size record set on a timer.
- **Map/Reduce (MR)**: server-side, designed for large-volume parallelized processing via `getInputData` → `map` → `reduce` → `summarize` stages, each stage getting its own fresh governance allocation per invocation — use this instead of Scheduled Script whenever the record set is large or unpredictable in size, since NetSuite auto-chunks and re-queues work across governance resets.
- **Suitelet**: server-side, renders a custom UI (via `N/ui/serverWidget`) or JSON/HTML response at a NetSuite URL — use for custom pages, wizards, or lightweight internal APIs reachable from within the NetSuite UI/session.
- **RESTlet**: server-side, exposes a custom REST-style endpoint authenticated via Token-Based Auth or OAuth 2.0 — use for external system integrations that need synchronous request/response against NetSuite data beyond what SuiteTalk REST/SOAP already covers.

## N/record and N/search

- `N/record` is the CRUD module: `record.load()`/`record.create()` return an in-memory record object you mutate with `setValue`/`setSublistValue` then `.save()` — each `load`+`save` pair costs governance units (roughly 10 for load, 20 for a plain submit, more for form-triggering submits) and each triggers any dependent User Event/workflow logic, so avoid load/save in tight loops when a direct field update would do.
- `record.submitFields()` performs a targeted field-only update without loading the full record — dramatically cheaper in governance and preferred for simple bulk field changes (e.g., updating a status field on thousands of records).
- `N/search` is the query module: prefer `search.create({type, filters, columns}).run().getRange()` or `.each()` for iterating results, and `N/query` (SuiteQL) for complex joins/aggregations that would be awkward as a saved-search-style filter/column definition — SuiteQL is generally cheaper and more expressive for reporting-style reads.
- Use `search.lookupFields()` for a single-record, single-call field lookup instead of a full `record.load()` when you only need a few field values — much lower governance cost.
- Always paginate large search results (`search.runPaged()` with a defined `pageSize`) rather than loading an unbounded result set into memory in a Map/Reduce `getInputData` stage.

## Governance and usage limits

- Every SuiteScript API call consumes "usage units" against the script's governance budget (varies by script type and NetSuite edition); when the budget is exhausted mid-script, NetSuite throws `SSS_USAGE_LIMIT_EXCEEDED` and the script stops — design for this rather than treating it as an edge case.
- In Scheduled Scripts, check remaining governance proactively with `runtime.getCurrentScript().getRemainingUsage()` before an expensive operation, and if it's low, call `N/task.create({taskType: task.TaskType.SCHEDULED_SCRIPT}).submit()` to re-queue a continuation with a saved checkpoint (e.g., last processed internal ID) rather than letting the platform hard-fail.
- Map/Reduce sidesteps most manual governance bookkeeping: NetSuite automatically yields and resumes the `map`/`reduce` stage across new governance allocations as long as each individual stage invocation processes one unit of work efficiently — keep `map`/`reduce` functions doing one record's worth of work each, not internal loops over many records.
- RESTlet and Suitelet governance is per-request (much smaller budget, ~1,000 units) — never do bulk multi-thousand-record processing directly in a RESTlet call; instead have the RESTlet enqueue a Scheduled/Map-Reduce script via `N/task` and return immediately.
- Concurrency limits (queued/concurrent scheduled script instances per account) are separate from per-script governance — heavy Map/Reduce usage across many deployments can queue behind each other account-wide, so check deployment status (`task.checkStatus`) rather than assuming immediate execution.

## Anti-patterns to avoid

- Using a Scheduled Script for an unbounded or fast-growing record set instead of Map/Reduce — it will eventually blow past governance without an automatic re-queue mechanism, requiring hand-rolled checkpoint logic that Map/Reduce already provides.
- Calling `record.load()`/`record.save()` inside a `search.run().each()` loop for simple field changes — use `record.submitFields()` or bulk CSV/`N/task.create` with `CSV_IMPORT`/bulk API paths instead.
- Doing heavy business logic directly in a RESTlet's synchronous request handler — long-running RESTlet calls risk client-side timeouts and burn the small per-request governance pool; offload to a queued Scheduled/Map-Reduce script.
- Ignoring `beforeSubmit` vs `afterSubmit` context in a User Event Script — mutating `newRecord` in `afterSubmit` does not persist without an explicit `record.submitFields()` call, since the record has already been committed by that point.

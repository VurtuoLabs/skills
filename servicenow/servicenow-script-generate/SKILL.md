---
name: servicenow-script-generate
description: "Guides writing ServiceNow server-side and client-side scripts — Script Includes, Business Rules, Client Scripts, and the GlideRecord/GlideAjax patterns that connect them — with emphasis on execution order and common runtime pitfalls. TRIGGER when: a user asks to write or debug a Script Include, Business Rule, Client Script, or GlideAjax call, or needs server logic invoked from client code in ServiceNow. DO NOT TRIGGER when: the request is purely declarative (Flow Designer flow, UI Policy without scripting, ATF test authoring) or is about a non-ServiceNow scripting platform."
triggers:
  - "script include"
  - "business rule"
  - "client script glide"
  - "glideajax"
  - "gliderecord"
---

# servicenow-script-generate

ServiceNow's scripting model splits cleanly into server (GlideRecord, GlideSystem, Script Includes) and client (GlideForm/`g_form`, GlideAjax) contexts that never share memory — every cross-boundary call is an async request/response. Getting the execution order and boundary crossing right is the difference between a script that works and one that silently corrupts data or freezes the UI.

## Script Includes

- Class-based Script Includes (`var MyClass = Class.create();`) are the standard reusable server-side unit — extend `AbstractAjaxProcessor` only when the include will be called from a Client Script via GlideAjax; otherwise extend nothing and just define methods.
- Set **Client callable** to true only for includes actually invoked via GlideAjax — leaving it on unnecessarily expands attack surface, since client-callable includes are reachable from browser-originated requests.
- Prefix methods intended for GlideAjax with a clear public name and keep input validation at the top of the method — GlideAjax parameters arrive as strings even for booleans/numbers, so cast explicitly (`getParameter('sysparm_active') == 'true'`).
- Cache expensive lookups (e.g., repeated GlideRecord queries for the same sys_id within one execution) in instance variables rather than re-querying; Script Includes are instantiated per call, not persisted across transactions.

## Business Rules

- **When** matters: `before` runs in-transaction before the database write (use for field validation/defaulting — changes to `current` are free, no `.update()` needed); `after` runs in-transaction after the write (use for touching *other* records, since `current` is already committed); `async` runs out-of-transaction on a scheduled job (use for slow operations — emails, external calls — that shouldn't block the user's save).
- `display` Business Rules run on form load to pass server data to the client via `g_scratchpad` — this is the sanctioned way to get server-only data (e.g., a computed permission flag) into a Client Script without a GlideAjax round-trip.
- Order value (default 100) controls execution sequence among Business Rules of the same `when` on the same table — set it explicitly when a rule depends on another rule's field changes having already applied.
- Use `current.setAbortAction(true)` in a `before` rule to stop the operation entirely (e.g., failed validation) — this is the correct cancel mechanism, not throwing an unhandled exception.

## Client Scripts

- `onLoad` runs after the form renders but before the user interacts — use for setting field visibility/mandatory state based on initial values; avoid slow synchronous work here since it delays perceived form readiness.
- `onChange` fires per field change (with an optional "isLoading" guard param) — use for dependent-field logic like clearing a dependent field or dynamically filtering a reference qualifier via `g_form.addOption`/`setValue`.
- `onSubmit` runs before form submission and can return `false` to block it — use for client-side cross-field validation that needs an immediate `g_form.showFieldMsg` or `g_form.addErrorMessage` without a server round-trip.
- Use `g_form` methods (`getValue`, `setValue`, `setMandatory`, `setVisible`, `setReadOnly`) rather than direct DOM manipulation — Client Scripts must remain compatible with both the classic UI and Service Portal/UI16 rendering.

## GlideRecord and GlideAjax patterns

- Server-side: always pair a query with an explicit `addQuery`/`addEncodedQuery` plus `.setLimit()` or `addActiveQuery()` where applicable — an unbounded `gr.query()` on a large table (incident, sys_audit) is the most common cause of a runaway background job.
- Use `GlideRecordSecure`/respect ACLs by default; only use `GlideRecord` with elevated privilege (`gs.getUser().hasRole(...)` bypass patterns) inside a Script Include deliberately marked for that purpose, never casually in a Business Rule.
- Client-side GlideAjax calls: prefer `getXMLWait()` only for legacy/edge cases — the standard, non-blocking pattern is `ga.getXMLAnswer(callback)`, which returns control to the browser immediately and invokes the callback when the server responds.
- Chain dependent GlideAjax calls via nested callbacks (or a small promise wrapper) rather than firing them in a tight loop — each call is a full HTTP round-trip, so N calls in a loop means N sequential network waits perceived by the user.

## Anti-patterns to avoid

- Calling `ga.getXMLWait()` (synchronous GlideAjax) in an `onChange`/`onLoad` Client Script — this blocks the browser's main thread until the server responds, freezing the form and is explicitly discouraged since it can deadlock the session under load.
- Writing an `after` Business Rule on table A that updates table B, which has its own Business Rule updating table A again — this creates an infinite or near-infinite loop; guard with a condition check or move one side into `async`/a flow with idempotency logic.
- Doing `current.update()` inside a `before` Business Rule — the DB write is about to happen anyway, so this either double-writes or throws; just mutate `current`'s fields and let the platform commit.
- Putting business logic directly in a Client Script instead of delegating to a Script Include via GlideAjax — client scripts run entirely in the browser and cannot be trusted for anything security- or data-integrity-relevant, since users can disable or tamper with client-side JS.

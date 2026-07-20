---
name: sheets-apps-script-generate
description: Writes Google Apps Script (V8 runtime) to automate Google Sheets — custom functions invoked as formulas, simple and installable triggers, SpreadsheetApp object-model manipulation, and calls to external APIs via UrlFetchApp. TRIGGER when: the user wants a `=MYFUNCTION()` custom formula, an onEdit/onOpen/time-driven trigger, code that reads or writes ranges programmatically, a Sheets-to-external-API integration (webhooks, REST calls), or help with Apps Script quota errors and execution-time limits. DO NOT TRIGGER when: the user wants a Sheets API call from an external backend (Python/Node client libraries, service-account REST calls) rather than script bound to the spreadsheet itself, or when the task is pure spreadsheet formula authoring with no script involved.
triggers:
  - "apps script"
  - "custom sheets function"
  - "onEdit trigger"
  - "UrlFetchApp"
  - "SpreadsheetApp"
---

# sheets-apps-script-generate

Google Apps Script is the V8-based JavaScript runtime bound to a Sheet (container-bound script) or standalone, giving direct access to the SpreadsheetApp service without OAuth boilerplate. Use it whenever automation needs to live inside the spreadsheet's edit/open lifecycle or be callable as a formula.

## Custom functions

- A function becomes a formula the moment it has a JSDoc `@customfunction` tag and returns a value, array of arrays (for spilling ranges), or throws to surface `#ERROR!`. Example: `/** @customfunction */ function DOUBLE(x) { return x * 2; }` is called as `=DOUBLE(A1)`.
- Custom functions run in a sandboxed, restricted context: no `UrlFetchApp`, no `SpreadsheetApp.getUi()`, no user-visible side effects — they must be pure with respect to the sheet. Use `SpreadsheetApp.getActiveSpreadsheet()` reads sparingly since recalculation can fire the function thousands of times.
- Array-formula behavior: return a 2D array to fill adjacent cells (equivalent to `ARRAYFORMULA`); Sheets auto-expands the output range and errors with `#REF!` if something blocks the spill.
- Cache expensive lookups with `CacheService.getScriptCache()` (6-hour max TTL) since custom functions cannot call `UrlFetchApp` directly — precompute via a time-driven trigger and read cached/staged values instead.

## Triggers

- **Simple triggers** (`onEdit(e)`, `onOpen(e)`, `onSelectionChange(e)`) are reserved function names Apps Script calls automatically; they run with limited authorization (no `UrlFetchApp`, no services requiring consent) and cannot be used for actions needing an external API call.
- **Installable triggers** (via `ScriptApp.newTrigger('functionName').forSpreadsheet(ss).onEdit().create()`, or `.onFormSubmit()`, `.timeDriven().everyMinutes(5).create()`) run with full authorization and can call `UrlFetchApp`, `MailApp`, etc. Set these up once from a setup function, not on every execution.
- The event object `e` on edit triggers exposes `e.range`, `e.oldValue`, `e.value`, and `e.source` — always check `e.range.getSheet().getName()` to scope logic to the intended tab and avoid firing on unrelated edits.
- Time-driven triggers count against the per-user daily trigger-runtime quota; prefer the coarsest interval that meets the requirement (hourly vs. every-minute) to avoid execution exhaustion.

## SpreadsheetApp object model and batching

- Hierarchy: `Spreadsheet` → `Sheet` → `Range`. Get values in bulk with `sheet.getDataRange().getValues()` or `sheet.getRange(row, col, numRows, numCols).getValues()`, returning a 2D array — never loop `getRange(r,c).getValue()` cell-by-cell, which multiplies round-trips and is the single biggest cause of script timeouts.
- Write back with a single `range.setValues(data)` call; batch reads/writes are orders of magnitude faster than per-cell calls because each Sheets service call is a remote RPC.
- Use `SpreadsheetApp.flush()` to force pending changes to write before a subsequent read that depends on them (e.g., after `setValues` and before triggering a recalculation-dependent read).

## Calling external APIs

- `UrlFetchApp.fetch(url, {method, headers, payload, muteHttpExceptions: true})` is the only outbound HTTP mechanism; always set `muteHttpExceptions: true` and check `response.getResponseCode()` explicitly rather than letting Apps Script throw on non-2xx.
- Store secrets (API keys, tokens) in `PropertiesService.getScriptProperties()`, never hardcoded in source — script properties are per-project and not exposed to editors without script access.
- For OAuth2-protected APIs, use the community `OAuth2` library (via Libraries panel) rather than hand-rolling token refresh logic.

## Quotas and execution limits

- Script execution is capped at 6 minutes per run for consumer accounts (30 minutes for Workspace with certain triggers); long jobs must checkpoint progress (e.g., last processed row in `PropertiesService`) and re-trigger themselves via a time-driven continuation.
- `UrlFetchApp` calls are capped at 20,000/day (consumer) and URL fetch calls also have their own timeout (~60s per call); batch external API requests where the target API supports it.
- Custom functions have a per-cell 30-second timeout and Sheets throttles rapid recalculation storms — avoid volatile-feeling patterns like calling `NOW()` or referencing whole-column ranges inside a custom function.

## Anti-patterns to avoid

- Looping `getValue()`/`setValue()` per cell instead of batching with `getValues()`/`setValues()` — causes timeouts on anything beyond a few hundred cells.
- Calling `UrlFetchApp` or requesting OAuth scopes from inside a simple trigger (`onEdit`, `onOpen`) — it will silently fail due to restricted authorization; use an installable trigger instead.
- Hardcoding API keys directly in script source instead of `PropertiesService` — leaks credentials to anyone with editor access to the script.

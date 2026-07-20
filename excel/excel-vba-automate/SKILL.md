---
name: excel-vba-automate
description: Writes and reviews VBA macros for Excel automation, covering the Workbook/Worksheet/Range object model, event-driven procedures like Workbook_Open and Worksheet_Change, and robust error handling with On Error GoTo. Flags common performance and reliability pitfalls in macro code. TRIGGER when: the user asks to write, fix, or review a VBA macro or Sub/Function; the task involves automating repetitive Excel actions across sheets or workbooks; the user mentions Workbook_Open, Worksheet_Change, or other Excel events; a macro is slow, crashes, or silently produces wrong results. DO NOT TRIGGER when: the request is purely about writing worksheet formulas with no macro code, or about Power Query M transformations with no VBA involved.
triggers:
  - "excel vba macro"
  - "worksheet_change event"
  - "on error goto"
---

# excel-vba-automate

VBA remains the right tool when Excel needs to drive imperative logic, react to user events, or touch the outside world (files, other apps, APIs) — this skill covers writing that code so it's correct, fast, and fails safely.

## Object model basics

- The hierarchy is **Application → Workbook → Worksheet → Range**; always qualify references explicitly (`ThisWorkbook.Worksheets("Data").Range("A1")`) rather than relying on the implicit ActiveWorkbook/ActiveSheet, which changes as the user clicks around.
- `Range` vs `Cells`: `Range("A1:B10")` takes A1-style strings, while `Cells(row, col)` takes numeric indices — use `Cells` inside loops where row/column are variables.
- `Range.End(xlDown)` / `.End(xlUp)` replicate Ctrl+Arrow key navigation and are the standard way to find the last used row/column without hardcoding bounds.
- Use `With ... End With` blocks when setting multiple properties on the same object to avoid re-resolving the reference each time and to make intent clearer.
- Declare variables with explicit types (`Dim ws As Worksheet`, `Dim rng As Range`) and put `Option Explicit` at the top of every module to catch typos as compile errors instead of runtime bugs.

## Event-driven macros

- `Workbook_Open()` in the ThisWorkbook module runs once when the file opens — use it for setup like refreshing external data or resetting a dashboard view, but keep it fast since it blocks the user.
- `Worksheet_Change(ByVal Target As Range)` fires on every cell edit; always check `If Not Intersect(Target, Range("B2:B100")) Is Nothing Then` to scope the logic to relevant cells, and wrap the body with `Application.EnableEvents = False` / `True` to prevent the handler from re-triggering itself when it writes back to the sheet.
- `Workbook_BeforeSave` and `Workbook_BeforeClose` are useful for validation gates (e.g., blocking save if required fields are blank) — set `Cancel = True` to stop the action.
- Event code lives in the sheet/workbook object modules (not a standard module) — code placed in the wrong module simply never fires, which is a common source of "my macro doesn't run" reports.

## Error handling patterns

- Standard pattern: `On Error GoTo ErrHandler` at the top of a Sub, a normal exit before the handler (`Exit Sub`), then the `ErrHandler:` label that inspects `Err.Number` / `Err.Description` and cleans up.
- Always restore state in the handler — re-enable `Application.ScreenUpdating`, `Application.Calculation`, and `Application.EnableEvents` — so a mid-loop failure doesn't leave Excel in a degraded state for the rest of the session.
- Use `On Error Resume Next` only for a single, deliberate line where failure is expected and immediately checked (e.g., testing whether a sheet exists), then reset with `On Error GoTo 0` right after.
- Wrap any external interaction — `Workbooks.Open` on a file path, ADO/API calls, `CreateObject` for another application — in its own error-checked block, since these are the operations most likely to fail for reasons outside the macro's control (missing file, network timeout, permission denied).

## Anti-patterns to avoid

- Hardcoding ranges like `Range("A1:A500")` instead of computing the used range dynamically, which silently drops data when the sheet grows.
- Leaving `Application.ScreenUpdating = True` and `Application.Calculation = xlCalculationAutomatic` during large loops, causing the screen to flicker-redraw and the workbook to recalculate on every cell write — set both to False/manual before the loop and restore them after (inside the error handler too).
- Looping cell-by-cell over a large range with `.Value` reads/writes instead of pulling the range into a Variant array, processing in memory, and writing back once — the array approach is often 10-100x faster.
- Calling external files, databases, or web APIs with no error handling, so a missing file or timeout crashes the macro mid-run and leaves partially-written data on the sheet.

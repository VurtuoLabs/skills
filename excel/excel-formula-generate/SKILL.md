---
name: excel-formula-generate
description: Generates and debugs complex Excel formulas, with emphasis on modern dynamic-array functions (XLOOKUP, FILTER, SORT, UNIQUE, LET, LAMBDA) and systematic techniques for tracing errors in deeply nested expressions. Also advises when a formula is the right tool versus reaching for VBA or Power Query. TRIGGER when: the user asks to write, fix, or explain an Excel formula; a formula returns #REF!, #SPILL!, #N/A, #VALUE!, #CALC!, or #NAME?; the user wants to replace VLOOKUP/INDEX-MATCH with XLOOKUP or array-based logic; the user asks how to break down or evaluate a nested formula. DO NOT TRIGGER when: the task is about writing VBA macros, building Power Query steps, or general dashboard/chart layout with no formula authoring or debugging involved.
triggers:
  - "excel formula"
  - "XLOOKUP FILTER LET LAMBDA"
  - "#REF #SPILL #N/A error"
---

# excel-formula-generate

Excel's modern function set (Excel 365 / 2021+) replaces many classic patterns with dynamic-array formulas that spill results automatically and compose more readably than legacy nested IF/INDEX/MATCH chains. This skill covers writing them correctly and diagnosing why they break.

## Modern function toolkit

- **XLOOKUP(lookup_value, lookup_array, return_array, [if_not_found], [match_mode], [search_mode])** replaces VLOOKUP/HLOOKUP: no column-index counting, native left-lookups, and an explicit `if_not_found` argument that avoids wrapping in IFERROR.
- **FILTER(array, include, [if_empty])** returns all matching rows as a spill range; combine boolean conditions with `*` (AND) or `+` (OR), e.g. `FILTER(data, (region="West")*(amount>1000))`.
- **SORT**/**SORTBY** order a spilled or literal range without helper columns; **UNIQUE(array, [by_col], [exactly_once])** dedupes or finds singleton values.
- **LET(name1, value1, name2, value2, ..., calculation)** assigns names to intermediate results inside one formula, cutting repeated subexpressions and making each step readable.
- **LAMBDA(param1, ..., calculation)**, usually bound to a name via Name Manager, builds reusable custom functions in pure formula language — pair with **LAMBDA** helpers like MAP, REDUCE, SCAN, and BYROW/BYCOL for row-wise or iterative logic without VBA.
- Nest FILTER inside SORT inside LET to build a single self-documenting "query" formula instead of stacking helper columns across the sheet.

## Debugging nested formulas

- Select a subexpression in the formula bar and press F9 to evaluate just that piece in place; press Esc afterward to avoid accidentally hardcoding the result.
- Use the built-in **Evaluate Formula** dialog (Formulas tab) to step through calculation order one operation at a time, which is more reliable than F9 for formulas with multiple nested functions.
- Build formulas outward-in: get the innermost lookup/filter working and confirmed correct in its own cell first, then wrap it, rather than writing the full nested formula blind.
- Use **Trace Precedents** / **Trace Dependents** (Formulas tab) to visualize which cells feed a formula, especially useful after inheriting a workbook with unclear structure.

## Common errors and root causes

- **#SPILL!** means the spill range is blocked by non-empty cells or the array is unbounded (e.g., a whole-column reference multiplying whole-column reference); clear the target range or scope the input ranges.
- **#REF!** typically follows a deleted row/column/sheet that a formula pointed to, or an INDEX/OFFSET argument resolving outside the sheet bounds.
- **#N/A** from lookup functions usually means a genuine non-match, a trailing-space/type mismatch (text "100" vs number 100), or wrong `match_mode`; TRIM/VALUE the lookup key before comparing.
- **#CALC!** appears when a dynamic-array function returns an empty array or an unsupported combination (e.g., FILTER with no matches and no `if_empty` fallback).
- **#NAME?** commonly means a function typo, a missing closing parenthesis, or use of a dynamic-array function in a workbook saved in compatibility mode / an older Excel version that doesn't support it.

## When to reach for VBA or Power Query instead

- Prefer a formula when the transformation is per-cell/per-row logic that should recalculate live as inputs change.
- Prefer **Power Query** when reshaping large external datasets (unpivoting, merging many sources, removing duplicates at scale) — it's faster than array formulas on big data and the steps are auditable.
- Prefer **VBA** when the task requires side effects (file I/O, sending email, manipulating other applications) or imperative control flow that formulas can't express, such as multi-sheet loops with conditional formatting changes.

## Anti-patterns to avoid

- Wrapping every lookup in IFERROR to silently swallow #N/A instead of using XLOOKUP's `if_not_found` argument or investigating the real mismatch.
- Referencing entire columns (A:A) in array formulas on large sheets, which forces Excel to evaluate far more rows than exist and slows recalculation.
- Rebuilding the same subexpression three times in one formula instead of naming it once with LET.

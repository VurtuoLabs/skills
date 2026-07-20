---
name: excel-power-query-build
description: Builds Power Query (M language) transformations for Excel data models, covering query folding and its performance implications, common reshaping steps like unpivot/merge/append/custom columns, and connecting to refreshable external sources such as CSV, SQL databases, and web APIs. TRIGGER when: the user asks to import, clean, reshape, or combine data with Power Query or Get & Transform; the user mentions M language, applied steps, query folding, or the Advanced Editor; a query is slow to refresh or pulls an entire external table instead of filtering server-side; the user needs a refreshable connection to CSV/SQL/web data. DO NOT TRIGGER when: the task is only about writing worksheet formulas or VBA macros with no query/ETL step involved.
triggers:
  - "power query M language"
  - "query folding"
  - "unpivot merge queries"
---

# excel-power-query-build

Power Query is Excel's ETL layer: it records transformations as a sequence of auditable steps in the M language and can refresh against live external sources, making it the right tool for reshaping data before it reaches formulas or PivotTables.

## Query folding

- Query folding is when Power Query translates its applied steps back into a single query pushed down to the source (e.g., a SQL `WHERE`/`GROUP BY`), instead of pulling the full table into Excel and filtering locally — this is the single biggest performance lever for database sources.
- Folding breaks the moment a step can't be translated to the source's query language; common fold-breakers include custom M functions, `Table.AddIndexColumn`, merges against non-foldable queries, and changing column data types in a way the connector doesn't support.
- Order steps to keep foldable operations (filter rows, remove columns, group by, sort) as early as possible, and push non-foldable steps (custom columns with M logic, fuzzy merges) to the end so as much work as possible happens on the server.
- Right-click a step and check whether **"View Native Query"** is available — if it's greyed out, folding has already broken upstream of that step.
- Folding only applies to sources that support it (SQL Server, SQL-based databases, OData, some web APIs); flat-file sources like CSV/Excel have nothing to fold into and are bounded purely by local processing.

## Common transformation steps

- **Unpivot Columns** turns wide data (e.g., one column per month) into a long/tall table with Attribute/Value columns — essential before feeding data into a PivotTable or data model that expects normalized rows; use "Unpivot Other Columns" when new columns may be added later so the transformation doesn't need updating.
- **Merge Queries** joins two queries on key columns (like SQL JOIN) — choose the join kind explicitly (Left Outer, Inner, Anti) rather than accepting the default, and expand only the columns actually needed to avoid bloating the result.
- **Append Queries** stacks queries with matching schemas (like SQL UNION) — useful for combining multiple months' CSV exports into one table; mismatched column names create extra columns instead of erroring, so verify column alignment first.
- **Custom Column** (`Add Column > Custom Column`) writes an M expression per row, e.g. `if [Amount] > 1000 then "High" else "Low"` — prefer this over post-hoc Excel formulas when the logic should refresh automatically with the query.
- **Group By** with aggregations (Sum, Count, All Rows) replaces manual SUMIF/COUNTIF patterns and, on foldable sources, executes as a server-side GROUP BY.

## Connecting to external sources

- **CSV/text files**: `Data > Get Data > From File > From Text/CSV` creates a connection that can be set to refresh on file change; watch for delimiter and encoding detection errors on files with inconsistent formatting.
- **SQL databases**: `Get Data > From Database > From SQL Server` (or other DB connector) supports both Import mode and a native SQL statement option — writing your own SQL in the connector opts out of query folding for anything Power Query can't further push down, so prefer letting Power Query build the query when folding matters.
- **Web APIs**: `Get Data > From Web` accepts a URL and can be parameterized for pagination or authentication headers; for APIs requiring auth tokens, use `Web.Contents` with the `Headers` record option, and store credentials via the connection's credential manager rather than hardcoding them in the M script.
- All connections are refreshable via `Data > Refresh All` or `Queries & Connections > Properties > Refresh every N minutes`; set "Refresh data when opening the file" for workbooks that should always show current source data.
- Use **Query Parameters** (Manage Parameters) for values like file paths, date ranges, or environment (dev/prod) so the same query logic can be repointed without editing M code.

## Anti-patterns to avoid

- Writing a fuzzy merge or custom-function step in the middle of an otherwise foldable query chain, silently killing performance on large SQL sources without realizing it.
- Loading full source tables into the Excel workbook and filtering afterward in a PivotTable instead of filtering rows during the query, which bloats file size and slows refresh.
- Hardcoding file paths or credentials directly in M code instead of using parameters and the built-in credential store, which breaks when the workbook moves machines.

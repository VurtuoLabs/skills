---
name: excel-dashboard-build
description: "Builds interactive Excel dashboards, covering data-model structuring with PivotTables, slicer/timeline-driven interactivity, chart-type selection, and performance tuning for large workbooks. TRIGGER when: the user asks to design or build an Excel dashboard, report, or interactive summary sheet; the task involves PivotTables/PivotCharts, slicers, or timelines; the user needs guidance on which chart type fits their data; a dashboard workbook is slow to open, recalculate, or filter. DO NOT TRIGGER when: the request is purely about writing individual formulas, VBA macros, or Power Query steps with no dashboard layout, chart, or PivotTable component involved."
triggers:
  - "excel dashboard"
  - "pivottable slicer timeline"
  - "chart type selection"
---

# excel-dashboard-build

A good Excel dashboard is a thin interactive layer over a clean data model — the layout choices and chart types matter, but so does keeping the underlying workbook fast enough to stay interactive as data grows.

## Structuring the data model

- Load source data as a proper **Excel Table** (`Ctrl+T`) or into the **Data Model** via Power Pivot rather than loose ranges — Tables auto-expand with new rows and PivotTables built on them don't need range updates.
- For multiple related tables (e.g., Orders, Customers, Products), use **Power Pivot's Data Model** with defined relationships instead of VLOOKUP-ing everything into one flat sheet — this keeps each table normalized and lets PivotTables aggregate across tables directly.
- Build one or more **PivotTables** as the calculation engine feeding the dashboard, then reference PivotTable output cells (or use **GETPIVOTTABLE**) from chart and KPI cells, rather than duplicating aggregation logic in separate formulas.
- Separate the workbook into distinct sheets by role — raw data, staging/model, calculation, and the dashboard canvas itself — so the dashboard sheet contains only presentation elements and is fast to render.
- Use **DAX measures** (SUM, CALCULATE, DISTINCTCOUNT-based) in the Data Model for aggregations that need to respond dynamically to slicer selections across multiple PivotTables at once.

## Interactivity: slicers and timelines

- **Slicers** (`Insert > Slicer`, or from a PivotTable's Analyze tab) give clickable filter buttons for categorical fields; connect one slicer to multiple PivotTables via `Slicer > Report Connections` so a single click filters every chart on the dashboard simultaneously.
- **Timelines** (`Insert > Timeline`) are the date-specific equivalent of slicers, offering period-granularity buttons (Days/Months/Quarters/Years) instead of a flat list of every date value — use them for any date-based filter instead of a slicer on a date field.
- Style slicers to reflect selection state clearly (Slicer Styles gallery) and arrange them consistently at the top or side of the dashboard so filter state is always visible to the viewer.
- For dashboards driven by the Data Model rather than a single PivotTable, slicers based on the model's lookup tables will filter every connected PivotTable/PivotChart at once — plan the model with dedicated dimension tables to make this work cleanly.

## Chart type selection

- **Line chart**: trend over continuous time (monthly revenue, daily active users) — avoid for fewer than ~4 data points, where a simple KPI or column chart reads better.
- **Column/bar chart**: comparing discrete categories; use horizontal bars when category labels are long or there are many categories, vertical columns for short labels and time-like sequences.
- **Stacked column/bar**: part-to-whole comparison across categories, but only when the number of segments is small (3-5) — beyond that, segments become hard to compare visually.
- **Combo chart** (column + line on secondary axis): pairing a magnitude metric with a rate/percentage metric, e.g., revenue bars with margin-% line.
- **Scatter chart**: relationship/correlation between two continuous variables — never use a line chart for this, since it implies an ordering the data doesn't have.
- Avoid pie/donut charts beyond 4-5 slices and avoid 3D chart variants entirely — both distort visual comparison and add no analytical value.
- **PivotChart** should be used whenever the chart's source is a PivotTable, since it inherits the same field buttons and filter connections rather than needing to be manually kept in sync.

## Performance for large workbooks

- Avoid volatile functions (`NOW()`, `TODAY()`, `RAND()`, `OFFSET()`, `INDIRECT()`) on dashboard sheets — these recalculate on every workbook change regardless of dependency, and compound badly across hundreds of dashboard cells.
- Avoid full-column references (`SUM(A:A)`) in formulas feeding the dashboard; scope ranges to the actual data extent (a Table reference like `Orders[Amount]` auto-scopes correctly and is both faster and safer).
- Set PivotTables to refresh on demand rather than "Refresh on file open" if the source is large and doesn't change every session, and disable "Save source data with file" for Data Model-based Pivots to keep file size down.
- Turn off automatic calculation (`Formulas > Calculation Options > Manual`) while doing heavy layout/design work on a large dashboard, then recalculate deliberately with `Ctrl+Alt+F9`.
- Limit conditional formatting rules on large ranges (especially formula-based rules) since Excel evaluates them on every recalculation pass — prefer rules scoped to the exact used range, not entire columns.

## Anti-patterns to avoid

- Building charts directly off raw data ranges instead of PivotTables/Tables, which breaks the moment new rows are added and requires manually re-selecting chart source ranges.
- Using unconnected slicers per PivotTable so clicking one filter control leaves the other charts on the same dashboard out of sync.
- Choosing a 3D or pie chart for a comparison with many categories purely for visual appeal, obscuring the actual magnitude differences the dashboard is meant to convey.

---
name: power-bi-report-generate
description: "Guides building Power BI reports and data models — star schema modeling fundamentals, when to write a DAX measure versus a calculated column, relationship cardinality and cross-filter direction choices, and performance considerations like import vs. DirectQuery and avoiding bidirectional filters on large fact tables. TRIGGER when: a user is designing a Power BI data model, writing DAX, setting up table relationships, choosing storage mode, or diagnosing slow report performance. DO NOT TRIGGER when: the task is pure Power BI Desktop UI styling/visuals with no modeling or DAX involved, or the user is working in Excel Power Pivot/Analysis Services outside a Power BI report context."
triggers:
  - "Power BI star schema"
  - "DAX measure vs calculated column"
  - "Power BI relationship cardinality cross filter"
  - "Power BI import vs DirectQuery performance"
---

# power-bi-report-generate

Power BI report quality is decided mostly in the model, not the visuals — a clean star schema with correctly-typed DAX and relationships is what makes reports fast, correct, and maintainable.

## Star schema modeling basics

- Separate tables into facts (transactional, numeric, high-row-count — sales, orders, events) and dimensions (descriptive, low-cardinality — date, product, customer, region); avoid snowflaking dimensions further than necessary since it adds join hops for no real benefit in Power BI's engine.
- Build a dedicated Date dimension table (marked as a date table via "Mark as Date Table") rather than relying on auto date/time hierarchies — this is required for time-intelligence DAX functions (`SAMEPERIODLASTYEAR`, `DATEADD`, `TOTALYTD`) to behave correctly.
- Keep fact tables narrow — strip out descriptive text columns that belong in a dimension, since fact table column cardinality directly drives VertiPaq compression efficiency and model size.
- Model many-to-many business relationships (e.g., a sales rep covering multiple regions) through a bridge table rather than a direct many-to-many relationship on the fact table, to keep filter propagation predictable.

## DAX measures vs. calculated columns

- Measures are computed at query time over the current filter context and are the default choice for aggregations (sums, ratios, YoY %, running totals) — they don't inflate model size and always reflect slicers/filters applied in the report.
- Calculated columns are computed at refresh time and materialized per row — use them only when the result must be sliced/filtered/grouped on directly (a categorical bucket, a flag used in a slicer) since that requires a physical column, not a measure.
- A common mistake is building a calculated column to hold an aggregation that should be a measure (e.g., a per-row "total sales" repeated on every row) — this bloats the model and produces wrong numbers when filters change, because it's frozen at refresh time.
- Prefer calculated columns in dimension tables over fact tables when unavoidable — fact-table calculated columns are the most expensive for compression since they don't benefit from repeated-value encoding as well as low-cardinality dimension columns.

## Relationships: cardinality and cross-filter direction

- Default to one-to-many relationships from dimension (one side) to fact (many side), single cross-filter direction (dimension filters fact) — this matches how star schemas are meant to propagate filters and is the most predictable and performant setup.
- Bidirectional (both) cross-filter direction lets a fact table's filters also propagate back up to a dimension, which is sometimes needed for many-to-many bridge scenarios, but it multiplies the filter-propagation paths the engine must evaluate and can create ambiguous circular logic between multiple fact tables.
- Many-to-many relationships (both sides non-unique) should be a last resort — they're slower to evaluate and harder to reason about than resolving the same requirement with a bridge table and two one-to-many relationships.
- Use `USERELATIONSHIP()` in a measure to activate an inactive relationship (e.g., a second date relationship like ShipDate vs. OrderDate) instead of making both relationships active/bidirectional, which would create ambiguity.

## Performance: storage mode and filter direction

- Import mode loads compressed data into VertiPaq (Power BI's in-memory columnar engine) and is fastest for most reporting workloads; DirectQuery leaves data in the source and issues live queries per visual, trading freshness for materially slower interactivity and source-side query load.
- Use DirectQuery only when real-time/near-real-time data is a hard requirement or source data volume genuinely exceeds what import/Premium capacity can hold — for most BI use cases, scheduled refresh on Import mode is both faster and simpler to maintain.
- Composite models (mixing Import and DirectQuery tables) let you import small dimension tables while DirectQuerying a huge fact table, but watch for "limited relationships" performance warnings when a DirectQuery table relates to an Import table.
- Avoid bidirectional cross-filtering on any relationship touching a large fact table — it forces the engine to evaluate filter context in both directions on every query, which is one of the most common causes of slow visuals reported as "the report is laggy" once row counts grow past a few million.

## Anti-patterns to avoid

- Building a wide, flat single-table model ("just one big Excel-like table") instead of a star schema, which breaks time intelligence and makes filter behavior unpredictable as the model grows.
- Using calculated columns for aggregate values that should be measures, silently freezing numbers at last refresh instead of responding to report filters.
- Turning on bidirectional cross-filter broadly "just to make a slicer work" instead of diagnosing the actual relationship path needed, degrading performance across the whole model.
- Defaulting to DirectQuery for freshness without first checking whether scheduled Import refresh (even hourly) would satisfy the actual business requirement at a fraction of the query latency.

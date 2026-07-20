---
name: dayforce-payroll-report-generate
description: Build and export Dayforce (Ceridian) payroll and reporting queries — using Dayforce's Reporting/Analytics endpoints, scheduled report exports, and effective-dated payroll data (earnings, deductions, taxes) for reconciliation. TRIGGER when: user is building a payroll reconciliation report against Dayforce, exporting earnings/deductions/tax data, scheduling a Dayforce report for a downstream system, or debugging why a payroll extract doesn't tie out to Dayforce's payroll register. DO NOT TRIGGER when: the task is general REST integration unrelated to payroll reporting (use dayforce-rest-api-integrate), or the platform is Workday.
triggers:
  - "Dayforce payroll report"
  - "Dayforce earnings export"
  - "Dayforce reconciliation"
  - "Dayforce tax report"
  - "Ceridian report export"
---

# dayforce-payroll-report-generate

Dayforce payroll data is effective-dated, pay-period-scoped, and split across several report surfaces (Reporting API, scheduled exports, Dayforce Analytics/Insights) — picking the wrong surface, or querying without pinning a pay run, is the main cause of numbers that don't reconcile against the payroll register.

## Report surfaces

- **Report Definitions via the Reporting/Analytics endpoints**: `GET /V1/{clientNamespace}/ReportDefinitions` lists available report templates (many pre-built, some client-authored in the Dayforce Reports module); `POST` to a report execution endpoint kicks off an async run, and results are polled/downloaded once status flips to complete — treat this as an async job pattern, not a synchronous request/response.
- **Scheduled exports**: report templates can be attached to a Dayforce schedule (daily/per-pay-run) that drops output to SFTP or a configured file location — this is the common pattern for recurring payroll GL feeds or benefits carrier files, and is configured in Dayforce admin rather than purely via API calls.
- **Ad hoc/API-driven pulls**: for integrations needing structured data rather than a formatted report, pulling directly from payroll-adjacent resources (Earnings, Deductions, TaxSetups, Timesheets under Employees) via the core REST API is more reliable than parsing a generated report file, at the cost of needing to replicate Dayforce's own aggregation logic.

## Structuring queries against effective-dated payroll data

- Earnings and deduction records are tied to a specific **pay run** (identified by PayGroup + pay period end date, not just a date range) — querying by calendar date range without anchoring to the actual pay run boundaries will split or duplicate amounts that straddle a period.
- Always resolve the pay calendar first (`PayGroups` → pay period definitions) before requesting earnings/deductions, since Dayforce's period-end dates don't always align to calendar week/month boundaries (e.g. semi-monthly, 4-4-5 patterns).
- Retro pay and off-cycle adjustments post against the **original** pay period they correct, not the period in which they were processed — a report scoped only to "current pay period" will miss retro amounts unless it also checks `ProcessedDate`/adjustment flags separate from `PayPeriodEndDate`.
- Deduction and tax records carry both an amount and a calculation basis (e.g. pre-tax vs post-tax, employee vs employer-paid); flattening these into a single "deductions" total without preserving the basis breaks downstream GL mapping.

## Common report types

- **Earnings reports**: regular, overtime, bonus, and imputed-income line items per employee per pay run — reconcile against Timesheets/WorkAssignments totals, since earnings codes map from approved time, not raw punches.
- **Deductions reports**: benefits, garnishments, retirement contributions — garnishments in particular have priority-order and max-percentage rules applied by Dayforce's payroll engine, so a naive sum of deduction codes can overstate what was actually withheld if a cap was hit.
- **Tax reports**: federal/state/local withholding plus employer-paid taxes (FUTA/SUTA equivalents) — multi-state employees (remote workers, multi-jurisdiction work) generate split tax records per jurisdiction per pay run that must be reported separately, not netted.

## Reconciliation gotchas

- Compare exported totals against the Dayforce **Payroll Register** report (the system of record for a finalized pay run) rather than re-deriving totals purely from timesheet/earnings API pulls — voids, manual checks, and off-cycle runs can exist only in the register.
- A pay run isn't final until it reaches a "committed"/finalized status; pulling earnings data on an open (in-progress) pay run will return numbers that can still change before commit.
- Currency and locale settings differ by legal entity for multi-country tenants — summing amounts across PayGroups without checking currency code produces meaningless totals.
- Report output timestamps are typically in the tenant's configured time zone, not UTC — date-boundary mismatches (a Friday pay-run landing in the wrong week) are a frequent symptom of not converting explicitly.

## Anti-patterns to avoid

- Querying earnings/deductions by calendar date range instead of by resolved pay-period boundaries.
- Treating an in-progress (uncommitted) pay run's data as final for reconciliation.
- Summing deduction amounts without preserving pre-tax/post-tax and employee/employer basis, breaking GL mapping.
- Ignoring retro/off-cycle adjustments that post back to a prior pay period instead of the current one.

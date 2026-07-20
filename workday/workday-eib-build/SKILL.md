---
name: workday-eib-build
description: "Build Workday EIB (Enterprise Interface Builder) inbound and outbound integrations — deciding when to use EIB versus REST/RaaS/Studio, structuring inbound data via XML/CSV/Excel and transformation, sequencing load order and validation, and diagnosing common failure modes. TRIGGER when: user is building or debugging a Workday EIB integration, choosing between EIB and other Workday integration tools, structuring a spreadsheet/XML load for Workday, or an inbound EIB load is failing on missing references or stuck approvals. DO NOT TRIGGER when: the task is a REST/RaaS integration with no EIB component (use workday-rest-integrate), or the platform is Dayforce/Ceridian."
triggers:
  - "Workday EIB"
  - "Enterprise Interface Builder"
  - "Workday inbound load"
  - "Workday integration template"
  - "Workday EIB validation error"
---

# workday-eib-build

EIB is Workday's built-in, config-driven tool for bulk-loading data in and pulling reports out, without writing custom code. It's the right default for structured bulk loads (new hires batch, org changes, benefit elections) but the wrong choice for real-time or complex-transformation scenarios — picking the wrong tool up front causes most EIB project pain.

## When to use EIB vs REST / RaaS / Studio

- **EIB inbound** fits high-volume, batch, config-only loads against a known Workday integration template (e.g. "Load Organization Assignments," "Import Candidate," custom template built on a business process) — no code, scheduled or on-demand runs, built-in validation preview.
- **EIB outbound** fits scheduled file drops of RaaS-report-backed data to SFTP/cloud storage, optionally with an XSLT transformation step — good for recurring vendor feeds (benefits carriers, GL extracts) that need a specific file layout.
- **REST/SOAP API** is the better choice for real-time, transactional, or event-driven needs (a self-service app that needs an immediate write-and-confirm) — EIB's batch/queued nature makes it unsuitable for interactive use cases.
- **Workday Studio** (Java-based integration IDE) is the fallback when EIB's transformation capabilities (XSLT only) aren't enough — complex conditional logic, multi-source joins, or custom error handling beyond what EIB's UI supports. Studio requires Workday Integration Cloud entitlement and developer skill EIB does not.
- Document Transformation add-on and Workday's "Core Connector" templates sit between plain EIB and Studio — prebuilt for common third-party systems (payroll vendors, benefit carriers) and worth checking before building a custom EIB template from scratch.

## Structuring inbound EIB data

- Inbound EIB expects data mapped to a specific **integration template** (a Workday-defined or custom-built XML schema corresponding to a business process, e.g. Hire, Request Compensation Change, or a data-load-only template like Organization Assignment). The source file — commonly Excel/CSV via Workday's "Simple/Complex" spreadsheet loader, or raw XML — must be transformed into that template's schema before Workday will accept it.
- EIB's built-in "Excel to XML" mapping step or the "Simple Import" wizard generates the transform for tabular sources; for XML or non-tabular sources, an XSLT stylesheet performs the transform explicitly — malformed XSLT is a common source of "integration ran but loaded zero records" failures with no obvious error.
- Every referenced object in the load (worker, position, organization, cost center, location) must resolve to an object **already existing in Workday**, identified by one of its accepted Reference ID types (WID is not portable and should not be used for external file references) — the ID type used in the source file must match a Reference ID type Workday recognizes for that object type, or the row fails resolution.
- Field order and required-vs-optional fields are defined by the underlying business process/template, not by convenience — a field that's conditionally required (e.g. termination reason only when action code = Terminate) will pass template validation but fail at business-process submission if omitted.

## Load order and validation

- EIB supports a two-stage run: a **validate-only** pass (checks reference resolution and required fields without committing) and the actual **launch** — always run validate-only first on a new or modified template, since Workday's error output at validate stage is more actionable than a partially-committed launch.
- Load order matters when a single integration touches interdependent objects — e.g. Organizations must exist before Positions reference them, and Positions must exist before Worker assignments reference them; sequencing this across multiple EIB runs (or multiple sub-steps within one) is the integration builder's responsibility, Workday will not auto-sequence for you.
- Each inbound row that maps to a business process (Hire, Change Job, etc.) triggers that business process individually — the EIB run itself can report "completed successfully" even though individual rows generated business processes that are now sitting in someone's approval inbox, unstarted.
- Large loads are processed in configurable batch sizes; a failure partway through does not necessarily roll back earlier successful rows — reconciliation after a large load should check actual counts in Workday, not just the EIB run's completion status.

## Common failure modes

- **Missing required references**: a row referencing a cost center, position, or worker ID that doesn't exist yet (often because a prerequisite EIB run hasn't completed or hasn't propagated) — surfaces as a resolution error naming the field, not always an obviously readable message.
- **Business process approval steps blocking completion**: the EIB "succeeds" but the underlying business process (e.g. Hire) is now awaiting an approval step defined in that business process's configuration — data appears "not loaded" to downstream consumers until someone (or an auto-approval rule) clears the step. This is the single most common cause of "the EIB ran clean but nothing changed" tickets.
- **Template/schema drift**: a custom integration template built against one Workday release can break silently after a semiannual Workday release if a referenced business process's required fields changed — re-run validate-only against a sandbox/preview tenant before each release upgrade window.
- **Encoding/format mismatches** in spreadsheet loads (date formats, leading zeros on ID fields, hidden Excel formatting) causing rows to fail type validation even though they "look" correct visually.

## Anti-patterns to avoid

- Launching an EIB run directly without a validate-only pass first, on a new or modified template.
- Assuming EIB "Completed" status means the underlying business processes were approved and effective, rather than just submitted.
- Using WID instead of a portable Reference ID type when building the source file's object references.
- Building a custom EIB/XSLT pipeline for a real-time interactive use case that actually needs REST.

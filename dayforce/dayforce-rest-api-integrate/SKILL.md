---
name: dayforce-rest-api-integrate
description: Integrate with the Dayforce (Ceridian) RESTful Web Services API for HCM, payroll, and timekeeping data — OAuth2 client-credentials auth, tenant-scoped base URLs, core resource endpoints (Employees, PayGroups, WorkAssignments, Timesheets, Punches), cursor-based pagination, and rate-limit handling. TRIGGER when: user is writing or debugging code that calls Dayforce REST endpoints, configuring an OAuth2 client-credentials connection to Dayforce, paginating through Dayforce employee or timesheet data, resolving XRefCode vs internal Dayforce IDs, or troubleshooting effective-dated record retrieval. DO NOT TRIGGER when: the task is building Dayforce payroll/report exports specifically (use dayforce-payroll-report-generate instead), or the platform in question is Workday or a non-HCM system.
triggers:
  - "Dayforce REST API"
  - "Ceridian API integration"
  - "Dayforce XRefCode"
  - "Dayforce OAuth2 client credentials"
  - "Dayforce Timesheets endpoint"
---

# dayforce-rest-api-integrate

Dayforce exposes HCM, payroll, and time/attendance data through a single RESTful Web Services API scoped per-tenant. Getting auth, pagination, and ID resolution wrong is the most common source of broken integrations, since Dayforce's data model differs from typical CRUD APIs in ways that aren't obvious from a first read of the docs.

## Auth

- Dayforce uses OAuth2 **client-credentials** grant against a tenant-specific token endpoint (commonly `https://<tenant-host>/api/<tenant-id>/token` or an Identity Cloud endpoint depending on the Dayforce release/region). Credentials are a client ID/secret pair issued per integration, not per user.
- The access token is a bearer token sent as `Authorization: Bearer <token>` on every call; tokens are short-lived (typically ~1 hour) and must be refreshed proactively — do not wait for a 401 to trigger refresh in high-throughput jobs.
- Some older/legacy Dayforce integrations still use HTTP Basic Auth with a dedicated integration user; this is being deprecated tenant-by-tenant in favor of OAuth2, so confirm which mode a given tenant supports before assuming client-credentials is available.
- Every request is scoped to a **Company ID** or tenant path segment (e.g. `/V1/{ClientNamespace}/...`), separate from the OAuth client — a valid token for one tenant will not implicitly grant access to another company code in a multi-entity Dayforce instance.

## Base URL and versioning

- Base URLs are environment- and datacenter-specific (`usr##`, `emea##`, `apj##` style host prefixes) — never hardcode a host across environments; resolve it per tenant/config, since sandbox (config/test) and production hosts differ.
- The API is versioned in the path (`/V1/...`); Dayforce adds fields and endpoints within a version rather than breaking changes, but new mandatory query behaviors (like pagination cursors) have been introduced as opt-in-then-default over time — check the release notes for the tenant's Dayforce version (e.g. R2024, R2025 wave).

## Common resource endpoints

- **Employees**: `GET /V1/{clientNamespace}/Employees` — supports filtering by `XRefCode`, `SSN` (if enabled), `BadgeNumber`, and `LastModifiedTimestamp` for delta syncs. Expand parameters (`expand=WorkAssignments,EmploymentStatuses,PersonalDocuments`) pull related sub-resources in one call instead of N+1 requests.
- **PayGroups**: `GET /V1/{clientNamespace}/PayGroups` — used to resolve pay calendar and payroll cutoff context before querying earnings/timesheet data scoped to a pay period.
- **WorkAssignments**: nested under Employees or queryable directly; represents the effective-dated job/position/org-unit assignment — an employee can have multiple concurrent or historical WorkAssignments, so "current" requires an effective-date filter, not just the latest record returned.
- **Timesheets / Punches**: `GET /V1/{clientNamespace}/Employees/{XRefCode}/Timesheets` for approved timesheet summaries, vs the lower-level Punches endpoint for raw clock in/out events — reports built off Punches without applying pay policy rules will not match approved Timesheets totals.

## Pagination

- List endpoints return a bounded page (default page sizes commonly 25–100 depending on endpoint) plus a `Paging` object containing a `Cursor` value — request the next page by passing that cursor back (`cursor=<value>`), not by incrementing an offset/page-number parameter.
- Cursors are opaque and endpoint-specific; do not attempt to construct or reuse a cursor from one resource query against a different query's parameters — a changed filter set invalidates the cursor chain.
- Always loop until the response omits a next cursor (or returns an empty result set) — a fixed "assume 3 pages" loop count silently drops records as headcount or timesheet volume grows.

## Rate limiting and gotchas

- Dayforce enforces per-tenant rate limits (requests/minute and concurrent-connection caps); a 429 response should trigger exponential backoff, not immediate retry — bursty batch jobs (e.g. nightly full employee syncs) are the most common trigger.
- **XRefCode vs internal ID**: nearly every resource has an internal numeric/GUID identifier plus a client-configurable `XRefCode` (external reference code). Integrations should always key off `XRefCode` for cross-system matching — internal IDs are not guaranteed stable across tenant migrations or data reloads.
- **Effective-dated records**: Employee, WorkAssignment, Compensation, and similar entities are effective-dated (`EffectiveStart`/`EffectiveEnd`). A GET without an `asOfDate` parameter typically returns the currently-effective row, but historical/future-dated changes (e.g. a promotion effective next pay period) require explicit date filtering to retrieve or avoid double-counting.
- Write operations (POST/PUT) commonly require sending the full effective-dated object shape, including unchanged fields — partial payloads can null out fields Dayforce expects to be explicitly re-asserted.

## Anti-patterns to avoid

- Hardcoding page-count loops instead of following the `Paging.Cursor` chain until exhausted.
- Matching records on Dayforce's internal numeric ID instead of `XRefCode`, breaking after a data migration or tenant refresh.
- Querying "current" employee/assignment data without an effective-date filter, silently picking up terminated or future-dated rows.
- Retrying 429s immediately in a tight loop instead of backing off, which can extend a temporary throttle into a full outage for the integration.

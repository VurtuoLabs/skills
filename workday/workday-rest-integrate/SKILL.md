---
name: workday-rest-integrate
description: "Integrate with Workday's REST API and Report-as-a-Service (RaaS) for HCM and Financials data — OAuth2/ISU (Integration System User) auth, tenant URL structure, core resource endpoints (Workers, Positions, Journals), and Workday-specific quirks like WID vs Reference ID and asynchronous business process transactions. TRIGGER when: user is writing or debugging code calling Workday REST endpoints or RaaS reports, configuring an ISU-based OAuth2 connection to Workday, resolving WID vs Reference ID for a Worker/Position, or handling async business-process-driven writes (e.g. Change Job, Hire). DO NOT TRIGGER when: the task is specifically about building an EIB load (use workday-eib-build instead), or the platform is Dayforce/Ceridian."
triggers:
  - "Workday REST API"
  - "Workday ISU OAuth"
  - "Workday RaaS"
  - "Workday WID"
  - "Workday business process API"
---

# workday-rest-integrate

Workday's REST API covers a growing but still partial slice of the functionality available through SOAP/RaaS, and its business-process-driven data model means writes often behave as async workflow submissions rather than instant record updates. Knowing which surface to use, and how to identify records correctly, avoids most integration failures.

## Auth

- Standard pattern is OAuth2 with an **Integration System User (ISU)** — a special non-human Workday user account created specifically for API access, paired with an **Integration System Security Group (ISSG)** that grants it scoped domain security policy permissions (e.g. "Worker Data: Public Worker Reports" or specific Staffing/Compensation domains).
- Auth flow is typically OAuth2 **client credentials** (for tenant-to-tenant/system integrations) or **Authorization Code** grant (when a user context is needed); the ISU's credentials are registered against a Workday-generated Client ID/Secret from the tenant's "Register API Client" task.
- Refresh tokens issued for the ISU can be long-lived, but access tokens are short-lived — cache and refresh proactively rather than re-authenticating per call, since Workday tenants also enforce concurrent-session and rate limits per integration.
- Every ISU is bound to specific domain security policies via its ISSG; a 403 on an otherwise well-formed request is more often a missing security group grant than a malformed call — check the ISSG's assigned domains before debugging the payload.

## Tenant URL structure

- REST base URLs follow `https://{wd-datacenter}.workday.com/ccx/api/{version}/{tenant}/...` — the datacenter prefix (`wdX`) and tenant name are both required and differ between sandbox (Implementation/Preview) and production tenants; never assume a single environment's URL is reusable.
- RaaS reports are exposed at a distinct path pattern, typically `https://{wd-datacenter}.workday.com/ccx/service/customreport2/{tenant}/{owner}/{report-name}` — these are custom reports built in Workday and published "as a web service," returning JSON or XML/CSV depending on report output format configured by the report owner.
- API version matters: Workday ships REST API versions tied to its biannual releases; a field or endpoint available in a newer version may not exist on a tenant still pinned to an older API version in the integration's endpoint URL.

## Common resource endpoints

- **Workers**: `GET /ccx/api/v#/{tenant}/workers` — the core HCM resource, returning worker profile, position, and related sub-resources; supports filtering and `?expand=` style inclusion of related data (organizations, compensation) though not every sub-resource is available on every API version.
- **Positions**: position-management-model tenants expose Position resources distinct from Worker — a single position can have an incumbent worker, be vacant, or be frozen, and position ID (not worker ID) is often the anchor for org-chart and headcount-planning integrations.
- **Journals** (Financials): `GET/POST .../journals` under the Financial Management API surface — journal entries follow Workday's ledger/accounting-period structure, and posting a journal via API still routes through Workday's approval business process if one is configured on the journal source.
- Custom RaaS reports are frequently the more practical integration point for HCM data that doesn't map cleanly to the REST resource model (e.g. flattened compensation history, custom eligibility calculations) — many integrations use REST for transactional writes and RaaS for bulk/reporting reads.

## Workday-specific quirks

- **WID vs Reference ID**: every Workday object has an internal **Workday ID (WID)** — a system-generated GUID — plus one or more business-friendly **Reference IDs** (Employee ID, Position ID, custom organization IDs, etc.). WIDs are stable within a tenant but are **not** portable across tenants (sandbox refreshes regenerate them) — integrations should key off Reference ID/custom ID types for cross-environment stability, and only use WID for same-session object resolution.
- **Business process transactions are asynchronous by design**: a POST that "hires" or "changes job" for a worker doesn't just update a field — it initiates a Workday **Business Process** (e.g. Hire, Change Job, Request Compensation Change) that may require downstream approvals, and the API call succeeds even if the business process is left pending in someone's inbox. Do not assume the write is "done" on a 201/202 — poll or event-subscribe to confirm the business process reached a completed state before treating the change as effective.
- Effective-dating applies broadly (compensation, position assignments, organization membership) — a GET without specifying an "as of" moment returns the currently effective picture, which may not match a future-dated change already submitted and pending approval.
- Workday enforces domain security at the field level, not just the endpoint level — an ISU with resource access can still get nulled-out or omitted fields if it lacks the specific domain security policy grant for that data element (e.g. compensation amounts).

## Anti-patterns to avoid

- Persisting Workday IDs (WID) as a durable cross-system key instead of a stable Reference ID/custom ID.
- Treating a successful business-process-initiating POST as confirmation the change is live, without checking the business process's actual completion status.
- Hardcoding the REST API version in integration code without a plan to test against the tenant's next release upgrade.
- Assuming a 403 is a payload bug before checking whether the ISU's security group actually grants the relevant domain.

---
name: adp-workforce-now-integrate
description: "Guides integration with ADP Workforce Now via ADP APIs — covering the OAuth2 client-credentials + mutual TLS (mTLS) authentication pattern ADP mandates, the ADP Marketplace/API Central app registration and certificate provisioning flow, common HR/payroll resource endpoints (workers, payroll-instructions, events), and choosing event-driven notification subscriptions over polling. TRIGGER when: a user is building or debugging a connector to ADP Workforce Now, asks about ADP OAuth/mTLS setup, ADP API Central app registration, worker or payroll-instructions endpoints, or ADP event notification subscriptions. DO NOT TRIGGER when: the user is asking about generic payroll concepts unrelated to ADP's APIs, working with a different HRIS (Workday, Dayforce, BambooHR), or doing ADP UI/administrative configuration with no API integration involved."
triggers:
  - "ADP Workforce Now API"
  - "ADP OAuth mutual TLS"
  - "ADP payroll-instructions endpoint"
  - "ADP event notification subscription"
---

# adp-workforce-now-integrate

Integrating with ADP Workforce Now means working through ADP's API Central/Marketplace gateway, which layers strict certificate-based trust on top of standard OAuth2 — most connector bugs come from mishandling that layer, not the business data itself.

## App registration and API Central structure

- Every integration starts as a registered application in ADP Marketplace (build.adp.com), which issues a `client_id`/`client_secret` pair scoped to a specific ADP client (employer) connection or a multi-tenant "Marketplace" listing.
- ADP API Central groups resources by domain: HCM (`/hr/v2/workers`), payroll (`/payroll/v1/payroll-instructions`), time (`/time/v2`), and each domain has its own product registration and scope grant, even under one app.
- Sandbox access uses ADP's shared demo data (fictitious worker `G3N1Z2...` style AOIDs); production access requires a signed Client Connect Agreement and a separate certificate pair per environment.

## OAuth2 + mutual TLS authentication

- ADP requires OAuth2 client_credentials grant AND mutual TLS on every call to `/auth/oauth/v2/token` and all resource endpoints — a bearer token alone is rejected without the client certificate presented at the TLS handshake.
- Generate a CSR, submit it through API Central, and ADP returns a signed certificate; bind the cert + private key (PEM or PKCS12) into your HTTP client's TLS context, not just the Authorization header.
- Token requests are `POST https://accounts.adp.com/auth/oauth/v2/token` with `grant_type=client_credentials`, `client_id`, `client_secret` as form params, over the same mTLS connection; tokens are short-lived (typically ~3600s) so cache and refresh proactively rather than per-call.
- Certificate expiry (commonly 2-year validity) is a frequent silent-failure cause — track expiry dates separately from token TTLs and alert well before renewal is due.

## Core HR/payroll resources

- `GET /hr/v2/workers` and `/hr/v2/workers/{aoid}` return worker profiles keyed by AOID (ADP's persistent worker identifier), not SSN or employee number — resolve and store the AOID as your integration key.
- `POST /payroll/v1/payroll-instructions` submits earnings, deductions, or hours adjustments for an upcoming payroll run; instructions are staged, not immediately applied, and are picked up by the client's next payroll cycle.
- Use `$select`, `$filter`, and pagination (`$top`/`$skip` or cursor-based `nextURL` depending on the version) — full worker collections can be tens of thousands of records for enterprise clients, so unbounded pulls will hit rate limits.
- Field-level payloads follow ADP's HR/payroll schema (workAssignments, payGroup, homeOrganizationalUnits) that is versioned independently per resource — check the resource's schema version before mapping fields to a downstream system.

## Event-driven notifications vs. polling

- ADP supports event subscriptions via the Event Notification API — subscribe to event types like `worker.hire`, `worker.terminate`, `worker.job.change` and receive push notifications to a registered HTTPS endpoint rather than re-polling worker collections.
- Notifications carry the event type and resource reference, not the full payload — your webhook handler must call back into the relevant `GET` endpoint to fetch current state, so treat the notification as a change signal, not a data source.
- Prefer event subscriptions for near-real-time HR sync (new hires, terminations, org changes) and reserve scheduled polling for reconciliation sweeps (e.g., nightly full-population diff) to catch missed or de-duplicated events.
- Webhook endpoints must themselves support mTLS validation of ADP's calling certificate — plan the inbound trust chain with the same rigor as the outbound one.

## Anti-patterns to avoid

- Treating the OAuth bearer token as sufficient auth and skipping mTLS client-certificate binding, which fails silently with generic 401s that look like bad credentials.
- Polling `/hr/v2/workers` on a tight interval as the primary sync mechanism when an event subscription exists for the same use case, burning rate limit and missing near-real-time changes.
- Hardcoding a single AOID-to-employee-ID mapping assumption instead of handling ADP's multi-assignment worker model (one worker, multiple work assignments/positions).
- Letting client certificates expire unnoticed because only OAuth token TTLs are monitored, causing a hard outage that requires a new CSR/approval cycle to resolve.

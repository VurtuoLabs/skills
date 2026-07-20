---
name: sap-odata-integrate
description: "Guides integrating with SAP OData services across classic Gateway/OData V2 and SAP S/4HANA Cloud OData V4, covering auth patterns (basic auth plus CSRF token fetch, and OAuth2), metadata-driven entity discovery, and batch request construction for bulk operations. TRIGGER when: a user asks to call, consume, or debug an SAP OData service (Gateway/OData V2 or S/4HANA Cloud V4 API), needs a CSRF token for a write operation, or wants to build a $batch request against SAP. DO NOT TRIGGER when: the task is SAP ABAP-side development (writing the OData service itself in SEGW/RAP) with no client integration involved, or is about SAP IDoc/BAPI/RFC integration unrelated to OData."
triggers:
  - "sap odata"
  - "csrf token sap"
  - "s/4hana api"
  - "odata batch request"
  - "sap gateway service"
---

# sap-odata-integrate

SAP exposes business data as OData services through two generations — classic Gateway (OData V2, SEGW-generated) and S/4HANA Cloud's API Business Hub services (mostly OData V4) — and each has distinct auth and write-operation quirks that trip up integrations built against generic REST assumptions. This skill frames auth, discovery, and batching for both.

## Auth patterns

- **OData V2 / classic Gateway (on-prem or S/4HANA on-prem)**: typically HTTP Basic Auth (or SAML/principal propagation in enterprise setups) for GET requests, but every state-changing call (POST/PUT/PATCH/DELETE/function import with side effects) requires a CSRF token. Fetch it first with a `GET` to any service entry point (often the service root or `$metadata`) sending header `X-CSRF-Token: Fetch`, capture the returned `X-CSRF-Token` value and the session cookie (`SAP_SESSIONID_*`), then replay both on the write request.
- CSRF tokens are tied to the session cookie jar — if your HTTP client doesn't persist cookies across the fetch-token and write-request calls, the write will fail with a 403 even though the token value itself is correct.
- A `403 CSRF Token Validation Failed` on a call that isn't a fresh token fetch usually means the token expired (session timeout) or a prior write already invalidated it — always re-fetch per logical transaction rather than caching a token long-term.
- **S/4HANA Cloud OData V4 (API Business Hub)**: uses OAuth 2.0, most commonly the client-credentials grant against the SAP Cloud Identity Services / XSUAA token endpoint for system-to-system integration, or authorization-code grant when acting on behalf of a named user. Communication Arrangements (transaction `SOAMANAGER`/Fiori "Communication Management" apps) on the S/4HANA Cloud side provision the OAuth client and scope the exposed services — the integration cannot call anything not explicitly granted via a Communication Scenario.
- OData V4 services generally do not require the CSRF-token dance that V2 does for writes, since OAuth bearer tokens already provide the anti-CSRF guarantee V2's cookie-based session model needed — don't carry the V2 pattern over to V4 integrations unnecessarily.

## Metadata-driven entity discovery

- Every OData service publishes its schema at `<service_root>/$metadata` as an EDMX/XML document listing EntityTypes, their properties (with EDM types and nullable/key flags), EntitySets, NavigationProperties, and (for V2) FunctionImports or (for V4) Actions/Functions — always fetch and parse this before hand-writing queries, since field names rarely match the underlying ABAP structure names exactly.
- Use `$metadata` to determine which properties are `Nullable="false"`/keys (mandatory on create), and which NavigationProperties exist for `$expand` — guessing at expandable associations without checking metadata is a common source of `400 Bad Request` on OData V2 services, which are far stricter about unknown query options than V4.
- The service catalog (`/sap/opu/odata/iwfnd/CATALOGSERVICE;v=2/` on-prem, or the API Business Hub catalog page for S/4HANA Cloud) lists available services and their technical names before you even know the specific `$metadata` URL to hit — start there when the exact service isn't already known.
- For S/4HANA Cloud, cross-check the published API's "release contract" state (released/unreleased) in the API Business Hub — building against an unreleased or version-specific API risks breaking on the next upgrade cycle, since SAP only guarantees compatibility for released, versioned APIs.

## Batch requests for bulk operations

- OData V2 batching uses multipart MIME (`Content-Type: multipart/mixed; boundary=...`) POSTed to `$batch`, with one or more **changesets** (each a nested multipart block, atomic as a unit) grouping related writes, plus optional standalone GET parts outside any changeset — a failure inside a changeset rolls back only that changeset, not the whole batch.
- Each part inside a changeset needs its own CSRF token header matching the session used to fetch it, and needs `Content-Transfer-Encoding: binary` plus a correctly incrementing `Content-ID` if later parts reference earlier ones (e.g., creating a header and its item in one changeset).
- OData V4 batching (used by S/4HANA Cloud) supports the same multipart form but also allows the simpler JSON-based batch format (`Content-Type: application/json` body with a `requests` array, each with `id`, `method`, `url`, `body`, and a `dependsOn` array for ordering) — prefer JSON batch for V4 services that advertise it, since it avoids MIME-boundary construction bugs entirely.
- Batch everything you can when doing bulk create/update against SAP — issuing hundreds of individual POSTs each pays full HTTP + backend-session overhead and is far more likely to hit rate limiting or dialog work-process exhaustion on the SAP side than an equivalent set of requests folded into a handful of `$batch` calls.

## Anti-patterns to avoid

- Fetching a CSRF token once at application startup and reusing it indefinitely across long-running integration processes — sessions expire, and the correct pattern is fetch-token-per-transaction (or at least per session refresh), not a global singleton token.
- Sending OData V2 write payloads with fields not declared in `$metadata`, or omitting required key fields — V2 services reject unknown properties strictly, unlike many REST APIs that silently ignore extras.
- Applying the OData V2 CSRF-fetch pattern to an OAuth-secured S/4HANA Cloud V4 service (or vice versa, trying pure Basic Auth against a Cloud V4 service that only accepts OAuth) — auth model mismatches like this produce confusing 401/403s that look like permissions issues but are actually protocol mismatches.
- Issuing bulk creates/updates as sequential individual calls in a loop instead of grouping them into `$batch` changesets — multiplies round trips and increases the chance of partial-failure states that are hard to reconcile without batch's atomic changeset semantics.

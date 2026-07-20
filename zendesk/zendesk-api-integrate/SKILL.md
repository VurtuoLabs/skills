---
name: zendesk-api-integrate
description: "Integrates with the Zendesk API — authentication (API token vs OAuth), core resources (Tickets, Users, Organizations), building Triggers/Automations for ticket routing, and the incremental export endpoint pattern for syncing ticket data to external systems. TRIGGER when: the user is calling the Zendesk REST API, choosing an auth method for a Zendesk integration, designing ticket-routing logic (Triggers vs. Automations), or building a sync job that pulls tickets/users incrementally. DO NOT TRIGGER when: the task is purely inside the Zendesk Guide/Help Center content editor with no API involved, or is unrelated CRM ticketing on a different platform."
triggers:
  - "zendesk api"
  - "zendesk trigger vs automation"
  - "zendesk incremental export"
  - "zendesk API token"
  - "zendesk ticket sync"
---

# zendesk-api-integrate

The Zendesk REST API exposes the same object model the agent UI operates on (Tickets, Users, Organizations, Groups) and is the basis for both custom integrations and Zendesk's own Trigger/Automation engine. Getting auth, resource semantics, and sync strategy right avoids duplicate syncs and rate-limit churn.

## Authentication

- **API token**: generated in Admin Center → Apps and Integrations → APIs, used as HTTP Basic Auth with username `{email}/token:{api_token}` — simplest for server-to-server scripts and scheduled jobs owned by a single admin identity.
- **OAuth 2.0**: register a client in Admin Center, use the authorization-code grant for anything acting on behalf of an individual agent/end-user (browser-based apps, marketplace apps) — required when the integration must respect per-agent permissions rather than a single service account's.
- Basic auth with an agent's actual password is deprecated/disallowed on most accounts — always use the token form. Every request must also include a valid subdomain host (`https://{subdomain}.zendesk.com/api/v2/...`); cross-subdomain requests simply 404.

## Core resources

- **Tickets** (`/api/v2/tickets`) are the central object: `requester_id`, `assignee_id`, `group_id`, `status` (new/open/pending/hold/solved/closed), `priority`, `type`, and `custom_fields` (an array of `{id, value}` pairs keyed by field ID, not name — fetch `/api/v2/ticket_fields` to resolve IDs per instance). Use side-loading (`?include=users,organizations`) to avoid N+1 calls when fetching related entities alongside a ticket list.
- **Users** (`/api/v2/users`) hold `role` (end-user/agent/admin), `organization_id`, and identities; creating a ticket for a not-yet-known requester can auto-create the user via the `requester` object embedded in the ticket-create payload (suspended/new users land in a "pending" state until they respond).
- **Organizations** (`/api/v2/organizations`) group users for shared visibility and routing (`organization_id` drives "Organization" conditions in Triggers); `shared_tickets`/`shared_comments` flags control cross-org visibility for shared support scenarios.
- Ticket updates support `safe_update` semantics via the `updated_stamp` field to detect concurrent-edit conflicts — pass it back on update to get a 409 instead of silently overwriting another agent's concurrent change.

## Triggers and Automations for routing

- **Triggers** are event-driven (fire immediately on ticket create/update) and evaluate ALL conditions in a single pass against the ticket's state at that moment — use them for immediate routing (e.g., "Subject contains 'billing' → set Group = Billing", "Priority = Urgent AND Tag = vip → notify Slack via target").
- **Automations** are time-based, evaluated hourly against tickets matching their conditions (e.g., "Status = Pending AND Hours since update > 24 → set Status = Open" for stale-ticket nudges) — they cannot fire on ticket creation, only on the recurring time check.
- Order matters: Triggers execute in the admin-defined order and can chain (one trigger's field change can satisfy conditions for a later trigger in the same pass), which is powerful but a common source of unexpected cascades — keep routing logic in as few triggers as possible and use explicit condition checks to prevent unintended re-firing.
- For routing logic too complex for the condition/action UI (e.g., round-robin across dynamic on-call lists), use a Trigger with an "webhook" action calling an external endpoint that then updates the ticket via the API — Zendesk's native actions can't do arbitrary computation.

## Incremental export for syncing

- Use `GET /api/v2/incremental/tickets/cursor.json?start_time={unix_ts}` (cursor-based, the current recommended form) rather than the legacy time-based `start_time`-only endpoint, which suffers from same-second duplicate/skip edge cases at high ticket volume.
- The response includes `after_cursor`/`before_cursor` and `end_of_stream`; persist `after_cursor` after each successful batch and pass it as `cursor=` on the next call — this is the durable checkpoint for a sync job, not a timestamp you compute yourself.
- Poll no more frequently than roughly every 5 minutes when `end_of_stream` is true (catching up to real time) — hammering the endpoint faster just returns empty batches and burns rate-limit budget; back off between polls once caught up.
- The same cursor pattern exists for `/api/v2/incremental/users/cursor.json` and `/api/v2/incremental/organizations/cursor.json` — sync users/orgs before tickets in a fresh migration so foreign-key references (`requester_id`, `organization_id`) resolve on first pass.

## Anti-patterns to avoid

- Matching custom fields by their UI label instead of resolving numeric `field_id` per instance via `/api/v2/ticket_fields` — field IDs are instance-specific and labels can be renamed.
- Using the legacy timestamp-based incremental export instead of the cursor-based endpoint for new integrations — it's prone to missed/duplicate records at second-level collision boundaries.
- Building routing logic that depends on Automations firing immediately on ticket creation — Automations only evaluate on their hourly schedule, so time-sensitive routing must be a Trigger.

---
name: jira-bulk-issue-manage
description: "Bulk creates, updates, and migrates Jira issues via the REST API — selecting issue sets with JQL, using the bulk create/update endpoints, mapping custom field IDs that differ per instance, and handling rate limits/backoff for large migrations. TRIGGER when: the user needs to create or update hundreds/thousands of Jira issues programmatically, migrate issues between projects or instances, script a JQL-driven bulk edit, or is hitting 429s/timeouts during a large Jira data load. DO NOT TRIGGER when: the task is configuring workflow/transition/automation-rule behavior (use jira-workflow-configure) or a one-off single-issue create/edit through the UI."
triggers:
  - "jira bulk create"
  - "jira migration script"
  - "jira REST API custom field"
  - "jira rate limit 429"
  - "JQL bulk update"
---

# jira-bulk-issue-manage

Bulk issue operations in Jira are driven entirely through the REST API (`/rest/api/3/` for Cloud, `/rest/api/2/` for Server/Data Center) since the UI's bulk-edit is capped and not scriptable. Migrations at scale need JQL selection, correct custom-field mapping, and disciplined rate-limit handling to avoid partial failures.

## Selecting issue sets with JQL

- Use `GET /rest/api/3/search` (or the newer `POST /rest/api/3/search/jql` with `nextPageToken` cursor pagination, which is replacing offset-based `startAt` on Cloud) with a JQL string like `project = MIG AND status = "To Do" AND updated <= -30d`, requesting only the `fields` you actually need via the `fields` parameter to cut payload size.
- Cloud enforces a max `maxResults` per page (typically 100); always loop on the pagination token/`isLast` rather than assuming a single page covers the result set — silent truncation is the most common migration bug.
- For deterministic re-runs (idempotent migrations), select on a stable marker field (e.g., a "Migration Batch" label or custom field you set once selected) rather than re-running the same JQL, since issues may change status mid-migration and drop out of the original result set.

## Bulk create and update endpoints

- `POST /rest/api/3/issue/bulk` accepts an `issueUpdates` array (each with `fields`, and optionally `update`) and creates up to the API's per-request cap (historically 50) issues in one call, returning per-item success/failure in the response body — always check the `errors` array per issue rather than trusting a 201 for the whole batch.
- There is no native "bulk update" endpoint equivalent to bulk create; updates are done issue-by-issue via `PUT /rest/api/3/issue/{issueIdOrKey}` (or `POST .../transitions` for status changes), so bulk-update scripts must parallelize with a bounded worker pool rather than looping serially.
- For structural bulk edits (move issues between projects, changing issue type en masse), use the UI-triggered `POST /rest/api/3/bulk/issues/move` (Cloud) or the legacy bulk-move wizard for anything involving issue-type-scheme or workflow-scheme changes, since project moves can force field/workflow remapping that the plain field-update endpoints don't handle.

## Handling custom field IDs

- Every custom field is instance-specific: `customfield_10041` on one Jira site is not the same field on another, even with an identical display name. Never hardcode field IDs across environments — resolve them at runtime via `GET /rest/api/3/field` and match on `name` (and `schema.custom` type) to build a name→ID map before each migration run.
- Multi-select, cascading-select, and user-picker custom fields require specific payload shapes (`{"value": "..."}`, `{"id": "..."}`, or arrays thereof) — inspect `GET /rest/api/3/field/{id}` and a sample issue's `editmeta` (`GET /rest/api/3/issue/{key}/editmeta`) to get the exact schema before writing values, rather than guessing from the UI label.
- When migrating between two Jira instances, build an explicit field-mapping table (source field ID/name → target field ID/name) as a config artifact, not inline in code — it's the first thing that needs updating when re-running against a different target site.

## Rate limits and backoff

- Jira Cloud enforces per-app, per-user rate limits (documented as a token-bucket via `X-RateLimit-*` response headers); a `429` includes a `Retry-After` header — honor it exactly rather than a fixed sleep, and implement exponential backoff with jitter for `5xx` responses.
- Large migrations should throttle proactively (e.g., bounded concurrency of 5-10 in-flight requests) rather than reactively backing off after every batch trips a 429, which wastes quota and slows overall throughput.
- Log a resumable checkpoint (last successfully processed issue key/ID) after every batch so a failed run can resume without re-processing already-migrated issues — critical since bulk create is not idempotent and re-running blindly creates duplicates.

## Anti-patterns to avoid

- Hardcoding `customfield_XXXXX` IDs copied from one Jira site's browser inspector into a script meant to run against another site or environment.
- Looping serial single-issue REST calls for thousands of issues with no concurrency control or checkpointing — slow, and a mid-run failure forces a full restart.
- Retrying on 429 with a fixed short sleep instead of respecting the `Retry-After` header — triggers repeated throttling and can escalate to a temporary IP/app block.

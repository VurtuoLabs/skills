---
name: jira-workflow-configure
description: Configures Jira workflows, statuses, transitions, and automation rules — workflow scheme structure, transition conditions/validators/post-functions, and trigger-condition-action automation for cases like auto-assignment or auto-transitioning issues. TRIGGER when: the user wants to add/edit a status or transition, restrict who can perform a transition, add validation before a transition, chain a workflow scheme to project(s) and issue types, or build a Jira Automation rule (auto-assign, auto-transition, notify, field sync). DO NOT TRIGGER when: the task is bulk-editing existing issues at scale via REST API (use jira-bulk-issue-manage) or is unrelated to workflow/automation configuration (e.g., plain issue creation, JQL search only).
triggers:
  - "jira workflow"
  - "transition condition"
  - "post function"
  - "jira automation rule"
  - "workflow scheme"
---

# jira-workflow-configure

Jira workflows model an issue's lifecycle as a directed graph of statuses and transitions; automation rules layer event-driven logic on top. Getting the scheme structure and rule scoping right avoids issues getting stuck or automation firing on the wrong projects.

## Workflow and workflow scheme structure

- A **workflow** is statuses + transitions (including "global" transitions reachable from any status, and self-transitions). A **status** is scheme-independent and shared across workflows; a **workflow scheme** maps issue types within a project to specific workflows, so "Bug" and "Story" can follow different lifecycles in the same project.
- Statuses belong to a status category (To Do / In Progress / Done) that drives board columns and burndown logic — always map new statuses to the correct category or reports will misclassify progress.
- Editing an active workflow requires either using the inactive "draft" copy-and-publish flow (classic projects) or editing live with migration screens (team-managed/next-gen projects); publishing a changed workflow with issues in a now-removed status forces a manual status-migration mapping step.

## Transition rules: conditions, validators, post-functions

- **Conditions** (e.g., "Only Assignee", "Permission-based", `hasProjectRole`) determine whether the transition is even visible/available to a given user — they run before the user acts and hide the button if unmet.
- **Validators** (e.g., "Field Required", "Field Changed", regex on a field) run after the user submits the transition screen and reject the transition with an error if unmet — use these to enforce data quality (e.g., "Resolution must be set before moving to Done").
- **Post-functions** run after a successful transition, in an ordered chain: default ones (update issue's status field, reindex, fire the `IssueUpdated` event) plus custom ones you append (assign to reporter, copy field value, trigger a webhook). Order matters — a custom post-function reading a field must run after the built-in "update fields" step.
- For Jira Cloud, complex conditions/validators/post-functions beyond the built-ins typically require a Forge/Connect app (e.g., "Jira Suite Utilities" equivalents) since server-side scripting (JQL-based conditions, Groovy post-functions) is a Data Center/Server-only capability via apps like ScriptRunner.

## Building automation rules

- Every rule is **trigger → conditions → actions**, optionally with branches (re-fetch a related set of issues, e.g., "for each sub-task") and smart-value templating (`{{issue.assignee.displayName}}`, `{{triggerIssue.summary}}`).
- Common triggers: "Issue Created", "Issue Transitioned", "Field Value Changed", "Scheduled" (cron-like), "Issue Commented". Scope every rule explicitly to specific projects — global/multi-project rules silently affect more than intended if left unscoped.
- Auto-assign pattern: trigger "Issue Created" → condition "Issue Type = Bug" → action "Assign Issue to → Component Lead" (or round-robin via a Forge action). Auto-transition pattern: trigger "All sub-tasks transitioned" → condition (none needed) → action "Transition Issue → Done" on the parent, since Jira has no native "all children done" trigger — this composite trigger fills that gap.
- Use the **condition** "If/else" block or "Related issues condition" to branch logic instead of writing near-duplicate rules; use "Advanced compare condition" to compare JQL results or smart-value fields directly.
- Rule execution has per-rule and per-site limits (execution count, API-call budget in cloud); a poorly bounded loop (rule A transitions an issue which re-triggers rule A) is auto-detected and disabled by Jira's loop-prevention after a threshold, but chained rules across different rules (A triggers B triggers A) can still create runaway loops undetected — add explicit conditions to break the cycle.

## Anti-patterns to avoid

- Adding validators that reference custom fields by name instead of field ID inside scripted validators — field names change or get duplicated across projects and silently break the rule.
- Leaving an automation rule's scope as "all projects" when it was designed for one team's workflow — causes surprise transitions/assignments elsewhere.
- Chaining post-functions that call external systems (webhooks) synchronously in the transition post-function chain — a slow/failing external call blocks the user's transition; prefer an automation rule action (async) for outbound integration calls instead.

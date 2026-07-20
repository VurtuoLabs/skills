# skills

Claude Code skills for application development, enterprise systems, and related tooling — organized by platform/domain, one subfolder per area, one skill per folder within it.

## Structure

```
skills/
├── salesforce/         # Salesforce/Agentforce (95 skills — see salesforce/README.md)
├── dayforce/            # Dayforce (Ceridian) HCM/payroll
├── workday/              # Workday HCM/Financials
├── excel/                # Microsoft Excel
├── google-sheets/        # Google Sheets
├── jira/                 # Jira
├── servicenow/           # ServiceNow
├── netsuite/              # NetSuite
├── sap/                    # SAP
├── adp/                     # ADP Workforce Now
├── slack/                    # Slack
├── power-platform/            # Power Automate / Power BI
├── zendesk/                    # Zendesk
└── consulting/                  # Client-services scoping, tracking, transitions
```

Each skill folder contains:
- `SKILL.md` (required) — instructions and YAML front matter
- `scripts/`, `references/`, `assets/` (optional) — supporting material

## Install / usage

| Tool | Usage |
|---|---|
| Claude Code, Codex, Cursor, OpenCode, [more](https://agentskills.io/) | `npx skills add VurtuoLabs/skills` |
| Manual | Clone this repo and copy the skill folder(s) you want into your project's `.claude/skills/` (or equivalent) directory |

## Skills

### Salesforce

95 skills (Agentforce, Apex, Flow, LWC, Data Cloud, DevOps, OmniStudio, and more) — one original (`agent-analyzer`), the rest vendored from Salesforce's [forcedotcom/sf-skills](https://github.com/forcedotcom/sf-skills) under Apache-2.0. Full list: [salesforce/README.md](salesforce/README.md).

### Dayforce

- **[dayforce-rest-api-integrate](dayforce/dayforce-rest-api-integrate/SKILL.md)** — Integrate with the Dayforce (Ceridian) RESTful Web Services API for HCM, payroll, and timekeeping data — OAuth2 client-credentials auth, tenant-scoped base URLs, core resource endpoints, cursor-based pagination, and rate-limit handling.
- **[dayforce-payroll-report-generate](dayforce/dayforce-payroll-report-generate/SKILL.md)** — Build and export Dayforce payroll and reporting queries against effective-dated payroll data for reconciliation.

### Workday

- **[workday-rest-integrate](workday/workday-rest-integrate/SKILL.md)** — Integrate with Workday's REST API and Report-as-a-Service (RaaS) for HCM and Financials data — ISU/OAuth2 auth, tenant URL structure, and Workday-specific quirks like WID vs Reference ID.
- **[workday-eib-build](workday/workday-eib-build/SKILL.md)** — Build Workday EIB (Enterprise Interface Builder) inbound/outbound integrations — when to use EIB vs REST/RaaS/Studio, data transformation, and load sequencing.

### Excel

- **[excel-formula-generate](excel/excel-formula-generate/SKILL.md)** — Generate and debug complex Excel formulas, with emphasis on modern dynamic-array functions (XLOOKUP, FILTER, SORT, UNIQUE, LET, LAMBDA) and systematic error tracing.
- **[excel-vba-automate](excel/excel-vba-automate/SKILL.md)** — Write and review VBA macros for Excel automation, covering the object model, event-driven procedures, and error handling.
- **[excel-power-query-build](excel/excel-power-query-build/SKILL.md)** — Build Power Query (M language) transformations for Excel data models, covering query folding and refreshable external connections.
- **[excel-dashboard-build](excel/excel-dashboard-build/SKILL.md)** — Build interactive Excel dashboards with PivotTables, slicers, chart selection, and performance tuning for large workbooks.

### Google Sheets

- **[sheets-apps-script-generate](google-sheets/sheets-apps-script-generate/SKILL.md)** — Write Google Apps Script to automate Sheets — custom functions, triggers, SpreadsheetApp manipulation, and external API calls via UrlFetchApp.

### Jira

- **[jira-workflow-configure](jira/jira-workflow-configure/SKILL.md)** — Configure Jira workflows, statuses, transitions, and automation rules.
- **[jira-bulk-issue-manage](jira/jira-bulk-issue-manage/SKILL.md)** — Bulk create, update, and migrate Jira issues via the REST API using JQL, the bulk endpoints, and rate-limit handling.

### ServiceNow

- **[servicenow-flow-generate](servicenow/servicenow-flow-generate/SKILL.md)** — Build ServiceNow Flow Designer flows and subflows — trigger selection, actions vs. subflows, and data pill wiring.
- **[servicenow-script-generate](servicenow/servicenow-script-generate/SKILL.md)** — Write ServiceNow server-side/client-side scripts — Script Includes, Business Rules, Client Scripts, and GlideRecord/GlideAjax patterns.

### NetSuite

- **[netsuite-suitescript-generate](netsuite/netsuite-suitescript-generate/SKILL.md)** — Write NetSuite SuiteScript 2.x — script-type selection, N/record and N/search modules, and governance/usage-unit limits.

### SAP

- **[sap-odata-integrate](sap/sap-odata-integrate/SKILL.md)** — Integrate with SAP OData services (Gateway/OData V2 and S/4HANA Cloud V4) — auth patterns, metadata-driven entity discovery, and batch requests.

### ADP

- **[adp-workforce-now-integrate](adp/adp-workforce-now-integrate/SKILL.md)** — Integrate with ADP Workforce Now — OAuth2 + mutual TLS auth, common HR/payroll endpoints, and event subscriptions vs. polling.

### Slack

- **[slack-workflow-build](slack/slack-workflow-build/SKILL.md)** — Build Slack workflows, slash commands, and bot automations with the Bolt framework, plus Workflow Builder vs. custom app guidance.

### Power Platform

- **[power-automate-flow-build](power-platform/power-automate-flow-build/SKILL.md)** — Build Power Automate cloud flows — trigger types, connector licensing, control patterns, and error handling.
- **[power-bi-report-generate](power-platform/power-bi-report-generate/SKILL.md)** — Build Power BI reports and data models — star schema, DAX measures vs. calculated columns, and performance tuning.

### Zendesk

- **[zendesk-api-integrate](zendesk/zendesk-api-integrate/SKILL.md)** — Integrate with the Zendesk API — auth, core resources, Triggers/Automations for ticket routing, and incremental export for syncing.

### Consulting

Client-services skills for scoping, tracking, and transitioning engagements — platform-agnostic. Full list: [consulting/README.md](consulting/README.md).

- **[discovery-call-prep](consulting/discovery-call-prep/SKILL.md)** — Prepares a structured discovery call agenda and question list for a new client engagement.
- **[proposal-scope-estimate](consulting/proposal-scope-estimate/SKILL.md)** — Turns discovery/requirements notes into a scoped proposal with effort estimates.
- **[sow-draft-generate](consulting/sow-draft-generate/SKILL.md)** — Drafts a Statement of Work from discovery notes or a requirements doc.
- **[change-order-draft](consulting/change-order-draft/SKILL.md)** — Drafts a change order when scope shifts mid-engagement.
- **[meeting-notes-action-extract](consulting/meeting-notes-action-extract/SKILL.md)** — Converts raw meeting notes/transcripts into decisions and owned, dated action items.
- **[status-report-generate](consulting/status-report-generate/SKILL.md)** — Generates a client-facing status report from raw internal activity.
- **[risk-register-track](consulting/risk-register-track/SKILL.md)** — Maintains a project risk register and flags stale or unowned entries.
- **[client-context-switch](consulting/client-context-switch/SKILL.md)** — Reconstructs a compact briefing for a specific client when switching back to it among multiple concurrent engagements.
- **[handoff-doc-generate](consulting/handoff-doc-generate/SKILL.md)** — Produces a project handoff/knowledge-transfer doc when rolling off or transitioning an engagement.
- **[engagement-retro-facilitate](consulting/engagement-retro-facilitate/SKILL.md)** — Runs a structured end-of-engagement retrospective and converts it into action items.

## License

Original content is licensed under [LICENSE](LICENSE) (MIT). Vendored Salesforce skills are licensed under Apache License 2.0 — see [salesforce/THIRD_PARTY_NOTICES.md](salesforce/THIRD_PARTY_NOTICES.md).

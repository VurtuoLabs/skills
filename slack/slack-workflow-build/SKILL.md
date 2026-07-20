---
name: slack-workflow-build
description: "Guides building Slack automations — the Bolt framework's event subscription, slash command, and interactivity/shortcut handlers; when to reach for no-code Workflow Builder versus a custom app/bot; and how to pick the right OAuth scopes and token type (bot vs user token) for a given feature. TRIGGER when: a user is building a Slack bot, slash command, workflow step, or interactive message; asks about Bolt (JS/Python/Java) event handling; is choosing between Workflow Builder and a custom app; or is debugging Slack OAuth scopes/token errors. DO NOT TRIGGER when: the task is generic Slack channel/workspace administration with no API or automation involved, or the user is asking about a different chat platform (Teams, Discord) despite superficial similarity."
triggers:
  - "Slack Bolt framework"
  - "Slack slash command"
  - "Slack Workflow Builder vs bot"
  - "Slack bot vs user token scopes"
---

# slack-workflow-build

Slack automation spans a spectrum from no-code Workflow Builder steps to fully custom Bolt apps, and picking the wrong end of that spectrum for a given use case creates either a brittle workflow or an over-engineered bot.

## Bolt framework basics

- Bolt (available for JavaScript, Python, and Java) wraps Slack's Events API, Web API, and Socket Mode into a single app object with `app.event()`, `app.command()`, `app.action()`, and `app.shortcut()` listeners — each maps to a distinct Slack subscription type configured in the app manifest.
- Event subscriptions (`app.event('app_mention')`, `app.event('message')`) require a public HTTPS Request URL for verification unless you use Socket Mode, which opens a WebSocket and avoids exposing an endpoint — favor Socket Mode for internal tools and dev environments, HTTP mode for production apps with existing infra.
- Slash commands are registered per-command in the app config (name, description, usage hint) and delivered to `app.command('/mycommand')`; always `ack()` within 3 seconds and do slow work asynchronously, or Slack will show the command as failed.
- Interactivity (button clicks, modals, select menus) and shortcuts (global or message shortcuts) both flow through the Interactivity & Shortcuts request URL — handle them with `app.action(action_id)` and `app.shortcut(callback_id)`, and use `client.views_open()` to trigger modals within the 3-second ack window using the provided `trigger_id`.

## Workflow Builder vs. custom app/bot

- Workflow Builder (including its 2023+ "workflow app" steps that call external HTTP endpoints) fits linear, form-driven processes triggered by a shortcut, scheduled time, or channel event — approvals, intake forms, standardized announcements — with no code beyond an optional webhook step.
- Reach for a custom Bolt app when logic needs branching beyond simple conditionals, external API calls with response parsing, persistent state across interactions, or dynamic UI (modals whose fields depend on prior answers) — Workflow Builder's steps are not expressive enough for these.
- A hybrid is common: Workflow Builder handles the trigger and form UI, then calls a custom "workflow step from app" or webhook endpoint (built with Bolt) for the business logic, giving non-engineers a maintainable front end over real code.
- Workflow Builder workflows are workspace-local and edited by non-developers in the Slack UI; custom apps are version-controlled, deployable, and testable — factor in who maintains it long-term, not just initial build effort.

## OAuth scopes and token types

- Bot tokens (`xoxb-`) act as the app's own identity, installed once per workspace, and are the default for anything the app itself should do (post messages, read channels it's in, respond to commands) — scopes are granted at install time via the OAuth & Permissions page.
- User tokens (`xoxp-`) act on behalf of the installing/authorizing user, needed when the action must be attributed to a human (posting "as" a user, accessing user's private search, admin-level actions bot tokens can't perform) — request user scopes separately from bot scopes in the manifest.
- Common bot scopes: `chat:write` (post as bot), `commands` (slash commands), `channels:history`/`groups:history` (read messages), `users:read` (lookup); grant the minimum needed — `chat:write.public` avoids requiring the bot be invited to every channel it posts in.
- Token rotation matters for long-lived apps: Slack supports token rotation with refresh tokens for apps enabling the "token rotation" opt-in — plan for `xoxe.xoxb-` rotating token formats if building for the app directory rather than assuming a static bot token forever.

## Anti-patterns to avoid

- Doing slow work (API calls, DB writes) before calling `ack()` in a command or action handler, causing Slack to mark the interaction as timed out even though it eventually succeeds.
- Requesting broad scopes like `channels:history` workspace-wide when the feature only needs `chat:write` to post into channels it's explicitly added to.
- Building a full custom Bolt app for a simple linear approval flow that Workflow Builder's native "Approvals" step already covers, adding unnecessary hosting and maintenance burden.
- Mixing up bot and user token in API calls — e.g., using a user token for automated posting, which breaks if that user is deprovisioned or revokes authorization.

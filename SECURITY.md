# Security

Skills for application development across Salesforce and other platforms.

## Reporting a vulnerability

Report security issues privately to **aimperiale@vurtuolabs.com**. Do not open a public
issue for anything you believe is exploitable.

Include the version or commit you tested, the org edition and configuration if relevant,
what you observed, and the smallest set of steps that reproduces it. A proof of concept is
welcome but not required.

What to expect:

| Stage | Target |
|---|---|
| Acknowledgement that the report was received | 3 working days |
| Initial assessment, including whether it is accepted | 10 working days |
| Fix or documented mitigation for an accepted issue | 30 days, sooner where severity warrants |

We will tell you which way the assessment went either way. If a report is not accepted you
will get the reasoning, not silence. Credit is offered on any accepted report unless you ask
us not to.

## Supported versions

Security fixes land on the default branch. There are no long-lived release branches and no
backports to older commits, so the supported version is the current `main`.

## What this repository is, and what that means for risk

This repository is a library of skills: instructions, reference documentation and
example assets that guide tooling. The Apex files it contains are teaching examples and
templates inside skill assets. They are illustrations of a pattern, not a deployable
application, and they are not installed into an org by using this repository.

## Threat model

- Skill instructions are executed by tooling on your behalf. A malicious or careless change to a skill can cause a tool to take actions you did not intend, including against a connected org.
- Example Apex in skill assets is illustrative. Some examples deliberately show an anti-pattern in order to explain the fix, so example code must never be copied into production without review.
- Scripts shipped alongside skills may read local Salesforce CLI credentials in order to query an org. They do not transmit them anywhere, but you should read any script before running it.

## Secrets

No API keys, tokens, passwords, certificates or org credentials are committed here.
Examples that need a credential use an obvious placeholder. If you find a real one,
treat it as a live incident and report it to the address above rather than opening an
issue.

## What this repository deliberately does not do

- It does not deploy anything to an org by itself.
- It does not store or transmit org credentials.
- It does not collect telemetry.

## Using this content safely

- Read a skill before invoking it, especially one that writes to an org.
- Treat example Apex as illustration, not as production-ready code.
- Pin to a commit when using these skills in automation.
- Run org-touching skills against a sandbox or scratch org first.

## License and warranty

Released under the MIT License. It is provided without warranty of any kind, including
any warranty of security or fitness for a particular purpose. See [LICENSE](LICENSE).

Copyright (c) 2026 VurtuoLabs

# validate-script-agent — Feature Parity Validation

A Claude Code **skill** that validates behavioral parity between a **Legacy Agentforce agent** (the proven baseline) and a **Script agent** (its AgentScript migration). It drives paired multi-turn `sf agent preview` sessions against both agents, collects transcripts, and runs LLM-based semantic evaluation across 3 behavioral dimensions to produce a PASS/FAIL parity report — CSV and interactive HTML — so a team migrating an agent from classic Agentforce authoring to AgentScript can confirm the new agent behaves the same way before cutting over.

> **Scope.** This skill validates that a migrated agent matches the legacy agent's behavior on a fixed set of test conversations. For declarative regression suites (`AiEvaluationDefinition`), use the `testing-agentforce` skill instead. For production session-trace analysis, use `observing-agentforce` instead.

---

## Listing Metadata

- **Industries:** Cross-industry
- **Horizontal Product:** Developer Tools
- **Business Need:** Agentforce migration QA — validating behavioral parity between a legacy Agentforce agent and its AgentScript migration
- **Requires:** Salesforce CLI (`sf`) with the Agentforce plugin; Claude Code
- **Compatible With:** Agentforce (Employee Agents, classic and Agent Script)
- **Salesforce Editions:** Any edition with Agentforce enabled

**App Details**
- Version: tracked via git history (no separate release versioning)
- Package Contents: not applicable — pure Python + Claude Code skill definition, no Salesforce metadata package
- Languages: English

**Security:** Not applicable — distributed as a Claude Code skill in this repo, not listed on AppExchange. See the root README's [Security & what not to commit](../README.md#security--what-not-to-commit) section.

## Architecture

This is not a standalone app — it is a **Claude Code skill**: a `SKILL.md` playbook that Claude Code reads and executes step-by-step, orchestrating small single-purpose Python scripts and its own sub-agents. There is no server, database, or long-running process; everything runs as CLI invocations for the duration of one validation pass.

```
                     ┌─────────────────────────────┐
                     │   Claude Code (orchestrator)  │
                     │   reads SKILL.md, drives the  │
                     │   pipeline step by step       │
                     └───────────────┬───────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        │ Step 2                      │ Step 3                      │ Step 6
        ▼                             ▼                              ▼
┌───────────────────┐      ┌───────────────────────┐      ┌───────────────────┐
│  run_preview.py     │      │  prep_eval_batches.py  │      │  build_report.py    │
│  drives paired       │      │  splits session JSON   │      │  merges verdicts,    │
│  `sf agent preview`  │      │  into batch_NN.json     │      │  writes CSV + HTML   │
│  sessions (Legacy    │─────▶│  files for parallel     │      │  report              │
│  then Script)        │      │  LLM evaluation          │      │                     │
│  → writes            │      └───────────┬────────────┘      └─────────▲───────────┘
│  <session>.json       │                  │                              │
└──────────┬───────────┘                  │ Step 4                       │ Step 5
           │                               ▼                              │
           │                    ┌────────────────────────┐    ┌─────────┴──────────┐
           │                    │ N parallel Claude Code    │    │ merge_verdicts.py    │
           │                    │ sub-agents, each reading   │───▶│ folds verdicts_NN     │
           │                    │ assets/eval_prompt.md +    │    │ back into per-session  │
           │                    │ one batch_NN.json, writing │    │ JSON, computes overall │
           │                    │ verdicts_NN.json            │    │ parity                │
           │                    └────────────────────────┘    └────────────────────┘
           │
           ▼
   sf agent preview (Salesforce CLI)
   ├── Legacy agent  — published Bot, --api-name        (ground truth)
   └── Script agent  — AiAuthoringBundle, --authoring-bundle + action mode
```

Data flow, concretely:

1. **`columns.py`** validates the input CSV has the fixed 7-column schema (imported by `run_preview.py`, not run standalone).
2. **`run_preview.py`** reads the CSV, groups rows into multi-turn sessions, and for each session shells out to `sf agent preview start/send/end` — first against the Legacy agent, then against the Script agent with the same utterances — writing one `<session_number>.json` transcript file per session.
3. **`prep_eval_batches.py`** reads all session JSON files and splits them into `batch_NN.json` files (default batch size 5) pairing Legacy and Script transcripts for LLM review.
4. Claude Code dispatches **one sub-agent per batch, in parallel**, each given the canonical rubric in `assets/eval_prompt.md` verbatim, reading its `batch_NN.json` and writing a `verdicts_NN.json` with PASS/FAIL + reason per dimension per session.
5. **`merge_verdicts.py`** reads all `verdicts_NN.json` files, folds the 3-dimension verdicts back into each session's JSON file, computes `overall_parity`, and exits non-zero listing any session that never got a verdict (so the orchestrator can re-dispatch that batch).
6. **`build_report.py`** reads the now-enriched session JSON files and produces `<name>_results.csv` (tabular) and `<name>_report.html` (self-contained interactive viewer with filter/sort/accordion transcript view).

All PASS/FAIL judgment is made by LLM sub-agents using semantic comparison — the Python scripts never make a correctness judgment themselves; they only orchestrate, validate schema, batch data, merge results, and render output.

---

## Features / Capabilities

- **Paired multi-turn session capture** against both a published Legacy agent (`--api-name`) and a Script agent authoring bundle (`--authoring-bundle`), reusing the exact same session across all turns (start once → send N utterances → end once) so conversational context is preserved on both sides.
- **Legacy-as-ground-truth semantics** — the Legacy agent's behavior is never scored or penalized; only the Script agent is judged against it.
- **3-dimension LLM evaluation** — Response Quality, Data Handling, Error Handling — each independently PASS/FAIL with a human-readable reason, computed via Claude Code sub-agents (not deterministic string comparison).
- **Overall parity rollup** — a session is PASS only if all 3 dimensions pass.
- **Resumable, partial re-run support** — `run_preview.py` skips sessions whose JSON already exists; `--only-sessions` lets you target specific session numbers to re-run failures without re-running the whole suite.
- **Resilience** — exponential backoff (max 3 retries) on rate-limit errors (`ConcurrentPerOrgLongTxn`, `REQUEST_LIMIT_EXCEEDED`, HTTP 429, `Too Many Requests`, `TotalRequests Limit exceeded`), a 240-second subprocess timeout per CLI call, guaranteed session cleanup via `try/finally` (no orphaned preview sessions), and continue-on-error handling so one failed session doesn't abort the batch.
- **Dual output** — a CSV for programmatic/spreadsheet use and a single self-contained HTML file (no external dependencies, no build step) with a summary bar, PASS/FAIL filter buttons per dimension, sortable columns, and expandable per-session accordions showing side-by-side Legacy vs. Script transcripts and evaluation reasons. Filter/sort state persists in the browser via `localStorage`.
- **Fixed, validated CSV schema** — `columns.py` checks for all 7 required columns (case/space-insensitive) before any CLI calls are made, failing fast with a clear error listing what's missing.

---

## Prerequisites

| Requirement | Version / detail | Why |
|---|---|---|
| **Salesforce CLI (`sf`)** | 2.138+ (script confirms via `sf agent preview --help` must list `start`, `send`, `end`) | Drives the actual agent preview sessions |
| **`@salesforce/plugin-agent`** | latest (installed via `sf plugins install` if `sf agent preview` is missing) | Provides the `sf agent preview` subcommand |
| **Python** | 3.8+, standard library only — no `pip install`, no `requirements.txt` | Runs all 5 pipeline scripts |
| **Salesforce org** | Authenticated, with BOTH agents present: Legacy agent published + activated; Script agent's `AiAuthoringBundle` deployed | Target of every `sf agent preview` call |
| **Salesforce project directory** | Must contain `sfdx-project.json` in the CLI's working directory | `sf agent preview` refuses to run without one (`RequiresProjectError`) |
| **Claude Code** | Any recent version, with skills enabled | Loads and executes `SKILL.md`, dispatches evaluation sub-agents |

There is no `package.json`, `requirements.txt`, or `pyproject.toml` in this repository — the Python scripts use only the standard library (`argparse`, `csv`, `json`, `os`, `random`, `re`, `subprocess`, `time`, `glob`, `html`, `sys`, `collections`).

---

## Installation / Setup

1. **Install the Salesforce CLI and agent plugin:**
   ```bash
   npm install --global @salesforce/cli
   sf --version
   sf agent preview --help    # must list: start, send, end
   ```
   If `sf agent preview` is missing: `sf update` or `sf plugins install @salesforce/plugin-agent`.

2. **Authenticate to the org that has both agents:**
   ```bash
   sf org login web --alias my-sandbox --instance-url https://test.salesforce.com
   sf org list
   ```

3. **Install this skill** so Claude Code can discover it — place (or symlink) this folder under `.claude/skills/validate-script-agent/` in your project, or `~/.claude/skills/validate-script-agent/` for a user-wide install.

4. **Create a Salesforce project directory to run from**, since `sf agent preview` requires `sfdx-project.json` in the current working directory. If running from the skill directory itself, create one:
   ```json
   {
     "packageDirectories": [{"path": "force-app", "default": true}],
     "sourceApiVersion": "65.0"
   }
   ```
   Also ensure `force-app/main/default/` exists.

5. **Retrieve the Script agent's authoring bundle locally** (required for `--authoring-bundle` to resolve):
   ```bash
   sf project retrieve start --metadata "AiAuthoringBundle:<BundleName>" --target-org <alias>
   ls force-app/main/default/aiAuthoringBundles/<BundleName>/
   ```

6. **(Employee Agents only) Verify the CLI isn't hit by a known bug** — see [Troubleshooting](#troubleshooting) below before your first real run.

No build step, no compiled artifacts, no service to deploy — this "installs" by being present on disk where Claude Code can see it.

---

## Configuration

There are no environment variables, `.env` files, or standalone config files consumed by this skill's own code. Configuration is entirely:

- **The input CSV** (session/turn/agent/org/action-mode data — see [CSV Format](#csv-format)).
- **CLI flags** passed to the Python scripts (see [Usage](#usage) and the flag tables below).
- **`.claude/settings.json` permission pre-approvals** (optional, reduces prompt friction) — this skill needs Bash execution (`sf` and `python3` calls), file read/write (CSV in, session JSON, CSV/HTML reports out), and sub-agent dispatch (parallel LLM evaluators):
  ```json
  {
    "permissions": {
      "allow": [
        "Bash(python3 *)",
        "Bash(sf agent preview *)",
        "Bash(sf org *)",
        "Bash(sf project retrieve *)"
      ]
    }
  }
  ```

One internal env var is set programmatically (not user-configured): `run_preview.py` sets `SF_DISABLE_LOG_FILE=true` on the subprocess environment for every `sf` call, to suppress CLI log-file noise.

`assets/columns.example.json` documents the fixed CSV schema for reference only — it is not read by any script at runtime.

---

## Usage

Invoke the skill from within Claude Code:

```
/validate-script-agent --csv-path ./sessions.csv
```

Claude Code will then:
1. Confirm scope with you (and offer a smoke test on 1-2 sessions first).
2. Run `scripts/run_preview.py` to capture paired transcripts (Legacy first, then Script) for each session.
3. Run `scripts/prep_eval_batches.py` to split sessions into batches, then dispatch one parallel sub-agent per batch using `assets/eval_prompt.md`.
4. Run `scripts/merge_verdicts.py` to fold verdicts back into session data.
5. Run `scripts/build_report.py` to produce the CSV + HTML report and open it.

### Equivalent manual pipeline (what the skill runs under the hood)

```bash
# Step 2 — capture paired sessions (resumable; add --only-sessions 1,2 for a smoke test)
python3 scripts/run_preview.py --csv ./sessions.csv --outdir "$DATA"

# Step 3 — split into batches for parallel LLM evaluation
python3 scripts/prep_eval_batches.py --datadir "$DATA" --evaldir "$EVAL" --batch-size 5

# Step 4 — (performed by Claude Code sub-agents, not a script)
#   one sub-agent per batch_NN.json, using assets/eval_prompt.md verbatim,
#   writes verdicts_NN.json into $EVAL

# Step 5 — merge verdicts back into session data
python3 scripts/merge_verdicts.py --datadir "$DATA" --evaldir "$EVAL"

# Step 6 — build the enriched CSV + interactive HTML report
python3 scripts/build_report.py --datadir "$DATA" --outdir ./reports --name parity_run1

# Step 7 — open the report
open ./reports/parity_run1_report.html
```

### Re-running just the failures (Step 8)

```bash
FAILS=$(python3 -c "import json,glob;print(','.join(str(json.load(open(p))['session']) for p in glob.glob('$DATA/*.json') if json.load(open(p)).get('overall_parity')=='FAIL'))")

python3 scripts/run_preview.py --csv ./sessions.csv --outdir "$DATA" --only-sessions "$FAILS"
# then re-run Steps 3–6 above
```

### Script CLI flag reference

| Script | Flags |
|---|---|
| `run_preview.py` | `--csv` (required), `--outdir` (required), `--only-sessions` (comma-separated session numbers, default: all) |
| `prep_eval_batches.py` | `--datadir` (required), `--evaldir` (required), `--batch-size` (default `5`), `--only-sessions` (default: all) |
| `merge_verdicts.py` | `--datadir` (required), `--evaldir` (required) |
| `build_report.py` | `--datadir` (required), `--outdir` (required), `--name` (default `parity`) |
| `columns.py` | Not a CLI entry point — imported by `run_preview.py` to validate CSV headers |

### CSV Format

Fixed schema — 7 columns required (case/space-insensitive matching):

```csv
Session_Number,Turn_Order,User_Utterance,Legacy_Agent_Name,Script_Agent_Bundle,Target_Org,Action_Mode
1,1,"Hi, I need help booking a room",Resort_Manager,Resort_Manager_Bundle,my-dev-org,simulate-actions
1,2,"I'd like a suite for July 15-17",Resort_Manager,Resort_Manager_Bundle,my-dev-org,simulate-actions
2,1,"What's your cancellation policy?",Resort_Manager,Resort_Manager_Bundle,my-dev-org,simulate-actions
```

| Column | Description |
|---|---|
| `Session_Number` | Groups rows into multi-turn conversations (same number = same session) |
| `Turn_Order` | Utterance sequence within a session (1, 2, 3...) |
| `User_Utterance` | Message sent to both agents |
| `Legacy_Agent_Name` | Published agent API name (Bot DeveloperName), used with `--api-name` |
| `Script_Agent_Bundle` | AiAuthoringBundle name, used with `--authoring-bundle` |
| `Target_Org` | Salesforce org alias |
| `Action_Mode` | `use-live-actions` or `simulate-actions` (Script agent only — Legacy never passes an action-mode flag) |

All rows within a session must share the same `Legacy_Agent_Name`, `Script_Agent_Bundle`, `Target_Org`, and `Action_Mode`.

### Output

- `./reports/parity_results.csv` — tabular data for programmatic use
- `./reports/parity_report.html` — interactive single-file viewer (open in any browser)

---

## Consuming the Report

### CSV (`<name>_results.csv`)

Each row is one session with columns:

| Column | Description |
|---|---|
| `Session_Number` | Session identifier |
| `Legacy_Agent` / `Script_Bundle` | Agent names |
| `Org` | Target org alias |
| `Turns` | Number of turns in the session |
| `Response Quality Result` / `Response Quality Reason` | PASS / FAIL / N/A + LLM explanation |
| `Data Handling Result` / `Data Handling Reason` | PASS / FAIL / N/A + LLM explanation |
| `Error Handling Result` / `Error Handling Reason` | PASS / FAIL / N/A + LLM explanation |
| `Overall Parity` | PASS only if all 3 dimensions pass |
| `Legacy Transcript` / `Script Transcript` | Full JSON turn arrays |
| `Legacy Error` / `Script Error` | Error messages (if any) |

### Interactive HTML (`<name>_report.html`)

Open in any browser:

```bash
open ./reports/parity_report.html
```

Features:
- **Summary bar** — pass/fail counts per dimension at a glance
- **Filter buttons** — show only PASS or FAIL sessions by any dimension
- **Sortable columns** — click headers to sort by session, turns, or any verdict
- **Expandable rows** — click a session to see side-by-side transcripts (Legacy vs Script) and evaluation reasons per dimension
- **Self-contained** — single HTML file with no external dependencies (no CDN, no build step); share via Slack/email directly. Filter and sort state is remembered per report via browser `localStorage`.

### Interpreting Results

Overall Parity = **PASS** only if ALL 3 dimensions pass for that session. A single dimension failing means the Script agent diverged from Legacy behavior in a meaningful way — check the reason column for specifics.

---

## 3 Evaluation Dimensions

| Dimension | PASS means |
|---|---|
| **Response Quality** | Script produced a substantively equivalent response (different wording, formatting, or added non-contradictory context is fine; different information, omitted critical details, or wrong values is not) |
| **Data Handling** | Script referenced the same records/values/counts as Legacy (same names, IDs, numbers, dates); PASS by default if neither agent's response contains data references |
| **Error Handling** | Script handled edge cases and conversation flow the same way Legacy did (both succeed, both ask for clarification, etc.); PASS by default if the session has no error/edge-case scenario |

**Overall parity**: PASS only if ALL 3 dimensions pass.

The exact rubric text — including the required JSON verdict schema (`{"session": N, "response_quality_result": "PASS|FAIL", "response_quality_reason": "...", ...}`) — lives in `assets/eval_prompt.md` and is used verbatim by every evaluation sub-agent; it is not paraphrased at dispatch time.

---

## How it works

- **Legacy = ground truth.** The Legacy agent's responses are always treated as correct. The LLM evaluates whether the Script agent matches.
- **Multi-turn sessions.** Sessions stay open between turns (start once → send N utterances → end once). Legacy runs first to establish baseline, then Script runs the same conversation.
- **LLM evaluation.** All PASS/FAIL judgments come from Claude Code sub-agents using `assets/eval_prompt.md`. 3 dimensions: Response Quality, Data Handling, Error Handling. The Python scripts only prepare batches and file verdicts — they make no judgment themselves.
- **Dual output.** `build_report.py` produces both a CSV (for programmatic use) and an interactive HTML report (for visual review). The HTML is a self-contained single file with no external dependencies.
- **Guaranteed cleanup.** Both sessions are ended in `finally` blocks — no orphaned preview sessions.
- **Sequential, not concurrent, session execution.** Sessions run one after another (Legacy CLI call, then Script CLI call, then next session) — there is no cross-session parallelism in `run_preview.py`, only cross-batch parallelism at the LLM-evaluation step.

---

## Project structure

```
Agent Analyzer/                      # skill root (a.k.a. validate-script-agent)
├── SKILL.md                         # skill definition — the step-by-step workflow Claude Code loads and executes
├── README.md                        # this file
├── .gitignore                       # standard Python .gitignore + Salesforce project artifacts (.sfdx/, .sf/, force-app/, sfdx-project.json, *.csv) + .claude/settings.local.json
├── scripts/
│   ├── columns.py                   # fixed 7-column CSV schema + case/space-insensitive validator (imported, not run directly)
│   ├── run_preview.py               # drives paired multi-turn `sf agent preview` sessions (Legacy then Script); resumable; writes <session>.json
│   ├── prep_eval_batches.py         # splits session JSON into batch_NN.json files for parallel LLM evaluation sub-agents
│   ├── merge_verdicts.py            # folds verdicts_NN.json (3-dimension PASS/FAIL) back into session JSON; computes overall_parity
│   └── build_report.py              # canonical report builder — produces <name>_results.csv and <name>_report.html
└── assets/
    ├── eval_prompt.md               # canonical LLM feature-parity evaluation rubric, used verbatim by every evaluation sub-agent
    └── columns.example.json         # reference documentation of the fixed CSV schema (not read at runtime)
```

---

## Testing

No automated test suite currently exists in this repository — there are no `test_*.py` files, no `tests/` directory, no `pytest`/`unittest` configuration, and no CI/CD pipeline (no `.github/workflows/` or equivalent). Validation of the pipeline itself is done manually by running a smoke test against 1-2 real sessions (`--only-sessions 1,2`) before running a full suite, as recommended in Step 1 of `SKILL.md`.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `sf agent preview` not found | `sf update` or `sf plugins install @salesforce/plugin-agent` |
| `AABNotFound` for Script agent | Retrieve with `--metadata AiAuthoringBundle:<name>` |
| Legacy agent won't preview | Ensure it's published AND activated |
| `Invalid user ID provided on start session` | Known CLI bug for Employee Agents — see workaround below |
| Rate limit errors (`ConcurrentPerOrgLongTxn`, `REQUEST_LIMIT_EXCEEDED`, 429) | Lower concurrency or wait between sessions — the script already retries with exponential backoff (max 3 attempts) but sustained limits need a longer pause |
| CSV column error | Ensure exact column names match (case-insensitive) — `columns.py` will list which required column(s) are missing |
| `RequiresProjectError` | Run from a directory with `sfdx-project.json` |
| Empty responses in JSON | Verify CLI version is 2.138+ (`sf update`) |
| `merge_verdicts.py` exits non-zero | It printed the list of sessions missing a verdict — re-dispatch those batches, then re-run merge |

### Employee Agent Preview Workaround

`sf agent preview start --api-name` fails for Employee Agents with `"Invalid user ID provided on start session"`. This is a known bug in `@salesforce/cli` (confirmed through v2.139.6) — the CLI sends `bypassUser: true` but Employee Agents require `bypassUser: false` (they run as the current user, not a configured Agent User).

**Fix:** Patch `~/.local/share/sf/client/<version>/node_modules/@salesforce/agents/lib/agents/productionAgent.js` in the `startPreview()` method. Replace the hardcoded `bypassUser: true` with:

```javascript
const metadata = await this.getBotMetadata();
const isEmployeeAgent = metadata.AgentType === 'AgentforceEmployeeAgent';
const hasNoAgentUser = !metadata.BotUserId;
// in body:
bypassUser: !(isEmployeeAgent || hasNoAgentUser),
```

This patch is overwritten on `sf update` — reapply after upgrading until the bug is fixed upstream.

---

## Limitations

> **Custom Lightning Types not supported.** This tool does not support Agent Interactions that use Custom Lightning Types (CLTs) for input/output action overrides. Actions configured with CLT-based structured input or output schemas cannot be exercised through `sf agent preview`. Validate those flows manually or via direct API invocation / in-app testing.

---

## Contributing

This is a small internal tool with no formal contribution process, issue tracker, or PR template in this repository. If you're changing it:

- Keep the CSV schema in `scripts/columns.py`, `assets/columns.example.json`, and both `README.md`/`SKILL.md` in sync if you ever change required columns.
- `assets/eval_prompt.md` is used verbatim by evaluation sub-agents — if you edit the rubric, keep the required JSON verdict shape (`session`, `<dimension>_result`, `<dimension>_reason` for `response_quality`, `data_handling`, `error_handling`) in sync with what `merge_verdicts.py` and `build_report.py` expect.
- `build_report.py` is the canonical report builder — avoid hand-generating or post-editing CSV/HTML output outside of it.
- Since there's no test suite, manually smoke-test any script change against a small (1-2 session) CSV before relying on it for a full run.

---

## License

MIT License — see [LICENSE](LICENSE).

---

## Requirements (summary)

- **Salesforce CLI** (`sf`) 2.138+ with `sf agent preview` (`start`, `send`, `end`)
- **Python 3.8+** (standard library only — no dependency manifest, no `pip install`)
- **An authenticated Agentforce 2.0 org** with both agents deployed (Legacy published+activated, Script's AiAuthoringBundle retrieved locally)
- **Claude Code** with this skill installed

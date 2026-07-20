---
name: validate-script-agent
description: Validate a Script agent against the Legacy agent baseline. Drives paired multi-turn sessions via `sf agent preview`, collects transcripts from both agents, and runs LLM-based 3-dimension evaluation (response quality, data handling, error handling) to produce a PASS/FAIL parity report. TRIGGER when the user wants to validate a script agent migration, compare a legacy agent against a script agent, run parity tests from a CSV of conversation sessions, or generate a feature-parity evaluation report. DO NOT TRIGGER for single-agent SOQL testing or production session-trace analysis.
triggers:
  - "validate-script-agent"
  - "validate script agent"
  - "feature parity"
  - "compare agents"
  - "validate migration"
  - "parity test"
---

# validate-script-agent — Feature Parity Validation

Validate that a **Script agent** (AgentScript migration) produces equivalent behavior to a **Legacy agent** (the proven baseline). The Legacy agent is always the gold standard — the Script agent must demonstrate it matches.

Drives paired multi-turn `sf agent preview` sessions, collects transcripts from both agents, then evaluates parity across 3 dimensions using LLM-based semantic judgment.

## When to Use

TRIGGER when the user wants to:
- Compare a Legacy agent against a migrated Script agent
- Validate that an AgentScript migration has feature parity
- Run multi-turn conversation tests against both agent versions
- Generate a feature-parity PASS/FAIL evaluation report

Do **not** use for single-agent SOQL evaluation, declarative `AiEvaluationDefinition` suites (use `testing-agentforce`), or production session-trace analysis (use `observing-agentforce`).

---

## STEP 0 — Verify prerequisites

Before running the pipeline, confirm these are in place. Guide the user through any missing items.

### 0.1 Salesforce CLI

```bash
sf --version    # Must be 2.138+
sf agent preview --help    # Must show: start, send, end subcommands
```

If missing or outdated: `npm install --global @salesforce/cli` or `sf update`.

### 0.2 Authenticated org

```bash
sf org list    # Must show the target org with an alias
```

If not authenticated: `sf org login web --alias <alias> --instance-url https://login.salesforce.com`

### 0.3 Identify both agents

Ask the user for:
- **Legacy Agent API Name** — the published Bot's DeveloperName (used with `--api-name`)
- **Script Agent Bundle Name** — the AiAuthoringBundle name (used with `--authoring-bundle`)
- **Org Alias** — the alias from `sf org list`

If the user doesn't know the names, help them find them:
```bash
sf org list metadata --metadata-type Bot --target-org <alias>
sf org list metadata --metadata-type AiAuthoringBundle --target-org <alias>
```

### 0.4 Project directory setup

`sf agent preview` requires running from a Salesforce project directory. Check if `sfdx-project.json` exists in the skill directory. If not, create one:

```json
{
  "packageDirectories": [{"path": "force-app", "default": true}],
  "name": "parity-test",
  "sourceApiVersion": "65.0"
}
```

Also create the `force-app/main/default` directory if it doesn't exist.

### 0.5 Retrieve the Script agent bundle

The `--authoring-bundle` flag requires the bundle to exist locally:

```bash
sf project retrieve start --metadata "AiAuthoringBundle:<BundleName>" --target-org <alias>
```

Verify: `ls force-app/main/default/aiAuthoringBundles/<BundleName>/`

### 0.6 Employee Agent CLI patch (if applicable)

If the Legacy agent is an **Employee Agent** (AgentType = `AgentforceEmployeeAgent`), check whether the CLI bug has been fixed:

```bash
sf agent preview start --api-name <LegacyAgentName> --target-org <alias> --json
```

If it returns `"Invalid user ID provided on start session"`, the patch is needed. Guide the user to patch `productionAgent.js`:

1. Locate: `~/.local/share/sf/client/<version>/node_modules/@salesforce/agents/lib/agents/productionAgent.js`
2. Find the `startPreview` method
3. Replace `bypassUser: true` with:
   ```javascript
   const metadata = await this.getBotMetadata();
   const isEmployeeAgent = metadata.AgentType === 'AgentforceEmployeeAgent';
   const hasNoAgentUser = !metadata.BotUserId;
   // ...
   bypassUser: !(isEmployeeAgent || hasNoAgentUser),
   ```

If the start command succeeds, end the test session immediately:
```bash
sf agent preview end --api-name <name> --session-id <sid> --target-org <alias> --json
```

---

## STEP 1 — Confirm scope with the user

Ask the user:
1. Which CSV file contains the test sessions? (or help them create one)
2. How many sessions to start with? (recommend 1-2 for a smoke test first)
3. Which action mode? (`simulate-actions` is safe; `use-live-actions` executes real actions)

### CSV Structure

Fixed schema — 7 columns required:

```csv
Session_Number,Turn_Order,User_Utterance,Legacy_Agent_Name,Script_Agent_Bundle,Target_Org,Action_Mode
1,1,"Hi, I need help",Resort_Manager,Resort_Manager_Bundle,my-dev-org,simulate-actions
1,2,"Book a suite for July 15",Resort_Manager,Resort_Manager_Bundle,my-dev-org,simulate-actions
2,1,"What is our PTO policy?",Resort_Manager,Resort_Manager_Bundle,my-dev-org,simulate-actions
```

| Column | Description |
|--------|-------------|
| `Session_Number` | Groups rows into multi-turn conversations (same number = same session) |
| `Turn_Order` | Sequence within a session (1, 2, 3...) |
| `User_Utterance` | The message sent to BOTH agents |
| `Legacy_Agent_Name` | Published agent API name (DeveloperName) |
| `Script_Agent_Bundle` | Authoring bundle name |
| `Target_Org` | Salesforce org alias |
| `Action_Mode` | `simulate-actions` (safe) or `use-live-actions` (real actions) |

---

## STEP 2 — Capture paired sessions

```bash
python3 <skill_dir>/scripts/run_preview.py \
  --csv <csv_path> --outdir "$DATA" \
  [--only-sessions 1,2]    # smoke subset; omit for all
```

For each session: runs all utterances against the Legacy agent (published, `--api-name`), then runs the same utterances against the Script agent (`--authoring-bundle` + action mode). Writes `$DATA/<session_number>.json` per session. Resumable — skips existing files.

**Expected output:**
```
Processing N session(s) -> $DATA
[session 1] 2 turn(s) | legacy=<name> script=<bundle> org=<alias>
  done: legacy=OK script=OK
preview run done.
```

If any session shows `legacy=ERR` or `script=ERR`, check the JSON file for the error and troubleshoot before continuing.

---

## STEP 3 — Prepare evaluation batches

```bash
python3 <skill_dir>/scripts/prep_eval_batches.py \
  --datadir "$DATA" --evaldir "$EVAL" --batch-size 5
```

**Expected output:** `{"sessions": N, "batches": M, "batch_size": 5}`

---

## STEP 4 — LLM semantic evaluation (parallel sub-agents)

Read the canonical prompt `<skill_dir>/assets/eval_prompt.md`. Dispatch **one sub-agent per batch, all in parallel**. For each batch `NN`, substitute:
- `{BATCH_PATH}` → `$EVAL/batch_NN.json`
- `{VERDICT_PATH}` → `$EVAL/verdicts_NN.json`
- `{DONE_TOKEN}` → `done NN`

Use the prompt verbatim (no paraphrasing).

---

## STEP 5 — Merge verdicts

```bash
python3 <skill_dir>/scripts/merge_verdicts.py --datadir "$DATA" --evaldir "$EVAL"
```

**Expected output:** JSON with `"merged": N`, dimension pass counts, `"overall_parity_pass": N`.

If it exits non-zero, re-dispatch missing batches and re-run merge.

---

## STEP 6 — Build report

```bash
python3 <skill_dir>/scripts/build_report.py \
  --datadir "$DATA" --outdir <output_dir> --name <name>
```

**Expected output:**
```
wrote <output_dir>/<name>_results.csv
Summary: N sessions | Response Quality X/N (%) | Data Handling X/N (%) | Error Handling X/N (%) | Overall Parity X/N (%)
wrote <output_dir>/<name>_report.html
```

Two files are produced:
- `<name>_results.csv` — tabular data for programmatic use
- `<name>_report.html` — interactive single-file HTML viewer with filters, sorting, and expandable session details

---

## STEP 7 — Present results to user

Open the HTML report in the browser:
```bash
open <output_dir>/<name>_report.html
```

Report to the user:
- Overall parity rate (X/N sessions passing)
- Which dimensions are weakest
- Which specific sessions failed and why (read reasons from the CSV)
- The HTML report path for interactive exploration (filter by dimension, expand sessions for side-by-side transcripts)

---

## STEP 8 — (Optional) Re-run failures

If some sessions failed, offer to re-run just those:

```bash
FAILS=$(python3 -c "import json,glob;print(','.join(str(json.load(open(p))['session']) for p in glob.glob('$DATA/*.json') if json.load(open(p)).get('overall_parity')=='FAIL'))")

python3 <skill_dir>/scripts/run_preview.py --csv <csv_path> --outdir "$DATA" --only-sessions "$FAILS"
# Then re-run Steps 3-6
```

---

## 3 Evaluation Dimensions

| Dimension | PASS means |
|---|---|
| **Response Quality** | Script produced substantively equivalent response |
| **Data Handling** | Script referenced the same records/values/counts |
| **Error Handling** | Script handled edge cases the same way |

**Overall parity**: PASS only if ALL 3 dimensions pass.

## Hard Guarantees

1. **Legacy = ground truth**: The Legacy agent's behavior is always correct.
2. **Every PASS/FAIL comes from LLM semantic evaluation** — never deterministic comparison.
3. **3 dimensions** — Response Quality, Data Handling, Error Handling. All must pass for parity.
4. **Report is script-only** — produced by `build_report.py`, never hand-generated.

## CLI Command Patterns

**Legacy** (published, `--api-name`, NO action mode):
```bash
sf agent preview start --api-name <name> --target-org <org> --json
sf agent preview send --utterance "..." --api-name <name> --session-id <sid> --target-org <org> --json
sf agent preview end --api-name <name> --session-id <sid> --target-org <org> --json
```

**Script** (authoring bundle, REQUIRES action mode):
```bash
sf agent preview start --authoring-bundle <bundle> --simulate-actions --target-org <org> --json
sf agent preview send --utterance "..." --authoring-bundle <bundle> --session-id <sid> --target-org <org> --json
sf agent preview end --authoring-bundle <bundle> --session-id <sid> --target-org <org> --json
```

## Design Constraints

1. Legacy = ground truth (never penalize Legacy)
2. Multi-turn sessions (start once → send N → end once)
3. Paired execution with guaranteed cleanup (try/finally)
4. Legacy runs first (sequential, not concurrent)
5. Continue-on-error (failed sessions logged + skipped)
6. PASS/FAIL verdicts (not scores) — all 3 must pass for parity
7. LLM judge via Claude Code sub-agents (no new dependencies)
8. Subprocess timeout 240s
9. Exponential backoff: max 3 retries for transient errors
10. `--only-sessions` supported for re-runs
11. Must run from a Salesforce project directory (cwd has `sfdx-project.json`)

## Bundled Scripts

| Script | Purpose |
|---|---|
| `columns.py` | Fixed CSV column validator (imported by run_preview.py) |
| `run_preview.py` | Drives paired multi-turn `sf agent preview` sessions. Legacy first, then Script. Writes one JSON per session. |
| `prep_eval_batches.py` | Splits session data into batches for LLM evaluation sub-agents |
| `merge_verdicts.py` | Folds 3-dimension verdicts back into session data |
| `build_report.py` | Produces enriched CSV + interactive HTML report with all verdicts + summary |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `RequiresProjectError` | Run from a directory with `sfdx-project.json` (see Step 0.4) |
| `AABNotFound` for Script agent | Retrieve the bundle (Step 0.5) |
| `Invalid user ID provided on start session` | Apply Employee Agent patch (Step 0.6) |
| Legacy agent won't preview | Ensure it's published AND activated in Setup |
| Rate limit / `ConcurrentPerOrgLongTxn` | Wait between runs or reduce session count |
| Empty responses in JSON | Verify CLI version is 2.138+ (`sf update`) |

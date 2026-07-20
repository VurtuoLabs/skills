#!/usr/bin/env python3
"""
Drive paired `sf agent preview` sessions for feature-parity validation.

For each multi-turn session in the CSV:
  1. Run ALL utterances against the Legacy agent (published, --api-name)
  2. Run the SAME utterances against the Script agent (--authoring-bundle)
  3. Collect per-turn transcripts from both into a session JSON file

The Legacy agent's responses are the gold-standard baseline. The Script
agent must demonstrate equivalent behavior.

Resumable: writes one JSON per session, skips existing. Sessions run
sequentially (no cross-session parallelism).

Usage:
  python3 run_preview.py \
    --csv ./sessions.csv \
    --outdir "$TMPDIR/parity_data" \
    [--only-sessions 1,3,5]   # re-run specific sessions
"""
import argparse, csv, json, os, random, re, subprocess, time
from collections import defaultdict

import columns as colmod


PROJECT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def sh(args, timeout=240):
    env = {**os.environ, "SF_DISABLE_LOG_FILE": "true"}
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout, env=env,
                       cwd=PROJECT_DIR)
    return r.stdout, r.stderr


RATE_LIMIT_MARKERS = ("ConcurrentPerOrgLongTxn", "REQUEST_LIMIT_EXCEEDED", "429",
                      "Too Many Requests", "TotalRequests Limit exceeded")


def is_rate_limited(text):
    t = text or ""
    return any(m in t for m in RATE_LIMIT_MARKERS)


def cj(raw):
    """Parse JSON from sf CLI output, stripping control chars that break json."""
    return json.loads(re.sub(r"[\x00-\x1f]", "", raw))


def preview_start(agent_flag, agent_value, org, action_mode=None):
    """Start a preview session. Returns session ID.
    agent_flag: '--api-name' or '--authoring-bundle'
    action_mode: None (legacy) or 'use-live-actions'/'simulate-actions' (script)
    """
    cmd = ["sf", "agent", "preview", "start", "--json",
           agent_flag, agent_value, "--target-org", org]
    if action_mode:
        cmd.append(f"--{action_mode}")

    for attempt in range(3):
        out, err = sh(cmd)
        if is_rate_limited(out) or is_rate_limited(err):
            time.sleep(min(2 ** attempt + random.uniform(0, 1), 30))
            continue
        break
    data = cj(out)
    return data["result"]["sessionId"]


def preview_send(agent_flag, agent_value, session_id, utterance, org):
    """Send an utterance to an open session. Returns the agent's response text."""
    cmd = ["sf", "agent", "preview", "send", "--json",
           "--session-id", session_id,
           agent_flag, agent_value,
           "--utterance", utterance,
           "--target-org", org]

    for attempt in range(3):
        out, err = sh(cmd)
        if is_rate_limited(out) or is_rate_limited(err):
            time.sleep(min(2 ** attempt + random.uniform(0, 1), 30))
            continue
        break

    try:
        data = cj(out)
        messages = data.get("result", {}).get("messages", [])
        response_parts = []
        for msg in messages:
            text = msg.get("message") or msg.get("text") or ""
            if text:
                response_parts.append(text)
        return " ".join(response_parts).strip() or data.get("result", {}).get("message", "")
    except Exception as e:
        return f"[parse error: {e}] stdout={out[:500]}"


def preview_end(agent_flag, agent_value, session_id, org):
    """End a preview session."""
    cmd = ["sf", "agent", "preview", "end", "--json",
           "--session-id", session_id,
           agent_flag, agent_value,
           "--target-org", org]
    sh(cmd)


def run_session_for_agent(agent_flag, agent_value, org, utterances, action_mode=None):
    """Run a full multi-turn session for one agent. Returns list of per-turn responses."""
    sid = None
    responses = []
    try:
        sid = preview_start(agent_flag, agent_value, org, action_mode)
        for utt in utterances:
            resp = preview_send(agent_flag, agent_value, sid, utt, org)
            responses.append(resp)
    finally:
        if sid:
            try:
                preview_end(agent_flag, agent_value, sid, org)
            except Exception:
                pass
    return responses


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="CSV with multi-turn sessions")
    ap.add_argument("--outdir", required=True, help="Output directory for session JSON files")
    ap.add_argument("--only-sessions", default="",
                    help="Comma-separated session numbers to run (default: all)")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    with open(a.csv, newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise SystemExit(f"CSV {a.csv} has no data rows")

    col_map = colmod.validate(rows[0].keys())

    c_session = col_map["session_number"]
    c_turn = col_map["turn_order"]
    c_utt = col_map["user_utterance"]
    c_legacy = col_map["legacy_agent_name"]
    c_script = col_map["script_agent_bundle"]
    c_org = col_map["target_org"]
    c_mode = col_map["action_mode"]

    # Group rows by session number, sorted by turn order
    sessions = defaultdict(list)
    for row in rows:
        snum = row[c_session].strip()
        sessions[snum].append(row)
    for snum in sessions:
        sessions[snum].sort(key=lambda r: int(r[c_turn].strip()))

    only = {x.strip() for x in a.only_sessions.split(",") if x.strip()}
    session_nums = sorted(sessions.keys(), key=lambda x: int(x))
    if only:
        session_nums = [s for s in session_nums if s in only]

    print(f"Processing {len(session_nums)} session(s) -> {a.outdir}")

    for snum in session_nums:
        outp = os.path.join(a.outdir, f"{snum}.json")
        if not only and os.path.exists(outp):
            print(f"[session {snum}] skip (exists)")
            continue

        turns = sessions[snum]
        first = turns[0]
        legacy_agent = first[c_legacy].strip()
        script_bundle = first[c_script].strip()
        org = first[c_org].strip()
        action_mode = first[c_mode].strip()
        utterances = [t[c_utt].strip() for t in turns]

        rec = {
            "session": int(snum),
            "legacy_agent": legacy_agent,
            "script_bundle": script_bundle,
            "org": org,
            "action_mode": action_mode,
            "utterances": utterances,
            "turns": [],
            "legacy_error": None,
            "script_error": None,
        }

        print(f"[session {snum}] {len(utterances)} turn(s) | "
              f"legacy={legacy_agent} script={script_bundle} org={org}")

        # Run Legacy agent (published — uses --api-name, no action mode)
        legacy_responses = []
        try:
            legacy_responses = run_session_for_agent(
                "--api-name", legacy_agent, org, utterances, action_mode=None)
        except Exception as e:
            rec["legacy_error"] = str(e)
            print(f"  legacy ERROR: {e}")

        # Run Script agent (authoring bundle — uses --authoring-bundle + action mode)
        script_responses = []
        try:
            script_responses = run_session_for_agent(
                "--authoring-bundle", script_bundle, org, utterances, action_mode=action_mode)
        except Exception as e:
            rec["script_error"] = str(e)
            print(f"  script ERROR: {e}")

        # Build per-turn transcript
        for i, utt in enumerate(utterances):
            turn = {
                "turn": i + 1,
                "utterance": utt,
                "legacy_response": legacy_responses[i] if i < len(legacy_responses) else "",
                "script_response": script_responses[i] if i < len(script_responses) else "",
            }
            rec["turns"].append(turn)

        json.dump(rec, open(outp, "w"), indent=2)
        legacy_ok = "OK" if not rec["legacy_error"] else "ERR"
        script_ok = "OK" if not rec["script_error"] else "ERR"
        print(f"  done: legacy={legacy_ok} script={script_ok}")

    print("preview run done.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Split captured session data into compact JSON batches for parallel LLM
evaluation sub-agents. Each batch item contains paired transcripts
(legacy = baseline, script = candidate).

Usage:
  python3 prep_eval_batches.py --datadir "$TMPDIR/parity_data" \
    --evaldir "$TMPDIR/parity_eval" \
    [--batch-size 5] [--only-sessions 1,3]
"""
import argparse, glob, json, os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datadir", required=True)
    ap.add_argument("--evaldir", required=True)
    ap.add_argument("--batch-size", type=int, default=5)
    ap.add_argument("--only-sessions", default="",
                    help="comma-separated session numbers (default: all)")
    a = ap.parse_args()
    os.makedirs(a.evaldir, exist_ok=True)

    only = {x.strip() for x in a.only_sessions.split(",") if x.strip()}
    paths = sorted(glob.glob(os.path.join(a.datadir, "*.json")))
    rows = []
    for p in paths:
        d = json.load(open(p))
        snum = str(d.get("session", ""))
        if only and snum not in only:
            continue
        # Skip sessions with fatal errors (no transcript to evaluate)
        if d.get("legacy_error") and not d.get("turns"):
            continue
        rows.append({
            "session": d["session"],
            "legacy_agent": d.get("legacy_agent", ""),
            "script_bundle": d.get("script_bundle", ""),
            "utterances": d.get("utterances", []),
            "legacy_transcript": [
                {"turn": t["turn"], "utterance": t["utterance"],
                 "response": t["legacy_response"]}
                for t in d.get("turns", [])
            ],
            "script_transcript": [
                {"turn": t["turn"], "utterance": t["utterance"],
                 "response": t["script_response"]}
                for t in d.get("turns", [])
            ],
            "legacy_error": d.get("legacy_error"),
            "script_error": d.get("script_error"),
        })

    rows.sort(key=lambda r: r["session"])
    bs = a.batch_size
    batches = [rows[i:i + bs] for i in range(0, len(rows), bs)]
    for i, b in enumerate(batches):
        json.dump(b, open(os.path.join(a.evaldir, f"batch_{i:02d}.json"), "w"), indent=1)

    print(json.dumps({"sessions": len(rows), "batches": len(batches), "batch_size": bs}))


if __name__ == "__main__":
    main()

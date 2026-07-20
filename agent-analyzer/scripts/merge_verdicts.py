#!/usr/bin/env python3
"""
Merge LLM verdict files (verdicts_NN.json written by evaluation sub-agents)
back into the per-session data files. Verdicts contain 3-dimension PASS/FAIL
results comparing the Script agent against the Legacy agent baseline.

Usage:
  python3 merge_verdicts.py --datadir "$TMPDIR/parity_data" \
    --evaldir "$TMPDIR/parity_eval"

Validates that every session received a verdict; exits non-zero and lists
any session missing a verdict so the orchestrator can re-dispatch that batch.
"""
import argparse, glob, json, os, sys

DIMENSIONS = [
    "response_quality",
    "data_handling",
    "error_handling",
]


def load_verdicts(evaldir):
    verdicts = {}
    for vf in sorted(glob.glob(os.path.join(evaldir, "verdicts_*.json"))):
        raw = open(vf).read().strip()
        # Tolerate accidental code fences from LLM output
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        try:
            arr = json.loads(raw)
        except Exception as e:
            print(f"WARN: could not parse {vf}: {e}", file=sys.stderr)
            continue
        for o in arr:
            verdicts[str(o["session"])] = o
    return verdicts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datadir", required=True)
    ap.add_argument("--evaldir", required=True)
    a = ap.parse_args()

    verdicts = load_verdicts(a.evaldir)
    data_paths = sorted(glob.glob(os.path.join(a.datadir, "*.json")))

    # Identify which sessions were part of this eval set
    eval_sessions = set()
    for bf in glob.glob(os.path.join(a.evaldir, "batch_*.json")):
        for o in json.load(open(bf)):
            eval_sessions.add(str(o["session"]))

    missing = sorted(s for s in eval_sessions if s not in verdicts)

    merged = 0
    dim_pass = {d: 0 for d in DIMENSIONS}
    total = 0

    for p in data_paths:
        d = json.load(open(p))
        snum = str(d.get("session", ""))
        v = verdicts.get(snum)
        if not v:
            continue

        for dim in DIMENSIONS:
            d[f"{dim}_result"] = v.get(f"{dim}_result", "N/A")
            d[f"{dim}_reason"] = v.get(f"{dim}_reason", "")

        # Overall parity: PASS only if ALL 3 dimensions pass
        all_pass = all(d.get(f"{dim}_result") == "PASS" for dim in DIMENSIONS)
        d["overall_parity"] = "PASS" if all_pass else "FAIL"

        json.dump(d, open(p, "w"), indent=2)
        merged += 1
        total += 1
        for dim in DIMENSIONS:
            if d.get(f"{dim}_result") == "PASS":
                dim_pass[dim] += 1

    summary = {"merged": merged, "total": total, "missing_verdicts": missing}
    for dim in DIMENSIONS:
        summary[f"{dim}_pass"] = dim_pass[dim]
    overall_pass = sum(1 for p in data_paths
                       if os.path.exists(p)
                       and json.load(open(p)).get("overall_parity") == "PASS")
    summary["overall_parity_pass"] = overall_pass

    print(json.dumps(summary))
    if missing:
        sys.exit(1)


if __name__ == "__main__":
    main()

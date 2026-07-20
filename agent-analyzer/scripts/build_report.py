#!/usr/bin/env python3
"""
Build the enriched results CSV + interactive HTML report from per-session
data files (after verdicts are merged). Outputs:
  - <name>_results.csv  — tabular data with 3-dimension PASS/FAIL verdicts
  - <name>_report.html  — interactive single-file viewer with filters/accordion

This is the CANONICAL report builder. Do not hand-generate output.

Usage:
  python3 build_report.py \
    --datadir "$TMPDIR/parity_data" \
    --outdir ./reports \
    [--name parity_run1]
"""
import argparse, csv, glob, html as html_mod, json, os

DIMENSIONS = [
    "response_quality",
    "data_handling",
    "error_handling",
]

DIM_LABELS = {
    "response_quality": "Response Quality",
    "data_handling": "Data Handling",
    "error_handling": "Error Handling",
}


def esc(x):
    return html_mod.escape(str(x if x is not None else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datadir", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--name", default="parity")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    csv_out = os.path.join(a.outdir, f"{a.name}_results.csv")
    html_out = os.path.join(a.outdir, f"{a.name}_report.html")

    paths = sorted(glob.glob(os.path.join(a.datadir, "*.json")))
    recs = []
    for p in paths:
        d = json.load(open(p))
        if "session" not in d:
            continue
        recs.append(d)
    recs.sort(key=lambda d: d["session"])

    if not recs:
        raise SystemExit("No session data found in datadir")

    # Build CSV
    cols = [
        "Session_Number",
        "Legacy_Agent",
        "Script_Bundle",
        "Org",
        "Turns",
    ]
    for dim in DIMENSIONS:
        cols.append(f"{DIM_LABELS[dim]} Result")
        cols.append(f"{DIM_LABELS[dim]} Reason")
    cols += ["Overall Parity", "Legacy Transcript", "Script Transcript",
             "Legacy Error", "Script Error"]

    with open(csv_out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for d in recs:
            turns = d.get("turns", [])
            legacy_transcript = json.dumps(
                [{"turn": t["turn"], "utterance": t["utterance"],
                  "response": t["legacy_response"]} for t in turns])
            script_transcript = json.dumps(
                [{"turn": t["turn"], "utterance": t["utterance"],
                  "response": t["script_response"]} for t in turns])

            row = {
                "Session_Number": d["session"],
                "Legacy_Agent": d.get("legacy_agent", ""),
                "Script_Bundle": d.get("script_bundle", ""),
                "Org": d.get("org", ""),
                "Turns": len(turns),
            }
            for dim in DIMENSIONS:
                row[f"{DIM_LABELS[dim]} Result"] = d.get(f"{dim}_result", "")
                row[f"{DIM_LABELS[dim]} Reason"] = d.get(f"{dim}_reason", "")
            row["Overall Parity"] = d.get("overall_parity", "")
            row["Legacy Transcript"] = legacy_transcript
            row["Script Transcript"] = script_transcript
            row["Legacy Error"] = d.get("legacy_error") or ""
            row["Script Error"] = d.get("script_error") or ""
            w.writerow(row)

    print(f"wrote {csv_out}")

    # Compute stats
    total = len(recs)
    dim_pass = {dim: sum(1 for d in recs if d.get(f"{dim}_result") == "PASS")
                for dim in DIMENSIONS}
    overall_pass = sum(1 for d in recs if d.get("overall_parity") == "PASS")

    def pct(n):
        return f"{round(100 * n / total)}%" if total else "0%"

    # Print summary
    parts = [f"{total} sessions"]
    for dim in DIMENSIONS:
        parts.append(f"{DIM_LABELS[dim]} {dim_pass[dim]}/{total} ({pct(dim_pass[dim])})")
    parts.append(f"Overall Parity {overall_pass}/{total} ({pct(overall_pass)})")
    print(f"Summary: {' | '.join(parts)}")

    # ---- HTML Report ----
    legacy_agent = recs[0].get("legacy_agent", "") if recs else ""
    script_bundle = recs[0].get("script_bundle", "") if recs else ""
    org_name = recs[0].get("org", "") if recs else ""

    # Build session rows
    rows_html = []
    for d in recs:
        snum = d["session"]
        turns = d.get("turns", [])
        n_turns = len(turns)
        rq = d.get("response_quality_result", "N/A") or "N/A"
        dh = d.get("data_handling_result", "N/A") or "N/A"
        eh = d.get("error_handling_result", "N/A") or "N/A"
        op = d.get("overall_parity", "N/A") or "N/A"

        def badge(val):
            cls = val.lower().replace("/", "")
            return f'<span class="badge {cls}">{esc(val)}</span>'

        # Turn-by-turn transcript
        transcript_rows = ""
        for t in turns:
            transcript_rows += f"""<div class="turn-row">
  <div class="turn-num">Turn {t['turn']}</div>
  <div class="turn-utterance"><strong>User:</strong> {esc(t.get('utterance',''))}</div>
  <div class="turn-responses">
    <div class="resp-col legacy-col">
      <div class="resp-label">Legacy</div>
      <div class="resp-text">{esc(t.get('legacy_response',''))}</div>
    </div>
    <div class="resp-col script-col">
      <div class="resp-label">Script</div>
      <div class="resp-text">{esc(t.get('script_response',''))}</div>
    </div>
  </div>
</div>"""

        # Error display
        error_html = ""
        if d.get("legacy_error"):
            error_html += f'<div class="error-box"><strong>Legacy Error:</strong> {esc(d["legacy_error"])}</div>'
        if d.get("script_error"):
            error_html += f'<div class="error-box"><strong>Script Error:</strong> {esc(d["script_error"])}</div>'

        # Verdict cards
        verdict_html = ""
        for dim in DIMENSIONS:
            result = d.get(f"{dim}_result", "N/A") or "N/A"
            reason = d.get(f"{dim}_reason", "") or ""
            verdict_html += f"""<div class="verdict-card">
  <div class="verdict-header">
    <span class="verdict-dim">{esc(DIM_LABELS[dim])}</span>
    {badge(result)}
  </div>
  <div class="verdict-reason">{esc(reason)}</div>
</div>"""

        rows_html.append(f"""<div class="accordion" data-session="{snum}" data-turns="{n_turns}"
  data-rq="{esc(rq)}" data-dh="{esc(dh)}" data-eh="{esc(eh)}" data-op="{esc(op)}">
  <div class="accordion-header colgrid" onclick="toggleAccordion(this)">
    <span class="col-num">{snum}</span>
    <span class="col-agents">{esc(d.get('legacy_agent',''))} vs {esc(d.get('script_bundle',''))}</span>
    <span class="col-turns">{n_turns} turn{'s' if n_turns != 1 else ''}</span>
    <span class="col-dim">{badge(rq)}</span>
    <span class="col-dim">{badge(dh)}</span>
    <span class="col-dim">{badge(eh)}</span>
    <span class="col-parity">{badge(op)}</span>
    <span class="expand-icon">&#9662;</span>
  </div>
  <div class="accordion-body">
    {error_html}
    <div class="transcript-section">
      <div class="section-title">Conversation Transcript</div>
      {transcript_rows}
    </div>
    <div class="verdicts-section">
      <div class="section-title">Evaluation Verdicts</div>
      {verdict_html}
    </div>
  </div>
</div>""")

    rows_joined = "\n".join(rows_html)
    state_key = f"validate_script_agent_{a.name}"

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Feature Parity Report</title>
<style>
* {{ box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; background: #f3f4f6; }}
.header {{ background: #1f2937; color: #fff; padding: 24px 28px; }}
.header h1 {{ margin: 0 0 6px; font-size: 22px; font-weight: 700; }}
.header .subtitle {{ margin: 0; font-size: 13px; color: #9ca3af; }}
.meta-row {{ margin-top: 12px; display: flex; gap: 8px; flex-wrap: wrap; }}
.meta-chip {{ display: inline-block; background: #374151; border-radius: 6px; padding: 4px 12px; font-size: 12px; color: #e5e7eb; }}
.meta-chip b {{ color: #fff; }}
.summary-row {{ margin-top: 10px; display: flex; gap: 8px; flex-wrap: wrap; }}
.summary-chip {{ display: inline-block; background: #374151; border-radius: 6px; padding: 5px 12px; font-size: 12px; color: #e5e7eb; }}
.summary-chip.pass {{ background: #065f46; color: #a7f3d0; }}
.summary-chip.fail {{ background: #7f1d1d; color: #fecaca; }}

.filter-bar {{ display: flex; align-items: center; gap: 8px; margin: 16px 24px 10px; background: #fff; padding: 12px 18px; border-radius: 8px; flex-wrap: wrap; box-shadow: 0 1px 3px rgba(0,0,0,.06); }}
.filter-group {{ display: flex; align-items: center; gap: 6px; }}
.filter-label {{ font-size: 10px; font-weight: 700; color: #6b7280; text-transform: uppercase; letter-spacing: .03em; }}
.filter-sep {{ color: #d1d5db; margin: 0 4px; }}
.filter-btn {{ font-size: 11px; font-weight: 600; padding: 4px 10px; border-radius: 20px; border: 1px solid #d1d5db; background: #f9fafb; color: #6b7280; cursor: pointer; transition: all .15s; }}
.filter-btn:hover {{ border-color: #9ca3af; }}
.filter-btn.active[data-value="PASS"] {{ background: #dcfce7; border-color: #86efac; color: #166534; }}
.filter-btn.active[data-value="FAIL"] {{ background: #fee2e2; border-color: #fca5a5; color: #991b1b; }}
.filter-reset {{ font-size: 11px; padding: 4px 10px; border-radius: 20px; border: 1px solid #d1d5db; background: #fff; cursor: pointer; margin-left: auto; }}
.filter-reset:hover {{ background: #f3f4f6; }}
.results-count {{ font-size: 12px; color: #6b7280; }}

.sort-header {{ margin: 0 24px 8px; background: #111827; color: #cbd5e1; border-radius: 8px; padding: 10px 18px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .03em; }}
.colgrid {{ display: grid; grid-template-columns: 50px 1fr 80px 100px 100px 100px 90px 30px; gap: 10px; align-items: center; }}
.sortable {{ cursor: pointer; user-select: none; white-space: nowrap; }}
.sortable:hover {{ color: #fff; }}
.sort-arrow {{ opacity: .4; font-size: 9px; margin-left: 3px; }}
.active-sort {{ color: #fff; }}
.active-sort .sort-arrow {{ opacity: 1; }}

.accordion {{ margin: 0 24px 8px; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.04); }}
.accordion-header {{ padding: 14px 18px; cursor: pointer; user-select: none; border-bottom: 1px solid transparent; transition: background .1s; }}
.accordion-header:hover {{ background: #f9fafb; }}
.accordion-header.open {{ border-bottom-color: #e5e7eb; }}
.col-num {{ font-size: 13px; font-weight: 700; color: #6b7280; }}
.col-agents {{ font-size: 12px; color: #374151; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.col-turns {{ font-size: 11px; color: #6b7280; }}
.col-dim {{ text-align: center; }}
.col-parity {{ text-align: center; }}
.expand-icon {{ font-size: 16px; color: #9ca3af; transition: transform .2s; text-align: center; }}
.accordion-header.open .expand-icon {{ transform: rotate(180deg); }}

.badge {{ font-size: 10px; font-weight: 600; padding: 3px 8px; border-radius: 4px; white-space: nowrap; display: inline-block; }}
.badge.pass {{ background: #dcfce7; color: #166534; }}
.badge.fail {{ background: #fee2e2; color: #991b1b; }}
.badge.na, .badge.n\\/a {{ background: #f3f4f6; color: #6b7280; }}

.accordion-body {{ display: none; padding: 18px 20px; }}
.accordion-body.open {{ display: block; }}

.section-title {{ font-size: 12px; font-weight: 700; color: #374151; text-transform: uppercase; letter-spacing: .03em; margin-bottom: 12px; padding-bottom: 6px; border-bottom: 1px solid #e5e7eb; }}

.turn-row {{ margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid #f3f4f6; }}
.turn-row:last-child {{ border-bottom: none; margin-bottom: 0; padding-bottom: 0; }}
.turn-num {{ font-size: 10px; font-weight: 700; color: #6b7280; text-transform: uppercase; margin-bottom: 4px; }}
.turn-utterance {{ font-size: 13px; color: #1f2937; margin-bottom: 10px; padding: 6px 10px; background: #f0f9ff; border-radius: 6px; border-left: 3px solid #3b82f6; }}
.turn-responses {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
.resp-col {{ background: #f9fafb; border-radius: 6px; padding: 10px 12px; border: 1px solid #e5e7eb; }}
.resp-label {{ font-size: 10px; font-weight: 700; text-transform: uppercase; margin-bottom: 6px; }}
.legacy-col .resp-label {{ color: #6b7280; }}
.script-col .resp-label {{ color: #7c3aed; }}
.resp-text {{ font-size: 12px; color: #374151; line-height: 1.5; white-space: pre-wrap; word-break: break-word; }}

.verdicts-section {{ margin-top: 20px; }}
.verdict-card {{ background: #f9fafb; border-radius: 6px; padding: 12px 14px; margin-bottom: 8px; border: 1px solid #e5e7eb; }}
.verdict-card:last-child {{ margin-bottom: 0; }}
.verdict-header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }}
.verdict-dim {{ font-size: 12px; font-weight: 700; color: #374151; }}
.verdict-reason {{ font-size: 12px; color: #4b5563; line-height: 1.5; padding-left: 10px; border-left: 3px solid #d1d5db; }}

.error-box {{ background: #fef2f2; border: 1px solid #fecaca; border-radius: 6px; padding: 10px 14px; margin-bottom: 14px; font-size: 12px; color: #991b1b; }}

.transcript-section {{ margin-bottom: 0; }}

@media (max-width: 900px) {{
  .colgrid {{ grid-template-columns: 40px 1fr 60px 70px 70px 70px 70px 24px; gap: 6px; }}
  .turn-responses {{ grid-template-columns: 1fr; }}
  .accordion {{ margin: 0 12px 8px; }}
  .filter-bar {{ margin: 12px 12px 8px; }}
  .sort-header {{ margin: 0 12px 8px; }}
}}
</style>
</head>
<body>
<div class="header">
  <h1>Feature Parity Report</h1>
  <p class="subtitle">validate-script-agent</p>
  <div class="meta-row">
    <span class="meta-chip"><b>Legacy:</b> {esc(legacy_agent)}</span>
    <span class="meta-chip"><b>Script:</b> {esc(script_bundle)}</span>
    <span class="meta-chip"><b>Org:</b> {esc(org_name)}</span>
    <span class="meta-chip"><b>Sessions:</b> {total}</span>
  </div>
  <div class="summary-row">
    <span class="summary-chip">Response Quality: {dim_pass['response_quality']}/{total} ({pct(dim_pass['response_quality'])})</span>
    <span class="summary-chip">Data Handling: {dim_pass['data_handling']}/{total} ({pct(dim_pass['data_handling'])})</span>
    <span class="summary-chip">Error Handling: {dim_pass['error_handling']}/{total} ({pct(dim_pass['error_handling'])})</span>
    <span class="summary-chip {'pass' if overall_pass == total else 'fail'}"><b>Overall Parity: {overall_pass}/{total} ({pct(overall_pass)})</b></span>
  </div>
</div>

<div class="filter-bar">
  <div class="filter-group">
    <span class="filter-label">Resp Quality</span>
    <button class="filter-btn active" data-filter="rq" data-value="PASS">PASS</button>
    <button class="filter-btn active" data-filter="rq" data-value="FAIL">FAIL</button>
  </div>
  <span class="filter-sep">|</span>
  <div class="filter-group">
    <span class="filter-label">Data</span>
    <button class="filter-btn active" data-filter="dh" data-value="PASS">PASS</button>
    <button class="filter-btn active" data-filter="dh" data-value="FAIL">FAIL</button>
  </div>
  <span class="filter-sep">|</span>
  <div class="filter-group">
    <span class="filter-label">Error</span>
    <button class="filter-btn active" data-filter="eh" data-value="PASS">PASS</button>
    <button class="filter-btn active" data-filter="eh" data-value="FAIL">FAIL</button>
  </div>
  <span class="filter-sep">|</span>
  <div class="filter-group">
    <span class="filter-label">Parity</span>
    <button class="filter-btn active" data-filter="op" data-value="PASS">PASS</button>
    <button class="filter-btn active" data-filter="op" data-value="FAIL">FAIL</button>
  </div>
  <button class="filter-reset" onclick="resetFilters()">Reset</button>
  <span class="results-count" id="count">{total} of {total} sessions</span>
</div>

<div class="sort-header colgrid">
  <span class="sortable" data-sort="session" onclick="doSort('session')">Session<span class="sort-arrow"></span></span>
  <span>Agents</span>
  <span class="sortable" data-sort="turns" onclick="doSort('turns')">Turns<span class="sort-arrow"></span></span>
  <span class="sortable" data-sort="rq" onclick="doSort('rq')">Resp Qual<span class="sort-arrow"></span></span>
  <span class="sortable" data-sort="dh" onclick="doSort('dh')">Data<span class="sort-arrow"></span></span>
  <span class="sortable" data-sort="eh" onclick="doSort('eh')">Error<span class="sort-arrow"></span></span>
  <span class="sortable" data-sort="op" onclick="doSort('op')">Parity<span class="sort-arrow"></span></span>
  <span></span>
</div>

<div id="rows-container">
{rows_joined}
</div>

<script>
const STATE_KEY = {json.dumps(state_key)};
const FILTERS = ['rq', 'dh', 'eh', 'op'];
const activeFilters = {{}};
FILTERS.forEach(f => activeFilters[f] = new Set(['PASS', 'FAIL', 'N/A']));
let sortCol = null, sortDir = 1;

function saveState() {{
  const s = {{ filters: {{}}, sort: (sortCol || '') + ':' + sortDir }};
  FILTERS.forEach(f => s.filters[f] = [...activeFilters[f]].join('||'));
  try {{ localStorage.setItem(STATE_KEY, JSON.stringify(s)); }} catch(e) {{}}
}}

function applyFilters() {{
  const rows = document.querySelectorAll('.accordion');
  let visible = 0;
  rows.forEach(r => {{
    const show = FILTERS.every(f => activeFilters[f].has(r.dataset[f]));
    r.style.display = show ? '' : 'none';
    if (show) visible++;
  }});
  document.getElementById('count').textContent = `${{visible}} of ${{rows.length}} sessions`;
  saveState();
}}

function doSort(col) {{
  if (sortCol === col) sortDir = -sortDir;
  else {{ sortCol = col; sortDir = 1; }}
  const cont = document.getElementById('rows-container');
  const rows = [...cont.querySelectorAll('.accordion')];
  rows.sort((a, b) => {{
    let av = a.dataset[col] || '', bv = b.dataset[col] || '';
    if (col === 'session' || col === 'turns') return (+av - +bv) * sortDir;
    return av.localeCompare(bv) * sortDir;
  }});
  rows.forEach(r => cont.appendChild(r));
  document.querySelectorAll('.sort-header .sortable').forEach(s => {{
    const ar = s.querySelector('.sort-arrow');
    if (s.dataset.sort === sortCol) {{ s.classList.add('active-sort'); ar.textContent = sortDir > 0 ? '\\u25B2' : '\\u25BC'; }}
    else {{ s.classList.remove('active-sort'); ar.textContent = ''; }}
  }});
  saveState();
}}

function toggleAccordion(hdr) {{
  const body = hdr.nextElementSibling;
  const isOpen = body.classList.contains('open');
  hdr.classList.toggle('open', !isOpen);
  body.classList.toggle('open', !isOpen);
}}

function resetFilters() {{
  FILTERS.forEach(f => activeFilters[f] = new Set(['PASS', 'FAIL', 'N/A']));
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.add('active'));
  sortCol = null; sortDir = 1;
  document.querySelectorAll('.sort-header .sortable').forEach(s => {{
    s.classList.remove('active-sort');
    s.querySelector('.sort-arrow').textContent = '';
  }});
  applyFilters();
}}

document.querySelectorAll('.filter-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    const f = btn.dataset.filter, val = btn.dataset.value;
    if (activeFilters[f].has(val)) {{ activeFilters[f].delete(val); btn.classList.remove('active'); }}
    else {{ activeFilters[f].add(val); btn.classList.add('active'); }}
    applyFilters();
  }});
}});

document.addEventListener('DOMContentLoaded', () => {{
  try {{
    const s = JSON.parse(localStorage.getItem(STATE_KEY) || '{{}}');
    if (s.filters) FILTERS.forEach(f => {{
      if (s.filters[f]) activeFilters[f] = new Set(s.filters[f].split('||').filter(Boolean));
    }});
    if (s.sort) {{
      const [c, dir] = s.sort.split(':');
      if (c) {{ sortCol = c; sortDir = +dir || 1; }}
    }}
    document.querySelectorAll('.filter-btn').forEach(btn => {{
      const f = activeFilters[btn.dataset.filter];
      btn.classList.toggle('active', f ? f.has(btn.dataset.value) : false);
    }});
    if (sortCol) doSort(sortCol);
    applyFilters();
  }} catch(e) {{}}
}});
</script>
</body>
</html>"""

    with open(html_out, "w") as f:
        f.write(html_doc)
    print(f"wrote {html_out}")


if __name__ == "__main__":
    main()

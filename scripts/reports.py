"""Stage 9: write report.md and SUMMARY.md from manifest, checks, logs and build info."""
import json, os, sys
from collections import defaultdict, Counter
sys.path.insert(0, os.path.dirname(__file__))
from assemble import TOPICS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "Δ-chemistry", "p2-topical-workbook")
PH = ["phase1", "phase2"]


def j(p):
    return json.load(open(os.path.join(ROOT, p)))


def main():
    man = j("data/manifest.json")
    checks = {ph: j(f"work/checks_{ph}.json") for ph in PH}
    logs = {ph: j(f"work/log_{ph}.json") for ph in PH}
    items = {ph: j(f"work/items_{ph}.json") for ph in PH}
    parts = {ph: j(f"work/parts_{ph}.json") for ph in PH}
    topics = j("topics.json")
    info = j("work/build_info.json")
    fc = j("work/final_checks.json")

    R = ["# Report — 9701 Paper 2 part-level topical workbook", "",
         "All failures, exclusions and AUTO-DECIDED items, grouped by type. Nothing was retyped or patched: "
         "every question and mark-scheme crop is a vector clip of the official PDF.", ""]

    # ---------- AUTO-DECIDED ----------
    R += ["## AUTO-DECIDED", "", "| Item | Issue | What I did |", "|---|---|---|"]
    title_var = Counter()
    series_var = []
    for pid, e in man.items():
        for k in ("qp", "ms"):
            for n in e[k].get("notes", []) if isinstance(e.get(k), dict) else []:
                if n.startswith("title"):
                    title_var[n] += 1
                else:
                    series_var.append(f"{pid} {k}")
    for n, c in title_var.items():
        R.append(f"| {c} downloaded files | Page-1 title reads {n.split(' ', 2)[2]} instead of \"Paper 2 AS Level "
                 f"Structured Questions\" (older official wording); code, series and MS/QP type match | Accepted |")
    if series_var:
        R.append(f"| {len(series_var)} files (m16–m17) | Series printed as \"March 20yy\" instead of \"February/March "
                 f"20yy\" | Accepted; reference written as MAR yy |")
    R += [
        "| Mark schemes 2015–2018 | Old layouts: question numbers/letters/romans in separate columns; marks as \"[1]\" in "
        "a Total column; text drawn 2–3× (faux bold) or split into overlapping fragments; part total printed above "
        "its per-point 1s; question total printed after the last part | MS reader extended (dedupe, rejoin "
        "fragments, carry labels across rows, use the Total column, keep only the part total when it equals the sum of "
        "its 1-mark points, drop a printed question total and trim it off the crop). Verified the change leaves every "
        "Phase-1 MS row identical. Every question still had to pass check 4 (MS = QP total) |",
        "| Consecutive roman sub-parts with the same topic | Split rule talks about individual sub-parts | Split only "
        "where the topic changes; same-topic neighbours stay together, e.g. Q3(c)(i)-(ii) |",
        "| Test/observation tables spanning several functional groups | One lowest-level part covers several organic "
        "topics | Tagged 21.1 (identify functional groups using the reactions in the syllabus) |",
        "| Items whose text says to use the Data Booklet (Phase 2 only) | Data Booklet is a separate document, not "
        "included, so the item is not solvable alone | Excluded (listed below) |",
        "| Phase 2 papers (pre-2022) | Older papers do not number figures/tables (\"the table below\") | Cross-part "
        "context found from part references, \"use your answer\", and defined labels/compounds; the lettered "
        "introduction is always included for split sub-parts |",
        "| Topic ties | Majority-topic marks tie | Filed under the topic of the first sub-part that belongs to one "
        "of the tied topics (listed below) |",
        "| Download-site watermark | Source PDFs carry a tiled \"PapaCambridge\" watermark (Form XObject + inline "
        "low-opacity glyphs) | Stripped in memory when loading; downloaded files left untouched |",
    ]
    for ph in PH:
        for a in logs[ph]["auto"]:
            R.append(f"| {a['ref']} | {a['issue']} | {a['action']} |")
    R.append("")

    # ---------- downloads ----------
    R += ["## Downloads and header checks", ""]
    for ph in PH:
        sel = {k: e for k, e in man.items() if e["phase"] == ph}
        bad = {k: e for k, e in sel.items() if e["status"] != "ok"}
        R.append(f"- {ph}: {len(sel)} papers attempted, {len(sel) - len(bad)} downloaded and verified, "
                 f"{len(bad)} excluded.")
        for k, e in bad.items():
            why = "; ".join(f"{t}: {', '.join(e[t].get('issues') or [e[t].get('error', '')])}"
                            for t in ("qp", "ms") if e[t]["status"] != "ok")
            R.append(f"  - {k}: {why}")
    R.append("")

    # ---------- paper / question exclusions ----------
    R += ["## Paper-level verification failures", "", "| Paper | Scope | Failure | Action |", "|---|---|---|---|"]
    for ph in PH:
        for pid, r in sorted(checks[ph].items()):
            if r["paper_excluded"]:
                R.append(f"| {r['ref'] or pid} | whole paper | {r['paper_excluded']} | paper excluded |")
            for n, q in r["questions"].items():
                if not q["ok"]:
                    R.append(f"| {r['ref']} | Q{n} | {q['why']} | question excluded |")
    R += ["", "Phase-1 causes (inspected): MS without Q5 rows (M/J 24/P22); MS rows printed without marks "
          "(O/N 22/P21–23 Q4(a), O/N 24/P22 Q4(e)(i)); MS label typo \"4(a(i)\" (O/N 23/P21, P23); Q1(c)(iii) withdrawn by "
          "Cambridge (O/N 25/P21–23, MS \"N/A\"). Phase-2 question failures are MS layouts whose marks could not be "
          "matched to the QP totals from the text layer; s15 P21's QP has no usable text layer.", ""]

    # ---------- item exclusions ----------
    R += ["## Item exclusions", "", "| Item | Issue | Action |", "|---|---|---|"]
    for ph in PH:
        for e in logs[ph]["excluded"]:
            R.append(f"| {e['ref']} | {e['issue']} | {e['action']} |")
    R.append("")

    # ---------- out of syllabus ----------
    R += ["## Out-of-syllabus (Phase 2; not clearly covered by the 2025–27 learning outcomes)", "",
          "| Item | Issue | Action |", "|---|---|---|"]
    for ph in PH:
        for e in logs[ph]["out_of_syllabus"]:
            R.append(f"| {e['ref']} | {e['issue']} | {e['action']} |")
    R.append("")

    # ---------- kept whole ----------
    R += ["## Multi-topic lettered parts kept whole (filed under the majority topic, tagged \"also\")", "",
          "| Item | Why not split | Marks by unit |", "|---|---|---|"]
    for ph in PH:
        for e in logs[ph]["kept_whole"]:
            R.append(f"| {e['ref']} | {e['why']} | {e['by']} |")
    R.append("")

    # ---------- thin units ----------
    per = Counter()
    for ph in PH:
        for it in items[ph]:
            per[it["topic"]] += 1
    thin = [t for t in TOPICS if per[t] < 5]
    R += ["## Thin units (< 5 items)", "", ("- " + ", ".join(f"Unit {t}" for t in thin)) if thin else "- None.", ""]

    # ---------- coverage & final checks ----------
    R += ["## Final checks on the built book", "",
          f"- Coverage: every lowest-level part of every included question appears in exactly one item, or is in "
          f"an exclusion list above. Unexplained gaps: {len(fc['coverage_unexplained'])}; duplicates: "
          f"{len(fc['coverage_dupes'])}.",
          f"- Self-containment re-check: {len(fc['selfcontained_fail'])} failures; context recomputed identically "
          f"for every item ({len(fc['ctx_mismatch'])} mismatches).",
          f"- Marks re-check (item [marks] = MS marks): {len(fc['marks_fail'])} failures.",
          f"- Every item reference found on its indexed page: {len(fc['ref_not_on_page'])} misses; every item has "
          f"an answer entry: {len(fc['answers_missing'])} misses.", "",
          "## Layout checks (rendered and inspected)", "",
          "- Cover, contents (2 pages), unit title pages; item pages in Units 1, 2, 7, 11, 14, 22; Answers Sections "
          "(Units 1, 2, 3, 7, 10) including 2015–2016 mark-scheme layouts; topic index; Periodic Table appendix.",
          "- Fixed after inspection: download-site watermark, corner marks/barcode stubs at page breaks, "
          "Periodic Table orientation and crop, contents box heights, printed question totals in old MS crops, "
          "font subsetting for size.", ""]
    open(os.path.join(ROOT, "report.md"), "w").write("\n".join(R) + "\n")

    # ---------- SUMMARY ----------
    S = ["# SUMMARY — Chemistry 9701 Paper 2 part-level topical workbook", ""]
    tot_dl = len(man)
    ok_dl = sum(1 for e in man.values() if e["status"] == "ok")
    inc = sum(len(parts[ph]) for ph in PH)
    S += ["## Papers", "",
          f"| | Phase 1 (m22–s26) | Phase 2 (2015–2021) | Total |", "|---|---|---|---|"]
    row = lambda f: [f(ph) for ph in PH]
    dl = row(lambda ph: sum(1 for e in man.values() if e["phase"] == ph))
    ok = row(lambda ph: sum(1 for e in man.values() if e["phase"] == ph and e["status"] == "ok"))
    incl = row(lambda ph: len(parts[ph]))
    q_inc = row(lambda ph: sum(len(p["questions"]) for p in parts[ph].values()))
    q_exc = row(lambda ph: sum(1 for r in checks[ph].values() for q in r["questions"].values() if not q["ok"]))
    it = row(lambda ph: len(items[ph]))
    for name, v in [("Papers attempted (qp + ms)", dl), ("Downloaded & header-verified", ok),
                    ("Papers included", incl), ("Questions included", q_inc), ("Questions excluded", q_exc),
                    ("Items in the book", it)]:
        S.append(f"| {name} | {v[0]} | {v[1]} | {v[0] + v[1]} |")
    S += ["", "Papers excluded: s20 v23 (MS header says \"Paper 3\"), s15 v21 (QP has no usable text layer).", ""]

    S += ["## Items per unit", "", "| Unit | Items | Marks |", "|---|---|---|"]
    mk = Counter()
    for ph in PH:
        for x in items[ph]:
            mk[x["topic"]] += x["marks"]
    for t, name in TOPICS.items():
        S.append(f"| {t} {name} | {per[t]} | {mk[t]} |")
    S.append(f"| **Total** | **{sum(per.values())}** | **{sum(mk.values())}** |")
    S.append("")

    S += ["## Files produced", "", "| File | Size |", "|---|---|"]
    def size(p):
        return f"{os.path.getsize(p) / 1e6:.1f} MB" if os.path.getsize(p) > 1e5 else f"{os.path.getsize(p) / 1e3:.0f} KB"
    rel = lambda p: os.path.relpath(p, ROOT)
    book = os.path.join(OUT, "Chemistry-9701-P2-Topical-Workbook.pdf")
    S.append(f"| {rel(book)} ({info['pages']} pages) | {size(book)} |")
    for f in sorted(os.listdir(os.path.join(OUT, "units"))):
        p = os.path.join(OUT, "units", f)
        S.append(f"| {rel(p)} | {size(p)} |")
    for p in [os.path.join(OUT, "index.csv"), os.path.join(ROOT, "topics.json"), os.path.join(ROOT, "report.md"),
              os.path.join(ROOT, "layout.md")]:
        S.append(f"| {rel(p)} | {size(p)} |")
    S += ["", "No file exceeds 95 MB, so everything is pushed. Per-unit PDFs keep the full book's page numbers "
          "(so they match index.csv).", ""]

    S += ["## Review these first", "",
          "1. **Topic tagging** (topics.json): every part was tagged by reading its text against the syllabus. "
          "Judgement calls worth a look: 21.1 for multi-functional-group test tables; 9.3 for unfamiliar elements; "
          "4.2 vs 3.x for structure/bonding explanations; Phase-2 parts marked out-of-syllabus (vapour pressure, "
          "cooling curves, fertilisers/eutrophication, Contact-process oleum stage, electrolysis, ceramics, "
          "enthalpy of atomisation, greenhouse/CFC questions, crude-oil fractional distillation).",
          "2. **2015–2018 mark schemes**: their marks were read with layout heuristics (see report.md "
          "AUTO-DECIDED). Each question still had to match the QP total, but spot-check a few answers in the "
          "older years.",
          "3. **Phase-2 context**: older papers don't number figures, so context comes from part references and "
          "defined labels only. Spot-check split sub-parts from 2015–2021 for anything that says \"the diagram "
          "above\" when the diagram sits in an earlier sub-part.",
          f"4. **Exclusions** ({sum(len(logs[ph]['excluded']) for ph in PH)} items, "
          f"{sum(q_exc)} questions, 2 papers): genuine source defects in Phase 1; mostly MS-layout and Data "
          "Booklet cases in Phase 2. Full list in report.md.",
          "5. **Repo size**: the book (40 MB) and 22 unit PDFs (~215 MB) are committed; consider Git LFS or a "
          "release if the repo gets heavy.", ""]
    open(os.path.join(ROOT, "SUMMARY.md"), "w").write("\n".join(S) + "\n")
    print("report.md and SUMMARY.md written")


if __name__ == "__main__":
    main()

"""Write λ-cs/report.md and λ-cs/SUMMARY.md from the manifest, checks, logs
and build info. Sections whose data does not exist yet (later stages) are
left out, so the report is accurate at every stage.

Hand-kept inputs (never generated): λ-cs/work/auto_decided.json (rows of the
AUTO-DECIDED table that are decisions rather than data), and
λ-cs/work/notes_layout.md / notes_open.md (inspection log, open issues).
Usage: python3 scripts/cs/reports.py
"""
import os, sys
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(__file__))
from paths import CS, ROOT, OUT, BOOK_FILE, MANIFEST, work, jload

PH = ["phase1", "phase2"]
PHNAME = {"phase1": "Phase 1 (9618)", "phase2": "Phase 2 (9608)"}


def exists(name):
    return os.path.exists(work(name))


def read(name):
    p = work(name)
    return open(p).read().strip() if os.path.exists(p) else ""


def size(p):
    n = os.path.getsize(p)
    return f"{n / 1e6:.1f} MB" if n > 1e5 else f"{n / 1e3:.0f} KB"


def main():
    man = jload(MANIFEST, {})
    phases = [ph for ph in PH if any(e["phase"] == ph for e in man.values())]
    checks = {ph: jload(work(f"checks_{ph}.json")) for ph in phases if exists(f"checks_{ph}.json")}
    logs = {ph: jload(work(f"log_{ph}.json")) for ph in phases if exists(f"log_{ph}.json")}
    items = {ph: jload(work(f"items_{ph}.json")) for ph in phases if exists(f"items_{ph}.json")}
    parts = {ph: jload(work(f"parts_{ph}.json")) for ph in phases if exists(f"parts_{ph}.json")}
    info = {b: jload(work(f"build_info_p{b}.json")) for b in (1, 2) if exists(f"build_info_p{b}.json")}
    built = [ph for ph in phases if ph in items and info and
             all(i["ref"] in info[i["book"]]["ref_pages"] for i in items[ph])]
    fc = jload(work("final_checks.json")) if exists("final_checks.json") else None
    syl = jload(work("syllabus.json"))
    TOPICS = {int(k): v for k, v in syl["units"].items()}

    R = ["# Report: Computer Science 9618 Paper 1 and Paper 2 part-level topical workbooks", "",
         "All failures, exclusions and AUTO-DECIDED items, grouped by type, for both books. Nothing was retyped "
         "or patched: every question and mark-scheme crop is a vector clip of the official PDF.", ""]

    # ---------- AUTO-DECIDED ----------
    R += ["## AUTO-DECIDED", "", "| Item | Issue | What I did |", "|---|---|---|"]
    for row in jload(work("auto_decided.json"), []):
        R.append(f"| {row['item']} | {row['issue']} | {row['action']} |")
    notes = Counter()
    for pid, e in man.items():
        for k in ("qp", "ms", "in"):
            for n in e[k].get("notes", []) if isinstance(e.get(k), dict) else []:
                notes[(k, n)] += 1
    for (k, n), c in sorted(notes.items()):
        R.append(f"| {c} downloaded {k.upper()} files | Page 1 reads {n} instead of the spec's wording; code, "
                 f"paper number, series and document type match | Accepted and logged (spec: Header check) |")
    for ph in checks:
        for pid, r in sorted(checks[ph].items()):
            for a, b in r.get("ms_label_fixes", []):
                R.append(f"| {r['ref']} MS label \"{a}\" | Typo in the mark scheme | Read as {b} (unambiguous) |")
            if r.get("unredacted_pages"):
                R.append(f"| {r['ref']} QP page(s) {', '.join(map(str, r['unredacted_pages']))} | Removing the answer-line dots "
                         f"from the text layer moved other glyphs on the page (text set with character spacing) | "
                         f"Page used unchanged: its dotted lines are hidden by white-outs and stay in the PDF text layer "
                         f"(not in items.jsonl) |")
            for a, b in r.get("ms_label_notes", []):
                R.append(f"| {r['ref']} MS label \"{a}\" | The question paper has no sub-parts in {b} | "
                         f"The row is the answer of {b} (unambiguous) |")
    for ph in logs:
        for a in logs[ph]["auto"]:
            R.append(f"| {a['ref']} | {a['issue']} | {a['action']} |")
    R.append("")

    # ---------- downloads ----------
    R += ["## Downloads and header checks", ""]
    for ph in phases:
        sel = {k: e for k, e in man.items() if e["phase"] == ph}
        c = Counter(e["status"] for e in sel.values())
        R.append(f"**{PHNAME[ph]}**: {len(sel)} papers attempted; {c['ok']} downloaded with QP and MS headers "
                 f"verified; {c['unavailable']} not on the site; {c['excluded']} excluded for a header mismatch; "
                 f"{c['download_failed']} download failures. Inserts found: "
                 f"{sum(e['in']['status'] == 'ok' for e in sel.values())}.")
        R += ["", "| Series | P1 papers | P2 papers | Inserts | Not on the site | Excluded |", "|---|---|---|---|---|---|"]
        ser = sorted({(e["year"], {"m": 0, "s": 1, "w": 2}[e["series"]], e["series"]) for e in sel.values()})
        for y, _, s in ser:
            es = [e for e in sel.values() if e["year"] == y and e["series"] == s]
            R.append(f"| {s}{y % 100:02d} | {sum(e['status'] == 'ok' and e['paper'] == 1 for e in es)} | "
                     f"{sum(e['status'] == 'ok' and e['paper'] == 2 for e in es)} | "
                     f"{sum(e['in']['status'] == 'ok' for e in es)} | "
                     f"{sum(e['status'] == 'unavailable' for e in es)} | "
                     f"{sum(e['status'] in ('excluded', 'download_failed') for e in es)} |")
        R.append("")
        una = sorted(k for k, e in sel.items() if e["status"] == "unavailable")
        if una:
            R.append("Unavailable (the site answers with a redirect, no PDF): " + ", ".join(una) + ".")
        for k, e in sorted(sel.items()):
            if e["status"] in ("excluded", "download_failed"):
                why = "; ".join(f"{t}: {', '.join(e[t].get('issues') or [e[t].get('error', '')])}"
                                for t in ("qp", "ms") if e[t]["status"] != "ok")
                R.append(f"- {k} excluded: {why}")
            elif e["status"] == "unavailable" and e["in"]["status"] == "ok":
                R.append(f"- {k}: only the insert is on the site (no QP or MS); not used.")
        R.append("")

    # ---------- paper / question exclusions ----------
    if checks:
        R += ["## Paper-level verification failures", "",
              "Checks: (1) every question number exactly once; (2) part [marks] add up to the cover total of 75; "
              "(3) MS marks of each question equal its QP marks; (4) reference from the header text.", "",
              "| Paper | Scope | Failure | Action |", "|---|---|---|---|"]
        n = 0
        for ph in checks:
            for pid, r in sorted(checks[ph].items()):
                if r["paper_excluded"]:
                    R.append(f"| {r['ref'] or pid} | whole paper | {r['paper_excluded']} | paper excluded |")
                    n += 1
                for qn, q in r["questions"].items():
                    if not q["ok"]:
                        R.append(f"| {r['ref']} | Q{qn} | {q['why']} | question excluded |")
                        n += 1
        if not n:
            R.append("| (none) | | | |")
        R.append("")
        for ph in checks:
            ok = sum(1 for r in checks[ph].values() if not r["paper_excluded"])
            R.append(f"- {PHNAME[ph]}: {len(checks[ph])} papers checked, {ok} pass, "
                     f"{len(checks[ph]) - ok} excluded; "
                     f"{sum(1 for r in checks[ph].values() for q in r['questions'].values() if not q['ok'])} "
                     f"questions excluded.")
        nc = read("notes_checks.md")
        if nc:
            R += ["", nc]
        R.append("")

    nt = read("notes_tags.md")
    if nt:
        R += ["## Tagging", "", nt, ""]
    if logs:
        # ---------- item exclusions ----------
        R += ["## Item exclusions", "", "| Item | Issue | Action |", "|---|---|---|"]
        n = 0
        for ph in logs:
            for e in logs[ph]["excluded"]:
                R.append(f"| {e['ref']} | {e['issue']} | {e['action']} |")
                n += 1
        if not n:
            R.append("| (none) | | |")
        R.append("")
        # ---------- out of syllabus / pre-release ----------
        R += ["## Out of syllabus (not clearly covered by the 2027-29 learning outcomes)", "",
              "| Item | Issue | Action |", "|---|---|---|"]
        n = 0
        for ph in logs:
            for e in logs[ph]["out_of_syllabus"]:
                R.append(f"| {e['ref']} | {e['issue']} | {e['action']} |")
                n += 1
        if not n:
            R.append("| (none) | | |")
        R += ["", "## Parts that need pre-release material (9608 Paper 2)", "", "| Item | Issue | Action |",
              "|---|---|---|"]
        n = 0
        for ph in logs:
            for e in logs[ph]["pre_release"]:
                R.append(f"| {e['ref']} | {e['issue']} | {e['action']} |")
                n += 1
        if not n:
            R.append("| (none) | | |")
        R.append("")
        # ---------- cross-filed ----------
        R += ["## Parts filed by topic in the other paper's book", "",
              "A part is filed by its topic, not its paper (spec, Goal).", "", "| Item | Unit | Filed in |",
              "|---|---|---|"]
        n = 0
        for ph in logs:
            for e in logs[ph]["cross_filed"]:
                R.append(f"| {e['ref']} | {e['unit']} {TOPICS[e['unit']]} | {e['action']} |")
                n += 1
        if not n:
            R.append("| (none) | | |")
        R.append("")
        # ---------- kept whole ----------
        R += ["## Multi-unit lettered parts kept whole (filed under the majority unit, tagged \"also\")", "",
              "| Item | Why not split | Marks by unit |", "|---|---|---|"]
        n = 0
        for ph in logs:
            for e in logs[ph]["kept_whole"]:
                R.append(f"| {e['ref']} | {e['why']} | {e['by']} |")
                n += 1
        if not n:
            R.append("| (none) | | |")
        R.append("")
        # ---------- split ----------
        ns = sum(len(logs[ph]["split"]) for ph in logs)
        R += ["## Lettered parts split by unit", "",
              f"{ns} lettered parts were split into roman-level items because their sub-parts belong to different "
              "units and each is solvable alone:", ""]
        for ph in logs:
            for e in logs[ph]["split"]:
                R.append(f"- {e['ref']}: " + "; ".join(f"{g[0]} → unit {g[1]}" for g in e["groups"]))
        R.append("")
        # ---------- insert ----------
        R += ["## Insert", "", "| Item | Shown as | Why |", "|---|---|---|"]
        n = 0
        for ph in logs:
            for e in logs[ph]["insert"]:
                how = {"note": "note \"Uses the insert (Appendix)\"",
                       "inline": f"this paper's insert inline ({len(e['pages'])} page(s))"}.get(e["mode"], e["mode"])
                R.append(f"| {e['ref']} | {how} | {e['why']} |")
                n += 1
        if not n:
            R.append("| (none) | | |")
        R.append("")
        # ---------- context ----------
        why = Counter()
        for ph in logs:
            for e in logs[ph]["context"]:
                w = e["why"]
                w = "identifier rule" if w.startswith("identifier") else "single-letter label" if w.startswith("label") \
                    else "scenario noun (\"the ...\")" if w.startswith("'the") else w
                why[w] += 1
        R += ["## Context added to items", "",
              "Besides the stem and the lettered introduction (always shown), earlier parts were added as context "
              "for these reasons (count of context parts):", ""]
        R += [f"- {k}: {v}" for k, v in why.most_common()] or ["- none"]
        R.append("")
        # ---------- thin units ----------
        per = Counter()
        for ph in items:
            for it in items[ph]:
                per[it["topic"]] += 1
        thin = [t for t in TOPICS if per[t] < 5]
        R += ["## Thin units (< 5 items)", "", ("- " + ", ".join(f"Unit {t}" for t in thin)) if thin else "- None.", ""]

    if fc and built:
        R += ["## Final checks on the built books", "",
              f"- Coverage: every lowest-level part of every included question appears in exactly one item, or is "
              f"in an exclusion list above. Unexplained gaps: {len(fc['coverage_unexplained'])}; duplicates: "
              f"{len(fc['coverage_dupes'])}.",
              f"- Self-containment re-check (build resolver): {len(fc['selfcontained_fail'])} failures; context "
              f"recomputed identically for every item ({len(fc['ctx_mismatch'])} mismatches).",
              f"- Marks re-check (item [marks] = MS marks): {len(fc['marks_fail'])} failures.",
              f"- Every item reference found on its indexed page: {len(fc['ref_not_on_page'])} misses; every item "
              f"has an answer entry: {len(fc['answers_missing'])} misses.",
              f"- Every item is in the book of its unit: {len(fc['wrong_book'])} misses.", ""]
    nl = read("notes_layout.md")
    if nl:
        R += ["## Layout and visual checks", "", nl, ""]
    open(os.path.join(CS, "report.md"), "w").write("\n".join(R) + "\n")

    # ---------- SUMMARY ----------
    S = ["# SUMMARY: Computer Science 9618 Paper 1 and Paper 2 part-level topical workbooks", ""]
    st = jload(os.path.join(CS, "state_cs.json"), {"stages": {}})
    done = [k for k, v in sorted(st["stages"].items(), key=lambda kv: int(kv[0])) if v == "done"]
    S += [f"Stages finished: {', '.join(done) or 'none'} (see `λ-cs/state_cs.json`). "
          f"Books contain: {', '.join(PHNAME[p] for p in built) or 'not built yet'}.", ""]
    S += ["## Papers", "", "| | " + " | ".join(PHNAME[p] for p in phases) + " | Total |",
          "|---|" + "---|" * (len(phases) + 1)]

    def row(name, f):
        v = [f(ph) for ph in phases]
        S.append(f"| {name} | " + " | ".join(str(x) for x in v) + f" | {sum(v)} |")
    row("Papers attempted", lambda ph: sum(1 for e in man.values() if e["phase"] == ph))
    row("Not on the site", lambda ph: sum(1 for e in man.values() if e["phase"] == ph and e["status"] == "unavailable"))
    row("Downloaded and header-verified (QP + MS)", lambda ph: sum(1 for e in man.values()
                                                                   if e["phase"] == ph and e["status"] == "ok"))
    row("Inserts found", lambda ph: sum(1 for e in man.values() if e["phase"] == ph and e["in"]["status"] == "ok"))
    if checks:
        row("Papers passing the paper checks", lambda ph: sum(1 for r in checks.get(ph, {}).values()
                                                             if not r["paper_excluded"]))
        row("Questions excluded (MS marks ≠ QP marks)", lambda ph: sum(1 for r in checks.get(ph, {}).values()
                                                                       for q in r["questions"].values() if not q["ok"]))
    if parts:
        row("Questions included", lambda ph: sum(len(p["questions"]) for p in parts.get(ph, {}).values()))
    if items:
        row("Items in the books", lambda ph: len(items.get(ph, [])))
        row("Marks in the books", lambda ph: sum(i["marks"] for i in items.get(ph, [])))
    S.append("")
    if items:
        for b in (1, 2):
            S += [f"## Paper {b} book: papers, items and marks per unit", "",
                  "| Unit | Papers | Items | Marks |", "|---|---|---|---|"]
            tot_p = set()
            ti = tm = 0
            for t, name in TOPICS.items():
                if (t <= 8) != (b == 1):
                    continue
                its = [i for ph in items for i in items[ph] if i["topic"] == t]
                ps = {i["paper"] for i in its}
                tot_p |= ps
                ti += len(its)
                tm += sum(i["marks"] for i in its)
                S.append(f"| {t} {name} | {len(ps)} | {len(its)} | {sum(i['marks'] for i in its)} |")
            S.append(f"| **Total** | **{len(tot_p)}** | **{ti}** | **{tm}** |")
            S.append("")
    if info:
        S += ["## Files produced", "", "| File | Size |", "|---|---|"]
        rel = lambda p: os.path.relpath(p, ROOT)
        big = []
        for b in (1, 2):
            if b not in info:
                continue
            book = os.path.join(OUT[b], BOOK_FILE[b])
            S.append(f"| {rel(book)} ({info[b]['pages']} pages) | {size(book)} |")
            fl = [book]
            for f in sorted(os.listdir(os.path.join(OUT[b], "units"))):
                p = os.path.join(OUT[b], "units", f)
                S.append(f"| {rel(p)} | {size(p)} |")
                fl.append(p)
            for n in ("index.csv", "items.jsonl", "topics.json"):
                p = os.path.join(OUT[b], n)
                S.append(f"| {rel(p)} | {size(p)} |")
            big += [rel(p) for p in fl if os.path.getsize(p) > 95e6]
        for p in [os.path.join(CS, "report.md"), os.path.join(CS, "layout.md"),
                  os.path.join(ROOT, "hub", "audit", "CS_CHECK.md")]:
            if os.path.exists(p):
                S.append(f"| {rel(p)} | {size(p)} |")
        S.append("")
        if big:
            S += ["Files over 95 MB (not pushed; use the per-unit PDFs): " + ", ".join(big) + ".", ""]
        else:
            S += ["No file exceeds 95 MB, so everything is pushed. Per-unit PDFs keep the full book's page numbers "
                  "(so they match index.csv).", ""]
    no = read("notes_open.md")
    S += ["## What is still open", "", no or "- Nothing recorded yet.", ""]
    open(os.path.join(CS, "SUMMARY.md"), "w").write("\n".join(S) + "\n")
    print("report.md and SUMMARY.md written")


if __name__ == "__main__":
    main()

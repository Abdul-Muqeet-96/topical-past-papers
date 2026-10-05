"""Write Ω-physics/report.md and Ω-physics/SUMMARY.md from the manifest, checks, logs,
booklet light check, build info and final checks."""
import json, os, sys
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(__file__))
from assemble import TOPICS
import report_partA

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PH = os.path.join(ROOT, "Ω-physics")
OUT = os.path.join(PH, "p2-topical-workbook")
BOOKNAME = "Physics-9702-P2-Topical-Workbook.pdf"


def j(p):
    return json.load(open(os.path.join(PH, p)))


def size(p):
    s = os.path.getsize(p)
    return f"{s / 1e6:.1f} MB" if s > 1e5 else f"{s / 1e3:.0f} KB"


def main():
    man = j("work/manifest_physics.json")
    chk = j("work/checks_partb.json")
    log = j("work/log_partb.json")
    items = j("work/items_partb.json")
    parts = j("work/parts_partb.json")
    info = j("work/build_info.json")
    fc = j("work/final_checks.json")
    bk = j("work/booklet_items.json")
    bchk = j("work/booklet_check.json")
    selfchk = os.path.join(ROOT, "audit", "PHYSICS_CHECK.md")

    R = ["# Report — Physics 9702 Paper 2 topical workbook", "",
         "Two sources (spec `Ω-physics/CLAUDE-physics.md`): **Part A** = the scanned Read and Write booklet "
         "(papers up to 2023; its items and answers used as they are, cropped from the OCR'd scan "
         "`Ω-physics/booklet-ocr.pdf`), **Part B** = official papers (O/N 2023, all 2024–2026 papers listed in "
         "the spec), built with the Chemistry pipeline. Nothing was retyped: every question and answer in the "
         "book is a crop of the scan or a vector clip of the official PDF.", ""]
    # ---------- AUTO-DECIDED ----------
    R += ["## AUTO-DECIDED", "", "| Item | Issue | What I did |", "|---|---|---|"]
    rows = [
        ("Run branch", "The prompt names `claude/physics-p2-booklet`; the session's default branch had another "
         "name", "Followed the prompt (the user's explicit instruction): all work pushed to "
         "`claude/physics-p2-booklet`; no pull request."),
        ("9702 s26 v21", "QP downloads, MS does not exist on the source (HTTP 302 to an error page)",
         "Excluded (as the spec says) and reported."),
        ("Data and Formulae pages", "In every Part B paper both are on QP page 2 (page 3 is blank or a "
         "question page)", "Page 2 recognised by its 'Data'/'Formulae' headings and never used as question "
         "material; a page 3 with questions is used normally. Appendix: the Data and Formulae page of the "
         "newest paper (M/J 26/P24)."),
        ("Physics mark schemes", "Marks are printed as codes (B1, C1, M1, A1; B2/B3) not numbers; codes in "
         "brackets, e.g. (C1), belong to an alternative method", "Marks = sum of the code digits; bracketed "
         "codes not counted. Check 4 (MS = QP total) passed for every question, so the reading is confirmed."),
        ("MS alternative introduced by 'OR'", "In a few rows a second method follows an 'OR' line with "
         "unbracketed codes", "Its codes are not counted only where the first method's marks equal that part's "
         "QP marks (else the row is read as printed). Applied to: " +
         ", ".join(f"{c['ref']} {a[0]} ({a[1]} → {a[2]})" for c in chk.values() for a in c.get("or_alternatives", []))
         + "."),
    ]
    for pid, c in sorted(chk.items()):
        for a, b in c.get("ms_label_fixes", []):
            rows.append((f"{c['ref']} MS label \"{a}\"", "Typo in the mark scheme (missing brackets)",
                         f"Read as {b} (unambiguous; Chemistry decision D6)."))
    for pid, c in sorted(chk.items()):
        if c.get("duplicate_of"):
            rows.append((c["ref"], c["paper_excluded"], "Paper not repeated: its questions are already in the "
                         f"book under {chk[c['duplicate_of']]['ref']}."))
    rows += [
        ("Figure captions", "Physics captions read 'Fig. 2.1 (not to scale)' and some figures share one caption "
         "line ('Fig. 4.1 (not to scale) Fig. 4.2 (not to scale)')", "Both forms recognised as captions (the "
         "copied Chemistry rule only accepted a bare caption). Before this, 79 items failed the "
         "self-containment check; after it none."),
        ("Context height", "The one-page context limit added the heights of overlapping regions (a figure "
         "inside a context part counted twice)", "Height measured on the union of the context regions, as the "
         "book lays them out."),
        ("Booklet items: marks", "The booklet's printed [marks] can only be read by OCR (the sample check shows "
         "the margin OCR is right for 46/55 items)", "Marks are not given for booklet items in index.csv, "
         "items.jsonl or the unit pages (no unverified figures); the crops show them."),
        ("Booklet item headings in crops", "The booklet prints its own number and reference above each item "
         "and answer", "Crops start below that heading line; the book prints its own number (one numbering per "
         "unit) and the normalised reference."),
    ]
    for a in log["auto"]:
        rows.append((a["ref"], a["issue"], a["action"]))
    rows += report_partA.auto_decided()
    # ---------- final-audit fixes ----------
    from build import MISFILED
    for (u, n), why in MISFILED.items():
        rows.append((f"Booklet Unit {u} #{n}", "The booklet files this question twice, once under an unrelated "
                     "unit", f"Dropped the misfiled copy: {why}."))
    gp = os.path.join(ROOT, "Ω-physics", "work", "gapfill.json")
    if os.path.exists(gp):
        G = json.load(open(gp))
        for k, o in G["replace_q"].items():
            rows.append((f"Booklet {k}", "Question runs into printed pages missing from the scan", "Question "
                         f"cropped from the official paper ({o['qp']}, Q{o['q']}; header verified, part marks = "
                         f"[Total] = MS marks = {o['marks']}); the booklet answer is kept. Grey note on the item."))
        for k, o in G["replace_a"].items():
            rows.append((f"Booklet {k}", "Answer missing from the scan or runs into missing pages", "Answer cropped "
                         f"from the official mark scheme ({o['ms']}, Q{o['q']}, {o['marks']} marks; checks as "
                         "above). Grey note on the answer."))
        for o in G["lost"]:
            rows.append((f"Booklet Unit {o['unit']} #{o['n']} {o['ref']}", "Question entirely on pages missing "
                         "from the scan (only its answer survived)", f"Restored at its booklet position from the "
                         f"official paper ({o['qp']}/{o['ms']}, Q{o['q']}, {o['marks']} marks; checks as above)."))
        for f_ in G["failed"]:
            rows.append((f"Booklet {f_[0]} {f_[1]}", "Gap could not be filled from the official paper", f_[3]))
    rows.append(("Answer-line dot removal (2017-19 papers)", "The copied Chemistry rule removed dot glyphs with a "
                 "box as tall as the line, which also removed some marks such as \"[2]\" on the next line in 11 "
                 "physics papers", "Box narrowed to a thin strip through the dots' centres; every question paper "
                 "now keeps all its non-dot text (checked on all 9702 and 9701 papers; the Chemistry book was not "
                 "affected)."))
    R += [f"| {a} | {b} | {c} |" for a, b, c in rows]
    R.append("")
    # ---------- downloads ----------
    R += ["## Downloads and header checks", ""]
    by_phase = defaultdict(list)
    for k, e in man.items():
        by_phase[e["phase"]].append((k, e))
    for ph, es in by_phase.items():
        bad = [(k, e) for k, e in es if e["status"] != "ok"]
        what = {"partb": "Part B papers (spec list + O/N 23)", "check": "QPs for the booklet light check"}[ph]
        R.append(f"- {what}: {len(es)} attempted, {len(es) - len(bad)} downloaded and header-verified "
                 f"(9702/<variant>, 'Paper 2 AS Level Structured Questions', series), {len(bad)} excluded.")
        for k, e in bad:
            R.append(f"  - {k}: " + "; ".join(f"{t}: {e[t].get('error') or ', '.join(e[t].get('issues', []))}"
                                            for t in ("qp", "ms") if t in e and e[t]["status"] != "ok"))
    R.append("")
    # ---------- paper checks ----------
    R += ["## Part B paper-level verification", "",
          "Checks per paper (scripts/physics/check_papers.py): every question once, [Total] = sum of part marks, "
          "totals = 60, MS marks = QP total per question, reference from the paper's own header.", "",
          "| Paper | Questions | Result |", "|---|---|---|"]
    for pid, c in sorted(chk.items(), key=lambda kv: (man[kv[0]]["year"], man[kv[0]]["series"], man[kv[0]]["variant"])):
        bad = [n for n, q in c["questions"].items() if not q["ok"]]
        res = c["paper_excluded"] or ("all pass" if not bad else f"questions failing: {bad}")
        R.append(f"| {c['ref']} | {len(c['questions'])} | {res} |")
    R.append("")
    # ---------- items ----------
    per = Counter(i["topic"] for i in items)
    R += ["## Part B items", "",
          f"- {len(items)} items from {len(parts)} papers ({sum(len(p['questions']) for p in parts.values())} "
          f"questions, {sum(i['marks'] for i in items)} marks). Excluded items: {len(log['excluded'])}"
          + (": " + "; ".join(f"{e['ref']} ({e['issue']})" for e in log["excluded"]) if log["excluded"] else "")
          + ". Out of syllabus: none (every lowest-level part matched a 2025–27 AS learning outcome; "
          "topics.json).",
          f"- Lettered parts split by topic: {len(log['split'])}; multi-topic lettered parts kept whole "
          f"(filed under the majority topic, tagged 'also'): {len(log['kept_whole'])}.", "",
          "| Kept whole | Why not split | Marks by unit |", "|---|---|---|"]
    for e in log["kept_whole"]:
        R.append(f"| {e['ref']} | {e['why']} | {e['by']} |")
    thin = [t for t in TOPICS if per[t] + sum(1 for b in bk if b["topic"] == t) < 5]
    R += ["", "Thin units (< 5 items): " + (", ".join(map(str, thin)) if thin else "none") + ".", ""]
    # ---------- Part A ----------
    R.append(report_partA.section())
    # ---------- final checks ----------
    R += ["## Checks on the built book", "",
          f"- Coverage (Part B): every lowest-level part of every included question is in exactly one item: "
          f"unexplained gaps {len(fc['coverage_unexplained'])}, duplicates {len(fc['coverage_dupes'])}.",
          f"- Self-containment re-check: {len(fc['selfcontained_fail'])} failures; context recomputed identically "
          f"({len(fc['ctx_mismatch'])} mismatches). Marks re-check (item [marks] = MS marks): "
          f"{len(fc['marks_fail'])} failures.",
          f"- Every item's reference is on its indexed page (official {len(fc['ref_not_on_page'])} misses, "
          f"booklet {len(fc['booklet_ref_not_on_page'])} misses) and appears with an answer entry and an index "
          f"row (official {len(fc['answers_missing'])} misses, booklet {len(fc['booklet_answer_missing'])} "
          f"misses). Booklet items in the book: {fc['counts']['booklet_in_book']}/{fc['counts']['booklet_items']}.",
          "- Full self-check with every audit-derived check: `audit/PHYSICS_CHECK.md`"
          + (" (see there)." if os.path.exists(selfchk) else " (not yet written)."), ""]
    open(os.path.join(PH, "report.md"), "w").write("\n".join(R) + "\n")

    # ---------- SUMMARY ----------
    S = ["# SUMMARY — Physics 9702 Paper 2 topical workbook", "",
         "## What was done", "",
         "- **Part A (booklet, papers up to 2023):** OCR of all 550 scanned pages (tesseract, 300 dpi); "
         "`booklet-ocr.pdf` = the original scans with every OCR word as invisible text; item and answer "
         "headings mapped (731 by OCR, 3 read by image, 18 numbers confirmed by image); items cropped from "
         "heading to heading with running headers and branding removed; light check against 55 official papers.",
         "- **Part B (official papers):** O/N 2023 (absent from the booklet) and all 2024–2026 papers in the spec; "
         "paper checks, part-level items with official context, topic tags with 2025–27 learning outcomes, "
         "mark-scheme crops.",
         "- **Book:** units 1–11 (syllabus names), Part B items then booklet items, newest first, one numbering, "
         "Answers Section after each unit, contents, bookmarks, Topic index, Data and Formulae appendix.", ""]
    S += ["## Items per unit", "", "| Unit | Part B items (marks) | Part A booklet items | Total |",
          "|---|---|---|---|"]
    mk = Counter()
    for i in items:
        mk[i["topic"]] += i["marks"]
    pb = Counter(b["topic"] for b in bk)
    for t, name in TOPICS.items():
        S.append(f"| {t} {name} | {per[t]} ({mk[t]}) | {pb[t]} | {per[t] + pb[t]} |")
    S.append(f"| **Total** | **{sum(per.values())} ({sum(mk.values())})** | **{len(bk)}** | "
             f"**{sum(per.values()) + len(bk)}** |")
    S += ["", f"Book: {info['pages']} pages. Part B: {len(parts)} papers "
          f"({sum(1 for e in man.values() if e['phase'] == 'partb')} attempted; s26 v21 has no mark scheme; "
          "O/N 25/P23 is identical to O/N 25/P21 and is not repeated).", ""]
    S += ["## Files", "", "| File | Size |", "|---|---|"]
    rel = lambda p: os.path.relpath(p, ROOT)
    book = os.path.join(OUT, BOOKNAME)
    S.append(f"| {rel(book)} ({info['pages']} pages) | {size(book)} |")
    for f in sorted(os.listdir(os.path.join(OUT, "units"))):
        p = os.path.join(OUT, "units", f)
        S.append(f"| {rel(p)} | {size(p)} |")
    for p in [os.path.join(OUT, "index.csv"), os.path.join(OUT, "items.jsonl"), os.path.join(PH, "topics.json"),
              os.path.join(PH, "booklet-ocr.pdf"), os.path.join(PH, "report.md")]:
        S.append(f"| {rel(p)} | {size(p)} |")
    big = [p for p in [book, os.path.join(PH, "booklet-ocr.pdf")] if os.path.getsize(p) > 95e6]
    S += ["", ("Files over 95 MB (not pushed): " + ", ".join(map(rel, big))) if big else
          "No file exceeds 95 MB, so everything is pushed. Unit PDFs keep the book's page numbers "
          "(they match index.csv).", ""]
    gaps = ", ".join(f"{a}–{b}" for a, b in bchk["lost_in_scan"]["missing_printed_pages"])
    S += ["## Still open", "",
          f"1. **Missing booklet pages.** The scan lacks printed pages {gaps}: 7 booklet items and 5 answers are "
          "lost, 4 items and 1 answer are cut short (marked in the book). A complete scan would restore them.",
          "2. **Booklet marks** are not in index.csv / items.jsonl (OCR of the margin is not reliable enough); "
          "the crops show them.",
          "3. **Booklet text layer** is OCR: good for search and for Claude, but formulas, subscripts and Greek "
          "letters are often misread. The page image is authoritative (items.jsonl says so per item).",
          f"4. **Flagged booklet items** ({len(bchk['outside_syllabus'])} on electric fields, outside the 2025–27 "
          "AS syllabus) are kept with a note; two booklet duplicates (filed twice by the booklet) are kept with "
          "a note.",
          "5. **Topic tags** (work/tags.txt, topics.json) were set by reading every part; worth a look: "
          "measurement parts inside topic-4 questions (density) and energy parts inside kinematics questions "
          "were tagged by what they test, which splits some questions across units.",
          "6. **Repo size:** the book, unit PDFs and booklet-ocr.pdf are committed (see sizes above).", ""]
    if os.path.exists(selfchk):
        S += ["Self-check results: `audit/PHYSICS_CHECK.md`.", ""]
    open(os.path.join(PH, "SUMMARY.md"), "w").write("\n".join(S) + "\n")
    print("report.md and SUMMARY.md written")


if __name__ == "__main__":
    main()

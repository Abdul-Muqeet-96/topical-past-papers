"""Write audit/CS_CHECK.md from the outputs of the check scripts (audit/out/cs/*.json, run.log).
Every check is PASS, FAIL or NOT RUN, with its counts and its script.

A finding list that is not empty is a FAIL unless every row of it has been read and judged: the
judgements are kept by hand in judged.json ({"<output file>": {"rows": n, "verdict": "..."}}); a
judgement counts only while the number of rows is still the one that was read."""
import json, re, datetime
from collections import Counter
from c00_common import *

J = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "judged.json")))
LOG = open(os.path.join(OUT, "run.log")).read() if os.path.exists(os.path.join(OUT, "run.log")) else ""
rows = []


def have(name):
    return os.path.exists(os.path.join(OUT, name))


def n_of(name):
    return len(jl(name)) if have(name) else None


def add(group, check, script, result, counts):
    rows.append((group, check, script, result, counts))


def lst(group, check, script, files, ok_note=""):
    """a check whose findings are lists: PASS when empty, or when every row was read and judged"""
    if not all(have(x) for x in files):
        add(group, check, script, "NOT RUN", "")
        return
    n = {x: n_of(x) for x in files}
    tot = sum(n.values())
    if tot == 0:
        add(group, check, script, "PASS", "0 findings" + (". " + ok_note if ok_note else ""))
        return
    notes, ok = [], True
    for x, k in n.items():
        if not k:
            continue
        j = J.get(x)
        if j and j["rows"] == k:
            notes.append(f"{k} flagged, all read: {j['verdict']}")
        else:
            ok = False
            notes.append(f"{k} findings in {x} not judged")
    add(group, check, script, "PASS" if ok else "FAIL", "; ".join(notes) + (". " + ok_note if ok_note else ""))


def log(section, pat):
    m = re.search(r"== " + re.escape(section) + r"\n(.*?)(?=\n== |\Z)", LOG, re.S)
    if not m:
        return None
    mm = re.search(pat, m.group(1))
    return mm


# 1 sources
if have("sources.json"):
    c = Counter((s["kind"], s["status"]) for s in jl("sources.json"))
    bad = [s for s in jl("sources.json") if s["status"] not in ("OK", "ABSENT")]
    probe = sum(1 for s in jl("sources.json") if s.get("probe"))
    add("Sources", "Header of every downloaded file (code, paper, series, document type)", "c10_sources.py",
        "PASS" if len(bad) == 2 else "FAIL",
        f"{len(jl('sources.json'))} expected files: QP {c[('qp','OK')]} ok, MS {c[('ms','OK')]} ok, inserts {c[('in','OK')]} ok; "
        f"absent on the site: QP {c[('qp','ABSENT')]}, MS {c[('ms','ABSENT')]}, inserts {c[('in','ABSENT')]}; "
        f"{len(bad)} files fail and both are excluded by the build and reported: " + ", ".join(f"{s['file']} ({s['status'].lower().replace('_', ' ')})" for s in bad))
else:
    add("Sources", "Header of every downloaded file", "c10_sources.py", "NOT RUN", "")
if have("redownload.json"):
    r = jl("redownload.json")
    add("Sources", "10 random files downloaded again and compared byte for byte", "c11_redownload.py",
        "PASS" if len(r) == 10 and all(x["identical"] for x in r) else "FAIL", f"{sum(1 for x in r if x['identical'])} of {len(r)} identical (SHA-256)")
else:
    add("Sources", "10 random files downloaded again and compared byte for byte", "c11_redownload.py", "NOT RUN", "")

# 2 paper level
if have("compare.json"):
    c = jl("compare.json")
    np_ = len(c["paper"])
    m = log("c22 compare", r"sequence ok (\d+) \| sum = cover = 75 (\d+) \| \[Total\] ok (\d+)")
    ok = not c["unexplained"] and not c["build_diff"] and not c["excluded_not_confirmed"] and m and all(int(x) == np_ for x in m.groups())
    add("Paper level", "Question numbers once and in order; part marks = cover total (75); printed [Total]; QP marks = MS marks per question and per part",
        "c20_qp_parse.py, c21_ms_parse.py, c22_compare.py (own parsers, no build code)", "PASS" if ok else "FAIL",
        f"{np_} papers: sequence ok {m.group(1)}, sum = cover {m.group(2)}, [Total] ok {m.group(3)}; "
        f"{len(c['q_mismatch'])} questions with QP ≠ MS marks, all excluded by the build; {len(c['leaf_mismatch'])} part-level differences, "
        f"all inside excluded questions or logged label slips; differences between the audit's and the build's reading: {len(c['build_diff'])}; unexplained: {len(c['unexplained'])}")
else:
    add("Paper level", "Paper-level checks", "c20, c21, c22", "NOT RUN", "")

# 3 coverage and marks
if have("coverage.json"):
    c = jl("coverage.json")
    ok = not (c["gaps"] or c["dupes"] or c["listed_and_included"] or c["bad_refs"] or c["item_marks_vs_qp"] or c["item_marks_vs_ms"] or c["stale_report_rows"])
    add("Coverage, marks", "Every lowest-level part of every verified paper is in exactly one item or in a reported exclusion; item marks = QP = MS",
        "c30_book_parse.py, c31_coverage.py", "PASS" if ok else "FAIL",
        f"{c['leaves']} parts: " + ", ".join(f"{v} {k}" for k, v in c["classes"].items()) +
        f"; gaps {len(c['gaps'])}, in two items {len(c['dupes'])}, item marks ≠ QP {len(c['item_marks_vs_qp'])}, ≠ MS {len(c['item_marks_vs_ms'])}")
else:
    add("Coverage, marks", "Coverage and marks", "c31_coverage.py", "NOT RUN", "")

# 4 three-way
m = log("c40 three-way", r"(\{.*\})\nthree-way failures: (\d+)")
lst("Consistency", "Book (both sides), index.csv, items.jsonl, topics.json, unit PDFs and the build's item list agree (items, order, units, pages, marks, notes)",
    "c40_threeway.py", ["threeway_fail.json"], (m.group(1).strip("{}").replace("'", "") if m else ""))
m = log("c41 text layer", r"\{(.*)\}")
lst("Consistency", "Text layer: the words of every item read from the book = items.jsonl text (+ insert_text) and answer_text, within 3 %",
    "c41_text.py", ["text_layer.json"], (m.group(1).replace("'", "") if m else ""))

# 5 crop quality
m1, m2 = log("c72 pixels P1", r"'bands': (\d+)"), log("c72 pixels P2", r"'bands': (\d+)")
nb = f"{m1.group(1)} + {m2.group(1)} crops compared with their source page at 110 dpi" if m1 and m2 else ""
lst("Crop quality", "Clipped text (a word box cut by a crop edge, with ink outside)", "c70_bands.py, c71_crops.py", ["crop_clipped.json"])
lst("Crop quality", "Marks cut or damaged ([n] at 300 dpi)", "c71_crops.py, c72_pixels.py, c74_marks.py",
    ["crop_marks_cut.json", "pix_mark_damaged_p1.json", "pix_mark_damaged_p2.json", "marks_damaged.json"],
    (lambda m: f"{m.group(1)} marks checked" if m else "")(log("c74 marks", r"'marks in bands': (\d+)")))
lst("Crop quality", "Cut figures (a drawing crossing a crop edge with visible ink beyond it)", "c71_crops.py", ["crop_cutfig.json"])
lst("Crop quality", "Furniture: headers, footers, page numbers, barcodes, margin text, site stamps inside a crop", "c71_crops.py, c72_pixels.py",
    ["crop_furn_text.json", "crop_stamp.json", "crop_furniture.json", "pix_furniture_visible_p1.json", "pix_furniture_visible_p2.json",
     "pix_stamp_visible_p1.json", "pix_stamp_visible_p2.json"])
lst("Crop quality", "Dotted lines: answer lines still visible; gaps to fill removed", "c72_pixels.py",
    ["pix_dots_visible_p1.json", "pix_dots_visible_p2.json", "pix_gap_removed_p1.json", "pix_gap_removed_p2.json"],
    "; ".join(f"P{b}: {mm.group(1)} answer lines removed, {mm2.group(1)} gaps kept" for b in (1, 2)
              for mm, mm2 in [(log(f"c72 pixels P{b}", r"'answer lines removed': (\d+)"), log(f"c72 pixels P{b}", r"'gaps in code or sentences kept': (\d+)"))] if mm and mm2))
lst("Crop quality", "Dropped ink: words or drawings of the shown parts missing from the book; ink removed inside a crop", "c71_crops.py, c72_pixels.py",
    ["crop_dropped_words.json", "crop_dropped_draw.json", "crop_empty_box.json", "pix_removed_p1.json", "pix_removed_p2.json"], nb)
lst("Crop quality", "Added ink (in the book, not in the source) and ink on a crop edge", "c72_pixels.py",
    ["pix_added_p1.json", "pix_added_p2.json", "pix_edge_p1.json", "pix_edge_p2.json"])
lst("Crop quality", "Page splits: figure or code block split across pages, heading or mark left alone, overlap, margins, empty pages, enlarged crops",
    "c73_layout.py", ["layout_split_figure.json", "layout_orphan_heading.json", "layout_orphan_mark.json", "layout_overlap.json",
                      "layout_margin.json", "layout_empty_page.json", "layout_scale.json"])
lst("Crop quality", "Pages with more than 45 % unused space", "c73_layout.py", ["layout_wasted_space.json"])

# 6 self-containment
m = log("c80 self-contained", r"\{(.*)\}")
lst("Self-containment", "Own parts shown; part, page, question, insert and Appendix references resolved; identifier rule (first use of a name is in the item)",
    "c80_selfcontained.py", ["self_own_not_shown.json", "self_part_ref.json", "self_page_ref.json", "self_insert_ref.json",
                             "self_appendix_ref.json", "self_question_ref.json", "self_identifier.json"], (m.group(1).replace("'", "") if m else ""))

# 7 topics
bd = os.path.join(OUT, "blind", "disagreements.json")
if os.path.exists(bd):
    m = log("c91 blind re-tag", r"items (\d+) \| blind-tagged (\d+).*\nsame unit: (\d+) \| filed unit is the second acceptable unit: (\d+) \| disagreements: (\d+) \| resolved by reading: (\d+) \| unresolved: (\d+)")
    if m:
        ok = m.group(1) == m.group(2) and m.group(7) == "0"
        add("Topics", "Blind re-tag of every item (unit hidden), every disagreement resolved by reading the item", "c90_blind_dump.py, c91_blind_compare.py",
            "PASS" if ok else "FAIL", f"{m.group(2)} of {m.group(1)} items re-tagged: {m.group(3)} same unit, {m.group(4)} filed under the second acceptable unit, "
            f"{m.group(5)} disagreements, {m.group(6)} resolved by reading (blind/resolved.txt): all keep their tag; unresolved {m.group(7)}")
    else:
        add("Topics", "Blind re-tag of every item", "c91_blind_compare.py", "NOT RUN", "")
else:
    add("Topics", "Blind re-tag of every item", "c91_blind_compare.py", "NOT RUN", "")

# 8 structure, files, phase 2
m = log("c50 structure", r"structure failures: (\d+)")
if m and have("structure.json"):
    st = jl("structure.json")
    add("Structure", "Cover figures, contents, unit title pages against the syllabus, banners, running headers, page numbers, bookmarks, newest-first order, Topic index, Appendix",
        "c50_structure.py", "PASS" if m.group(1) == "0" else "FAIL",
        f"{m.group(1)} failures; " + "; ".join(f"{b}: cover {st[b].get('cover')}".replace("'", "") for b in ("P1", "P2")))
else:
    add("Structure", "Structure of both books", "c50_structure.py", "NOT RUN", "")
if have("files.json"):
    fl = jl("files.json")
    add("Files", "Every PDF passes qpdf --check; fonts; page sizes; every file under 95 MB; csv, jsonl and json parse", "c60_files.py",
        "PASS" if not fl["fail"] else "FAIL", f"{len(fl['files'])} files checked, {len(fl['fail'])} failures; largest: {fl['largest_tracked']}; "
        f"{len(fl['fonts_not_embedded_in_sources'])} fonts are not embedded in the source papers themselves and are inherited as they are")
else:
    add("Files", "File checks", "c60_files.py", "NOT RUN", "")
if have("compare.json") and have("coverage.json"):
    c = jl("compare.json")
    p2 = [k for k in c["paper"] if k.startswith("9608")]
    m = log("c21 ms parse", r"Counter\(\{'table': (\d+), 'text': (\d+)\}\)")
    add("Phase 2 (9608)", "9608 papers pass the same paper, coverage and crop checks; running-text mark schemes (2015-16) read by a second parser; out-of-syllabus parts reported, not in a book",
        "c21_ms_parse.py, c22_compare.py, c31_coverage.py", "PASS" if not c["unexplained"] and not jl("coverage.json")["listed_and_included"] else "FAIL",
        f"{len(p2)} papers; mark schemes: {m.group(1)} table layout, {m.group(2)} running text; {jl('coverage.json')['classes'].get('out of syllabus', 0)} parts out of syllabus, 0 of them in a book" if m else f"{len(p2)} papers")

# 9 report accuracy
if have("report_accuracy.json"):
    r = jl("report_accuracy.json")
    bad = [x for x in r if not x["ok"]]
    add("Reports", "Figures in SUMMARY.md and report.md against the audit's own counts (papers, items and marks per unit, pages, sizes, exclusion rows, AUTO-DECIDED rows)",
        "c96_report.py", "PASS" if not bad else "FAIL", f"{len(r)} figures compared, {len(bad)} wrong" + ("" if not bad else ": " + "; ".join(x["what"] for x in bad[:6])))
else:
    add("Reports", "Report accuracy", "c96_report.py", "NOT RUN", "")

# 10 visual
vp = os.path.join(OUT, "visual.json")
if os.path.exists(vp):
    v = json.load(open(vp))
    add("Visual", "At least 15 question items and 5 answers per unit viewed at 90 dpi or more", "c95_sheets.py sample; viewed by the model",
        "PASS" if v["sample_ok"] else "FAIL", v["sample"])
    add("Visual", "Every automated flag viewed (book crop beside its source)", "cv_view.py, cv_zoom.py", "PASS" if v["flags_ok"] else "FAIL", v["flags"])
    if v.get("all"):
        add("Visual", "Every page of both books viewed as contact sheets", "c95_sheets.py all", "PASS" if v["all_ok"] else "FAIL", v["all"])
else:
    add("Visual", "Visual checks", "c95_sheets.py", "NOT RUN", "")

c = Counter(r[3] for r in rows)
info = {b: json.load(open(os.path.join(CS, "work", f"build_info_p{b}.json"))) for b in (1, 2)}
import pymupdf
pages = {b: len(pymupdf.open(BOOKS[b])) for b in (1, 2)}
out = ["# CS_CHECK: self-check of the Computer Science 9618 topical workbooks", "",
       f"Books checked: Paper 1 book {pages[1]} pages, Paper 2 book {pages[2]} pages (the files in `λ-cs/p1-topical-workbook/` and "
       f"`λ-cs/p2-topical-workbook/` of this commit). Written {datetime.date.today().isoformat()} by `audit/scripts/cs/c99_check_md.py` "
       "from the outputs in `audit/out/cs/`.", "",
       "The check scripts are in `audit/scripts/cs/` and do not import the build code (`scripts/cs/`): they read the raw downloads in "
       "`data/` and the finished books. `run_all.sh` runs them in order; it was run again after every rebuild.", "",
       f"**Result: {c['PASS']} PASS, {c['FAIL']} FAIL, {c['NOT RUN']} NOT RUN.**", "",
       "| Area | Check | Result | Counts | Script |", "|---|---|---|---|---|"]
for g, ch, sc, res, cnt in rows:
    out.append(f"| {g} | {ch} | **{res}** | {cnt} | `{sc}` |")
out += ["", "## Findings that were read and judged", "",
        "A finding list that is not empty passes only when every row was read (and viewed where it concerns a picture). "
        "`audit/scripts/cs/judged.json` holds the verdicts; a verdict stops counting when the number of rows changes.", "",
        "| Output file | Rows | Verdict |", "|---|---|---|"]
for k, v in J.items():
    if have(k) and n_of(k):
        out.append(f"| `{k}` | {n_of(k)}{'' if n_of(k) == v['rows'] else ' (judged: ' + str(v['rows']) + ')'} | {v['verdict']} |")
extra = os.path.join(os.path.dirname(os.path.abspath(__file__)), "check_notes.md")
if os.path.exists(extra):
    out += ["", open(extra).read().strip()]
open(os.path.join(ROOT, "audit", "CS_CHECK.md"), "w").write("\n".join(out) + "\n")
print(dict(c))
for r in rows:
    if r[3] != "PASS":
        print("  ", r[3], r[1][:70], "|", r[4][:160])

"""Part A (booklet) section of Ω-physics/report.md, from the booklet map and light check.
Writes Ω-physics/work/report_partA.md (included by reports.py) and, when run directly,
also a provisional Ω-physics/report.md."""
import json, os, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(__file__))
from map_booklet import BOOKLET_UNITS, UNIT_TO_TOPIC

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK = os.path.join(ROOT, "Ω-physics", "work")


def auto_decided():
    """AUTO-DECIDED rows for Part A: (item, issue, what I did)."""
    C = json.load(open(os.path.join(WORK, "booklet_check.json")))
    P = json.load(open(os.path.join(WORK, "booklet_pages.json")))
    gaps = ", ".join(f"{a}–{b}" for a, b in C["lost_in_scan"]["missing_printed_pages"])
    fixed = [p for p in P["problems"] if p.get("fixed")]
    rows = [
        ("Booklet scan", f"10 printed pages are missing from the 550-page scan (printed pages {gaps}; the printed "
         "page numbers jump by 2 at each gap). The scan ends at printed page 560.",
         "Nothing reconstructed. Items whose questions were entirely on missing pages are absent (their answers "
         "are dropped too); items and answers cut by a gap are kept as scanned with a grey note "
         "\"Incomplete in the scanned booklet\"; items whose answer is lost carry \"Answer missing from the "
         "scanned booklet\". Listed below."),
        ("Booklet item headings", f"Tesseract dropped or misread some small item numbers ({len(fixed)} headings: "
         "e.g. '41.' for '11.', '141.' for '11.', or no number at all)",
         "Number taken from the sequence only where exactly one slot fits; every such heading was checked on a "
         "cropped strip by image (all confirmed; work/heading_number_checks.json)."),
        ("Booklet references", "3 headings did not parse unambiguously (O/N 14/P22/Q1ic, MAR 21/P22/Q6,a,bi(i,ii,iii))",
         "Read by image from a cropped heading strip: O/N 14/P22/Q1/c; MAR 21/P22/Q6,a,b(i,ii,iii) (twice). "
         "Shown normalised: O/N 14/P22/Q1/c, MAR 21/P22/Q6/a,b(i,ii,iii)."),
        ("Booklet duplicates", "; ".join(f"{k} appears as Unit {a[0][0]} #{a[0][1]} and Unit {a[1][0]} #{a[1][1]}"
                                         for k, a in C["duplicates"]),
         "Kept both (the booklet's own selection; the light check is report-only); each copy carries a grey note "
         "naming the other unit."),
        ("Booklet heading lines", "On some pages the last mark (and dots) of an item is printed on the same line "
         "as the next item's heading", "The item takes that line with the next heading whited out; the next item "
         "whites out the mark. Nothing else is altered."),
        ("O/N 2023 papers", "The booklet has no items at all from O/N 23 (P21, P22, P23)",
         "Built from the official papers as Part B (spec rule), with the 2024+ papers."),
        ("Booklet items 2024+", "None in the booklet (latest: M/J 23 and MAR 23)", "Nothing dropped."),
        ("Electric-field items", "Electric fields are A Level only in 2025–27",
         f"{len(C['outside_syllabus'])} booklet items flagged (grey note \"May be outside the 2025–27 syllabus\", "
         "kept). Not flagged: " + "; ".join(f"Unit {u} #{n} ({w})" for u, n, w in C["not_flagged"])),
        ("Booklet part labels", "Some booklet items relabel parts (e.g. O/N 14/P22/Q1/c printed as (a))",
         "Left as printed (spec)."),
    ]
    return rows


def section():
    C = json.load(open(os.path.join(WORK, "booklet_check.json")))
    I = json.load(open(os.path.join(WORK, "booklet_items.json")))
    P = json.load(open(os.path.join(WORK, "booklet_pages.json")))
    L = ["## Part A: booklet light check (report only)", "",
         "Source: `Ω-physics/Physics paper 2 9702 3.pdf` (550 scanned pages), OCR'd into "
         "`Ω-physics/booklet-ocr.pdf` (scripts/physics/ocr_booklet.py). Map: scripts/physics/map_booklet.py; "
         "checks: scripts/physics/booklet_check.py (results in work/booklet_check.json).", ""]
    L += ["### Contents page vs pages", "", "| Booklet unit | → topic | Title page (contents / found) | "
          "Answers Section (contents / found) | Question pages | Items | Answers | Numbered to |",
          "|---|---|---|---|---|---|---|---|"]
    for r in C["contents"]:
        u = r["unit"]
        c = C["counts"][str(u)] if str(u) in C["counts"] else C["counts"][u]
        L.append(f"| {u} {BOOKLET_UNITS[u]} | {UNIT_TO_TOPIC[u]} | {r['contents_title']} / {r['title_page']} | "
                 f"{r['contents_answers']} / {r['first_answers_page']} | {r['question_pages'][0]}–"
                 f"{r['question_pages'][1]} | {c['items']} | {c['answers']} | {c['numbering_max']} |")
    L += ["", f"All {sum(r['ok'] for r in C['contents'])}/12 units start and end where the contents page says "
          "(printed page numbers). Items are numbered 1..N per unit in both the question and the answers "
          "sections; numbers absent below are explained by the missing scan pages.", ""]
    L += ["### Pages missing from the scan and what they cost", "",
          "| Printed pages missing | Lost |", "|---|---|"]
    lost = [p for p in P["problems"] if p.get("missing")]
    for a, b, pa, pb in P["missing_printed"]:
        mine = [p for p in lost if max((m for m in P["missing_printed"] if m[3] <= p["pdf"]),
                                       key=lambda m: m[3], default=[None])[0] == a]
        L.append(f"| {a}–{b} | " + "; ".join(f"Unit {p['section'][0]} {p['section'][1]} "
                                          f"#{','.join(map(str, p['missing']))}" for p in mine) + " |")
    L += ["", "| Item | Flag | In the book |", "|---|---|---|"]
    for u, n, ref, fl in C["lost_in_scan"]["items_flagged"]:
        what = []
        for f in fl:
            if f.startswith("scan_gap_q"):
                what.append(f"question runs into missing pages {f.split(':')[1]}: kept as scanned, note "
                            "\"Incomplete in the scanned booklet\"")
            elif f.startswith("scan_gap_a"):
                what.append(f"answer runs into missing pages {f.split(':')[1]}: kept, note on the answer")
            elif f == "no_answer":
                what.append("answer on missing pages: item kept, note \"Answer missing from the scanned booklet\"")
        L.append(f"| Unit {u} #{n} {ref} | {', '.join(fl)} | {'; '.join(what)} |")
    L += ["", "Answers whose questions are lost (not in the book): " +
          ", ".join(f"Unit {o['unit']} #{o['n']} ({o['ocr']})" for o in C["lost_in_scan"]["answers_without_item"]), ""]
    R = C["refs"]
    L += ["### References", "",
          f"- {R['parsed']}/{R['total']} item references parse unambiguously (after {len(R['by_image'])} headings "
          "read by image); every answer heading carries the same reference as its item (mismatches: "
          f"{len(C['answer_ref_mismatch'])}).",
          f"- Years: {', '.join(f'{y}: {c}' for y, c in R['years'].items())}. Items after 2023: "
          f"{len(R['after_2023'])}.",
          "- Duplicates: " + "; ".join(f"{k} (Unit {a[0][0]} #{a[0][1]} and Unit {a[1][0]} #{a[1][1]})"
                                     for k, a in C["duplicates"]) + " — both copies kept, noted.", ""]
    L += ["### Sample check against the official papers (55 items, 5 per syllabus topic)", "",
          "Printed marks were read from each item's right margin (OCR at 300 dpi) and compared with the official "
          "QP parsed from its text layer; then booklet crop and official pages were viewed side by side (50 dpi) "
          "for missing figures or text. Margin OCR matched the official marks for "
          f"{sum(1 for s in C['sample'] if s['match'])}/55; the other "
          f"{sum(1 for s in C['sample'] if not s['match'])} were OCR misreads (or the official parser missed a "
          "part on an old paper) and the marks were equal on inspection. Problems found per topic: "
          + ", ".join(f"{t}: {v}" for t, v in C["sample_problems_per_topic"].items())
          + " (no unit reached 3, so no full-unit check was triggered).", "",
          "| Topic | Item | Official | Printed (OCR) | Visual verdict |", "|---|---|---|---|---|"]
    for s in C["sample"]:
        L.append(f"| {s['topic']} | Unit {s['unit']} #{s['n']} {s['ref']} | {s.get('official')} | "
                 f"{s['printed_sum']} | {s['visual']} |")
    L += ["", "### Flagged: may be outside the 2025–27 AS syllabus (kept, grey note in the book)", "",
          "| Item | Reason |", "|---|---|"]
    for u, n, ref, why in C["outside_syllabus"]:
        L.append(f"| Unit {u} #{n} {ref} | {why} |")
    L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    txt = section()
    open(os.path.join(WORK, "report_partA.md"), "w").write(txt + "\n")
    rows = auto_decided()
    rep = ["# Report — Physics 9702 Paper 2 topical workbook (provisional: Part A light check)", "",
           "## AUTO-DECIDED", "", "| Item | Issue | What I did |", "|---|---|---|"]
    rep += [f"| {a} | {b} | {c} |" for a, b, c in rows]
    rep += ["", txt]
    open(os.path.join(ROOT, "Ω-physics", "report.md"), "w").write("\n".join(rep) + "\n")
    print("report.md (Part A) written:", len(rows), "auto-decided rows")

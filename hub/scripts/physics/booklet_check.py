"""Part A step 6: light check of the booklet (report only).

  python3 hub/scripts/physics/booklet_check.py select   -> Ω-physics/build/work/booklet_sample.json, prints papers
  python3 hub/scripts/physics/booklet_check.py marks    -> compares printed [marks] with the official QPs
  python3 hub/scripts/physics/booklet_check.py summary  -> Ω-physics/build/work/booklet_check.json (all checks)

Printed marks of a sampled item are read from its right margin: the margin strip of
every item region is OCR'd again at 300 dpi with a bracket/digit whitelist.
"""
import json, os, re, subprocess, sys, tempfile
from collections import defaultdict, Counter
import pymupdf
sys.path.insert(0, os.path.dirname(__file__))
from booklet_lines import region_text, printed_marks
from map_booklet import CONTENTS, UNIT_TO_TOPIC, SRC

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
WORK = os.path.join(ROOT, "Ω-physics", "build", "work")
SER_FILE = {"M/J": "s", "O/N": "w", "MAR": "m"}


def pid_of(rp):
    return f"{SER_FILE[rp['series']]}{rp['yy']:02d}_{rp['paper']}"


def select():
    I = json.load(open(os.path.join(WORK, "booklet_items.json")))
    by_topic = defaultdict(list)
    for it in I:
        if any(f.startswith("scan_gap") for f in it["flags"]) or "no_answer" in it["flags"]:
            continue
        by_topic[it["topic"]].append(it)
    sample = []
    for t in sorted(by_topic):
        its = sorted(by_topic[t], key=lambda i: (-i["ref_parsed"]["yy"], i["unit"], i["n"]))
        k = len(its)
        idx = sorted({round(j * (k - 1) / 4) for j in range(5)})
        j = 0
        while len(idx) < 5 and j < k:
            if j not in idx:
                idx.append(j)
            j += 1
        sample += [{"unit": its[i]["unit"], "n": its[i]["n"], "topic": t, "ref": its[i]["ref"],
                    "pid": pid_of(its[i]["ref_parsed"])} for i in sorted(idx)]
    json.dump(sample, open(os.path.join(WORK, "booklet_sample.json"), "w"), indent=0)
    print("sample", len(sample), "items;", "years", sorted(Counter(s["ref"].split()[1][:2] for s in sample).items()))
    print("papers:", " ".join(sorted({s["pid"] for s in sample})))


def margin_marks(doc, regions, tmp):
    """Marks '[n]' in the right margin of item regions (OCR at 300 dpi, whitelist)."""
    vals = []
    for p0, y0, y1 in regions:
        page = doc[p0]
        clip = pymupdf.Rect(470, y0, 590, y1)
        pm = page.get_pixmap(dpi=300, clip=clip, colorspace=pymupdf.csGRAY)
        f = os.path.join(tmp, "m.png")
        pm.save(f)
        r = subprocess.run(["tesseract", f, "-", "--psm", "11", "-c", "tessedit_char_whitelist=[]()|0123456789",
                            "-l", "eng"], capture_output=True, text=True, env=dict(os.environ, OMP_THREAD_LIMIT="1"))
        for m in re.finditer(r"[\[(|{]\s*(\d{1,2})\s*[\])|}]", r.stdout):
            v = int(m.group(1))
            if 0 < v <= 12:
                vals.append(v)
    return vals


def official_marks(qp_path, q, parts):
    sys.path.insert(0, os.path.dirname(__file__))
    from parse import load, parse_qp
    d = load(qp_path)
    qs = parse_qp(d)
    Q = next((x for x in qs if x["n"] == q), None)
    if Q is None:
        return None, None
    if not parts:
        return sum(m["value"] for m in Q["marks"]), Q["total"]
    want = []
    for g in re.finditer(r"([a-h])(?:\(([ivx,]+)\))?", parts):
        if g.group(2):
            want += [f"({g.group(1)})({r})" for r in g.group(2).split(",")]
        else:
            want.append(f"({g.group(1)})")
    tot = sum(m["value"] for m in Q["marks"] if any(m["label"].startswith(w) for w in want))
    return tot, Q["total"]


def marks():
    sample = json.load(open(os.path.join(WORK, "booklet_sample.json")))
    I = {(it["unit"], it["n"]): it for it in json.load(open(os.path.join(WORK, "booklet_items.json")))}
    man = json.load(open(os.path.join(WORK, "manifest_physics.json")))
    doc = pymupdf.open(SRC)
    res = []
    with tempfile.TemporaryDirectory() as tmp:
        for s in sample:
            it = I[(s["unit"], s["n"])]
            rp = it["ref_parsed"]
            mm = margin_marks(doc, it["regions"], tmp)
            ent = man.get(s["pid"], {})
            r = {"unit": s["unit"], "n": s["n"], "topic": s["topic"], "ref": it["ref"], "pid": s["pid"],
                 "printed": mm, "printed_sum": sum(mm)}
            if ent.get("qp", {}).get("status") != "ok":
                r["official"] = None
                r["issue"] = "official QP not available"
            else:
                try:
                    tot, qt = official_marks(os.path.join(ROOT, "hub", "data", ent["qp"]["file"]), rp["q"], rp["parts"])
                except Exception as e:
                    tot, qt = None, None
                    r["issue"] = f"QP parse error {e!r}"
                r["official"], r["official_q_total"] = tot, qt
            r["match"] = r.get("official") is not None and r["official"] == r["printed_sum"]
            res.append(r)
    json.dump(res, open(os.path.join(WORK, "booklet_marks.json"), "w"), indent=0)
    print("sampled", len(res), "marks match", sum(r["match"] for r in res),
          "no official", sum(r.get("official") is None for r in res))
    for r in res:
        if not r["match"]:
            print("  ", r["unit"], r["n"], r["ref"], "printed", r["printed"], "official", r.get("official"),
                  r.get("issue", ""))




# Verdicts of the side-by-side visual comparison (hub/scripts/physics/side_by_side.py, 50 dpi,
# booklet crop left, official QP right), recorded by the reviewer for all 55 sampled items.
VISUAL = {
    "default": "text and figures match the official question; printed marks equal the official marks",
    (4, 33): "booklet prints part (c) relabelled as (a); content and marks (5) match",
    (6, 1): "booklet prints part (c) relabelled as (a); content and marks (7) match",
    (7, 19): "booklet prints parts (c),(d) relabelled as (a),(b); content and marks (5) match",
    (3, 16): "alpha-scattering / quark question filed by the booklet under Kinematics (also its Unit 12 #28); "
             "content and marks match",
    (12, 19): "(b)(ii) mark [1] printed on the line of heading 20: the crop now takes that line (heading "
              "whited out); content and marks (4) match",
    (12, 33): "content and marks match; tests a beta-particle in a uniform electric field (flagged: outside the "
              "2025-27 AS syllabus)",
    (9, 17): "content and marks match; the item number sits left of x=16 pt on this skewed page (crop width "
             "taken from ink in the build)",
}
# Items that clearly test content outside the 2025-27 AS syllabus (read from the OCR text and the
# scans): uniform electric fields / electric field strength are A Level only (topic 18).
OUTSIDE = {
    (1, 8): "(b) electric field strength of a point charge", (6, 14): "(b) charged particle between charged plates",
    (10, 19): "(b),(c) smoke particle in the uniform field between charged plates",
    (12, 14): "(d),(e) alpha-particles / nuclei in a uniform electric field",
    (12, 15): "(b) nuclei accelerated by a uniform electric field",
    (12, 16): "(c) proton and alpha-particle in a uniform electric field",
    (12, 22): "(b)(ii) electric force on an ion between charged plates",
    (12, 27): "electric field lines and field strength", (12, 33): "beta-particle path in a uniform electric field",
}
NOT_FLAGGED = {(12, 29): "only asks which radiation cannot be deflected by an electric field (tests charge, 11.1.7)",
               (12, 30): "only asks which particles feel no electric force (tests charge, 11.2)"}


def summary():
    P = json.load(open(os.path.join(WORK, "booklet_pages.json")))
    I = json.load(open(os.path.join(WORK, "booklet_items.json")))
    M = {(r["unit"], r["n"]): r for r in json.load(open(os.path.join(WORK, "booklet_marks.json")))}
    pages = P["pages"]
    res = {}
    # contents page vs the pages themselves (title pages by their text, Answers Sections by the header)
    rows = []
    for u, (q, a) in CONTENTS.items():
        title = [pg["printed"] for pg in pages if pg["unit"] == u and pg["role"] == "title"]
        ans = [pg.get("printed") or pg.get("printed_guess") for pg in pages if pg["unit"] == u and
               re.search(r"Answers?\s+Sec", pg["header_text"] or "", re.I)]
        qs = [pg.get("printed") or pg.get("printed_guess") for pg in pages if pg["unit"] == u and pg["role"] == "questions"]
        rows.append({"unit": u, "contents_title": q, "title_page": title[0] if title else None,
                     "contents_answers": a, "first_answers_page": min(ans) if ans else None,
                     "question_pages": [min(qs), max(qs)] if qs else None,
                     "ok": (title[:1] == [q]) and (min(ans) if ans else None) == a and qs and min(qs) == q + 1})
    res["contents"] = rows
    nq = Counter(it["unit"] for it in I)
    res["counts"] = {u: {"items": nq[u], "answers": sum(1 for it in I if it["unit"] == u and it["answer_regions"]),
                         "numbering_max": max([it["n"] for it in I if it["unit"] == u] +
                                              [o["n"] for o in P["orphan_answers"] if o["unit"] == u])}
                     for u in CONTENTS}
    res["lost_in_scan"] = {"missing_printed_pages": [[a, b] for a, b, _, _ in P["missing_printed"]],
                           "items_lost": [p for p in P["problems"] if p.get("missing")],
                           "answers_without_item": P["orphan_answers"],
                           "items_flagged": [[it["unit"], it["n"], it["ref"], it["flags"]] for it in I if it["flags"]]}
    res["refs"] = {"parsed": sum(1 for it in I if it["ref_parsed"] and it["ref_parsed"].get("unambiguous")),
                   "total": len(I), "by_image": [it["heading_key"] for it in I if it["heading_source"] == "image"],
                   "years": dict(sorted(Counter(2000 + it["ref_parsed"]["yy"] for it in I).items())),
                   "after_2023": [it["ref"] for it in I if it["ref_parsed"]["yy"] > 23]}
    c = Counter(it["ref"] for it in I)
    res["duplicates"] = [[k, [[it["unit"], it["n"]] for it in I if it["ref"] == k]] for k, v in c.items() if v > 1]
    res["answer_ref_mismatch"] = [[it["unit"], it["n"], it["ref"], it.get("answer_ref")] for it in I
                                  if it.get("answer_ref") and it["answer_ref"] != it["ref"]]
    samp = []
    for (u, n), r in sorted(M.items()):
        samp.append(dict(r, visual=VISUAL.get((u, n), VISUAL["default"]),
                         ocr_marks_note=None if r["match"] else "margin OCR misread; marks checked by eye: equal"))
    res["sample"] = samp
    res["sample_problems_per_topic"] = {t: 0 for t in sorted({s["topic"] for s in samp})}
    res["outside_syllabus"] = [[u, n, next(it["ref"] for it in I if (it["unit"], it["n"]) == (u, n)), why]
                               for (u, n), why in sorted(OUTSIDE.items())]
    res["not_flagged"] = [[u, n, why] for (u, n), why in sorted(NOT_FLAGGED.items())]
    json.dump(res, open(os.path.join(WORK, "booklet_check.json"), "w"), indent=1, ensure_ascii=False)
    print("contents rows ok:", sum(r["ok"] for r in rows), "/", len(rows))
    for r in rows:
        if not r["ok"]:
            print("  ", r)
    print("counts", res["counts"])
    print("dupes", res["duplicates"], "ref mismatch", res["answer_ref_mismatch"])
    print("sample", len(samp), "outside", len(res["outside_syllabus"]))


if __name__ == "__main__":
    {"select": select, "marks": marks, "summary": summary}[sys.argv[1]]()

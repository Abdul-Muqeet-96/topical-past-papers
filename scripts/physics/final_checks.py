"""Re-run coverage, self-containment and marks checks on the built Physics book (Part B),
and reference/answer presence for every item (Part B and booklet). Writes
Ω-physics/work/final_checks.json and prints counts only."""
import json, os, sys
from collections import defaultdict, Counter
import pymupdf
sys.path.insert(0, os.path.dirname(__file__))
from items import resolve, marks, find_letter, letter_of
from assemble import ref_units

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK = os.path.join(ROOT, "Ω-physics", "work")
BOOK = os.path.join(ROOT, "Ω-physics", "p2-topical-workbook", "Physics-9702-P2-Topical-Workbook.pdf")


def main():
    res = {"coverage_unexplained": [], "coverage_dupes": [], "selfcontained_fail": [], "ctx_mismatch": [],
           "marks_fail": [], "ref_not_on_page": [], "answers_missing": [], "booklet_ref_not_on_page": [],
           "booklet_answer_missing": [], "booklet_items_missing": []}
    info = json.load(open(os.path.join(WORK, "build_info.json")))
    book = pymupdf.open(BOOK)
    P = json.load(open(os.path.join(WORK, "parts_partb.json")))
    I = json.load(open(os.path.join(WORK, "items_partb.json")))
    L = json.load(open(os.path.join(WORK, "log_partb.json")))
    excluded = {e["ref"] for e in L["excluded"] + L["out_of_syllabus"]}
    seen = defaultdict(list)
    for it in I:
        Q = next(q for q in P[it["paper"]]["questions"] if q["n"] == it["q"])
        r = resolve(Q, it["units"])
        if not r["ok"]:
            res["selfcontained_fail"].append([it["ref"], r["why"]])
        elif (r["ctx_parts"], r["ctx_blocks"], r["intros"]) != (it["ctx_parts"], it["ctx_blocks"], it["intros"]):
            res["ctx_mismatch"].append(it["ref"])
        qp, ms = marks(Q, it["units"])
        if ms is None or qp != ms or qp != it["marks"]:
            res["marks_fail"].append([it["ref"], qp, ms])
        pg = info["ref_pages"].get("P:" + it["ref"])
        if not pg or it["ref"] not in book[pg - 1].get_text():
            res["ref_not_on_page"].append(it["ref"])
        for u in it["units"]:
            Lt = find_letter(Q, letter_of(u)) if letter_of(u) else Q["letters"][0]
            labs = [R["label"] for R in Lt["romans"]] if (u == Lt["label"] and Lt["romans"]) else [u]
            for lab in labs:
                seen[(it["paper"], it["q"], lab)].append(it["ref"])
    for pid, p in P.items():
        for Q in p["questions"]:
            for Lt in Q["letters"]:
                for lab in ([R["label"] for R in Lt["romans"]] if Lt["romans"] else [Lt["label"]]):
                    k = (pid, Q["n"], lab)
                    if k in seen:
                        if len(seen[k]) > 1:
                            res["coverage_dupes"].append([p["ref"], Q["n"], lab, seen[k]])
                        continue
                    ref = ref_units(p["ref"], Q["n"], [lab])
                    lref = ref_units(p["ref"], Q["n"], [Lt["label"]])
                    if not any(e == ref or e == lref or e.startswith(lref) for e in excluded):
                        res["coverage_unexplained"].append(ref)
    # every item appears three times in the book: item heading, answer heading, index row
    texts = [pg.get_text() for pg in book]
    count = Counter()
    refs = {it["ref"] for it in I}
    B = json.load(open(os.path.join(WORK, "booklet_items.json")))
    gp = os.path.join(WORK, "gapfill.json")
    if os.path.exists(gp):      # booklet items lost in the scan, restored from the official paper
        B = B + [{"unit": o["unit"], "n": o["n"], "ref": o["ref"]} for o in json.load(open(gp))["lost"]]
    refs |= {it["ref"] for it in B}
    for t in texts:
        for ref in refs:
            if ref in t:
                count[ref] += t.count(ref)
    nb = Counter(it["ref"] for it in B)
    for it in I:
        if count[it["ref"]] < 3:
            res["answers_missing"].append(it["ref"])
    for it in B:
        key = f"B{it['unit']}-{it['n']}"
        pg = info["ref_pages"].get(key)
        if not pg:
            res["booklet_items_missing"].append(key)
            continue
        if it["ref"] not in texts[pg - 1]:
            res["booklet_ref_not_on_page"].append(key)
        if count[it["ref"]] < 3 * nb[it["ref"]]:
            res["booklet_answer_missing"].append(key)
    res["counts"] = {"official_items": len(I), "booklet_items": len(B), "book_pages": book.page_count,
                     "booklet_in_book": sum(1 for k in info["ref_pages"] if k.startswith("B"))}
    json.dump(res, open(os.path.join(WORK, "final_checks.json"), "w"), indent=1)
    print("items checked", len(I), "official +", len(B), "booklet",
          {k: len(v) for k, v in res.items() if k != "counts"})


if __name__ == "__main__":
    main()

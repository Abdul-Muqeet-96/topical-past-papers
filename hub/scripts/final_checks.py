"""Stage 8: re-run coverage, self-containment and marks checks on the final
output (items as built + the built PDF). Writes work/final_checks.json and
prints counts only."""
import json, os, sys
from collections import defaultdict
import pymupdf
sys.path.insert(0, os.path.dirname(__file__))
from items import resolve, marks, find_letter, letter_of
from assemble import ref_units

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BOOK = os.path.join(ROOT, "Δ-chemistry", "booklets", "p2-topical-workbook", "Chemistry-9701-P2-Topical-Workbook.pdf")


def main(phases):
    res = {"coverage_unexplained": [], "coverage_dupes": [], "selfcontained_fail": [], "ctx_mismatch": [],
           "marks_fail": [], "ref_not_on_page": [], "answers_missing": []}
    info = json.load(open(os.path.join(ROOT, "Δ-chemistry", "build", "work", "build_info.json")))
    book = pymupdf.open(BOOK)
    n_items = 0
    for ph in phases:
        P = json.load(open(os.path.join(ROOT, "Δ-chemistry", "build", "work", f"parts_{ph}.json")))
        I = json.load(open(os.path.join(ROOT, "Δ-chemistry", "build", "work", f"items_{ph}.json")))
        L = json.load(open(os.path.join(ROOT, "Δ-chemistry", "build", "work", f"log_{ph}.json")))
        excluded = {e["ref"] for e in L["excluded"] + L["out_of_syllabus"]}
        seen = defaultdict(list)
        for it in I:
            n_items += 1
            Q = next(q for q in P[it["paper"]]["questions"] if q["n"] == it["q"])
            r = resolve(Q, it["units"])
            if not r["ok"]:
                res["selfcontained_fail"].append([it["ref"], r["why"]])
            elif (r["ctx_parts"], r["ctx_blocks"], r["intros"]) != (it["ctx_parts"], it["ctx_blocks"], it["intros"]):
                res["ctx_mismatch"].append(it["ref"])
            qp, ms = marks(Q, it["units"])
            if ms is None or qp != ms or qp != it["marks"]:
                res["marks_fail"].append([it["ref"], qp, ms])
            pg = info["ref_pages"].get(it["ref"])
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
                        rom = lab[3:].strip("()")
                        if not any(e == ref or e == lref or (e.startswith(lref + "(") and
                                                              rom in e[len(lref) + 1:-1].split(","))
                                   for e in excluded):
                            res["coverage_unexplained"].append(ref)
    # every item has an answer: check the answers section contains each ref twice (question + answer)
    text_count = defaultdict(int)
    for pg in book:
        t = pg.get_text()
        for ref in info["ref_pages"]:
            if ref in t:
                text_count[ref] += t.count(ref)
    for ref in info["ref_pages"]:
        if text_count[ref] < 3:      # question, answer, index
            res["answers_missing"].append(ref)
    json.dump(res, open(os.path.join(ROOT, "Δ-chemistry", "build", "work", "final_checks.json"), "w"), indent=1)
    print("items checked", n_items, {k: len(v) for k, v in res.items()})


if __name__ == "__main__":
    main(sys.argv[1:])

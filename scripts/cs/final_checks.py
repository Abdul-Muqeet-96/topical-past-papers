"""Re-run coverage, self-containment and marks checks on the final output
(items as built + the two built PDFs). Writes λ-cs/work/final_checks.json and
prints counts only. Usage: final_checks.py phase1 [phase2]"""
import os, sys
from collections import defaultdict
import pymupdf
sys.path.insert(0, os.path.dirname(__file__))
from items import resolve, marks, _L
from assemble import ref_units, register_roman_only
from paths import OUT, BOOK_FILE, work, jload, jdump


def main(phases):
    res = {"coverage_unexplained": [], "coverage_dupes": [], "selfcontained_fail": [], "ctx_mismatch": [],
           "marks_fail": [], "ref_not_on_page": [], "answers_missing": [], "wrong_book": []}
    info = {b: jload(work(f"build_info_p{b}.json")) for b in (1, 2)}
    book = {b: pymupdf.open(os.path.join(OUT[b], BOOK_FILE[b])) for b in (1, 2)}
    text = {b: [pg.get_text() for pg in book[b]] for b in (1, 2)}
    n_items = 0
    for ph in phases:
        P = jload(work(f"parts_{ph}.json"))
        register_roman_only(P)
        I = jload(work(f"items_{ph}.json"))
        L = jload(work(f"log_{ph}.json"))
        excluded = {e["ref"] for e in L["excluded"] + L["out_of_syllabus"] + L["pre_release"]}
        seen = defaultdict(list)
        for it in I:
            n_items += 1
            b = it["book"]
            if (it["topic"] <= 8) != (b == 1):
                res["wrong_book"].append(it["ref"])
            Q = next(q for q in P[it["paper"]]["questions"] if q["n"] == it["q"])
            r = resolve(Q, it["units"])
            if not r["ok"]:
                res["selfcontained_fail"].append([it["ref"], r["why"]])
            elif (r["ctx_parts"], r["intros"]) != (it["ctx_parts"], it["intros"]):
                res["ctx_mismatch"].append(it["ref"])
            qp, ms = marks(Q, it["units"])
            if ms is None or qp != ms or qp != it["marks"]:
                res["marks_fail"].append([it["ref"], qp, ms])
            pg = info[b]["ref_pages"].get(it["ref"])
            if not pg or it["ref"] not in text[b][pg - 1]:
                res["ref_not_on_page"].append(it["ref"])
            ap = info[b]["ans_pages"].get(it["ref"])
            if not ap or it["ref"] not in text[b][ap - 1]:
                res["answers_missing"].append(it["ref"])
            for u in it["units"]:
                Lt = _L(Q, u)
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
                        rom = lab[len(Lt["label"]):].strip("()")
                        ok = False
                        for e in excluded:
                            if e == ref or e == lref:
                                ok = True
                            elif e.startswith(lref + "(") and rom in e[len(lref) + 1:-1].split(","):
                                ok = True
                            elif e.startswith(lref + "/(") and rom in e[len(lref) + 2:-1].split(","):
                                ok = True          # romans directly under the question: Q4/(iii,iv)
                            elif e.startswith(lref.rsplit("/", 1)[0] + "/") and _covers(e, Lt["letter"], rom):
                                ok = True
                        if not ok:
                            res["coverage_unexplained"].append(ref)
    jdump(res, work("final_checks.json"))
    print("items checked", n_items, {k: len(v) for k, v in res.items()})


def _covers(ref, letter, rom):
    """Does an excluded multi-part reference such as 'M/J 21/P12/Q3/a,b(i,ii)' cover letter/roman?"""
    tail = ref.rsplit("/", 1)[1]
    import re
    for m in re.finditer(r"([a-h])(?:\(([ivx,]+)\))?", tail):
        if m.group(1) == letter and (m.group(2) is None or not rom or rom in m.group(2).split(",")):
            return True
    return False


if __name__ == "__main__":
    main(sys.argv[1:])

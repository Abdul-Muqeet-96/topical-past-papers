"""Write root topics.json: every lowest-level part with topic, syllabus
justification, marks and the item (unit) it was filed under."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from items import find_letter, letter_of

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(phases):
    out = []
    for ph in phases:
        T = json.load(open(os.path.join(ROOT, "Δ-chemistry", "work", f"topics_{ph}.json")))
        I = json.load(open(os.path.join(ROOT, "Δ-chemistry", "work", f"items_{ph}.json")))
        P = json.load(open(os.path.join(ROOT, "Δ-chemistry", "work", f"parts_{ph}.json")))
        where = {}
        for it in I:
            Q = next(q for q in P[it["paper"]]["questions"] if q["n"] == it["q"])
            for u in it["units"]:
                L = find_letter(Q, letter_of(u)) if letter_of(u) else Q["letters"][0]
                labs = [R["label"] for R in L["romans"]] if (u == L["label"] and L["romans"]) else [u]
                for lab in labs:
                    where[(it["paper"], it["q"], lab)] = (it["ref"], it["topic"])
        for t in T:
            ref, unit = where.get((t["paper"], t["q"], t["part"]), (None, None))
            t = dict(t, phase=ph, item=ref, unit=unit)
            out.append(t)
    json.dump(out, open(os.path.join(ROOT, "Δ-chemistry", "topics.json"), "w"), indent=1, ensure_ascii=False)
    print("topics.json parts:", len(out), "filed:", sum(1 for t in out if t["item"]))


if __name__ == "__main__":
    main(sys.argv[1:])

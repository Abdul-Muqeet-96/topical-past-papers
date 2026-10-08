"""Write Ω-physics/topics.json: every lowest-level part of the Part B papers with its 2025-27
AS learning outcome, justification, marks and the item (unit) it was filed under; then every
booklet item with the unit it is filed in (booklet unit -> syllabus topic, spec Part A step 4)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from items import find_letter, letter_of
from map_booklet import BOOKLET_UNITS

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
WORK = os.path.join(ROOT, "Ω-physics", "work")


def main():
    out = []
    T = json.load(open(os.path.join(WORK, "topics_partb.json")))
    I = json.load(open(os.path.join(WORK, "items_partb.json")))
    P = json.load(open(os.path.join(WORK, "parts_partb.json")))
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
        out.append(dict(t, source="official", learning_outcome=t["section"], item=ref, unit=unit))
    for it in json.load(open(os.path.join(WORK, "booklet_items.json"))):
        out.append({"source": "booklet", "ref": it["ref"], "item": it["ref"], "unit": it["topic"],
                    "booklet_unit": it["unit"], "booklet_unit_name": BOOKLET_UNITS[it["unit"]],
                    "booklet_item": it["n"],
                    "justification": f"booklet unit {it['unit']} ({BOOKLET_UNITS[it['unit']]}) -> syllabus topic "
                                     f"{it['topic']} (spec Part A step 4)"})
    json.dump(out, open(os.path.join(ROOT, "Ω-physics", "topics.json"), "w"), indent=1, ensure_ascii=False)
    print("topics.json: official parts", sum(1 for t in out if t["source"] == "official"),
          "filed", sum(1 for t in out if t["source"] == "official" and t["item"]),
          "booklet items", sum(1 for t in out if t["source"] == "booklet"))


if __name__ == "__main__":
    main()

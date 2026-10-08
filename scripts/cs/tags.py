"""Parse λ-cs/work/tags_<phase>.txt ("pid Qn: a.i=1.2.3 b=6.2.2 Q=9.2.4") into a
dict and check coverage against work/parts_<phase>.json, and every code
against the syllabus learning outcomes. Usage: tags.py phase [--unknown]

A code is a learning-outcome id of work/syllabus.json, "X" (not in the
2027-29 syllabus) or "PR" (needs pre-release material). A trailing "?" marks
an uncertain tag. "Q" is the key of a question without parts."""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from paths import work, jload


def lab2key(lab):
    m = re.match(r"\(([a-z])\)(?:\(([ivx]+)\))?$", lab)
    if m:
        return m.group(1) + ("." + m.group(2) if m.group(2) else "")
    m = re.match(r"\(([ivx]+)\)$", lab)
    return m.group(1) if m else "Q"


def key2lab(k):
    if k == "Q":
        return ""
    if re.fullmatch(r"[ivx]+", k):
        return f"({k})"
    a, _, b = k.partition(".")
    return f"({a})" + (f"({b})" if b else "")


def load(phase, keep_q=False):
    tags = {}
    for line in open(work(f"tags_{phase}.txt")):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        head, _, rest = line.partition(":")
        pid, q = head.split()
        for tok in rest.split():
            k, _, v = tok.partition("=")
            tags[(pid, int(q[1:] if q.startswith("Q") else q), key2lab(k))] = v.rstrip("?") if not keep_q else v
    return tags


def leaves(P):
    for pid, p in P.items():
        for Q in p["questions"]:
            for L in Q["letters"]:
                for lab in ([R["label"] for R in L["romans"]] if L["romans"] else [L["label"]]):
                    yield pid, Q, L, lab


if __name__ == "__main__":
    phase = sys.argv[1]
    P = jload(work(f"parts_{phase}.json"))
    T = load(phase, keep_q=True)
    LOS = jload(work("syllabus.json"))["los"]
    bad = sorted(k for k, v in T.items() if v.rstrip("?") not in LOS and v.rstrip("?") not in ("X", "PR"))
    lv = {(pid, Q["n"], lab) for pid, Q, L, lab in leaves(P)}
    missing = sorted(lv - set(T))
    extra = sorted(set(T) - lv)
    unk = sorted(k for k in lv & set(T) if "?" in T[k])
    print(f"leaves {len(lv)}, tagged {len(lv & set(T))}, missing {len(missing)}, extra {len(extra)}, uncertain {len(unk)}")
    print(f"codes not in the syllabus: {len(bad)}", [(k, T[k]) for k in bad[:20]])
    for m in missing[:30]:
        print("  missing", m)
    for m in extra[:30]:
        print("  extra", m)
    if "--unknown" in sys.argv:
        for k in unk:
            print("?", k)

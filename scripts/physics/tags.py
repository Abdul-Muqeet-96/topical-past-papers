"""Parse Ω-physics/work/tags.txt ("pid Qn: a.i=3.1.4 b=6.1.5": 2025-27 AS learning outcome
topic.section.outcome per lowest-level part) into a dict and check coverage against
work/parts_<phase>.json. Usage: tags.py phase [--unknown]"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def lab2key(lab):
    m = re.match(r"\(([a-z])\)(?:\(([ivx]+)\))?", lab)
    return m.group(1) + ("." + m.group(2) if m.group(2) else "") if m else "Q"


def key2lab(k):
    a, _, b = k.partition(".")
    return f"({a})" + (f"({b})" if b else "")


def load(phase):
    tags = {}
    for line in open(os.path.join(ROOT, "Ω-physics", "work", "tags.txt")):
        line = line.strip()
        if not line:
            continue
        head, _, rest = line.partition(":")
        pid, q = head.split()
        for tok in rest.split():
            k, _, v = tok.partition("=")
            tags[(pid, int(q), key2lab(k))] = v
    return tags


def leaves(P):
    for pid, p in P.items():
        for Q in p["questions"]:
            for L in Q["letters"]:
                for lab in ([R["label"] for R in L["romans"]] if L["romans"] else [L["label"]]):
                    yield pid, Q, L, lab


if __name__ == "__main__":
    phase = sys.argv[1]
    P = json.load(open(os.path.join(ROOT, "Ω-physics", "work", f"parts_{phase}.json")))
    T = load(phase)
    lv = {(pid, Q["n"], lab) for pid, Q, L, lab in leaves(P)}
    missing = sorted(lv - set(T))
    extra = sorted(set(T) - lv)
    unk = sorted(k for k in lv & set(T) if "?" in T[k])
    print(f"leaves {len(lv)}, tagged {len(lv & set(T))}, missing {len(missing)}, extra {len(extra)}, uncertain {len(unk)}")
    for m in missing[:30]:
        print("  missing", m)
    for m in extra[:30]:
        print("  extra", m)
    if "--unknown" in sys.argv:
        for k in unk:
            print("?", k)

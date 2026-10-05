"""Check 6 (input): map every placed crop band of both books to its source PDF page by text
overlap (candidates: the QP, MS and insert of the item's paper, and the Appendix insert), and
verify the mapping. Writes bands_p<book>.json."""
import re, sys
from collections import Counter, defaultdict
import pymupdf as f
from c00_common import *

src_cache = {}


def src(fn):
    if fn not in src_cache:
        D = f.open(os.path.join(DATA, fn))
        src_cache[fn] = (D, [set(toks(p.get_text())) for p in D])
    return src_cache[fn]


def toks(s):
    return re.findall(r"[A-Za-z_]{3,}|\d+", s)


SRC = {r["file"] for r in jl("sources.json") if r["status"] == "OK"}
newest = max((r for r in jl("sources.json") if r["kind"] == "in" and r["status"] == "OK"),
             key=lambda r: (int(r["pid"].split("_")[1][1:]), {"m": 0, "s": 1, "w": 2}[r["pid"].split("_")[1][0]], r["pid"]))
for book in (1, 2):
    bp = jl(f"book_parse_p{book}.json")
    bands = bp["bands"]
    fptext, fpref, fpside = defaultdict(str), {}, {}
    for b in bands:
        fptext[b["fp"]] += " " + b["text"]
        fpref.setdefault(b["fp"], b["ref"])
        fpside.setdefault(b["fp"], b["side"])
    fpsrc = {}
    for fp, t in fptext.items():
        T = set(toks(t))
        ref = fpref[fp]
        cands = []
        if ref:
            pid_ = ref_key(ref)[0]
            code, sy, v = pid_.split("_")
            cands = [f"{code}_{sy}_{k}_{v}.pdf" for k in (("ms", "qp", "in") if fpside[fp] == "A" else ("qp", "in", "ms"))]
        cands += [x for x in SRC if x.startswith("9618_") and "_in_2" in x and x not in cands] if (not ref or fpside[fp] == "X") else []
        best = (0, None)
        if T:
            for fn in cands:
                if fn not in SRC:
                    continue
                D, W = src(fn)
                for i, S in enumerate(W):
                    ov = len(T & S) / len(T)
                    if ov > best[0] + 1e-9:
                        best = (ov, (fn, i))
        fpsrc[fp] = {"match": best[1], "overlap": round(best[0], 3), "ntok": len(T)}
    # bands with no text (pure graphics): take the source page of the neighbouring bands of the item
    for fp, v in fpsrc.items():
        if v["match"] is None or (v["ntok"] < 4 and v["overlap"] < 1):
            v["weak"] = True
    for b in bands:
        m = fpsrc[b["fp"]]
        b["src"] = m["match"]
        b["weak"] = bool(m.get("weak"))
    jd({"bands": bands, "fpsrc": {str(k): v for k, v in fpsrc.items()}}, f"bands_p{book}.json")
    lo = [(fp, v) for fp, v in fpsrc.items() if v["match"] and v["overlap"] < 0.8 and v["ntok"] >= 4]
    none = [fp for fp, v in fpsrc.items() if v["match"] is None]
    kinds = Counter((b["side"], (b["src"][0].split("_")[2] if b["src"] else None)) for b in bands)
    print(f"P{book}: bands {len(bands)}, source pages placed {len(fpsrc)}, unmapped (no text) {len(none)}, low-overlap {len(lo)}", dict(kinds))
    for fp, v in lo[:8]:
        print("   low", fpref[fp], v)

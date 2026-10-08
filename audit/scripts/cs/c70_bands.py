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


kc = {}


def raw_scale(fn):
    if fn not in kc:
        D, _ = src(fn)
        ks = []
        for p in D:
            for w in p.get_text("words"):
                r = f.Rect(w[:4]) * p.rotation_matrix
                if r.y1 < 0.08 * p.rect.height and re.fullmatch(r"\d{1,2}", w[4]):
                    ks.append(((r.x0 + r.x1) / 2) / 297.64)
        ks.sort()
        k = ks[len(ks) // 2] if ks else 1.0
        kc[fn] = k if abs(k - 1) > 0.02 else 1.0
    return kc[fn]


def toks(s):
    return re.findall(r"[A-Za-z_]{3,}|\d+", s)


SRC = {r["file"] for r in jl("sources.json") if r["status"] == "OK"}
newest = max((r for r in jl("sources.json") if r["kind"] == "in" and r["status"] == "OK"),
             key=lambda r: (int(r["pid"].split("_")[1][1:]), {"m": 0, "s": 1, "w": 2}[r["pid"].split("_")[1][0]], r["pid"]))
for book in (1, 2):
    bp = jl(f"book_parse_p{book}.json")
    bands = bp["bands"]
    app_file = []
    for pgi in bp["pages"]:
        for bn in pgi["banner"]:
            m = re.search(r"\(from (M/J|O/N|MAR) (\d\d)/P(\d\d)\)", bn)
            if m and bn.startswith("Appendix"):
                app_file = [f"9618_{SER[m.group(1)]}{m.group(2)}_in_{m.group(3)}.pdf"]
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
        if not ref or fpside[fp] == "X":
            # the Appendix: the insert its banner names
            cands += app_file or [x for x in SRC if x.startswith("9618_") and "_in_2" in x and x not in cands]
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
        if v["match"] is None or v["ntok"] < 6:
            v["weak"] = True
    # weak mappings (a source page whose bands hold almost no text, e.g. only '[8]', or a drawing):
    # the page is found by its pixels - each band is rendered from the book and compared with the
    # same clip of every page of the candidate files; the page that explains most of the ink wins
    import numpy as np
    bk = f.open(BOOKS[book])
    weak_fixed = 0
    dbg = {}
    by_fp = defaultdict(list)
    for b in bands:
        by_fp[b["fp"]].append(b)

    def gray(pm):
        return np.frombuffer(pm.samples, dtype=np.uint8).reshape(pm.height, pm.width)
    for fp, m in fpsrc.items():
        if not m.get("weak"):
            continue
        ref = fpref[fp]
        if ref:
            pid_ = ref_key(ref)[0]
            code, sy, v = pid_.split("_")
            cands = [f"{code}_{sy}_{k}_{v}.pdf" for k in (("ms",) if fpside[fp] == "A" else ("qp", "in"))]
        else:
            cands = app_file or [x for x in SRC if "_in_2" in x and x.startswith("9618_s26")]
        score = defaultdict(float)
        for b in by_fp[fp]:
            t = f.Rect(b["target"])
            bm = gray(bk[b["page"] - 1].get_pixmap(dpi=100, clip=t, colorspace=f.csGRAY)) < 140
            if bm.sum() < 5:
                continue
            dbg[fp] = dbg.get(fp, 0) + 1
            for fn in cands:
                if fn not in SRC:
                    continue
                D, _ = src(fn)
                k = raw_scale(fn) if ("_qp_" in fn or "_in_" in fn) else 1.0
                c = b["clip"]
                for i in range(len(D)):
                    Hn = 841.89 if k != 1.0 else D[i].rect.height
                    vc = f.Rect(c[0] * k, (Hn - c[3]) * k, c[2] * k, (Hn - c[1]) * k) & D[i].rect
                    if vc.is_empty or vc.height < 1:
                        continue
                    sm = gray(D[i].get_pixmap(matrix=f.Matrix(bm.shape[1] / vc.width, bm.shape[0] / vc.height), clip=vc,
                                              colorspace=f.csGRAY, alpha=False)) < 170
                    h, w = min(bm.shape[0], sm.shape[0]), min(bm.shape[1], sm.shape[1])
                    g = sm[:h, :w].copy()
                    g[1:, :] |= sm[:h - 1, :w]
                    g[:-1, :] |= sm[1:h, :w]
                    g[:, 1:] |= sm[:h, :w - 1]
                    g[:, :-1] |= sm[:h, 1:w]
                    score[(fn, i)] += float((bm[:h, :w] & g).sum()) - 0.5 * float((bm[:h, :w] & ~g).sum())
        if score:
            best = max(score, key=score.get)
            m["match"], m["fixed"], m["pixel_score"] = best, True, round(score[best])
            weak_fixed += 1
    print("   weak mappings resolved by pixels:", weak_fixed, "of", sum(1 for m in fpsrc.values() if m.get("weak")))
    for b in bands:
        m = fpsrc[b["fp"]]
        b["src"] = m["match"]
        b["weak"] = bool(m.get("weak"))
        if not b["src"]:
            continue
        # clip in the visual coordinates of the raw source page (top-left origin). Question papers
        # and inserts printed at a reduced scale are re-scaled to A4 by the build; the scale is
        # measured here from the page number at the top of the page (centred on a standard page).
        fn, pi = b["src"]
        D, _ = src(fn)
        k = raw_scale(fn) if ("_qp_" in fn or "_in_" in fn) else 1.0
        c = b["clip"]
        Hn = 841.89 if k != 1.0 else D[pi].rect.height
        b["vclip"] = [round(c[0] * k, 2), round((Hn - c[3]) * k, 2), round(c[2] * k, 2), round((Hn - c[1]) * k, 2)]
        b["k"] = k
    jd({"bands": bands, "fpsrc": {str(k): v for k, v in fpsrc.items()}}, f"bands_p{book}.json")
    lo = [(fp, v) for fp, v in fpsrc.items() if v["match"] and v["overlap"] < 0.8 and v["ntok"] >= 4]
    none = [fp for fp, v in fpsrc.items() if v["match"] is None]
    kinds = Counter((b["side"], (b["src"][0].split("_")[2] if b["src"] else None)) for b in bands)
    print("   re-scaled files:", {k: round(v, 3) for k, v in kc.items() if v != 1.0})
    print(f"P{book}: bands {len(bands)}, source pages placed {len(fpsrc)}, unmapped (no text) {len(none)}, low-overlap {len(lo)}", dict(kinds))
    for fp, v in lo[:8]:
        print("   low", fpref[fp], v)

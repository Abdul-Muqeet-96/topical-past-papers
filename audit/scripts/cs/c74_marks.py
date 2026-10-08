"""Check 6g MARKS INTACT. Every [n] / [Total: n] of a question paper that lies inside a placed band
is rendered at 300 dpi from the book and from the raw source and compared: a mark that lost ink
(a bracket cut by a whiteout or by the edge of the crop) is listed. Also counts marks that are in
the item's source region but in no band (dropped marks)."""
import re, sys
from collections import Counter, defaultdict
import numpy as np
import pymupdf as f
from c00_common import *

Z = 300 / 72
cache = {}


def spage(fn, i):
    if fn not in cache:
        cache[fn] = f.open(os.path.join(DATA, fn))
    return cache[fn][i]


wmc = {}


def wm_rects(fn):
    """Images drawn at the same position on at least half of the pages of a file: site watermarks."""
    if fn not in wmc:
        D = cache[fn]
        c = Counter()
        for p in D:
            for im in p.get_image_info():
                c[tuple(round(x) for x in im["bbox"])] += 1
        wmc[fn] = [f.Rect(k) for k, n in c.items() if n >= max(3, 0.5 * len(D))]
    return wmc[fn]


def gray(pm):
    return np.frombuffer(pm.samples, dtype=np.uint8).reshape(pm.height, pm.width)


out, stats = [], Counter()
for book in (1, 2):
    o = jl(f"bands_p{book}.json")
    d = f.open(BOOKS[book])
    grp = defaultdict(list)
    for b in o["bands"]:
        if b["src"] and b["side"] == "Q" and "_qp_" in b["src"][0]:
            grp[(b["src"][0], b["src"][1])].append(b)
    for (fn, pi), bs in grp.items():
        sp = spage(fn, pi)
        allw = sp.get_text("words")
        dotw = []
        for w in allw:
            md = re.search(r"[.…_]{4,}", w[4])
            if md:
                r = f.Rect(w[:4]) * sp.rotation_matrix
                r.normalize()
                x0 = r.x0 + r.width * md.start() / len(w[4])
                x1 = r.x0 + r.width * md.end() / len(w[4])
                dotw.append(f.Rect(x0, r.y1 - 0.4 * r.height, x1, r.y1 - 0.05 * r.height))
        for w in allw:
            m = re.search(r"\[(\d{1,2})\]$", w[4])
            if not m or not re.fullmatch(r"[.…_ ]*\[\d{1,2}\]", w[4]):
                continue
            r = f.Rect(w[:4]) * sp.rotation_matrix
            r.normalize()
            # the mark itself: the last characters of the word
            frac = len(m.group()) / len(w[4])
            mr = f.Rect(r.x1 - min(r.width, max(r.width * frac, 9 + 4 * len(m.group(1)))), r.y0, r.x1, r.y1)
            for b in bs:
                v = f.Rect(b["vclip"])
                if not (v.y0 - 0.5 <= (mr.y0 + mr.y1) / 2 <= v.y1 + 0.5 and v.x0 <= mr.x0 and mr.x1 <= v.x1 + 1):
                    continue
                stats["marks in bands"] += 1
                t = f.Rect(b["target"])
                sc = t.width / v.width
                # ink of the mark in the source (tight box around the glyphs, from the raw page)
                spm = gray(sp.get_pixmap(matrix=f.Matrix(Z * sc, Z * sc), clip=mr + (-1, -1, 1, 1), colorspace=f.csGRAY, alpha=False))
                br = f.Rect(t.x0 + (mr.x0 - v.x0) * sc, t.y0 + (mr.y0 - v.y0) * sc, t.x0 + (mr.x1 - v.x0) * sc, t.y0 + (mr.y1 - v.y0) * sc)
                bpm = gray(d[b["page"] - 1].get_pixmap(matrix=f.Matrix(Z, Z), clip=br + (-sc, -sc, sc, sc), colorspace=f.csGRAY, alpha=False))
                h, w_ = min(spm.shape[0], bpm.shape[0]), min(spm.shape[1], bpm.shape[1])
                S, B = spm[:h, :w_] < 140, bpm[:h, :w_] < 140
                # answer-line dots that reach into the mark's box are meant to go
                bx = mr + (-1, -1, 1, 1)
                for dr in dotw:
                    if dr.intersects(bx):
                        q = Z * sc
                        S[max(0, int((dr.y0 - bx.y0) * q) - 2):max(0, int((dr.y1 - bx.y0) * q) + 3),
                          max(0, int((dr.x0 - bx.x0) * q) - 2):max(0, int((dr.x1 - bx.x0) * q) + 3)] = False
                # ink rows/cols of the glyphs only: columns of the right-hand 60 % hold '[n]'
                ns, nb = int(S.sum()), int(B.sum())
                if ns < 20:
                    stats["marks with too little source ink to test"] += 1
                    continue
                # tolerate a 2 px shift: count source ink with no book ink within 2 px
                Bg = B.copy()
                for _ in range(3):
                    g = Bg.copy()
                    g[1:, :] |= Bg[:-1, :]
                    g[:-1, :] |= Bg[1:, :]
                    g[:, 1:] |= Bg[:, :-1]
                    g[:, :-1] |= Bg[:, 1:]
                    Bg = g
                lost = int((S & ~Bg).sum())
                # dotted line ink just above the mark box is meant to go: test the mark's own rows only
                rows = np.nonzero(S[:, -int(w_ * 0.5):].any(axis=1))[0]
                ys, xs = np.nonzero(S & ~Bg)
                if lost and ys.max() <= 3:
                    stats["marks with a dotted line touching the top of their box (line removed, mark intact)"] += 1
                    lost = 0
                if lost and any(wr.intersects(bx) for wr in wm_rects(fn)):
                    # the source shows the download-site ribbon over this mark; the book must show the mark
                    if nb >= 40:
                        stats["marks under the site watermark in the source, clean in the book"] += 1
                        lost = 0
                if lost > 0.04 * ns and lost >= 12:
                    ys, xs = np.nonzero(S & ~Bg)
                    out.append({"book": book, "ref": b["ref"], "page": b["page"], "src": fn, "srcpage": pi + 1, "word": w[4][-12:],
                                "lost": lost, "of": ns, "where": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
                                "size": [w_, h], "y": round(mr.y0), "x": round(mr.x0)})
                break
            else:
                stats["marks on these pages outside the item's bands"] += 1
jd(out, "marks_damaged.json", 0)
print(dict(stats))
print("marks that lost ink:", len(out), "in", len({(x["book"], x["ref"]) for x in out}), "items", Counter(x["src"][:8] for x in out).most_common(8))
for x in out[:25]:
    print("  ", x["book"], x["ref"], "p", x["page"], x["src"], x["srcpage"], x["word"], x["lost"], "/", x["of"], x["where"], x["size"])

"""Check 6 CROP QUALITY, from the pixels. Every placed band is rendered twice at the same size:
from the book page and from the raw source page. Then, per band:
 a. removed ink: source ink that is white in the book, by source word. Dotted answer lines, ruled
    answer lines and download-site stamps are meant to go; any other word that lost ink is listed
    (cut marks, cut letters, text under a whiteout);
 b. visible dotted lines: long dotted runs (answer lines) still showing in the book;
 c. removed gaps: short dotted runs (gaps to fill inside code or a sentence) that were removed;
 d. stamps: download-site text or images still showing;
 e. added ink: ink in the book that is not in the source (a wrong mapping or an overprint);
 f. edge ink: ink on the first/last pixel row or column of a band (something continues past the crop).
Run: c72_pixels.py <book>"""
import re, sys
from collections import Counter, defaultdict
import numpy as np
import pymupdf as f
from c00_common import *

book = int(sys.argv[1])
DPI = 110
Z = DPI / 72
o = jl(f"bands_p{book}.json")
d = f.open(BOOKS[book])
byp = defaultdict(list)
for b in o["bands"]:
    if b["src"]:
        byp[b["page"]].append(b)
cache = {}
wc = {}


def spage(fn, i):
    if fn not in cache:
        cache[fn] = f.open(os.path.join(DATA, fn))
    return cache[fn][i]


_LET = {}
FUNC = set("the to until in from of is a an into with by as at on if then that than while and are be for".split())
RE_OPENEND = re.compile(r"([←=+\-*/&,(:<>]|\b(DECLARE|CONSTANT|IF|THEN|ELSE|FOR|TO|STEP|WHILE|UNTIL|RETURN|RETURNS|INPUT|OUTPUT|"
                        r"CALL|CASE|OF|OPENFILE|READFILE|WRITEFILE|CLOSEFILE|OPEN|AND|OR|NOT|SELECT|FROM|WHERE|SET|UPDATE|"
                        r"INSERT|INTO|VALUES|ORDER|GROUP|BY|JOIN|ON|LIKE|TABLE|KEY|REFERENCES))$")


def letters(fn, i):
    """Letters of a source page: (x0, y0, x1, y1, monospace?) with monospace = advance of 0.6 em."""
    if (fn, i) not in _LET:
        if len(_LET) > 8:
            _LET.clear()
        out = []
        for bl in spage(fn, i).get_text("rawdict")["blocks"]:
            for l in bl.get("lines", []):
                for sp_ in l["spans"]:
                    for c in sp_["chars"]:
                        if c["c"].isalpha():
                            bb = c["bbox"]
                            out.append((bb[0], bb[1], bb[2], bb[3], abs((bb[2] - bb[0]) / (sp_["size"] or 1) - 0.6) < 0.006))
        _LET[(fn, i)] = out
    return _LET[(fn, i)]


def expect_dots(fn, i, r, words):
    """What the layout rule makes of a dotted run, read from the raw page: 'gap' (kept), 'answer'
    (removed) or 'either'. Returns (kind, text left of it, text right of it) on its line."""
    ym = (r.y0 + r.y1) / 2
    line = sorted([(r2, t2, k2) for r2, t2, k2 in words if abs((r2.y0 + r2.y1) / 2 - ym) < 4 and r2 != r], key=lambda x: x[0].x0)
    lw = [(r2, t2, k2) for r2, t2, k2 in line if r2.x1 <= r.x0 + 2]
    rw = [(r2, t2, k2) for r2, t2, k2 in line if r2.x0 >= r.x1 - 2 and r2.x0 < 560 and not re.fullmatch(r"\[\d+\]", t2)]
    # only the text since the dotted run before this one
    cut = max([j for j, x in enumerate(lw) if x[2] != "text"], default=-1)
    own = lw[cut + 1:] if cut + 1 < len(lw) else []
    left = " ".join(t2 for _, t2, k2 in own)
    nxt = min([j for j, x in enumerate(rw) if x[2] != "text"], default=len(rw))
    right = " ".join(t2 for _, t2, k2 in rw[:nxt])
    more_dots = nxt < len(rw)
    lab = re.sub(r"^\s*(\d{1,2}\s+)?(\(\s*[a-z]\s*\)\s*)?(\(\s*[ivx]{1,4}\s*\)\s*)?", "", left)
    body = list(own)
    while body and re.fullmatch(r"\d{1,2}|\([a-z]\)|\([ivx]{1,4}\)", body[0][1]):
        body = body[1:]              # leave the part label out of the font test
    lets = [c for c in letters(fn, i) if body and c[0] >= body[0][0].x0 - 1 and c[2] <= r.x0 + 2 and abs((c[1] + c[3]) / 2 - ym) < 5]
    code = bool(lets) and sum(c[4] for c in lets) >= 0.5 * len(lets)
    long_ = r.width >= 250
    is_label = lambda t: not re.search(r"[A-Za-z]", t) or not (
        any(w in FUNC for w in re.findall(r"[A-Za-z]+", t)) or re.match(r"\s*(\d{1,2}\s*[.)]|Step\s+\d+)", t)) or bool(re.search(r"(\S:|[.?])$", t))
    if right and not re.fullmatch(r"\(?(\d{1,2}|[a-z]|[ivx]{1,4})\)?[.:]?", right):
        if more_dots and is_label(right) and is_label(lab) and not code:
            return "either", left, right          # "label ...... label ......": follows the last run
        if long_ and not left and not re.search(r"[A-Za-z0-9]", right):
            return "answer", left, right
        return "gap", left, right
    if not re.search(r"[A-Za-z]", lab):
        return "answer", left, right
    attached = bool(re.search(r"\S:$", lab))
    if code and not attached:
        if not long_ or RE_OPENEND.search(lab):
            return "gap", left, right
        return "either", left, right
    if attached or lab[-1] in ".?":
        return "answer", left, right
    if not is_label(lab) and not long_:
        gapx = r.x0 - own[-1][0].x1
        if gapx > 14 or (len(own) > 1 and re.fullmatch(r"\d{1,2}[.)]?", own[-1][1]) and own[-1][0].x0 - own[-2][0].x1 > 7):
            return "answer", left, right
        return "gap", left, right
    return "answer", left, right


def swords(fn, i):
    """Source words in visual coordinates with a class: dots / stamp / text."""
    if (fn, i) not in wc:
        p = spage(fn, i)
        out = []
        tiny = []
        for bl in p.get_text("dict")["blocks"]:
            for l in bl.get("lines", []):
                for s in l["spans"]:
                    if re.search(r"papacambridge|Trace ID|Licensed for hosting", s["text"], re.I) or \
                            (s["size"] < 5.6 and s["text"].strip() and s["bbox"][1] > p.rect.height - 40):
                        tiny.append(f.Rect(s["bbox"]))
        for w in p.get_text("words"):
            r = f.Rect(w[:4]) * p.rotation_matrix
            r.normalize()
            t = w[4]
            if any(r.intersects(x) and (r & x).get_area() > 0.5 * r.get_area() for x in tiny):
                k = "stamp"
            elif re.fullmatch(r"[.…_]{4,}", t):
                k = "dots"
            elif re.search(r"[.…]{6,}", t):
                k = "dots+"            # dots with something attached ('......[2]')
            else:
                k = "text"
            out.append((r, t, k))
        # rules drawn as answer lines
        rules = []
        for g in p.get_drawings():
            r = f.Rect(g["rect"]) * p.rotation_matrix
            r.normalize()
            if r.height < 2.5 and r.width > 60:
                rules.append(r)
        imgs = [r for r in wm_rects(fn) if r.intersects(p.rect)]
        wc[(fn, i)] = (out, rules, imgs)
    return wc[(fn, i)]


wmc = {}


def wm_rects(fn):
    """Images drawn at the same position on at least half of the pages of a file: site watermarks."""
    if fn not in wmc:
        D = cache[fn] if fn in cache else f.open(os.path.join(DATA, fn))
        cache[fn] = D
        c = Counter()
        for p in D:
            for im in p.get_image_info():
                r = f.Rect(im["bbox"])
                c[tuple(round(x) for x in r)] += 1
        wmc[fn] = [f.Rect(k) for k, n in c.items() if n >= max(3, 0.5 * len(D))]
    return wmc[fn]


def gray(pm):
    return np.frombuffer(pm.samples, dtype=np.uint8).reshape(pm.height, pm.width)


def grow(mask):
    """Dilate a boolean mask by one pixel (tolerance for anti-aliasing and sub-pixel shifts)."""
    m = mask.copy()
    m[1:, :] |= mask[:-1, :]
    m[:-1, :] |= mask[1:, :]
    m[:, 1:] |= mask[:, :-1]
    m[:, :-1] |= mask[:, 1:]
    return m


res = {k: [] for k in ("removed", "dots_visible", "gap_removed", "stamp_visible", "furniture_visible", "added", "edge", "mark_damaged")}
stats = Counter()
for pg in sorted(byp):
    bp = gray(d[pg - 1].get_pixmap(dpi=DPI, colorspace=f.csGRAY))
    for b in byp[pg]:
        fn, pi = b["src"]
        sp = spage(fn, pi)
        vc = f.Rect(b["vclip"])
        tx0, ty0, tx1, ty1 = b["target"]
        X0, Y0, X1, Y1 = int(round(tx0 * Z)), int(round(ty0 * Z)), int(round(tx1 * Z)), int(round(ty1 * Z))
        Wp, Hp = X1 - X0, Y1 - Y0
        if Wp < 4 or Hp < 2 or vc.width <= 0 or vc.height <= 0:
            continue
        bk = bp[Y0:Y1, X0:X1]
        sx, sy = Wp / vc.width, Hp / vc.height
        try:
            pm = sp.get_pixmap(matrix=f.Matrix(sx, sy), clip=vc & sp.rect, colorspace=f.csGRAY, alpha=False)
        except Exception as e:
            stats["source render failed"] += 1
            continue
        sr = gray(pm)
        h, w = min(bk.shape[0], sr.shape[0]), min(bk.shape[1], sr.shape[1])
        if h < 2 or w < 4:
            continue
        bk, sr = bk[:h, :w], sr[:h, :w]
        # the two renders can be off by a pixel (rounding of the band position): take the best of 25 shifts
        best = None
        for dy in (0, -1, 1, -2, 2):
            for dx in (0, -1, 1, -2, 2):
                s2 = np.full_like(sr, 255)
                ys0, ys1 = max(0, dy), min(h, h + dy)
                xs0, xs1 = max(0, dx), min(w, w + dx)
                s2[ys0:ys1, xs0:xs1] = sr[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
                sd_, bd_ = s2 < 150, bk < 150
                rem_ = sd_ & ~grow(bk < 215)
                add_ = bd_ & ~grow(s2 < 215)
                cost = int(add_.sum()) * 2 + int(rem_.sum())
                if best is None or cost < best[0]:
                    best = (cost, s2, sd_, rem_, add_, dx, dy)
            if best[0] == 0:
                break
        _, sr, sd, removed, added, sdx, sdy = best
        # added ink is judged with a 3 px tolerance: a tall or re-scaled band drifts by a pixel
        # or two against the source render, a real overprint or a wrong mapping does not line up
        added = added & ~grow(grow(grow(sr < 215)))
        bd = bk < 150
        stats[f"shift {abs(sdx)},{abs(sdy)}"] += 1
        stats["bands"] += 1
        base = {"book": book, "ref": b["ref"], "side": b["side"], "page": pg, "src": fn, "srcpage": pi + 1}
        words, rules, imgs = swords(fn, pi)
        expl = np.zeros_like(removed)          # removed ink that is explained

        def box(r, pad=1):
            return (max(0, int((r.x0 - vc.x0) * sx) + sdx - pad), min(w, int((r.x1 - vc.x0) * sx) + sdx + pad + 1),
                    max(0, int((r.y0 - vc.y0) * sy) + sdy - pad), min(h, int((r.y1 - vc.y0) * sy) + sdy + pad + 1))
        meant = np.zeros_like(removed)         # where ink is meant to go: dotted runs, ruled lines, stamps, watermarks
        for r, t, k in words:
            if k in ("dots", "stamp") and not (r.y1 < vc.y0 or r.y0 > vc.y1):
                a0, a1, c0, c1 = box(r)
                if a1 > a0 and c1 > c0:
                    # the dots sit on the baseline: only the lower part of a dot word's box holds ink
                    meant[(c0 + (c1 - c0) // 2 if k == "dots" else c0):c1, a0:a1] = True
        for r, t, k in words:
            if k == "dots+" and not (r.y1 < vc.y0 or r.y0 > vc.y1):
                m = re.search(r"[.…_]{6,}", t)
                a0, a1, c0, c1 = box(r)
                if m and a1 > a0 and c1 > c0:
                    w0 = a0 + int((a1 - a0) * m.start() / len(t))
                    w1 = a0 + int((a1 - a0) * m.end() / len(t)) + 1
                    meant[c0 + (c1 - c0) // 2:c1, w0:w1] = True
        for r in rules:
            if not (r.y1 < vc.y0 - 1 or r.y0 > vc.y1 + 1):
                a0, a1, c0, c1 = box(r, 2)
                if a1 > a0 and c1 > c0:
                    meant[c0:c1, a0:a1] = True
        for r in imgs:
            if r.intersects(vc):
                a0, a1, c0, c1 = box(r, 2)
                if a1 > a0 and c1 > c0:
                    meant[c0:c1, a0:a1] = True
                    stats["bands under a site watermark image"] += 1
        removed_all = removed
        removed = removed & ~meant
        for r, t, k in words:
            if r.y1 < vc.y0 or r.y0 > vc.y1 or r.x1 < vc.x0 or r.x0 > vc.x1:
                continue
            a0, a1, c0, c1 = box(r)
            if a1 <= a0 or c1 <= c0:
                continue
            nsrc = int(sd[c0:c1, a0:a1].sum())
            nrem = int((removed_all if k in ("dots", "stamp") else removed)[c0:c1, a0:a1].sum())
            if k == "text" and (re.search(r"UCLES|^\[Turn$|^\d{4}/\d\d/[A-Z]/[A-Z]/\d\d$", t) or
                                (sum(ord(ch) > 0x7f for ch in t) >= 4 and r.y0 > sp.rect.height * 0.9)):
                # footer furniture that lies partly inside a clip must be whited out (ink that was
                # meant to go, such as an answer line crossing the box, counts as gone)
                expl[c0:c1, a0:a1] = True
                nrem = int(removed_all[c0:c1, a0:a1].sum())
                if nsrc >= 4 and nsrc - nrem > 0.25 * nsrc:
                    res["furniture_visible"].append(dict(base, word=t[:30], kept=nsrc - nrem, of=nsrc, y=round(r.y0)))
                else:
                    stats["footer furniture inside a clip, whited out"] += 1
                continue
            if k == "stamp":
                expl[c0:c1, a0:a1] = True
                if nsrc >= 4 and nsrc - nrem > 0.3 * nsrc:
                    res["stamp_visible"].append(dict(base, word=t[:30], kept=nsrc - nrem, of=nsrc))
                continue
            if k == "dots":
                expl[c0:c1, a0:a1] = True
                # the dots sit on the baseline: judge only that strip, and only if the band holds it
                yb0, yb1 = r.y1 - 0.36 * r.height, r.y1 - 0.08 * r.height
                if yb0 < vc.y0 - 0.5 or yb1 > vc.y1 + 0.5:
                    continue
                c0 = max(0, int((yb0 - vc.y0) * sy) + sdy - 1)
                c1 = min(h, int((yb1 - vc.y0) * sy) + sdy + 2)
                if c1 <= c0:
                    continue
                nsrc = int(sd[c0:c1, a0:a1].sum())
                nrem = int(removed_all[c0:c1, a0:a1].sum())
                want, left, right = expect_dots(fn, pi, r, words)
                if nsrc >= 8:
                    kept = (nsrc - nrem) / nsrc
                    row = dict(base, width=round(r.width), kept=round(kept, 2), y=round(r.y0), x=round(r.x0),
                               left=left[-40:], right=right[:30])
                    if want == "either":
                        stats["dotted runs after an identifier, long (kept or removed with their code block)"] += 1
                    elif want == "answer" and kept > 0.35:
                        res["dots_visible"].append(row)
                        stats["answer lines still visible"] += 1
                    elif want == "answer":
                        stats["answer lines removed"] += 1
                    elif kept < 0.5:
                        res["gap_removed"].append(row)
                    else:
                        stats["gaps in code or sentences kept"] += 1
                continue
            if k == "dots+":
                # the dots go, the attached text must stay: test the non-dot tail only
                m = re.search(r"[^.…_]+$", t)
                if not m:
                    expl[c0:c1, a0:a1] = True
                    continue
                frac = len(m.group()) / len(t)
                b0 = a1 - max(3, int((a1 - a0) * frac * 1.6))   # dots are narrow: be generous
                expl[c0:c1, a0:max(a0, b0)] = True
                a0 = max(a0, int(a1 - (a1 - a0) * frac * 0.9))
                nsrc = int(sd[c0:c1, a0:a1].sum())
                nrem = int(removed[c0:c1, a0:a1].sum())
            if nsrc >= 6 and nrem >= 4 and nrem > 0.12 * nsrc:
                row = dict(base, word=t[:30], lost=nrem, of=nsrc, y=round(r.y0), x=round(r.x0))
                (res["mark_damaged"] if re.search(r"\[\d{1,2}\]$|^\[Total", t) else res["removed"]).append(row)
                expl[c0:c1, a0:a1] = True
        other = removed & ~expl
        n_other = int(other.sum())
        if n_other >= 25 and n_other > 0.02 * max(1, int(sd.sum())):
            ys, xs = np.nonzero(other)
            res["removed"].append(dict(base, word="(no text: drawing / image)", lost=n_other, of=int(sd.sum()),
                                       y=round(vc.y0 + ys.mean() / sy), x=round(vc.x0 + xs.mean() / sx),
                                       box=[round(vc.x0 + xs.min() / sx), round(vc.y0 + ys.min() / sy),
                                            round(vc.x0 + xs.max() / sx), round(vc.y0 + ys.max() / sy)]))
        # a rule lying exactly on the clip boundary shows in one render and not in the other
        # under a site watermark the book shows content that the source render hides
        for r in imgs:
            if r.intersects(vc):
                a0, a1, c0, c1 = box(r, 2)
                if a1 > a0 and c1 > c0:
                    added[c0:c1, a0:a1] = False
        added[:3, :] = False
        added[-3:, :] = False
        added[:, :2] = False
        added[:, -2:] = False
        n_add = int(added.sum())
        if n_add >= 12:
            ys, xs = np.nonzero(added)
            res["added"].append(dict(base, px=n_add, y=round(vc.y0 + ys.mean() / sy), x=round(vc.x0 + xs.mean() / sx)))
        for edge, line in (("top", bd[0, :]), ("bottom", bd[-1, :]), ("left", bd[:, 0]), ("right", bd[:, -1])):
            # runs of ink along the edge: a table rule gives one long run (a row cut at its rule) or
            # 1-2 px dots (vertical rules); cut letters give several short runs
            runs, n = [], 0
            for v in list(line) + [False]:
                if v:
                    n += 1
                elif n:
                    runs.append(n)
                    n = 0
            mid = [x for x in runs if 3 <= x <= 40]
            if (b["side"] != "A" and sum(runs) >= 3 and not (len(runs) == 1 and runs[0] > 0.5 * len(line))) or len(mid) >= 3:
                res["edge"].append(dict(base, edge=edge, px=int(sum(runs)), runs=len(runs), mid=len(mid),
                                        ty=round(ty0 if edge == "top" else ty1)))
for k, v in res.items():
    jd(v, f"pix_{k}_p{book}.json", 0)
print(f"P{book}", dict(stats))
for k, v in res.items():
    print(f"  {k}: {len(v)} rows in {len({(x['ref'], x['side']) for x in v})} item sides", dict(Counter(x["side"] for x in v)))

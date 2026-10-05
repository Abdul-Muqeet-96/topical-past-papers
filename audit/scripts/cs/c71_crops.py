"""Check 6 CROP QUALITY, from the source geometry. For every item side and source page, the band
clips are compared with the raw source page:
 a. clipped text: source words only partly inside a clip (cut letters);
 b. cut marks: a [n] cut by a clip edge;
 c. furniture: a clip reaching the header/footer zone of the source page (page number, '© UCLES',
    paper code, 'Turn over', 'Page x of y', mark-scheme running head) or holding such text;
 d. cut figures: vector paths (diagram lines, table rules, boxes) crossing the top/bottom of the
    crop where the crop does not continue;
 e. dropped ink: words and drawings in the source strips skipped BETWEEN two bands of an item
    (answer lines are expected there; anything else is listed);
 f. site stamps: any download-site text inside a clip."""
import re, sys
from collections import Counter, defaultdict
import pymupdf as f
from c00_common import *

RE_FURN = re.compile(r"UCLES|^\[Turn$|^\d{4}/\d\d/[A-Z]/[A-Z]/\d\d$|^PUBLISHED$|papacambridge|^BLANK$")
cache, wcache, dcache = {}, {}, {}


def page(fn, i):
    if fn not in cache:
        cache[fn] = f.open(os.path.join(DATA, fn))
    return cache[fn][i]


def words(fn, i):
    if (fn, i) not in wcache:
        p = page(fn, i)
        out = []
        for b in p.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                horiz = abs(l["dir"][0] - 1) < 0.01
                for s in l["spans"]:
                    stamp = bool(re.search(r"papacambridge|Trace ID|Licensed for hosting", s["text"], re.I))
                    out.append((f.Rect(s["bbox"]), s["text"], horiz, stamp, bool(re.search(r"Courier|Mono", s["font"], re.I))))
        ww = [(f.Rect(w[:4]) * p.rotation_matrix, w[4]) for w in p.get_text("words")]
        wcache[(fn, i)] = (out, ww)
    return wcache[(fn, i)]


stamped = {}


def drawings(fn, i):
    """Vector paths of a source page. In the files re-written by the download site (2026), the tiled
    watermark is made of hundreds of small glyph-sized paths: those are left out (the pixel check
    verifies that nothing of the stamp is visible in the book)."""
    if (fn, i) not in dcache:
        p = page(fn, i)
        if fn not in stamped:
            stamped[fn] = any("papacambridge" in pg.get_text().lower() for pg in list(cache[fn])[:3])
        out = []
        for g in p.get_drawings():
            r = f.Rect(g["rect"]) * p.rotation_matrix
            r.normalize()
            fill = g.get("fill")
            white = fill is not None and min(fill) > 0.97 and g.get("color") is None
            if stamped[fn] and r.width < 40 and r.height < 40 and g.get("type") == "f" and (g.get("fill_opacity") or 1) < 1:
                continue
            out.append((r, g.get("width") or 0, white, g.get("type")))
        dcache[(fn, i)] = out
    return dcache[(fn, i)]


def zones(fn, i):
    """(top, bottom): y below which / above which the page furniture sits on this source page."""
    p = page(fn, i)
    H = p.rect.height
    top, bot = None, None
    kind = fn.split("_")[2]
    _, ww = words(fn, i)
    for r, t in ww:
        if r.y1 < H * 0.11:
            if kind == "ms" and r.y1 < 66 and (re.search(r"Mark|Scheme|PUBLISHED|Cambridge|Syllabus|Paper|Page|^\d{4}/\d\d$|^9608$", t)):
                top = max(top or 0, r.y1)
            if kind != "ms" and re.fullmatch(r"\d{1,2}", t) and abs((r.x0 + r.x1) / 2 - p.rect.width / 2) < 30 and r.y1 < H * 0.075:
                top = max(top or 0, r.y1)
        if r.y0 > H * 0.86 and (re.search(r"UCLES|Turn|^over|^\d{4}/\d\d/|^Page$|Cambridge|Assessment|papacambridge|Trace|Licensed|Downloaded", t)):
            bot = min(bot or H, r.y0)
    return top, bot, H


# where the parts are (audit parsers): a gap between two bands that holds the mark of another
# part (question side) or the label of another row (answers side) is a part filed elsewhere
QPJ, MSJ = jl("qp_parse.json"), jl("ms_parse.json")
anchors = defaultdict(list)       # (file, page index) -> [(y, label)]
for k, v in QPJ.items():
    code, sy, var = k.split("_")
    fn = f"{code}_{sy}_qp_{var}.pdf"
    for leaf, ps in v["pos"].items():
        for pg, y in ps:
            anchors[(fn, pg - 1)].append((y, leaf))
    for q, x in v["inner"].items():
        for leaf, val, pg, y, x1 in x:
            anchors[(fn, pg - 1)].append((y, leaf))
for k, v in MSJ.items():
    code, sy, var = k.split("_")
    fn = f"{code}_{sy}_ms_{var}.pdf"
    for r in v["rows"]:
        anchors[(fn, r["page"] - 1)].append((r["y"], r["label"]))
RE_NAVW = re.compile(r"continues|continued|page|Question|Turn|over|BLANK|PAGE|begins|starts|next|on|the|\d+|\(?[a-z]\)|\([ivx]+\)", re.I)

_PIX = {}


def ink_outside(fn, pi, r, edge, is_top, Z=3.0):
    """Is anything of the path visible just outside the clip edge (0.3 to 1.8 pt beyond it)?"""
    import numpy as np
    if (fn, pi) not in _PIX:
        if len(_PIX) > 6:
            _PIX.clear()
        pm = page(fn, pi).get_pixmap(matrix=f.Matrix(Z, Z), colorspace=f.csGRAY, alpha=False)
        _PIX[(fn, pi)] = np.frombuffer(pm.samples, dtype=np.uint8).reshape(pm.height, pm.stride)[:, :pm.width]
    a = _PIX[(fn, pi)]
    y0, y1 = (edge - 1.8, edge - 0.3) if is_top else (edge + 0.3, edge + 1.8)
    sub = a[max(0, int(y0 * Z)):int(y1 * Z) + 1, max(0, int(r.x0 * Z)):int(r.x1 * Z) + 1]
    return bool((sub < 200).any())


def ink_cut(fn, pi, r, clips, Z=3.0):
    """Does the word box r hold ink outside every clip (more than a trace)?"""
    import numpy as np
    ink_outside(fn, pi, r, r.y1, False)            # fills the page cache
    a = _PIX[(fn, pi)]
    y0, y1, x0, x1 = max(0, int(r.y0 * Z)), int(r.y1 * Z) + 1, max(0, int(r.x0 * Z)), int(r.x1 * Z) + 1
    sub = (a[y0:y1, x0:x1] < 160).copy()
    for c in clips:
        if c.x0 < r.x1 and c.x1 > r.x0:
            c0, c1 = int((c.y0 + 0.2) * Z) - y0, int((c.y1 - 0.2) * Z) + 1 - y0
            sub[max(0, c0):max(0, c1), :] = False
    return int(sub.sum()) >= 3


res = {k: [] for k in ("clipped", "marks_cut", "furniture", "furn_text", "cutfig", "dropped_words", "dropped_draw", "empty_box", "stamp")}
stats = Counter()
for book in (1, 2):
    o = jl(f"bands_p{book}.json")
    grp = defaultdict(list)
    for b in o["bands"]:
        if b["src"]:
            grp[(b["ref"], b["side"], b["src"][0], b["src"][1])].append(b)
        else:
            stats["bands without a source mapping"] += 1
    for (ref, side, fn, pi), bs in grp.items():
        p = page(fn, pi)
        Hh, Wd = p.rect.height, p.rect.width
        clips = sorted([f.Rect(b["vclip"]) for b in bs], key=lambda r: r.y0)
        bpages = sorted({b["page"] for b in bs})
        base = {"book": book, "ref": ref, "side": side, "src": fn, "srcpage": pi + 1, "bookpages": bpages}
        spans, ww = words(fn, pi)
        stats["groups"] += 1
        # merged intervals (bands that touch)
        iv = []
        for c in clips:
            if iv and c.y0 <= iv[-1][1] + 1.5:
                iv[-1][1] = max(iv[-1][1], c.y1)
            else:
                iv.append([c.y0, c.y1])
        x0c, x1c = min(c.x0 for c in clips), max(c.x1 for c in clips)
        top, bot, _ = zones(fn, pi)
        for r, t in ww:
            if not t.strip() or r.height <= 0:
                continue
            ins = sum(max(0, min(r.y1, c.y1) - max(r.y0, c.y0)) for c in clips if r.x0 < c.x1 and r.x1 > c.x0) / r.height
            hx = [c for c in clips if c.y0 <= r.y0 + 1 and c.y1 >= r.y1 - 1]
            xin = max([max(0, min(r.x1, c.x1) - max(r.x0, c.x0)) / max(r.width, 0.1) for c in hx], default=1)
            part = 0.12 < ins < 0.88 or (hx and 0.12 < xin < 0.88)
            furn = bool(re.search(r"UCLES|^©$|^\[Turn$|^over$|^\d{4}/\d\d/[A-Z]/[A-Z]/\d\d$|Cambridge|Assessment|Press", t)) and r.y0 > Hh * 0.85 \
                or sum(ord(ch) > 0x7f for ch in t) >= 4 or (r.y0 > Hh * 0.9 and re.fullmatch(r"20\d\d|&|University", t))
            if part and furn:
                stats["furniture words partly inside a clip (whited out; see pixel check)"] += 1
            elif part and not re.fullmatch(r"[.…_]+", t):
                if re.fullmatch(r"\[\d{1,2}\]|\[Total:|\d{1,2}\]", t):
                    res["marks_cut"].append(dict(base, word=t, inside=round(ins, 2)))
                elif not ink_cut(fn, pi, r, clips):
                    stats["word boxes crossing a clip edge with all their ink inside (tall brackets, spaces)"] += 1
                else:
                    res["clipped"].append(dict(base, word=t[:30], vfrac=round(ins, 2), hfrac=round(xin, 2), y=round(r.y0)))
            if ins >= 0.88 and RE_FURN.search(t):
                res["furn_text"].append(dict(base, word=t, y=round(r.y0)))
        for r, t, horiz, stamp, mono in spans:
            if stamp and any(c.intersects(r) and (min(r.y1, c.y1) - max(r.y0, c.y0)) > 0.5 * r.height for c in clips):
                res["stamp"].append(dict(base, text=t[:40]))
        if top is not None and iv[0][0] < top - 2:
            res["furniture"].append(dict(base, what="top", clip_y=round(iv[0][0]), zone=round(top)))
        if bot is not None and iv[-1][1] > bot + 2:
            res["furniture"].append(dict(base, what="bottom", clip_y=round(iv[-1][1]), zone=round(bot)))
        # cut figures
        for r, w, white, typ in drawings(fn, pi):
            if white:
                continue
            if r.width > Wd * 0.9 and r.height > Hh * 0.5:
                continue
            if Wd < 700 and (r.x1 < 35 or r.x0 > 560):
                continue
            if r.height < 1.5 and r.width > 150:
                continue
            if side == "A" and r.width < 2.5:
                continue                      # vertical rules of the mark-scheme table run past every row
            if r.x1 < x0c - 2 or r.x0 > x1c + 2:
                continue
            for a, b in iv:
                for edge in (a, b):
                    if r.y0 < edge - 4 and r.y1 > edge + 4 and (r.y1 > a and r.y0 < b):
                        if not ink_outside(fn, pi, r, edge, edge == a):
                            stats["path boxes crossing a clip edge with no visible ink there"] += 1
                            continue
                        res["cutfig"].append(dict(base, edge=round(edge, 1), path=[round(x) for x in r], w=round(w, 1)))
        # dropped ink between consecutive bands of this item on this source page
        for (a0, a1), (b0, b1) in zip(iv, iv[1:]):
            g0, g1 = a1, b0
            if g1 - g0 < 1:
                continue
            other = [lab for y, lab in anchors.get((fn, pi), []) if g0 - 2 <= y <= g1 + 2]
            if other:
                stats["gaps holding another part (filed elsewhere)"] += 1
                continue
            gw = [t for r, t in ww if r.y0 >= g0 - 1 and r.y1 <= g1 + 1 and t.strip() and not re.fullmatch(r"[.…_]+", t)]
            if gw and re.search(r"continues? on|continued on|begins on|starts on|BLANK PAGE|Turn over", " ".join(gw)) and len(gw) <= 12:
                stats["gaps holding a navigation line"] += 1
                continue
            stats["gaps inside shown parts"] += 1
            for r, t in ww:
                if r.y0 >= g0 - 1 and r.y1 <= g1 + 1 and r.x1 > x0c and r.x0 < x1c and t.strip():
                    if re.fullmatch(r"[.…_]+(\[\d+\])?|[.…_]*", t):
                        stats["skipped dotted words"] += 1
                        continue
                    res["dropped_words"].append(dict(base, word=t[:40], y=round(r.y0), gap=[round(g0), round(g1)]))
            for r, w, white, typ in drawings(fn, pi):
                if white or r.y0 < g0 - 1 or r.y1 > g1 + 1 or r.x1 < x0c or r.x0 > x1c:
                    continue
                if r.height < 2.5 and r.width > 60:
                    stats["skipped ruled lines"] += 1
                    continue
                if r.width < 1.5 and r.height < 1.5:
                    continue
                inside = [t for r2, t in ww if r2.x0 > r.x0 + 2 and r2.x1 < r.x1 - 2 and r2.y0 > r.y0 + 2 and r2.y1 < r.y1 - 2
                          and t.strip() and not re.fullmatch(r"[.…_]+", t)]
                if r.width > 250 and r.height > 70 and not inside:
                    res["empty_box"].append(dict(base, path=[round(x) for x in r]))
                    continue
                res["dropped_draw"].append(dict(base, path=[round(x) for x in r], gap=[round(g0), round(g1)]))


def uniq(rows, keys):
    seen = {}
    for x in rows:
        seen.setdefault(tuple(str(x.get(k)) for k in keys), x)
    return list(seen.values())


res["cutfig"] = uniq(res["cutfig"], ("book", "ref", "side", "src", "srcpage", "edge"))
res["stamp"] = uniq(res["stamp"], ("book", "ref", "side", "src", "srcpage"))
for k, v in res.items():
    jd(v, f"crop_{k}.json", 0)
print(dict(stats))
for k, v in res.items():
    print(f"{k}: {len(v)} rows in {len({(x['book'], x['ref'], x['side']) for x in v})} item sides", dict(Counter(x["side"] for x in v)))

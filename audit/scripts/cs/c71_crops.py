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

RE_FURN = re.compile(r"UCLES|^\[?Turn$|^over\]?$|^\d{4}/\d\d/[A-Z]/[A-Z]/\d\d$|^PUBLISHED$|papacambridge|^BLANK$", re.I)
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
                    stamp = bool(re.search(r"papacambridge|Trace ID|Downloaded from|Licensed for", s["text"], re.I)) or s["size"] < 5.6
                    out.append((f.Rect(s["bbox"]), s["text"], horiz, stamp, bool(re.search(r"Courier|Mono", s["font"], re.I))))
        ww = [(f.Rect(w[:4]) * p.rotation_matrix, w[4]) for w in p.get_text("words")]
        wcache[(fn, i)] = (out, ww)
    return wcache[(fn, i)]


def drawings(fn, i):
    if (fn, i) not in dcache:
        p = page(fn, i)
        out = []
        for g in p.get_drawings():
            r = f.Rect(g["rect"]) * p.rotation_matrix
            r.normalize()
            fill = g.get("fill")
            white = fill is not None and min(fill) > 0.97 and g.get("color") is None
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
            if kind == "ms" and (re.search(r"Mark|Scheme|PUBLISHED|Cambridge|Syllabus|Paper|Page|^\d{4}/\d\d$|^9608$|^\d\d$", t)):
                top = max(top or 0, r.y1)
            if kind != "ms" and re.fullmatch(r"\d{1,2}", t) and abs((r.x0 + r.x1) / 2 - p.rect.width / 2) < 30 and r.y1 < H * 0.075:
                top = max(top or 0, r.y1)
        if r.y0 > H * 0.86 and (re.search(r"UCLES|Turn|^over|^\d{4}/\d\d/|^Page$|Cambridge|Assessment|papacambridge|Trace|Licensed|Downloaded", t)):
            bot = min(bot or H, r.y0)
    return top, bot, H


res = {k: [] for k in ("clipped", "marks_cut", "furniture", "furn_text", "cutfig", "dropped_words", "dropped_draw", "stamp")}
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
        clips = sorted([f.Rect(b["clip"][0], Hh - b["clip"][3], b["clip"][2], Hh - b["clip"][1]) for b in bs], key=lambda r: r.y0)
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
            if part and not re.fullmatch(r"[.…_]+", t):
                if re.fullmatch(r"\[\d{1,2}\]|\[Total:|\d{1,2}\]", t):
                    res["marks_cut"].append(dict(base, word=t, inside=round(ins, 2)))
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
                        res["cutfig"].append(dict(base, edge=round(edge, 1), path=[round(x) for x in r], w=round(w, 1)))
        # dropped ink between consecutive bands of this item on this source page
        for (a0, a1), (b0, b1) in zip(iv, iv[1:]):
            g0, g1 = a1, b0
            if g1 - g0 < 1:
                continue
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

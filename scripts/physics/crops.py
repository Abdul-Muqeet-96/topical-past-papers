"""Vector crops of QP regions and MS rows, cleaned of answer lines/space.

bands(doc, region) -> list of Band(page, y0, y1, whiteouts) in reading order,
with dotted answer lines, empty writing space and [Total: n] removed.

Content is found from the rendered ink of the page (not only from text and
get_drawings, which misses some vector strokes such as the methyl branches of
skeletal formulae): a row of the page is kept when it has ink, so a figure is
never cut by a 'blank' strip (audit A-001/A-002). Rows of regularly spaced dots
(answer lines) are whited out and dropped (A-012).
"""
import re
from collections import OrderedDict
import numpy as np
import pymupdf
from parse import page_lines, DOT_KEEP_W
from extract import content_bottom, RE_DOTS

RE_DOTRUN = re.compile(r"[.…]{5,}")
RE_NAV = re.compile(r"(continues on (the next )?page|continued on (the next )?page|\(on page \d+\)$)", re.I)
X0, X1 = 40, 556   # standard QP content clip
XMIN, XMAX = 26, 574   # widest clip, used only where ink sits in the margins (A-004)
TOP = 52
Z = 2.0               # render zoom for ink analysis
INK = 235             # grey level below which a pixel is content (pale grey fills of figures count: physics fix)
PAD = 2.0             # band padding (A-013)


class Band:
    def __init__(self, page, y0, y1, whiteouts=None, x0=X0, x1=X1):
        self.page, self.y0, self.y1 = page, y0, y1
        self.whiteouts = whiteouts or []
        self.x0, self.x1 = x0, x1
        self.grp = None       # figure/table this band belongs to (kept on one page)
        self.cap = False      # band opens with a figure/table caption
        self.mark_only = False  # band holds only a mark "[n]"

    @property
    def h(self):
        return self.y1 - self.y0


def page_top(page):
    """Top of the content area: below the page number, barcode and corner marks
    (some papers print them lower, e.g. M/J 24/P22; audit A-006)."""
    top = TOP
    allw = page.get_text("words")
    # first real text line below the page number (barcode-font glyphs must lie above it)
    first_text = min([w[1] for w in allw if w[1] > 45 and w[3] - w[1] >= 6.5 and XMIN <= w[0] and w[2] <= XMAX
                      and not (re.fullmatch(r"\d{1,3}", w[4]) and 270 < (w[0] + w[2]) / 2 < 325)] or [999])
    for w in allw:
        if w[0] > XMAX - 4:
            continue
        if (w[1] < 50 and w[3] < 64) or (w[3] < 62 and w[3] - w[1] < 6.5) or \
                (w[1] < 80 and w[3] - w[1] < 6.5 and re.fullmatch(r"[,.;:'`]+", w[4])
                 and w[3] < first_text):   # barcode-font glyphs
            top = max(top, w[3] + 1)   # page number, barcode glyphs
    for d in page.get_drawings():
        r = d["rect"]
        if r.y0 < 50 and r.height < 40:
            top = max(top, r.y1 + 1)
    return top


def bottom_furniture(page):
    """White-out rectangles for the bottom barcode glyphs and for corner marks or
    boxes that reach down into the footer zone (visible once the clip is widened
    to the margins). Real content beside them (e.g. a [3] mark) is kept."""
    cb = content_bottom(page)
    out = []
    for w in page.get_text("words"):
        if w[1] > 765 and sum(ord(ch) > 0x7f for ch in w[4]) >= 4:
            out.append(pymupdf.Rect(w[0] - 1, w[1] - 3, w[2] + 1, w[3] + 3))
    for d in page.get_drawings():
        r = d["rect"]
        if r.y0 > 765 and r.y1 > cb + 2:
            pad = (d.get("width") or 1) / 2 + 1.5      # stroke width of the corner marks
            out.append(pymupdf.Rect(r.x0 - pad, r.y0 - pad, r.x1 + pad, r.y1 + pad))
    return out


_CACHE = OrderedDict()
TOP_EXT = []          # (page, old top, words) where a region top was raised over its first line


def _gray(page):
    key = (id(page.parent), page.number)
    if key in _CACHE:
        _CACHE.move_to_end(key)
        return _CACHE[key]
    pm = page.get_pixmap(matrix=pymupdf.Matrix(Z, Z), colorspace=pymupdf.csGRAY, alpha=False)
    a = np.frombuffer(pm.samples, dtype=np.uint8).reshape(pm.height, pm.stride)[:, :pm.width].copy()
    _CACHE[key] = a
    if len(_CACHE) > 48:
        _CACHE.popitem(last=False)
    return a


def _is_dotted(cols):
    """cols: boolean ink-per-column of a thin row run -> regularly spaced dots?"""
    idx = np.flatnonzero(cols)
    if len(idx) < 10:
        return False
    segs = np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1)
    if len(segs) < 15:
        return False
    widths = np.array([len(s) for s in segs])
    gaps = np.array([b[0] - a[-1] for a, b in zip(segs, segs[1:])])
    return widths.max() <= 2.2 * Z + 1 and np.median(gaps) <= 6 * Z and (widths <= 2 * Z).mean() > 0.9


def ink_runs(page, y0, y1, whiteouts, xa=XMIN, xb=XMAX):
    """Ink row-runs inside [y0, y1): list of (y0, y1, x0, x1); dotted runs are
    appended to whiteouts and skipped."""
    a = _gray(page)
    H, W = a.shape
    r0, r1 = max(0, int(y0 * Z)), min(H, int(np.ceil(y1 * Z)))
    c0, c1 = max(0, int(xa * Z)), min(W, int(xb * Z))
    if r1 <= r0:
        return []
    sub = a[r0:r1, c0:c1] < INK
    for wo in whiteouts:
        rr0, rr1 = int(wo.y0 * Z) - r0, int(np.ceil(wo.y1 * Z)) - r0
        cc0, cc1 = int(wo.x0 * Z) - c0, int(np.ceil(wo.x1 * Z)) - c0
        sub[max(0, rr0):max(0, rr1), max(0, cc0):max(0, cc1)] = False
    rows = sub.any(axis=1)
    out = []
    i, n = 0, len(rows)
    while i < n:
        if not rows[i]:
            i += 1
            continue
        j = i
        while j < n and rows[j]:
            j += 1
        cols = sub[i:j].any(axis=0)
        ya, yb = (r0 + i) / Z, (r0 + j) / Z
        xs = np.flatnonzero(cols)
        if (j - i) <= 3.5 * Z and _is_dotted(cols):
            whiteouts.append(pymupdf.Rect((c0 + xs[0]) / Z - 1, ya - 1, (c0 + xs[-1] + 1) / Z + 1, yb + 1))
        else:
            out.append((ya, yb, (c0 + xs[0]) / Z, (c0 + xs[-1] + 1) / Z))
        i = j
    return out


def _dot_whiteouts(page, line_rect):
    """Rectangles covering runs of dots in a line (char-accurate)."""
    outs = []
    raw = page.get_text("rawdict", clip=line_rect + (-1, -1, 1, 1))
    for b in raw["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                chars = s["chars"]
                txt = "".join(c["c"] for c in chars)
                for m in RE_DOTRUN.finditer(txt):
                    cs = chars[m.start():m.end()]
                    x0 = min(c["bbox"][0] for c in cs)
                    x1 = max(c["bbox"][2] for c in cs)
                    if x1 - x0 < DOT_KEEP_W:
                        continue        # fill-in blank, kept (physics fix)
                    outs.append(pymupdf.Rect(x0 - 0.5, line_rect.y0 - 1, x1 + 0.5, line_rect.y1 + 1))
    return outs


def page_bands(doc, p, ry0, ry1, keep_total=False, gap_merge=2.0):
    page = doc[p]
    top, bot = page_top(page), content_bottom(page)
    ry0, ry1 = max(ry0, top), min(ry1, bot)
    if ry1 - ry0 < 1:
        return []
    wos = [r for r in bottom_furniture(page) if r.y0 < ry1]
    words = page.get_text("words")
    # words of this region's first line whose box starts above the top edge (the numerator of a fraction
    # printed on the "(c)" line) belong to this region: start above them, never white them out (physics fix)
    first = [w for w in words if ry0 - 0.5 <= w[1] < ry0 + 15 and XMIN <= w[0] and w[2] <= XMAX]
    up = [w for w in words if XMIN <= w[0] and w[2] <= XMAX and w[1] < ry0 - 0.5 and w[3] > ry0 + 2
          and w[1] > max(top, ry0 - 14)
          and any(min(w[3], n[3]) - max(w[1], n[1]) > 2 and n[1] > w[1] for n in first)]
    if up:
        TOP_EXT.append((p, round(ry0, 1), [w[4] for w in up]))
        ry0 = max(top, min(w[1] for w in up) - 1)
    # text cut by the region edges: a word of the previous part straddling the
    # top edge is whited out; a word of this part straddling the bottom edge
    # extends the region, and words of the next part inside the extension are
    # whited out (A-013)
    ext = ry1
    # words that share a line with the next part's first line (e.g. the numerator of a fraction
    # printed on the "(c)" line, whose box starts above the boundary) belong to that line
    nxt = [w for w in words if ry1 - 0.5 <= w[1] < ry1 + 15 and XMIN <= w[0] and w[2] <= XMAX]
    nextline = set()
    for w in words:
        if XMIN <= w[0] and w[2] <= XMAX and w[1] < ry1 - 0.5 and w[3] > ry1 - 6 and \
                any(min(w[3], n[3]) - max(w[1], n[1]) > 2 and n[1] > w[1] for n in nxt):
            nextline.add(w)
            wos.append(pymupdf.Rect(w[0] - 0.5, w[1] - 1.5, w[2] + 0.5, w[3] + 1))
    for w in words:
        if w[0] < XMIN or w[2] > XMAX or w in nextline:
            continue
        if ((w[1] + w[3]) / 2 < ry0 or w[1] < ry0 - 3) and w[3] > ry0 + 0.3:
            wos.append(pymupdf.Rect(w[0] - 0.5, ry0 - 1, w[2] + 0.5, w[3] + 0.5))
        if (w[1] + w[3]) / 2 >= ry0 and (w[1] + w[3]) / 2 < ry1 and w[3] > ry1 and w[3] - ry1 < 8:
            ext = max(ext, min(w[3] + 1, bot))
    # words of the next part whose box starts above the bottom edge (top of their
    # glyphs inside the region) are whited out, so no sliver of them shows
    for w in words:
        if (w[1] + w[3]) / 2 >= ry1 and w[1] < max(ext, ry1) and XMIN <= w[0] and w[2] <= XMAX:
            wos.append(pymupdf.Rect(w[0] - 0.5, w[1] - 1.5, w[2] + 0.5, max(ext, ry1) + 1))
    ry1 = max(ry1, ext)
    for ws in page_lines(page, bottom=bot):
        ly0 = min(w[1] for w in ws)
        if not (ry0 - 0.5 <= ly0 < ry1):
            continue
        txt = " ".join(w[4] for w in ws)
        if not keep_total and re.search(r"\[Total:", txt):
            wos += [pymupdf.Rect(w[0] - 1, w[1] - 1, w[2] + 1, w[3] + 1) for w in ws
                    if re.match(r"\[Total:|\d+\]$", w[4])]
        if RE_NAV.search(txt):
            # navigation note of the source paper, e.g. "Question 4 continues on page 10" (A-023)
            m = RE_NAV.search(txt)
            if m.group(0).lower().startswith("(on page"):
                pass
            else:
                wos.append(pymupdf.Rect(min(w[0] for w in ws) - 1, ly0 - 1, max(w[2] for w in ws) + 1,
                                        max(w[3] for w in ws) + 1))
        if any(RE_DOTRUN.search(w[4]) for w in ws):
            wos += _dot_whiteouts(page, pymupdf.Rect(min(w[0] for w in ws), ly0, max(w[2] for w in ws),
                                                    max(w[3] for w in ws)))
    runs = ink_runs(page, ry0, ry1, wos)
    merged = []
    for y0, y1, x0, x1 in sorted(runs):
        if merged and y0 <= merged[-1][1] + gap_merge:
            m = merged[-1]
            m[1], m[2], m[3] = max(m[1], y1), min(m[2], x0), max(m[3], x1)
        else:
            merged.append([y0, y1, x0, x1])
    # slivers of a neighbouring line touching the region edge
    merged = [m for m in merged if not (m[1] - m[0] < 1.6 and (m[0] <= ry0 + 0.6 or m[1] >= ry1 - 0.6))]
    # extend each band over the full boxes of the words whose centre lies in it,
    # so no glyph box is cut by the clip (A-013)
    wb = [w for w in words if XMIN <= w[0] and w[2] <= XMAX]
    ext_m = []
    for y0, y1, x0, x1 in merged:
        a, b2 = y0 - PAD, y1 + PAD
        for w in wb:
            cy = (w[1] + w[3]) / 2
            if y0 - 0.5 <= cy <= y1 + 0.5:
                a, b2 = min(a, w[1] - 0.5), max(b2, w[3] + 0.5)
        a, b2 = max(ry0, a), min(ry1, b2)
        if ext_m and a <= ext_m[-1][1]:
            m = ext_m[-1]
            m[1], m[2], m[3] = max(m[1], b2), min(m[2], x0), max(m[3], x1)
        else:
            ext_m.append([a, b2, x0, x1])
    out = []
    for y0, y1, x0, x1 in ext_m:
        b = Band(p, y0, y1, x0=min(X0, x0 - 1.5), x1=max(X1, x1 + 1.5))
        b.whiteouts = [w for w in wos if w.y0 < b.y1 and w.y1 > b.y0]
        # a band that opens with a figure/table caption ("Fig. 3.2", "Table 2.1") stays with the figure
        # above it even when a mark on the next line makes it taller than one line (physics fix)
        bw = sorted([w for w in wb if y0 <= (w[1] + w[3]) / 2 <= y1], key=lambda w: (round(w[1]), w[0]))
        b.cap = bool(bw) and bw[0][4] in ("Fig.", "Figure", "Table") and b.h < 40
        # a band holding only a part's mark "[n]" (and answer dots) stays with the band above it, so a mark
        # never opens a page alone (physics fix)
        b.mark_only = bool(bw) and b.h < 18 and all(re.fullmatch(r"\[\d+\]|[.…]+", w[4]) for w in bw) and \
            any(re.fullmatch(r"\[\d+\]", w[4]) for w in bw)
        if b.h > 1:
            out.append(b)
    return out


def bands(doc, region, keep_total=False):
    out = []
    for p, y0, y1 in region:
        out += page_bands(doc, p, y0, y1, keep_total)
    return out


def ms_bands(doc, segs):
    """MS row segments are kept whole (full width, incl. Guidance column)."""
    return [Band(p, r[1], r[3]) for p, r in segs if r[3] - r[1] > 2]


def ms_x(segs):
    return min(r[0] for _, r in segs), max(r[2] for _, r in segs)

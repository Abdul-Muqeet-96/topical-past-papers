"""Vector crops of QP regions and MS rows, cleaned of answer lines/space.

bands(doc, region) -> list of Band(page, y0, y1, whiteouts) in reading order,
with dotted answer lines, empty writing space and [Total: n] removed.
"""
import re
import pymupdf
from parse import page_lines
from extract import drawing_boxes, content_bottom, RE_DOTS

RE_DOTRUN = re.compile(r"[.…]{5,}")
X0, X1 = 40, 556   # QP content clip (drops margin text and corner marks)


class Band:
    def __init__(self, page, y0, y1, whiteouts=None):
        self.page, self.y0, self.y1 = page, y0, y1
        self.whiteouts = whiteouts or []

    @property
    def h(self):
        return self.y1 - self.y0


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
                    outs.append(pymupdf.Rect(x0 - 0.5, line_rect.y0 - 1, x1 + 0.5, line_rect.y1 + 1))
    return outs


def page_bands(doc, p, ry0, ry1, keep_total=False, gap_merge=2.0):
    page = doc[p]
    els, wos = [], []
    for ws in page_lines(page, bottom=content_bottom(page)):
        ly0 = min(w[1] for w in ws)
        ly1 = max(w[3] for w in ws)
        if not (ry0 - 0.5 <= ly0 < ry1):
            continue
        words = [w[4] for w in ws]
        if not keep_total and re.search(r"\[Total:", " ".join(words)):
            tot = [w for w in ws if re.match(r"\[Total:|\d+\]$", w[4])]
            rest = [w for w in ws if w not in tot]
            if not rest:
                continue
            wos += [pymupdf.Rect(w[0] - 1, w[1] - 1, w[2] + 1, w[3] + 1) for w in tot]
            ws, words = rest, [w[4] for w in rest]
        if all(RE_DOTS.match(w) for w in words):
            continue          # pure answer line
        lr = pymupdf.Rect(min(w[0] for w in ws), ly0, max(w[2] for w in ws), ly1)
        if any(RE_DOTRUN.search(w) for w in words):
            wos += _dot_whiteouts(page, lr)
        els.append((ly0, ly1))
    for b in drawing_boxes(page):
        if b[3] > ry0 and b[1] < ry1 and b[2] > X0 and b[0] < X1:
            els.append((max(b[1], ry0), min(b[3], ry1)))
    els.sort()
    merged = []
    for y0, y1 in els:
        if merged and y0 <= merged[-1][1] + gap_merge:
            merged[-1][1] = max(merged[-1][1], y1)
        else:
            merged.append([y0, y1])
    out = []
    for y0, y1 in merged:
        b = Band(p, max(ry0, y0 - 1.5), min(ry1, y1 + 1.5))
        b.whiteouts = [w for w in wos if w.y0 < b.y1 and w.y1 > b.y0]
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

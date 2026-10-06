"""Page layout engine for the workbook (see layout.md).

Flow places generated text and vector crops (Bands) onto A4 pages with the
running header, banners and keep-together items.
"""
import pymupdf
from crops import X0, X1

W, H = 595.28, 841.89
ML, MR, MT, MB = 40, 40, 58, 40
TW = W - ML - MR
BOOK = "Computer Science 9618 Topical Workbook"     # set per book by build.py
DARK = (0.17, 0.2, 0.27)
GREY = (0.45, 0.45, 0.45)
ACCENT = (0.12, 0.38, 0.55)
MAX_GAP = 8.0
import os


def _fonts():
    """Liberation Sans (as in the Chemistry book) when installed, else Noto Sans."""
    for d, names in [("/usr/share/fonts/truetype/liberation/", ("LiberationSans-Regular.ttf",
                                                                 "LiberationSans-Bold.ttf",
                                                                 "LiberationSans-Italic.ttf")),
                     ("/usr/share/fonts/liberation/", ("LiberationSans-Regular.ttf", "LiberationSans-Bold.ttf",
                                                       "LiberationSans-Italic.ttf")),
                     ("/usr/share/fonts/noto/", ("NotoSans-Regular.ttf", "NotoSans-Bold.ttf",
                                                 "NotoSans-Italic.ttf"))]:
        if all(os.path.exists(d + n) for n in names):
            return {"helv": ("wbr", d + names[0]), "hebo": ("wbb", d + names[1]), "heit": ("wbi", d + names[2])}
    raise SystemExit("no usable sans-serif font found (Liberation Sans or Noto Sans)")


FONTS = _fonts()
_FONT_OBJ = {}


def tlen(s, font="helv", size=10):
    if font not in _FONT_OBJ:
        _FONT_OBJ[font] = pymupdf.Font(fontfile=FONTS[font][1])
    return _FONT_OBJ[font].text_length(s, fontsize=size)


def put(page, pt, s, font="helv", size=10, color=(0, 0, 0)):
    name, path = FONTS[font]
    page.insert_text(pt, s, fontname=name, fontfile=path, fontsize=size, color=color)


class Flow:
    def __init__(self, doc, book=BOOK):
        self.doc = doc
        self.book = book
        self.page = None
        self.y = MT
        self.header = None     # right-hand running header text, None = no header
        self.page_log = []     # (page index, header)

    # ---------- pages ----------
    def new_page(self, header=None):
        self.page = self.doc.new_page(width=W, height=H)
        self.header = header
        self.y = MT if header else 50
        if header:
            self._draw_header()
        return self.page

    def _draw_header(self):
        pg = self.page
        n = pg.number + 1
        put(pg, (ML, 34), self.book, size=7.5, color=GREY)
        s = str(n)
        put(pg, (W / 2 - tlen(s, "helv", 8) / 2, 34), s, size=8)
        put(pg, (W - MR - tlen(self.header, "helv", 7.5), 34), self.header, size=7.5, color=GREY)
        pg.draw_line((ML, 40), (W - MR, 40), color=GREY, width=0.4)

    def room(self):
        return H - MB - self.y

    def ensure(self, h):
        if h > self.room():
            self.new_page(self.header)

    # ---------- generated text ----------
    def text(self, s, size=10, bold=False, color=(0, 0, 0), x=ML, gap=4, width=None):
        font = "hebo" if bold else "helv"
        width = width or (W - MR - x)
        lines = _wrap(s, font, size, width)
        h = len(lines) * size * 1.25
        self.ensure(h)
        for ln in lines:
            self.y += size
            put(self.page, (x, self.y), ln, font, size, color)
            self.y += size * 0.25
        self.y += gap

    def banner(self, s, center=False):
        self.ensure(30)
        r = pymupdf.Rect(ML, self.y, W - MR, self.y + 22)
        if center:
            tw = tlen(s, "hebo", 12) + 30
            r = pymupdf.Rect(W / 2 - tw / 2, self.y, W / 2 + tw / 2, self.y + 22)
        self.page.draw_rect(r, color=DARK, fill=DARK)
        tx = r.x0 + 8 if not center else W / 2 - tlen(s, "hebo", 12) / 2
        put(self.page, (tx, r.y0 + 15.5), s, "hebo", 12, (1, 1, 1))
        self.y = r.y1 + 12

    # ---------- crops ----------
    @staticmethod
    def bands_height(bands, scale):
        h, prev = 0.0, None
        for b in bands:
            if prev is not None:
                h += _gap(prev, b) * scale
            h += b.h * scale
            prev = b
        return h

    def place_bands(self, src, bands, x0=X0, x1=X1, scale=None, label=None, indent=0, first_break=False):
        """Place bands (from one source doc) in flow; returns list of (page, rect).
        first_break: the first band may also start a new page (a later block of an item)."""
        avail = TW - indent
        if scale is None:
            scale = min(1.0, avail / (x1 - x0))
        placed = []
        prev = None
        first = True
        maxh = H - MB - MT - 20
        for i, b in enumerate(bands):
            gap = _gap(prev, b) * scale if prev is not None else 0
            h = b.h * scale
            s = scale
            if h > maxh:     # oversize band: shrink to fit a page
                s = scale * maxh / h
                h = maxh
            in_grp = b.grp is not None and prev is not None and prev.grp == b.grp
            chain, core, with_fig = keep_heights(bands, i, scale, maxh)
            tog = prev is not None and _together(prev, b)
            brk = False
            if not in_grp and (prev is not None or first_break):
                if gap + chain > self.room() and chain <= maxh and not tog:
                    brk = True       # everything that belongs with this band fits on a fresh page
                elif gap + core > self.room() and core <= maxh and (with_fig or not tog):
                    brk = True       # a figure (with the label line above it) is never split
            if not brk and gap + h > self.room():
                brk = True
            if brk:
                self.new_page(self.header)
                gap = 0
            self.y += gap
            if first and label:
                put(self.page, (ML + indent, self.y + 6), label, "helv", 6.5, ACCENT)
                self.y += 9
                if h > self.room():
                    self.new_page(self.header)
            first = False
            tx0 = ML + indent
            r = pymupdf.Rect(tx0, self.y, tx0 + (x1 - x0) * s, self.y + h)
            clip = pymupdf.Rect(x0, b.y0, x1, b.y1)
            self.page.show_pdf_page(r, src, b.page, clip=clip)
            for wo in b.whiteouts:
                wr = pymupdf.Rect(tx0 + (wo.x0 - x0) * s, self.y + (wo.y0 - b.y0) * s,
                                  tx0 + (wo.x1 - x0) * s, self.y + (wo.y1 - b.y0) * s) & r
                if not wr.is_empty and wo.y1 >= b.y1:
                    # a white-out that runs past the foot of the band: the band's last pixel row
                    # is only partly covered at the edge, so cover a little more (blank paper)
                    wr.y1 += 0.6
                if not wr.is_empty and wo.y0 <= b.y0:
                    wr.y0 -= 0.6     # the same at the head of the band (the edge of a removed frame)
                if not wr.is_empty:
                    self.page.draw_rect(wr, color=None, fill=(1, 1, 1), overlay=True)
            placed.append((self.page.number, r))
            self.y += h
            prev = b
        return placed

    def context_rule(self, placed):
        """Thin accent rule to the left of context crops."""
        by_page = {}
        for pno, r in placed:
            a = by_page.setdefault(pno, [r.y0, r.y1])
            a[0], a[1] = min(a[0], r.y0), max(a[1], r.y1)
        for pno, (y0, y1) in by_page.items():
            self.doc[pno].draw_line((ML - 6, y0 - 8), (ML - 6, y1), color=ACCENT, width=1.2)


def keep_heights(bands, i, scale, maxh):
    """Heights that must be free for band i to be placed where the flow stands:
    chain: band i and every band linked to it (pairwise, see _together);
    core:  band i with its figure: the whole figure when band i starts one, or the label line
           (band i) plus the figure that starts directly below it; a trailing mark is included;
    with_fig: core holds a figure."""
    def bh(k):
        return min(bands[k].h * scale, maxh)

    def run(k, cond):
        hh = 0.0
        while k + 1 < len(bands) and cond(bands[k], bands[k + 1]):
            hh += _gap(bands[k], bands[k + 1]) * scale + bh(k + 1)
            k += 1
        return hh, k

    b = bands[i]
    hh, _ = run(i, _together)
    chain = bh(i) + hh
    same = lambda a, c: a.grp is not None and a.grp == c.grp

    def core_of(k, depth=0):
        """(height, holds a figure) of band k with what it introduces"""
        c = bands[k]
        if c.grp is not None:
            hh2, e = run(k, same)
            hgt = bh(k) + hh2
            if e + 1 < len(bands) and bands[e + 1].mark_only:
                hgt += _gap(bands[e], bands[e + 1]) * scale + bh(e + 1)
            return hgt, True
        if k + 1 < len(bands) and depth < 3 and (_label_above(c, bands[k + 1]) or _introduces(c, bands[k + 1])):
            nh, fig = core_of(k + 1, depth + 1)
            return bh(k) + _gap(c, bands[k + 1]) * scale + nh, True
        return bh(k), False

    core, with_fig = core_of(i)
    return chain, core, with_fig


def _introduces(a, b):
    """a ends with a colon ("... the following instruction:") and b is what it introduces."""
    if not getattr(a, "colon_end", False) or a.grp is not None:
        return False
    # on the same page of the paper, or the paper itself turns the page after the colon
    return (a.page == b.page and 0 <= b.y0 - a.y1 <= 60) or b.page == a.page + 1


def _label_above(a, b):
    """a is the short line printed last before a figure b starts (only blank answer space lies
    between them, at most 60 pt of it)."""
    return a.grp is None and b.grp is not None and a.page == b.page and 0 <= b.y0 - a.y1 <= 60 and a.h < 30


def _together(a, b):
    """Bands a, b (consecutive, same source page) that must stay on one page:
    a short label line directly above a figure, or a figure and its caption /
    the label line directly below it."""
    if getattr(a, "grp", None) is not None and a.grp == getattr(b, "grp", None):
        return True
    if getattr(b, "mark_only", False):
        return True          # a [mark] on its own stays with the line it closes
    if _label_above(a, b) or _introduces(a, b):
        return True          # the line that introduces a figure, or that ends with a colon
    if a.page != b.page or b.y0 - a.y1 > 14:
        return False
    return (a.h < 18 and b.h > 30) or (a.h > 30 and b.h < 18)


def _gap(prev, b):
    if prev is None:
        return 0
    if prev.page == b.page and b.y0 >= prev.y1:
        return min(b.y0 - prev.y1, MAX_GAP)
    return 4


def _wrap(s, font, size, width):
    out = []
    for para in s.split("\n"):
        words = para.split(" ")
        cur = ""
        for w in words:
            t = (cur + " " + w).strip()
            if tlen(t, font, size) <= width or not cur:
                cur = t
            else:
                out.append(cur)
                cur = w
        out.append(cur)
    return out

"""Page layout engine for the workbook (see layout.md).

Flow places generated text and vector crops (Bands) onto A4 pages with the
running header, banners and keep-together items.
"""
import pymupdf
from crops import X0, X1

W, H = 595.28, 841.89
ML, MR, MT, MB = 40, 40, 58, 40
TW = W - ML - MR
BOOK = "Chemistry 9701 Paper 2 Topical Workbook"
DARK = (0.17, 0.2, 0.27)
GREY = (0.45, 0.45, 0.45)
ACCENT = (0.12, 0.38, 0.55)
MAX_GAP = 8.0


class Flow:
    def __init__(self, doc):
        self.doc = doc
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
        pg.insert_text((ML, 34), BOOK, fontname="helv", fontsize=7.5, color=GREY)
        s = str(n)
        pg.insert_text((W / 2 - pymupdf.get_text_length(s, "helv", 8) / 2, 34), s, fontname="helv", fontsize=8)
        pg.insert_text((W - MR - pymupdf.get_text_length(self.header, "helv", 7.5), 34), self.header,
                       fontname="helv", fontsize=7.5, color=GREY)
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
            self.page.insert_text((x, self.y), ln, fontname=font, fontsize=size, color=color)
            self.y += size * 0.25
        self.y += gap

    def banner(self, s, center=False):
        self.ensure(30)
        r = pymupdf.Rect(ML, self.y, W - MR, self.y + 22)
        if center:
            tw = pymupdf.get_text_length(s, "hebo", 12) + 30
            r = pymupdf.Rect(W / 2 - tw / 2, self.y, W / 2 + tw / 2, self.y + 22)
        self.page.draw_rect(r, color=DARK, fill=DARK)
        tx = r.x0 + 8 if not center else W / 2 - pymupdf.get_text_length(s, "hebo", 12) / 2
        self.page.insert_text((tx, r.y0 + 15.5), s, fontname="hebo", fontsize=12, color=(1, 1, 1))
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

    def place_bands(self, src, bands, x0=X0, x1=X1, scale=None, label=None, indent=0):
        """Place bands (from one source doc) in flow; returns list of (page, rect)."""
        avail = TW - indent
        if scale is None:
            scale = min(1.0, avail / (x1 - x0))
        placed = []
        prev = None
        first = True
        for b in bands:
            gap = _gap(prev, b) * scale if prev is not None else 0
            h = b.h * scale
            s = scale
            maxh = H - MB - MT - 20
            if h > maxh:     # oversize band: shrink to fit a page
                s = scale * maxh / h
                h = maxh
            if gap + h > self.room():
                self.new_page(self.header)
                gap = 0
            self.y += gap
            if first and label:
                self.page.insert_text((ML + indent, self.y + 6), label, fontname="helv", fontsize=6.5, color=ACCENT)
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
            if pymupdf.get_text_length(t, font, size) <= width or not cur:
                cur = t
            else:
                out.append(cur)
                cur = w
        out.append(cur)
    return out

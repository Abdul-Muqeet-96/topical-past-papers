"""Visual review helper. cv_zoom.py <book> <page> <srcfile> <srcpage> <y> <out.png> [x0 x1] [dpi]
The band of a book page that covers source y (raw visual coordinates), drawn from the book (top)
and from the raw source page (bottom)."""
import sys
import pymupdf as f
from c00_common import *

book, page, fn, sp, y, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], int(sys.argv[4]), float(sys.argv[5]), sys.argv[6]
x0, x1 = (float(sys.argv[7]), float(sys.argv[8])) if len(sys.argv) > 8 else (None, None)
dpi = int(sys.argv[9]) if len(sys.argv) > 9 else 300
B = jl(f"bands_p{book}.json")["bands"]
bb = [b for b in B if b["page"] == page and b["src"] and b["src"][0] == fn and b["src"][1] == sp - 1
      and b["vclip"][1] - 2 <= y <= b["vclip"][3] + 2]
d = f.open(BOOKS[book])
s = f.open(os.path.join(DATA, fn))
b = bb[0]
t, v = f.Rect(b["target"]), f.Rect(b["vclip"])
if x0 is not None:
    sc = t.width / v.width
    t = f.Rect(t.x0 + (x0 - v.x0) * sc, t.y0, t.x0 + (x1 - v.x0) * sc, t.y1)
    v = f.Rect(x0, v.y0, x1, v.y1)
o = f.open()
pad = 6
pg = o.new_page(width=max(t.width, v.width) + 2 * pad, height=t.height + v.height + 7 * pad)
pg.show_pdf_page(f.Rect(pad, pad, pad + t.width, pad + t.height + 2 * pad), d, page - 1, clip=t + (0, -pad, 0, pad))
pg.draw_line((0, t.height + 3.5 * pad), (pg.rect.width, t.height + 3.5 * pad), color=(0.7, 0, 0), width=1)
pg.show_pdf_page(f.Rect(pad, t.height + 4 * pad, pad + v.width, t.height + 6 * pad + v.height), s, sp - 1, clip=v + (0, -pad, 0, pad))
pg.get_pixmap(dpi=dpi).save(out)
print(len(bb), b["target"], b["vclip"])

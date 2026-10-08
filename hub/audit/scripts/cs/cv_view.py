"""Visual review helper. cv_view.py <book> <page[,page...]> <out.png> [dpi] [y0 y1]
Renders book pages (1-based) side by side, optionally only the strip y0..y1."""
import sys
import pymupdf as f
from c00_common import *

d = f.open(BOOKS[int(sys.argv[1])])
pages = [int(x) - 1 for x in sys.argv[2].split(",")]
dpi = int(sys.argv[4]) if len(sys.argv) > 4 else 80
y0, y1 = (float(sys.argv[5]), float(sys.argv[6])) if len(sys.argv) > 6 else (0, 842)
s = f.open()
w = 595.3
pg = s.new_page(width=len(pages) * (w + 6), height=y1 - y0)
for i, p in enumerate(pages):
    pg.show_pdf_page(f.Rect(i * (w + 6), 0, i * (w + 6) + w, y1 - y0), d, p, clip=f.Rect(0, y0, w, y1))
    pg.draw_line((i * (w + 6) + w + 3, 0), (i * (w + 6) + w + 3, y1 - y0), color=(0.7, 0, 0), width=4)
pg.get_pixmap(dpi=dpi).save(sys.argv[3])

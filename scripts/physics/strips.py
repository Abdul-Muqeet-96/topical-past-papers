"""Tile the left column of booklet pages (to read item headings by image).
usage: strips.py out.png dpi x1 page[:y0-y1] ...   (1-based pdf pages, y in pt)"""
import sys, pymupdf
from PIL import Image, ImageDraw
d = pymupdf.open("Ω-physics/Physics paper 2 9702 3.pdf")
out, dpi, x1 = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
ims = []
for a in sys.argv[4:]:
    p, _, yr = a.partition(":")
    y0, y1 = (float(v) for v in yr.split("-")) if yr else (0, 842)
    pm = d[int(p) - 1].get_pixmap(dpi=dpi, clip=pymupdf.Rect(0, y0, x1, y1))
    im = Image.frombytes("RGB", (pm.width, pm.height), pm.samples)
    ImageDraw.Draw(im).text((2, 2), f"p{p}", fill="red")
    ims.append(im)
W = max(i.width for i in ims); H = max(i.height for i in ims); cols = min(len(ims), 6)
S = Image.new("RGB", (W * cols, H * ((len(ims) + cols - 1) // cols)), "white")
for k, i in enumerate(ims):
    S.paste(i, ((k % cols) * W, (k // cols) * H))
S.save(out)
print(S.size)

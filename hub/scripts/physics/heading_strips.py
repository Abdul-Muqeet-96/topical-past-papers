"""Stack cropped heading strips (for reading item headings by image).
usage: heading_strips.py out.png pdfpage:y0:y1[:label] ..."""
import sys, pymupdf
from PIL import Image, ImageDraw
d = pymupdf.open("Ω-physics/Physics paper 2 9702 3.pdf")
ims = []
for a in sys.argv[2:]:
    p, y0, y1, *lab = a.split(":")
    pm = d[int(p) - 1].get_pixmap(dpi=130, clip=pymupdf.Rect(0, float(y0) - 5, 330, float(y1) + 5))
    im = Image.frombytes("RGB", (pm.width, pm.height), pm.samples)
    c = Image.new("RGB", (im.width + 170, im.height), "white")
    c.paste(im, (170, 0))
    ImageDraw.Draw(c).text((2, 2), f"p{p} y{float(y0):.0f} {' '.join(lab)}", fill="red")
    ims.append(c)
W = max(i.width for i in ims)
S = Image.new("RGB", (W, sum(i.height + 4 for i in ims)), (200, 200, 200))
y = 0
for i in ims:
    S.paste(i, (0, y)); y += i.height + 4
S.save(sys.argv[1]); print(S.size)

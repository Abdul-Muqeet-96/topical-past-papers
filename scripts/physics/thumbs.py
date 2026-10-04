"""Contact sheet of Physics booklet pages: python3 scripts/thumbs.py first last out.png"""
import sys, pymupdf
from PIL import Image, ImageDraw
src = "Ω-physics/Physics paper 2 9702 3.pdf"
a, b, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
d = pymupdf.open(src)
ims = []
for i in range(a - 1, b):
    p = d[i].get_pixmap(dpi=14, colorspace=pymupdf.csGRAY)
    im = Image.frombytes("L", (p.width, p.height), p.samples)
    ImageDraw.Draw(im).text((2, 2), str(i + 1), fill=0)
    ims.append(im)
w, h = ims[0].size
cols = 8
sheet = Image.new("L", (cols * w, ((len(ims) + cols - 1) // cols) * h), 255)
for k, im in enumerate(ims):
    sheet.paste(im, ((k % cols) * w, (k // cols) * h))
sheet.save(out)
print(sheet.size)

"""Render selected pages of a PDF to PNG (for inspection). usage: pdf dpi out page..."""
import sys, pymupdf
from PIL import Image
pdf, dpi, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
pages = [int(x) for x in sys.argv[4:]]
d = pymupdf.open(pdf)
ims = []
for p in pages:
    pix = d[p].get_pixmap(dpi=dpi)
    ims.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
w, h = ims[0].size
s = Image.new("RGB", (w * len(ims) + 6 * (len(ims) - 1), h), (180, 0, 0))
for i, im in enumerate(ims):
    s.paste(im, (i * (w + 6), 0))
s.save(out)

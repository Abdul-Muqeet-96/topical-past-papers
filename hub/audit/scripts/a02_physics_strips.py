"""Audit (Physics reference standard): tile the left reference column of a range of pages of the scanned
Physics booklet so item references (e.g. 'M/J 23/P21/Q2/a,b') can be read by eye. (Tesseract OCR of the
whole 550-page scan, a02_physics_ocr.py, was attempted first and was far too slow in this container
(~9 min per page); it was stopped.)
usage: a02_physics_strips.py out.png page page ...   (1-based PDF pages)"""
import pymupdf as f, sys
from PIL import Image, ImageDraw
d = f.open('Ω-physics/reference/Physics paper 2 9702 3.pdf')
out = sys.argv[1]; pages = [int(x) for x in sys.argv[2:]]
ims = []
for p in pages:
    pm = d[p - 1].get_pixmap(dpi=62, clip=f.Rect(20, 20, 330, 830))
    im = Image.frombytes('RGB', (pm.width, pm.height), pm.samples)
    ImageDraw.Draw(im).text((2, 2), f'pdf p{p}', fill='red')
    ims.append(im)
W = ims[0].width; H = ims[0].height; cols = 6; rows = (len(ims) + cols - 1) // cols
S = Image.new('RGB', (W * cols, H * rows), 'white')
for k, i in enumerate(ims):
    S.paste(i, ((k % cols) * W, (k // cols) * H))
S.save(out)

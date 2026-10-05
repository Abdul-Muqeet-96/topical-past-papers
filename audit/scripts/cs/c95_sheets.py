"""Visual review material.
  c95_sheets.py all <outdir>      contact sheets of every page of both books (8 pages per sheet)
  c95_sheets.py sample <outdir>   per unit: 15 question items and 5 answers picked at random (seed
                                  9618), each on its page(s) at 92 dpi, two pages per image
Writes PNG files and an index (sheets.json / samples.json) into <outdir>."""
import json, random, sys
import pymupdf as f
from c00_common import *

mode, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
W, H = 595.28, 841.89


def compose(doc, pages, cols, dpi, out, labels=None):
    rows = (len(pages) + cols - 1) // cols
    gap = 5
    s = f.open()
    pg = s.new_page(width=cols * (W + gap), height=rows * (H + gap))
    pg.draw_rect(pg.rect, color=None, fill=(0.55, 0, 0))
    for i, p in enumerate(pages):
        x, y = (i % cols) * (W + gap), (i // cols) * (H + gap)
        r = f.Rect(x, y, x + W, y + H)
        pg.draw_rect(r, color=None, fill=(1, 1, 1))
        pg.show_pdf_page(r, doc, p - 1)
    pg.get_pixmap(dpi=dpi).save(out)


if mode == "all":
    idx = []
    for book in (1, 2):
        d = f.open(BOOKS[book])
        n = len(d)
        for a in range(1, n + 1, 8):
            pages = list(range(a, min(n, a + 7) + 1))
            fn = f"p{book}_{a:04d}.png"
            compose(d, pages, 4, 46, os.path.join(outdir, fn))
            idx.append({"file": fn, "book": book, "pages": [pages[0], pages[-1]]})
    json.dump(idx, open(os.path.join(outdir, "sheets.json"), "w"))
    print(len(idx), "sheets")
else:
    random.seed(9618)
    idx = []
    for book in (1, 2):
        bp = jl(f"book_parse_p{book}.json")
        d = f.open(BOOKS[book])
        for u in UNITS[book]:
            q = [i for i in bp["items"] if i["unit"] == u and i["side"] == "Q"]
            a = [i for i in bp["items"] if i["unit"] == u and i["side"] == "A"]
            pick = random.sample(q, min(15, len(q))) + random.sample(a, min(5, len(a)))
            for k in range(0, len(pick), 2):
                grp = pick[k:k + 2]
                pages = []
                for it in grp:
                    pages.append(it["page"])
                fn = f"s{book}_u{u:02d}_{k // 2:02d}.png"
                compose(d, pages, 2, 92, os.path.join(outdir, fn))
                idx.append({"file": fn, "book": book, "unit": u,
                            "items": [{"ref": it["ref"], "side": it["side"], "n": it["n"], "page": it["page"], "end_page": it.get("end_page")} for it in grp]})
    json.dump(idx, open(os.path.join(outdir, "samples.json"), "w"), indent=0)
    print(len(idx), "sample images")

"""Part A step 1: OCR every page of the scanned Physics booklet.

Usage: python3 scripts/physics/ocr_booklet.py ocr [jobs]   -> Ω-physics/work/ocr/pNNN.tsv
       python3 scripts/physics/ocr_booklet.py pdf          -> Ω-physics/booklet-ocr.pdf
The 'ocr' step renders each page at 300 dpi (grey) and runs tesseract
(--oem 1 --psm 3 -l eng, TSV word boxes), several pages in parallel. It
writes Ω-physics/work/ocr/DONE when every page has a TSV (marker for waiting).
The 'pdf' step writes the original scanned pages with each OCR word added as
invisible text (insert_text, render_mode 3) sized to its word box, so crops
of this file carry a text layer. The scan itself is not changed.
"""
import csv, os, subprocess, sys, tempfile
from concurrent.futures import ProcessPoolExecutor
import pymupdf

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "Ω-physics", "Physics paper 2 9702 3.pdf")
OCR = os.path.join(ROOT, "Ω-physics", "work", "ocr")
OUT = os.path.join(ROOT, "Ω-physics", "booklet-ocr.pdf")
DPI = 300
FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"


def ocr_page(i):
    dest = os.path.join(OCR, f"p{i + 1:03d}.tsv")
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return i, "cached"
    d = pymupdf.open(SRC)
    pm = d[i].get_pixmap(dpi=DPI, colorspace=pymupdf.csGRAY)
    with tempfile.TemporaryDirectory() as td:
        png = os.path.join(td, "p.png")
        pm.save(png)
        base = os.path.join(td, "out")
        env = dict(os.environ, OMP_THREAD_LIMIT="1")
        r = subprocess.run(["tesseract", png, base, "--oem", "1", "--psm", "3", "-l", "eng", "tsv"],
                           capture_output=True, text=True, env=env)
        if r.returncode != 0:
            return i, "error: " + r.stderr[-200:]
        os.replace(base + ".tsv", dest + ".tmp")
    os.replace(dest + ".tmp", dest)
    return i, "ok"


def read_tsv(path):
    """Word boxes in points: list of dicts (block, par, line, word, x0, y0, x1, y1, conf, text)."""
    out = []
    k = 72.0 / DPI
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t", quoting=csv.QUOTE_NONE):
            if r["level"] != "5" or not (r["text"] or "").strip():
                continue
            x, y, w, h = (int(r[c]) for c in ("left", "top", "width", "height"))
            out.append({"block": int(r["block_num"]), "par": int(r["par_num"]), "line": int(r["line_num"]),
                        "word": int(r["word_num"]), "x0": x * k, "y0": y * k, "x1": (x + w) * k,
                        "y1": (y + h) * k, "conf": float(r["conf"]), "text": r["text"].strip()})
    return out


def main_ocr(jobs):
    os.makedirs(OCR, exist_ok=True)
    marker = os.path.join(OCR, "DONE")
    if os.path.exists(marker):
        os.remove(marker)
    n = pymupdf.open(SRC).page_count
    errs = []
    with ProcessPoolExecutor(jobs) as ex:
        for i, st in ex.map(ocr_page, range(n)):
            if st.startswith("error"):
                errs.append((i + 1, st))
    done = sum(1 for i in range(n) if os.path.exists(os.path.join(OCR, f"p{i + 1:03d}.tsv")))
    with open(marker, "w") as fh:
        fh.write(f"pages {n} tsv {done} errors {len(errs)}\n")
        for e in errs:
            fh.write(f"{e}\n")
    print(f"pages {n}, tsv {done}, errors {len(errs)}")


def main_pdf():
    d = pymupdf.open(SRC)
    font = pymupdf.Font(fontfile=FONT)
    asc, desc = font.ascender, -font.descender          # em units (about 0.91 and 0.21)
    nwords = 0
    for page in d:
        if page.rotation:
            page.remove_rotation()      # displayed orientation = page coordinates (scan unchanged)
        words = read_tsv(os.path.join(OCR, f"p{page.number + 1:03d}.tsv"))
        lines = {}
        for w in words:
            k = (w["block"], w["par"], w["line"])
            a = lines.setdefault(k, [w["y0"], w["y1"]])
            a[0], a[1] = min(a[0], w["y0"]), max(a[1], w["y1"])
        for w in words:
            bw = w["x1"] - w["x0"]
            ly0, ly1 = lines[(w["block"], w["par"], w["line"])]
            lh = ly1 - ly0
            if bw <= 0 or lh <= 0:
                continue
            fs = max(lh / (asc + desc), 2.0)
            base = ly1 - desc * fs
            tl = font.text_length(w["text"], fontsize=fs)
            if tl <= 0:
                continue
            page.insert_text((w["x0"], base), w["text"], fontsize=fs, fontname="F0", fontfile=FONT,
                             render_mode=3, morph=(pymupdf.Point(w["x0"], base), pymupdf.Matrix(bw / tl, 1)))
            nwords += 1
        page.clean_contents()        # one content stream per page instead of one per word
    d.subset_fonts()
    d.save(OUT, garbage=4, deflate=True)
    print(f"booklet-ocr.pdf: pages {d.page_count}, words {nwords}, size {os.path.getsize(OUT) / 1e6:.1f} MB")


if __name__ == "__main__":
    if sys.argv[1] == "ocr":
        main_ocr(int(sys.argv[2]) if len(sys.argv) > 2 else 4)
    else:
        main_pdf()

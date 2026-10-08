"""Side-by-side sheets for the booklet light check: booklet item crop (left) and the
official QP pages of that question (right). Usage:
  python3 hub/scripts/physics/side_by_side.py OUTDIR [unit:n ...]   (default: the 55 sampled items)
Writes OUTDIR/sbs_<unit>_<n>.png and prints the file names."""
import json, os, re, sys
import pymupdf
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from parse import load, parse_qp, special_page

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
WORK = os.path.join(ROOT, "Ω-physics", "build", "work")
SRC = os.path.join(ROOT, "Ω-physics", "reference", "Physics paper 2 9702 3.pdf")
DPI = 50


def pix(page, clip=None, dpi=DPI):
    pm = page.get_pixmap(dpi=dpi, clip=clip)
    return Image.frombytes("RGB", (pm.width, pm.height), pm.samples)


def stack(ims, gap=6):
    W = max(i.width for i in ims)
    S = Image.new("RGB", (W, sum(i.height + gap for i in ims)), (190, 190, 190))
    y = 0
    for i in ims:
        S.paste(i, (0, y))
        y += i.height + gap
    return S


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    I = {(it["unit"], it["n"]): it for it in json.load(open(os.path.join(WORK, "booklet_items.json")))}
    man = json.load(open(os.path.join(WORK, "manifest_physics.json")))
    keys = [tuple(int(v) for v in a.split(":")) for a in sys.argv[2:]] or \
        [(s["unit"], s["n"]) for s in json.load(open(os.path.join(WORK, "booklet_sample.json")))]
    bk = pymupdf.open(SRC)
    for u, n in keys:
        it = I[(u, n)]
        rp = it["ref_parsed"]
        left = stack([pix(bk[p0], pymupdf.Rect(16, y0, 580, y1)) for p0, y0, y1 in it["regions"]])
        pid = {"M/J": "s", "O/N": "w", "MAR": "m"}[rp["series"]] + f"{rp['yy']:02d}_{rp['paper']}"
        ent = man.get(pid)
        right = None
        if ent and ent.get("qp", {}).get("status") == "ok":
            d = load(os.path.join(ROOT, "hub", "data", ent["qp"]["file"]))
            qs = parse_qp(d)
            Q = next((q for q in qs if q["n"] == rp["q"]), None)
            if Q:
                nxt = next((q for q in qs if q["n"] == rp["q"] + 1), None)
                p_end = nxt["start"][0] if nxt else d.page_count - 1
                pages = [p for p in range(Q["start"][0], p_end + 1) if not special_page(d[p])]
                ims = []
                for p in pages:
                    y0 = Q["start"][1] - 4 if p == Q["start"][0] else 40
                    y1 = nxt["start"][1] - 2 if (nxt and p == nxt["start"][0]) else 800
                    if y1 - y0 > 10:
                        ims.append(pix(d[p], pymupdf.Rect(30, y0, 570, y1)))
                right = stack(ims) if ims else None
        H = max(left.height, right.height if right else 0) + 16
        S = Image.new("RGB", (left.width + (right.width if right else 0) + 12, H), "white")
        S.paste(left, (0, 16))
        if right:
            S.paste(right, (left.width + 12, 16))
        ImageDraw.Draw(S).text((2, 2), f"U{u} #{n} {it['ref']}  | booklet (left)  official {pid} (right)", fill="red")
        f = os.path.join(out, f"sbs_{u:02d}_{n:02d}.png")
        S.save(f)
        print(os.path.basename(f), S.size)


if __name__ == "__main__":
    main()

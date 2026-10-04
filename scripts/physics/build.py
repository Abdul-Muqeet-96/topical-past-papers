"""Stage 6/8: build the workbook PDF, per-unit PDFs and index.csv.

Usage: python3 scripts/build.py OUTDIR phase1 [phase2 ...]
Layout follows layout.md. Contents page numbers are filled after the body is
rendered (front pages are reserved first), so they are exact.
"""
import csv, datetime, json, os, sys
from collections import defaultdict
import pymupdf
sys.path.insert(0, os.path.dirname(__file__))
from parse import load, special_page
from crops import bands, ms_bands, Band, X0, X1
from items import find_letter, letter_of, unit_region
from layout import Flow, put, tlen, W, H, ML, MR, MT, MB, TW, DARK, GREY, ACCENT, BOOK
from assemble import TOPICS, SECTIONS

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERIES_NAME = {"m": "Feb/March", "s": "May/June", "w": "Oct/Nov"}


class Docs:
    def __init__(self):
        self.d = {}

    def __call__(self, f):
        if f not in self.d:
            self.d[f] = load(os.path.join(ROOT, "data", f))
        return self.d[f]


def unit_ms_rows(Q, u):
    if u.endswith("#intro"):
        return []
    L = find_letter(Q, letter_of(u)) if letter_of(u) else Q["letters"][0]
    if u == L["label"]:
        return L["ms_rows"]
    R = next(R for R in L["romans"] if R["label"] == u)
    return R["ms_rows"]


def item_regions(it, Q):
    """All source regions of an item (stem, context figures/tables, context
    parts, lettered intros, the item's own parts), merged in paper order, so the
    item reads like the paper with no generated labels and nothing shown twice
    (audit A-028/A-022, decision D2)."""
    regs = list(Q["stem"])
    for b in it["ctx_blocks"]:
        regs += Q["blocks"][b]
    for c in it["ctx_parts"]:
        regs += unit_region(Q, c) or []
    for i in it["intros"]:
        regs += find_letter(Q, letter_of(i))["intro"]
    for u in it["units"]:
        regs += unit_region(Q, u)
    regs = sorted([list(r) for r in regs], key=lambda r: (r[0], r[1]))
    out = []
    for p, y0, y1 in regs:
        if out and out[-1][0] == p and y0 <= out[-1][2] + 0.5:
            out[-1][2] = max(out[-1][2], y1)
        else:
            out.append([p, y0, y1])
    return out


def item_blocks(it, Q, qd):
    bs = bands(qd, item_regions(it, Q))
    for b in bs:      # bands of one figure/table stay on one page (audit A-014)
        for k, reg in Q["blocks"].items():
            if reg and any(p == b.page and y0 - 1 <= b.y0 and b.y1 <= y1 + 1 for p, y0, y1 in reg):
                b.grp = k
    return [(None, bs)]


def also_text(it):
    if not it["also"]:
        return ""
    parts = [f"Unit {k} ({v} mark{'s' if v != 1 else ''})" for k, v in
             sorted(it["also"].items(), key=lambda kv: -kv[1])]
    main = it["by_topic"].get(str(it["topic"]), 0)
    return f"also {', '.join(parts)}; this unit {main} mark{'s' if main != 1 else ''}"


def est_height(blocks):
    h = 18
    allb = [b for _, bs in blocks for b in bs]
    if allb:
        w = max(b.x1 for b in allb) - min(b.x0 for b in allb)
        h += Flow.bands_height(allb, min(1.0, TW / w)) + 4
    return h


def place_item(f, num, it, blocks, ref_pages):
    h = est_height(blocks) + (10 if it["also"] else 0) + (10 if it.get("data_booklet") else 0)
    avail = H - MB - MT - 30
    if h > f.room() and h <= avail:
        f.new_page(f.header)
    elif f.room() < 80:
        f.new_page(f.header)
    f.text(f"{num}.  {it['ref']}", size=10.5, bold=True, gap=2)
    ref_pages[it["ref"]] = f.page.number + 1
    at = also_text(it)
    if at:
        f.text(at, size=7.5, color=GREY, gap=3)
    if it.get("data_booklet"):
        f.text("Data Booklet needed", size=7.5, color=GREY, gap=3)
    allb = [b for _, bs in blocks for b in bs]
    x0 = min([b.x0 for b in allb] or [X0])
    x1 = max([b.x1 for b in allb] or [X1])
    for lab, bs in blocks:
        if bs:
            f.place_bands(f.cur_src, bs, x0=x0, x1=x1)
            f.y += 2
    f.y += 14


def place_answer(f, num, it, Q, md):
    rows = []
    for u in it["units"]:
        rows += [(None, r) for r in unit_ms_rows(Q, u)]
    ctx = []
    for c in it.get("deps", []):          # parts whose answer the item uses (decision D2)
        rr = unit_ms_rows(Q, c)
        if rr:
            ctx.append((c, rr))
    segs = [s for _, r in rows for s in r["segs"]]
    if not segs:
        return False
    x0 = min(s[1][0] for s in segs)
    x1 = max(s[1][2] for s in segs)
    bs = [Band(p, r[1], r[3]) for p, r in segs if r[3] - r[1] > 2]
    first_h = (bs[0].h * TW / (x1 - x0)) if bs else 0
    if f.room() < 30 + min(first_h, 200):
        f.new_page(f.header)
    f.text(f"{num}.  {it['ref']}", size=10.5, bold=True, gap=3)
    f.place_bands(f.cur_ms, bs, x0=x0, x1=x1)
    for c, rr in ctx:
        cs = [s for r in rr for s in r["segs"]]
        cbs = [Band(p, r[1], r[3]) for p, r in cs if r[3] - r[1] > 2]
        f.y += 6
        f.place_bands(f.cur_ms, cbs, x0=x0, x1=x1)
    f.y += 14
    return True


def cover(doc, stats):
    pg = doc.new_page(width=W, height=H)
    pg.draw_rect(pymupdf.Rect(0, 0, W, 300), color=None, fill=DARK)
    for i, c in enumerate([(0.12, 0.38, 0.55), (0.2, 0.55, 0.6), (0.85, 0.6, 0.2)]):
        pg.draw_rect(pymupdf.Rect(ML + i * 26, 60, ML + i * 26 + 18, 78), color=None, fill=c)
    put(pg, (ML, 140), "Physics 9702", "hebo", 34, (1, 1, 1))
    put(pg, (ML, 175), "Paper 2 · AS Level Structured Questions", "helv", 16, (0.85, 0.88, 0.92))
    put(pg, (ML, 235), "Part-level Topical Workbook", "hebo", 22, (1, 1, 1))
    put(pg, (ML, 262), "with Mark Scheme", "helv", 14, (0.85, 0.88, 0.92))
    y = 350
    bullets = [
        "Every question part filed under its own syllabus topic (22 AS units)",
        "Each item carries the official context it needs: stem, tables, figures, earlier parts",
        "Answer lines removed; tables to complete kept",
        "Newest papers first; mark scheme in an Answers Section after each unit",
        "Index of every part with its unit, marks and page; Periodic Table appendix",
    ]
    for b in bullets:
        pg.draw_rect(pymupdf.Rect(ML, y - 7, ML + 6, y - 1), color=None, fill=ACCENT)
        put(pg, (ML + 14, y), b, "helv", 11)
        y += 22
    y += 20
    put(pg, (ML, y), "Coverage", "hebo", 12)
    y += 20
    for line in stats:
        put(pg, (ML, y), line, "helv", 10.5, (0.25, 0.25, 0.25))
        y += 17
    put(pg, (ML, H - 60), "Question and mark scheme content © UCLES / Cambridge University Press & Assessment,",
        "helv", 8, GREY)
    put(pg, (ML, H - 48), "reproduced from the published past papers for study use.", "helv", 8, GREY)
    put(pg, (ML, H - 30), f"Built {datetime.date.today().isoformat()}", "helv", 8, GREY)


def unit_title_page(f, t, items):
    pg = f.new_page(None)
    pg.draw_rect(pymupdf.Rect(0, 0, W, 8), color=None, fill=DARK)
    put(pg, (ML, 130), f"Unit {t}", "hebo", 22, ACCENT)
    y = 170
    for ln in _wrap(TOPICS[t].upper(), "hebo", 24, TW):
        put(pg, (ML, y), ln, "hebo", 24, DARK)
        y += 30
    pg.draw_line((ML, y), (W - MR, y), color=DARK, width=1.5)
    y += 30
    marks = sum(i["marks"] for i in items)
    put(pg, (ML, y), f"{len(items)} items · {marks} marks", "helv", 12)
    y += 30
    put(pg, (ML, y), "Syllabus sections in this unit", "hebo", 11)
    y += 18
    secs = sorted({s for s in SECTIONS if int(s.split('.')[0]) == t}, key=lambda s: float(s.split('.')[1]))
    for s in secs:
        for ln in _wrap(f"{s}  {SECTIONS[s]}", "helv", 10, TW):
            put(pg, (ML + 10, y), ln, "helv", 10, (0.25, 0.25, 0.25))
            y += 14


def _wrap(s, font, size, width):
    out, cur = [], ""
    for w in s.split(" "):
        t = (cur + " " + w).strip()
        if tlen(t, font, size) <= width or not cur:
            cur = t
        else:
            out.append(cur)
            cur = w
    out.append(cur)
    return out


def contents(doc, front, rows):
    """Fill reserved contents pages. rows: (label, sublabel, page)"""
    pi = 0
    pg = doc[front[pi]]
    put(pg, (ML, 70), "Contents", "hebo", 20, DARK)
    y = 105
    for label, sub, page in rows:
        if y > H - MB - 30:
            pi += 1
            pg = doc[front[pi]]
            y = 70
        if label:
            two = label.startswith("UNIT")
            pg.draw_rect(pymupdf.Rect(ML, y - 2, ML + 62, y + (30 if two else 14)), color=GREY, width=0.5)
            put(pg, (ML + 6, y + (18 if two else 10)), label, "hebo", 9)
        x = ML + 70
        put(pg, (x, y + 10), sub[0], "hebo" if sub[1] else "helv", 9.5)
        ps = str(page)
        px = W - MR - tlen(ps, "helv", 9.5)
        lx = x + tlen(sub[0], "hebo" if sub[1] else "helv", 9.5) + 4
        dots = "." * max(0, int((px - lx - 4) / tlen(".", "helv", 9.5)))
        put(pg, (lx, y + 10), dots, "helv", 9.5, GREY)
        put(pg, (px, y + 10), ps, "helv", 9.5)
        y += 16 if label is None else 16


def periodic_clip(pt):
    """Clip around the Periodic Table itself (no barcodes/margins); rotate it
    upright when the table is printed sideways."""
    from collections import Counter
    lines = [l for b in pt.get_text("dict")["blocks"] for l in b.get("lines", [])]
    dirs = Counter(tuple(round(v) for v in l["dir"]) for l in lines)
    main = dirs.most_common(1)[0][0]
    rot = -90 if main == (0, -1) else (90 if main == (0, 1) else 0)
    inner = pymupdf.Rect(45, 50, pt.rect.width - 45, pt.rect.height - 50)
    tl = [pymupdf.Rect(l["bbox"]) for l in lines if tuple(round(v) for v in l["dir"]) == main
          and pymupdf.Rect(l["bbox"]) in inner and "".join(s["text"] for s in l["spans"]).strip()
          and not "".join(s["text"] for s in l["spans"]).strip().startswith(("©", "*", "9702/", "DO NOT"))]
    box = pymupdf.Rect(tl[0])
    for r in tl:
        box |= r
    grown = box + (-25, -25, 25, 25)
    for dr in pt.get_drawings():
        r = dr["rect"]
        if r.intersects(grown) and r in inner and r.width < pt.rect.width * 0.9:
            box |= r
    return box + (-4, -4, 4, 4), rot


def build(outdir, phases):
    docs = Docs()
    items, parts = [], {}
    for ph in phases:
        items += json.load(open(os.path.join(ROOT, "Ω-physics", "work", f"items_{ph}.json")))
        parts.update(json.load(open(os.path.join(ROOT, "Ω-physics", "work", f"parts_{ph}.json"))))
    by_unit = defaultdict(list)
    for it in items:
        by_unit[it["topic"]].append(it)
    for t in by_unit:
        by_unit[t].sort(key=lambda i: tuple(-x for x in i["sort"][:3]) + tuple(-x for x in i["sort"][3:]))
    papers = sorted({(i["year"], i["series"], i["variant"], i["paper_ref"]) for i in items})
    stats = [f"{len(papers)} papers: {papers[0][3]} to {papers[-1][3]} (newest first in each unit)",
             f"{len(items)} items, {sum(i['marks'] for i in items)} marks across {len(by_unit)} units"]
    out = pymupdf.open()
    cover(out, stats)
    n_rows = 2 * len(TOPICS) + 2
    n_front = 1 + (n_rows * 16 + 120) // int(H - MB - 70 - 35) + 1
    front = []
    for _ in range(n_front - 1):
        out.new_page(width=W, height=H)
        front.append(out.page_count - 1)
    f = Flow(out)
    rows, ref_pages, unit_ranges = [], {}, {}
    for t in TOPICS:
        its = by_unit.get(t, [])
        start = out.page_count
        unit_title_page(f, t, its)
        name = f"Unit {t}: {TOPICS[t]}"
        f.new_page(name)
        f.banner(name)
        q_page = out.page_count
        for k, it in enumerate(its, 1):
            P = parts[it["paper"]]
            Q = next(q for q in P["questions"] if q["n"] == it["q"])
            qd = docs(P["qp"])
            f.cur_src = qd
            place_item(f, k, it, item_blocks(it, Q, qd), ref_pages)
        f.new_page(f"Unit {t}: Answers Section")
        f.banner("Answers Section", center=True)
        a_page = out.page_count
        for k, it in enumerate(its, 1):
            P = parts[it["paper"]]
            Q = next(q for q in P["questions"] if q["n"] == it["q"])
            f.cur_ms = docs(P["ms"])
            place_answer(f, k, it, Q, f.cur_ms)
        unit_ranges[t] = (start, out.page_count - 1)
        rows.append((f"UNIT {t}", (TOPICS[t], True), start + 1))
        rows.append((None, ("Answers Section", False), a_page))
    # index
    f.new_page("Topic index")
    f.banner("Topic index: where each part was filed")
    idx_page = out.page_count
    idx = sorted(items, key=lambda i: (-i["year"], -{"w": 3, "s": 2, "m": 1}[i["series"]], i["variant"], i["q"],
                                       i["sort"][4] * -1))
    cols = [ML, ML + 170, ML + 215, ML + 255, ML + 300]
    def head():
        for x, h in zip(cols, ["Reference", "Unit", "Marks", "Page", "Also / context"]):
            put(f.page, (x, f.y + 8), h, "hebo", 8)
        f.y += 14
        f.page.draw_line((ML, f.y - 3), (W - MR, f.y - 3), color=GREY, width=0.4)
    head()
    csvrows = []
    for it in idx:
        if f.room() < 14:
            f.new_page("Topic index")
            head()
        extra = []
        if it["also"]:
            extra.append("also " + ", ".join(f"U{k}:{v}" for k, v in it["also"].items()))
        ctxp = [c.replace("#intro", " intro") for c in it["ctx_parts"]] + it["ctx_blocks"]
        if ctxp:
            extra.append("ctx " + ", ".join(ctxp))
        vals = [it["ref"], str(it["topic"]), str(it["marks"]), str(ref_pages[it["ref"]]), "; ".join(extra)]
        for x, v in zip(cols, vals):
            s = v
            while tlen(s, "helv", 7.5) > (W - MR - x if x == cols[-1] else 999) and len(s) > 4:
                s = s[:-4] + "…"
            put(f.page, (x, f.y + 8), s, "helv", 7.5)
        f.y += 11
        csvrows.append({"reference": it["ref"], "unit": it["topic"], "marks": it["marks"],
                        "page": ref_pages[it["ref"]],
                        "also_topics": ";".join(f"{k}:{v}" for k, v in it["also"].items()),
                        "context_parts": ";".join(ctxp)})
    rows.append(("INDEX", ("Topic index", True), idx_page))
    # appendix: periodic table from newest paper
    newest = max(parts.values(), key=lambda p: (p["year"], {"w": 3, "s": 2, "m": 1}[p["series"]], p["variant"]))
    qd = docs(newest["qp"])
    pt = next(p for p in qd if special_page(p) == "periodic")
    f.new_page("Appendix: Periodic Table")
    f.banner(f"Appendix: The Periodic Table of Elements (from {newest['ref']})")
    app_page = out.page_count
    clip, rot = periodic_clip(pt)
    cw, ch = (clip.height, clip.width) if rot else (clip.width, clip.height)
    s = min(TW / cw, (H - MB - f.y) / ch)
    dest = pymupdf.Rect(ML, f.y, ML + cw * s, f.y + ch * s)
    f.page.show_pdf_page(dest, qd, pt.number, clip=clip, rotate=rot)
    rows.append(("APPENDIX", ("The Periodic Table of Elements", True), app_page))
    contents(out, front, rows)
    # bookmarks (audit A-016)
    toc = [[1, "Contents", front[0] + 1]]
    for t in TOPICS:
        r = [x for x in rows if x[0] == f"UNIT {t}"]
        if r:
            toc.append([1, f"Unit {t}: {TOPICS[t]}", r[0][2]])
            ai = rows.index(r[0]) + 1
            toc.append([2, f"Unit {t}: Answers Section", rows[ai][2]])
    toc.append([1, "Topic index", idx_page])
    toc.append([1, "Appendix: The Periodic Table of Elements", app_page])
    out.set_toc(toc)
    os.makedirs(outdir, exist_ok=True)
    book = os.path.join(outdir, "Physics-9702-P2-Topical-Workbook.pdf")
    out.subset_fonts()
    out.save(book, garbage=4, deflate=True, deflate_fonts=True)
    unit_dir = os.path.join(outdir, "units")
    os.makedirs(unit_dir, exist_ok=True)
    for t, (a, b) in unit_ranges.items():
        u = pymupdf.open()
        u.insert_pdf(out, from_page=a, to_page=b)
        ai = [x for x in rows if x[0] == f"UNIT {t}"][0]
        ap = rows[rows.index(ai) + 1][2]
        u.set_toc([[1, f"Unit {t}: {TOPICS[t]}", 1], [2, "Answers Section", ap - a]])
        u.subset_fonts()
        u.save(os.path.join(unit_dir, f"Unit-{t:02d}-{TOPICS[t].replace(':', '').replace(' ', '-')}.pdf"),
               garbage=4, deflate=True, deflate_fonts=True)
    with open(os.path.join(outdir, "index.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["reference", "unit", "marks", "page", "also_topics", "context_parts"])
        w.writeheader()
        w.writerows(csvrows)
    # items.jsonl: each item's question text from the source text layer (audit A-020)
    from extract import text_of
    with open(os.path.join(outdir, "items.jsonl"), "w") as fh:
        for it in idx:
            P = parts[it["paper"]]
            Q = next(q for q in P["questions"] if q["n"] == it["q"])
            fh.write(json.dumps({"reference": it["ref"], "unit": it["topic"], "marks": it["marks"],
                                 "page": ref_pages[it["ref"]], "data_booklet": it.get("data_booklet", False),
                                 "text": text_of(docs(P["qp"]), item_regions(it, Q))},
                                ensure_ascii=False) + "\n")
    json.dump({"pages": out.page_count, "ref_pages": ref_pages, "unit_ranges": unit_ranges,
               "contents": rows}, open(os.path.join(ROOT, "Ω-physics", "work", "build_info.json"), "w"), indent=0)
    print(f"book pages {out.page_count}, items {len(items)}, size {os.path.getsize(book)/1e6:.1f} MB")


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2:])

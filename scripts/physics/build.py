"""Stage 5: build the Physics workbook PDF, per-unit PDFs, index.csv, items.jsonl.

Usage: python3 scripts/physics/build.py OUTDIR
Each unit: Part B items (official papers, newest first), then the booklet items
(crops of Ω-physics/booklet-ocr.pdf, newest first, booklet order within a year),
one numbering; Answers Section after each unit in the same order. Layout as in
the Chemistry book (Δ-chemistry/layout.md). Contents page numbers are filled after
the body is rendered (front pages are reserved first), so they are exact.
"""
import csv, datetime, json, os, re, sys
from collections import defaultdict
import pymupdf
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
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



BOOKLET_PDF = os.path.join(ROOT, "Ω-physics", "booklet-ocr.pdf")
WORK = os.path.join(ROOT, "Ω-physics", "work")
BOOKNAME = "Physics-9702-P2-Topical-Workbook.pdf"
BX0, BX1 = 8, 588          # horizontal limits for booklet crops (ink extent inside them)
_GRAY = {}


def _booklet_gray(bd, p0, z=1.5):
    if p0 not in _GRAY:
        pm = bd[p0].get_pixmap(matrix=pymupdf.Matrix(z, z), colorspace=pymupdf.csGRAY, alpha=False)
        _GRAY[p0] = np.frombuffer(pm.samples, dtype=np.uint8).reshape(pm.height, pm.stride)[:, :pm.width].copy()
        if len(_GRAY) > 40:
            _GRAY.pop(next(iter(_GRAY)))
    return _GRAY[p0]


def booklet_bands(bd, regions, wos):
    """One band per booklet region (a region never crosses a page), x-extent from ink."""
    z = 1.5
    out = []
    for p0, y0, y1 in regions:
        a = _booklet_gray(bd, p0)[int(y0 * z):int(np.ceil(y1 * z)), int(BX0 * z):int(BX1 * z)] < 150
        w = [pymupdf.Rect(r[1], r[2], r[3], r[4]) for r in wos if r[0] == p0 and r[2] < y1 and r[4] > y0]
        for r in w:      # whiteouts do not count as ink
            a[max(0, int((r.y0 - y0) * z)):max(0, int((r.y1 - y0) * z)),
              max(0, int((r.x0 - BX0) * z)):max(0, int((r.x1 - BX0) * z))] = False
        cols = np.flatnonzero(a.sum(axis=0) >= 3)
        x0 = BX0 + cols[0] / z - 2 if len(cols) else 40
        x1 = BX0 + (cols[-1] + 1) / z + 2 if len(cols) else 556
        b = Band(p0, y0, y1, w, x0=max(BX0, x0), x1=min(BX1, x1))
        out.append(b)
    return out


def booklet_entries():
    """Booklet items with their notes, from work/booklet_items.json and the light check."""
    sys.path.insert(0, os.path.dirname(__file__))
    from map_booklet import UNIT_TO_TOPIC
    I = json.load(open(os.path.join(WORK, "booklet_items.json")))
    C = json.load(open(os.path.join(WORK, "booklet_check.json")))
    outside = {(u, n) for u, n, _, _ in C["outside_syllabus"]}
    dup = {}
    for ref, locs in C["duplicates"]:
        for u, n in locs:
            dup[(u, n)] = [UNIT_TO_TOPIC[v] for v, m in locs if (v, m) != (u, n)]
    out = []
    for it in I:
        u, n = it["unit"], it["n"]
        notes, anotes = ["booklet (scan + OCR)"], []
        if (u, n) in outside:
            notes.append("May be outside the 2025–27 syllabus")
        for fl in it["flags"]:
            if fl.startswith("scan_gap_q"):
                a, b = fl.split(":")[1].split("-")
                notes.append(f"Incomplete in the scanned booklet: its printed pages {a}–{b} are missing")
            elif fl.startswith("scan_gap_a"):
                a, b = fl.split(":")[1].split("-")
                anotes.append(f"Answer incomplete in the scanned booklet: its printed pages {a}–{b} are missing")
            elif fl == "no_answer":
                anotes.append("Answer missing from the scanned booklet (printed pages 328–329 are missing)")
        if (u, n) in dup:
            notes.append("The booklet also files this question under Unit " + ", ".join(map(str, dup[(u, n)])))
        rp = it["ref_parsed"]
        out.append({"kind": "booklet", "key": f"B{u}-{n}", "ref": it["ref"], "topic": it["topic"],
                    "booklet_unit": u, "booklet_n": n, "marks": None, "year": 2000 + rp["yy"],
                    "regions": it["regions"], "whiteouts": it.get("whiteouts", []),
                    "answer_regions": it["answer_regions"], "answer_whiteouts": it.get("answer_whiteouts", []),
                    "notes": notes, "answer_notes": anotes, "flags": it["flags"],
                    "sort": (-(2000 + rp["yy"]), u, n)})
    return out


def est_height(blocks, x0=None, x1=None):
    h = 18
    allb = [b for _, bs in blocks for b in bs]
    if allb:
        x0 = min(b.x0 for b in allb) if x0 is None else x0
        x1 = max(b.x1 for b in allb) if x1 is None else x1
        h += Flow.bands_height(allb, min(1.0, TW / (x1 - x0))) + 4
    return h


def place_item(f, num, it, blocks, ref_pages, src):
    notes = []
    if it["kind"] == "official":
        at = also_text(it)
        if at:
            notes.append(at)
    else:
        notes = it["notes"]
    h = est_height(blocks) + 10 * len(notes)
    avail = H - MB - MT - 30
    if h > f.room() and h <= avail:
        f.new_page(f.header)
    elif f.room() < 80:
        f.new_page(f.header)
    f.text(f"{num}.  {it['ref']}", size=10.5, bold=True, gap=2)
    ref_pages[it["key"]] = f.page.number + 1
    for n in notes:
        f.text(n, size=7.5, color=GREY, gap=3)
    allb = [b for _, bs in blocks for b in bs]
    x0 = min([b.x0 for b in allb] or [X0])
    x1 = max([b.x1 for b in allb] or [X1])
    for lab, bs in blocks:
        if bs:
            f.place_bands(src, bs, x0=x0, x1=x1)
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
    f.place_bands(md, bs, x0=x0, x1=x1)
    for c, rr in ctx:
        cs = [s for r in rr for s in r["segs"]]
        cbs = [Band(p, r[1], r[3]) for p, r in cs if r[3] - r[1] > 2]
        f.y += 6
        f.place_bands(md, cbs, x0=x0, x1=x1)
    f.y += 14
    return True


def place_booklet_answer(f, num, it, bd):
    bs = booklet_bands(bd, it["answer_regions"], it["answer_whiteouts"])
    notes = it["answer_notes"]
    first_h = bs[0].h if bs else 0
    if f.room() < 30 + 10 * len(notes) + min(first_h, 200):
        f.new_page(f.header)
    f.text(f"{num}.  {it['ref']}", size=10.5, bold=True, gap=3)
    for n in notes:
        f.text(n, size=7.5, color=GREY, gap=3)
    if bs:
        x0 = min(b.x0 for b in bs)
        x1 = max(b.x1 for b in bs)
        f.place_bands(bd, bs, x0=x0, x1=x1)
    f.y += 14
    return True


def cover(doc, stats):
    pg = doc.new_page(width=W, height=H)
    pg.draw_rect(pymupdf.Rect(0, 0, W, 300), color=None, fill=DARK)
    for i, c in enumerate([(0.12, 0.38, 0.55), (0.2, 0.55, 0.6), (0.85, 0.6, 0.2)]):
        pg.draw_rect(pymupdf.Rect(ML + i * 26, 60, ML + i * 26 + 18, 78), color=None, fill=c)
    put(pg, (ML, 140), "Physics 9702", "hebo", 34, (1, 1, 1))
    put(pg, (ML, 175), "Paper 2 · AS Level Structured Questions", "helv", 16, (0.85, 0.88, 0.92))
    put(pg, (ML, 235), "Topical Workbook", "hebo", 22, (1, 1, 1))
    put(pg, (ML, 262), "with Mark Scheme", "helv", 14, (0.85, 0.88, 0.92))
    y = 350
    bullets = [
        "Questions filed under the 11 AS topics of the 2025–27 syllabus",
        "Official papers (Oct/Nov 2023 – May/June 2026): each question part under its own topic,",
        "    with the official context it needs and the official mark scheme",
        "Booklet questions up to 2023: scanned pages with an OCR text layer, marked \"booklet (scan + OCR)\"",
        "Newest first in each unit; Answers Section after each unit",
        "Topic index with page numbers; Data and Formulae appendix",
    ]
    for b in bullets:
        if not b.startswith("    "):
            pg.draw_rect(pymupdf.Rect(ML, y - 7, ML + 6, y - 1), color=None, fill=ACCENT)
        put(pg, (ML + 14, y), b.strip(), "helv", 10.5)
        y += 21
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
    off = [i for i in items if i["kind"] == "official"]
    bk = [i for i in items if i["kind"] == "booklet"]
    put(pg, (ML, y), f"{len(items)} items: {len(off)} from official papers ({sum(i['marks'] for i in off)} marks), "
        f"{len(bk)} from the booklet", "helv", 12)
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
        y += 16


def data_clip(pg):
    """Clip around the Data and Formulae content of the QP page (no page number, barcode,
    footer or margin text)."""
    from crops import page_top
    from extract import content_bottom
    top, bot = page_top(pg), content_bottom(pg)
    box = None
    for b in pg.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            r = pymupdf.Rect(l["bbox"])
            t = "".join(s["text"] for s in l["spans"]).strip()
            if not t or r.y0 < top or r.y1 > bot or r.x0 < 40 or r.x1 > pg.rect.width - 30:
                continue
            box = r if box is None else box | r
    for d in pg.get_drawings():
        r = d["rect"]
        if box is not None and r.y0 >= top and r.y1 <= bot and r.x0 >= 40 and r.x1 <= pg.rect.width - 30:
            box |= r
    return box + (-4, -4, 4, 4)


def item_text_booklet(it):
    from booklet_lines import region_text
    return region_text(it["regions"])


def build(outdir):
    docs = Docs()
    bd = pymupdf.open(BOOKLET_PDF)
    items = json.load(open(os.path.join(WORK, "items_partb.json")))
    parts = json.load(open(os.path.join(WORK, "parts_partb.json")))
    for it in items:
        it["kind"] = "official"
        it["key"] = "P:" + it["ref"]
    bitems = booklet_entries()
    by_unit = defaultdict(list)
    for it in items:
        by_unit[it["topic"]].append(it)
    for t in by_unit:
        by_unit[t].sort(key=lambda i: tuple(-x for x in i["sort"][:3]) + tuple(-x for x in i["sort"][3:]))
    for it in sorted(bitems, key=lambda i: i["sort"]):
        by_unit[it["topic"]].append(it)
    papers = sorted({(i["year"], i["series"], i["variant"], i["paper_ref"]) for i in items},
                    key=lambda p: (p[0], {"m": 1, "s": 2, "w": 3}[p[1]], p[2]))
    byears = sorted({i["year"] for i in bitems})
    stats = [f"Official papers: {len(papers)} ({papers[0][3]} to {papers[-1][3]}), {len(items)} items, "
             f"{sum(i['marks'] for i in items)} marks",
             f"Booklet: {len(bitems)} items from {byears[0]}–{byears[-1]} papers (Read and Write booklet scan)",
             f"{len(items) + len(bitems)} items across {len(by_unit)} units"]
    out = pymupdf.open()
    cover(out, stats)
    n_rows = 2 * len(TOPICS) + 2
    n_front = 1 + (n_rows * 16 + 120) // int(H - MB - 70 - 35) + 1
    front = []
    for _ in range(n_front - 1):
        out.new_page(width=W, height=H)
        front.append(out.page_count - 1)
    f = Flow(out)
    rows, ref_pages, unit_ranges, numbers = [], {}, {}, {}
    for t in TOPICS:
        its = by_unit.get(t, [])
        start = out.page_count
        unit_title_page(f, t, its)
        name = f"Unit {t}: {TOPICS[t]}"
        f.new_page(name)
        f.banner(name)
        for k, it in enumerate(its, 1):
            numbers[it["key"]] = k
            if it["kind"] == "official":
                P = parts[it["paper"]]
                Q = next(q for q in P["questions"] if q["n"] == it["q"])
                qd = docs(P["qp"])
                place_item(f, k, it, item_blocks(it, Q, qd), ref_pages, qd)
            else:
                place_item(f, k, it, [(None, booklet_bands(bd, it["regions"], it["whiteouts"]))], ref_pages, bd)
        f.new_page(f"Unit {t}: Answers Section")
        f.banner("Answers Section", center=True)
        a_page = out.page_count
        for k, it in enumerate(its, 1):
            if it["kind"] == "official":
                P = parts[it["paper"]]
                Q = next(q for q in P["questions"] if q["n"] == it["q"])
                place_answer(f, k, it, Q, docs(P["ms"]))
            else:
                place_booklet_answer(f, k, it, bd)
        unit_ranges[t] = (start, out.page_count - 1)
        rows.append((f"UNIT {t}", (TOPICS[t], True), start + 1))
        rows.append((None, ("Answers Section", False), a_page))
    # index
    f.new_page("Topic index")
    f.banner("Topic index: where each item was filed")
    idx_page = out.page_count
    so = {"w": 3, "s": 2, "m": 1}
    idx = sorted(items, key=lambda i: (-i["year"], -so[i["series"]], i["variant"], i["q"], i["sort"][4] * -1)) + \
        sorted(bitems, key=lambda i: i["sort"])
    cols = [ML, ML + 165, ML + 200, ML + 235, ML + 268, ML + 318]
    def head():
        for x, h in zip(cols, ["Reference", "Unit", "Marks", "Page", "Source", "Also / context / notes"]):
            put(f.page, (x, f.y + 8), h, "hebo", 8)
        f.y += 14
        f.page.draw_line((ML, f.y - 3), (W - MR, f.y - 3), color=GREY, width=0.4)
    head()
    csvrows, jl = [], []
    for it in idx:
        if f.room() < 14:
            f.new_page("Topic index")
            head()
        extra, ctxp = [], []
        if it["kind"] == "official":
            if it["also"]:
                extra.append("also " + ", ".join(f"U{k}:{v}" for k, v in it["also"].items()))
            ctxp = [c.replace("#intro", " intro") for c in it["ctx_parts"]] + it["ctx_blocks"]
            if ctxp:
                extra.append("ctx " + ", ".join(ctxp))
            src, mk = "official", str(it["marks"])
        else:
            extra = [f"booklet unit {it['booklet_unit']} #{it['booklet_n']}"] + \
                [n for n in it["notes"][1:]] + it["answer_notes"]
            src, mk = "booklet", "–"
        vals = [it["ref"], str(it["topic"]), mk, str(ref_pages[it["key"]]), src, "; ".join(extra)]
        for x, v in zip(cols, vals):
            s = v
            while tlen(s, "helv", 7.5) > (W - MR - x if x == cols[-1] else 999) and len(s) > 4:
                s = s[:-4] + "…"
            put(f.page, (x, f.y + 8), s, "helv", 7.5)
        f.y += 11
        csvrows.append({"reference": it["ref"], "unit": it["topic"],
                        "marks": it["marks"] if it["kind"] == "official" else "",
                        "page": ref_pages[it["key"]], "source": src,
                        "also_topics": ";".join(f"{k}:{v}" for k, v in it["also"].items()) if src == "official" else "",
                        "context_parts": ";".join(ctxp)})
    rows.append(("INDEX", ("Topic index", True), idx_page))
    # appendix: Data and Formulae page(s) from the newest paper
    newest = max(parts.values(), key=lambda p: (p["year"], so[p["series"]], p["variant"]))
    qd = docs(newest["qp"])
    dps = [p for p in qd if special_page(p) == "data"]
    f.new_page("Appendix: Data and Formulae")
    f.banner(f"Appendix: Data and Formulae (from {newest['ref']})")
    app_page = out.page_count
    for k, dp in enumerate(dps):
        clip = data_clip(dp)
        s = min(TW / clip.width, (H - MB - f.y) / clip.height)
        if s < 0.6 and k:
            f.new_page(f.header)
            s = min(TW / clip.width, (H - MB - f.y) / clip.height)
        dest = pymupdf.Rect(ML, f.y, ML + clip.width * s, f.y + clip.height * s)
        f.page.show_pdf_page(dest, qd, dp.number, clip=clip)
        f.y = dest.y1 + 10
    rows.append(("APPENDIX", ("Data and Formulae", True), app_page))
    contents(out, front, rows)
    toc = [[1, "Contents", front[0] + 1]]
    for t in TOPICS:
        r = [x for x in rows if x[0] == f"UNIT {t}"]
        if r:
            toc.append([1, f"Unit {t}: {TOPICS[t]}", r[0][2]])
            ai = rows.index(r[0]) + 1
            toc.append([2, f"Unit {t}: Answers Section", rows[ai][2]])
    toc.append([1, "Topic index", idx_page])
    toc.append([1, "Appendix: Data and Formulae", app_page])
    out.set_toc(toc)
    os.makedirs(outdir, exist_ok=True)
    book = os.path.join(outdir, BOOKNAME)
    out.subset_fonts()
    out.save(book, garbage=4, deflate=True, deflate_fonts=True)
    unit_dir = os.path.join(outdir, "units")
    os.makedirs(unit_dir, exist_ok=True)
    for fn in os.listdir(unit_dir):
        os.remove(os.path.join(unit_dir, fn))
    for t, (a, b) in unit_ranges.items():
        u = pymupdf.open()
        u.insert_pdf(out, from_page=a, to_page=b)
        ai = [x for x in rows if x[0] == f"UNIT {t}"][0]
        ap = rows[rows.index(ai) + 1][2]
        u.set_toc([[1, f"Unit {t}: {TOPICS[t]}", 1], [2, "Answers Section", ap - a]])
        u.subset_fonts()
        u.save(os.path.join(unit_dir, f"Unit-{t:02d}-{TOPICS[t].replace(':', '').replace(' ', '-').replace('.', '').replace(',', '')}.pdf"),
               garbage=4, deflate=True, deflate_fonts=True)
    with open(os.path.join(outdir, "index.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["reference", "unit", "marks", "page", "source", "also_topics",
                                           "context_parts"])
        w.writeheader()
        w.writerows(csvrows)
    # items.jsonl: question (and answer) text of every item: Part B from the official PDFs' text layer,
    # booklet items from the OCR of the scan
    from extract import text_of
    with open(os.path.join(outdir, "items.jsonl"), "w") as fh:
        for it in idx:
            if it["kind"] == "official":
                P = parts[it["paper"]]
                Q = next(q for q in P["questions"] if q["n"] == it["q"])
                md = docs(P["ms"])
                ans = []
                for u in it["units"]:
                    for r in unit_ms_rows(Q, u):
                        for p, rc in r["segs"]:
                            ans.append(md[p].get_text("text", clip=pymupdf.Rect(rc)).strip())
                rec = {"reference": it["ref"], "unit": it["topic"], "marks": it["marks"],
                       "page": ref_pages[it["key"]], "source": "official", "number": numbers[it["key"]],
                       "also_topics": it["also"], "text": text_of(docs(P["qp"]), item_regions(it, Q)),
                       "answer_text": "\n".join(ans)}
            else:
                from booklet_lines import region_text
                rec = {"reference": it["ref"], "unit": it["topic"], "marks": None,
                       "page": ref_pages[it["key"]], "source": "booklet", "number": numbers[it["key"]],
                       "booklet_unit": it["booklet_unit"], "booklet_item": it["booklet_n"],
                       "notes": it["notes"][1:] + it["answer_notes"],
                       "text_note": "booklet item: text is OCR of the scanned page (may contain recognition "
                                    "errors; the page image is authoritative); marks not read",
                       "text": region_text(it["regions"]), "answer_text": region_text(it["answer_regions"])}
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    json.dump({"pages": out.page_count, "ref_pages": ref_pages, "numbers": numbers, "unit_ranges": unit_ranges,
               "contents": rows, "n_official": len(items), "n_booklet": len(bitems)},
              open(os.path.join(WORK, "build_info.json"), "w"), indent=0)
    print(f"book pages {out.page_count}, items {len(items)} official + {len(bitems)} booklet, "
          f"size {os.path.getsize(book)/1e6:.1f} MB")


if __name__ == "__main__":
    build(sys.argv[1])

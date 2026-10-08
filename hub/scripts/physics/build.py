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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SERIES_NAME = {"m": "Feb/March", "s": "May/June", "w": "Oct/Nov"}


class Docs:
    def __init__(self):
        self.d = {}

    def __call__(self, f):
        if f not in self.d:
            self.d[f] = load(os.path.join(ROOT, "hub", "data", f))
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


_LABEL_DOCS = {}


def lost_label_bands(it, Q, qd):
    """A lettered part with no introduction prints its label on the line of its first sub-part, e.g.
    "(c) (i) ...". If the item shows later sub-parts of that letter but not the first one, the label
    would be lost and "(ii)" would read as part of the previous letter. Return a band showing only the
    source's own label (the rest of that line is removed from a copy of the page), placed in paper order."""
    shown = set(it["units"]) | {c.replace("#intro", "") for c in it["ctx_parts"]}
    out = []
    for L in Q["letters"]:
        if not L["letter"] or not L["romans"] or L["label"] in shown or L["intro"]:
            continue
        rl = [R["label"] for R in L["romans"]]
        if rl[0] in shown or not any(r in shown for r in rl):
            continue
        p, y0, y1 = L["romans"][0]["region"][0]
        words = qd[p].get_text("words")
        lw = [w for w in words if w[4] == L["label"] and w[0] < 110 and y0 - 2 <= w[1] <= y0 + 14]
        if not lw:
            continue
        lw = lw[0]
        line = [w for w in words if abs(w[1] - lw[1]) < 3 and w is not lw]
        key = (id(qd), p, round(lw[1]))
        if key not in _LABEL_DOCS:
            d2 = pymupdf.open("pdf", qd.tobytes())
            for w in line:
                d2[p].add_redact_annot(pymupdf.Rect(w[:4]))
            d2[p].apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE,
                                   graphics=pymupdf.PDF_REDACT_LINE_ART_NONE, text=pymupdf.PDF_REDACT_TEXT_REMOVE)
            _LABEL_DOCS[key] = d2
        b = Band(p, lw[1] - 1.5, lw[3] + 1.5, [pymupdf.Rect(lw[2] + 1, lw[1] - 2, 600, lw[3] + 2)])
        b.src = _LABEL_DOCS[key]
        first = next(r for r in rl if r in shown)
        b.before = unit_region(Q, first)[0]
        out.append(b)
    return out


def item_blocks(it, Q, qd):
    bs = bands(qd, item_regions(it, Q))
    for lb in lost_label_bands(it, Q, qd):
        bp, by0 = lb.before[0], lb.before[1]
        k = next((i for i, b in enumerate(bs) if (b.page, b.y0) >= (bp, by0 - 0.5)), len(bs))
        bs.insert(k, lb)
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
        if len(cols):
            # scan blobs in the left margin (binding shadow): a dense ink cluster at the left end, 8 pt or
            # more clear of the content, inside the outer 45 pt, at least 10 pt tall, holding no OCR word,
            # is whited out and left out of the crop width (physics fix). The right margin is never
            # touched: the answer pages print their marks there, and OCR misses some single digits.
            ws = [q for q in bd[p0].get_text("words") if q[1] < y1 and q[3] > y0]
            groups = np.split(cols, np.flatnonzero(np.diff(cols) > 8 * z) + 1)
            while len(groups) > 1:
                g = groups[0]
                gx0, gx1 = BX0 + g[0] / z, BX0 + (g[-1] + 1) / z
                sub = a[:, g[0]:g[-1] + 1]
                rr = np.flatnonzero(sub.any(axis=1))
                box = sub[rr[0]:rr[-1] + 1] if len(rr) else sub[:0]
                if not (gx1 < 45 and len(rr) and (rr[-1] - rr[0] + 1) / z >= 10 and box.mean() >= 0.2
                        and not any(q[0] < gx1 + 1 and q[2] > gx0 - 1 for q in ws)):
                    break
                w.append(pymupdf.Rect(gx0 - 1.5, y0 - 1, gx1 + 1.5, y1 + 1))
                MARGIN_BLOBS.append((p0, round(y0), round(gx0), round(gx1)))
                groups.pop(0)
            cols = np.concatenate(groups)
        x0 = BX0 + cols[0] / z - 2 if len(cols) else 40
        x1 = BX0 + (cols[-1] + 1) / z + 2 if len(cols) else 556
        b = Band(p0, y0, y1, w, x0=max(BX0, x0), x1=min(BX1, x1))
        if BUILD_DOCS:
            # text layer without the whited-out words: own-heading tails whited out in this band -> copy
            # with tails removed too; otherwise the copy with only the booklet headings removed
            own_tail = any(r[5:] == ["t"] and r[0] == p0 and r[2] < y1 and r[4] > y0 for r in wos)
            b.src = BUILD_DOCS["t" if own_tail else "h"]
        out.append(b)
    return out


BUILD_DOCS = {}
MARGIN_BLOBS = []


def booklet_build_docs():
    """In-memory copies of booklet-ocr.pdf for cropping: the invisible OCR text of the booklet's own item
    headings (always hidden in the book) is removed ("h"), and in the second copy also the words of a
    previous item's mark that are whited out at the top of the next item ("t"). The scan is untouched."""
    I = json.load(open(os.path.join(WORK, "booklet_items.json")))
    rects = defaultdict(lambda: {"h": [], "t": []})
    for it in I:
        for r in it.get("whiteouts", []) + it.get("answer_whiteouts", []):
            kind = r[5] if len(r) > 5 else "h"
            # a thin band through the middle of the word: the invisible glyph boxes of the lines above
            # and below (taller than the OCR word boxes) must not be touched
            c = (r[2] + r[4]) / 2
            rects[r[0]][kind].append(pymupdf.Rect(r[1] + 1.5, c - 1.0, r[3] - 1.5, c + 1.0))
    for kind in ("h", "t"):
        d = pymupdf.open(BOOKLET_PDF)
        for p0, rr in rects.items():
            use = rr["h"] + (rr["t"] if kind == "t" else [])
            if not use:
                continue
            pg = d[p0]
            for r in use:
                pg.add_redact_annot(r)
            pg.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE, graphics=pymupdf.PDF_REDACT_LINE_ART_NONE,
                                text=pymupdf.PDF_REDACT_TEXT_REMOVE)
        BUILD_DOCS[kind] = d
    return BUILD_DOCS


# The booklet files two questions twice; one copy sits in a unit whose topic the question does not test.
# That copy is dropped (the copy in the right unit stays): (booklet unit, number) -> reason
MISFILED = {(3, 16): "M/J 19/P21/Q7 (alpha-particle scattering, quarks) is particle physics; kept in booklet "
                     "Unit 12 (book Unit 11), dropped from booklet Unit 3 (book Unit 2, Kinematics)",
            (4, 11): "MAR 20/P22/Q4 (progressive waves, diffraction grating) is waves/superposition; kept in "
                     "booklet Unit 9 (book Unit 8), dropped from booklet Unit 4 (book Unit 3, Dynamics)"}


def booklet_entries():
    """Booklet items with their notes, from work/booklet_items.json and the light check."""
    sys.path.insert(0, os.path.dirname(__file__))
    from map_booklet import UNIT_TO_TOPIC
    I = json.load(open(os.path.join(WORK, "booklet_items.json")))
    C = json.load(open(os.path.join(WORK, "booklet_check.json")))
    outside = {(u, n) for u, n, _, _ in C["outside_syllabus"]}
    dup, dupl = {}, {}
    for ref, locs in C["duplicates"]:
        for u, n in locs:
            dup[(u, n)] = [UNIT_TO_TOPIC[v] for v, m in locs if (v, m) != (u, n)]
            dupl[(u, n)] = [(v, m) for v, m in locs if (v, m) != (u, n)]
    gp = os.path.join(WORK, "gapfill.json")
    G = json.load(open(gp)) if os.path.exists(gp) else {"replace_q": {}, "replace_a": {}, "lost": []}
    out = []
    for it in I:
        u, n = it["unit"], it["n"]
        key = f"B{u}-{n}"
        if (u, n) in MISFILED:
            continue
        notes, anotes = ["booklet (scan + OCR)"], []
        if (u, n) in outside:
            notes.append("May be outside the 2025–27 syllabus")
        oq, oa = G["replace_q"].get(key), G["replace_a"].get(key)
        for fl in it["flags"]:
            if fl.startswith("scan_gap_q"):
                a, b = fl.split(":")[1].split("-")
                notes.append(f"Question from the official paper: printed pages {a}–{b} of the scanned booklet "
                             "are missing" if oq else
                             f"Incomplete in the scanned booklet: its printed pages {a}–{b} are missing")
            elif fl.startswith("scan_gap_a"):
                a, b = fl.split(":")[1].split("-")
                anotes.append(f"Answer from the official mark scheme: printed pages {a}–{b} of the scanned booklet "
                              "are missing" if oa else
                              f"Answer incomplete in the scanned booklet: its printed pages {a}–{b} are missing")
            elif fl == "no_answer":
                anotes.append("Answer from the official mark scheme: printed pages 328–329 of the scanned booklet "
                              "are missing" if oa else
                              "Answer missing from the scanned booklet (printed pages 328–329 are missing)")
        if oq:
            notes[0] = "booklet selection; question from the official paper"
        if (u, n) in dup and not any((v, m) in MISFILED for v, m in [x for x in dupl.get((u, n), [])]):
            notes.append("The booklet also files this question under Unit " + ", ".join(map(str, dup[(u, n)])))
        rp = it["ref_parsed"]
        out.append({"kind": "booklet", "key": f"B{u}-{n}", "ref": it["ref"], "topic": it["topic"],
                    "booklet_unit": u, "booklet_n": n, "marks": None, "year": 2000 + rp["yy"],
                    "regions": it["regions"], "whiteouts": it.get("whiteouts", []),
                    "answer_regions": it["answer_regions"], "answer_whiteouts": it.get("answer_whiteouts", []),
                    "notes": notes, "answer_notes": anotes, "flags": it["flags"],
                    "official_q": oq, "official_a": oa,
                    "sort": (-(2000 + rp["yy"]), u, n)})
    for o in G["lost"]:
        u, n = o["unit"], o["n"]
        out.append({"kind": "booklet", "key": f"B{u}-{n}", "ref": o["ref"], "topic": o["topic"],
                    "booklet_unit": u, "booklet_n": n, "marks": None, "year": o["year"],
                    "regions": [], "whiteouts": [], "answer_regions": [], "answer_whiteouts": [],
                    "notes": ["booklet selection; question and answer from the official paper",
                              "The scanned booklet lost this question (missing pages); only its answer survives"],
                    "answer_notes": ["Answer from the official mark scheme"], "flags": ["lost_in_scan"],
                    "official_q": o, "official_a": o, "sort": (-o["year"], u, n)})
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
    allb0 = [b for _, bs in blocks for b in bs]
    first = 0.0
    if allb0:
        sc = min(1.0, TW / (max(b.x1 for b in allb0) - min(b.x0 for b in allb0)))
        g = allb0[0].grp
        k = 0
        first = allb0[0].h * sc
        while g is not None and k + 1 < len(allb0) and allb0[k + 1].grp == g:   # a figure: keep whole
            k += 1
            first += allb0[k].h * sc + 4
        first = min(first, avail)
    if h > f.room() and h <= avail:
        f.new_page(f.header)
    elif f.room() < max(80, 22 + 10 * len(notes) + first):
        f.new_page(f.header)        # never leave a heading alone at the foot of a page
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


def first_block_h(bs, scale):
    """Height of the leading bands that place_bands keeps on one page (a band with its label/caption,
    a figure group), capped at a page: a heading needs at least this much room under it."""
    from layout import _together, _gap
    if not bs:
        return 0.0
    h, k = bs[0].h * scale, 0
    while k + 1 < len(bs) and (_together(bs[k], bs[k + 1]) or (bs[k].grp is not None and bs[k].grp == bs[k + 1].grp)):
        h += (_gap(bs[k], bs[k + 1]) + bs[k + 1].h) * scale
        k += 1
    return min(h, H - MB - MT - 20)


def place_answer(f, num, it, Q, md):
    rows = []
    for u in it["units"]:
        rows += [(None, r) for r in unit_ms_rows(Q, u)]
    ctx = []
    for c in it.get("deps", []):          # parts whose answer the item uses (decision D2)
        rr = unit_ms_rows(Q, c)
        if rr:
            ctx.append((c, rr))
    from items import _order_key
    labs = [(u, r) for u in it["units"] for r in unit_ms_rows(Q, u)] + [(c, r) for c, rr in ctx for r in rr]
    labs.sort(key=lambda t: _order_key(Q, t[0]))       # answers in paper order, earlier parts included
    rows, ctx = [(None, r) for _, r in labs], []
    segs = [s for _, r in rows for s in r["segs"]]
    if not segs:
        return False
    x0 = min(s[1][0] for s in segs)
    x1 = max(s[1][2] for s in segs)
    bs = [Band(p, r[1], r[3]) for p, r in segs if r[3] - r[1] > 2]
    first_h = first_block_h(bs, min(1.0, TW / (x1 - x0)))
    if f.room() < 30 + first_h:
        f.new_page(f.header)        # never leave an answer heading alone at the foot of a page
    f.text(f"{num}.  {it['ref']}", size=10.5, bold=True, gap=3)
    f.place_bands(md, bs, x0=x0, x1=x1)
    for c, rr in ctx:
        cs = [s for r in rr for s in r["segs"]]
        cbs = [Band(p, r[1], r[3]) for p, r in cs if r[3] - r[1] > 2]
        f.y += 6
        f.place_bands(md, cbs, x0=x0, x1=x1)
    f.y += 14
    return True


def place_official_answer(f, num, it, md):
    """A booklet item whose answer page is missing from the scan: the official MS rows of that question."""
    segs = it["official_a"]["ms_segs"]
    bs = [Band(p, r[1], r[3]) for p, r in segs if r[3] - r[1] > 2]
    x0 = min(r[0] for _, r in segs)
    x1 = max(r[2] for _, r in segs)
    first_h = first_block_h(bs, min(1.0, TW / (x1 - x0)))
    if f.room() < 30 + 10 * len(it["answer_notes"]) + first_h:
        f.new_page(f.header)
    f.text(f"{num}.  {it['ref']}", size=10.5, bold=True, gap=3)
    for n in it["answer_notes"]:
        f.text(n, size=7.5, color=GREY, gap=3)
    f.place_bands(md, bs, x0=x0, x1=x1)
    f.y += 14
    return True


def place_booklet_answer(f, num, it, bd):
    bs = booklet_bands(bd, it["answer_regions"], it["answer_whiteouts"])
    notes = it["answer_notes"]
    first_h = first_block_h(bs, min(1.0, TW / (max(b.x1 for b in bs) - min(b.x0 for b in bs)))) if bs else 0
    if f.room() < 30 + 10 * len(notes) + first_h:
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
    booklet_build_docs()
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
             f"Booklet: {len(bitems)} items from {byears[0]}–{byears[-1]} papers (scanned topical booklet)",
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
            elif it.get("official_q"):
                o = it["official_q"]
                place_item(f, k, it, [(None, bands(docs(o["qp"]), o["regions"]))], ref_pages, docs(o["qp"]))
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
            elif it.get("official_a"):
                place_official_answer(f, k, it, docs(it["official_a"]["ms"]))
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
    # no font subsetting: PyMuPDF's subset_fonts drops glyphs that the source papers' fonts reach through
    # unusual encodings (e.g. the multiplication sign in "2.1 × 10^11 Pa" became a box)
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
                if it.get("official_q"):
                    o = it["official_q"]
                    rec["text"] = text_of(docs(o["qp"]), o["regions"])
                if it.get("official_a"):
                    o = it["official_a"]
                    md = docs(o["ms"])
                    rec["answer_text"] = "\n".join(md[p].get_text("text", clip=pymupdf.Rect(r)).strip()
                                                    for p, r in o["ms_segs"])
                if it.get("official_q") or it.get("official_a"):
                    rec["text_note"] = ("question" if it.get("official_q") else "answer") + \
                        (" and answer" if it.get("official_q") and it.get("official_a") else "") + \
                        " from the official paper's text layer (booklet page missing from the scan); " + \
                        ("" if it.get("official_q") else "question text is OCR of the scan")
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    json.dump({"pages": out.page_count, "ref_pages": ref_pages, "numbers": numbers, "unit_ranges": unit_ranges,
               "contents": rows, "n_official": len(items), "n_booklet": len(bitems)},
              open(os.path.join(WORK, "build_info.json"), "w"), indent=0)
    print(f"book pages {out.page_count}, items {len(items)} official + {len(bitems)} booklet, "
          f"size {os.path.getsize(book)/1e6:.1f} MB")
    import crops
    mb = sorted(set(MARGIN_BLOBS))
    print(f"booklet margin blobs whited out: {len(mb)}", mb)
    te = sorted({(id(None), p, y, tuple(w)) for p, y, w in crops.TOP_EXT})
    print(f"region tops raised over a first-line fraction/superscript: {len(te)}", [t[1:] for t in te][:30])


if __name__ == "__main__":
    build(sys.argv[1])

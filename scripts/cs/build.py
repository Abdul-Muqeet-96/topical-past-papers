"""Stage 4/5: build the two CS workbooks (Paper 1 book: units 1-8; Paper 2
book: units 9-12), the per-unit PDFs, index.csv, items.jsonl and topics.json.

Usage: python3 scripts/cs/build.py phase1 [phase2]
Layout follows Δ-chemistry/layout.md with CS names. Contents page numbers are
filled after the body is rendered (front pages are reserved first), so they
are exact.
"""
import csv, datetime, os, re, sys
from collections import defaultdict
import pymupdf
sys.path.insert(0, os.path.dirname(__file__))
from parse import load, paper_ref
from crops import bands, Band, X0, X1
from items import find_letter, letter_of, unit_region, _L
from layout import Flow, put, tlen, W, H, ML, MR, MT, MB, TW, DARK, GREY, ACCENT
from assemble import TOPICS, SECTIONS, LOS, book_of
from extract import text_of
from paths import DATA, OUT, BOOK_FILE, TITLES, SERIES_ORDER, work, jload, jdump
import inserts

BOOK_NAME = {1: "Computer Science 9618 Paper 1 Topical Workbook",
             2: "Computer Science 9618 Paper 2 Topical Workbook"}
INSERT_NOTE = "Uses the insert (Appendix)"
INSERT_INLINE_NOTE = "Insert of this paper (its text differs from the Appendix copy):"
APPENDIX_INLINE_NOTE = "Appendix of this paper:"


class Docs:
    def __init__(self):
        self.d = {}

    def __call__(self, f):
        if f not in self.d:
            self.d[f] = load(os.path.join(DATA, f))
        return self.d[f]


def unit_ms_rows(Q, u):
    if u.endswith("#intro"):
        return []
    L = _L(Q, u)
    if u == L["label"]:
        return L["ms_rows"]
    R = next(R for R in L["romans"] if R["label"] == u)
    return R["ms_rows"]


def item_regions(it, Q):
    """All source regions of an item (stem, context parts, lettered intros, the
    item's own parts), merged in paper order, so the item reads like the paper
    with no generated labels and nothing shown twice (decision D2)."""
    regs = list(Q["stem"])
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


def item_blocks(it, Q, qd, docs):
    """[(source doc, grey note or None, bands)]: the question crops, then the
    paper's own insert / appendix pages when they are shown inline."""
    blocks = [(qd, None, bands(qd, item_regions(it, Q)))]
    if it.get("insert") == "inline":
        by_file = defaultdict(list)
        for kind, f, pg in it["insert_pages"]:
            by_file[(kind, f)].append(pg)
        for (kind, f), pages in by_file.items():
            d = docs(f)
            bs = []
            for pg in pages:
                bs += bands(d, [inserts.content_region(d, pg)])
            for b in bs:
                b.grp = None        # reference pages may break between lines
            blocks.append((d, INSERT_INLINE_NOTE if kind == "in" else APPENDIX_INLINE_NOTE, bs))
    return blocks


def also_text(it):
    if not it["also"]:
        return ""
    parts = [f"Unit {k} ({v} mark{'s' if v != 1 else ''})" for k, v in
             sorted(it["also"].items(), key=lambda kv: -kv[1])]
    main = it["by_topic"].get(str(it["topic"]), 0)
    return f"also {', '.join(parts)}; this unit {main} mark{'s' if main != 1 else ''}"


def est_height(blocks):
    h = 18
    for _, note, bs in blocks:
        if bs:
            w = max(b.x1 for b in bs) - min(b.x0 for b in bs)
            h += Flow.bands_height(bs, min(1.0, TW / w)) + 4 + (12 if note else 0)
    return h


def place_item(f, num, it, blocks, ref_pages):
    h = est_height(blocks) + (10 if it["also"] else 0) + (10 if it.get("insert") == "note" else 0)
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
    if it.get("insert") == "note":
        f.text(INSERT_NOTE, size=7.5, color=GREY, gap=3)
    for src, note, bs in blocks:
        if not bs:
            continue
        if note:
            f.y += 4
            f.text(note, size=7.5, color=GREY, gap=3)
        x0 = min(b.x0 for b in bs)
        x1 = max(b.x1 for b in bs)
        f.place_bands(src, bs, x0=x0, x1=x1)
        f.y += 2
    f.y += 14


def answer_segs(it, Q):
    rows = []
    for u in it["units"]:
        rows += unit_ms_rows(Q, u)
    ctx = []
    for c in it.get("deps", []):          # parts whose answer the item uses (decision D2)
        rr = unit_ms_rows(Q, c)
        if rr:
            ctx.append((c, rr))
    return rows, ctx


def place_answer(f, num, it, Q, md, ans_pages):
    rows, ctx = answer_segs(it, Q)
    segs = [s for r in rows for s in r["segs"]]
    if not segs:
        return False
    x0 = min(s[1][0] for s in segs)
    x1 = max(s[1][2] for s in segs)
    bs = [Band(p, r[1], r[3]) for p, r in segs if r[3] - r[1] > 2]
    first_h = (bs[0].h * min(1.0, TW / (x1 - x0))) if bs else 0
    if f.room() < 30 + min(first_h, 200):
        f.new_page(f.header)
    f.text(f"{num}.  {it['ref']}", size=10.5, bold=True, gap=3)
    ans_pages[it["ref"]] = f.page.number + 1
    f.place_bands(md, bs, x0=x0, x1=x1)
    for c, rr in ctx:
        cs = [s for r in rr for s in r["segs"]]
        cbs = [Band(p, r[1], r[3]) for p, r in cs if r[3] - r[1] > 2]
        f.y += 6
        f.place_bands(md, cbs, x0=x0, x1=x1)
    f.y += 14
    return True


def ms_text(md, it, Q):
    """Answer text of an item from the mark scheme's text layer (row by row)."""
    rows, ctx = answer_segs(it, Q)
    out = []
    for r in rows + [x for _, rr in ctx for x in rr]:
        for p, rc in r["segs"]:
            t = md[p].get_text("text", clip=pymupdf.Rect(rc))
            out.append(re.sub(r"[ \t]+", " ", t).strip())
    return "\n".join(x for x in out if x)


def cover(doc, book, stats):
    pg = doc.new_page(width=W, height=H)
    pg.draw_rect(pymupdf.Rect(0, 0, W, 300), color=None, fill=DARK)
    for i, c in enumerate([(0.12, 0.38, 0.55), (0.2, 0.55, 0.6), (0.85, 0.6, 0.2)]):
        pg.draw_rect(pymupdf.Rect(ML + i * 26, 60, ML + i * 26 + 18, 78), color=None, fill=c)
    put(pg, (ML, 140), "Computer Science 9618", "hebo", 34, (1, 1, 1))
    sub = {1: "Paper 1 · Theory Fundamentals",
           2: "Paper 2 · Fundamental Problem-solving and Programming Skills"}[book]
    put(pg, (ML, 175), sub, "helv", 16 if book == 1 else 14.5, (0.85, 0.88, 0.92))
    put(pg, (ML, 235), "Part-level Topical Workbook", "hebo", 22, (1, 1, 1))
    put(pg, (ML, 262), "with Mark Scheme", "helv", 14, (0.85, 0.88, 0.92))
    y = 350
    units = "units 1 to 8" if book == 1 else "units 9 to 12"
    bullets = [
        f"Every question part filed under its own syllabus topic ({units} of the 2027-29 syllabus)",
        "Each item carries the official context it needs: stem, code, tables, diagrams, earlier parts",
        "Answer lines removed; tables, trace tables and code to complete kept",
        "Newest papers first; mark scheme in an Answers Section after each unit",
        "Index of every part with its unit, marks and page"
        + ("; pseudocode insert in the Appendix" if book == 2 else ""),
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
        y += 16


def unit_file(t):
    return f"Unit-{t:02d}-{re.sub(r'[^A-Za-z0-9]+', '-', TOPICS[t]).strip('-')}.pdf"


def sort_key(i):
    # newest first; within a paper, question / part order
    y, s, code, nv, nq, no = i["sort"]
    return (-y, -s, -code, -nv, -nq, -no)


def build_book(book, items, parts, docs, ins, phases):
    outdir = OUT[book]
    units = [t for t in TOPICS if book_of(t) == book]
    by_unit = defaultdict(list)
    for it in items:
        by_unit[it["topic"]].append(it)
    for t in by_unit:
        by_unit[t].sort(key=sort_key)
    papers = sorted({(i["year"], SERIES_ORDER[i["series"]], i["code"], i["variant"], i["paper_ref"]) for i in items})
    stats = [f"{len(papers)} papers: {papers[0][4]} to {papers[-1][4]} (newest first in each unit)" if papers
             else "0 papers",
             f"{len(items)} items, {sum(i['marks'] for i in items)} marks across {len(units)} units"]
    codes = sorted({i["code"] for i in items})
    if codes:
        stats.append("Syllabus codes: " + ", ".join(codes) +
                     (" (9608 parts only where the 2027-29 syllabus covers them)" if "9608" in codes else ""))
    cross = sum(1 for i in items if i["paper_no"] != book)
    if cross:
        stats.append(f"{cross} items come from Paper {3 - book} papers (filed here by topic)")
    out = pymupdf.open()
    cover(out, book, stats)
    n_rows = 2 * len(units) + 2
    n_front = 1 + (n_rows * 16 + 120) // int(H - MB - 70 - 35) + 1
    front = []
    for _ in range(n_front - 1):
        out.new_page(width=W, height=H)
        front.append(out.page_count - 1)
    f = Flow(out, BOOK_NAME[book])
    rows, ref_pages, ans_pages, unit_ranges = [], {}, {}, {}
    for t in units:
        its = by_unit.get(t, [])
        start = out.page_count
        unit_title_page(f, t, its)
        name = f"Unit {t}: {TOPICS[t]}"
        f.new_page(name)
        f.banner(name)
        for k, it in enumerate(its, 1):
            P = parts[it["paper"]]
            Q = next(q for q in P["questions"] if q["n"] == it["q"])
            qd = docs(P["qp"])
            place_item(f, k, it, item_blocks(it, Q, qd, docs), ref_pages)
        f.new_page(f"Unit {t}: Answers Section")
        f.banner("Answers Section", center=True)
        a_page = out.page_count
        for k, it in enumerate(its, 1):
            P = parts[it["paper"]]
            Q = next(q for q in P["questions"] if q["n"] == it["q"])
            place_answer(f, k, it, Q, docs(P["ms"]), ans_pages)
        unit_ranges[t] = (start, out.page_count - 1)
        rows.append((f"UNIT {t}", (TOPICS[t], True), start + 1))
        rows.append((None, ("Answers Section", False), a_page))
    # ---------- topic index ----------
    f.new_page("Topic index")
    f.banner("Topic index: where each part was filed")
    idx_page = out.page_count
    idx = sorted(items, key=lambda i: (-i["year"], -SERIES_ORDER[i["series"]], -int(i["code"]), i["variant"],
                                       i["q"], -i["sort"][5]))
    cols = [ML, ML + 185, ML + 220, ML + 255, ML + 295]

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
        ctxp = [c.replace("#intro", " intro") for c in it["ctx_parts"]]
        if ctxp:
            extra.append("ctx " + ", ".join(ctxp))
        if it.get("insert"):
            extra.append("insert " + ("(Appendix)" if it["insert"] == "note" else "inline"))
        vals = [it["ref"], str(it["topic"]), str(it["marks"]), str(ref_pages[it["ref"]]), "; ".join(extra)]
        for x, v in zip(cols, vals):
            s = v
            lim = (W - MR - x) if x == cols[-1] else (cols[1] - cols[0] - 4 if x == cols[0] else 999)
            while tlen(s, "helv", 7.5) > lim and len(s) > 4:
                s = s[:-4] + "…"
            put(f.page, (x, f.y + 8), s, "helv", 7.5)
        f.y += 11
        csvrows.append({"reference": it["ref"], "unit": it["topic"], "marks": it["marks"],
                        "page": ref_pages[it["ref"]],
                        "also_topics": ";".join(f"{k}:{v}" for k, v in it["also"].items()),
                        "context_parts": ";".join(ctxp),
                        "sections": ";".join(it["sections"]), "answer_page": ans_pages.get(it["ref"], ""),
                        "insert": it.get("insert") or ""})
    rows.append(("INDEX", ("Topic index", True), idx_page))
    # ---------- appendix (P2 book): the newest insert, once ----------
    app_page, app_name = None, None
    if book == 2 and ins.appendix():
        kind, fn, pages, _, _ = ins.appendix()
        ref = paper_ref(docs(fn))            # from the insert's own header text
        app_name = "Insert: pseudocode functions and operators"
        f.new_page("Appendix: Insert")
        f.banner(f"Appendix: {app_name} (from {ref})")
        app_page = out.page_count
        d = docs(fn)
        for pg in pages:
            bs = bands(d, [inserts.content_region(d, pg)])
            for b in bs:
                b.grp = None
            if bs:
                f.place_bands(d, bs, x0=min(b.x0 for b in bs), x1=max(b.x1 for b in bs))
                f.y += 10
        rows.append(("APPENDIX", (app_name, True), app_page))
    contents(out, front, rows)
    toc = [[1, "Contents", front[0] + 1]]
    for t in units:
        r = [x for x in rows if x[0] == f"UNIT {t}"][0]
        toc.append([1, f"Unit {t}: {TOPICS[t]}", r[2]])
        toc.append([2, f"Unit {t}: Answers Section", rows[rows.index(r) + 1][2]])
    toc.append([1, "Topic index", idx_page])
    if app_page:
        toc.append([1, f"Appendix: {app_name}", app_page])
    out.set_toc(toc)
    out.set_metadata({"title": BOOK_NAME[book], "subject": TITLES[book],
                      "creator": "topical-past-papers scripts/cs", "producer": "PyMuPDF"})
    os.makedirs(outdir, exist_ok=True)
    bookf = os.path.join(outdir, BOOK_FILE[book])
    out.subset_fonts()
    out.save(bookf, garbage=4, deflate=True, deflate_fonts=True)
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
        u.save(os.path.join(unit_dir, unit_file(t)), garbage=4, deflate=True, deflate_fonts=True)
    with open(os.path.join(outdir, "index.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["reference", "unit", "marks", "page", "also_topics", "context_parts",
                                           "sections", "answer_page", "insert"])
        w.writeheader()
        w.writerows(csvrows)
    # items.jsonl: each item's question and answer text from the source text layers
    import json
    with open(os.path.join(outdir, "items.jsonl"), "w") as fh:
        for it in idx:
            P = parts[it["paper"]]
            Q = next(q for q in P["questions"] if q["n"] == it["q"])
            fh.write(json.dumps({"reference": it["ref"], "syllabus_code": it["code"], "book": f"P{book}",
                                 "unit": it["topic"], "unit_name": TOPICS[it["topic"]],
                                 "sections": it["sections"], "learning_outcomes": it["los"],
                                 "marks": it["marks"], "page": ref_pages[it["ref"]],
                                 "answer_page": ans_pages.get(it["ref"]),
                                 "also_units": it["also"], "context_parts": it["ctx_parts"],
                                 "insert": {"note": "appendix", "inline": "inline"}.get(it.get("insert")),
                                 "text": text_of(docs(P["qp"]), item_regions(it, Q)),
                                 "answer_text": ms_text(docs(P["ms"]), it, Q)},
                                ensure_ascii=False) + "\n")
    # topics.json: every lowest-level part filed in this book, with its syllabus justification
    where = {}
    for it in items:
        Q = next(q for q in parts[it["paper"]]["questions"] if q["n"] == it["q"])
        for u in it["units"]:
            L = _L(Q, u)
            for lab in ([R["label"] for R in L["romans"]] if (u == L["label"] and L["romans"]) else [u]):
                where[(it["paper"], it["q"], lab)] = it["ref"]
    tp = []
    for ph in phases:
        for t in jload(work(f"topics_{ph}.json")):
            ref = where.get((t["paper"], t["q"], t["part"]))
            unfiled_here = ref is None and ((t["unit"] and book_of(t["unit"]) == book) or
                                            (not t["unit"] and parts[t["paper"]]["paper"] == book))
            if ref is not None or unfiled_here:
                tp.append(dict(t, phase=ph, item=ref, filed_unit=next((i["topic"] for i in items if i["ref"] == ref),
                                                                      None) if ref else None))
    jdump(tp, os.path.join(outdir, "topics.json"))
    info = {"book": book, "file": BOOK_FILE[book], "pages": out.page_count, "ref_pages": ref_pages,
            "ans_pages": ans_pages, "unit_ranges": {str(k): v for k, v in unit_ranges.items()}, "contents": rows,
            "items": len(items), "front": front, "index_page": idx_page, "appendix_page": app_page}
    jdump(info, work(f"build_info_p{book}.json"), indent=0)
    print(f"P{book} book: pages {out.page_count}, items {len(items)}, marks {sum(i['marks'] for i in items)}, "
          f"size {os.path.getsize(bookf) / 1e6:.1f} MB")
    return info


def build(phases):
    docs = Docs()
    ins = inserts.Inserts()
    items, parts = [], {}
    for ph in phases:
        items += jload(work(f"items_{ph}.json"))
        parts.update(jload(work(f"parts_{ph}.json")))
    refs = [i["ref"] for i in items]
    assert len(refs) == len(set(refs)), "duplicate item references"
    for book in (1, 2):
        build_book(book, [i for i in items if i["book"] == book], parts, docs, ins, phases)


if __name__ == "__main__":
    build(sys.argv[1:])

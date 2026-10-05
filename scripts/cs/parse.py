"""Parse 9618 / 9608 Paper 1 and Paper 2 question papers and mark schemes from
the PDF text layer.

QP: question numbers, lettered parts (a), roman sub-parts (i), [marks], with
page/y positions so regions can be cropped later. CS papers print no
[Total: n] per question; the cover prints the paper total (75).
MS: table rows keyed by labels like 3(c)(ii), with their marks and the
row rectangles (one per page segment).
All pages are de-rotated first so coordinates match the displayed page.
"""
import os, re
import pymupdf

ROMANS = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"]
LETTERS = "abcdefghijklmnop"
SERIES = {"February/March": "MAR", "May/June": "M/J", "October/November": "O/N", "March": "MAR"}
CODES = "9618|9608"

RE_MARK = re.compile(r"(?:^|[.…_ ])\[(\d+)\]$")
RE_TOTAL = re.compile(r"\[Total:\s*(\d+)\]")
RE_MS_TYPO = re.compile(r"^(\d{1,2})\(?([a-h])\)?(?:\(?(i|ii|iii|iv|v|vi|vii|viii|ix|x)\)?)?$")
MS_TYPOS = []   # (original token, normalised label) seen while reading mark schemes


def fix_label(tok):
    """Typo-tolerant MS label (audit A-009, decision D6): '4(a(i)' -> '4(a)(i)',
    '5f)' -> '5(f)', '2c(i)' -> '2(c)(i)'. Only tokens that are a question number
    followed by a letter (and optional roman) with missing brackets are changed."""
    if RE_MS_LABEL.match(tok) or not re.match(r"^\d{1,2}\(?[a-h]", tok):
        return tok
    m = RE_MS_TYPO.match(tok)
    if not m:
        return tok
    lab = f"{m.group(1)}({m.group(2)})" + (f"({m.group(3)})" if m.group(3) else "")
    MS_TYPOS.append((tok, lab))
    return lab


RE_MS_LABEL = re.compile(r"^(\d{1,2})((?:\([a-z]\))?)((?:\((?:i|ii|iii|iv|v|vi|vii|viii|ix|x)\))?)$")


RE_WM = re.compile(rb"/FormXob\.pcm\s+Do")


def strip_watermark(d):
    """Remove the download site's tiled watermark (Form XObject 'FormXob.pcm')
    from every content stream, in memory only. Returns number of removals."""
    n = 0
    for x in range(1, d.xref_length()):
        try:
            if not d.xref_is_stream(x):
                continue
            st = d.xref_stream(x)
        except Exception:
            continue
        if not st or (b"FormXob.pcm" not in st and b"gRLs" not in st and b"Trace ID" not in st):
            continue
        new, k = RE_WM.subn(b"", st)
        new, k2 = _drop_wm_blocks(new)
        new, k3 = RE_WM_FOOT.subn(b"", new)
        if k or k2 or k3:
            d.update_stream(x, new)
            n += k + k2 + k3
    return n


# footer block added by the download site: a thin rule, the site name and
# invisible lines ending in "Trace ID: ..." (seen on the 9618 files)
RE_WM_FOOT = re.compile(rb"0\.78 0\.82 0\.86 RG\s+0\.4 w\s+n\s.{0,4000}?Trace ID.{0,80}?T\*\s+ET", re.S)


RE_WM_BLOCK = re.compile(rb"(?<![^\s])q\s+0?\.055 0?\.227 0?\.361 rg\s+/gRLs\S* gs")


def _drop_wm_blocks(st):
    """Remove 'q <watermark colour> rg /gRLs.. gs ... Q' blocks (inline glyph
    paths of the watermark), matching q/Q nesting."""
    out, pos, k = [], 0, 0
    for m in RE_WM_BLOCK.finditer(st):
        if m.start() < pos:
            continue
        depth, i = 0, m.start()
        toks = re.finditer(rb"(?<![^\s])([qQ])(?![^\s])", st[m.start():])
        end = None
        for t in toks:
            depth += 1 if t.group(1) == b"q" else -1
            if depth == 0:
                end = m.start() + t.end()
                break
        if end is None:
            continue
        out.append(st[pos:m.start()])
        pos = end
        k += 1
    out.append(st[pos:])
    return b"".join(out), k


_UID = [0]


def doc_key(doc):
    """A key for per-document caches that is never reused. (id(doc) is reused
    by Python once a document has been freed, which would hand one paper the
    cached pages of another.)"""
    k = getattr(doc, "_uid", None)
    if k is None:
        _UID[0] += 1
        k = doc._uid = _UID[0]
    return k


A4 = pymupdf.Rect(0, 0, 595.28, 841.89)
RE_DOTRUN = re.compile(r"[.…]{5,}")


def content_scale(d):
    """Scale of the printed content relative to a standard A4 paper, from the
    '©' footer word (x0 = 50 pt on standard pages; scaled about the origin).
    s15 v21 is A3-sized (x1.41); m20, s21, w19/w20 v21 are printed at 0.9-0.95."""
    ks = []
    for p in d:
        ws = [w for w in p.get_text("words") if w[4] == "©" and w[1] > p.rect.height * 0.8]
        if ws:
            ks.append(ws[0][0] / 50.0)
    if not ks:
        return 1.0
    ks.sort()
    k = ks[len(ks) // 2]
    return k if abs(k - 1) > 0.03 else 1.0


def visual_lines(page):
    """Characters of the page grouped into visual lines (same baseline), each
    sorted by x: [[char dict, ...], ...]. Rawdict lines can split one printed
    line into pieces, so the grouping is by baseline."""
    chars = []
    for b in page.get_text("rawdict")["blocks"]:
        for l in b.get("lines", []):
            if abs(l["dir"][0] - 1) > 0.01:
                continue          # rotated margin text
            for s in l["spans"]:
                chars += s["chars"]
    chars.sort(key=lambda c: (round(c["origin"][1]), c["origin"][0]))
    lines = []
    for c in chars:
        if lines and abs(lines[-1][-1]["origin"][1] - c["origin"][1]) < 2.0:
            lines[-1].append(c)
        else:
            lines.append([c])
    for ln in lines:
        ln.sort(key=lambda c: c["origin"][0])
    return lines


def dot_runs(page):
    """Runs of 5+ dots on the page: [(Rect, is_answer_line)].

    An answer line (removed from crops and from the text layer) is a run that
    reaches the right-hand margin or is long, on a line with little other text.
    A short run inside a line of code or a sentence is a gap the candidate must
    fill ("DECLARE Pass : ........", "IF ........ (Pass) < 6") and is kept."""
    out = []
    for ln in visual_lines(page):
        txt = "".join(c["c"] for c in ln)
        runs = list(RE_DOTRUN.finditer(txt))
        if not runs:
            continue
        rest = RE_DOTRUN.sub(" ", txt)
        rest = re.sub(r"\[\d+\]\s*$", "", rest)
        other = len(re.sub(r"[\s.…]", "", rest))
        for m in runs:
            run = ln[m.start():m.end()]
            x0, x1 = run[0]["bbox"][0], run[-1]["bbox"][2]
            y0 = min(c["bbox"][1] for c in run)
            y1 = max(c["bbox"][3] for c in run)
            after = len(re.sub(r"[\s.…]", "", re.sub(r"\[\d+\]\s*$", "", txt[m.end():])))
            long_ = (x1 - x0) >= GAP_MAX_W
            if after:
                answer = long_ or other < 6
            else:
                answer = long_ or x1 > 500
            out.append((pymupdf.Rect(x0, y0, x1, y1), answer, run[0]["origin"][1]))
    return out


GAP_MAX_W = 250    # a dotted run at least this wide is an answer line, never a gap


def redact_dot_runs(d):
    """Remove answer-line glyphs (runs of 5+ dots) from the text layer itself,
    so the book's text layer holds no hidden '......' (audit A-020). Only the
    dot characters are removed; every other glyph and all graphics stay.
    Gaps to fill inside code or sentences are kept (see dot_runs)."""
    n = 0
    for p in d:
        # a thin band just above the baseline: it meets every dot of the run but not
        # the line below (a [mark] is often printed directly under a dotted line)
        rects = [pymupdf.Rect(r.x0 + 0.4, base - 4.0, r.x1 - 0.4, base - 1.0)
                 for r, answer, base in dot_runs(p) if answer]
        for r in rects:
            p.add_redact_annot(r)
        if rects:
            p.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE,
                               graphics=pymupdf.PDF_REDACT_LINE_ART_NONE,
                               text=pymupdf.PDF_REDACT_TEXT_REMOVE)
            n += len(rects)
    return n


def normalise(d):
    """Return a copy of d whose pages are A4 with the content at standard scale
    (audit A-007/A-005): every coordinate rule then applies to every paper."""
    k = content_scale(d)
    if k == 1.0 and all(abs(p.rect.width - A4.width) < 2 and abs(p.rect.height - A4.height) < 2 for p in d):
        return d
    out = pymupdf.open()
    for p in d:
        np = out.new_page(width=A4.width, height=A4.height)
        clip = pymupdf.Rect(0, 0, A4.width * k, A4.height * k) & p.rect
        np.show_pdf_page(pymupdf.Rect(0, 0, clip.width / k, clip.height / k), d, p.number, clip=clip)
    out.scale_k = k
    return out


def load(path, redact=None):
    d = pymupdf.open(path)
    strip_watermark(d)
    for p in d:
        if p.rotation:
            p.remove_rotation()
    if redact is None:
        redact = "_qp_" in os.path.basename(path)   # inserts and mark schemes keep every glyph
    if redact:
        redact_dot_runs(d)
    base = os.path.basename(path)
    return normalise(d) if ("_qp_" in base or "_in_" in base) else d


def norm_text(t):
    t = re.sub(r"[‐‑‒–—]", "-", t)
    return re.sub(r"\s+", " ", t)


def paper_ref(doc):
    """Reference from the paper's own page-1 header, e.g. 'M/J 25/P12'."""
    t = norm_text(doc[0].get_text())
    m = re.search(rf"(?:{CODES})/([12]\d)\b", t)
    s = re.search(r"(February/March|May/June|October/November) (20\d\d)", t)
    if not (m and s):
        return None
    return f"{SERIES[s.group(1)]} {s.group(2)[2:]}/P{m.group(1)}"


def cover_total(doc):
    """Paper total printed on the cover ('The total mark for this paper is 75';
    older papers: 'The maximum number of marks is 75')."""
    t = norm_text(doc[0].get_text())
    m = re.search(r"total mark for this paper is (\d+)", t) or \
        re.search(r"maximum number of marks (?:for this paper )?is (\d+)", t) or \
        re.search(r"Maximum Mark:? (\d+)", t)
    return int(m.group(1)) if m else None


RE_FOOT = re.compile(rf"(?:{CODES})/\d\d/\S+")


RE_BOILER = re.compile(r"Permission to reproduce|To avoid the issue of disclosure|Every reasonable effort|"
                       r"Cambridge Assessment International Education is part|is a department of the University|"
                       r"Cambridge International Examinations is part|copyright holders", re.I)
_BOIL = {}


def boiler_top(page):
    """y of the top of the small-print copyright paragraph, if the page has one
    in its lower half (it is not question material); else None."""
    key = (doc_key(page.parent), page.number)
    if key not in _BOIL:
        top = None
        for b in page.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                if l["bbox"][1] > page.rect.height * 0.5 and l["spans"] and l["spans"][0]["size"] < 9.5 \
                        and RE_BOILER.search("".join(sp["text"] for sp in l["spans"])):
                    top = l["bbox"][1] if top is None else min(top, l["bbox"][1])
        _BOIL[key] = top
        if len(_BOIL) > 400:
            _BOIL.pop(next(iter(_BOIL)))
    return _BOIL[key]


def page_lines(page, top=46, bottom=798.5, left=25, right=572):
    """Text lines (list of word tuples) inside the content area, sorted by y."""
    allw = page.get_text("words")
    foot = [w[1] for w in allw if w[1] > 740 and (w[4] == "©" or RE_FOOT.fullmatch(w[4]))]
    bt = boiler_top(page)
    if bt is not None:
        foot.append(bt - 1.5)
    if foot:
        bottom = min(foot) - 0.5
    words = [w for w in allw
             if w[1] >= top and (w[3] <= bottom or (w[3] <= bottom + 5 and w[1] < bottom - 8
                                                    and re.fullmatch(r"\[\d+\]", w[4])))
             and w[0] >= left and w[2] <= right
             and (w[3] - w[1]) >= 6.5]
    # the footer's "[Turn over" (the word "over" beside "[Turn" only: "over" is also
    # an ordinary word of question text)
    turn = [w for w in words if w[4] == "[Turn"]
    words = [w for w in words if w[4] != "[Turn" and not (
        w[4] == "over" and any(abs(t[1] - w[1]) < 3 and 0 <= w[0] - t[2] < 12 for t in turn))]
    lines = {}
    for w in words:
        lines.setdefault((w[5], w[6]), []).append(w)
    out = []
    for ws in lines.values():
        ws.sort(key=lambda w: w[0])
        out.append(ws)
    # merge lines that share a baseline (labels are often separate blocks)
    out.sort(key=lambda ws: (round(ws[0][3]), ws[0][0]))
    merged = []
    for ws in out:
        if merged and abs(merged[-1][0][3] - ws[0][3]) < 2.5:
            merged[-1] = sorted(merged[-1] + ws, key=lambda w: w[0])
        else:
            merged.append(ws)
    merged.sort(key=lambda ws: (min(w[1] for w in ws), ws[0][0]))
    return merged


_SPECIAL = {}


def special_page(page):
    """'blank' for a BLANK PAGE; 'appendix' for the built-in function list that
    older papers print inside the question paper (reference material, not a
    question), including its continuation pages."""
    doc = page.parent
    k = doc_key(doc)
    if k not in _SPECIAL:
        out = []
        for p in doc:
            kind = _special_one(p)
            if kind is None and out and out[-1] == "appendix" and not _has_marks(p):
                kind = "appendix"          # the list continues (operators, further functions)
            out.append(kind)
        _SPECIAL[k] = out
    return _SPECIAL[k][page.number]


def _has_marks(page):
    return any(re.fullmatch(r"\[\d+\]", w[4]) and w[0] > 495 for w in page.get_text("words"))


def _special_one(page):
    t = re.sub(r"[‐‑‒–—]", "-", page.get_text())
    body = "\n".join(l for l in t.splitlines()
                     if l.strip() and "DO NOT WRITE" not in l and not re.search(r"©|UCLES|^\s*\*", l))
    if "BLANK PAGE" in t and len(body.strip()) < 900 and not re.search(r"\[\d+\]", body):
        return "blank"
    if page.number > 0 and re.search(r"^\s*Appendix\s*$", t, re.M) and \
            re.search(r"built-in functions|pseudocode functions|STRING Functions|"
                      r"String and character functions|operators", t, re.I) and not _has_marks(page):
        return "appendix"
    return None


def data_cut(page):
    """Kept for the shared region code: CS papers have no data block."""
    return None


def _mono_word(page, w):
    """Is the word set in a monospace font (a line number of a code listing,
    not a question number)? Character advance of 0.6 em."""
    for b in page.get_text("rawdict", clip=pymupdf.Rect(w[0] - 1, w[1] - 1, w[2] + 1, w[3] + 1))["blocks"]:
        for l in b.get("lines", []):
            for sp in l["spans"]:
                cs = [c for c in sp["chars"] if not c["c"].isspace()]
                if cs and all(abs((c["bbox"][2] - c["bbox"][0]) / (sp["size"] or 1) - 0.6) < 0.006 for c in cs):
                    return True
    return False


def _join_marks(ws):
    """A mark printed as two words ('[1' and ']') becomes one word."""
    out = []
    for w in ws:
        if out and w[4] == "]" and re.search(r"\[\d+$", out[-1][4]) and 0 <= w[0] - out[-1][2] < 8:
            p = out[-1]
            out[-1] = (p[0], min(p[1], w[1]), w[2], max(p[3], w[3]), p[4] + "]") + tuple(p[5:])
        else:
            out.append(w)
    return out


def use_secondary_marks(qs, total):
    """If the right-aligned marks do not reach the cover total but adding the
    lone marks printed a little short of the margin does, accept those marks.
    Returns the list of accepted marks."""
    s1 = sum(m["value"] for q in qs for m in q["marks"])
    extra = [(q, m) for q in qs for m in q.get("marks2", [])]
    if total is None or s1 == total or not extra or s1 + sum(m["value"] for _, m in extra) != total:
        return []
    for q, m in extra:
        q["marks"].append(m)
        q["marks"].sort(key=lambda m: (m["pos"][0], m["pos"][1]))
        if q.get("last_mark") is None or (m["pos"][0], m["pos"][2]) > tuple(q["last_mark"]):
            q["last_mark"] = (m["pos"][0], m["pos"][2])
    return [m for _, m in extra]


def parse_qp(doc):
    """Return dict with questions -> labels, marks, totals and positions."""
    qs = []          # list of question dicts
    cur_q = None
    cur_l = None     # current letter
    cur_r = None     # current roman
    events = []
    for pno in range(1, doc.page_count):
        page = doc[pno]
        if special_page(page):
            continue
        cut = data_cut(page)
        for ws in page_lines(page):
            ws = _join_marks(ws)
            y0 = min(w[1] for w in ws)
            if cut is not None and y0 >= cut - 2:
                break
            y1 = max(w[3] for w in ws)
            i = 0
            while i < len(ws):
                w = ws[i]
                txt, x0 = w[4], w[0]
                nxt_q = (cur_q["n"] + 1) if cur_q else 1
                if i == 0 and re.fullmatch(r"[1-9]\d?", txt) and x0 < 64 and int(txt) == nxt_q \
                        and not _mono_word(page, w):
                    cur_q = {"n": nxt_q, "start": (pno, y0), "parts": [], "marks": [],
                             "total": None, "total_pos": None}
                    qs.append(cur_q)
                    cur_l = cur_r = None
                    events.append(("Q", nxt_q, pno, y0))
                    i += 1
                    continue
                m = re.fullmatch(r"\(([a-z])\)", txt)
                if cur_q and m and x0 < 90 and (i == 0 or ws[i - 1][4] in (str(cur_q["n"]),)):
                    exp = LETTERS[LETTERS.index(cur_l) + 1] if cur_l else "a"
                    if m.group(1) == exp:
                        cur_l, cur_r = exp, None
                        cur_q["parts"].append({"label": f"({exp})", "letter": exp, "roman": None,
                                               "start": (pno, y0), "x0": x0})
                        events.append(("L", exp, pno, y0))
                        i += 1
                        continue
                m = re.fullmatch(r"\(((?:i|ii|iii|iv|v|vi|vii|viii|ix|x))\)", txt)
                if cur_q and m and x0 < 125 and (i == 0 or re.fullmatch(r"\([a-z]\)|\d{1,2}", ws[i - 1][4])):
                    exp = ROMANS[ROMANS.index(cur_r) + 1] if cur_r else "i"
                    if m.group(1) == exp:
                        cur_r = exp
                        lab = f"({cur_l})({exp})" if cur_l else f"({exp})"
                        cur_q["parts"].append({"label": lab, "letter": cur_l, "roman": exp,
                                               "start": (pno, y0), "x0": x0})
                        events.append(("R", exp, pno, y0))
                        i += 1
                        continue
                break
            line = " ".join(w[4] for w in ws)
            if cur_q:
                for wi, w in enumerate(ws):
                    mm = RE_MARK.search(w[4])
                    # a mark is right-aligned at the margin, or closes a dotted answer line
                    # ("........[1]" beside a label in a diagram)
                    dotted = bool(mm and re.fullmatch(r"[.…]{5,}\[\d+\]", w[4]))
                    if mm and not (w[2] > 525 and w[0] > 495) and not dotted \
                            and re.fullmatch(r"\[\d+\]", w[4]) \
                            and not any(re.search(r"\[\d+\]", o[4]) for o in ws if o is not w):
                        # a lone [n] ending a line short of the margin: kept aside; used
                        # only if the paper total cannot be reached without it (see check_papers)
                        lab = (f"({cur_l})" if cur_l else "") + (f"({cur_r})" if cur_r else "")
                        cur_q.setdefault("marks2", []).append({"label": lab, "value": int(mm.group(1)),
                                                               "pos": (pno, w[1], w[3])})
                    if mm and ((w[2] > 525 and w[0] > 495) or dotted):
                        lab = (f"({cur_l})" if cur_l else "") + (f"({cur_r})" if cur_r else "")
                        cur_q["marks"].append({"label": lab, "value": int(mm.group(1)),
                                               "pos": (pno, w[1], w[3])})
                    if mm and ((w[2] > 525 and w[0] > 495) or dotted):
                        cur_q["last_mark"] = (pno, w[3])
                mt = RE_TOTAL.search(line)
                if mt:
                    if cur_q["total"] is None:
                        cur_q["total"] = int(mt.group(1))
                        cur_q["total_pos"] = (pno, y0, y1)
                    else:
                        cur_q["total_dup"] = True
    doc._marks2_used = use_secondary_marks(qs, cover_total(doc))
    return qs


RE_HQ = re.compile(r"^\d{1,2}$")
RE_HL = re.compile(r"^\(([a-h])\)$")
RE_HR = re.compile(r"^\((i|ii|iii|iv|v|vi|vii|viii|ix|x)\)$")


def ms_rows(doc):
    """Rows of the mark-scheme table: [{label, q, part, marks, segs:[(pno, rect)]}].
    Handles both label styles: combined '3(c)(ii)' (2017+) and the older
    column style where '3', '(c)', '(ii)' are separate tokens that carry over
    from row to row. A page may hold several tables; a row may continue onto
    the next page; a 'Total' row ends the previous row and is not a part."""
    rows = []
    open_row = None
    cq = cl = cr = None
    for pno in range(doc.page_count):
        page = doc[pno]
        words = _dedupe(page.get_text("words"))
        drs = page.get_drawings()
        heads = []
        for h in sorted((w for w in words if w[4] == "Question" and w[0] < 140), key=lambda w: w[1]):
            mk = [w for w in words if w[4] in ("Marks", "Mark", "Total") and w[0] > 300 and abs(w[1] - h[1]) < 3]
            if mk:
                tot = [w for w in mk if w[4] == "Total"]
                heads.append((h, tot[0] if tot else max(mk, key=lambda w: w[0])))
        if not heads:
            continue
        foot = [w for w in words if w[4] == "Page" and w[1] > page.rect.height - 70]
        bottom = (min(w[1] for w in foot) - 4) if foot else page.rect.height - 50
        for hi, (h, mk) in enumerate(heads):
            hy = h[3]
            reg_end = heads[hi + 1][0][1] - 6 if hi + 1 < len(heads) else bottom
            tx0 = h[0] - 8
            mx0, mx1 = mk[0] - 12, mk[2] + 12
            bo = mk[4] == "Total"
            gd = any(w[4] == "Guidance" and abs(w[1] - h[1]) < 3 for w in words)
            vr = [d["rect"] for d in drs if d["rect"].width < 2 and d["rect"].height > 4
                  and d["rect"].y1 > hy and d["rect"].y0 < reg_end]
            right = [r.x0 for r in vr if r.x0 > mk[2] - 2]
            if right:   # marks column ends at the next vertical rule (drops off-table duplicates)
                mx1 = min(mx1, min(right) + 1)
            qcol_x1 = min([r.x0 for r in vr if r.x0 > h[0] + 5] or [h[2] + 20])
            table_x1 = max([r.x1 for r in vr] or [page.rect.width - 60])
            tab_bottom = max([r.y1 for r in vr if r.y1 <= reg_end + 1] or [reg_end])
            # full-width row rules only (rules of tables nested in a cell start further right)
            hr = sorted({round(d["rect"].y0, 1) for d in drs
                         if d["rect"].height < 2 and d["rect"].width > 30 and d["rect"].x0 < tx0 + 12
                         and hy < d["rect"].y0 < reg_end})
            qx0 = min([r.x0 for r in vr if r.x0 < h[0]] or [h[0] - 15]) - 2
            qw = sorted([w for w in words if hy < w[1] < tab_bottom and w[2] <= qcol_x1 + 4 and w[0] >= qx0],
                        key=lambda w: (w[1], w[0]))
            lines = []
            for w in qw:
                if lines and abs(lines[-1][0][1] - w[1]) < 3:
                    lines[-1].append(w)
                else:
                    lines.append([w])
            starts = []      # (top, label or None for 'Total', first word)
            # (Chemistry's answer-column 'Total' rows are not used: CS answers contain
            # identifiers such as Total, and CS mark schemes print no question totals)
            for ln in lines:
                ln.sort(key=lambda w: w[0])
                toks = [w[4] for w in ln]
                toks[0] = fix_label(toks[0])
                lab = None
                if toks[0] == "Total":
                    starts.append((ln[0][1], None, ln[0]))
                    continue
                if RE_MS_LABEL.match(toks[0]) and "(" in toks[0] or (RE_MS_LABEL.match(toks[0]) and len(toks) == 1
                                                                    and not RE_HQ.match(toks[0])):
                    lab = toks[0]
                elif all(RE_HQ.match(t) or RE_HL.match(t) or RE_HR.match(t) for t in toks):
                    q, l, r = cq, cl, cr
                    for t in toks:
                        if RE_HQ.match(t):
                            q, l, r = int(t), None, None
                        elif RE_HL.match(t) and not (RE_HR.match(t) and l is not None):
                            l, r = RE_HL.match(t).group(1), None
                        elif RE_HR.match(t):
                            r = RE_HR.match(t).group(1)
                    if q is None:
                        continue
                    cq, cl, cr = q, l, r
                    lab = f"{q}" + (f"({l})" if l else "") + (f"({r})" if r else "")
                elif RE_MS_LABEL.match(toks[0]):
                    lab = toks[0]
                if lab and RE_MS_LABEL.match(lab):
                    starts.append((ln[0][1], lab, ln[0]))
            starts.sort(key=lambda t: t[0])
            row_starts = []
            for y0, lab, w in starts:
                above = [y for y in hr if y <= y0 + 1]
                row_starts.append((max(above) if above else (y0 - 3 if not hr else hy + 2), lab, w))
            first_top = row_starts[0][0] if row_starts else tab_bottom
            start_hdr = min(hr or [hy + 4])
            if hi == 0 and open_row is not None and first_top - start_hdr > 8:
                seg = pymupdf.Rect(tx0, start_hdr - 0.5, table_x1 + 1, first_top + 0.5)
                open_row["segs"].append((pno, seg))
                open_row["marks"] += _marks_in(words, seg, mx0, mx1, bo, None if bo else mk[2] - 1)
            for k, (top, lab, w) in enumerate(row_starts):
                end = row_starts[k + 1][0] if k + 1 < len(row_starts) else tab_bottom
                if lab is None:          # 'Total' row
                    open_row = None
                    continue
                seg = pymupdf.Rect(tx0, top - 0.5, table_x1 + 1, end + 0.5)
                m = RE_MS_LABEL.match(lab)
                row = {"label": lab, "q": int(m.group(1)), "part": m.group(2) + m.group(3),
                       "segs": [(pno, seg)], "marks": _marks_in(words, seg, mx0, mx1, bo, None if bo else mk[2] - 1),
                       "na": any(w2[4] == "N/A" for w2 in words if w2[0] >= mx0 and w2[2] <= mx1
                                 and seg.y0 - 1 <= w2[1] <= seg.y1),
                       "guidance": gd, "total_col": bo}
                rows.append(row)
                open_row = row
    # older layouts print the question total after the last part's marks:
    # drop a final value that equals the sum of all other marks of that question
    for r in rows:
        # part total printed above its per-point marks: [2, 1, 1] -> [2]
        m = r["marks"]
        if len(m) >= 3 and m[0] == sum(m[1:]) and all(v == 1 for v in m[1:]):
            r["points"] = m[1:]
            r["marks"] = [m[0]]
    byq = {}
    for r in rows:
        byq.setdefault(r["q"], []).append(r)
    for q, rs in byq.items():
        last = rs[-1]
        big = len(rs) >= 3 and last["marks"] and last["marks"][-1] >= 5 and len(last["marks"]) >= 2
        if (last.get("total_col") or big) and (len(last["marks"]) >= 2 or (len(rs) > 1 and last["marks"])):
            others = sum(sum(r["marks"]) for r in rs) - last["marks"][-1]
            if last["marks"][-1] == others and others > 0:
                last["marks"] = last["marks"][:-1]
                last["dropped_total"] = others
                # trim the printed question total off the bottom of the crop
                pno, rect = last["segs"][-1]
                tw = [w for w in _dedupe(doc[pno].get_text("words"))
                      if re.fullmatch(rf"\[?{others}\]?", w[4]) and rect.y0 < w[1] < rect.y1
                      and w[0] > rect.x0 + (rect.width * 0.6)]
                if tw:
                    y = max(w[1] for w in tw)
                    if y - rect.y0 > 12:
                        last["segs"][-1] = (pno, pymupdf.Rect(rect.x0, rect.y0, rect.x1, y - 3))
                    elif len(last["segs"]) > 1:
                        # the printed total is all that continues onto the next page (audit A-015)
                        last["segs"].pop()
    # a row continued on the next page under the same label with the same mark
    # printed again: the mark counts once (seen in 9608 2018 mark schemes)
    for a, b in zip(rows, rows[1:]):
        if a["label"] == b["label"] and b["segs"][0][0] > a["segs"][0][0] and a["marks"] and b["marks"] == a["marks"]:
            b["repeated_marks"] = b["marks"]
            b["marks"] = []
    for r in rows:
        r["mark_total"] = sum(r["marks"])
    return rows


RE_TL = re.compile(r"^\(([a-z])\)$")
RE_TR = re.compile(r"^\((i|ii|iii|iv|v|vi|vii|viii|ix|x)\)$")


def ms_rows_text(doc, qs):
    """Rows of a mark scheme that is printed as running text, not as a table
    (9608, 2015-2016): '2 (a) (i) Any one from: ... [1]'.

    A row starts at a part label printed at the start of a line and runs to
    the next label. Labels are accepted only in the order of the question
    paper's own parts (qs). Marks are the [n] printed at the right-hand margin;
    where a row prints 'max n', that is the row's mark."""
    order = {}
    for q in qs:
        seq = [(p["letter"], p["roman"]) for p in q["parts"]]
        order[q["n"]] = seq
    rows = []
    cur = None
    cq, cl, cr = 0, None, None
    for pno in range(1, doc.page_count):
        page = doc[pno]
        words = _dedupe(page.get_text("words"))
        if not words:
            continue
        H = page.rect.height
        foot = [w[1] for w in words if w[1] > H - 80 and (w[4].startswith("©") or w[4] == "UCLES")]
        bottom = (min(foot) - 3) if foot else H - 45
        head = [w[3] for w in words if w[1] < 70 and w[4] in ("Page", "Mark", "Syllabus", "Paper", "Scheme",
                                                               "Cambridge", "International")]
        top = (max(head) + 3) if head else 60
        ws = sorted([w for w in words if top <= w[1] and w[3] <= bottom + 2], key=lambda w: (round(w[3]), w[0]))
        lines = []
        for w in ws:
            if lines and abs(lines[-1][0][3] - w[3]) < 2.5:
                lines[-1].append(w)
            else:
                lines.append([w])
        if cur is not None:
            cur["segs"].append((pno, pymupdf.Rect(40, top - 1, page.rect.width - 38, bottom)))
        for ln in lines:
            ln.sort(key=lambda w: w[0])
            y0 = min(w[1] for w in ln)
            i, started = 0, False
            q, l, r = cq, cl, cr
            if i < len(ln) and re.fullmatch(r"[1-9]\d?", ln[i][4]) and ln[i][0] < 66 and int(ln[i][4]) == cq + 1 \
                    and (cq + 1) in order:
                q, l, r = cq + 1, None, None
                started = True
                i += 1
            seq = order.get(q, [])
            letters = [a for a, b in seq if b is None]
            if i < len(ln) and RE_TL.match(ln[i][4]) and ln[i][0] < (110 if i == 0 else 140):
                L = RE_TL.match(ln[i][4]).group(1)
                after = letters.index(L) > letters.index(l) if (L in letters and l in letters) else L in letters
                if after and not (RE_TR.match(ln[i][4]) and (l, L) in seq and r is not None
                                  and ROMANS.index(L) == ROMANS.index(r) + 1 if L in ROMANS and r in ROMANS else False):
                    l, r = L, None
                    started = True
                    i += 1
            if i < len(ln) and RE_TR.match(ln[i][4]) and ln[i][0] < (135 if i == 0 else 175):
                R = RE_TR.match(ln[i][4]).group(1)
                if (l, R) in seq and (r is None or ROMANS.index(R) > ROMANS.index(r)):
                    r = R
                    started = True
                    i += 1
            if started:
                cq, cl, cr = q, l, r
                if cur is not None:      # close the previous row just above this line
                    pg, rc = cur["segs"][-1]
                    if pg == pno:
                        if y0 - 2 - rc.y0 > 3:
                            cur["segs"][-1] = (pg, pymupdf.Rect(rc.x0, rc.y0, rc.x1, y0 - 2))
                        else:
                            cur["segs"].pop()
                part = (f"({l})" if l else "") + (f"({r})" if r else "")
                cur = {"label": f"{q}{part}", "q": q, "part": part, "marks": [], "na": False, "guidance": False,
                       "total_col": False, "text_layout": True,
                       "segs": [(pno, pymupdf.Rect(40, y0 - 2, page.rect.width - 38, bottom))], "_m": []}
                rows.append(cur)
            if cur is not None:
                for k, w in enumerate(ln):
                    m = re.fullmatch(r"\[(\d{1,2})\]", w[4])
                    prev = ln[k - 1][4].lower().strip("([:") if k else ""
                    if m and w[0] > 495:
                        cur["_m"].append((int(m.group(1)), prev.strip(".") == "max"))
                    m2 = re.fullmatch(r"(\d{1,2})\]", w[4])
                    if m2 and k and ln[k - 1][4].lower().strip("[(.:") == "max" and w[2] > 500:
                        cur["_m"].append((int(m2.group(1)), True))
    for r in rows:
        mx = [v for v, is_max in r["_m"] if is_max]
        if len(mx) > 1 and len(set(mx)) == 1:
            mx = mx[:1]          # the same 'max n' under alternative solutions: one mark
        r["marks"] = mx if mx else [v for v, _ in r["_m"]]
        del r["_m"]
        r["segs"] = [(p, rc) for p, rc in r["segs"] if rc.height > 3]
        r["mark_total"] = sum(r["marks"])
    return [r for r in rows if r["segs"]]


APX_NOTES = []      # appendix headings matched to a row with a different label
RE_APX = re.compile(r"^\s*(?:Q(?:uestion)?\s*)?(\d{1,2})?\s*((?:\(\s*[a-h]\s*\))?\s*(?:\(\s*(?:i|ii|iii|iv|v|vi)\s*\))?)"
                    r"\s*:\s*(Visual Basic|VB\.?\s?NET|VB|Pascal|Free Pascal|Python)\b.{0,25}$")
RE_APX_LABEL = re.compile(r"^\s*Q(?:uestion)?\s*(\d{1,2})\s*((?:\(\s*[a-h]\s*\))?\s*(?:\(\s*(?:i|ii|iii|iv|v|vi)\s*\))?)"
                          r"\s*:?\s*$")


def attach_appendix(doc, rows):
    """9608 Paper 2 mark schemes print the program-code solutions (Visual
    Basic, Pascal, Python) in an appendix after the table, under headings such
    as 'Q6 (a): Visual Basic'; the table row only says that the solutions
    'appear in the Appendix'. The appendix section of a part is added to that
    part's row, so the answer is whole. Returns (sections attached, rows that
    refer to the Appendix but got no section)."""
    need = []
    for r in rows:
        t = " ".join(doc[p].get_text("text", clip=rc) for p, rc in r["segs"])
        if re.search(r"appear in the\s+Appendix|in the\s+Appendix", t):
            need.append(r)
    if not need:
        return 0, []
    last_row_page = max(r["segs"][0][0] for r in rows)      # page where the last row starts
    heads = []      # (page, y0, q or None, part)
    limits = {}
    apx_start = None
    for pno in range(1, doc.page_count):
        page = doc[pno]
        words = _dedupe(page.get_text("words"))
        if not words:
            continue
        H = page.rect.height
        foot = [w[1] for w in words if w[1] > H - 75 and (w[4].startswith("©") or w[4] in ("Page", "UCLES"))]
        hd = [w[3] for w in words if w[1] < 58]
        limits[pno] = ((max(hd) + 3) if hd else 50, (min(foot) - 3) if foot else H - 45)
        ws = sorted(words, key=lambda w: (round(w[3]), w[0]))
        lines = []
        for w in ws:
            if lines and abs(lines[-1][0][3] - w[3]) < 2.5:
                lines[-1].append(w)
            else:
                lines.append([w])
        for ln in lines:
            ln.sort(key=lambda w: w[0])
            t = " ".join(w[4] for w in ln)
            if re.search(r"Program Code( Example)? Solutions|^\s*Appendix\b.*(code|solutions)|^\s*Appendix\s*$", t,
                         re.I) and apx_start is None and pno >= last_row_page:
                apx_start = (pno, min(w[1] for w in ln))
            m = RE_APX.match(t) or RE_APX_LABEL.match(t)
            if m and (m.group(1) or m.group(2).strip()) and ln[0][0] < 140:
                part = re.sub(r"\s+", "", m.group(2))
                heads.append((pno, min(w[1] for w in ln), int(m.group(1)) if m.group(1) else None, part))
    if apx_start is None and heads:
        after = [h for h in heads if h[0] >= last_row_page]
        apx_start = after[0][:2] if after else None
    heads = [h for h in heads if apx_start is not None and h[:2] >= apx_start]
    if apx_start is not None:
        # a running-text row must not run on into the appendix
        for r in rows:
            segs = []
            for pg, rc in r["segs"]:
                if pg > apx_start[0]:
                    continue
                if pg == apx_start[0] and rc.y1 > apx_start[1] - 3:
                    rc = pymupdf.Rect(rc.x0, rc.y0, rc.x1, apx_start[1] - 3)
                if rc.height > 3:
                    segs.append((pg, rc))
            r["segs"] = segs or r["segs"][:1]
    groups = []
    for h in heads:
        if groups and groups[-1][2:] == h[2:]:
            continue
        groups.append(h)
    attached, used = 0, set()
    for gi, (pno, y0, q, part) in enumerate(groups):
        cand = [r for r in need if id(r) not in used and r["part"] == part and (q is None or r["q"] == q)]
        if not cand and q is not None:
            # a slip in the appendix heading ("Q5(b)(i)" for 5(b)(ii)): the only row of that
            # question and letter that says its solutions are in the Appendix
            same_q = [r for r in need if id(r) not in used and r["q"] == q and r["part"][:3] == part[:3]]
            if len({r["label"] for r in same_q}) == 1:
                cand = same_q
                APX_NOTES.append(f"appendix heading Q{q}{part} read as {same_q[0]['label']}")
        if not cand and q is not None and not any(id(r) not in used and r["q"] == q for r in need):
            # the row does not mention the Appendix but its solutions are printed there
            cand = [r for r in rows if id(r) not in used and r["part"] == part and r["q"] == q][-1:]
        if not cand:
            continue
        row = cand[0]
        used.add(id(row))
        end = groups[gi + 1][:2] if gi + 1 < len(groups) else (max(limits), None)
        segs = []
        for pg in range(pno, end[0] + 1):
            if pg not in limits:
                continue
            top, bot = limits[pg]
            a = (y0 - 3) if pg == pno else top
            b = (end[1] - 3) if (pg == end[0] and end[1] is not None) else bot
            if b - a > 6:
                segs.append((pg, pymupdf.Rect(40, a, doc[pg].rect.width - 38, b)))
        if segs:
            row["segs"] = list(row["segs"]) + segs
            row["appendix_segs"] = len(segs)
            attached += 1
    return attached, [r["label"] for r in need if id(r) not in used]


def ms_rows_any(doc, qs):
    """Table mark schemes (2017 on) or running-text mark schemes (2015-2016)."""
    rows = ms_rows(doc)
    if not rows:
        rows = ms_rows_text(doc, qs)
    doc._apx = attach_appendix(doc, rows)
    return rows


def _marks_in(words, rect, mx0, mx1, bracket_only=False, pt_x=None):
    """Mark values in the marks column of a row: one value per text line
    (older PDFs carry hidden duplicates). With bracket_only (old 'Total'
    column layout) bare numbers are question totals and are ignored.
    Old layouts also print '[max N]' (the part is worth N, not the sum of its
    [1] points) and, in 2016 Oct/Nov, a part-total column right of the Marks
    header (pt_x) beside per-point entries such as '1+1' (audit A-008)."""
    inrow = [w for w in sorted(words, key=lambda w: (w[1], w[0]))
             if w[1] >= rect.y0 - 1.5 and w[3] <= rect.y1 + 1.5]
    # '[max' 'N]' -> N for the whole row
    for i, w in enumerate(inrow):
        if w[4] == "[max" and w[0] >= mx0 - 45 and w[0] <= mx1:
            nx = next((v for v in inrow[i + 1:] if abs(v[1] - w[1]) < 2 and v[0] > w[0]), None)
            m = re.fullmatch(r"(\d{1,2})\]", nx[4]) if nx else None
            if m:
                later = [int(v[4][1:-1]) for v in inrow if mx0 - 1 <= v[0] <= mx1 and v[1] > w[1] + 2
                         and re.fullmatch(r"\[\d{1,2}\]", v[4])]
                return [int(m.group(1))] + later
    if pt_x is not None:
        tot = [w for w in inrow if w[0] > pt_x and w[0] <= mx1 and re.fullmatch(r"\d{1,2}", w[4])]
        if tot:
            return [int(w[4]) for w in tot]
    out, lines = [], set()
    for w in inrow:
        if w[0] >= mx0 - 1 and w[0] <= mx1:
            if not bracket_only and re.fullmatch(r"\d(?:\+\d)+", w[4]) and round(w[1]) not in lines:
                lines.add(round(w[1]))
                out.append(sum(int(x) for x in w[4].split("+")))
                continue
            m = re.fullmatch(r"\[(\d{1,2})\]" if bracket_only else r"\[?(\d{1,2})\]?", w[4])
            if m and round(w[1]) not in lines:
                lines.add(round(w[1]))
                out.append(int(m.group(1)))
    return out


def _dedupe(words):
    """Some older PDFs draw each word 2-3 times (faux bold) or split words into
    overlapping fragments ('Que'+'estion', '3('+'(b)(i)'). Keep one copy and
    re-join touching fragments, dropping the duplicated overlap characters."""
    seen, uniq = set(), []
    for w in words:
        k = (round(w[0]), round(w[1]), w[4])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(list(w[:5]))
    srt = sorted(uniq, key=lambda w: (round(w[1]), w[0]))
    fragmented = sum(1 for a, b in zip(srt, srt[1:])
                     if abs(a[1] - b[1]) < 1.5 and a[2] - b[0] > 1 and b[0] > a[0]) >= 3
    if not fragmented:
        return [tuple(w) for w in uniq]
    uniq = srt
    out = []
    for w in uniq:
        if out and abs(out[-1][1] - w[1]) < 1.5 and w[0] <= out[-1][2] + 0.6:
            prev = out[-1]
            ov = prev[2] - w[0]
            txt = w[4]
            if ov > 1 and txt:
                cw = (w[2] - w[0]) / len(txt)
                n = int(round(ov / cw)) if cw > 0 else 0
                txt = txt[n:]
            prev[4] += txt
            prev[2] = max(prev[2], w[2])
            prev[3] = max(prev[3], w[3])
            continue
        out.append(w)
    return [tuple(w) for w in out]


def fix_ms_rows(rows, qs):
    """Relabel an MS row whose label matches no part of the QP question when it is
    unambiguous (audit A-009, decision D6): exactly one unmatched MS row and exactly
    one QP part without MS rows, with equal marks. Returns [(q, old, new)]."""
    fixed = []
    for q in qs:
        qp = {}
        for m in q["marks"]:
            qp[m["label"]] = qp.get(m["label"], 0) + m["value"]
        rq = [r for r in rows if r["q"] == q["n"]]
        def known(p):
            if p == "":
                return "" in qp or True      # a row labelled with the question number alone
            return any(p == l or l.startswith(p) or p.startswith(l) for l in qp if l)
        bad = [r for r in rq if not known(r["part"])]
        missing = [l for l in qp if not any(r["part"] == l or l.startswith(r["part"]) and r["part"]
                                            or r["part"].startswith(l) for r in rq if known(r["part"]))]
        if len(bad) == 1 and len(missing) == 1 and bad[0]["mark_total"] == qp[missing[0]]:
            r = bad[0]
            old = r["label"]
            r["part"] = missing[0]
            r["label"] = f"{q['n']}{missing[0]}"
            r["relabelled_from"] = old
            fixed.append((q["n"], old, r["label"]))
    return fixed

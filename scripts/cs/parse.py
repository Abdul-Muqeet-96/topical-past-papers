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


def page_lines(page, top=46, bottom=798.5, left=25, right=572):
    """Text lines (list of word tuples) inside the content area, sorted by y."""
    allw = page.get_text("words")
    foot = [w[1] for w in allw if w[1] > 740 and (w[4] == "©" or RE_FOOT.fullmatch(w[4]))]
    if foot:
        bottom = min(foot) - 0.5
    words = [w for w in allw
             if w[1] >= top and (w[3] <= bottom or (w[3] <= bottom + 1.5 and w[1] < bottom - 8))
             and w[0] >= left and w[2] <= right
             and (w[3] - w[1]) >= 6.5 and w[4] not in ("[Turn", "over")]
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


def special_page(page):
    """'blank' for a BLANK PAGE; 'appendix' for the built-in function list that
    older papers print inside the question paper (reference material, not a
    question)."""
    t = page.get_text()
    body = "\n".join(l for l in t.splitlines()
                     if l.strip() and "DO NOT WRITE" not in l and not re.search(r"©|UCLES|^\s*\*", l))
    if "BLANK PAGE" in t and len(body.strip()) < 900 and not re.search(r"\[\d+\]", body):
        return "blank"
    if page.number > 0 and re.search(r"^\s*Appendix\s*$", t, re.M) and \
            re.search(r"built-in functions|Built-in functions|pseudocode functions|STRING Functions|"
                      r"String and character functions|operators", t, re.I) and not re.search(r"\[\d+\]\s*$", body, re.M):
        return "appendix"
    return None


def data_cut(page):
    """Kept for the shared region code: CS papers have no data block."""
    return None


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
            y0 = min(w[1] for w in ws)
            if cut is not None and y0 >= cut - 2:
                break
            y1 = max(w[3] for w in ws)
            i = 0
            while i < len(ws):
                w = ws[i]
                txt, x0 = w[4], w[0]
                nxt_q = (cur_q["n"] + 1) if cur_q else 1
                if i == 0 and re.fullmatch(r"\d{1,2}", txt) and x0 < 64 and int(txt) == nxt_q:
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
                for w in ws:
                    mm = RE_MARK.search(w[4])
                    if mm and w[2] > 525 and w[0] > 495:      # right-aligned at the margin
                        lab = (f"({cur_l})" if cur_l else "") + (f"({cur_r})" if cur_r else "")
                        cur_q["marks"].append({"label": lab, "value": int(mm.group(1)),
                                               "pos": (pno, w[1], w[3])})
                    if mm and w[2] > 525 and w[0] > 495:
                        cur_q["last_mark"] = (pno, w[3])
                mt = RE_TOTAL.search(line)
                if mt:
                    if cur_q["total"] is None:
                        cur_q["total"] = int(mt.group(1))
                        cur_q["total_pos"] = (pno, y0, y1)
                    else:
                        cur_q["total_dup"] = True
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
    for r in rows:
        r["mark_total"] = sum(r["marks"])
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

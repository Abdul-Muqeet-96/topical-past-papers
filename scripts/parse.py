"""Parse 9701 Paper 2 question papers and mark schemes from the PDF text layer.

QP: question numbers, lettered parts (a), roman sub-parts (i), [marks],
[Total: n], with page/y positions so regions can be cropped later.
MS: table rows keyed by labels like 3(c)(ii), with their marks and the
row rectangles (one per page segment).
All pages are de-rotated first so coordinates match the displayed page.
"""
import re
import pymupdf

ROMANS = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"]
LETTERS = "abcdefghijklmnop"
SERIES = {"February/March": "MAR", "May/June": "M/J", "October/November": "O/N"}

RE_MARK = re.compile(r"(?:^|[.…_ ])\[(\d+)\]$")
RE_TOTAL = re.compile(r"\[Total:\s*(\d+)\]")
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
        if not st or (b"FormXob.pcm" not in st and b"gRLs" not in st):
            continue
        new, k = RE_WM.subn(b"", st)
        new, k2 = _drop_wm_blocks(new)
        if k or k2:
            d.update_stream(x, new)
            n += k + k2
    return n


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


def load(path):
    d = pymupdf.open(path)
    strip_watermark(d)
    for p in d:
        if p.rotation:
            p.remove_rotation()
    return d


def paper_ref(doc):
    """Reference from the paper's own page-1 header, e.g. 'M/J 25/P22'."""
    t = re.sub(r"\s+", " ", doc[0].get_text())
    m = re.search(r"9701/(2\d)", t)
    s = re.search(r"(February/March|May/June|October/November) (20\d\d)", t)
    if not (m and s):
        return None
    return f"{SERIES[s.group(1)]} {s.group(2)[2:]}/P{m.group(1)}"


def page_lines(page, top=46, bottom=798.5, left=25, right=572):
    """Text lines (list of word tuples) inside the content area, sorted by y."""
    allw = page.get_text("words")
    foot = [w[1] for w in allw if w[1] > 740 and (w[4] == "©" or re.fullmatch(r"9701/\d\d/\S+", w[4]))]
    if foot:
        bottom = min(foot) - 0.5
    words = [w for w in allw
             if w[1] >= top and w[3] <= bottom and w[0] >= left and w[2] <= right
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
    t = page.get_text()
    if "BLANK PAGE" in t and len(t.strip()) < 400:
        return "blank"
    if "Periodic Table of Elements" in t:
        return "periodic"
    return None


def data_cut(page):
    """y of the 'Important values, constants and standards' heading, if any.
    Content below it is the data block, not question material."""
    if page.number == 0:
        return None
    hits = page.search_for("Important values, constants and standards")
    return min(r.y0 for r in hits) if hits else None


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
                    if mm and w[2] > 470:
                        lab = (f"({cur_l})" if cur_l else "") + (f"({cur_r})" if cur_r else "")
                        cur_q["marks"].append({"label": lab, "value": int(mm.group(1)),
                                               "pos": (pno, w[1], w[3])})
                mt = RE_TOTAL.search(line)
                if mt:
                    if cur_q["total"] is None:
                        cur_q["total"] = int(mt.group(1))
                        cur_q["total_pos"] = (pno, y0, y1)
                    else:
                        cur_q["total_dup"] = True
    return qs


def ms_rows(doc):
    """Rows of the mark-scheme table: [{label, q, part, marks, segs:[(pno, rect)]}].
    A page may hold several tables (each with its own header row); a row may
    continue onto the next page (content above the first label there)."""
    rows = []
    open_row = None
    for pno in range(doc.page_count):
        page = doc[pno]
        words = page.get_text("words")
        drs = page.get_drawings()
        heads = []
        for h in sorted((w for w in words if w[4] == "Question" and w[0] < 140), key=lambda w: w[1]):
            mk = [w for w in words if w[4] == "Marks" and w[0] > 300 and abs(w[1] - h[1]) < 3]
            if mk:
                heads.append((h, mk[0]))
        if not heads:
            continue
        foot = [w for w in words if w[4] == "Page" and w[1] > page.rect.height - 70]
        bottom = (min(w[1] for w in foot) - 4) if foot else page.rect.height - 50
        for hi, (h, mk) in enumerate(heads):
            hy = h[3]
            reg_end = heads[hi + 1][0][1] - 6 if hi + 1 < len(heads) else bottom
            tx0 = h[0] - 8
            mx0, mx1 = mk[0] - 12, mk[2] + 12
            gd = any(w[4] == "Guidance" and abs(w[1] - h[1]) < 3 for w in words)
            vr = [d["rect"] for d in drs if d["rect"].width < 2 and d["rect"].height > 4
                  and d["rect"].y1 > hy and d["rect"].y0 < reg_end]
            qcol_x1 = min([r.x0 for r in vr if r.x0 > h[0] + 5] or [h[2] + 20])
            table_x1 = max([r.x1 for r in vr] or [page.rect.width - 60])
            tab_bottom = max([r.y1 for r in vr if r.y1 <= reg_end + 1] or [reg_end])
            # full-width row rules only (rules of tables nested in a cell start further right)
            hr = sorted({round(d["rect"].y0, 1) for d in drs
                         if d["rect"].height < 2 and d["rect"].width > 30 and d["rect"].x0 < tx0 + 12
                         and hy < d["rect"].y0 < reg_end})
            labels = sorted([w for w in words if hy < w[1] < tab_bottom and w[2] <= qcol_x1 + 4
                             and RE_MS_LABEL.match(w[4])], key=lambda w: w[1])
            row_starts = []
            for w in labels:
                above = [y for y in hr if y <= w[1] + 1]
                row_starts.append((max(above) if above else hy + 2, w))
            first_top = row_starts[0][0] if row_starts else tab_bottom
            start_hdr = min(hr or [hy + 4])
            if hi == 0 and open_row is not None and first_top - start_hdr > 8:
                seg = pymupdf.Rect(tx0, start_hdr - 0.5, table_x1 + 1, first_top + 0.5)
                open_row["segs"].append((pno, seg))
                open_row["marks"] += _marks_in(words, seg, mx0, mx1)
            for k, (top, w) in enumerate(row_starts):
                end = row_starts[k + 1][0] if k + 1 < len(row_starts) else tab_bottom
                seg = pymupdf.Rect(tx0, top - 0.5, table_x1 + 1, end + 0.5)
                m = RE_MS_LABEL.match(w[4])
                row = {"label": w[4], "q": int(m.group(1)), "part": m.group(2) + m.group(3),
                       "segs": [(pno, seg)], "marks": _marks_in(words, seg, mx0, mx1),
                       "na": any(w2[4] == "N/A" for w2 in words if w2[0] >= mx0 and w2[2] <= mx1
                                 and seg.y0 - 1 <= w2[1] <= seg.y1),
                       "guidance": gd}
                rows.append(row)
                open_row = row
    for r in rows:
        r["mark_total"] = sum(r["marks"])
    return rows


def _marks_in(words, rect, mx0, mx1):
    out = []
    for w in words:
        if w[0] >= mx0 and w[2] <= mx1 and w[1] >= rect.y0 - 1.5 and w[3] <= rect.y1 + 1.5:
            if re.fullmatch(r"\d{1,2}", w[4]):
                out.append(int(w[4]))
    return out

"""Check 7 SELF-CONTAINMENT, from the books. For every item, what is actually shown (the placed bands,
mapped to source positions) is compared with what its own parts ask for:
 a. every own part is fully shown (its marks lie inside the bands);
 b. part references ("part (a)", "(b)(ii)", "your answer to ...") point to parts that are shown;
 c. page references ("on page 12") point to source pages that are shown;
 d. references to the insert / the Appendix: the item carries the note or the pages inline;
 e. references to another question are listed for reading;
 f. identifier rule: an identifier (monospace name) used in an own part and first printed
    elsewhere in the question must have its first occurrence inside the shown bands."""
import csv, re, sys
from collections import Counter, defaultdict
import pymupdf as f
from c00_common import *

QP = jl("qp_parse.json")
RO = "|".join(sorted(ROM, key=len, reverse=True))
KEYW = set("""DECLARE CONSTANT INTEGER REAL STRING CHAR BOOLEAN DATE ARRAY OF TYPE ENDTYPE IF THEN ELSE ENDIF CASE ENDCASE OTHERWISE
FOR TO STEP NEXT ENDFOR WHILE DO ENDWHILE REPEAT UNTIL PROCEDURE ENDPROCEDURE FUNCTION ENDFUNCTION RETURNS RETURN CALL BYREF BYVAL
INPUT OUTPUT OPENFILE READFILE WRITEFILE CLOSEFILE READ WRITE APPEND EOF TRUE FALSE AND OR NOT MOD DIV LENGTH LEFT RIGHT MID LCASE
UCASE INT RAND NUM_TO_STR STR_TO_NUM IS_NUM ASC CHR TO_UPPER TO_LOWER DAY MONTH YEAR DAYINDEX SETDATE TODAY NOW SELECT FROM WHERE
ORDER BY GROUP INNER JOIN ON INSERT INTO VALUES UPDATE SET DELETE CREATE TABLE DATABASE ALTER ADD PRIMARY KEY FOREIGN REFERENCES
VARCHAR COUNT SUM AVG ENDSELECT NULL LDM LDD LDI LDX LDR MOV STO ADD SUB INC DEC JMP CMP CMI JPE JPN IN OUT END LSL LSR XOR
ReDim Dim As Integer String Boolean Double Single Char End Sub Function Console WriteLine ReadLine Module Public Private Then Next
print input def return while for if elif else in range len int str float True False None import var begin end program procedure
function writeln readln integer string boolean real char array of then do until repeat const type record""".split())
cache = {}


def spage(fn, i):
    if fn not in cache:
        cache[fn] = f.open(os.path.join(DATA, fn))
    return cache[fn][i]


tc = {}


def tokens(fn, i):
    """Words of a source page in reading order: (y, x0, x1, text, mono)."""
    if (fn, i) not in tc:
        p = spage(fn, i)
        out = []
        for b in p.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                if abs(l["dir"][0] - 1) > 0.01:
                    continue
                for s in l["spans"]:
                    if s["size"] < 5.6 or not s["text"].strip():
                        continue
                    mono = bool(re.search(r"Courier|Mono|Consol", s["font"], re.I))
                    x0, y0, x1, y1 = s["bbox"]
                    n = max(1, len(s["text"]))
                    for m in re.finditer(r"\S+", s["text"]):
                        out.append(((y0 + y1) / 2, x0 + (x1 - x0) * m.start() / n, x0 + (x1 - x0) * m.end() / n, m.group(), mono))
        out.sort(key=lambda t: (round(t[0] / 4), t[1]))
        tc[(fn, i)] = out
    return tc[(fn, i)]


apx_cache = {}


def appendix_pages(fn):
    """Pages of a question paper whose first body line reads 'Appendix' (9608 Paper 2)."""
    if fn not in apx_cache:
        D = f.open(os.path.join(DATA, fn))
        out = []
        for p in D:
            body = [" ".join(w[4] for w in l["w"]) for l in lines(p) if 46 < l["c"] < p.rect.height - 46]
            body = [t for t in body if not re.fullmatch(r"\d+", t.strip())]
            if body and re.fullmatch(r"(Appendix|APPENDIX)", body[0].strip()):
                out.append(p.number)
            elif out and out[-1] == p.number - 1 and body and not any(re.search(r"\[\d+\]$", x) for x in body) \
                    and not body[0].startswith(("BLANK PAGE", "Permission to reproduce")):
                out.append(p.number)
        apx_cache[fn] = out
    return apx_cache[fn]


res = {k: [] for k in ("own_not_shown", "part_ref", "page_ref", "insert_ref", "appendix_ref", "question_ref", "announced", "dangling", "identifier")}
stats = Counter()
ctx_seen = {}
for book in (1, 2):
    bands = jl(f"bands_p{book}.json")["bands"]
    bp = jl(f"book_parse_p{book}.json")
    idx = {r["reference"]: r for r in csv.DictReader(open(os.path.join(BOOKDIR[book], "index.csv")))}
    byitem = defaultdict(list)
    for b in bands:
        if b["side"] == "Q" and b["src"]:
            byitem[b["ref"]].append(b)
    notes = {i["ref"]: i["notes"] for i in bp["items"] if i["side"] == "Q"}
    for ref, bs in byitem.items():
        pid_, q, suf = ref_key(ref)
        code, sy, v = pid_.split("_")
        qfn = f"{code}_{sy}_qp_{v}.pdf"
        P = QP[pid_]
        k = bs[0].get("k", 1.0)
        shown = defaultdict(list)       # source page index -> [(y0, y1)]
        ins_pages = set()
        for b in bs:
            if b["src"][0] == qfn:
                shown[b["src"][1]].append((b["vclip"][1], b["vclip"][3]))
            else:
                ins_pages.add((b["src"][0], b["src"][1]))

        def is_shown(pg, y, tol=3.0):
            return any(a - tol <= y <= c + tol for a, c in shown.get(pg, []))
        leaves = list(P["parts"][str(q)])
        marks = dict(P["pos"])
        for qq, x in P["inner"].items():
            for key, val, pg, y, x1 in x:
                marks.setdefault(key, []).append([pg, y])
                if qq == str(q) and key not in leaves:
                    leaves.append(key)
        own = expand(q, suf, leaves)
        stats["items"] += 1
        base = {"book": book, "ref": ref}
        # a. own parts shown
        for l in own:
            for pg, y in marks.get(l, []):
                if not is_shown(pg - 1, y):
                    res["own_not_shown"].append(dict(base, leaf=l, page=pg, y=y))
        shown_leaves = [l for l in leaves if marks.get(l) and all(is_shown(pg - 1, y) for pg, y in marks[l])]
        ctx_seen[ref] = sorted(set(shown_leaves) - set(own))
        # regions of the question: ordered marks
        order = sorted(((pg, y, l) for l in leaves for pg, y in marks.get(l, [])))
        qstart = tuple(P["qpos"][str(q)])
        nq = P["qpos"].get(str(q + 1))
        qend = tuple(nq) if nq else (P["pages"] + 1, 0)
        regions = {}
        prev = (qstart[0], qstart[1] - 6)
        last_of = {}
        for pg, y, l in order:
            last_of[l] = (pg, y)
        for l in sorted(last_of, key=lambda l: last_of[l]):
            regions[l] = (prev, (last_of[l][0], last_of[l][1] + 4))
            prev = regions[l][1]

        def words_between(a, b):
            out = []
            for pg in range(a[0], min(b[0], P["pages"]) + 1):
                for t in tokens(qfn, pg - 1):
                    if (pg > a[0] or t[0] > a[1]) and (pg < b[0] or t[0] <= b[1]) and 44 < t[0] < spage(qfn, pg - 1).rect.height - 44:
                        out.append((pg,) + t)
            return out
        allw = words_between((qstart[0], qstart[1] - 6), qend)
        own_w = []
        for l in own:
            if l in regions:
                own_w += [(l,) + w for w in words_between(*regions[l])]
        text = " ".join(w[5] for w in own_w)
        # b. part references
        cur_letter = lambda l: re.match(r"\d+\(([a-z])\)", l).group(1) if re.match(r"\d+\(([a-z])\)", l) else None
        for i, w in enumerate(own_w):
            l, pg, y, x0, x1, t, mono = w
            m = re.fullmatch(r"\(([a-h])\)(?:\((%s)\))?[.,;:]?" % RO, t)
            m2 = re.fullmatch(r"\((%s)\)[.,;:]?" % RO, t)
            prevt = own_w[i - 1][5].lower().strip("(") if i else ""
            same_line = i and abs(own_w[i - 1][2] - y) < 4 and own_w[i - 1][1] == pg
            if not ((m or m2) and same_line and prevt in ("part", "parts", "and", "in", "from", "to", "for", "of", "question", "or", "see")):
                continue
            if m and not m.group(2) and m.group(1) == cur_letter(l):
                continue            # "described in part (b)" inside (b): its own lettered part, always shown
            if m and not (m.group(1) == "i" and m2 and cur_letter(l)):
                tgt = [x for x in leaves if x == f"{q}({m.group(1)})" + (f"({m.group(2)})" if m.group(2) else "")
                       or (not m.group(2) and x.startswith(f"{q}({m.group(1)})("))]
            else:
                cl = cur_letter(l)
                tgt = [x for x in leaves if x == (f"{q}({cl})({m2.group(1)})" if cl else f"{q}({m2.group(1)})")]
            # 'and (b)' etc. only count after a part reference on the same line
            if prevt in ("and", "or") and not any(own_w[j][5].lower() in ("part", "parts") for j in range(max(0, i - 5), i)):
                continue
            stats["part references"] += 1
            if not tgt:
                res["part_ref"].append(dict(base, leaf=l, token=t, why="no such part in the question", line=" ".join(x[5] for x in own_w[max(0, i - 6):i + 3])))
            else:
                miss = [x for x in tgt if x not in shown_leaves and x not in own]
                if miss:
                    res["part_ref"].append(dict(base, leaf=l, token=t, why=f"refers to {miss} which is not shown",
                                                line=" ".join(x[5] for x in own_w[max(0, i - 6):i + 3])))
        # c. page references
        for m in re.finditer(r"\bpages? (\d+)(?:\s*(?:–|-|and|to)\s*(\d+))?", text):
            for n in range(int(m.group(1)), int(m.group(2) or m.group(1)) + 1):
                stats["page references"] += 1
                if not shown.get(n - 1):
                    res["page_ref"].append(dict(base, page=n, text=text[max(0, m.start() - 60):m.end() + 20]))
        # d. insert / Appendix
        mi = re.search(r"\b([Tt]he|[Tt]his|[Yy]our) insert\b", text)
        if mi:
            stats["insert references"] += 1
            if not (any(n.startswith("Uses the insert") for n in notes.get(ref, [])) or any("_in_" in a for a, _ in ins_pages)):
                res["insert_ref"].append(dict(base, text=text[max(0, mi.start() - 60):][:120]))
        if re.search(r"\bAppendix\b", text):
            stats["Appendix references"] += 1
            ap = appendix_pages(qfn)
            if not ap or not all(shown.get(a) for a in ap):
                if not (any("_in_" in a for a, _ in ins_pages) or any(n.startswith("Uses the insert") for n in notes.get(ref, []))):
                    res["appendix_ref"].append(dict(base, appendix_pages=[a + 1 for a in ap], shown=sorted(a + 1 for a in shown)))
        # e. other questions
        for m in re.finditer(r"\b[Qq]uestion (\d+)", text):
            if int(m.group(1)) != q:
                res["question_ref"].append(dict(base, text=text[max(0, m.start() - 70):m.end() + 40]))
        # e2. material announced as following ("Incomplete pseudocode follows ..."): the next printed
        # lines of the question paper must be shown too
        qlines = []
        for w in sorted(allw, key=lambda w: (w[0], round(w[1] / 3), w[2])):
            if qlines and qlines[-1][0] == w[0] and abs(qlines[-1][1] - w[1]) < 4:
                qlines[-1][2].append(w[4])
            else:
                qlines.append([w[0], w[1], [w[4]]])
        qlines = [x for x in qlines if re.search(r"[A-Za-z0-9]", " ".join(x[2]))
                  and not (x[1] < 62 and re.fullmatch(r"\d{1,2}", " ".join(x[2]).strip()))        # page number
                  and not (x[1] > 780 and re.search(r"UCLES|Turn over|\d{4}/\d\d/", " ".join(x[2])))]
        for k, (pg, y, ws_) in enumerate(qlines):
            if re.search(r"\b(pseudocode|program code|algorithm|flowchart)\b[^.:]{0,20}\bfollows\b", " ".join(ws_)) and is_shown(pg - 1, y):
                stats["announcements ('... follows')"] += 1
                nxt = qlines[k + 1:k + 4]
                miss = [(a, round(b), " ".join(c)[:40]) for a, b, c in nxt if not is_shown(a - 1, b)]
                if miss:
                    res["announced"].append(dict(base, line=" ".join(ws_)[:90], not_shown=miss))
        # e3. a shown line that announces what follows ("The following diagram shows ...", "... as
        # follows:") while the lines printed next in the paper (within 70 pt, or the top of the next
        # page) are not shown
        for k, (pg, y, ws_) in enumerate(qlines):
            t_ = " ".join(ws_)
            if not is_shown(pg - 1, y) or k + 1 >= len(qlines):
                continue
            if not (t_.rstrip().endswith(":") or re.search(r"\b[Tt]he following (diagram|table|pseudocode|program|code|algorithm|flowchart|structure chart)\b[^.]*\.?$", t_)):
                continue
            npg, ny, nws = qlines[k + 1]
            if (npg == pg and ny - y > 70) or npg > pg + 1:
                continue                     # answer space follows: nothing was announced
            if t_.rstrip().endswith(":") and re.match(r"\(?([a-h]|[ivx]{1,4})\)", nws[0]):
                continue                     # "... of the following devices:" - the parts are the list
            stats["announcing lines (colon / 'the following ...')"] += 1
            if not is_shown(npg - 1, ny):
                res["dangling"].append(dict(base, line=t_[-90:], next=" ".join(nws)[:60], at=[pg, round(y)]))
        # f. identifiers
        first = {}
        for w in allw:
            pg, y, x0, x1, t, mono = w
            for tok in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", t):
                first.setdefault(tok, (pg, y, t))
        seen = set()
        for w in own_w:
            l, pg, y, x0, x1, t, mono = w
            if not mono:
                continue
            for tok in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", t):
                if tok in KEYW or tok.upper() in KEYW and tok.isupper() or tok in seen:
                    continue
                if not (re.search(r"[a-z]", tok) and re.search(r"[A-Z]", tok) or "_" in tok):
                    continue
                seen.add(tok)
                stats["identifiers checked"] += 1
                fp, fy, ft = first[tok]
                if not is_shown(fp - 1, fy):
                    # where it was first printed
                    where = next((x for a, b_, x in order if (a, b_) >= (fp, fy - 4)), "?")
                    res["identifier"].append(dict(base, leaf=l, ident=tok, first_page=fp, first_y=round(fy), first_in=where,
                                                  shown_ctx=ctx_seen[ref]))
for k, v in res.items():
    jd(v, f"self_{k}.json", 0)
jd(ctx_seen, "self_context_shown.json")
print(dict(stats))
for k, v in res.items():
    print(f"{k}: {len(v)} rows in {len({(x['book'], x['ref']) for x in v})} items")

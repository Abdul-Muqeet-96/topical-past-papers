"""Stage 3 (structure): for every included question, find the regions of the
stem, lettered parts and roman sub-parts; their text; cross-references (parts,
identifiers, single-letter labels, scenario nouns); and the matching
mark-scheme rows. Writes λ-cs/work/parts_<phase>.json. Prints counts only.

Regions are lists of [page, y0, y1] on the de-rotated question paper.

CS papers do not number their figures or tables, so there are no caption
blocks: a figure, table or block of code belongs to the part it is printed in,
and another part that needs it gets that whole part as context.
"""
import json, os, re, sys
import pymupdf
from collections import defaultdict
sys.path.insert(0, os.path.dirname(__file__))
from parse import (load, parse_qp, ms_rows_any, fix_ms_rows, page_lines, special_page, data_cut, ROMANS, RE_FOOT,
                   answer_dot_rects,
                   doc_key, boiler_top)
from paths import DATA, MANIFEST, work, jload, jdump

TOP = 52
RE_DOTS = re.compile(r"^[.…·_ ]{6,}$")
RM = r"(?:i|ii|iii|iv|v|vi|vii|viii|ix|x)"
# "(a)", "(b)(ii)", "part (a)"; a bare roman "(ii)" = sibling of the same lettered part
RE_PREF = re.compile(rf"(?<![\w)])\(([a-h])\)(?:\s*\(({RM})\))?|(?<![\w)])\(({RM})\)(?!\()")
# "1(a)", "3(b)(ii)": question number + part
RE_QPREF = re.compile(rf"(?<![\w.(])(\d{{1,2}})\s?\(([a-h])\)(?:\s*\(({RM})\))?")
RE_QREF = re.compile(r"\b[Qq]uestions?\s+(\d{1,2})\b")
RE_NAVLINE = re.compile(r"(continues|continued|begins|starts) on (the next )?page|^\s*(Please )?[Tt]urn over\s*$|"
                        r"^\s*BLANK PAGE\s*$", re.I)
RE_BOILER = re.compile(r"Permission to reproduce|To avoid the issue of disclosure|Every reasonable effort|"
                       r"Cambridge Assessment International Education is part|is a department of the University|"
                       r"Cambridge International Examinations is part|copyright holders", re.I)
RE_LAB = re.compile(r"(?<![A-Za-z0-9(\[–\-+=/'\"‘“&#])([A-Z])(?![A-Za-z0-9a-z+\-–=(\['\"’”])")

# words that are never identifiers (pseudocode / SQL / assembly keywords, data
# types, built-in functions and operators, literals)
STOP = set("""
DECLARE CONSTANT IF THEN ELSE ELSEIF ENDIF CASE OF OTHERWISE ENDCASE FOR TO STEP NEXT WHILE DO ENDWHILE REPEAT UNTIL
PROCEDURE ENDPROCEDURE FUNCTION ENDFUNCTION RETURNS RETURN CALL INPUT OUTPUT OPENFILE READFILE WRITEFILE CLOSEFILE
READ WRITE APPEND RANDOM SEEK GETRECORD PUTRECORD BYREF BYVAL BYVALUE TYPE ENDTYPE ARRAY INTEGER REAL STRING CHAR
BOOLEAN DATE CURRENCY TRUE FALSE AND OR NOT NAND NOR XOR EOR MOD DIV EOF NULL DEFINE CLASS ENDCLASS NEW PUBLIC PRIVATE
INHERITS SUPER PRINT LEFT RIGHT MID LENGTH LCASE UCASE TO_UPPER TO_LOWER NUM_TO_STR STR_TO_NUM IS_NUM ASC CHR INT RAND
DAY MONTH YEAR DAYINDEX SETDATE TODAY NOW ROUND CONCAT ONECHAR CHARACTERCOUNT TONUM SUBSTR TOSTRING
SELECT FROM WHERE ORDER BY GROUP INNER JOIN ON INSERT INTO VALUES UPDATE SET DELETE CREATE TABLE DATABASE ALTER ADD
PRIMARY FOREIGN KEY REFERENCES VARCHAR CHARACTER TIME COUNT SUM AVG AS DESC DISTINCT LIKE BETWEEN IN IS MAX MIN HAVING
LDM LDD LDI LDX LDR MOV STO SUB INC DEC JMP CMP CMI JPE JPN OUT END LSL LSR ACC IX
ERROR TOS ASCII
""".split())
RE_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z]{2,4})?")
# identifiers recognisable in ordinary (non-monospace) text
RE_PROSE_ID = re.compile(r"\b[A-Za-z_]\w*(?=\(\))|\b[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]*)+\b|\b[A-Z]{2,}(?:_[A-Z0-9]+)+\b|"
                         r"\b[A-Za-z]\w*\.(?:txt|TXT|dat|DAT|csv|CSV)\b")
PROSE_NOT_ID = {"JavaScript", "PowerPoint", "WiFi", "IPv4", "IPv6", "MySQL", "YouTube", "PayPal", "McDonald",
                "eBay", "iPhone", "FireWire", "PostScript", "BitTorrent", "QuickTime", "OneDrive", "GitHub"}

# scenario nouns: "the program", "this table" ... refer to something introduced earlier
NOUNS = ("program|algorithm|pseudocode|code|function|procedure|module|subroutine|flowchart|chart|diagram|table|"
         "array|file|record|database|circuit|expression|network|statement|statements|instruction|instructions|"
         "structure|list|stack|queue|loop|design|identifier|variable|constant|image|sound|recording|message|"
         "text|data|system|company|school|college|shop|business|organisation|student|students|teacher|manager|"
         "customer|customers|programmer|developer|user|website|application|app|game|robot|sensor|sensors|device|"
         "computer|laptop|printer|processor|register|registers|truth table|trace table|logic circuit|"
         "state-transition diagram|structure chart|linked list|test|tests|error|errors|solution|query|script|"
         "tables|arrays|files|records|functions|procedures|modules|programs|values|value|number|numbers|"
         "character|characters|string|strings|bitmap|photograph|photographs|video|document|software|"
         "language|interpreter|compiler|assembler|library|operating system")
RE_ANA = re.compile(rf"(\b\w+\s+)?\b(?:the|this|these|that|those)\s+(?:(?:same|above|original|completed|"
                    rf"corrected|amended|modified|previous)\s+)?({NOUNS})\b(\s+\w+)?", re.I)
# "Complete the table", "Write the pseudocode ..." name the thing to produce, not something shown earlier
ANA_VERBS = {"complete", "write", "draw", "give", "state", "identify", "describe", "explain", "create", "produce",
             "define", "declare", "outline", "suggest", "construct", "show", "calculate", "name"}
# "the table below", "the pseudocode for ...", "the program that ..." point forward or are defined on the spot
ANA_AFTER = {"below", "shown", "for", "to", "that", "which", "of", "used", "statement", "statements", "expression",
             "expressions", "is", "are", "will", "contains", "contain", "given", "has", "have", "would", "should",
             "can", "could", "must", "needs", "need", "called", "named", "above", "in", "from", "on", "structure",
             "type", "types", "header", "headers", "name", "names", "life", "development", "code", "design",
             "file", "segment", "extract", "clause", "function", "module", "procedure", "algorithm"}


def noun_key(n):
    """Singular form: 'robots' and 'robot' are the same thing."""
    n = n.lower()
    if n.endswith("ies"):
        return n[:-3] + "y"
    if n.endswith("sses") or n.endswith("xes"):
        return n[:-2]
    return n[:-1] if n.endswith("s") and not n.endswith("ss") else n


# nouns so general that "the X" needs no antecedent
GENERIC = {noun_key(x) for x in {"pseudocode", "data", "user", "computer", "value", "values", "number", "numbers", "text", "code", "system", "software",
           "processor", "character", "characters", "string", "strings", "language", "operating system", "statement",
           "statements", "error", "errors", "solution", "test", "tests", "design", "identifier", "variable",
           "instruction", "instructions", "structure", "list", "loop", "interpreter", "compiler", "assembler",
           "register", "registers", "document", "table", "tables", "file", "files", "record", "records",
           "function", "functions", "procedure", "procedures", "module", "modules", "program", "programs",
           "array", "arrays", "image", "sound", "message", "device", "library", "constant"}}


def content_bottom(page):
    allw = page.get_text("words")
    foot = [w[1] for w in allw if w[1] > 740 and (w[4] == "©" or RE_FOOT.fullmatch(w[4]))]
    bt = boiler_top(page)
    if bt is not None:
        foot.append(bt - 1.5)       # the small-print copyright paragraph is not question material
    return (min(foot) - 0.5) if foot else 794


def span(doc, a, b):
    """Region from position a=(page,y) to b=(page,y) (exclusive), skipping special pages."""
    (p1, y1), (p2, y2) = a, b
    out = []
    for p in range(p1, p2 + 1):
        if special_page(doc[p]):
            continue
        top = y1 if p == p1 else TOP
        bot = y2 if p == p2 else content_bottom(doc[p]) + 2.0
        if bot - top > 2:
            out.append([p, round(top - 1.5, 1), round(bot - 1.5, 1)])
    return out


def region_lines(doc, region):
    out = []
    for p, y0, y1 in region:
        for ws in page_lines(doc[p], bottom=content_bottom(doc[p])):
            ly0 = min(w[1] for w in ws)
            if y0 - 0.5 <= ly0 < y1:
                out.append((p, ws))
    return out


def text_of(doc, region, strip_labels=True):
    """Text of a region from the paper's text layer. Answer-line dots are gone
    (redacted at load); gaps to fill inside code are kept as printed."""
    parts = []
    for p, ws in region_lines(doc, region):
        # a page that was put back unredacted still carries its answer-line dots: drop them here
        adots = answer_dot_rects(doc[p])
        if adots:
            kept = []
            for w in ws:
                if any(r.intersects(pymupdf.Rect(w[:4])) for r in adots):
                    t = re.sub(r"[.…]{5,}", "", w[4])
                    if not t:
                        continue
                    w = tuple(w[:4]) + (t,) + tuple(w[5:])
                kept.append(w)
            ws = kept
        words = [w[4] for w in ws]
        line = " ".join(words)
        if RE_NAVLINE.search(line) and len(words) <= 9:
            continue
        if strip_labels:
            while words and re.fullmatch(rf"\d{{1,2}}|\([a-z]\)|\({RM}\)", words[0]) and ws[0][0] < 125:
                words = words[1:]
                ws = ws[1:]
        if words:
            parts.append(" ".join(words))
    return " ".join(parts)


# ---------- identifiers ----------
_MONO = {}


def mono_lines(page):
    """Per visual line: (y0, y1, text of the monospace characters only). A
    character is monospace when its advance is 0.6 em (Courier); proportional
    fonts never give a whole word of such characters."""
    key = (doc_key(page.parent), page.number)
    if key in _MONO:
        return _MONO[key]
    rows = []
    for b in page.get_text("rawdict")["blocks"]:
        for l in b.get("lines", []):
            if abs(l["dir"][0] - 1) > 0.01:
                continue
            for s in l["spans"]:
                size = s["size"] or 1
                for c in s["chars"]:
                    w = (c["bbox"][2] - c["bbox"][0]) / size
                    rows.append((c["origin"][1], c["origin"][0], c["c"], abs(w - 0.6) < 0.006, c["bbox"][1], c["bbox"][3]))
    rows.sort(key=lambda r: (round(r[0]), r[1]))
    lines = []
    for r in rows:
        if lines and abs(lines[-1][-1][0] - r[0]) < 2.0:
            lines[-1].append(r)
        else:
            lines.append([r])
    out = []
    full = []
    nmono = []
    for ln in lines:
        ln.sort(key=lambda r: r[1])
        # a word counts as monospace only if every character of it is
        txt, word = [], []
        def flush():
            if word:
                ok = len(word) >= 2 and all(m for _, m in word)
                txt.append("".join(ch for ch, _ in word) if ok else " " * len(word))
                word.clear()
        prev_x = None
        for y, x, ch, m, by0, by1 in ln:
            if ch.isspace():
                flush()
                txt.append(" ")
            else:
                word.append((ch, m))
        flush()
        ink = [r for r in ln if not r[2].isspace()] or ln      # spaces can carry tall boxes
        out.append((min(r[4] for r in ink), max(r[5] for r in ink), "".join(txt)))
        full.append("".join(r[2] for r in ln))
        nmono.append(sum(1 for r in ln if r[3] and not r[2].isspace()))
    _MONO[key] = out
    _FULL[key] = full
    _NMONO[key] = nmono
    if len(_MONO) > 64:
        k0 = next(iter(_MONO))
        _MONO.pop(k0)
        _FULL.pop(k0, None)
        _NMONO.pop(k0, None)
    return out


_FULL = {}
_NMONO = {}


def line_mono_chars(page):
    """Per visual line (as line_texts): how many of its characters are monospace, single letters
    included ("n <- 0" has no monospace word of two letters, but is a line of code)."""
    mono_lines(page)
    return _NMONO[(doc_key(page.parent), page.number)]


def line_texts(page):
    """Per visual line: (y0, y1, monospace text, all the text of that line). The text is taken
    from the characters on the line's own baseline: the boxes of Courier lines overlap their
    neighbours, so a text box cut out by y would pick up parts of the lines above and below."""
    rows = mono_lines(page)
    full = _FULL[(doc_key(page.parent), page.number)]
    return [(a, b, m, t) for (a, b, m), t in zip(rows, full)]


def _clean_ident(tok):
    if "." in tok and not re.search(r"\.(txt|dat|csv)$", tok, re.I):
        tok = tok.split(".")[0]
    return tok


def idents_of(doc, region, text=None):
    """Identifiers used in a region: monospace words that are not keywords,
    plus names recognisable in ordinary text (Name(), CamelCase, TBL_ORDER,
    File.txt)."""
    out = set()
    for p, y0, y1 in region:
        for ly0, ly1, mono in mono_lines(doc[p]):
            if not (y0 - 0.5 <= ly0 < y1) or not mono.strip():
                continue
            s = re.sub(r"\"[^\"]*\"|“[^”]*”|'[^']*'|‘[^’]*’", " ", mono)   # string literals
            s = re.sub(r"//.*$", " ", s)                                     # comments
            for m in RE_IDENT.finditer(s):
                tok = _clean_ident(m.group(0))
                if len(tok) < 3 or tok.upper() in STOP:
                    continue
                if not re.search(r"[A-Z0-9_]", tok) and "." not in tok:
                    continue          # lower-case words in monospace are prose (comments, messages)
                out.add(tok)
    if text is None:
        text = text_of(doc, region)
    for m in RE_PROSE_ID.finditer(text):
        tok = m.group(0)
        if tok.upper() in STOP or tok in PROSE_NOT_ID or len(tok) < 3:
            continue
        out.add(tok)
    return out


# ---------- references ----------
def refs_in(text, qn=None):
    """Cross-references in a piece of question text."""
    parts, xq = [], []
    used = []
    for m in RE_QPREF.finditer(text):
        lab = f"({m.group(2)})" + (f"({m.group(3)})" if m.group(3) else "")
        if qn is None or int(m.group(1)) == qn:
            parts.append(lab)
        else:
            xq.append(f"{m.group(1)}{lab}")
        used.append((m.start(), m.end()))
    for m in RE_PREF.finditer(text):
        if any(a <= m.start() < b for a, b in used):
            continue
        if m.group(1):
            parts.append(f"({m.group(1)})" + (f"({m.group(2)})" if m.group(2) else ""))
        else:
            parts.append(f"(*)({m.group(3)})")   # sibling roman, letter resolved later
    for m in RE_QREF.finditer(text):
        if qn is not None and int(m.group(1)) != qn:
            xq.append(f"Question {m.group(1)}")
    labs = set()
    for m in RE_LAB.finditer(text):
        L = m.group(1)
        before = text[:m.start()].rstrip()
        if L in ("A", "I"):
            # the article "A" opens a sentence or a bullet; a label does not
            if not before or before[-1] in ".:?!•;–-" or re.search(r"\[\d+\]$", before):
                continue
            nxt = text[m.end():m.end() + 14]
            if L == "A" and re.match(r"\s+(Level|level)\b", nxt):
                continue
        labs.add(L)
    # "use your answer" (not "in your answer", which only says where to write)
    your = bool(re.search(r"\b(use|uses|using|used|from)\s+your\s+(answers?|values?|solution|algorithm|pseudocode|"
                          r"program|table|design)\b", text, re.I))
    insert = bool(re.search(r"\b(?:the|an) insert\b|\bfrom the insert\b|\(from the insert\)", text, re.I))
    appendix = bool(re.search(r"\bAppendix\b", text))
    return {"parts": sorted(set(parts)), "xq": sorted(set(xq)), "labels": sorted(labs), "your": your,
            "insert": insert, "appendix": appendix}


def anaphora(text):
    """Scenario nouns used with 'the/this/these' about something shown earlier
    -> [(noun, position)]."""
    out = []
    for m in RE_ANA.finditer(text):
        before = (m.group(1) or "").strip().lower()
        after = (m.group(3) or "").strip().lower()
        if before in ANA_VERBS or after in ANA_AFTER:
            continue
        out.append((noun_key(m.group(2)), m.start()))
    return out


def build_question(doc, q, nxt_start, rows_q, last):
    parts = q["parts"]
    end = nxt_start
    if last and q.get("last_mark"):
        # the last question ends at the foot of the page that holds its last [mark]
        # (above the small-print copyright paragraph, if that page carries it)
        lp = q["last_mark"][0]
        bot = content_bottom(doc[lp]) + 2.0
        for b in doc[lp].get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                if RE_BOILER.search("".join(sp["text"] for sp in l["spans"])) and l["bbox"][1] > q["last_mark"][1]:
                    bot = min(bot, l["bbox"][1] - 2)
        end = (lp, max(bot, q["last_mark"][1] + 3.0))
    first = parts[0]["start"] if parts else end
    stem = span(doc, q["start"], first) if parts and first != q["start"] else []
    if parts and first[0] == q["start"][0] and abs(first[1] - q["start"][1]) < 3:
        stem = []
    letters = []
    seq = parts
    for i, pt in enumerate(seq):
        if pt["roman"] is None:
            nxt = next((s["start"] for s in seq[i + 1:] if s["roman"] is None), end)
            intro_end = seq[i + 1]["start"] if i + 1 < len(seq) else end
            letters.append({"letter": pt["letter"], "label": pt["label"],
                            "full": span(doc, pt["start"], nxt),
                            "intro": span(doc, pt["start"], intro_end) if intro_end != pt["start"] else [],
                            "romans": []})
            if i + 1 < len(seq) and seq[i + 1]["roman"] and seq[i + 1]["start"] == pt["start"]:
                letters[-1]["intro"] = []
            if not (i + 1 < len(seq) and seq[i + 1]["roman"]):
                letters[-1]["intro"] = []          # no sub-parts: the part has no separate intro
        else:
            nxt = seq[i + 1]["start"] if i + 1 < len(seq) else end
            if not letters:   # romans directly under the question (no letters)
                letters.append({"letter": None, "label": "", "full": span(doc, pt["start"], end),
                                "intro": [], "romans": []})
            letters[-1]["romans"].append({"roman": pt["roman"], "label": pt["label"],
                                          "region": span(doc, pt["start"], nxt)})
    if not parts:
        letters.append({"letter": None, "label": "", "full": span(doc, q["start"], end), "intro": [],
                        "romans": []})
    mk = defaultdict(int)
    for m in q["marks"]:
        mk[m["label"]] += m["value"]
    msm = defaultdict(int)
    msrows = defaultdict(list)
    for r in rows_q:
        msm[r["part"]] += r["mark_total"]
        msrows[r["part"]].append({"label": r["label"], "segs": [[p, list(rc)] for p, rc in r["segs"]],
                                  "marks": r["mark_total"]})
    qn = q["n"]
    for L in letters:
        lab = L["label"]
        L["intro_text"] = text_of(doc, L["intro"])
        L["full_text"] = text_of(doc, L["full"])
        L["marks"] = sum(v for k, v in mk.items() if k.startswith(lab)) if lab else sum(mk.values())
        L["own_marks"] = mk.get(lab, 0)
        L["ms_marks"] = sum(v for k, v in msm.items() if k.startswith(lab)) if lab else sum(msm.values())
        ro = not any(x["letter"] for x in letters)       # romans directly under the question number
        L["ms_rows"] = [r for k in sorted(msrows, key=lambda k: _order(k, ro)) if (k.startswith(lab) if lab else True)
                        for r in msrows[k]]
        L["ms_letter_level"] = bool(lab) and lab in msrows and any(k != lab and k.startswith(lab) for k in mk)
        L["refs"] = refs_in(L["intro_text"], qn)
        L["intro_ids"] = sorted(idents_of(doc, L["intro"], L["intro_text"])) if L["intro"] else []
        L["full_ids"] = sorted(idents_of(doc, L["full"], L["full_text"]))
        for R in L["romans"]:
            R["text"] = text_of(doc, R["region"])
            R["marks"] = mk.get(R["label"], 0)
            R["ms_marks"] = msm.get(R["label"], 0)
            R["ms_rows"] = msrows.get(R["label"], [])
            R["refs"] = refs_in(R["text"], qn)
            R["ids"] = sorted(idents_of(doc, R["region"], R["text"]))
            for i, pr in enumerate(R["refs"]["parts"]):
                if pr.startswith("(*)"):
                    R["refs"]["parts"][i] = (f"({L['letter']})" if L["letter"] else "") + pr[3:]
        L["full_refs"] = refs_in(L["full_text"], qn)
        L["full_refs"]["parts"] = [(f"({L['letter']})" if L["letter"] else "") + p[3:] if p.startswith("(*)") else p
                                   for p in L["full_refs"]["parts"]]
    stem_text = text_of(doc, stem) if stem else ""
    stem_ids = sorted(idents_of(doc, stem, stem_text)) if stem else []
    # first-occurrence map (definition sites) for identifiers, single-letter labels and scenario nouns
    order = [("stem", stem_text, stem_ids)]
    for L in letters:
        if L["romans"]:
            order.append((L["label"] or "Q", L["intro_text"], L["intro_ids"]))
            for R in L["romans"]:
                order.append((R["label"], R["text"], R["ids"]))
        else:
            order.append((L["label"] or "Q", L["full_text"], L["full_ids"]))
    first_def = {}
    all_ids = sorted({x for _, _, ids in order for x in ids})
    for where, t, ids in order:
        # an identifier is defined where its name first appears, in code or in ordinary text
        for x in all_ids:
            if "I:" + x in first_def:
                continue
            # a distinctive name (TwoHumps, WITH_UNDERSCORE, File.txt) also counts where it
            # appears in ordinary text; a plain word (Name, Index) only where it is set as code
            distinctive = bool(re.search(r"[a-z0-9][A-Z]|_|\.|\d", x)) or (x.isupper() and len(x) >= 3)
            if x in ids or (distinctive and re.search(rf"(?<![A-Za-z0-9_]){re.escape(x)}(?![A-Za-z0-9_])", t)):
                first_def["I:" + x] = where
        for lab in refs_in(t, qn)["labels"]:
            first_def.setdefault("L:" + lab, where)
        low = t.lower()
        for n in set(re.findall(rf"\b({NOUNS})(?:s|es)?\b", low)):
            first_def.setdefault("N:" + noun_key(n), where)
    return {"n": qn, "total": q["total"], "stem": stem, "stem_text": stem_text, "stem_ids": stem_ids,
            "stem_refs": refs_in(stem_text, qn), "letters": letters, "captions": {}, "cap_site": {}, "blocks": {},
            "first_def": first_def,
            "ms_unmatched": sorted(k for k in msrows if k and not any(k == L["label"] or k.startswith(L["label"])
                                                                      for L in letters if L["label"]))}


def _order(k, roman_only=False):
    m = None if roman_only else re.match(r"\(([a-z])\)(?:\(([ivx]+)\))?", k)
    if not m:
        m2 = re.match(r"\(([ivx]+)\)", k)
        return (0, ROMANS.index(m2.group(1)) + 1 if m2 else 0)
    return (ord(m.group(1)), ROMANS.index(m.group(2)) + 1 if m.group(2) else 0)


def main():
    phase = sys.argv[1]
    man = jload(MANIFEST)
    checks = jload(work(f"checks_{phase}.json"))
    out = {}
    nq = nl = nr = 0
    for pid, chk in sorted(checks.items()):
        if chk["paper_excluded"]:
            continue
        ent = man[pid]
        qd = load(os.path.join(DATA, ent["qp"]["file"]))
        md = load(os.path.join(DATA, ent["ms"]["file"]))
        qs = parse_qp(qd)
        rows = ms_rows_any(md, qs)
        fix_ms_rows(rows, qs)
        paper = {"pid": pid, "ref": chk["ref"], "code": ent["code"], "year": ent["year"], "series": ent["series"],
                 "variant": ent["variant"], "paper": ent["paper"], "qp": ent["qp"]["file"], "ms": ent["ms"]["file"],
                 "insert": ent["in"]["file"] if ent["in"]["status"] == "ok" else None,
                 "insert_line": chk.get("insert_line", False), "questions": []}
        for i, q in enumerate(qs):
            if not chk["questions"][str(q["n"])]["ok"]:
                continue
            last = i + 1 == len(qs)
            nxt = qs[i + 1]["start"] if not last else (qd.page_count - 1, 800)
            Q = build_question(qd, q, nxt, [r for r in rows if r["q"] == q["n"]], last)
            paper["questions"].append(Q)
            nq += 1
            nl += len(Q["letters"])
            nr += sum(len(L["romans"]) for L in Q["letters"])
        out[pid] = paper
    jdump(out, work(f"parts_{phase}.json"), indent=0)
    print(f"{phase}: papers {len(out)}, questions {nq}, lettered parts {nl}, roman sub-parts {nr}")


if __name__ == "__main__":
    main()

"""CS self-check, shared helpers. Nothing here imports the build's code (hub/scripts/cs): the checks
re-derive questions, parts, marks and mark-scheme rows from the downloaded PDFs and from the built
books themselves."""
import json, os, re
import pymupdf as f

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
DATA = os.path.join(ROOT, "hub", "data")
CS = os.path.join(ROOT, "λ-cs")
OUT = os.path.join(ROOT, "hub", "audit", "out", "cs")
BOOKS = {1: os.path.join(CS, "booklets", "p1-topical-workbook", "CS-9618-P1-Topical-Workbook.pdf"),
         2: os.path.join(CS, "booklets", "p2-topical-workbook", "CS-9618-P2-Topical-Workbook.pdf")}
BOOKDIR = {1: os.path.join(CS, "booklets", "p1-topical-workbook"), 2: os.path.join(CS, "booklets", "p2-topical-workbook")}
UNITS = {1: range(1, 9), 2: range(9, 13)}
URL = "https://pastpapers.papacambridge.com/directories/CAIE/CAIE-pastpapers/upload/"
SER = {"M/J": "s", "O/N": "w", "MAR": "m"}
ROM = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"]
RE_REF = re.compile(r"^(\d+)\.\s+((?:9608 )?(?:M/J|O/N|MAR)\s\d\d/P\d\d/Q\d+\S*)\s*$")
os.makedirs(OUT, exist_ok=True)


def jl(name):
    return json.load(open(os.path.join(OUT, name)))


def jd(obj, name, indent=None):
    json.dump(obj, open(os.path.join(OUT, name), "w"), indent=indent, ensure_ascii=False)


def expected():
    """Every paper the run was told to try: (code, series, yy, variant)."""
    E = []
    for code, years in (("9618", range(21, 27)), ("9608", range(15, 22))):
        for y in years:
            for v in (12, 22):
                E.append((code, "m", y, v))
            for s in ("s", "w"):
                for v in (11, 12, 13, 21, 22, 23):
                    E.append((code, s, y, v))
    return E


def pid(code, s, y, v):
    return f"{code}_{s}{y:02d}_{v}"


def vwords(p):
    m = p.rotation_matrix
    out = []
    for w in p.get_text("words"):
        r = f.Rect(w[:4]) * m
        out.append((r.x0, r.y0, r.x1, r.y1, w[4]))
    return out


def lines(p, tol=3.5, merge=False, words=None):
    """Words in visual coordinates grouped into lines by their vertical centre."""
    ws = sorted(words if words is not None else vwords(p), key=lambda w: ((w[1] + w[3]) / 2, w[0]))
    L = []
    for w in ws:
        c = (w[1] + w[3]) / 2
        if L and abs(L[-1]["c"] - c) < tol:
            L[-1]["w"].append(w)
        else:
            L.append({"c": c, "w": [w]})
    for l in L:
        l["w"].sort(key=lambda w: w[0])
        if merge:      # faux-bold duplicates / overlapping fragments of old PDFs
            out = []
            for w in l["w"]:
                if out and w[0] < out[-1][2] - 0.3:
                    a, b = out[-1][4], w[4]
                    k = 0
                    for j in range(min(len(a), len(b)), 0, -1):
                        if a.endswith(b[:j]):
                            k = j
                            break
                    out[-1] = (out[-1][0], min(out[-1][1], w[1]), max(out[-1][2], w[2]), max(out[-1][3], w[3]),
                               a + b[k:])
                else:
                    out.append(w)
            l["w"] = out
    return L


def ref_key(ref):
    """'9608 M/J 21/P11/Q3/a,b(i)' -> (paper id, question number, suffix)."""
    m = re.match(r"(9608 )?(M/J|O/N|MAR) (\d\d)/P(\d\d)/Q(\d+)(.*)$", ref)
    yy = int(m.group(3))
    code = "9608" if (m.group(1) or yy < 21) else "9618"
    return f"{code}_{SER[m.group(2)]}{m.group(3)}_{m.group(4)}", int(m.group(5)), m.group(6)


def expand(q, suf, leaves):
    """Leaves ('3(b)(ii)') of question q covered by a reference suffix: '', '/a', '/b(i,ii)',
    '/a,b(i)', '/(i,ii)' (romans directly under the question)."""
    if suf == "":
        return list(leaves)
    out = []
    body = suf[1:]
    if body.startswith("("):
        for r in body.strip("()").split(","):
            out += [x for x in leaves if x == f"{q}({r})"]
        return out
    for l, rs in re.findall(r"([a-z])(?:\(([ivx,]+)\))?", body):
        if rs:
            out += [x for x in leaves if any(x == f"{q}({l})({r})" for r in rs.split(","))]
        else:
            out += [x for x in leaves if x == f"{q}({l})" or x.startswith(f"{q}({l})(")]
    return out

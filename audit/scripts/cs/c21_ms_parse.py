"""Check 2 (MS side), independent parser. Two layouts:
 - table (2017 on): 'Question | Answer | Marks' header; compact labels '2(b)(ii)' in the first column,
   whole numbers in the Marks column;
 - running text (2015-16): labels at the start of a line, marks as [n] at the right-hand edge.
Gives, per paper, the rows in reading order: label, marks, page, y."""
import re, sys
from collections import Counter, defaultdict
import pymupdf as f
from c00_common import *

RO = "|".join(sorted(ROM, key=len, reverse=True))
PART = re.compile(r"(\d{1,2})?\.?(?:\(([a-z])\))?(?:\((%s)\))?" % RO)
CMP = re.compile(r"(\d{1,2})(?:\(([a-z])\))?(?:\((%s)\))?" % RO)


def parse_table(d):
    rows, notes = [], []
    cur = None
    st = {"q": None, "L": None, "R": None}
    for pno in range(len(d)):
        p = d[pno]
        Ls = lines(p, merge=True)
        hdr = None
        for l in Ls:
            T = [w[4] for w in l["w"]]
            if T[0].startswith("Question") and any(t.startswith("Answe") for t in T) and any(t.startswith("Mar") for t in T):
                if hdr is None:
                    hdr = {"y": l["c"], "mx": [w[0] for w in l["w"] if w[4].startswith("Mar")][-1],
                           "ax": [w[0] for w in l["w"] if w[4].startswith("Answe")][0],
                           "qx": l["w"][0][0],
                           "gx": ([w[0] for w in l["w"] if w[4].startswith("Guidance")] or [9999])[0]}
        if hdr is None:
            continue
        # the Marks column: between the vertical rules either side of the header word
        rm = p.rotation_matrix
        vx = Counter()
        for g in p.get_drawings():
            r = f.Rect(g["rect"]) * rm
            r.normalize()
            if r.height > 8:
                for x in ((r.x0, r.x1) if r.width > 3 else ((r.x0 + r.x1) / 2,)):
                    vx[round(x)] += r.height
        vr = sorted(x for x, h in vx.items() if h > 40)
        mw = [w for l in Ls if abs(l["c"] - hdr["y"]) < 1 for w in l["w"] if w[4].startswith("Mar")][-1]
        lo = [v for v in vr if v <= mw[0] + 2]
        hi = [v for v in vr if v >= mw[2] - 2]
        # the header word is centred in its column, so the right-hand rule mirrors the left-hand one
        zlo = lo[-1] if lo else hdr["mx"] - 6
        zhi = min(hi, key=lambda v: abs(v - (mw[0] + mw[2] - zlo))) if hi and lo else min(hdr["mx"] + 55, hdr["gx"] - 4)
        for l in Ls:
            if l["c"] <= hdr["y"] - 2:
                continue
            ws = l["w"]
            T = [w[4] for w in ws]
            if T[0].startswith("Question") and any(t.startswith("Mar") for t in T):
                continue
            if any("UCLES" in t for t in T) or (T[0] == "Page" and "of" in T):
                continue
            lab = "".join(w[4] for w in ws if w[0] < hdr["qx"] + 56 and w[2] < hdr["qx"] + 75)
            m = PART.fullmatch(lab) if lab else None
            if m and (m.group(1) or m.group(2) or m.group(3)):
                n, a_, r_ = m.group(1), m.group(2), m.group(3)
                if a_ and not r_ and not n and a_ in ROM and st["L"] is not None and not (a_ == "i" and st["L"] == "h") \
                        and a_ != chr(ord(st["L"]) + 1):
                    a_, r_ = None, a_          # a bare (i) / (v) after a letter is a roman sub-part
                if n:
                    st.update(q=int(n), L=None, R=None)
                if a_:
                    st.update(L=a_, R=None)
                if r_:
                    st["R"] = r_
                if st["q"] is not None:
                    key = f"{st['q']}" + (f"({st['L']})" if st["L"] else "") + (f"({st['R']})" if st["R"] else "")
                    cur = {"label": key, "marks": [], "page": pno + 1, "y": round(l["c"]), "q": st["q"]}
                    rows.append(cur)
            elif lab and cur is not None and not re.fullmatch(r"[•\-–]?", lab):
                notes.append(f"p{pno + 1} y{round(l['c'])}: text in label column: {lab[:20]!r}")
            zone = [w for w in ws if zlo - 1 <= w[0] and w[2] <= zhi + 1]
            zn = [w for w in zone if not re.fullmatch(r"\(?[Mm][Aa][Xx][A-Za-z]*[.:]?\)?", w[4])]
            for w in zn:
                mm = re.fullmatch(r"\[?(?:[Mm][Aa][Xx])?(\d{1,2})\]?", w[4])     # 2, [2], Max2, MAX8
                if mm and len(zn) == 1:
                    w = w[:4] + (mm.group(1),)
                    if cur is None:
                        notes.append(f"p{pno + 1}: mark before any label")
                    else:
                        cur["marks"].append((int(w[4]), pno + 1, round(l["c"])))
    return rows, notes


def parse_text(d):
    """Running-text mark schemes: per question, every [n] printed at the right-hand edge."""
    rows, notes = [], []
    q = 0
    L = R = None
    cur = None
    cx = Counter(round(w[2]) for pg in d for w in vwords(pg) if re.fullmatch(r"\[\d{1,2}\]", w[4]))
    for pno in range(1, len(d)):
        p = d[pno]
        Ls = lines(p, merge=True)
        for l in Ls:
            ws = l["w"]
            T = [w[4] for w in ws]
            if l["c"] < 66 or any("UCLES" in t for t in T):
                continue
            k = 0
            if re.fullmatch(r"\d{1,2}", T[0]) and ws[0][0] < 64 and int(T[0]) == q + 1 and \
                    (len(T) == 1 or ws[1][0] - ws[0][2] > 6):
                q, L, R, k = q + 1, None, None, 1
                cur = None
            # labels: the first words left of the answer text, re-joined ("(i" "i)" -> "(ii)")
            head = "".join(w[4] for w in ws[k:k + 5] if w[0] < 112)
            for t in re.findall(r"\(([a-z]{1,4})\)", head if re.match(r"(\([a-z]{1,4}\))+", head) else ""):
                if len(t) == 1 and t == ("a" if L is None else chr(ord(L) + 1)) and not (t == "i" and L != "h"):
                    L, R = t, None
                    cur = None
                elif t in ROM and (R is None and t == "i" or R in ROM and ROM.index(t) == ROM.index(R) + 1):
                    R = t
                    cur = None
                elif len(t) == 1 and L and t > L and t not in ("i", "v", "x"):
                    notes.append(f"Q{q}: ({t}) follows ({L}) p{pno + 1}")
                    L, R = t, None
                    cur = None
            if not q:
                continue
            # marks: what is printed at the right-hand edge, re-joined ("[1" "]", "[MAX" "6]", "[Max." "2]")
            tail = "".join(w[4] for w in ws if w[2] > 470)
            for m in re.finditer(r"\[(max\.?:?|maximum)?(\d{1,2})\]", tail, re.I):
                if cur is None:
                    key = f"{q}" + (f"({L})" if L else "") + (f"({R})" if R else "")
                    cur = {"label": key, "marks": [], "max": [], "page": pno + 1, "y": round(l["c"]), "q": q}
                    rows.append(cur)
                (cur["max"] if m.group(1) else cur["marks"]).append((int(m.group(2)), pno + 1, round(l["c"])))
    return rows, notes


def parse_ms(fn):
    d = f.open(fn)
    table = False
    for pg in list(d)[1:]:
        for l in lines(pg, merge=True):
            T = [w[4] for w in l["w"]]
            if T[0].startswith("Question") and any(t.startswith("Answe") for t in T) and any(t.startswith("Mar") for t in T) and len(T) <= 5:
                table = True
    rows, notes = parse_table(d) if table else parse_text(d)
    return {"layout": "table" if table else "text", "rows": rows, "notes": notes}


if __name__ == "__main__":
    src = jl("sources.json")
    out = {}
    for r in src:
        if r["kind"] == "ms" and r["status"] == "OK":
            out[r["pid"]] = parse_ms(os.path.join(DATA, r["file"]))
    jd(out, "ms_parse.json")
    print(len(out), "MS parsed;", Counter(v["layout"] for v in out.values()))
    print("rows", sum(len(v["rows"]) for v in out.values()), "| rows without a mark", sum(1 for v in out.values() for r in v["rows"] if not r["marks"] and not r.get("max")),
          "| notes", sum(len(v["notes"]) for v in out.values()))

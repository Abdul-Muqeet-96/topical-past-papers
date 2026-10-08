"""Check 2 (QP side), independent parser. For each downloaded question paper: question numbers
(integers at the left margin that are not program text), lettered parts, roman sub-parts, [n] marks
and [Total: n], in reading order, plus the total printed on the cover. Fonts (not character
advances) are used to tell code from prose, and the download-site stamps are skipped by size/position,
so nothing is shared with hub/scripts/cs/parse.py."""
import re, sys
from collections import Counter
import pymupdf as f
from c00_common import *

NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}


def plines(p):
    """Horizontal text lines of a page as lists of (x0,y0,x1,y1,text,mono,size), stamps removed."""
    ws = []
    for b in p.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            if abs(l["dir"][0] - 1) > 0.01:
                continue
            for s in l["spans"]:
                if s["size"] < 5.6 or not s["text"].strip():
                    continue
                if re.search(r"papacambridge|Trace ID", s["text"], re.I):
                    continue
                mono = bool(re.search(r"Courier|Mono|Consol", s["font"], re.I))
                # split the span into words with proportional x positions
                x0, y0, x1, y1 = s["bbox"]
                t = s["text"]
                n = max(1, len(t))
                for m in re.finditer(r"\S+", t):
                    ws.append((x0 + (x1 - x0) * m.start() / n, y0, x0 + (x1 - x0) * m.end() / n, y1, m.group(), mono,
                               s["size"]))
    ws.sort(key=lambda w: ((w[1] + w[3]) / 2, w[0]))
    L = []
    for w in ws:
        c = (w[1] + w[3]) / 2
        if L and abs(L[-1][0] - c) < 3.5:
            L[-1][1].append(w)
        else:
            L.append([c, [w]])
    for l in L:
        l[1].sort(key=lambda w: w[0])
    return L


def cover_total(d):
    for p in list(d)[:2]:
        t = re.sub(r"\s+", " ", p.get_text())
        m = re.search(r"total (?:number of )?marks? (?:for|available for|on) this paper is (\d+)", t, re.I)
        if m:
            return int(m.group(1))
        m = re.search(r"maximum (?:number of )?marks? (?:for this paper )?is (\d+)", t, re.I)
        if m:
            return int(m.group(1))
    return None


def parse_qp(fn):
    d = f.open(fn)
    ev, notes, stray = [], [], []
    last_q = 0
    in_apx = False
    # the column where this paper prints its marks (right edge of the commonest [n])
    cx = Counter(round(w[2]) for pg in d for w in pg.get_text('words') if re.fullmatch(r'\[\d{1,2}\]', w[4]))
    COL = cx.most_common(1)[0][0] if cx else 546
    for pno in range(1, len(d)):
        p = d[pno]
        txt = p.get_text()
        flat = re.sub(r"\s+", " ", txt)
        if "BLANK PAGE" in txt and len(re.sub(r"papacambridge.*|Trace ID.*|Downloaded.*|Licensed.*|\d{4}/\d\d.*", "", txt,
                                              flags=re.I).strip()) < 400 and not re.search(r"\[\d+\]", txt):
            continue
        PL = plines(p)
        body = [(c, W) for c, W in PL if 40 <= c <= p.rect.height - 38 and not any("UCLES" in w[4] for w in W)]
        first = " ".join(w[4] for w in body[0][1]) if body else ""
        if re.fullmatch(r"(Appendix|APPENDIX)( [A-Z0-9])?", first.strip()) or \
                (in_apx and not any(re.fullmatch(r"\[\d{1,2}\]", w[4]) for c, W in body for w in W)):
            notes.append(f"p{pno + 1} appendix")
            in_apx = True
            continue
        in_apx = False
        H = p.rect.height
        for c, W in PL:
            if c < 40 or c > H - 38:
                # the mark of the last part may sit on the footer row: keep only a right-margin [n]
                W = [w for w in W if re.fullmatch(r"\[\d{1,2}\]", w[4]) and abs(w[2] - COL) < 4 and c < H - 20]
                if not W:
                    continue
            if any("UCLES" in w[4] for w in W):
                W = [w for w in W if re.fullmatch(r"\[\d{1,2}\]", w[4]) and abs(w[2] - COL) < 4]
                if not W:
                    continue
            k = 0
            w0 = W[0]
            if re.fullmatch(r"[1-9]\d?", w0[4]) and w0[0] < 64 and not w0[5]:
                n = int(w0[4])
                if n == last_q + 1:
                    last_q = n
                    ev.append(("Q", n, pno, c))
                    k = 1
                else:
                    stray.append((n, pno + 1, round(c)))
            for w in W[k:k + 2]:
                m = re.fullmatch(r"\(([a-z]{1,4})\)", w[4])
                if not m or w[0] > 122 or w[5]:
                    break
                ev.append(("P", m.group(1), pno, c, w[0]))
            for i, w in enumerate(W):
                m = re.fullmatch(r"[.…_ ]*\[(\d{1,2})\]", w[4])   # a mark is a word of its own, not Name[4]
                if m and not w[5]:
                    ev.append(("M" if abs(w[2] - COL) < 4 and i == len(W) - 1 else "m",
                               int(m.group(1)), pno, c, round(w[2])))
                elif re.fullmatch(r"\[\d{1,2}", w[4]) and i + 1 < len(W) and W[i + 1][4] == "]" and abs(W[i + 1][2] - COL) < 4:
                    ev.append(("M", int(w[4][1:]), pno, c, round(W[i + 1][2])))
                if w[4] == "[Total:" and i + 1 < len(W):
                    m2 = re.fullmatch(r"(\d{1,2})\]", W[i + 1][4])
                    if m2:
                        ev.append(("T", int(m2.group(1)), pno, c))
    # label columns: lettered parts sit left of roman parts
    xa = Counter(round(e[4]) for e in ev if e[0] == "P" and e[1] == "a")
    xl = xa.most_common(1)[0][0] if xa else 72
    parts, pos, totals, inner = {}, {}, {}, {}
    q = L = R = None
    for e in ev:
        if e[0] == "Q":
            q, L, R = e[1], None, None
            parts.setdefault(q, {})
        elif e[0] == "P":
            if q is None:
                continue
            t = e[1]
            at_letter = abs(e[4] - xl) < 9
            nxt_letter = "a" if L is None else chr(ord(L) + 1)
            nxt_rom = "i" if R is None else (ROM[ROM.index(R) + 1] if R in ROM[:-1] else None)
            if at_letter and len(t) == 1 and t == nxt_letter:
                L, R = t, None
            elif t in ROM and t == nxt_rom and (not at_letter or L is None or t != "i" or L != "h"):
                R = t
            elif at_letter and len(t) == 1 and L and t > L:
                notes.append(f"Q{q}: letter ({t}) follows ({L}) p{e[2] + 1}")
                L, R = t, None
            elif t in ROM and R and ROM.index(t) > ROM.index(R):
                notes.append(f"Q{q}: roman ({t}) follows ({R}) p{e[2] + 1}")
                R = t
        elif e[0] in "Mm":
            if q is None:
                notes.append(f"mark before any question p{e[2] + 1}")
                continue
            key = f"{q}" + (f"({L})" if L else "") + (f"({R})" if R else "")
            tgt = parts if e[0] == "M" else inner
            if e[0] == "M":
                parts[q][key] = parts[q].get(key, 0) + e[1]
                pos.setdefault(key, []).append((e[2] + 1, round(e[3])))
            else:
                inner.setdefault(q, []).append((key, e[1], e[2] + 1, round(e[3]), e[4]))
        elif e[0] == "T" and q is not None:
            totals.setdefault(q, []).append(e[1])
    return {"qnums": [e[1] for e in ev if e[0] == "Q"], "parts": parts, "totals": totals, "inner": inner,
            "pos": pos, "stray": stray, "notes": notes, "pages": len(d), "cover": cover_total(d),
            "qpos": {e[1]: (e[2] + 1, round(e[3])) for e in ev if e[0] == "Q"}}


if __name__ == "__main__":
    src = jl("sources.json")
    ok = {}
    for r in src:
        ok.setdefault(r["pid"], {})[r["kind"]] = r["status"]
    out = {}
    for pid_, st in sorted(ok.items()):
        if st.get("qp") != "OK":
            continue
        code, sy, v = pid_.split("_")
        out[pid_] = parse_qp(os.path.join(DATA, f"{code}_{sy}_qp_{v}.pdf"))
    jd(out, "qp_parse.json")
    bad = 0
    for k, v in out.items():
        qn = v["qnums"]
        g = sum(sum(x.values()) for x in v["parts"].values())
        gi = sum(m[1] for x in v["inner"].values() for m in x)
        tot_ok = all(len(t) == 1 and t[0] == sum(v["parts"][q].values()) for q, t in v["totals"].items())
        real_notes = [n for n in v["notes"] if "appendix" not in n]
        if not (qn == list(range(1, len(qn) + 1)) and g == v["cover"] == 75 and tot_ok) or real_notes:
            bad += 1
            print(k, "cover", v["cover"], "margin marks", g, "inner marks", gi, "| totals ok", tot_ok, "| stray", v["stray"][:4],
                  "|", v["notes"][:3])
    print(len(out), "QPs parsed;", bad, "need a look (margin marks != cover total, or notes)")
    print("questions", sum(len(v["qnums"]) for v in out.values()), "leaves", sum(len(x) for v in out.values() for x in v["parts"].values()))

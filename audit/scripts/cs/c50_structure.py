"""Check 9 STRUCTURE of both books: cover figures, contents entries against the real pages, unit
title pages (name, item count, marks, sections against the syllabus PDF), banners, running headers,
printed page numbers, bookmarks, newest-first order, the Topic index rows against index.csv, and
the Appendix (P2: the newest insert, once; P1: none)."""
import csv, json, re
from collections import Counter, defaultdict
import pymupdf as f
from c00_common import *

SPEC_UNITS = {1: "Information representation", 2: "Communication", 3: "Hardware", 4: "Processor Fundamentals",
              5: "System Software", 6: "Security, privacy and data integrity", 7: "Ethics and Ownership",
              8: "Databases", 9: "Algorithm Design and Problem-solving", 10: "Data Types and Structures",
              11: "Programming", 12: "Software Development"}
SPEC_SECS = {1: 3, 2: 1, 3: 2, 4: 3, 5: 2, 6: 2, 7: 1, 8: 3, 9: 2, 10: 4, 11: 3, 12: 3}
NAME = {1: "Computer Science 9618 Paper 1 Topical Workbook", 2: "Computer Science 9618 Paper 2 Topical Workbook"}
SORD = {"MAR": 0, "M/J": 1, "O/N": 2}
# section names straight from the syllabus PDF (independent of work/syllabus.json)
sd = f.open(os.path.join(CS, "cs-syllabus.pdf"))
stext = "\n".join(p.get_text() for p in sd)
out = {}
allF = []
for book in (1, 2):
    F = []
    info = {}
    bp = jl(f"book_parse_p{book}.json")
    d = f.open(BOOKS[book])
    P = bp["pages"]
    idx = list(csv.DictReader(open(os.path.join(BOOKDIR[book], "index.csv"))))
    Q = sorted([i for i in bp["items"] if i["side"] == "Q"], key=lambda i: (i["page"], i["y"]))
    kinds = [p["kind"] for p in P]
    info["kinds"] = dict(Counter(kinds))
    if kinds[0] != "cover":
        F.append(("page 1 is not the cover",))
    if "unknown" in kinds:
        F.append(("pages of unknown kind", [p["i"] for p in P if p["kind"] == "unknown"][:10]))
    # ---- cover ----
    ct = d[0].get_text()
    want_sub = {1: "Paper 1 · Theory Fundamentals", 2: "Paper 2 · Fundamental Problem-solving and Programming Skills"}[book]
    if "Computer Science 9618" not in ct or want_sub not in ct:
        F.append(("cover title/subtitle", ct[:80]))
    m = re.search(r"(\d+) papers: (.+?) to (.+?) \(newest first", ct)
    m2 = re.search(r"(\d+) items, (\d+) marks across (\d+) units", ct)
    papers = {re.match(r"((?:9608 )?\S+ \d\d/P\d\d)", r["reference"]).group(1) for r in idx}
    marks = sum(int(r["marks"]) for r in idx)
    if not m or int(m.group(1)) != len(papers):
        F.append(("cover paper count", m and m.group(1), len(papers)))
    if not m2 or (int(m2.group(1)), int(m2.group(2)), int(m2.group(3))) != (len(idx), marks, len(UNITS[book])):
        F.append(("cover items/marks/units", m2 and m2.groups(), (len(idx), marks, len(UNITS[book]))))
    def pkey(pr):
        mm = re.match(r"(9608 )?(\S+) (\d\d)/P(\d\d)", pr)
        return (int(mm.group(3)), SORD[mm.group(2)], 0 if mm.group(1) or int(mm.group(3)) < 21 else 1, int(mm.group(4)))
    if m and papers:
        srt = sorted(papers, key=pkey)
        if (m.group(2), m.group(3)) != (srt[0], srt[-1]):
            F.append(("cover paper range", (m.group(2), m.group(3)), (srt[0], srt[-1])))
    mc = re.search(r"(\d+) items come from Paper (\d) papers", ct)
    cross = sum(1 for r in idx if int(re.search(r"/P(\d)", r["reference"]).group(1)) != book)
    if (int(mc.group(1)) if mc else 0) != cross or (mc and int(mc.group(2)) != 3 - book):
        F.append(("cover cross-filed count", mc and mc.group(0), cross))
    codes = sorted({"9608" if ref_key(r["reference"])[0].startswith("9608") else "9618" for r in idx})
    mcode = re.search(r"Syllabus codes: ([\d, ]+)", ct)
    if not mcode or [c.strip() for c in mcode.group(1).split(",")] != codes:
        F.append(("cover syllabus codes", mcode and mcode.group(1), codes))
    info["cover"] = {"papers": len(papers), "items": len(idx), "marks": marks, "cross_filed": cross}
    # ---- contents ----
    cpages = [p["i"] for p in P if p["kind"] == "contents"]
    ctext = "".join(d[i - 1].get_text() for i in cpages)
    ents = re.findall(r"^(.+?) ?\.{3,} ?\n?(\d+)$", ctext, re.M)
    if not ents:
        # label, dots and number may be separate lines
        ls = [x for x in ctext.split("\n") if x.strip()]
        ents = []
        for k, x in enumerate(ls):
            if re.fullmatch(r"\d+", x.strip()) and k >= 1:
                name = ls[k - 1] if not re.fullmatch(r"\.+", ls[k - 1].strip()) else ls[k - 2]
                ents.append((re.sub(r"\s*\.{3,}\s*$", "", name).strip(), x.strip()))
    info["contents_entries"] = len(ents)
    utitle = {p["unit_title"]: p["i"] for p in P if "unit_title" in p}
    first_ans = {}
    for p in P:
        if p["kind"] == "answers" and p["unit"] not in first_ans:
            first_ans[p["unit"]] = p["i"]
    idx_first = next((p["i"] for p in P if p["kind"] == "index"), None)
    app_first = next((p["i"] for p in P if p["kind"] == "appendix"), None)
    exp = []
    for u in UNITS[book]:
        exp.append((SPEC_UNITS[u], utitle.get(u)))
        exp.append(("Answers Section", first_ans.get(u)))
    exp.append(("Topic index", idx_first))
    if book == 2:
        exp.append(("Insert: pseudocode functions and operators", app_first))
    got = [(a.strip(), int(b)) for a, b in ents]
    if got != exp:
        F.append(("contents entries != real pages", [x for x in zip(got, exp) if x[0] != x[1]][:6], len(got), len(exp)))
    lab = re.findall(r"^(UNIT \d+|INDEX|APPENDIX)$", ctext, re.M)
    if lab != [f"UNIT {u}" for u in UNITS[book]] + ["INDEX"] + (["APPENDIX"] if book == 2 else []):
        F.append(("contents labels", lab))
    # ---- unit title pages ----
    for u in UNITS[book]:
        tpg = next((p for p in P if p.get("unit_title") == u), None)
        if not tpg:
            F.append(("no title page", u))
            continue
        qi = [i for i in Q if i["unit"] == u]
        um = sum(int(r["marks"]) for r in idx if int(r["unit"]) == u)
        if (tpg["title_items"], tpg["title_marks"]) != (len(qi), um):
            F.append(("title page counts", u, (tpg["title_items"], tpg["title_marks"]), (len(qi), um)))
        if tpg["title_name"] != SPEC_UNITS[u].upper():
            F.append(("title page name", u, tpg["title_name"]))
        secs = tpg["title_sections"]
        if [s for s, _ in secs] != [f"{u}.{k}" for k in range(1, SPEC_SECS[u] + 1)]:
            F.append(("title page sections", u, [s for s, _ in secs]))
        for s, nm in secs:
            if not re.search(re.escape(s) + r"\s+" + re.escape(nm).replace(r"\ ", r"\s+"), stext):
                F.append(("section name not found in the syllabus PDF", s, nm))
        if not re.search(rf"\b{u}\s+{re.escape(SPEC_UNITS[u])}", stext):
            F.append(("unit name not found in the syllabus PDF", u))
        nxt = P[tpg["i"]] if tpg["i"] < len(P) else None
        if not nxt or nxt["banner"] != [f"Unit {u}: {SPEC_UNITS[u]}"]:
            F.append(("no unit banner after the title page", u, nxt and nxt["banner"]))
        ap = P[first_ans[u] - 1] if u in first_ans else None
        if not ap or ap["banner"] != ["Answers Section"]:
            F.append(("no Answers banner", u))
    # ---- running headers and page numbers ----
    bad_h, bad_n = [], []
    for p in P:
        if p["kind"] in ("cover", "contents", "unit_title"):
            if p["header"]:
                bad_h.append((p["i"], "header on a front/title page"))
            continue
        h = p["header"]
        want = {"question": f"Unit {p['unit']}: {SPEC_UNITS.get(p['unit'])}", "answers": f"Unit {p['unit']}: Answers Section",
                "index": "Topic index", "appendix": "Appendix: Insert"}.get(p["kind"])
        joined = " ".join(h)
        if not joined.startswith(NAME[book]) or not joined.endswith(want or "?"):
            bad_h.append((p["i"], joined[-60:], want))
        mm = re.search(re.escape(NAME[book]) + r" (\d+) ", joined)
        if not mm or int(mm.group(1)) != p["i"]:
            bad_n.append(p["i"])
    info["bad_headers"], info["bad_numbers"] = len(bad_h), len(bad_n)
    if bad_h:
        F.append(("running headers", bad_h[:6]))
    if bad_n:
        F.append(("printed page numbers", bad_n[:10]))
    sizes = Counter((p["w"], p["h"]) for p in P)
    if set(sizes) != {(595.3, 841.9)}:
        F.append(("page sizes", dict(sizes)))
    # ---- bookmarks ----
    toc = bp["toc"]
    exp_toc = [[1, "Contents", cpages[0] if cpages else None]]
    for u in UNITS[book]:
        exp_toc.append([1, f"Unit {u}: {SPEC_UNITS[u]}", utitle.get(u)])
        exp_toc.append([2, f"Unit {u}: Answers Section", first_ans.get(u)])
    exp_toc.append([1, "Topic index", idx_first])
    if book == 2:
        exp_toc.append([1, "Appendix: Insert: pseudocode functions and operators", app_first])
    if toc != exp_toc:
        F.append(("bookmarks", [x for x in zip(toc, exp_toc) if x[0] != x[1]][:5], len(toc), len(exp_toc)))
    # ---- order: newest first; within a paper by question and part ----
    def key(ref):
        mm = re.match(r"(9608 )?(M/J|O/N|MAR) (\d\d)/P(\d\d)/Q(\d+)(.*)", ref)
        code = 0 if (mm.group(1) or int(mm.group(3)) < 21) else 1
        return (int(mm.group(3)), SORD[mm.group(2)], code, int(mm.group(4)), int(mm.group(5)))
    bad_o = []
    for u in UNITS[book]:
        q = [i for i in Q if i["unit"] == u]
        for a, b in zip(q, q[1:]):
            if key(a["ref"])[:3] < key(b["ref"])[:3]:
                bad_o.append((u, a["ref"], b["ref"], b["page"]))
    info["order_violations"] = len(bad_o)
    if bad_o:
        F.append(("newest-first order", bad_o[:6]))
    # ---- items start where the page flow says: question pages have at least one band or heading ----
    empty = [p["i"] for p in P if p["kind"] in ("question", "answers") and p["nwords"] < 12]
    if empty:
        F.append(("near-empty body pages", empty[:20]))
    # ---- topic index rows == index.csv ----
    rows = []
    for p in P:
        if p["kind"] != "index":
            continue
        for l in lines(d[p["i"] - 1]):
            ws = l["w"]
            t = " ".join(w[4] for w in ws)
            mm = re.match(r"((?:9608 )?(?:M/J|O/N|MAR) \d\d/P\d\d/Q\S+)\s+(\d+)\s+(\d+)\s+(\d+)(.*)$", t)
            if mm and ws[0][0] < 46:
                rows.append((mm.group(1), mm.group(2), mm.group(3), mm.group(4), mm.group(5).strip()))
    exp_rows = [(r["reference"], r["unit"], r["marks"], r["page"]) for r in idx]
    got_rows = [r[:4] for r in rows]
    trunc = [(g, e) for g, e in zip(got_rows, exp_rows) if g != e and not (g[0].endswith("…") and e[0].startswith(g[0][:-1]) and g[1:] == e[1:])]
    if len(got_rows) != len(exp_rows) or trunc:
        F.append(("topic index rows != index.csv", len(got_rows), len(exp_rows), trunc[:5]))
    info["index_rows"] = len(rows)
    info["index_refs_truncated"] = sum(1 for g in got_rows if g[0].endswith("…"))
    extra_bad = 0
    for g, r in zip(rows, idx):
        e = []
        if r["also_topics"]:
            e.append("also " + ", ".join(f"U{x.split(':')[0]}:{x.split(':')[1]}" for x in r["also_topics"].split(";")))
        if r["context_parts"]:
            e.append("ctx " + ", ".join(r["context_parts"].split(";")))
        if r["insert"]:
            e.append("insert " + ("(Appendix)" if r["insert"] == "note" else "inline"))
        want = "; ".join(e)
        if g[4] != want and not (g[4].endswith("…") and want.startswith(g[4][:-1])):
            extra_bad += 1
    if extra_bad:
        F.append(("topic index 'also / context' column != index.csv", extra_bad))
    # ---- appendix ----
    if book == 1 and app_first:
        F.append(("P1 has an appendix",))
    if book == 2:
        if not app_first:
            F.append(("P2 has no appendix",))
        else:
            ap = [p for p in P if p["kind"] == "appendix"]
            ban = ap[0]["banner"]
            ins = [r for r in jl("sources.json") if r["kind"] == "in" and r["status"] == "OK"]
            skey = lambda r: (int(r["pid"].split("_")[1][1:]), {"m": 0, "s": 1, "w": 2}[r["pid"].split("_")[1][0]])
            top = max(skey(r) for r in ins)
            newest = [r for r in ins if skey(r) == top]        # every variant of the newest series
            mm = re.search(r"\(from ((?:M/J|O/N|MAR) \d\d/P\d\d)\)", ban[0]) if ban else None
            named = None
            for r in newest:
                code, sy, v = r["pid"].split("_")
                if mm and mm.group(1) == f"{ {'s': 'M/J', 'w': 'O/N', 'm': 'MAR'}[sy[0]]} {sy[1:]}/P{v}":
                    named = r
            info["appendix"] = {"pages": [p["i"] for p in ap], "banner": ban, "newest_series_inserts": [r["file"] for r in newest],
                                "named": named and named["file"]}
            if not named:
                F.append(("appendix is not an insert of the newest series", ban))
            else:
                src = f.open(os.path.join(DATA, named["file"]))
                tok = lambda s_: Counter(re.findall(r"[A-Za-z_<>]{2,}|\d+", s_))
                st = Counter()
                for pg in list(src)[1:]:
                    ws = pg.get_text("words")
                    if any(w[4] == "BLANK" for w in ws) and len(ws) < 60:
                        continue
                    cut = min([w[1] for w in ws if w[4] == "Permission" and w[1] > 0.5 * pg.rect.height] +
                              [w[1] for w in ws if ("UCLES" in w[4] or w[4] == "©") and w[1] > 0.8 * pg.rect.height] + [pg.rect.height - 30])
                    body = [w for w in ws if 50 < w[1] < cut - 2]
                    st += tok(" ".join(w[4] for w in body if not re.search(r"papacambridge", w[4], re.I)))
                at = Counter()
                for p in ap:
                    t = d[p["i"] - 1].get_text(clip=f.Rect(0, 50, 596, 842))
                    at += tok("\n".join(l for l in t.split("\n") if not l.startswith("Appendix: Insert")))
                miss = sum((st - at).values())
                extra = sum((at - st).values())
                info["appendix"].update(source_tokens=sum(st.values()), missing=miss, extra=extra,
                                        missing_examples=list((st - at))[:12], extra_examples=list((at - st))[:12])
                if miss > 0.01 * sum(st.values()) or extra > 0.01 * sum(st.values()):
                    F.append(("appendix text differs from the insert", miss, extra, list((st - at))[:10], list((at - st))[:10]))
            n_app = sum(1 for p in P if p["banner"] and p["banner"][0].startswith("Appendix:"))
            if n_app != 1:
                F.append(("appendix banner count", n_app))
            if ap[-1]["i"] != len(P):
                F.append(("appendix is not last",))
    out[f"P{book}"] = {"info": info, "fail": F}
    allF += [(book,) + tuple(x) for x in F]
    print(f"P{book}:", {k: v for k, v in info.items() if k != "kinds"}, "| kinds", info["kinds"])
jd(out, "structure.json", 1)
print("structure failures:", len(allF))
for x in allF:
    print("  ", str(x)[:400])

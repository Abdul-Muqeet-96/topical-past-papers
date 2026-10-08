"""Check 4 THREE-WAY: the book (question side, answers side), index.csv, items.jsonl, topics.json,
the unit PDFs and the build's own item list must tell the same story: same items, units, numbers,
order, pages, answer pages, marks, notes."""
import csv, glob, json, re
from collections import Counter, defaultdict
from c00_common import *

F = []


def fail(kind, book, ref, detail=""):
    F.append({"kind": kind, "book": book, "ref": ref, "detail": str(detail)[:200]})


tot = Counter()
allrefs = Counter()
work_items = []
for ph in ("phase1", "phase2"):
    work_items += json.load(open(os.path.join(CS, "work", f"items_{ph}.json")))
wi = {i["ref"]: i for i in work_items}
syl = json.load(open(os.path.join(CS, "work", "syllabus.json")))
for book in (1, 2):
    bp = jl(f"book_parse_p{book}.json")
    Q = [i for i in bp["items"] if i["side"] == "Q"]
    A = [i for i in bp["items"] if i["side"] == "A"]
    idx = list(csv.DictReader(open(os.path.join(BOOKDIR[book], "index.csv"))))
    js = [json.loads(l) for l in open(os.path.join(BOOKDIR[book], "items.jsonl"))]
    tp = json.load(open(os.path.join(BOOKDIR[book], "topics.json")))
    tot.update({f"P{book} Q headings": len(Q), f"P{book} A headings": len(A), f"P{book} index rows": len(idx),
                f"P{book} jsonl rows": len(js)})
    bq = {i["ref"]: i for i in Q}
    ba = {i["ref"]: i for i in A}
    for name, lst in (("book-Q", [i["ref"] for i in Q]), ("book-A", [i["ref"] for i in A]),
                      ("index", [r["reference"] for r in idx]), ("jsonl", [r["reference"] for r in js])):
        for r, c in Counter(lst).items():
            if c > 1:
                fail(f"duplicate ref in {name}", book, r, c)
    ix = {r["reference"]: r for r in idx}
    jx = {r["reference"]: r for r in js}
    for r in bq:
        allrefs[r] += 1
    for a, b, na, nb in ((bq, ix, "book", "index"), (bq, jx, "book", "jsonl"), (bq, ba, "book-Q", "book-A"),
                         (bq, {k: v for k, v in wi.items() if v["book"] == book}, "book", "work items")):
        for r in set(a) - set(b):
            fail(f"in {na} not in {nb}", book, r)
        for r in set(b) - set(a):
            fail(f"in {nb} not in {na}", book, r)
    if [r["reference"] for r in idx] != [r["reference"] for r in js]:
        fail("index.csv order != items.jsonl order", book, None)
    for r in set(bq) & set(ix) & set(jx):
        b, i, j = bq[r], ix[r], jx[r]
        if int(i["unit"]) != b["unit"] or j["unit"] != b["unit"]:
            fail("unit differs", book, r, (b["unit"], i["unit"], j["unit"]))
        if b["unit"] not in UNITS[book]:
            fail("unit not in this book", book, r, b["unit"])
        if int(i["page"]) != b["page"] or j["page"] != b["page"]:
            fail("page differs", book, r, (b["page"], i["page"], j["page"]))
        if r in ba and (str(ba[r]["page"]) != i["answer_page"] or ba[r]["page"] != j["answer_page"]):
            fail("answer page differs", book, r, (ba[r]["page"], i["answer_page"], j["answer_page"]))
        if int(i["marks"]) != j["marks"]:
            fail("marks differ index/jsonl", book, r, (i["marks"], j["marks"]))
        if j["book"] != f"P{book}":
            fail("jsonl book field", book, r, j["book"])
        code = "9608" if ref_key(r)[0].startswith("9608") else "9618"
        if j["syllabus_code"] != code:
            fail("syllabus_code", book, r, j["syllabus_code"])
        if j["unit_name"] != syl["units"][str(b["unit"])] if isinstance(syl["units"], dict) else False:
            fail("unit_name", book, r, j["unit_name"])
        if ";".join(j["sections"]) != i["sections"]:
            fail("sections differ index/jsonl", book, r, (i["sections"], j["sections"]))
        if any(int(s.split(".")[0]) != b["unit"] for s in j["sections"]) and not j["also_units"]:
            fail("section outside the unit without an 'also' note", book, r, j["sections"])
        if any(lo not in syl["los"] for lo in j["learning_outcomes"]):
            fail("learning outcome id not in the syllabus", book, r, j["learning_outcomes"])
        if sorted({lo.rsplit(".", 1)[0] for lo in j["learning_outcomes"]}) != sorted(j["sections"]):
            fail("sections != sections of the learning outcomes", book, r, (j["sections"], j["learning_outcomes"]))
        also_i = ";".join(f"{k}:{v}" for k, v in j["also_units"].items())
        if also_i != i["also_topics"]:
            fail("also differs index/jsonl", book, r, (i["also_topics"], also_i))
        note_also = [n for n in b["notes"] if n.startswith("also Unit")]
        if bool(note_also) != bool(j["also_units"]):
            fail("'also' note on the page != data", book, r, (note_also, j["also_units"]))
        elif note_also:
            got = {int(a): int(m) for a, m in re.findall(r"Unit (\d+) \((\d+) marks?\)", note_also[0])}
            if got != {int(k): v for k, v in j["also_units"].items()}:
                fail("'also' note values", book, r, (note_also, j["also_units"]))
            mm = re.search(r"this unit (\d+) mark", note_also[0])
            if not mm or int(mm.group(1)) + sum(got.values()) != j["marks"]:
                fail("'also' note marks do not add up to the item", book, r, (note_also, j["marks"]))
        note_ins = any(n.startswith("Uses the insert") for n in b["notes"])
        if note_ins != (i["insert"] == "note") or (j["insert"] == "appendix") != (i["insert"] == "note") \
                or (j["insert"] == "inline") != (i["insert"] == "inline"):
            fail("insert flag differs page/index/jsonl", book, r, (b["notes"], i["insert"], j["insert"]))
        if ";".join(c.replace("#intro", " intro") for c in j["context_parts"]) != i["context_parts"]:
            fail("context differs index/jsonl", book, r)
        if not j["text"].strip():
            fail("empty text in jsonl", book, r)
        if not j["answer_text"].strip():
            fail("empty answer_text in jsonl", book, r)
        w = wi.get(r)
        if w and (w["topic"] != b["unit"] or w["marks"] != j["marks"]):
            fail("work item differs", book, r, (w["topic"], w["marks"]))
    # numbering and order on both sides
    for u in UNITS[book]:
        q = [i for i in sorted(Q, key=lambda i: (i["page"], i["y"])) if i["unit"] == u]
        a = [i for i in sorted(A, key=lambda i: (i["page"], i["y"])) if i["unit"] == u]
        if [i["n"] for i in q] != list(range(1, len(q) + 1)):
            fail("question numbering not 1..n", book, f"unit {u}")
        if [(i["n"], i["ref"]) for i in q] != [(i["n"], i["ref"]) for i in a]:
            fail("answers differ from questions in number/order", book, f"unit {u}", (len(q), len(a)))
    # topics.json
    tix = Counter()
    for t in tp:
        if t.get("item"):
            tix[t["item"]] += t["marks"]
            if t["item"] not in bq:
                fail("topics.json item not in book", book, t["item"])
            elif t["filed_unit"] != bq[t["item"]]["unit"]:
                fail("topics.json filed_unit", book, t["item"], (t["filed_unit"], bq[t["item"]]["unit"]))
    for r in bq:
        if r not in tix:
            fail("item without parts in topics.json", book, r)
        elif r in jx and tix[r] != jx[r]["marks"]:
            fail("topics.json part marks != item marks", book, r, (tix[r], jx[r]["marks"]))
    for r in set(jx) & set(bq):
        los = {t["lo"] for t in tp if t.get("item") == r and t.get("lo")}
        if los != set(jx[r]["learning_outcomes"]):
            fail("jsonl learning_outcomes != topics.json parts", book, r, (sorted(los), jx[r]["learning_outcomes"]))
        by = Counter()
        for t in tp:
            if t.get("item") == r:
                by[t["unit"]] += t["marks"]
        exp_also = {str(k): v for k, v in by.items() if k != bq[r]["unit"]}
        if exp_also != {str(k): v for k, v in jx[r]["also_units"].items()}:
            fail("also_units != marks by unit in topics.json", book, r, (exp_also, jx[r]["also_units"]))
        if by and max(by.values()) > by.get(bq[r]["unit"], 0):
            fail("item filed under a unit that is not its majority unit", book, r, dict(by))
    # unit PDFs: same items in the same order, printed page numbers = book page numbers
    upages = 0
    for fn, u in sorted(bp["units"].items()):
        un = int(re.search(r"Unit-(\d+)", fn).group(1))
        qb = [i for i in sorted(bp["items"], key=lambda i: (i["page"], i["y"])) if i["unit"] == un]
        a = [(i["n"], i["ref"], i["side"]) for i in sorted(u["items"], key=lambda i: (i["page"], i["y"]))]
        if a != [(i["n"], i["ref"], i["side"]) for i in qb]:
            fail("unit PDF items/order differ from the book", book, fn, (len(a), len(qb)))
        rng = [p["i"] for p in bp["pages"] if p["unit"] == un]
        if u["n"] != len(rng):
            fail("unit PDF page count != unit pages in the book", book, fn, (u["n"], len(rng)))
        upages += u["n"]
        for k, pg in enumerate(u["pages"]):
            bpg = bp["pages"][rng[0] - 1 + k] if rng and rng[0] - 1 + k < len(bp["pages"]) else None
            if bpg is None or pg["header"] != bpg["header"] or pg["nwords"] != bpg["nwords"]:
                fail("unit PDF page differs from the book page", book, fn, (k + 1, pg["header"][:1]))
                break
    if sorted(bp["units"]) != sorted(f for f in bp["units"]) or len(bp["units"]) != len(UNITS[book]):
        fail("number of unit PDFs", book, None, len(bp["units"]))
    tot[f"P{book} unit PDF pages"] = upages
for r, c in allrefs.items():
    if c > 1:
        fail("item in both books", 0, r)
miss = set(wi) - set(allrefs)
for r in miss:
    fail("work item in neither book", 0, r)
jd(F, "threeway_fail.json", 0)
print(dict(tot))
print("three-way failures:", len(F), dict(Counter(f["kind"] for f in F)))
for x in F[:20]:
    print("  ", x)

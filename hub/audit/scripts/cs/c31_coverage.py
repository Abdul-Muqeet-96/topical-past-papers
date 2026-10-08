"""Check 3 COVERAGE + marks. Every lowest-level part of every verified paper (independent QP parse)
must be in exactly one item of exactly one book, or be listed in report.md as excluded (question
failing check 3, out of syllabus, pre-release, item exclusion). Also, for every item:
index marks = sum of its parts' [marks] in the QP (audit parser) = MS marks (audit parser)."""
import csv, json, re
from collections import Counter, defaultdict
from c00_common import *

QP, MS = jl("qp_parse.json"), jl("ms_parse.json")
CMPJ = jl("compare.json")
rep = open(os.path.join(CS, "reports", "report.md")).read()


def section(title):
    m = re.search(r"^## " + re.escape(title) + r".*?\n(.*?)(?=^## |\Z)", rep, re.S | re.M)
    return m.group(1) if m else ""


def rows(title):
    return [[c.strip() for c in l.strip().strip("|").split("|")] for l in section(title).split("\n")
            if l.startswith("|") and not l.startswith("|---") and not l.startswith("| Item") and not l.startswith("| Paper")]


def leaves_of(pid_):
    q = QP[pid_]
    marks = {int(a): dict(b) for a, b in q["parts"].items()}
    g = sum(sum(x.values()) for x in marks.values())
    if g != q["cover"]:
        for qq, x in q["inner"].items():
            for key, v, pg, y, x1 in x:
                marks[int(qq)][key] = marks[int(qq)].get(key, 0) + v
    return marks


LEAF = {k: leaves_of(k) for k in QP if k in MS}
idx = []
for b in (1, 2):
    for r in csv.DictReader(open(os.path.join(BOOKDIR[b], "index.csv"))):
        r["book"] = b
        idx.append(r)
cover = defaultdict(list)
bad_ref, item_marks = [], []
for r in idx:
    try:
        pid_, q, suf = ref_key(r["reference"])
    except Exception:
        bad_ref.append(r["reference"])
        continue
    if pid_ not in LEAF or q not in LEAF[pid_]:
        bad_ref.append(r["reference"])
        continue
    lv = expand(q, suf, list(LEAF[pid_][q]))
    if not lv:
        bad_ref.append(r["reference"])
    for l in lv:
        cover[(pid_, l)].append(r["reference"])
    qm = sum(LEAF[pid_][q][l] for l in lv)
    if qm != int(r["marks"]):
        item_marks.append({"ref": r["reference"], "index": int(r["marks"]), "qp_audit": qm, "leaves": lv})


def explained_sets():
    exq, oos, pre, exi = set(), [], [], []
    for c in rows("Paper-level verification failures"):
        m = re.match(r"(?:9608 )?(M/J|O/N|MAR) (\d\d)/P(\d\d)", c[0])
        if m and re.fullmatch(r"Q\d+", c[1]):
            # the report writes the paper reference; 2021 9608 papers carry the code
            exq.add((c[0], int(c[1][1:])))
    for c in rows("Out of syllabus"):
        oos.append(c[0])
    for c in rows("Parts that need pre-release material"):
        if c[0] != "(none)":
            pre.append(c[0])
    for c in rows("Item exclusions"):
        if c[0] != "(none)":
            exi.append(c[0])
    return exq, oos, pre, exi


exq, oos, pre, exi = explained_sets()


def paper_ref_of(pid_):
    code, sy, v = pid_.split("_")
    base = {"s": "M/J", "w": "O/N", "m": "MAR"}[sy[0]] + f" {sy[1:]}/P{v}"
    twin = f"9618_{sy}_{v}"
    return ("9608 " + base) if code == "9608" and twin in QP and twin in MS else base


def covered_by(lst, pid_, q, leaf):
    hits = []
    for ref in lst:
        try:
            p2, q2, suf = ref_key(ref)
        except Exception:
            continue
        if p2 == pid_ and q2 == q and leaf in expand(q, suf, list(LEAF[pid_][q])):
            hits.append(ref)
    return hits


gaps, dupes, n = [], [], 0
cls = Counter()
both = []
for pid_, qs in sorted(LEAF.items()):
    pref = paper_ref_of(pid_)
    for q, lv in sorted(qs.items()):
        for leaf in lv:
            n += 1
            c = cover.get((pid_, leaf), [])
            why = []
            if (pref, q) in exq:
                why.append("question excluded (check 3)")
            if covered_by(oos, pid_, q, leaf):
                why.append("out of syllabus")
            if covered_by(pre, pid_, q, leaf):
                why.append("pre-release")
            if covered_by(exi, pid_, q, leaf):
                why.append("item excluded")
            if len(c) == 1 and not why:
                cls["in one item"] += 1
            elif len(c) > 1:
                dupes.append({"paper": pid_, "leaf": leaf, "items": c})
            elif not c and why:
                cls[why[0]] += 1
            elif not c:
                gaps.append({"paper": pid_, "leaf": leaf, "marks": lv[leaf]})
            else:
                both.append({"paper": pid_, "leaf": leaf, "items": c, "also_listed_as": why})
# report rows that match nothing in the papers
stale = [r for r in oos + pre + exi if not any(True for _ in [0] if (lambda k: k[0] in LEAF and k[1] in LEAF[k[0]] and expand(k[1], k[2], list(LEAF[k[0]][k[1]])))(ref_key(r)))]
# item marks against the MS (audit parser), where the MS labels its rows like the QP
msm = {}
for k, m in MS.items():
    d = defaultdict(int)
    prev = None
    for r in m["rows"]:
        v = sum(x[0] for x in r["marks"])
        if m["layout"] == "text" and r.get("max"):
            mx = [x[0] for x in r["max"]]
            v = mx[0] if len(set(mx)) == 1 else sum(mx)
        if prev and prev["label"] == r["label"] and r["page"] > prev["page"] and [x[0] for x in r["marks"]] == [x[0] for x in prev["marks"]]:
            v = 0
        d[r["label"]] += v
        prev = r
    msm[k] = d
ms_item = []
known = {(x["paper"], x["leaf"]) for x in CMPJ["leaf_mismatch"]}
for r in idx:
    if r["reference"] in bad_ref:
        continue
    pid_, q, suf = ref_key(r["reference"])
    lv = expand(q, suf, list(LEAF[pid_][q]))
    tot = 0
    for l in lv:
        v = msm[pid_].get(l)
        if v is None:
            v = sum(b for a, b in msm[pid_].items() if a.startswith(l + "("))
        tot += v
    if tot != int(r["marks"]) and not any((pid_, l) in known for l in lv):
        ms_item.append({"ref": r["reference"], "index": int(r["marks"]), "ms_audit": tot})
out = {"leaves": n, "classes": dict(cls), "gaps": gaps, "dupes": dupes, "listed_and_included": both, "bad_refs": bad_ref,
       "item_marks_vs_qp": item_marks, "item_marks_vs_ms": ms_item, "stale_report_rows": stale,
       "report_counts": {"excluded_questions": len(exq), "out_of_syllabus_rows": len(oos), "pre_release_rows": len(pre),
                         "item_exclusion_rows": len(exi)}}
jd(out, "coverage.json", 1)
print("leaves in verified papers:", n, dict(cls))
print("unexplained gaps:", len(gaps), "| in more than one item:", len(dupes), "| listed as excluded but in a book:", len(both),
      "| index refs that match no paper part:", len(bad_ref), "| report rows that match no part:", len(stale))
print("items:", len(idx), "| item marks != QP parts (audit):", len(item_marks), "| item marks != MS (audit; known label slips left out):", len(ms_item))
for x in (gaps[:12] + dupes[:6] + both[:6] + item_marks[:6] + ms_item[:8]):
    print("  ", x)
print("  bad refs", bad_ref[:8], "stale", stale[:8])

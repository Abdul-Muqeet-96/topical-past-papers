"""Check 8 TOPICS. Compares the blind re-tag (hub/audit/out/cs/blind/tags.txt: item number, unit, and
where the item legitimately spans two units a second acceptable unit) with the unit each item is
filed under. Every disagreement is written out with the item's parts and their learning outcomes,
to be resolved by reading (hub/audit/out/cs/blind/resolved.txt holds the verdicts)."""
import json, re, sys
from collections import Counter, defaultdict
from c00_common import *

key = jl("blind/key.json")
tags = {}
for l in open(os.path.join(OUT, "blind", "tags.txt")):
    if l.startswith("#") or not l.strip():
        continue
    p = l.split()
    tags[int(p[0])] = [int(x) for x in p[1:]]
miss = [n for n in map(int, key) if n not in tags]
extra = [n for n in tags if str(n) not in key]
tp = {}
for b in (1, 2):
    for t in json.load(open(os.path.join(BOOKDIR[b], "topics.json"))):
        if t.get("item"):
            tp.setdefault(t["item"], []).append(t)
res = {}
rp = os.path.join(OUT, "blind", "resolved.txt")
if os.path.exists(rp):
    for l in open(rp):
        m = re.match(r"(\d+)\s+(KEEP|CHANGE)\s*(.*)", l)
        if m:
            res[int(m.group(1))] = (m.group(2), m.group(3).strip())
# where each part is filed NOW (index.csv of the books as they are): the blind tags were given to
# the items as they stood when the dump was made; an item regrouped since is followed by its parts
import csv
now, leaves_of = {}, {}
for b in (1, 2):
    for r in csv.DictReader(open(os.path.join(BOOKDIR[b], "index.csv"))):
        also = [int(x.split(":")[0]) for x in r["also_topics"].split(";") if x.strip()]
        now[r["reference"]] = (b, int(r["unit"]), also)
        pid_, q_, suf_ = ref_key(r["reference"])
        leaves_of[r["reference"]] = (pid_, q_, suf_)


def current(ref):
    """(reference, book, unit, also-units) of the item that holds this reference's parts today"""
    if ref in now:
        return (ref,) + now[ref]
    pid_, q_, suf_ = ref_key(ref)
    first = re.match(r"/?([a-h])", suf_ or "")
    for r2, (p2, q2, s2) in leaves_of.items():
        if p2 == pid_ and q2 == q_ and (not first or re.search(r"(^|[/,])" + first.group(1) + r"(\(|,|$)", s2 or "")):
            return (r2,) + now[r2]
    return None


agree = alt = moved = gone = 0
dis = []
conf = Counter()
regrouped = []
for n, k in sorted(((int(a), b) for a, b in key.items())):
    if n not in tags:
        continue
    t = tags[n]
    cur = current(k["ref"])
    if cur is None:
        gone += 1
        dis.append({"n": n, "ref": k["ref"], "book": k["book"], "filed": None, "blind": t, "parts": [], "verdict": None})
        continue
    if cur[0] != k["ref"]:
        regrouped.append((k["ref"], cur[0]))
    unit_now, also_now = cur[2], cur[3]
    k = dict(k, unit=unit_now)
    if t[0] == unit_now:
        agree += 1
    elif unit_now in t[1:]:
        alt += 1
    elif cur[0] != k["ref"] and t[0] in also_now:
        moved += 1          # its parts are now inside an item that names the blind unit in its "also" note
    else:
        conf[(k["unit"], t[0])] += 1
        dis.append({"n": n, "ref": k["ref"], "book": k["book"], "filed": k["unit"], "blind": t,
                    "parts": [(x["part"], x["lo"], x["marks"]) for x in tp.get(k["ref"], [])],
                    "verdict": res.get(n)})
jd(dis, "blind/disagreements.json", 1)
print("items", len(key), "| blind-tagged", len(tags), "| not tagged", miss[:10], "| unknown numbers", extra[:10])
print("items in the books now:", len(now), "| regrouped since the blind pass:", regrouped, "| of these, blind unit named in the item's also-note:", moved)
print("same unit:", agree, "| filed unit is the second acceptable unit:", alt, "| disagreements:", len(dis),
      "| resolved by reading:", sum(1 for d in dis if d["verdict"]), "| unresolved:", sum(1 for d in dis if not d["verdict"]))
print("verdicts:", dict(Counter(d["verdict"][0] for d in dis if d["verdict"])))
print("filed -> blind:", sorted(conf.items(), key=lambda kv: -kv[1])[:30])

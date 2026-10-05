"""Check 8 TOPICS. Compares the blind re-tag (audit/out/cs/blind/tags.txt: item number, unit, and
where the item legitimately spans two units a second acceptable unit) with the unit each item is
filed under. Every disagreement is written out with the item's parts and their learning outcomes,
to be resolved by reading (audit/out/cs/blind/resolved.txt holds the verdicts)."""
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
agree = alt = 0
dis = []
conf = Counter()
for n, k in sorted(((int(a), b) for a, b in key.items())):
    if n not in tags:
        continue
    t = tags[n]
    if t[0] == k["unit"]:
        agree += 1
    elif k["unit"] in t[1:]:
        alt += 1
    else:
        conf[(k["unit"], t[0])] += 1
        dis.append({"n": n, "ref": k["ref"], "book": k["book"], "filed": k["unit"], "blind": t,
                    "parts": [(x["part"], x["lo"], x["marks"]) for x in tp.get(k["ref"], [])],
                    "verdict": res.get(n)})
jd(dis, "blind/disagreements.json", 1)
print("items", len(key), "| blind-tagged", len(tags), "| not tagged", miss[:10], "| unknown numbers", extra[:10])
print("same unit:", agree, "| filed unit is the second acceptable unit:", alt, "| disagreements:", len(dis),
      "| resolved by reading:", sum(1 for d in dis if d["verdict"]), "| unresolved:", sum(1 for d in dis if not d["verdict"]))
print("verdicts:", dict(Counter(d["verdict"][0] for d in dis if d["verdict"])))
print("filed -> blind:", sorted(conf.items(), key=lambda kv: -kv[1])[:30])

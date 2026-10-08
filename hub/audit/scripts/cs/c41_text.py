"""Check 4b TEXT LAYER: the text of every item must be readable in the book itself and agree with
items.jsonl (the copy that a program reads). For each item, the words of the jsonl "text" (plus "insert_text", the insert pages printed with the item) are
compared with the words that the book's own text layer gives for the item's question crops, and
"answer_text" with the item's Answers crops. Reported: items where less than 97 % of the words of
one side are found on the other (multiset of word tokens; part labels and marks are left out,
because the jsonl text does not repeat the labels)."""
import json, re
from collections import Counter
from c00_common import *

TOK = re.compile(r"[A-Za-z0-9_]+|[^\sA-Za-z0-9_.…]")


LABEL = re.compile(r"[()\[\]]|[a-h]|[ivx]{1,4}|\d{1,2}|J")     # part labels, marks; "J": the foot of "M/J" in the heading above a crop


# the book's own grey note lines under a heading or above inline reference pages
NOTE = re.compile(r"^(also [^\n]*this unit[^\n]*|Uses the insert.*|Insert of this paper:.*|Appendix of this paper:.*)$", re.M)


def toks(t):
    t = re.sub(r"[.…]{3,}", " ", t)
    return Counter(x for x in TOK.findall(t) if not LABEL.fullmatch(x))


def cover(a, b):
    """share of the tokens of a that are found in b"""
    n = sum(a.values())
    return 1.0 if not n else sum(min(v, b.get(k, 0)) for k, v in a.items()) / n


res, stats = [], Counter()
for book in (1, 2):
    bp = jl(f"book_parse_p{book}.json")
    js = {}
    for line in open(os.path.join(BOOKDIR[book], "items.jsonl")):
        j = json.loads(line)
        js[j["reference"]] = j
    side = {"Q": {}, "A": {}}
    for it in bp["items"]:
        side[it["side"]][it["ref"]] = it
    for ref, j in js.items():
        for sd, key in (("Q", "text"), ("A", "answer_text")):
            it = side[sd].get(ref)
            if it is None:
                res.append({"book": book, "ref": ref, "side": sd, "what": "item not in the book"})
                continue
            a, b = toks(j[key] + (" " + (j.get("insert_text") or "") if sd == "Q" else "")), toks(NOTE.sub(" ", it["text"]))
            ca, cb = cover(a, b), cover(b, a)
            stats[f"{sd} items"] += 1
            stats[f"{sd} tokens (jsonl)"] += sum(a.values())
            if ca < 0.97 or cb < 0.97:
                miss_a = list((a - b).elements())[:12]
                miss_b = list((b - a).elements())[:12]
                res.append({"book": book, "ref": ref, "side": sd, "jsonl_in_book": round(ca, 3), "book_in_jsonl": round(cb, 3),
                            "only_jsonl": miss_a, "only_book": miss_b})
jd(res, "text_layer.json", 0)
print(dict(stats))
print("items whose book text and jsonl text differ by more than 3 %:", len(res), dict(Counter((r["book"], r["side"]) for r in res)))

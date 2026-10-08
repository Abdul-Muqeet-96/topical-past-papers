"""Checks 4/9 (input): parse the two final books and every unit PDF, with no help from the build's
own records. Per page: running header, printed page number, kind (cover / contents / unit title /
question / answers / index / appendix). Per item: heading 'n. REF' on the question side and on the
answers side with page and y, the grey notes under it, and its text (to the next heading).
Also every placed crop band (Form XObject wrapping a source page; BBox = the clip)."""
import glob, re, sys
from collections import Counter, defaultdict
import pymupdf as f
from c00_common import *

NAME = {1: "Computer Science 9618 Paper 1 Topical Workbook", 2: "Computer Science 9618 Paper 2 Topical Workbook"}


def parse(path, book):
    d = f.open(path)
    pages, items, bands = [], [], []
    unit = None
    side = None
    kind = None
    for i, p in enumerate(d):
        L = lines(p)
        txt = p.get_text()
        head = [" ".join(w[4] for w in l["w"]) for l in L if l["c"] < 50]
        pg = {"i": i + 1, "header": head, "label": p.get_label(), "w": round(p.rect.width, 1), "h": round(p.rect.height, 1)}
        first = txt.strip().split("\n")[0] if txt.strip() else ""
        m = re.match(r"\s*Unit (\d+)\n", txt)
        if i == 0 and "Part-level Topical Workbook" in txt:
            kind = "cover"
        elif first == "Contents" or (kind == "contents" and not head and not (m and "items ·" in txt)):
            kind = "contents"
        elif m and "items ·" in txt and "Syllabus sections in this unit" in txt:
            kind, unit, side = "unit_title", int(m.group(1)), None
            pg["unit_title"] = unit
            mm = re.search(r"(\d+) items · (\d+) marks", txt)
            pg["title_items"], pg["title_marks"] = int(mm.group(1)), int(mm.group(2))
            pg["title_name"] = " ".join(txt.split("\n")[1:txt.split("\n").index(mm.group(0))]).strip()
            pg["title_sections"] = re.findall(r"^(\d+\.\d+)\s+(.+)$", txt, re.M)
        else:
            h = " | ".join(head)
            if "Topic index" in h:
                kind, side = "index", None
            elif "Appendix: Insert" in h:
                kind, side = "appendix", None
            elif re.search(r"Unit \d+: Answers Section", h):
                kind, side = "answers", "A"
            elif re.search(r"Unit \d+: ", h):
                kind, side = "question", "Q"
            else:
                kind = "unknown"
        pg["kind"] = kind
        pg["unit"] = unit if kind in ("unit_title", "question", "answers") else None
        # banner lines (white text on dark): found by their wording
        pg["banner"] = [t for t in (" ".join(w[4] for w in l["w"]) for l in L if 50 <= l["c"] < 110)
                        if re.fullmatch(r"(Unit \d+: .+|Answers Section|Topic index: where each part was filed|Appendix: .+)", t)][:1]
        pg["nwords"] = len(txt.split())
        pages.append(pg)
        if kind in ("question", "answers"):
            for k, l in enumerate(L):
                t = " ".join(w[4] for w in l["w"])
                mm = RE_REF.match(t)
                if mm and l["w"][0][0] < 46 and l["c"] > 50:
                    notes = []
                    for l2 in L[k + 1:k + 4]:
                        t2 = " ".join(w[4] for w in l2["w"])
                        if l2["c"] - l["c"] < 34 and l2["w"][0][0] < 46 and (
                                t2.startswith("also Unit") or t2.startswith("Uses the insert")):
                            notes.append(t2)
                    items.append({"n": int(mm.group(1)), "ref": mm.group(2), "page": i + 1, "y": round(l["c"], 1),
                                  "unit": unit, "side": side, "notes": notes})
        if kind in ("question", "answers", "appendix"):
            Hh = p.rect.height
            for xref, name, inv, bbox in p.get_xobjects():
                if inv:
                    continue
                obj = d.xref_object(xref)
                if "/fullpage" not in obj:
                    continue
                m = re.search(r"/BBox \[ ([\d.\-]+) ([\d.\-]+) ([\d.\-]+) ([\d.\-]+) \]", obj)
                clip = [float(x) for x in m.groups()]
                fp = int(re.search(r"/fullpage (\d+) 0 R", obj).group(1))
                tr = [bbox[0], Hh - bbox[3], bbox[2], Hh - bbox[1]]
                bands.append({"page": i + 1, "target": [round(x, 2) for x in tr], "clip": clip, "fp": fp,
                              "text": p.get_text(clip=f.Rect(tr) + (-1, -1, 1, 1))})
    return {"pages": pages, "items": items, "bands": bands, "toc": d.get_toc(), "meta": d.metadata, "n": len(d)}


def item_texts(path, o):
    """Text of each item on each side: everything between its heading and the next heading (or the
    end of the side), running headers left out; also the note lines printed between crops."""
    d = f.open(path)
    seq = sorted(o["items"], key=lambda i: (i["page"], i["y"]))
    for k, it in enumerate(seq):
        nxt = seq[k + 1] if k + 1 < len(seq) and seq[k + 1]["side"] == it["side"] and seq[k + 1]["unit"] == it["unit"] else None
        out = []
        pg = it["page"]
        while pg <= len(d) and o["pages"][pg - 1]["kind"] == ("question" if it["side"] == "Q" else "answers") \
                and o["pages"][pg - 1]["unit"] == it["unit"]:
            y0 = it["y"] + 8 if pg == it["page"] else 50
            y1 = nxt["y"] - 6 if nxt and nxt["page"] == pg else 842
            if y1 > y0:
                out.append(d[pg - 1].get_text(clip=f.Rect(0, y0, 596, y1)))
            if nxt is not None and nxt["page"] == pg:
                break
            if pg + 1 > len(d) or o["pages"][pg]["kind"] != o["pages"][pg - 1]["kind"] or o["pages"][pg]["unit"] != it["unit"]:
                break                     # the last item of a side runs to the end of that side
            pg += 1
        it["end_page"] = pg if pg <= len(d) else len(d)
        it["text"] = "\n".join(out)
    return seq


if __name__ == "__main__":
    for book in (1, 2):
        o = parse(BOOKS[book], book)
        o["items"] = item_texts(BOOKS[book], o)
        seq = o["items"]
        import bisect
        keys = [(i["page"], i["y"]) for i in seq]
        for b in o["bands"]:
            k = bisect.bisect_right(keys, (b["page"], (b["target"][1] + b["target"][3]) / 2)) - 1
            kind = o["pages"][b["page"] - 1]["kind"]
            b["ref"], b["side"] = (seq[k]["ref"], seq[k]["side"]) if k >= 0 and kind != "appendix" else (None, "X")
        units = {}
        for fn in sorted(glob.glob(os.path.join(BOOKDIR[book], "units", "*.pdf"))):
            u = parse(fn, book)
            u.pop("bands")
            units[os.path.basename(fn)] = u
        o["units"] = units
        jd(o, f"book_parse_p{book}.json")
        c = Counter(p["kind"] for p in o["pages"])
        print(f"P{book}: {o['n']} pages {dict(c)}; headings Q {sum(i['side'] == 'Q' for i in seq)} A {sum(i['side'] == 'A' for i in seq)};"
              f" bands {len(o['bands'])}; unit PDFs {len(units)}; toc {len(o['toc'])}")

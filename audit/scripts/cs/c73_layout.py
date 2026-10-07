"""Check 6h PAGE LAYOUT of both books, from the placed bands and headings:
 a. bands outside the page margins or overlapping each other / a heading;
 b. a heading left alone at the foot of a page (its first crop starts on the next page);
 c. figures split across pages: a block of code (consecutive monospace lines), a table or a drawing
    whose source ink runs across the break between the last band of one book page and the first
    band of the next;
 d. nearly empty body pages and large unused space before an item that would have fitted;
 e. bands scaled up (never allowed) or scaled differently inside one item side."""
import re, sys
from collections import Counter, defaultdict
import pymupdf as f
from c00_common import *

ML, MR, MT, MB, W, H = 40, 40, 58, 40, 595.28, 841.89
res = {k: [] for k in ("margin", "overlap", "orphan_heading", "orphan_mark", "orphan_intro", "orphan_caption", "orphan_lead", "split_figure", "empty_page", "wasted_space", "wasted_by_design", "scale")}
stats = Counter()
cache = {}


def spage(fn, i):
    if fn not in cache:
        cache[fn] = f.open(os.path.join(DATA, fn))
    return cache[fn][i]


mc, dc = {}, {}


def mono_lines(fn, i):
    """y-ranges of source lines that are mostly monospace text."""
    if (fn, i) not in mc:
        p = spage(fn, i)
        out = []
        for b in p.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                n = sum(len(s["text"].strip()) for s in l["spans"])
                m = sum(len(s["text"].strip()) for s in l["spans"] if re.search(r"Courier|Mono", s["font"], re.I))
                txt = "".join(s["text"] for s in l["spans"]).strip()
                # one monospace word closing a sentence ("... returned the value TRUE.") is not code
                if n >= 3 and m / n > 0.6 and not re.fullmatch(r"[\w\"'()]+[.,]", txt):
                    out.append((l["bbox"][1], l["bbox"][3]))
        mc[(fn, i)] = sorted(out)
    return mc[(fn, i)]


def drawings(fn, i):
    if (fn, i) not in dc:
        p = spage(fn, i)
        out = []
        for g in p.get_drawings():
            r = f.Rect(g["rect"]) * p.rotation_matrix
            r.normalize()
            fill = g.get("fill")
            if fill is not None and min(fill) > 0.97 and g.get("color") is None:
                continue
            if fill is not None and g.get("color") is None and (g.get("fill_opacity") or 1) < 0.2:
                continue                  # tile of the download site's watermark
            if r.width > p.rect.width * 0.9 and r.height > p.rect.height * 0.5:
                continue
            out.append(r)
        dc[(fn, i)] = out
    return dc[(fn, i)]


for book in (1, 2):
    o = jl(f"bands_p{book}.json")
    bp = jl(f"book_parse_p{book}.json")
    byp = defaultdict(list)
    for b in o["bands"]:
        byp[b["page"]].append(b)
    heads = defaultdict(list)
    for it in bp["items"]:
        heads[it["page"]].append(it)
    kinds = {p["i"]: p["kind"] for p in bp["pages"]}
    units = {p["i"]: p["unit"] for p in bp["pages"]}
    for pg in sorted(kinds):
        if kinds[pg] not in ("question", "answers", "appendix"):
            continue
        bs = sorted(byp.get(pg, []), key=lambda b: b["target"][1])
        stats["body pages"] += 1
        for b in bs:
            t = b["target"]
            if t[0] < ML - 0.6 or t[2] > W - MR + 0.6 or t[1] < MT - 0.6 or t[3] > H - MB + 0.6:
                res["margin"].append({"book": book, "page": pg, "ref": b["ref"], "target": t})
            sc = (t[2] - t[0]) / (b["clip"][2] - b["clip"][0])
            if sc > 1.002:
                res["scale"].append({"book": book, "page": pg, "ref": b["ref"], "scale": round(sc, 3)})
        for a, b in zip(bs, bs[1:]):
            if b["target"][1] < a["target"][3] - 0.8 and min(a["target"][2], b["target"][2]) > max(a["target"][0], b["target"][0]):
                res["overlap"].append({"book": book, "page": pg, "ref": b["ref"], "a": a["target"], "b": b["target"]})
        for it in heads.get(pg, []):
            for b in bs:
                if b["target"][1] < it["y"] + 4 < b["target"][3] - 1:
                    res["overlap"].append({"book": book, "page": pg, "ref": it["ref"], "heading_y": it["y"], "b": b["target"]})
            below = [b for b in bs if b["target"][1] > it["y"] - 2]
            nxt_head = [h for h in heads[pg] if h["y"] > it["y"] + 1]
            first = min((b["target"][1] for b in below), default=None)
            if first is None or (nxt_head and first > min(h["y"] for h in nxt_head)):
                res["orphan_heading"].append({"book": book, "page": pg, "ref": it["ref"], "side": it["side"], "y": it["y"]})
        # fill of the page
        bottom = max([b["target"][3] for b in bs] + [h["y"] + 8 for h in heads.get(pg, [])] + [MT])
        last_of_side = kinds.get(pg + 1) != kinds[pg] or units.get(pg + 1) != units[pg]
        if not bs and not heads.get(pg):
            res["empty_page"].append({"book": book, "page": pg})
        elif not last_of_side and H - MB - bottom > 0.45 * (H - MB - MT):
            # what starts the next page: a new item (moved whole) or the continuation of this one?
            nb = sorted(byp.get(pg + 1, []), key=lambda b: b["target"][1])
            nh = sorted(heads.get(pg + 1, []), key=lambda h: h["y"])
            new_item = bool(nh) and (not nb or nh[0]["y"] < nb[0]["target"][1])
            first_h = (nb[0]["target"][3] - nb[0]["target"][1]) if nb else 0
            # height of what starts the next page and stays together there: its bands down to the
            # first wider gap (a figure with its label line and mark is placed with gaps of 8 pt or less)
            blk = 0.0
            for k, x in enumerate(nb):
                if k and x["target"][1] - nb[k - 1]["target"][3] > 8.6:
                    break
                blk = x["target"][3] - nb[0]["target"][1]
            free = H - MB - bottom
            cause = "next item kept whole or its start kept together" if new_item else \
                ("figure or block kept together" if blk > free - 12 else "other")
            stats["unused space: " + cause] += 1
            res["wasted_space" if cause == "other" else "wasted_by_design"].append(
                {"book": book, "page": pg, "free_pt": round(free), "next_starts_new_item": new_item, "next_block_h": round(blk),
                 "next_first_band_h": round(first_h), "cause": cause, "ref": (nh[0]["ref"] if new_item else (bs[-1]["ref"] if bs else None))})
        # figures split at the page break: last band of this page / first band of the next, same item side
        nb = sorted(byp.get(pg + 1, []), key=lambda b: b["target"][1])
        if bs and nb:
            a, b = bs[-1], nb[0]
            if a["ref"] == b["ref"] and a["side"] == b["side"] and a["src"] and b["src"] and a["src"] == b["src"] and a["side"] != "A":
                fn, pi = a["src"]
                ya, yb = a["vclip"][3], b["vclip"][1]
                if 0 <= yb - ya < 40:
                    stats["page breaks inside a source page"] += 1
                    ml = mono_lines(fn, pi)
                    ca = [m for m in ml if m[0] >= a["vclip"][1] - 1 and m[1] <= ya + 2]
                    cb = [m for m in ml if m[0] >= yb - 2 and m[1] <= b["vclip"][3] + 1]
                    code = bool(ca and cb and ca[-1][1] > ya - 16 and cb[0][0] < yb + 16 and cb[0][0] - ca[-1][1] < 20)
                    dr = drawings(fn, pi)
                    cross = [r for r in dr if r.y0 < ya - 3 and r.y1 > yb + 3 and r.x1 > a["vclip"][0] and r.x0 < a["vclip"][2]]
                    # a rule or a box edge at the break: two rows or two boxes, one under the other
                    edge = any(r.width > 100 and (ya - 4 <= r.y0 <= yb + 4 or ya - 4 <= r.y1 <= yb + 4) for r in dr)
                    if edge:
                        code = False
                        # between rows a table may break only when it is a reference page (insert or
                        # appendix, longer than a page as a whole) or taller than a page itself
                        tall = max([r.height for r in cross] + [0])
                        ref_page = "_in_" in fn or bool(re.search(r"Appendix|Built-in functions|An error will be generated", spage(fn, pi).get_text()[:400]))
                        cross = [] if (ref_page or tall > 640 or tall < 3) else [r for r in cross if r.width > 2.5 or r.height == tall]
                        if ref_page:
                            stats["breaks between rows of a reference page"] += 1
                    if code or cross:
                        res["split_figure"].append({"book": book, "page": pg, "ref": a["ref"], "src": fn, "srcpage": pi + 1, "y": round(ya),
                                                    "why": ("code block" if code else "") + (" drawing/table crosses the break" if cross else ""),
                                                    "fig_h": round(max([r.height for r in cross] + [0]))})
            # a line that ends with a colon at the foot of a page, cut off from what it introduces
            # (unless what follows fills a page of its own)
            same_pg = a["src"] and a["src"] == b["src"] and 0 <= b["vclip"][1] - a["vclip"][3] <= 60
            next_pg = a["src"] and b["src"] and a["src"][0] == b["src"][0] and b["src"][1] == a["src"][1] + 1
            if a["ref"] == b["ref"] and a["side"] == b["side"] == "Q" and (same_pg or next_pg) \
                    and (a["text"] or "").strip().endswith(":"):
                blk2 = 0.0
                for k, x in enumerate(nb):
                    if k and x["target"][1] - nb[k - 1]["target"][3] > 8.6:
                        break
                    blk2 = x["target"][3] - nb[0]["target"][1]
                if blk2 + (a["target"][3] - a["target"][1]) + 8 <= H - MB - MT - 20:
                    res["orphan_intro"].append({"book": book, "page": pg, "ref": a["ref"], "line": (a["text"] or "").strip()[-60:], "next_block_h": round(blk2)})
                else:
                    stats["colon line before a block that fills a page"] += 1
            # a caption or title (one to three words on a short line) at the foot of a page, cut off
            # from what is printed directly under it in the paper
            words_a = (a["text"] or "").split()
            if a["ref"] == b["ref"] and a["side"] == b["side"] == "Q" and a["src"] and a["src"] == b["src"] \
                    and 1 <= len(words_a) <= 3 and a["vclip"][3] - a["vclip"][1] < 18 \
                    and 0 <= b["vclip"][1] - a["vclip"][3] <= 14 and not re.fullmatch(r"\[\d{1,2}\]", " ".join(words_a)) \
                    and re.search(r"[A-Za-z]{3}", " ".join(words_a)) and not re.fullmatch(r"\(?[a-z]\)|\([ivx]+\)|\d{1,2}", words_a[0]):
                res["orphan_caption"].append({"book": book, "page": pg, "ref": a["ref"], "line": " ".join(words_a)[:40]})
            # a short instruction (up to 45 pt of text) at the foot of a page, cut off from the table,
            # diagram or listing printed directly under it (or under one or two more short lines),
            # although all of it would fit on one page
            if a["ref"] == b["ref"] and a["side"] == b["side"] == "Q" and a["src"] and a["src"] == b["src"] \
                    and a["vclip"][3] - a["vclip"][1] < 45 and 0 <= b["vclip"][1] - a["vclip"][3] <= 60 \
                    and not re.fullmatch(r"\s*\[\d{1,2}\]\s*", a["text"] or "") and re.search(r"[A-Za-z]{3}", a["text"] or ""):
                fn, pi = b["src"]

                def figure_like(x):
                    y0_, y1_ = x["vclip"][1], x["vclip"][3]
                    fig = [r for r in drawings(fn, pi) if r.y0 >= y0_ - 3 and r.y1 <= y1_ + 3 and (r.width > 100 or r.height > 30)]
                    code_n = [m for m in mono_lines(fn, pi) if m[0] >= y0_ - 2 and m[1] <= y1_ + 2]
                    return (bool(fig) or len(code_n) >= 3) and x["target"][3] - x["target"][1] > 40
                k = 0                                   # the figure: the first band of the next page, or after 1-2 short lines
                while k < 2 and k + 1 < len(nb) and not figure_like(nb[k]) and nb[k]["target"][3] - nb[k]["target"][1] < 45 \
                        and nb[k + 1]["src"] == b["src"] and 0 <= nb[k + 1]["vclip"][1] - nb[k]["vclip"][3] <= 14:
                    k += 1
                if (k == 0 or b["vclip"][1] - a["vclip"][3] <= 14) and figure_like(nb[k]):
                    need = nb[k]["target"][3] - nb[0]["target"][1] + (a["target"][3] - a["target"][1]) + 10
                    if need <= H - MB - MT - 20:
                        res["orphan_lead"].append({"book": book, "page": pg, "ref": a["ref"], "line": " ".join((a["text"] or "").split())[-70:],
                                                   "lines_between": k, "figure_h": round(nb[k]["target"][3] - nb[k]["target"][1])})
            # a mark alone at the top of a page, cut off from the line it closes
            if a["ref"] == b["ref"] and a["side"] == b["side"] == "Q" and re.fullmatch(r"\s*\[\d{1,2}\]\s*", b["text"] or ""):
                res["orphan_mark"].append({"book": book, "page": pg + 1, "ref": b["ref"], "mark": b["text"].strip()})
for k, v in res.items():
    jd(v, f"layout_{k}.json", 0)
print(dict(stats))
for k, v in res.items():
    print(f"{k}: {len(v)}", dict(Counter(x["book"] for x in v)))

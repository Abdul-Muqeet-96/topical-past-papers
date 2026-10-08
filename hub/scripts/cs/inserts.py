"""Inserts (pseudocode functions and operators) and in-paper appendices.

λ-cs/reference/CLAUDE-cs.md, Sources: the P2 book's Appendix is the insert of the newest
paper. An item whose text refers to the insert gets a note when its own
paper's insert matches the Appendix copy in text; otherwise the relevant pages
of its own insert are shown inline. Older papers print the function list as an
"Appendix" page inside the question paper; that page is treated as the paper's
insert.

Also treated as needing the paper's own insert: an item that uses a function
its own insert defines and the Appendix copy does not (e.g. LCASE in 2021).
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from parse import load, special_page, page_lines, norm_text
from paths import DATA, MANIFEST, SERIES_ORDER, jload

RE_BOILER = re.compile(r"Permission to reproduce|To avoid the issue of disclosure|Every reasonable effort|"
                       r"Cambridge Assessment International Education is part|is a department of the University|"
                       r"Cambridge International Examinations is part|copyright holders", re.I)
RE_FUNC = re.compile(r"\b([A-Z][A-Z_]{1,}[A-Z])\s?\(")


def content_pages(doc, kind):
    """Pages that hold reference material: for an insert, every page after the
    cover that is not blank; for a question paper, its 'Appendix' pages."""
    out = []
    for p in doc:
        sp = special_page(p)
        if kind == "in":
            if p.number > 0 and sp != "blank" and len(p.get_text().strip()) > 200:
                out.append(p.number)
        elif sp == "appendix":
            out.append(p.number)
    return out


def content_region(doc, pno):
    """[page, y0, y1] of the reference material on a page: below the page
    furniture, above the footer and the small-print copyright paragraph."""
    from crops import page_top
    from extract import content_bottom
    page = doc[pno]
    top, bot = page_top(page), content_bottom(page)
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            t = "".join(s["text"] for s in l["spans"])
            if RE_BOILER.search(t) and l["bbox"][1] > page.rect.height * 0.5:
                bot = min(bot, l["bbox"][1] - 2)
    return [pno, top, bot]


def body_text(doc, pages):
    out = []
    for pno in pages:
        _, y0, y1 = content_region(doc, pno)
        for ws in page_lines(doc[pno]):
            if min(w[1] for w in ws) < y0 - 1 or max(w[3] for w in ws) > y1 + 1:
                continue
            out.append(" ".join(w[4] for w in ws))
    t = norm_text(" ".join(out))
    t = t.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').replace("−", "-")
    return re.sub(r"\s+", " ", t).strip()


def cmp_key(t):
    return re.sub(r"\s+", " ", re.sub(r"[.,:;]+(?=\s|$)", "", t)).strip()


class Inserts:
    def __init__(self):
        self.man = jload(MANIFEST)
        self.cache = {}
        cands = [(e["year"], SERIES_ORDER[e["series"]], e["variant"], pid) for pid, e in self.man.items()
                 if e["status"] == "ok" and e["paper"] == 2 and e["code"] == "9618" and e["in"]["status"] == "ok"]
        self.appendix_pid = max(cands)[3] if cands else None

    def source(self, pid):
        """-> (kind, file, pages, text, funcs) for the paper's own reference material, or None."""
        if pid in self.cache:
            return self.cache[pid]
        e = self.man[pid]
        res = None
        if e["in"]["status"] == "ok":
            d = load(os.path.join(DATA, e["in"]["file"]), redact=False)
            pages = content_pages(d, "in")
            if pages:
                res = ("in", e["in"]["file"], pages)
        if res is None:
            d = load(os.path.join(DATA, e["qp"]["file"]))
            pages = content_pages(d, "qp")
            if pages:
                res = ("qp", e["qp"]["file"], pages)
        if res is not None:
            text = body_text(d, res[2])
            per_page = {p: set(RE_FUNC.findall(body_text(d, [p]))) for p in res[2]}
            res = res + (text, per_page)
        self.cache[pid] = res
        return res

    def appendix(self):
        return self.source(self.appendix_pid) if self.appendix_pid else None

    def matches(self, pid):
        """Same text as the Appendix copy. AUTO-DECIDED: punctuation at the end of
        a word is ignored (the 2024-25 inserts differ from the 2026 one only by a
        colon after one "Example" and a full stop after "records")."""
        a, b = self.source(pid), self.appendix()
        return bool(a and b and cmp_key(a[3]) == cmp_key(b[3]))

    def for_item(self, p, uses_insert, uses_appendix, text):
        """-> (mode, pages, why): mode None / 'note' / 'inline' / 'missing'."""
        pid = p["pid"]
        src = self.source(pid)
        app = self.appendix()
        app_funcs = set().union(*app[4].values()) if app else set()
        why = []
        if uses_insert:
            why.append("text refers to the insert")
        if uses_appendix:
            why.append("text refers to the Appendix")
        legacy = set()
        if src:
            own = set().union(*src[4].values())
            for f in sorted(own - app_funcs):
                if re.search(rf"\b{re.escape(f)}\s?\(", text):
                    legacy.add(f)
        if legacy:
            why.append("uses " + ", ".join(sorted(legacy)) + " (defined in this paper's insert, not in the Appendix)")
        if not why:
            return None, [], ""
        if src is None:
            if uses_appendix and not uses_insert:
                return "missing", [], "; ".join(why) + "; no Appendix page found in the paper"
            return "missing", [], "; ".join(why) + "; no insert available for the paper"
        if self.matches(pid) and not legacy:
            return "note", [], "; ".join(why)
        # relevant pages: those defining the functions the item names; else all
        own = set().union(*src[4].values())
        named = {f for f in own if re.search(rf"\b{re.escape(f)}\s?\(", text)} | legacy
        pages = [pg for pg in src[2] if src[4][pg] & named] if named and not (uses_insert or uses_appendix) else []
        if not pages:
            pages = list(src[2])
        return "inline", [[src[0], src[1], pg] for pg in pages], "; ".join(why) + "; insert text differs from the Appendix"


if __name__ == "__main__":
    ins = Inserts()
    man = ins.man
    print("appendix:", ins.appendix_pid, "pages", ins.appendix()[2] if ins.appendix() else None)
    n = same = 0
    groups = {}
    for pid, e in sorted(man.items()):
        if e["status"] != "ok" or e["paper"] != 2:
            continue
        s = ins.source(pid)
        n += 1
        if s is None:
            groups.setdefault("none", []).append(pid)
            continue
        same += ins.matches(pid)
        groups.setdefault((s[0], len(s[3]), ins.matches(pid)), []).append(pid[5:])
    print(f"P2 papers {n}, insert text equal to the Appendix copy: {same}")
    for k, v in groups.items():
        print(" ", k, len(v), v[:12])

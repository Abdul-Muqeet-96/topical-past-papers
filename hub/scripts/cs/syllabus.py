"""Extract units, sections and learning outcomes (AS content, units 1-12) from
λ-cs/reference/cs-syllabus.pdf (text layer; nothing is typed by hand).

Writes λ-cs/build/work/syllabus.json:
  {"units": {"1": name, ...}, "sections": {"1.1": name, ...},
   "los": {"1.1.1": {"section": "1.1", "text": "...", "notes": "..."}, ...}}
Each learning outcome is one "Candidates should be able to" statement (left
column); "notes" is the "Notes and guidance" text printed beside it.
Usage: python3 hub/scripts/cs/syllabus.py [--print]
"""
import os, re, sys
import pymupdf
sys.path.insert(0, os.path.dirname(__file__))
from paths import CS, work, jdump

PDF = os.path.join(CS, "reference", "cs-syllabus.pdf")
MIDX = 300        # left column: learning outcomes; right column: notes and guidance


def page_lines(page):
    out = []
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            t = "".join(s["text"] for s in l["spans"]).strip()
            if not t:
                continue
            x0, y0, x1, y1 = l["bbox"]
            if y0 < 60 or y0 > 800:
                continue      # running header / footer
            s0 = l["spans"][0]
            out.append({"x": x0, "y": y0, "y1": y1, "t": t, "bold": bool(s0["flags"] & 16), "size": s0["size"]})
    # merge fragments on one baseline (number + heading are separate lines)
    out.sort(key=lambda l: (round(l["y"]), l["x"]))
    return out


def main():
    d = pymupdf.open(PDF)
    start = next(p.number for p in d if "AS content" in p.get_text() and "Subject content" in p.get_text()
                 and p.number > 5)
    units, sections, los = {}, {}, {}
    cur_sec = None
    order = []
    for pn in range(start, d.page_count):
        lines = page_lines(d[pn])
        text = " ".join(l["t"] for l in lines)
        if re.search(r"\bA Level content\b", text) and pn > start:
            # stop at the A Level content (unit 13 onwards)
            lines = lines[:next(i for i, l in enumerate(lines) if "A Level content" in l["t"])]
            stop = True
        else:
            stop = False
        # headings: bold number at the left + bold name beside it
        i = 0
        left, right = [], []
        while i < len(lines):
            l = lines[i]
            mu = re.fullmatch(r"(\d{1,2})", l["t"]) if l["bold"] and l["x"] < 80 else None
            ms = re.fullmatch(r"(\d{1,2}\.\d)", l["t"]) if l["bold"] and l["x"] < 80 else None
            mboth = re.fullmatch(r"(\d{1,2}(?:\.\d)?)[\s \t]+(.+)", l["t"]) if l["bold"] and l["x"] < 80 else None
            if (mu or ms) and i + 1 < len(lines) and abs(lines[i + 1]["y"] - l["y"]) < 3:
                name = lines[i + 1]["t"]
                num = (mu or ms).group(1)
                j = i + 2
                while j < len(lines) and lines[j]["bold"] and lines[j]["x"] > 80 and lines[j]["x"] < MIDX \
                        and lines[j]["y"] - lines[j - 1]["y"] < 16:
                    name += " " + lines[j]["t"]
                    j += 1
                order.append(("unit" if mu else "sec", num, name, pn, l["y"]))
                i = j
                continue
            if mboth and int(mboth.group(1).split(".")[0]) <= 20:
                num, name = mboth.group(1), mboth.group(2)
                order.append(("unit" if "." not in num else "sec", num, name, pn, l["y"]))
                i += 1
                continue
            if l["t"] in ("Candidates should be able to:", "Notes and guidance"):
                i += 1
                continue
            order.append(("L" if l["x"] < MIDX else "R", l, None, pn, l["y"]))
            i += 1
        if stop:
            break
    # group left-column lines into statements: a new statement starts after a vertical gap
    cur_sec, stmts = None, []
    prev = None
    for kind, a, b, pn, y in order:
        if kind == "unit":
            if int(a) <= 12:
                units[a] = b
            cur_sec, prev = None, None
        elif kind == "sec":
            if int(a.split(".")[0]) <= 12:
                sections[a] = b
                cur_sec = a
            else:
                cur_sec = None
            prev = None
        elif cur_sec is None:
            continue
        elif kind == "L":
            new = prev is None or prev[0] != pn or a["y"] - prev[1] > 15.5
            if new:
                stmts.append({"section": cur_sec, "page": pn, "y0": a["y"], "y1": a["y1"], "text": a["t"], "notes": ""})
            else:
                stmts[-1]["text"] += " " + a["t"]
                stmts[-1]["y1"] = a["y1"]
            prev = (pn, a["y"])
    # a statement continued at the top of the next page (starts lower-case or with a bullet)
    merged = []
    for s in stmts:
        if merged and merged[-1]["section"] == s["section"] and s["page"] != merged[-1]["page"] \
                and re.match(r"^[a-z•–-]", s["text"]):
            merged[-1]["text"] += " " + s["text"]
            merged[-1].setdefault("cont", []).append((s["page"], s["y0"], s["y1"]))
            continue
        merged.append(s)
    stmts = merged
    # attach right-column notes to the statement whose vertical band they sit in
    for kind, a, b, pn, y in order:
        if kind != "R":
            continue
        cands = [s for s in stmts if s["page"] == pn and s["y0"] - 4 <= a["y"]]
        cont = [s for s in stmts if any(c[0] == pn for c in s.get("cont", []))]
        if cands:
            s = max(cands, key=lambda s: s["y0"])
            s["notes"] += (" " if s["notes"] else "") + a["t"]
        elif cont:
            cont[-1]["notes"] += (" " if cont[-1]["notes"] else "") + a["t"]
        else:
            before = [s for s in stmts if s["page"] < pn]
            if before:
                before[-1]["notes"] += (" " if before[-1]["notes"] else "") + a["t"]
    # a paragraph that does not open with a command word continues the previous
    # statement: its bullets (after a colon) or printed tables (kept as notes)
    START = re.compile(r"^(Show|Describe|Explain|Use|Perform|Justify|Understand|Construct|Write|Draw|Document|"
                       r"Define|Select|Implement|Locate|Correct|Choose|Analyse|Trace|Produce)\b")
    out = []
    for s in stmts:
        if START.match(s["text"]) or not out or out[-1]["section"] != s["section"]:
            if not START.match(s["text"]):
                continue          # sub-heading such as "Graphics" / "Sound"
            out.append(s)
        elif out[-1]["text"].rstrip().endswith(":") or out[-1]["text"].rstrip().endswith(" :"):
            out[-1]["text"] += " " + s["text"]
            out[-1]["notes"] += (" " if out[-1]["notes"] and s["notes"] else "") + s["notes"]
        elif re.fullmatch(r"Graphics|Sound", s["text"].strip()):
            continue
        else:
            out[-1]["notes"] += (" " if out[-1]["notes"] else "") + s["text"] + (" " + s["notes"] if s["notes"] else "")
    stmts = out
    n = {}
    for s in stmts:
        n[s["section"]] = n.get(s["section"], 0) + 1
        los[f"{s['section']}.{n[s['section']]}"] = {"section": s["section"],
                                                    "text": re.sub(r"\s+", " ", s["text"]),
                                                    "notes": re.sub(r"\s+", " ", s["notes"])}
    units = dict(sorted(units.items(), key=lambda kv: int(kv[0])))
    sections = {k: re.sub(r"\s+continued$", "", v) for k, v in
                sorted(sections.items(), key=lambda kv: [int(x) for x in kv[0].split(".")])}
    jdump({"units": units, "sections": sections, "los": los}, work("syllabus.json"))
    print(f"units {len(units)}, sections {len(sections)}, learning outcomes {len(los)}")
    if "--print" in sys.argv:
        for u, name in units.items():
            print(f"UNIT {u} {name}")
            for sec, sn in sections.items():
                if sec.split(".")[0] != u:
                    continue
                print(f" {sec} {sn}")
                for k, v in los.items():
                    if v["section"] == sec:
                        print(f"  {k} {v['text']}" + (f" || {v['notes']}" if v["notes"] else ""))


if __name__ == "__main__":
    main()

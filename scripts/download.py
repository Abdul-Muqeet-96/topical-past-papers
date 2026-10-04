"""Download 9701 Paper 2 qp/ms PDFs into data/ and verify page-1 headers.

Usage: python3 scripts/download.py phase1|phase2
Writes/updates data/manifest.json. Prints counts only.
"""
import json, os, re, subprocess, sys, time
import pymupdf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
URL = "https://pastpapers.papacambridge.com/directories/CAIE/CAIE-pastpapers/upload/9701_{s}{yy}_{kind}_{v}.pdf"
SERIES_NAME = {"m": "February/March", "s": "May/June", "w": "October/November"}


def papers(phase):
    out = []
    if phase == "phase1":
        years_m, years_s, years_w = range(22, 27), range(22, 27), range(22, 26)
    else:
        years_m, years_s, years_w = range(16, 22), range(15, 22), range(15, 22)
    for yy in years_m:
        out.append(("m", yy, 22))
    for yy in years_s:
        for v in (21, 22, 23):
            out.append(("s", yy, v))
        if yy in (25, 26):
            out.append(("s", yy, 24))
    for yy in years_w:
        for v in (21, 22, 23):
            out.append(("w", yy, v))
        if yy == 25:
            out.append(("w", yy, 24))
    return out


def fetch(url, dest):
    for i in range(4):
        r = subprocess.run(["curl", "-sS", "-f", "-o", dest, url], capture_output=True)
        if r.returncode == 0 and os.path.getsize(dest) > 1000:
            with open(dest, "rb") as f:
                if f.read(5) == b"%PDF-":
                    return True, ""
            return False, "not a PDF"
        if r.returncode == 22:  # HTTP error (404 etc): don't retry
            return False, r.stderr.decode().strip()[-120:]
        time.sleep(2 ** (i + 1))
    return False, r.stderr.decode().strip()[-120:]


def verify(path, s, yy, v, kind):
    d = pymupdf.open(path)
    t = d[0].get_text()
    t = re.sub(r"\s+", " ", t)
    issues = []
    if f"9701/{v}" not in t:
        issues.append(f"9701/{v} not on page 1")
    notes = []
    if not re.search(r"Paper 2 AS Level Structured Questions", t, re.I):
        # AUTO-DECIDED: some official MS headers read "Paper 2 AS Structured
        # Questions" (no "Level"); same paper, so accept and record.
        m = re.search(r"Paper 2 \(?(AS Structured Questions|Structured Questions? AS Core)\)?", t, re.I)
        if m:
            notes.append(f"title variant 'Paper 2 {m.group(1)}'")
        else:
            issues.append("paper title not on page 1")
    series = f"{SERIES_NAME[s]} 20{yy:02d}"
    if series not in t:
        # AUTO-DECIDED: Feb/March series was published as "March 20yy" up to 2017
        if s == "m" and re.search(rf"\bMarch 20{yy:02d}\b", t):
            notes.append(f"series variant 'March 20{yy:02d}'")
        else:
            issues.append(f"'{series}' not on page 1")
    if kind == "ms" and "MARK SCHEME" not in t.upper():
        issues.append("not a mark scheme")
    return issues, notes, d.page_count


def main():
    phase = sys.argv[1]
    mpath = os.path.join(ROOT, "Δ-chemistry", "work", "manifest.json")
    man = json.load(open(mpath)) if os.path.exists(mpath) else {}
    for s, yy, v in papers(phase):
        pid = f"{s}{yy:02d}_{v}"
        ent = {"phase": phase, "series": s, "year": 2000 + yy, "variant": v}
        ok_all = True
        for kind in ("qp", "ms"):
            fn = f"9701_{s}{yy:02d}_{kind}_{v}.pdf"
            dest = os.path.join(DATA, fn)
            if not (os.path.exists(dest) and os.path.getsize(dest) > 1000):
                ok, err = fetch(URL.format(s=s, yy=f"{yy:02d}", kind=kind, v=v), dest)
                if not ok:
                    if os.path.exists(dest):
                        os.remove(dest)
                    ent[kind] = {"file": fn, "status": "download_failed", "error": err}
                    ok_all = False
                    continue
            issues, notes, n = verify(dest, s, yy, v, kind)
            ent[kind] = {"file": fn, "pages": n,
                         "status": "ok" if not issues else "header_mismatch",
                         "issues": issues, "notes": notes}
            ok_all &= not issues
        ent["status"] = "ok" if ok_all else "excluded"
        man[pid] = ent
    json.dump(man, open(mpath, "w"), indent=1)
    sel = [e for e in man.values() if e["phase"] == phase]
    print(phase, "papers:", len(sel), "ok:", sum(e["status"] == "ok" for e in sel),
          "excluded:", sum(e["status"] != "ok" for e in sel))
    for k, e in man.items():
        if e["phase"] == phase and e["status"] != "ok":
            print(" ", k, {kk: (e[kk]["status"], e[kk].get("issues") or e[kk].get("error")) for kk in ("qp", "ms")})


if __name__ == "__main__":
    main()

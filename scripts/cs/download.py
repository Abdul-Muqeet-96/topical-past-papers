"""Download 9618 / 9608 Paper 1 and Paper 2 qp/ms/insert PDFs into data/ and
verify page-1 headers.

Usage: python3 scripts/cs/download.py phase1|phase2
Writes/updates λ-cs/work/manifest_cs.json. Prints counts only.
"""
import os, re, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
import pymupdf
sys.path.insert(0, os.path.dirname(__file__))
from paths import DATA, MANIFEST, SERIES_NAME, TITLES, jload, jdump

URL = "https://pastpapers.papacambridge.com/directories/CAIE/CAIE-pastpapers/upload/{code}_{s}{yy}_{kind}_{v}.pdf"
# month names accepted for a series (older papers print "June 2015" style in places)
SERIES_ALT = {"m": ["February/March", "March"], "s": ["May/June", "June"], "w": ["October/November", "November"]}


def papers(phase):
    """(code, series, yy, variant) to attempt. Everything is attempted, including
    the series the spec lists as not on the site, so that each is logged."""
    out = []
    if phase == "phase1":
        code, years = "9618", range(21, 27)
    else:
        code, years = "9608", range(15, 22)
    for yy in years:
        for v in (12, 22):
            out.append((code, "m", yy, v))
        for s in ("s", "w"):
            for v in (11, 12, 13, 21, 22, 23):
                out.append((code, s, yy, v))
    return out


def fetch(url, dest):
    """-> (ok, error, http_code). Retries network errors 4 times (2, 4, 8, 16 s)."""
    err, code = "", ""
    for i in range(5):
        r = subprocess.run(["curl", "-sS", "-o", dest, "-w", "%{http_code}", "--max-time", "120", url],
                           capture_output=True)
        code = r.stdout.decode().strip()
        if r.returncode == 0:
            if code == "200" and os.path.exists(dest) and os.path.getsize(dest) > 1000:
                with open(dest, "rb") as f:
                    if f.read(5) == b"%PDF-":
                        return True, "", code
                return False, "not a PDF", code
            if code in ("301", "302", "404", "403", "410"):   # not on the site: don't retry
                return False, f"HTTP {code} (not on the site)", code
            err = f"HTTP {code}"
        else:
            err = r.stderr.decode().strip()[-120:]
        if i < 4:
            time.sleep(2 ** (i + 1))
    return False, err, code


def norm(t):
    t = re.sub(r"[‐‑‒–—]", "-", t)
    return re.sub(r"\s+", " ", t)


def verify(path, code, s, yy, v, kind):
    d = pymupdf.open(path)
    t = norm(d[0].get_text())
    issues, notes = [], []
    if f"{code}/{v}" not in t:
        issues.append(f"{code}/{v} not on page 1")
    pn = v // 10
    if not re.search(re.escape(TITLES[pn]), t, re.I):
        # AUTO-DECIDED: older wording is accepted when the paper number and a
        # matching title are printed; each variant is logged
        alt = {1: r"Paper 1 \(?(Theory Fundamentals|Written Paper)\)?",
               2: r"Paper 2 \(?((Fundamental )?Problem[- ]solving (and|&) Programming( Skills)?|Written Paper)\)?"}[pn]
        m = re.search(alt, t, re.I)
        if m:
            notes.append(f"title variant '{m.group(0)}'")
        else:
            issues.append("paper title not on page 1")
    full = f"{SERIES_NAME[s]} 20{yy:02d}"
    if full not in t:
        alts = [a for a in SERIES_ALT[s] if re.search(rf"\b{a} 20{yy:02d}\b", t)]
        if alts:
            notes.append(f"series variant '{alts[0]} 20{yy:02d}'")
        else:
            issues.append(f"'{full}' not on page 1")
    up = t.upper()
    if kind == "ms" and "MARK SCHEME" not in up:
        issues.append("not a mark scheme")
    if kind == "in" and "INSERT" not in up:
        issues.append("not an insert")
    if kind == "qp" and ("MARK SCHEME" in up or re.search(r"\bINSERT\b(?! \(ENCLOSED\))", up) and "You will need" not in t):
        issues.append("not a question paper")
    return issues, notes, d.page_count


def one(job):
    code, s, yy, v, kind = job
    fn = f"{code}_{s}{yy:02d}_{kind}_{v}.pdf"
    dest = os.path.join(DATA, fn)
    if not (os.path.exists(dest) and os.path.getsize(dest) > 1000):
        ok, err, http = fetch(URL.format(code=code, s=s, yy=f"{yy:02d}", kind=kind, v=v), dest)
        if not ok:
            if os.path.exists(dest):
                os.remove(dest)
            st = "unavailable" if "not on the site" in err else "download_failed"
            return job, {"file": fn, "status": st, "error": err}
    try:
        issues, notes, n = verify(dest, code, s, yy, v, kind)
    except Exception as e:
        return job, {"file": fn, "status": "header_mismatch", "issues": [f"unreadable: {e!r}"], "notes": []}
    return job, {"file": fn, "pages": n, "status": "ok" if not issues else "header_mismatch",
                 "issues": issues, "notes": notes, "bytes": os.path.getsize(dest)}


def main():
    phase = sys.argv[1]
    man = jload(MANIFEST, {})
    jobs = [(c, s, yy, v, k) for c, s, yy, v in papers(phase) for k in ("qp", "ms", "in")]
    with ThreadPoolExecutor(4) as ex:
        res = dict(ex.map(one, jobs))
    for code, s, yy, v in papers(phase):
        pid = f"{code}_{s}{yy:02d}_{v}"
        ent = {"phase": phase, "code": code, "series": s, "year": 2000 + yy, "variant": v, "paper": v // 10}
        for k in ("qp", "ms", "in"):
            ent[k] = res[(code, s, yy, v, k)]
        q, m = ent["qp"]["status"], ent["ms"]["status"]
        if q == "ok" and m == "ok":
            ent["status"] = "ok"
        elif q == "unavailable" and m == "unavailable":
            ent["status"] = "unavailable"
        elif "download_failed" in (q, m):
            ent["status"] = "download_failed"
        else:
            ent["status"] = "excluded"
        man[pid] = ent
    jdump(man, MANIFEST)
    sel = {k: e for k, e in man.items() if e["phase"] == phase}
    # count table: series x (P1 ok, P2 ok, inserts, unavailable)
    print(f"{phase}: papers attempted {len(sel)}; ok {sum(e['status'] == 'ok' for e in sel.values())}; "
          f"unavailable {sum(e['status'] == 'unavailable' for e in sel.values())}; "
          f"excluded {sum(e['status'] == 'excluded' for e in sel.values())}; "
          f"download failed {sum(e['status'] == 'download_failed' for e in sel.values())}")
    print("series | P1 ok | P2 ok | inserts ok | unavailable | excluded/failed")
    ser = sorted({(e["year"], {"m": 0, "s": 1, "w": 2}[e["series"]], e["series"]) for e in sel.values()})
    for y, _, s in ser:
        es = [e for e in sel.values() if e["year"] == y and e["series"] == s]
        print(f"  {s}{y % 100:02d} | {sum(e['status'] == 'ok' and e['paper'] == 1 for e in es)} | "
              f"{sum(e['status'] == 'ok' and e['paper'] == 2 for e in es)} | "
              f"{sum(e['in']['status'] == 'ok' for e in es)} | "
              f"{sum(e['status'] == 'unavailable' for e in es)} | "
              f"{sum(e['status'] in ('excluded', 'download_failed') for e in es)}")
    for k, e in sorted(sel.items()):
        if e["status"] in ("excluded", "download_failed"):
            print("  X", k, {kk: (e[kk]["status"], e[kk].get("issues") or e[kk].get("error")) for kk in ("qp", "ms")})
        elif e["status"] == "ok" and e["in"]["status"] == "header_mismatch":
            print("  insert?", k, e["in"]["issues"])
    nfail = sum(e[k]["status"] == "download_failed" for e in sel.values() for k in ("qp", "ms", "in"))
    print("network failures:", nfail)


if __name__ == "__main__":
    main()

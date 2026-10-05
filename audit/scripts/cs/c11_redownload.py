"""Check 1b: download 10 random source PDFs again (seed 9618) and compare them byte for byte with data/.
Files re-written by the download site carry a per-download trace ID; for those the comparison is
repeated on the page text."""
import hashlib, os, random, re, subprocess, sys
import pymupdf as f
from c00_common import *

tmp = sys.argv[1]
rows = [r for r in jl("sources.json") if r["status"] == "OK"]
random.seed(9618)
smp = random.sample(rows, 10)
out = []
for r in smp:
    b = r["file"]
    dst = os.path.join(tmp, b)
    code = subprocess.run(["curl", "-sS", "-o", dst, "-w", "%{http_code}", "--max-time", "180", URL + b],
                          capture_output=True, text=True).stdout
    h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None
    a, c = h(os.path.join(DATA, b)), h(dst)
    row = {"file": b, "http": code, "identical": a == c, "local_sha256": a, "remote_sha256": c,
           "local_size": os.path.getsize(os.path.join(DATA, b)), "remote_size": os.path.getsize(dst) if c else None}
    if a != c and c:
        strip = lambda t: re.sub(r"Trace ID: \S+", "", t)
        ta = [strip(p.get_text()) for p in f.open(os.path.join(DATA, b))]
        tb = [strip(p.get_text()) for p in f.open(dst)]
        row["same_text_apart_from_trace_id"] = ta == tb
        row["producer"] = f.open(dst).metadata.get("producer")
    out.append(row)
    print(b, code, "IDENTICAL" if a == c else f"DIFFERENT (text equal apart from trace ID: {row.get('same_text_apart_from_trace_id')})")
jd(out, "redownload.json", 1)

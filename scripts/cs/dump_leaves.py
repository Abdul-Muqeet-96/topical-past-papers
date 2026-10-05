"""Print the extracted text of every lowest-level part, compactly, for tagging.
usage: dump_leaves.py phase pid [pid ...] [--words N] [--untagged]
Line format:  "Qn S: stem"   " a>: lettered intro"   " a.i [marks] text"."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from paths import work, jload
from tags import lab2key


def cut(t, n):
    """Head and tail of a long text: the question itself often follows a table."""
    t = re.sub(r"[.…]{4,}", "…", t)
    w = t.split()
    if len(w) <= n + 6:
        return " ".join(w)
    h = int(n * 0.6)
    return " ".join(w[:h]) + " ⟨…⟩ " + " ".join(w[-(n - h):])


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--") and not a.isdigit()]
    phase, pids = args[0], args[1:]
    n = int(sys.argv[sys.argv.index("--words") + 1]) if "--words" in sys.argv else 55
    P = jload(work(f"parts_{phase}.json"))
    for pid in pids or sorted(P):
        p = P[pid]
        print(f"## {pid} ({p['ref']})")
        for Q in p["questions"]:
            if Q["stem_text"]:
                print(f"Q{Q['n']} S: {cut(Q['stem_text'], n)}")
            else:
                print(f"Q{Q['n']}")
            for L in Q["letters"]:
                if L["romans"]:
                    if L["intro_text"]:
                        print(f" {lab2key(L['label'])}>: {cut(L['intro_text'], n // 2)}")
                    for R in L["romans"]:
                        print(f" {lab2key(R['label'])} [{R['marks']}] {cut(R['text'], n)}")
                else:
                    print(f" {lab2key(L['label'])} [{L['marks']}] {cut(L['full_text'], n)}")


if __name__ == "__main__":
    main()

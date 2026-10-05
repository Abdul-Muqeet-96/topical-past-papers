"""Check every unit's tags against the syllabus wording.

For each tagged part, compare the words of the part (with its stem and
lettered introduction) with the wording of its learning outcome and notes.
Parts that share no significant word with their outcome are listed for a
reading check. Also prints the number of parts per learning outcome.
usage: check_tags.py phase [--list] [--unit N]"""
import os, re, sys
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(__file__))
from paths import work, jload
from tags import load as load_tags, lab2key

STOP = set("""show understanding describe explain using used use uses including include given following different
between their that this with from which each will have been such other than more when where what also into only
candidates should able data computer system systems program write simple example statement statements appropriate
suitable need needs purpose method methods type types terms term value values number state identify give complete
table tick draw line lines box boxes one two three four correct answer working stored store stores""".split())
# words of question papers that point to an outcome whose own wording differs
EXTRA = {
    "9.2.7": "flowchart", "9.2.6": "flowchart structured steps step", "9.2.5": "steps step algorithm describe",
    "9.2.4": "selection iteration algorithm pseudocode loop", "9.2.2": "identifier variable names meaningful practice",
    "9.2.8": "steps refinement", "9.2.9": "logic expression condition statement",
    "9.1.1": "abstraction information items required essential", "9.1.2": "decomposition modules sub-modules",
    "10.1.1": "data type types integer real string boolean char date", "10.1.2": "record type field fields",
    "10.2.1": "array index bound elements dimension", "10.2.2": "array structure", "10.2.3": "array arrays element",
    "10.2.4": "array sort search bubble linear", "10.3.1": "file files text", "10.3.2": "file files text line lines",
    "10.4.2": "stack queue linked list adt", "10.4.3": "stack queue linked list push pop pointer",
    "10.4.4": "stack queue linked list array pointer", "11.1.2": "expression evaluate constant assignment declare",
    "11.1.3": "function functions expression evaluates library insert", "11.2.1": "case loop construct iteration if",
    "11.2.2": "loop structure construct", "11.3.1": "procedure module", "11.3.2": "subroutine module modules local",
    "11.3.3": "parameter parameters header byref reference", "11.3.4": "function module",
    "11.3.5": "function module", "11.3.6": "header interface parameter", "11.3.7": "efficient",
    "12.1.4": "stage life cycle analysis design", "12.2.1": "structure chart module modules",
    "12.2.2": "state-transition state", "12.3.1": "fault errors", "12.3.2": "error errors syntax logic run-time",
    "12.3.3": "error errors correct correction", "12.3.4": "trace dry testing test walkthrough stub",
    "12.3.5": "test plan", "12.3.6": "test data", "12.3.7": "maintenance", "12.3.8": "change changes modified amend",
    "4.2.3": "trace", "4.2.5": "addressing instruction instructions acc", "4.3.2": "bit instruction acc and xor",
    "4.3.1": "shift lsl lsr", "3.2.4": "logic circuit expression", "3.2.5": "truth table", "3.2.6": "logic expression",
    "3.2.2": "gate gates", "3.2.3": "gate truth", "3.2.1": "gate gates symbol", "8.3.4": "sql ddl define table field",
    "8.3.5": "sql dml script return", "8.1.4": "e-r entity-relationship", "8.1.3": "key relationship tuple entity",
    "8.1.7": "normalised 3nf tables", "8.1.5": "normal form 1nf 2nf 3nf", "8.1.6": "3nf normal form",
    "8.2.1": "dbms dictionary schema security integrity", "8.2.2": "dbms query processor developer interface",
    "1.1.2": "binary denary hexadecimal bcd complement convert", "1.1.3": "addition subtraction add subtract overflow",
    "1.1.1": "kibibyte kilobyte mebibyte megabyte gibibyte prefix tebibyte gigabyte", "1.1.5": "ascii unicode character",
    "1.2.2": "file size calculate", "1.2.3": "resolution depth", "1.2.1": "pixel header bitmap resolution depth",
    "1.2.6": "sampling sound analogue", "1.2.7": "sampling rate resolution sound", "1.3.3": "rle compress compression",
    "1.3.1": "compress compressed compression", "1.3.2": "lossy lossless", "5.2.4": "ide", "5.2.2": "compiler interpreter",
    "5.1.2": "management operating", "5.1.3": "utility defragmentation formatter back-up", "5.1.4": "library dll",
    "6.2.2": "validation check", "6.2.3": "verification parity checksum", "6.2.1": "validation verification integrity",
    "6.1.3": "firewall password signature encryption security", "6.1.4": "malware virus phishing pharming hacker threat",
    "6.1.5": "risk threat restrict", "6.1.6": "encryption access rights secure", "7.1.5": "ai artificial",
    "7.1.4": "licence", "7.1.3": "copyright", "7.1.1": "ethical body conduct", "7.1.2": "ethical ethically",
    "2.1.14": "ip address subnet subnetting", "2.1.5": "topology", "2.1.10": "ethernet csma collision",
    "2.1.6": "cloud", "2.1.9": "router", "2.1.8": "switch nic wnic wap bridge", "2.1.11": "streaming",
    "2.1.7": "wired wireless cable satellite", "2.1.13": "modem pstn cell dedicated", "2.1.3": "client-server peer",
    "2.1.4": "thin-client thick-client", "2.1.2": "lan wan", "3.1.8": "sensor monitoring control feedback actuator",
    "3.1.2": "embedded", "3.1.3": "printer microphone touchscreen disk solid optical headset operation",
    "3.1.4": "buffer", "3.1.5": "ram rom", "3.1.6": "sram dram", "3.1.7": "prom eprom eeprom",
    "4.1.2": "register registers", "4.1.7": "fetch-execute f-e", "4.1.8": "interrupt", "4.1.5": "performance",
    "4.1.6": "port", "4.1.3": "clock control unit", "4.1.4": "bus", "4.1.1": "von neumann",
    "4.2.2": "assembler pass", "4.2.4": "instruction group groups", "4.2.1": "assembly machine",
}


def words(t):
    return {w for w in re.findall(r"[a-z][a-z0-9\-]{2,}", t.lower()) if w not in STOP}


def main():
    phase = sys.argv[1]
    P = jload(work(f"parts_{phase}.json"))
    T = load_tags(phase)
    S = jload(work("syllabus.json"))
    LOS = S["los"]
    kw = {k: words(v["text"] + " " + v["notes"] + " " + S["sections"][v["section"]] + " " + EXTRA.get(k, ""))
          for k, v in LOS.items()}
    only = int(sys.argv[sys.argv.index("--unit") + 1]) if "--unit" in sys.argv else None
    per = Counter()
    flagged = []
    for pid, p in sorted(P.items()):
        for Q in p["questions"]:
            for L in Q["letters"]:
                for lab, text in ([(R["label"], R["text"]) for R in L["romans"]] if L["romans"]
                                  else [(L["label"], L["full_text"])]):
                    code = T[(pid, Q["n"], lab)]
                    per[code] += 1
                    if code not in LOS:
                        continue
                    ctx = words(text + " " + L["intro_text"])
                    if not (ctx & kw[code]) and not (words(Q["stem_text"]) & kw[code] and len(ctx) < 6):
                        flagged.append((code, pid, Q["n"], lab2key(lab), text))
    # a second view: parts whose words fit another outcome's wording much better
    import math
    df = Counter(w for k in kw for w in kw[k])
    idf = {w: math.log(len(kw) / df[w]) + 0.2 for w in df}
    better = []
    for pid, p in sorted(P.items()):
        for Q in p["questions"]:
            for L in Q["letters"]:
                for lab, text in ([(R["label"], R["text"]) for R in L["romans"]] if L["romans"]
                                  else [(L["label"], L["full_text"])]):
                    code = T[(pid, Q["n"], lab)]
                    if code not in LOS:
                        continue
                    ctx = words(text + " " + L["intro_text"])
                    sc = {k: sum(idf[w] for w in ctx & kw[k]) for k in kw}
                    best = max(sc, key=sc.get)
                    if best != code and sc[best] > 2 * sc[code] + 1.5 and best.split(".")[0] != code.split(".")[0]:
                        better.append((code, best, pid, Q["n"], lab2key(lab), text))
    units = defaultdict(lambda: [0, 0])
    for code, n in per.items():
        if code in LOS:
            units[int(code.split(".")[0])][0] += n
    for f in flagged:
        units[int(f[0].split(".")[0])][1] += 1
    print("unit: parts tagged / parts sharing no word with their outcome")
    print("  " + "  ".join(f"U{u}: {a}/{b}" for u, (a, b) in sorted(units.items())))
    unused = [k for k in LOS if not per[k]]
    print(f"outcomes used {len(LOS) - len(unused)} of {len(LOS)}; unused: {' '.join(unused)}")
    print(f"parts whose words fit an outcome of another unit much better: {len(better)}")
    if "--better" in sys.argv:
        for code, best, pid, q, key, text in sorted(better):
            if only and int(code.split(".")[0]) != only:
                continue
            t = re.sub(r"[.…]{4,}", "…", text)
            print(f"{code}>{best}? {pid[5:]} Q{q} {key}: {' '.join(t.split()[:30])}")
    if "--list" in sys.argv:
        for code, pid, q, key, text in sorted(flagged):
            if only and int(code.split(".")[0]) != only:
                continue
            t = re.sub(r"[.…]{4,}", "…", text)
            print(f"{code} [{LOS[code]['text'][:48]}] {pid[5:]} Q{q} {key}: {' '.join(t.split()[:26])}")


if __name__ == "__main__":
    main()

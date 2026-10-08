"""Paths and constants shared by the CS (9618/9608) pipeline."""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
CS = os.path.join(ROOT, "λ-cs")
WORK = os.path.join(CS, "build", "work")
DATA = os.path.join(ROOT, "hub", "data")
MANIFEST = os.path.join(WORK, "manifest_cs.json")
STATE = os.path.join(CS, "build", "state_cs.json")
OUT = {1: os.path.join(CS, "booklets", "p1-topical-workbook"), 2: os.path.join(CS, "booklets", "p2-topical-workbook")}
BOOK_FILE = {1: "CS-9618-P1-Topical-Workbook.pdf", 2: "CS-9618-P2-Topical-Workbook.pdf"}
PAPER_TOTAL = 75
TITLES = {1: "Paper 1 Theory Fundamentals",
          2: "Paper 2 Fundamental Problem-solving and Programming Skills"}
SERIES_NAME = {"m": "February/March", "s": "May/June", "w": "October/November"}
SERIES_REF = {"m": "MAR", "s": "M/J", "w": "O/N"}
SERIES_ORDER = {"w": 3, "s": 2, "m": 1}

os.makedirs(WORK, exist_ok=True)
os.makedirs(DATA, exist_ok=True)


def jload(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)


def jdump(obj, path, indent=1):
    with open(path, "w") as f:
        json.dump(obj, f, indent=indent, ensure_ascii=False)


def work(name):
    return os.path.join(WORK, name)


def set_stage(stage, status, note=None):
    st = jload(STATE, {"stages": {}, "notes": {}})
    st["stages"][str(stage)] = status
    if note:
        st["notes"][str(stage)] = note
    jdump(st, STATE)

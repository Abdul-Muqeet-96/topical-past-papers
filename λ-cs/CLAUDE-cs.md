# Computer Science 9618 Papers 1 and 2: spec

Specification for the CS run (prompt: `PROMPT-cs.md`). Repo-wide rules are in
`CLAUDE.md`. Item, context, cropping, mark-scheme and layout rules are those of
`Δ-chemistry/CLAUDE-chemistry.md`, as fixed by the audit (the current
`scripts/` already do all of this); this file lists what is different.

## Goal
Two part-level topical workbooks, built in one run:
- **P1 book**: Paper 1 Theory Fundamentals, units 1-8 of `λ-cs/cs-syllabus.pdf`.
- **P2 book**: Paper 2 Fundamental Problem-solving and Programming Skills,
  units 9-12.

Use the syllabus version in this repo, valid for 2027-29. Verify the unit and
section names and numbers against it:
1 Information representation (1.1-1.3); 2 Communication (2.1);
3 Hardware (3.1-3.2); 4 Processor Fundamentals (4.1-4.3);
5 System Software (5.1-5.2); 6 Security, privacy and data integrity (6.1-6.2);
7 Ethics and Ownership (7.1); 8 Databases (8.1-8.3);
9 Algorithm Design and Problem-solving (9.1-9.2);
10 Data Types and Structures (10.1-10.4); 11 Programming (11.1-11.3);
12 Software Development (12.1-12.3).

A part is filed by its topic, not its paper. A Paper 1 part that tests a unit
9-12 topic goes to the P2 book, and the reverse; log each case.

## Sources
URL: `https://pastpapers.papacambridge.com/directories/CAIE/CAIE-pastpapers/upload/{code}_{s|w}{yy}_{qp|ms|in}_{variant}.pdf`

- **Phase 1: 9618 (current syllabus, first exams 2021).** Question papers
  found on the site: s21, w21, s23, w23, s24, w24, s25, w25, s26, each with
  P1 variants 11-13 and P2 variants 21-23.
  - Not on the site (log as unavailable): s22, every March (m) series, and
    w26 (not yet sat).
  - Mark schemes were spot-checked as present. Verify every paper by
    download.
- **Phase 2: 9608 (previous syllabus).** Found: s15-s21 (variants 11-13,
  21-23); w15 (11, 13, 21-23); w16-w19 (11-13, 21-23); w21 (11 only); w20 is
  missing.
  - Include a part only if it is clearly covered by the 2027-29 learning
    outcomes; otherwise list it as out-of-syllabus and exclude it.
- **Inserts.** Many 9618 Paper 2 papers have an insert (`_in_2x`) holding
  the pseudocode functions/operators. Try to download one for every paper,
  P1 too.
  - The P2 book's Appendix gets the insert of the newest paper, once.
  - An item whose text refers to the insert gets a grey note "Uses the
    insert (Appendix)", provided its own paper's insert matches the
    appendix copy in text.
  - If its paper's insert differs, show the relevant insert pages inline as
    context for that item instead.
- **Pre-release material (9608 Paper 2).** A part that needs pre-release
  material is excluded and reported. Pre-release material is not
  downloaded.
- **Header check.** Page 1 must show `<code>/<variant>`, the series, and the
  paper title: "Paper 1 Theory Fundamentals" or "Paper 2 Fundamental
  Problem-solving and Programming Skills" (older 9608 wording may differ
  slightly; accept the paper number plus a matching title and log it).

## Paper-level verification (replaces the Chemistry checks 1-4)
1. Every question number appears exactly once.
2. The part [marks] add up to the paper total printed on the cover ("The
   total mark for this paper is 75"). Where a question has [Total: n], that
   must match too.
3. The MS marks for each question equal the QP marks for that question.
4. References come from the header text only, e.g. `M/J 25/P12/Q3/b`,
   `O/N 17/P21/Q2/a,b(i,ii)`.

Failures: a missing or duplicated question, or a wrong paper total → exclude
the paper. A single question failing check 3 → exclude that question. Log
everything. Typo-tolerant MS labels are allowed only when unambiguous (as in
Chemistry).

## CS-specific context rules
- Pseudocode, program code, tables, trace tables, logic circuits, ER
  diagrams, SQL and network diagrams are figures: keep them whole, and never
  split them across pages.
- Tables and trace tables the student must complete stay, with their blank
  cells.
- An identifier defined in an earlier part is a label, like "compound G" in
  Chemistry: a procedure, function, array, record type, variable, file or
  table name such as `Search()`, `StudentRecord`, `Stock` or `TBL_ORDER`.
  An item that uses it must include the part that defines it (question crop
  only).
- "Write program code" answers: the MS rows can be long. Crop them whole,
  across pages.

## The books
- Layout as in the Chemistry book: own cover, contents with exact page numbers,
  unit title pages, running header, bookmarks, newest first, Answers Section
  after each unit, Topic index, items.jsonl, index.csv, topics.json, one PDF
  per unit.
- Appendix: P2 book = the newest insert. P1 book = none, unless the papers
  print shared reference material.
- Output: `λ-cs/p1-topical-workbook/` and `λ-cs/p2-topical-workbook/`. Each
  holds the book, `units/`, index.csv, items.jsonl and topics.json.
  `λ-cs/report.md` and `λ-cs/SUMMARY.md` cover both books.
- Build and commit a Phase-1-only pair of books first (fallback), then add
  Phase 2.
- Any file over 95 MB: don't push it; note it in SUMMARY.md.

## Self-check (repeat check → fix → rebuild until everything passes)
Adapt `audit/scripts` and run every check of the Chemistry audit on both
books:
- source headers, plus 10 random re-downloads compared byte for byte;
- paper level, coverage, and marks;
- the three-way consistency of book, index, items.jsonl and unit PDFs;
- crop quality: clipped text, cut figures, furniture, visible dotted lines,
  page splits, dropped ink;
- self-containment, including the identifier rule;
- topics: a blind re-tag of every item, with every disagreement resolved by
  reading the item;
- structure, file, and Phase 2 checks;
- report accuracy.

Visual: at least 15 question items and 5 answers per unit, plus every
automated flag, viewed at ≥ 90 dpi. After every rebuild, re-run all checks.

Write `audit/CS_CHECK.md` with every check marked PASS / FAIL / NOT RUN,
with counts and the script used. Keep report.md and SUMMARY.md accurate.

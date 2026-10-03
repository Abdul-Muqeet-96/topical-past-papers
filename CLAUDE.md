# Cambridge 9701 Chemistry Paper 2 — part-level topical workbook

Goal: one PDF workbook of 9701 Paper 2 (AS Level Structured Questions, 60
marks). Each question PART is a separate item filed under its own syllabus
topic, with enough official context to be solvable alone, and an Answers
Section after each unit. Readers: a student, and Claude (to generate new
questions from it). Anything unreadable by either is excluded and reported.

## Autonomy (nobody is watching this run)
- Do NOT stop to ask questions. Apply the defaults below, log each in
  report.md under "AUTO-DECIDED" (item, issue, what you did), and continue.
- STOP only for hard blockers: (1) the start-up curl is blocked; (2) all
  downloads fail mid-run; (3) PyMuPDF/PDF tooling cannot be installed;
  (4) you cannot commit/push. On a hard blocker, write STOPPED.md (what failed,
  what you tried, what state.json says is done) and end the run.
- Never guess, retype, or reconstruct content. When unsure, exclude the item
  and list it in report.md. Do not use web_fetch as a workaround for blocked
  downloads.
- Keep heavy work in /scripts. Print counts and short summaries only.
- Commit and push after every stage. Progress lives in state.json so a new
  session can resume from the last finished stage.
- Spend vision (image reading) sparingly: use the PDF text layer and
  coordinates wherever possible; use images for spot-checks, figure-only parts,
  and anything the text layer can't resolve.

## Sources
URL: https://pastpapers.papacambridge.com/directories/CAIE/CAIE-pastpapers/upload/9701_{m|s|w}{yy}_{qp|ms}_{variant}.pdf
- m = Feb/March (India), variant 22 only; s = May/June; w = Oct/Nov.
- Paper 2 variants 21, 22, 23; variant 24 only for s25, s26, w25.
- Checked to exist: m16-m26 (v22); s15-s26 and w15-w25 (v21-23) plus v24 for
  s25, s26, w25. Each has both qp and ms (re-verify by download).
- Verify each download: page-1 header must show the expected 9701/<variant>,
  "Paper 2 AS Level Structured Questions" and the series. Mismatch = exclude
  and report.

## Phases
- Phase 1: m22 through s26 (syllabus 2025-27 is version 1, Sep 2022; its only
  content change is some reagents, so content matches exams from 2022).
- Phase 2: m16-m21, s15-s21, w15-w21. Set on an earlier syllabus. Include an
  item only if clearly covered by the current learning outcomes in
  chemistry-syllabus.pdf; otherwise list it as out-of-syllabus and exclude.
- Build and commit a complete Phase-1-only book first (fallback), then extend.

## Paper-level verification (before splitting; all must pass)
1. Every question number present exactly once.
2. Each question's [Total: n] equals the sum of its part [marks].
3. Question totals sum to 60.
4. MS marks for each question equal the QP total.
5. References come from the paper's own header text, never typed:
   "May/June 2025" + 9701/22 -> M/J 25/P22
   "February/March 2026" + 9701/22 -> MAR 26/P22
   "October/November 2025" + 9701/23 -> O/N 25/P23
   Item reference = paper reference + question/part, e.g. M/J 25/P22/Q3(c).
Defaults on failure: missing/duplicate question or total != 60 -> exclude the
whole paper. A single question failing checks 2 or 4 -> exclude that question.
Log all in report.md. Never patch.

## Splitting into items
- Default item = lettered part: (a), (b), (c).
- Split roman sub-parts (i),(ii) into separate items ONLY if they belong to
  different topics AND each is solvable independently (needs only the stem, the
  lettered part's intro, and shared data; not an earlier sub-part's answer).
  Otherwise keep the lettered part whole.
- A part (or unsplittable block) covering several topics goes under the topic
  with the most marks, tagged "also <n>" with the mark split. Tie -> use the
  topic of its first sub-part and log as AUTO-DECIDED.
- Dependent adjacent parts of one question landing in the same unit stay
  together as one item (reference like Q3(a)-(c)), stem shown once. Otherwise
  each part is its own item with its own context.
- Coverage check: every part of every included question appears as an item in
  exactly one unit. Context-only appearances don't count. Report gaps/dupes.

## Context (each item must be solvable on its own)
An item = reference + "Context" block(s) + the part. Build context from crops of
the SAME paper, in this order:
1. The question stem (text before the first lettered part).
2. Every Table / Fig. / data block / equation the part mentions.
3. Any earlier part the item depends on: wording like "your answer to", "the
   compound/species/letter ... in (x)", or a label (compound G, element X,
   ion Y) defined earlier. Include that part's question crop (answer lines
   removed, nothing from the mark scheme).
Rules:
- Resolve references with the text layer (patterns for "Table n.n", "Fig. n.n",
  "(x)(y)", defined labels); confirm visually on a sample.
- Self-containment check per item: every Table/Fig./label/part reference in the
  item's text must be present in the item. On failure: keep the lettered part
  whole; if still failing, exclude and report. Never leave a dangling
  reference.
- If context would exceed about one page or can't be resolved: keep the
  lettered part whole, else exclude and report.
- Do not show the question's [Total: n] in a split item; keep the part's own
  [marks].
- Context blocks carry a small generated "Context" label.

## Cropping
- Vector clips via PyMuPDF (pip install pymupdf); stitch multi-page regions
  into one flow. Screenshots only if no other way, and report them.
- Remove: dotted answer lines, empty writing space, "DO NOT WRITE IN THIS
  MARGIN", barcodes, page numbers, footers, BLANK PAGE pages, cover and
  instruction pages.
- Keep: all text, diagrams, structural formulae, graphs/axes, and tables,
  INCLUDING tables the student must complete (blank cells stay).
- Mark scheme: crop rows matching the item's part (e.g. "3(c)(i)"), full width
  including the Guidance column when present (2022+ layout is Question |
  Answer | Marks | Guidance; older has no Guidance). Also crop rows for every
  context part, labelled "Answer for context part (x)".
- The item's [marks] must equal the MS marks for that part; mismatch -> exclude
  item and report.
- Appendix: include the Periodic Table once, cropped from the newest paper.
  (The Data Booklet is a separate document: not included.)

## Topics (22 AS units; verify numbers/names against chemistry-syllabus.pdf)
1 Atomic structure; 2 Atoms, molecules and stoichiometry; 3 Chemical bonding;
4 States of matter; 5 Chemical energetics; 6 Electrochemistry; 7 Equilibria;
8 Reaction kinetics; 9 Periodic Table: chemical periodicity; 10 Group 2;
11 Group 17; 12 Nitrogen and sulfur; 13 Intro to AS organic chemistry;
14 Hydrocarbons; 15 Halogen compounds; 16 Hydroxy compounds;
17 Carbonyl compounds; 18 Carboxylic acids and derivatives;
19 Nitrogen compounds; 20 Polymerisation; 21 Organic synthesis;
22 Analytical techniques.
- Tag every lowest-level part in topics.json with: topic number, the syllabus
  section/learning outcome that justifies it, and its marks.
- A part with no clear syllabus match: exclude and list. A unit with fewer than
  5 items: keep it, list it in report.md, do not merge or drop.

## Layout (follow the Physics booklet in this repo)
Study its cover, contents, unit-title, question, running-header and answers
pages; write layout.md; then follow it (no approval needed; render 3 sample
pages, inspect them, and fix obvious problems; log what you checked).
- Cover: your own design, no Read & Write branding.
- Contents: each unit and its Answers Section with page numbers (two-pass
  build so numbers are correct).
- Title page per unit; running header with the unit name.
- Numbered items, bold reference above each, newest first; within a paper, in
  question/part order.
- Answers Section after each unit, same order.
- Index of which unit each part went to (in the book and as index.csv:
  reference, unit, marks, page, also-topics, context-parts).
Deliverables: full book PDF, one PDF per unit (items + answers), index.csv,
report.md, SUMMARY.md. If any file exceeds 95 MB (GitHub limit is 100 MB),
don't push it; keep the per-unit PDFs and note this in SUMMARY.md.

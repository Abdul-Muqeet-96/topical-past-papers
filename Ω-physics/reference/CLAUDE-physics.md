# Physics 9702 Paper 2 spec

Specification for the Physics run (prompt: `PROMPT-physics.md`). Repo-wide rules are in `CLAUDE.md`.

# Physics 9702 Paper 2 — topical workbook (for a student and for Claude)

Goal: one PDF workbook of 9702 Paper 2 (AS Level Structured Questions, 60
marks), filed by the 11 AS topics of `Ω-physics/reference/physics-syllabus.pdf`
(2025-27), with an Answers Section after each unit. Two readers: the student,
and Claude Code teaching the student, so every item must have readable text
(a text layer), not only pixels.

## Two sources, split by year
- **Part A, papers up to and including 2023: the uploaded booklet only**
  (`Ω-physics/reference/Physics paper 2 9702 3.pdf`, 550 scanned pages, no text layer,
  12 old-syllabus units, Read and Write Publications). Its selection of
  questions, its items and its answers are used as they are. Do not rebuild
  them from official papers.
- **Part B, 2024 onwards: built from the official papers** with the
  Chemistry pipeline (vector crops, part-level items, mark-scheme crops).
- Booklet items dated 2024 or later are dropped (Part B covers them). If the
  booklet has no items at all from a 2023 series/variant, build that paper
  as Part B and log it.

## Autonomy (nobody is watching)
- Do not ask questions. Apply the defaults here, log each in report.md under
  "AUTO-DECIDED" (item, issue, what you did), and continue.
- STOP only for hard blockers: downloads all fail; PyMuPDF/tesseract cannot be
  installed; cannot commit/push. Then write STOPPED.md (what failed, what you
  tried, what state_physics.json says is done) and end.
- Never retype or reconstruct question content. OCR text is only an invisible
  text layer over the original scan, never a replacement for it.
- Commit and push after every stage; progress in `Ω-physics/build/state_physics.json` so a new
  session can resume.

## Quality first (cost is not a constraint)
- Accuracy and quality come before token use. Never skip a check, a fix or a
  visual inspection to save tokens; rebuild as many times as needed until the
  checks pass.
- Still work efficiently: heavy work in Python scripts, print counts and short
  summaries, OCR locally with tesseract (no websites), reuse code (copy
  `scripts/` to `hub/scripts/physics/` and adapt; don't edit the Chemistry scripts).
- Use images whenever text or coordinates can't settle a question, and for all
  the visual checks below. Wait for background jobs with a check that can't
  match its own command line (a marker file or PID, not `pgrep -f`).

## Part A: the booklet
1. OCR every page (tesseract 300 dpi, `--oem 1 --psm 3 -l eng`, 4 jobs in
   parallel). Save word boxes (TSV) in `Ω-physics/build/work/ocr/`. Write
   `Ω-physics/reference/booklet-ocr.pdf`: the original page images with the words added as
   invisible text (PyMuPDF `insert_text`, render_mode 3, sized to each word box).
   All Part A crops come from this file, so they carry the text layer.
2. Find the structure from OCR: unit title pages, Answers Sections, running
   headers ("Physics A Level P-2 Topical Workbook", page number, unit name),
   footer/branding, and every item heading "n. <reference>" (e.g.
   "2. M/J 23/P21/Q2/a,b", "9. MAR 21/P22/Q6,a,b(i,ii,iii)"). References are
   printed inconsistently: parse with a tolerant regex; read only the heading
   strips that fail the regex by image (a cropped strip, not the full page).
3. Item = from its heading to the next heading (or the end of the unit),
   across pages. Answer = the same number in that unit's Answers Section.
   Crop out running headers, footers, page numbers, branding and blank space
   between items. Keep everything else exactly as scanned (answer lines too).
4. Units: booklet unit → syllabus topic: 1→1, 2 (Measurement techniques)→1,
   3→2, 4→3, 5→4, 6→5, 7→6, 8→7, 9→8, 10 (Current of electricity)→9,
   11→10, 12 (Particle and nuclear)→11. Verify names against the syllabus.
5. Reference shown in the book: normalised to the Part B style when the parse
   is unambiguous (`M/J 23/P21/Q2/a,b`), otherwise exactly as printed. Keep
   the booklet's own part letters (some booklet items relabel parts: leave
   them; do not fix).
6. Light check of the booklet (less rigorous than Part B; report only):
   - every item has an answer with the same number, and vice versa;
   - references parse; no duplicate items; years ≤ 2023;
   - item counts per unit and page ranges match the booklet contents page;
   - 5 items per unit (55 in all, spread across years): compare the item's
     printed [marks] with the official QP of that paper (download only those
     papers) and view the images side by side for missing figures or text;
     if more than 2 problems are found in a unit, check every item of that unit;
   - flag (do not remove) items that clearly test content outside the 2025-27
     AS syllabus: add a small grey note "May be outside the 2025–27 syllabus"
     and list them in report.md.

## Part B: official papers 2024 onwards
Source URL:
`https://pastpapers.papacambridge.com/directories/CAIE/CAIE-pastpapers/upload/9702_{m|s|w}{yy}_{qp|ms}_{variant}.pdf`
Checked to exist (qp and ms): m24 v22; s24 v21-23; w24 v21-23; m25 v22;
s25 v21-24; w25 v21-24; m26 v22; s26 v22-24. s26 v21 has a QP but no MS:
exclude and report. Re-verify by download; page-1 header must show
9702/<variant>, "Paper 2 AS Level Structured Questions" and the series.
Downloads go to `data/` (gitignored); manifest `Ω-physics/build/work/manifest_physics.json`.

Follow `Δ-chemistry/reference/CLAUDE-chemistry.md` for Part B except where this file
differs. Already-fixed behaviour of the copied scripts (keep it):
- non-standard page scale normalised to A4; crops found from rendered ink;
  answer-line dots removed from the text layer; page furniture excluded;
- typo-tolerant MS labels (only when unambiguous, logged);
- one item per question per unit; references like `M/J 25/P22/Q5/b`,
  `Q3/b(ii,iii)`, `Q3/a,b,c`; context inline in paper order, no "Context"
  labels, nothing shown twice; MS rows of an earlier part only when the item
  uses its answer; bookmarks; items.jsonl.
Physics differences:
- QP pages 2-3 are "Data" and "Formulae": treat them like the Chemistry
  Periodic Table page (never part of a question). Appendix: the Data and
  Formulae pages, once, from the newest paper (replaces the Periodic Table).
- No chemistry-specific rules (data block "Important values...", Data
  Booklet note). Check every regex that mentions 9701.
- Tag every lowest-level part with a 2025-27 AS topic and learning outcome
  (topics 1-11). Most-marks rule for multi-topic parts; tie → topic of the
  first sub-part in a tied topic; log it.

## The book
- Units 1-11 (syllabus names). In each unit: Part B items (newest first), then
  the booklet items (newest first, booklet order within a year), one numbering.
  Answers Section after each unit, same order and numbers.
- Layout and front/back matter as in the Chemistry book: own cover (no
  Read & Write branding), contents with exact page numbers, unit title pages,
  running header, bookmarks, Topic index, Appendix (Data and Formulae).
- Each booklet item carries a small grey source tag "booklet (scan + OCR)";
  Part B items carry nothing extra.

## Deliverables (`Ω-physics/booklets/p2-topical-workbook/`)
Full book PDF; one PDF per unit (items + answers); index.csv (reference,
unit, marks, page, source = booklet|official, also_topics, context_parts);
items.jsonl (reference, unit, marks, page, source, text; booklet text is OCR,
say so); topics.json (Part B leaves; booklet items with their unit);
report.md; SUMMARY.md; booklet-ocr.pdf. Any file over 95 MB: don't push it,
note it in SUMMARY.md.

## Final self-check (repeat check → fix → rebuild until everything passes)
Adapt and run the relevant `hub/audit/scripts` checks on the physics book: paper
checks and coverage (Part B), item/index/items.jsonl/unit PDF consistency,
structure (contents, headers, bookmarks), crop checks (clipped text, figures,
furniture, visible dotted lines, page splits), self-containment (Part B),
file checks (qpdf, sizes). Visual: at least 15 Part B items (or all, if fewer)
and 5 booklet items per unit, plus every automated flag, viewed at a
readable dpi (≥ 90); the answers too. After every rebuild, re-run all checks,
not only the failed ones. Write `hub/audit/PHYSICS_CHECK.md` with every check: PASS / FAIL /
NOT RUN, with counts and the script used. Keep report.md and SUMMARY.md
accurate (no claim without a check behind it).

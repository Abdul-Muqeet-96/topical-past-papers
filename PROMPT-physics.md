# Prompt: build the Physics 9702 Paper 2 topical workbook

Paste this one line into a fresh session:

> Read PROMPT-physics.md and follow it exactly, unattended, to the end.

---

## Task

Build the Physics 9702 Paper 2 topical workbook described in `Ω-physics/CLAUDE-physics.md`, in
one unattended run. `Ω-physics/CLAUDE-physics.md` is the specification; if this prompt and the
specification ever disagree, follow the specification. Quality and accuracy come first;
cost is not a constraint. Never skip a check, a fix or a visual inspection to
save tokens. Still let scripts do the heavy lifting and print only counts and
short summaries.

## Setup
1. `git fetch origin main`, check it out, then create the branch
   `claude/physics-p2-booklet` from it. Work and push only there
   (`git push -u origin claude/physics-p2-booklet`; on network errors retry 4
   times with 2/4/8/16 s waits). Do not open a pull request. Do not touch
   `main` or the Chemistry files.
2. Install what is missing: `pip install pymupdf numpy`; tesseract (`apt-get
   install -y tesseract-ocr`) if `tesseract --version` fails; qpdf if missing.
3. Create `Ω-physics/state_physics.json` and update it after every stage.

## Stages (commit and push after each)
0. **Tooling and sources.** Copy `scripts/` to `scripts/physics/` and adapt it
   (subject code 9702, URLs, Data/Formulae pages, topics). Download and verify
   the Part B papers listed in the specification. Print a count table.
1. **OCR the booklet** (Part A, step 1 of the specification). Run it in the
   background, 4 parallel jobs; write `Ω-physics/booklet-ocr.pdf`. Check: the
   page count is 550 and a text search finds a known heading.
2. **Map the booklet**: units, item headings, answers, page spans, references
   (Part A, steps 2-5). Write `Ω-physics/work/booklet_items.json`. Print counts
   per unit and the number of headings read by image.
3. **Light check of the booklet** (Part A, step 6). Write the results to
   report.md.
4. **Part B**: paper checks, parts, topic tags (by reading the extracted
   text, written compactly to `Ω-physics/work/tags.txt`), items, context, marks.
5. **Build**: book, unit PDFs, index.csv, items.jsonl, topics.json,
   report.md, SUMMARY.md. Render 3 sample pages (cover/contents, a Part B
   page, a booklet page) and fix obvious problems.
6. **Self-check** (the final section of the specification): write
   `audit/PHYSICS_CHECK.md`, fix what failed, rebuild, and re-run all checks;
   repeat until everything passes or the remaining issue cannot be fixed
   (then report exactly why). Commit after each round.
7. **Finish**: update SUMMARY.md with what was done, counts per unit (Part A
   and Part B), files and sizes, and what is still open. Your final message:
   a compact summary table, the open issues, and the branch name.

## Rules that matter most
- Up to 2023: only the booklet (crops of the OCR'd scan). From 2024: official
  papers. Never retype content.
- When unsure about an item: keep the booklet item as it is (Part A), or
  exclude and report (Part B). Never guess.
- Wait for background jobs on a marker file or PID, not with `pgrep -f` on a
  pattern that also matches the waiting command itself.
- Stop only for the hard blockers in the specification; write STOPPED.md if you do.

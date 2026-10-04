# Prompt: build the Computer Science 9618 Paper 1 and Paper 2 workbooks

Paste this one line into a fresh session:

> Read PROMPT-cs.md and follow it exactly, unattended, to the end.

---

## Task
Build the two CS workbooks described in `λ-cs/CLAUDE-cs.md`, in one
unattended run. `λ-cs/CLAUDE-cs.md` is the specification; repo-wide rules are
in `CLAUDE.md`. If this prompt and the specification disagree, follow the
specification.

Quality and accuracy come first; cost is not a constraint. Never skip a
check, a fix or a visual inspection to save tokens. Don't waste effort
either: scripts do the heavy lifting, and you print only counts and short
summaries.

## Setup
1. `git fetch origin claude/audit-fixes` and check it out. Then create the
   branch `claude/cs-9618-booklets` from it.
   - Work and push only there: `git push -u origin claude/cs-9618-booklets`.
     On network errors, retry 4 times with waits of 2, 4, 8 and 16 s.
   - Do not open a pull request.
   - Do not touch `main`, or the Chemistry or Physics files.
2. Install what is missing: `pip install pymupdf numpy`, and qpdf.
3. Create `state_cs.json` and update it after every stage.

## Stages (commit and push after each)
0. **Tooling.** Copy `scripts/` to `scripts/cs/` and adapt it:
   - codes 9618/9608, variants 1x/2x, URLs and header titles;
   - inserts;
   - the paper-total check (75, not 60);
   - two books, with filing by topic across them;
   - remove the chemistry-only rules (Periodic Table, data block, Data
     Booklet).
   Then read `layout.md` and the Chemistry book's code. The CS layout is the
   same, with CS names.
1. **Downloads.** Download Phase 1 (9618) QPs, MSs and inserts; verify the
   headers; write `data/manifest_cs.json`. Print a count table, including
   unavailable papers.
2. **Paper checks** (the spec's paper-level verification). Log every failure
   in `λ-cs/report.md`.
3. **Parts and tags.** Split into parts and resolve context, including the
   identifier rule and the inserts. Tag every lowest-level part with a unit,
   section and learning outcome, by reading the extracted text, in compact
   files under `work/cs/`. Check every unit's tags against the syllabus wording.
4. **Phase 1 books.** Build both books, the unit PDFs, the index files,
   report.md and SUMMARY.md. Render sample pages (cover, contents, a P1 page,
   a P2 page with pseudocode, an answers page) and fix what is wrong. Commit
   this as the fallback.
5. **Phase 2 (9608).** Download and check. Tag against the 2027-29 syllabus.
   Exclude pre-release and out-of-syllabus parts, and list them. Rebuild both
   books with Phase 1 and Phase 2 together.
6. **Self-check** (the final section of the spec). Write `audit/CS_CHECK.md`,
   fix what failed, rebuild, and re-run all checks. Repeat until everything
   passes, or until a remaining issue cannot be fixed (then report exactly
   why). Commit after each round.
7. **Finish.** Update `λ-cs/SUMMARY.md`: papers, items and marks per unit for
   each book, files and sizes, and what is still open. Your final message: a
   compact summary table, the open issues, and the branch name.

## Rules that matter most
- Never retype or reconstruct content. When unsure, exclude and report.
- Every item must be solvable alone: stem, the figures/code/tables it
  mentions, the earlier parts it depends on, and the insert where it is used.
  Never leave a dangling reference.
- Wait for background jobs on a marker file or PID, never with `pgrep -f` on
  a pattern that also matches the waiting command itself.
- Stop only for the hard blockers in `CLAUDE.md`; write STOPPED.md if you do.

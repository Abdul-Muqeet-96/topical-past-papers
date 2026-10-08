# Repo rules: Cambridge topical workbooks

This repo builds part-level topical workbooks of Cambridge past papers. Each
book serves two readers: a student, and Claude Code teaching that student.
So every item must be readable as text (a text layer), not only as pixels.

| Subject | Spec | Run prompt | Output | Status |
|---|---|---|---|---|
| Chemistry 9701 P2 | `Δ-chemistry/reference/CLAUDE-chemistry.md` | (done) | `Δ-chemistry/booklets/p2-topical-workbook/` | finished, audited, fixed |
| Physics 9702 P2 | `Ω-physics/reference/CLAUDE-physics.md` | `hub/PROMPT-physics.md` | `Ω-physics/booklets/p2-topical-workbook/` | built |
| Computer Science 9618 P1 + P2 | `λ-cs/reference/CLAUDE-cs.md` | `hub/PROMPT-cs.md` | `λ-cs/booklets/p1-topical-workbook/`, `λ-cs/booklets/p2-topical-workbook/` | built |

Repo layout (root = four subject folders + `hub/`):
- `hub/scripts/` is the shared, audited pipeline. It currently reads and writes
  the Chemistry paths (`Δ-chemistry/build/work/`, `Δ-chemistry/reports/report.md`, ...).
- `hub/audit/` holds the Chemistry audit and its check scripts.
- `hub/data/` holds downloads (gitignored).
- `π-maths/` holds the maths syllabus only (no booklet yet).
- Each subject folder uses the same layout: `booklets/` (finished output),
  `reference/` (syllabus, spec `CLAUDE-<subject>.md`, layout.md), `reports/`
  (report.md, SUMMARY.md), `build/` (`work/`, `topics.json`, `state_<subject>.json`)
  and a README.md. The repo root holds only README.md, this file, `.gitignore`,
  the subject folders and `hub/` (run prompts live in `hub/`). Scripts run from the repo root.

A run follows its prompt and its subject spec. Never change another subject's
files, scripts or outputs; copy `hub/scripts/` to `hub/scripts/<subject>/` and adapt
it there. `hub/audit/` holds the Chemistry audit, whose scripts can be adapted for
a self-check.

## Rules for every run
- Unattended: don't ask questions. Apply the spec's defaults and log each in
  that book's report.md under "AUTO-DECIDED" (item, issue, what you did).
  Stop only for hard blockers (downloads all fail, tooling can't be installed,
  can't commit/push); then write STOPPED.md and end.
- Never retype, guess or reconstruct question or mark-scheme content. When
  unsure, exclude and report.
- Quality first. Never skip a check, a fix or a visual inspection to save
  tokens. Rebuild as often as needed. But don't waste effort either:
  - heavy work in Python scripts;
  - print counts and short summaries;
  - read images only where text or coordinates can't decide, and for the
    required visual checks;
  - batch fixes before a rebuild.
- Commit and push after every stage on the run's own branch, never main. Keep
  progress in `<subject folder>/state_<subject>.json` so a new session can
  resume. Change every path in the copied scripts to the subject's folder.
- Wait for background jobs on a marker file or a PID. Never use `pgrep -f`
  with a pattern that also matches the waiting command itself.
- Downloads go to `hub/data/` (gitignored). No third-party websites besides the
  past-paper source.

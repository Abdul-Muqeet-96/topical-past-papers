# Repo rules: Cambridge topical workbooks

This repo builds part-level topical workbooks of Cambridge past papers. Each
book serves two readers: a student, and Claude Code teaching that student.
So every item must be readable as text (a text layer), not only as pixels.

| Subject | Spec | Run prompt | Output | Status |
|---|---|---|---|---|
| Chemistry 9701 P2 | `Δ-chemistry/CLAUDE-chemistry.md` | (done) | `Δ-chemistry/p2-topical-workbook/` | finished, audited, fixed |
| Physics 9702 P2 | `Ω-physics/CLAUDE-physics.md` | `PROMPT-physics.md` | `Ω-physics/p2-topical-workbook/` | to build |
| Computer Science 9618 P1 + P2 | `λ-cs/CLAUDE-cs.md` | `PROMPT-cs.md` | `λ-cs/p1-topical-workbook/`, `λ-cs/p2-topical-workbook/` | to build |

A run follows its prompt and its subject spec. Never change another subject's
files, scripts or outputs; copy `scripts/` to `scripts/<subject>/` and adapt
it there. `audit/` holds the Chemistry audit, whose scripts can be adapted for
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
  progress in a `state_<subject>.json` so a new session can resume.
- Wait for background jobs on a marker file or a PID. Never use `pgrep -f`
  with a pattern that also matches the waiting command itself.
- Downloads go to `data/` (gitignored). No third-party websites besides the
  past-paper source.

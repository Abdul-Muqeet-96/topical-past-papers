# SUMMARY: Computer Science 9618 Paper 1 and Paper 2 part-level topical workbooks

Stages finished: 0, 1, 2, 3, 4 (see `λ-cs/state_cs.json`). Books contain: Phase 1 (9618), Phase 2 (9608).

## Papers

| | Phase 1 (9618) | Phase 2 (9608) | Total |
|---|---|---|---|
| Papers attempted | 84 | 98 | 182 |
| Not on the site | 24 | 26 | 50 |
| Downloaded and header-verified (QP + MS) | 60 | 70 | 130 |
| Inserts found | 31 | 0 | 31 |
| Papers passing the paper checks | 60 | 70 | 130 |
| Questions excluded (MS marks ≠ QP marks) | 1 | 3 | 4 |
| Questions included | 472 | 473 | 945 |
| Items in the books | 692 | 659 | 1351 |
| Marks in the books | 4492 | 4863 | 9355 |

## Paper 1 book: papers, items and marks per unit

| Unit | Papers | Items | Marks |
|---|---|---|---|
| 1 Information representation | 67 | 124 | 782 |
| 2 Communication | 53 | 64 | 491 |
| 3 Hardware | 59 | 110 | 650 |
| 4 Processor Fundamentals | 62 | 92 | 766 |
| 5 System Software | 80 | 96 | 563 |
| 6 Security, privacy and data integrity | 56 | 69 | 363 |
| 7 Ethics and Ownership | 42 | 49 | 236 |
| 8 Databases | 59 | 59 | 810 |
| **Total** | **89** | **663** | **4661** |

## Paper 2 book: papers, items and marks per unit

| Unit | Papers | Items | Marks |
|---|---|---|---|
| 9 Algorithm Design and Problem-solving | 64 | 145 | 848 |
| 10 Data Types and Structures | 63 | 182 | 1607 |
| 11 Programming | 62 | 198 | 1315 |
| 12 Software Development | 65 | 163 | 924 |
| **Total** | **65** | **688** | **4694** |

## Files produced

| File | Size |
|---|---|
| λ-cs/p1-topical-workbook/CS-9618-P1-Topical-Workbook.pdf (1101 pages) | 21.3 MB |
| λ-cs/p1-topical-workbook/units/Unit-01-Information-representation.pdf | 7.9 MB |
| λ-cs/p1-topical-workbook/units/Unit-02-Communication.pdf | 5.1 MB |
| λ-cs/p1-topical-workbook/units/Unit-03-Hardware.pdf | 6.7 MB |
| λ-cs/p1-topical-workbook/units/Unit-04-Processor-Fundamentals.pdf | 7.9 MB |
| λ-cs/p1-topical-workbook/units/Unit-05-System-Software.pdf | 7.8 MB |
| λ-cs/p1-topical-workbook/units/Unit-06-Security-privacy-and-data-integrity.pdf | 6.5 MB |
| λ-cs/p1-topical-workbook/units/Unit-07-Ethics-and-Ownership.pdf | 3.9 MB |
| λ-cs/p1-topical-workbook/units/Unit-08-Databases.pdf | 7.6 MB |
| λ-cs/p1-topical-workbook/index.csv | 28 KB |
| λ-cs/p1-topical-workbook/items.jsonl | 1.3 MB |
| λ-cs/p1-topical-workbook/topics.json | 0.7 MB |
| λ-cs/p2-topical-workbook/CS-9618-P2-Topical-Workbook.pdf (1516 pages) | 25.9 MB |
| λ-cs/p2-topical-workbook/units/Unit-09-Algorithm-Design-and-Problem-solving.pdf | 13.0 MB |
| λ-cs/p2-topical-workbook/units/Unit-10-Data-Types-and-Structures.pdf | 13.5 MB |
| λ-cs/p2-topical-workbook/units/Unit-11-Programming.pdf | 14.7 MB |
| λ-cs/p2-topical-workbook/units/Unit-12-Software-Development.pdf | 13.4 MB |
| λ-cs/p2-topical-workbook/index.csv | 29 KB |
| λ-cs/p2-topical-workbook/items.jsonl | 1.8 MB |
| λ-cs/p2-topical-workbook/topics.json | 0.5 MB |
| λ-cs/report.md | 78 KB |
| λ-cs/layout.md | 3 KB |

No file exceeds 95 MB, so everything is pushed. Per-unit PDFs keep the full book's page numbers (so they match index.csv).

## What is still open

Nothing is open that a further run could close from the files on the site. What a reader should know:

- **Two papers are not in the books.** 9608 O/N 17/P11: the question-paper file on the site is damaged (475 136 bytes, unreadable; the same bytes on a second download). 9608 O/N 18/P21: the cover of its mark-scheme file prints "Paper 1", so it fails the header check and the paper is excluded.
- **Four questions are excluded** because the mark scheme and the question paper give different marks (nothing is patched): 9618 M/J 25/P12 Q7; 9608 M/J 15/P23 Q1; 9608 O/N 17/P21 Q1 and O/N 17/P23 Q1. Details under "Paper-level verification failures" in report.md.
- **50 papers are not on the site**: every March series (2015-2026), 9618 M/J 22 and O/N 26, 9608 O/N 20, five of the six 9608 O/N 21 papers and 9608 O/N 15/P12. They are listed per series in report.md. 9608 M/J 17/P22: the mark-scheme file has no program-code appendix, although rows 5(b) and 6(a) refer to one; those rows are shown as printed.
- **143 parts of 9608 papers are out of the 2027-29 syllabus** and are listed in report.md, not printed.
- **Text layer, inherited from the source files.** On 7 question-paper pages the answer-line dots could not be taken out of the PDF text layer without moving other glyphs, and on 13 pages the footer words beside a mark could not; they are hidden in the picture and absent from items.jsonl, but a text search of the book PDF finds them. 20 crops carry control characters where the source font has no text code for a bullet. 19 fonts are not embedded in the source papers themselves and stay that way in the books (the standard PDF fonts).
- **Dotted lines.** The rule that tells an answer line (removed) from a gap to fill in code or in a sentence (kept) is a set of printed-form tests (AUTO-DECIDED, "Gaps to fill and answer lines"). The self-check finds no answer line left and no gap removed by that rule; a reader may still judge a single borderline line differently.
- **Unused space.** About 290 pages are less than 55 % full, because an item that fits on one page, a figure, and the line that introduces a figure are never split (counts in audit/CS_CHECK.md).
- **Tags.** Every part was tagged from its text against the 2027-29 learning outcomes, and every item was re-tagged blind in the self-check (10 disagreements, all read, no change). Where one part touches two units the choice follows the conventions in AUTO-DECIDED; such items carry an "also" note.


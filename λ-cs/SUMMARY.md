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
| Questions excluded (MS marks ≠ QP marks) | 1 | 5 | 6 |
| Questions included | 472 | 471 | 943 |
| Items in the books | 692 | 655 | 1347 |
| Marks in the books | 4492 | 4834 | 9326 |

## Paper 1 book: papers, items and marks per unit

| Unit | Papers | Items | Marks |
|---|---|---|---|
| 1 Information representation | 67 | 124 | 782 |
| 2 Communication | 53 | 64 | 491 |
| 3 Hardware | 59 | 110 | 650 |
| 4 Processor Fundamentals | 62 | 92 | 766 |
| 5 System Software | 80 | 96 | 563 |
| 6 Security, privacy and data integrity | 57 | 70 | 365 |
| 7 Ethics and Ownership | 42 | 49 | 236 |
| 8 Databases | 59 | 59 | 810 |
| **Total** | **90** | **664** | **4663** |

## Paper 2 book: papers, items and marks per unit

| Unit | Papers | Items | Marks |
|---|---|---|---|
| 9 Algorithm Design and Problem-solving | 63 | 144 | 837 |
| 10 Data Types and Structures | 63 | 180 | 1589 |
| 11 Programming | 62 | 196 | 1300 |
| 12 Software Development | 65 | 163 | 937 |
| **Total** | **65** | **683** | **4663** |

## Files produced

| File | Size |
|---|---|
| λ-cs/p1-topical-workbook/CS-9618-P1-Topical-Workbook.pdf (1126 pages) | 21.1 MB |
| λ-cs/p1-topical-workbook/units/Unit-01-Information-representation.pdf | 8.3 MB |
| λ-cs/p1-topical-workbook/units/Unit-02-Communication.pdf | 5.1 MB |
| λ-cs/p1-topical-workbook/units/Unit-03-Hardware.pdf | 6.7 MB |
| λ-cs/p1-topical-workbook/units/Unit-04-Processor-Fundamentals.pdf | 8.0 MB |
| λ-cs/p1-topical-workbook/units/Unit-05-System-Software.pdf | 7.9 MB |
| λ-cs/p1-topical-workbook/units/Unit-06-Security-privacy-and-data-integrity.pdf | 6.7 MB |
| λ-cs/p1-topical-workbook/units/Unit-07-Ethics-and-Ownership.pdf | 3.9 MB |
| λ-cs/p1-topical-workbook/units/Unit-08-Databases.pdf | 7.6 MB |
| λ-cs/p1-topical-workbook/index.csv | 28 KB |
| λ-cs/p1-topical-workbook/items.jsonl | 1.3 MB |
| λ-cs/p1-topical-workbook/topics.json | 0.7 MB |
| λ-cs/p2-topical-workbook/CS-9618-P2-Topical-Workbook.pdf (1537 pages) | 24.6 MB |
| λ-cs/p2-topical-workbook/units/Unit-09-Algorithm-Design-and-Problem-solving.pdf | 12.3 MB |
| λ-cs/p2-topical-workbook/units/Unit-10-Data-Types-and-Structures.pdf | 13.6 MB |
| λ-cs/p2-topical-workbook/units/Unit-11-Programming.pdf | 13.5 MB |
| λ-cs/p2-topical-workbook/units/Unit-12-Software-Development.pdf | 13.4 MB |
| λ-cs/p2-topical-workbook/index.csv | 29 KB |
| λ-cs/p2-topical-workbook/items.jsonl | 1.6 MB |
| λ-cs/p2-topical-workbook/topics.json | 0.5 MB |
| λ-cs/report.md | 61 KB |
| λ-cs/layout.md | 2 KB |

No file exceeds 95 MB, so everything is pushed. Per-unit PDFs keep the full book's page numbers (so they match index.csv).

## What is still open

- The run stopped during stage 5 (usage limit). Stages 6 (self-check, audit/CS_CHECK.md) and 7 were not run.
- Stage 5 state: both books are rebuilt with Phase 1 and Phase 2 together, but the Phase 2 pages have not been viewed yet (no render of a 9608 item, a 2015-16 running-text answer or an appended program-code appendix was inspected).
- `final_checks.py` on the combined build reports 4 unexplained coverage gaps: O/N 16/P11 Q4 (iii), (iv) and O/N 16/P13 Q4 (iii), (iv) (tagged out of syllabus). Not yet investigated; all other final checks are zero.
- The Phase 2 tag check list (203 flagged parts) was read and no tag changed, but this is not yet written into the Tagging section of report.md.
- Phase 2 exclusions so far: 2 papers (O/N 17/P11 damaged file, O/N 18/P21 MS header), 5 questions (MS marks ≠ QP marks), 2 items (9608 M/J 21/P21 Q2 a, b), and the out-of-syllabus parts listed in report.md. For M/J 17/P22 the mark scheme file has no program-code appendix although rows 5(b) and 6(a) refer to it.


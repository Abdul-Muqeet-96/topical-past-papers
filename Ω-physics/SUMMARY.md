# SUMMARY — Physics 9702 Paper 2 topical workbook

## What was done

- **Part A (booklet, papers up to 2023):** OCR of all 550 scanned pages (tesseract, 300 dpi); `booklet-ocr.pdf` = the original scans with every OCR word as invisible text; item and answer headings mapped (731 by OCR, 3 read by image, 18 numbers confirmed by image); items cropped from heading to heading with running headers and branding removed; light check against 55 official papers.
- **Part B (official papers):** O/N 2023 (absent from the booklet) and all 2024–2026 papers in the spec; paper checks, part-level items with official context, topic tags with 2025–27 learning outcomes, mark-scheme crops.
- **Book:** units 1–11 (syllabus names), Part B items then booklet items, newest first, one numbering, Answers Section after each unit, contents, bookmarks, Topic index, Data and Formulae appendix.

## Items per unit

| Unit | Part B items (marks) | Part A booklet items | Total |
|---|---|---|---|
| 1 Physical quantities and units | 24 (67) | 56 | 80 |
| 2 Kinematics | 20 (95) | 32 | 52 |
| 3 Dynamics | 34 (173) | 31 | 65 |
| 4 Forces, density and pressure | 26 (113) | 33 | 59 |
| 5 Work, energy and power | 23 (114) | 31 | 54 |
| 6 Deformation of solids | 22 (128) | 32 | 54 |
| 7 Waves | 23 (83) | 22 | 45 |
| 8 Superposition | 22 (147) | 33 | 55 |
| 9 Electricity | 22 (115) | 33 | 55 |
| 10 D.C. circuits | 21 (132) | 33 | 54 |
| 11 Particle physics | 23 (153) | 30 | 53 |
| **Total** | **260 (1320)** | **366** | **626** |

Book: 930 pages. Part B: 22 papers (24 attempted; s26 v21 has no mark scheme; O/N 25/P23 is identical to O/N 25/P21 and is not repeated).

## Files

| File | Size |
|---|---|
| Ω-physics/p2-topical-workbook/Physics-9702-P2-Topical-Workbook.pdf (930 pages) | 36.3 MB |
| Ω-physics/p2-topical-workbook/units/Unit-01-Physical-quantities-and-units.pdf | 6.4 MB |
| Ω-physics/p2-topical-workbook/units/Unit-02-Kinematics.pdf | 6.8 MB |
| Ω-physics/p2-topical-workbook/units/Unit-03-Dynamics.pdf | 8.2 MB |
| Ω-physics/p2-topical-workbook/units/Unit-04-Forces-density-and-pressure.pdf | 7.1 MB |
| Ω-physics/p2-topical-workbook/units/Unit-05-Work-energy-and-power.pdf | 5.8 MB |
| Ω-physics/p2-topical-workbook/units/Unit-06-Deformation-of-solids.pdf | 8.1 MB |
| Ω-physics/p2-topical-workbook/units/Unit-07-Waves.pdf | 5.7 MB |
| Ω-physics/p2-topical-workbook/units/Unit-08-Superposition.pdf | 7.1 MB |
| Ω-physics/p2-topical-workbook/units/Unit-09-Electricity.pdf | 6.2 MB |
| Ω-physics/p2-topical-workbook/units/Unit-10-DC-circuits.pdf | 6.6 MB |
| Ω-physics/p2-topical-workbook/units/Unit-11-Particle-physics.pdf | 5.8 MB |
| Ω-physics/p2-topical-workbook/index.csv | 23 KB |
| Ω-physics/p2-topical-workbook/items.jsonl | 1.1 MB |
| Ω-physics/topics.json | 0.4 MB |
| Ω-physics/booklet-ocr.pdf | 24.1 MB |
| Ω-physics/report.md | 27 KB |

No file exceeds 95 MB, so everything is pushed. Unit PDFs keep the book's page numbers (they match index.csv).

## Still open

1. **Missing booklet pages.** The scan lacks printed pages 96–97, 144–145, 313–314, 328–329, 534–535: 7 booklet items and 5 answers are lost, 4 items and 1 answer are cut short (marked in the book). A complete scan would restore them.
2. **Booklet marks** are not in index.csv / items.jsonl (OCR of the margin is not reliable enough); the crops show them.
3. **Booklet text layer** is OCR: good for search and for Claude, but formulas, subscripts and Greek letters are often misread. The page image is authoritative (items.jsonl says so per item).
4. **Flagged booklet items** (9 on electric fields, outside the 2025–27 AS syllabus) are kept with a note; two booklet duplicates (filed twice by the booklet) are kept with a note.
5. **Topic tags** (work/tags.txt, topics.json) were set by reading every part; worth a look: measurement parts inside topic-4 questions (density) and energy parts inside kinematics questions were tagged by what they test, which splits some questions across units.
6. **Repo size:** the book, unit PDFs and booklet-ocr.pdf are committed (see sizes above).


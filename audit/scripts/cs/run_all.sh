#!/bin/sh
# Run every automated check of the CS self-check, in order. Usage: run_all.sh [--probe]
# Output: audit/out/cs/run.log (and one JSON per check). The marker audit/out/cs/run.done is
# written when everything has finished.
cd "$(dirname "$0")"
O=../../out/cs
rm -f $O/run.done
{
  echo "== c10 sources";        python3 c10_sources.py $1 | tail -8
  echo "== c20 qp parse";       python3 c20_qp_parse.py | tail -6
  echo "== c21 ms parse";       python3 c21_ms_parse.py | tail -2
  echo "== c22 compare";        python3 c22_compare.py | tail -8
  echo "== c30 book parse";     python3 c30_book_parse.py | tail -2
  echo "== c31 coverage";       python3 c31_coverage.py | tail -6
  echo "== c40 three-way";      python3 c40_threeway.py | tail -8
  echo "== c50 structure";      python3 c50_structure.py | tail -6 | cut -c1-600
  echo "== c60 files";          python3 c60_files.py | tail -24
  echo "== c70 bands";          python3 c70_bands.py | grep -v "re-scaled" | tail -6
  echo "== c71 crops";          python3 c71_crops.py | tail -10
  echo "== c72 pixels P1";      python3 c72_pixels.py 1 | tail -10
  echo "== c72 pixels P2";      python3 c72_pixels.py 2 | tail -10
  echo "== c73 layout";         python3 c73_layout.py | tail -8 | cut -c1-300
  echo "== c74 marks";          python3 c74_marks.py | head -3
  echo "== c80 self-contained"; python3 c80_selfcontained.py | tail -8
  echo "== c91 blind re-tag";   python3 c91_blind_compare.py | tail -4 | cut -c1-300
} > $O/run.log 2>&1
touch $O/run.done

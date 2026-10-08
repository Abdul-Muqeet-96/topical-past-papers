#!/bin/bash
# Re-run every Physics self-check on the current build (order matters: book parse first).
set -e
cd "$(dirname "$0")/../.."
python3 scripts/physics/final_checks.py
for s in pc01_book pc02_threeway pc03_partb pc04_structure pc05_bands pc06_crops pc07_selfcontained; do
  echo "== $s"; python3 audit/physics/$s.py | tail -16
done
echo "== pc08_files"; bash audit/physics/pc08_files.sh

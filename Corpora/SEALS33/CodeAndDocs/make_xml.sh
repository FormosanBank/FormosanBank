#!/usr/bin/env bash
# make_xml.sh — rerun all post-scrape processing for Corpora/SEALS33.
#
# Executable form of the "Processing pipeline" section in ../README.md.
# SEALS33 is non-regenerable from source (the XML was hand-assembled by
# copy-and-paste from the 2024 SEALS conference website), so this script
# starts from the pristine POL-035 snapshot in
# CodeAndDocs/pre_correction_snapshot/XML/ and rebuilds the published
# XML/ from it, in order:
#
#   0. restore XML/ from the pre-correction snapshot
#   1. clean_xml           (original-tier cleaning, null-glyph canonicalization)
#   2. standardize --remove_accents
#                          (standard tier: copy of original + accent deletion
#                           + S-level null-unit removal)
#   3. add_phonology --orthography Ortho94
#
# Warning sidecars (cleaner_warnings.csv / standardize_warnings.csv) are
# per-run reports (POL-033): review them after a run, then delete; never
# commit them.
#
# Usage:
#   ./make_xml.sh [FORMOSANBANK_ROOT]
#
# The FormosanBank repo root defaults to the checkout this corpus lives in
# (two levels above the corpus directory); pass a path (or set the
# FORMOSANBANK_ROOT environment variable) to use another checkout's QC
# scripts. The script is idempotent: it always rebuilds from the snapshot.

set -euo pipefail

CODEDOCS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # .../CodeAndDocs
CORPUS="$(dirname "$CODEDOCS")"                            # corpus root
BANK="${1:-${FORMOSANBANK_ROOT:-$(cd "$CORPUS/../.." && pwd)}}"
BANK="$(cd "$BANK" && pwd)"
XML="$CORPUS/XML"
SNAPSHOT="$CODEDOCS/pre_correction_snapshot/XML"

PY="${PYTHON:-$BANK/.venv/bin/python}"
[[ -x "$PY" ]] || PY="$(command -v python3)"

[[ -d "$SNAPSHOT" ]] || { echo "missing POL-035 snapshot: $SNAPSHOT" >&2; exit 1; }

step() { printf '\n=== %s ===\n' "$*"; }

step "0. Restore XML/ from pre-correction snapshot"
rm -rf "$XML"
cp -r "$SNAPSHOT" "$XML"

step "1. clean_xml"
"$PY" "$BANK/QC/cleaning/clean_xml.py" --corpora_path "$XML"

step "2. standardize --remove_accents"
"$PY" "$BANK/QC/utilities/standardize.py" --remove_accents --corpora_path "$XML"

step "3. add_phonology --orthography Ortho94"
"$PY" "$BANK/QC/utilities/add_phonology.py" --corpora_path "$XML" --orthography Ortho94

step "Done. Review + delete any $XML/*_warnings.csv sidecars (POL-033)."

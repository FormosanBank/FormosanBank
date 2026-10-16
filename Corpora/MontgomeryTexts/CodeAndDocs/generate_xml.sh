#!/usr/bin/env bash
# generate_xml.sh — THE entry point for Corpora/MontgomeryTexts (POL-047).
#
#   1. generate_xml.py   corpus-local: builds the original tier from the
#                        pre-correction snapshot and splits the source's
#                        slashed word glosses per gloss_alternations.json
#   2. clean_xml.py      shared original-tier canonicalization (typographic
#                        quotes/dashes/tildes, null glyphs, entities)
#   3. standardize.py    shared: rebuilds the standard tier from the original
#                        through Amis_Montgomery_113.tsv — the letter
#                        correspondences Hsu Cheng-Wen "Akiw" identified for
#                        this text (ts->c, ?->', l->d, r->l, ř->r)
#   4. add_phonology.py  shared: original PHON from Orthographies/Montgomery/,
#                        standard PHON from Ortho113 (POL-003)
#
# All four shared steps run, so this corpus has no POL-047 step-order deviation
# to declare beyond the two noted below.
#
# --segmented-without-m-tier on step 3: this corpus prints morpheme hyphens
# (`na-romoal`, `saka-falo`) but publishes no M analysis, so C012's M-tier
# guard would otherwise leave segmentation in the standard tier. See the
# docstring on standardize.py's _apply_standard_hyphens.
#
# There is no apply_manual_edits.py step: the corpus has no manual_edits.xml.
# Hand corrections belong in the snapshot, which is the source of record; the
# one that has been made is recorded in source_discrepancies.md.
#
# Idempotent: XML/ is rebuilt from the snapshot on every run, so a re-run over
# a clean checkout leaves `git status` empty. Validators do not run here
# (POL-047, "build only"); run them from QC/ separately.
#
# Warning sidecars (cleaner_warnings.csv, standardize_warnings.csv) are per-run
# reports (POL-033): review them after a run, then delete; never commit them.
#
# Usage:
#   ./generate_xml.sh [FORMOSANBANK_ROOT]
#
# The repo root defaults to the checkout this corpus lives in; pass a path (or
# set FORMOSANBANK_ROOT) to use another checkout's QC scripts, and PYTHON to
# override the interpreter. Nothing outside this checkout is required (POL-048).

set -euo pipefail

CODEDOCS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORPUS="$(dirname "$CODEDOCS")"
BANK="${1:-${FORMOSANBANK_ROOT:-$(cd "$CORPUS/../.." && pwd)}}"
BANK="$(cd "$BANK" && pwd)"
XML="$CORPUS/XML"
SNAPSHOT="$CODEDOCS/pre_correction_snapshot/XML"
TABLE="$BANK/Orthographies/ConversionTables/Amis_Montgomery_113.tsv"

PY="${PYTHON:-$BANK/.venv/bin/python}"
[[ -x "$PY" ]] || PY="$(command -v python3)"

[[ -d "$SNAPSHOT" ]] || { echo "missing POL-035 snapshot: $SNAPSHOT" >&2; exit 1; }
[[ -f "$TABLE" ]] || { echo "missing conversion table: $TABLE" >&2; exit 1; }

step() { printf '\n=== %s ===\n' "$*"; }

step "1. generate_xml.py (snapshot -> XML/, slashed glosses split)"
"$PY" "$CODEDOCS/generate_xml.py" \
  --snapshot "$SNAPSHOT" \
  --alternations "$CODEDOCS/gloss_alternations.json" \
  --xml-dir "$XML"

step "2. clean_xml"
"$PY" "$BANK/QC/cleaning/clean_xml.py" --corpora_path "$XML"

step "3. standardize (Amis_Montgomery_113.tsv)"
"$PY" "$BANK/QC/utilities/standardize.py" \
  --tsv_path "$TABLE" \
  --corpora_path "$XML" \
  --segmented-without-m-tier

step "4. add_phonology (original: Orthographies/Montgomery)"
"$PY" "$BANK/QC/utilities/add_phonology.py" \
  --orthography Montgomery \
  --corpora_path "$XML"

step "Done. Review + delete any $XML/*_warnings.csv sidecars (POL-033)."

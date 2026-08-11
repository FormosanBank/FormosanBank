#!/usr/bin/env bash
# make_xml.sh — regenerate Virginia_Fey_Dictionary/XML/ from the POL-035
# pre-correction snapshot.
#
# This corpus is NON-REGENERABLE from source (the XML is itself the
# hand-cleaned product), so the reproduction baseline is the snapshot at
# CodeAndDocs/pre_correction_snapshot/ (POL-035). Taking that snapshot is
# NOT a pipeline step — it was made once, before automated corrections
# first touched this corpus (2026-08-11), and per POL-038 it changes only
# via committed scripts (fix_duplicate_ids.py has been applied to it).
#
# Pipeline (see ../README.md for per-step explanations):
#   0. restore XML/ from the snapshot (baseline)
#   1. fix_duplicate_ids.py       — already applied to the snapshot, so this
#                                   run is an idempotent no-op guard
#   2. clean_xml.py               — original-tier cleaning (+ Amis quote-
#                                   correction arming)
#   3. standardize.py --remove_accents  — standard tier: copy original,
#                                   strip accents, remove S-level null units
#   4. add_phonology.py --orthography Ortho113 — regenerate PHON tiers
#   5. remove_duplicate_sentences.py --apply — dedup (reference resource,
#                                   POL-022; declared here, so leftover
#                                   duplicates are HARD findings)
#
# Usage:
#   ./make_xml.sh [FORMOSANBANK_ROOT]
#
# FORMOSANBANK_ROOT defaults to the repo this corpus sits in
# (../../.. relative to this script). Override it (or set PYTHON) to run
# the pipeline with another checkout's QC scripts.

set -euo pipefail

CODEDOCS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # .../CodeAndDocs
CORPUS="$(dirname "$CODEDOCS")"                            # corpus root
BANK="${1:-$(cd "$CORPUS/../.." && pwd)}"                  # FormosanBank root
SNAPSHOT="$CODEDOCS/pre_correction_snapshot"
XML="$CORPUS/XML"

PY="${PYTHON:-$BANK/.venv/bin/python}"
[[ -x "$PY" ]] || PY="$(command -v python3)"

step() { printf '\n=== %s ===\n' "$*"; }

[[ -d "$SNAPSHOT" ]] || { echo "ERROR: snapshot missing at $SNAPSHOT" >&2; exit 1; }

step "0. Restore XML/ from POL-035 snapshot"
rm -rf "$XML"
mkdir -p "$XML"
cp -r "$SNAPSHOT/." "$XML/"

step "1. fix_duplicate_ids (no-op guard; fix already lives in the snapshot)"
"$PY" "$CODEDOCS/fix_duplicate_ids.py" --path "$XML"

step "2. clean_xml"
"$PY" "$BANK/QC/cleaning/clean_xml.py" --corpora_path "$XML"

step "3. standardize --remove_accents"
"$PY" "$BANK/QC/utilities/standardize.py" --remove_accents --corpora_path "$XML"

step "4. add_phonology (Ortho113)"
"$PY" "$BANK/QC/utilities/add_phonology.py" --corpora_path "$XML" --orthography Ortho113

step "5. remove_duplicate_sentences (POL-022 dedup)"
"$PY" "$BANK/QC/cleaning/remove_duplicate_sentences.py" by_path --path "$XML" --apply

step "Done"
echo "Review any warning sidecars (cleaner_warnings.csv, standardize_warnings.csv;"
echo "POL-033: per-run reports, never committed) and CodeAndDocs/quote_corrections.csv"
echo "(durable log — commit if rows were added)."

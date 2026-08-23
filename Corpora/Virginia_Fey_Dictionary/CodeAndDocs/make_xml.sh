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
#   2. reconcile_source.py        — reviewed source/metadata corrections,
#                                   complete POL-027 expansion, and exact
#                                   translation-field provenance
#   3. clean_xml.py               — original-tier cleaning (+ Amis quote-
#                                   correction arming)
#   4. standardize.py --remove_accents  — standard tier: copy original,
#                                   strip accents, remove S-level null units
#   5. add_phonology.py --orthography Ortho113 — regenerate PHON tiers
#   6. audit_source_alignment.py --stage pre-dedup — all 2,051 source
#                                   units present and source-faithful
#   7. remove_duplicate_sentences.py --apply — dedup (reference resource,
#                                   POL-022; declared here, so leftover
#                                   duplicates are HARD findings)
#   8. audit_source_alignment.py --stage canonical — exact declared
#                                   dedup state and full source accounting
#
# Usage:
#   ./make_xml.sh [FORMOSANBANK_ROOT]
#
# FORMOSANBANK_ROOT is auto-detected when this corpus is embedded under
# FormosanBank/Corpora/ or sits beside a FormosanBank checkout. Pass it
# explicitly (or set PYTHON) for any other layout.

set -euo pipefail

CODEDOCS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # .../CodeAndDocs
CORPUS="$(dirname "$CODEDOCS")"                            # corpus root
SNAPSHOT="$CODEDOCS/pre_correction_snapshot"
XML="$CORPUS/XML"

if [[ $# -gt 0 ]]; then
    BANK="$(cd "$1" && pwd)"
elif [[ -d "$CORPUS/../../QC" ]]; then
    BANK="$(cd "$CORPUS/../.." && pwd)"
elif [[ -d "$CORPUS/../FormosanBank/QC" ]]; then
    BANK="$(cd "$CORPUS/../FormosanBank" && pwd)"
else
    echo "ERROR: cannot locate FormosanBank; pass FORMOSANBANK_ROOT" >&2
    exit 1
fi

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

step "2. reconcile source coverage, metadata, forms, and translations"
"$PY" "$CODEDOCS/reconcile_source.py" --path "$XML/Amis/Amis.xml"

step "3. clean_xml"
"$PY" "$BANK/QC/cleaning/clean_xml.py" --corpora_path "$XML"

step "4. standardize --remove_accents"
"$PY" "$BANK/QC/utilities/standardize.py" --remove_accents --corpora_path "$XML"

step "5. add_phonology (Ortho113)"
"$PY" "$BANK/QC/utilities/add_phonology.py" --corpora_path "$XML" --orthography Ortho113

step "6. source alignment before dedup"
"$PY" "$CODEDOCS/audit_source_alignment.py" --stage pre-dedup --path "$XML/Amis/Amis.xml"

step "7. remove_duplicate_sentences (POL-022 dedup)"
"$PY" "$BANK/QC/cleaning/remove_duplicate_sentences.py" by_path --path "$XML" --apply

step "8. canonical source alignment"
"$PY" "$CODEDOCS/audit_source_alignment.py" --stage canonical --path "$XML/Amis/Amis.xml"

step "Done"
echo "Review any warning sidecars (cleaner_warnings.csv, standardize_warnings.csv;"
echo "POL-033: per-run reports, never committed) and CodeAndDocs/quote_corrections.csv"
echo "(durable log — commit if rows were added)."

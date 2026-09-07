#!/usr/bin/env bash
# generate_xml.sh — THE entry point for Corpora/WakelinTexts (POL-047).
#
#   1. generate_xml.py   corpus-local: builds the original tier from the
#                        pre-correction snapshot and resolves the source's
#                        slash alternations per alternative_decisions.json
#   2. clean_xml.py      shared original-tier canonicalization (typographic
#                        quotes/dashes/tildes, null glyphs, entities)
#
# Steps 4 and 5 of the POL-047 shape — standardize.py and add_phonology.py —
# are DELIBERATELY ABSENT, and this is the deviation POL-047 requires a corpus
# to state. This text's orthography has never been identified: the article
# names no writing system and the transcription matches no profile in
# ../../../Orthographies/. A `standard` FORM asserts that a text has been
# transliterated into FormosanBank's common orthography and a PHON asserts a
# pronunciation; we can support neither, so the corpus publishes only what the
# article prints. See ../README.md, "What you get: the original tier only".
#
# There is no apply_manual_edits.py step: the corpus has no manual_edits.xml.
# Hand corrections belong in the snapshot, which is the source of record.
#
# Idempotent: XML/ is rebuilt from the snapshot on every run, so a re-run over
# a clean checkout leaves `git status` empty. Validators do not run here
# (POL-047, "build only"); run them from QC/ separately.
#
# Warning sidecars (cleaner_warnings.csv) are per-run reports (POL-033):
# review them after a run, then delete; never commit them. This corpus
# currently produces none.
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
SNAPSHOT="$CODEDOCS/pre_correction_snapshot"

PY="${PYTHON:-$BANK/.venv/bin/python}"
[[ -x "$PY" ]] || PY="$(command -v python3)"

[[ -d "$SNAPSHOT" ]] || { echo "missing POL-035 snapshot: $SNAPSHOT" >&2; exit 1; }

step() { printf '\n=== %s ===\n' "$*"; }

step "1. generate_xml.py (snapshot -> XML/, alternations resolved)"
rm -rf "$XML"
"$PY" "$CODEDOCS/generate_xml.py" \
  --snapshot "$SNAPSHOT" \
  --decisions "$CODEDOCS/alternative_decisions.json" \
  --xml-dir "$XML" \
  --gloss-report "$CODEDOCS/gloss_alignment_review.tsv"

step "2. clean_xml"
"$PY" "$BANK/QC/cleaning/clean_xml.py" --corpora_path "$XML"

step "Done. Review + delete any $XML/*_warnings.csv sidecars (POL-033)."

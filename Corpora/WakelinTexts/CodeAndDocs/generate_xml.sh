#!/usr/bin/env bash
# generate_xml.sh — THE entry point for Corpora/WakelinTexts (POL-047).
#
#   1. generate_xml.py         corpus-local: builds the original tier from the
#                              pre-correction snapshot and resolves the
#                              source's slash alternations per
#                              alternative_decisions.json
#   2. clean_xml.py            shared original-tier canonicalization
#                              (typographic quotes/dashes/tildes, null glyphs,
#                              entities)
#   3. resolve_parentheses.py  corpus-local: resolves the article's ( ) in the
#                              original tier, before any derived tier is built
#   4. standardize.py          builds the standard tier
#                              (Yami_Wakelin_113.tsv)
#   5. apply_r_caron_words.py  corpus-local: the five 'r-caron' words
#   6. add_phonology.py        PHON for both tiers (Wakelin profile for
#                              original, Ortho113 for standard)
#
# The numbers above are THIS SCRIPT's. POL-047's canonical steps are a
# different sequence and the two do not line up: POL-047 is 1 generate_xml.py,
# 2 apply_manual_edits.py, 3 clean_xml.py, 4 standardize.py,
# 5 add_phonology.py. So POL-047 step 3 is local step 2, POL-047 step 4 is
# local step 4 (coincidence), and POL-047 step 5 is local step 6.
#
# POL-047 deviation: two corpus-local steps are interleaved with the shared
# ones, and one of them sits in a position POL-047 does not contemplate.
#
#   - Local step 3 (resolve_parentheses.py) runs between clean and standardize,
#     so every derived tier is built from an original that carries no
#     parenthesis (POL-028). See ../README.md, pipeline step 3.
#   - Local step 5 (apply_r_caron_words.py) runs BETWEEN POL-047 steps 4 and 5
#     — before add_phonology.py, where POL-047 says a corpus-local corrections
#     script "belongs after step 5". It must run before, because PHON is
#     generated from the standard tier and has to reflect the corrected words.
#     It also edits the standard tier outside standardize.py, which POL-002
#     otherwise reserves to that tool, on the maintainer ruling of 2026-09-07.
#     See ../README.md, pipeline step 5, for the cost that ruling accepted.
#
# There is no apply_manual_edits.py step (POL-047 step 2): the corpus has no
# manual_edits.xml. Hand corrections belong in the snapshot, which is the
# source of record.
#
# Superseded 2026-09-10 (POL-050): this header used to state that POL-047 steps
# 4 and 5 were "DELIBERATELY ABSENT" because the 1958 orthography had never
# been identified, so the corpus published only the original tier. That was
# true until 282c49e31 (2026-09-08) profiled the orthography and added both
# tiers. The corpus now publishes 2189 standard FORMs and 4378 PHONs; the claim
# was simply left behind, and the deviation it declared no longer exists.
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

step "3. resolve_parentheses (original tier; standardize derives the rest)"
"$PY" "$CODEDOCS/resolve_parentheses.py" --xml-dir "$XML"

step "4. standardize (Wakelin -> Ortho113)"
"$PY" "$BANK/QC/utilities/standardize.py" \
  --corpora_path "$XML" \
  --tsv_path "$BANK/Orthographies/ConversionTables/Yami_Wakelin_113.tsv" \
  --segmented-without-m-tier

step "5. apply_r_caron_words (standard tier only)"
"$PY" "$CODEDOCS/apply_r_caron_words.py" \
  --xml-dir "$XML" --words "$CODEDOCS/r_caron_words.tsv"

step "6. add_phonology (Wakelin profile for original, Ortho113 for standard)"
"$PY" "$BANK/QC/utilities/add_phonology.py" \
  --corpora_path "$XML" --orthography Wakelin

step "Done. Review + delete any $XML/*_warnings.csv sidecars (POL-033)."

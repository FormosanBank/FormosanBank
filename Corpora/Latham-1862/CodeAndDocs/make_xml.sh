#!/usr/bin/env bash
# make_xml.sh — Latham-1862 maintenance pipeline.
#
# Rebuilds the published XML/ from the POL-035 pre-correction snapshot, in
# the canonical order:
#
#   0. restore XML/ from CodeAndDocs/pre_correction_snapshot/
#   1. clean_xml            character-level canonicalization of the original
#                           tier (a verified no-op on this corpus)
#   2. drop_derived_tiers   delete every FORM[@kindOf="standard"] and every
#                           PHON, at S, W and M level, leaving the original
#                           tier alone
#
# It does NOT rebuild the XML from the source ledger — for that, run
# build_lexical_xml.py first (see README "Reproduce"); its output is
# byte-identical to the snapshot this script restores from.
#
# Step 2 is why this pipeline exists, so it is worth stating why a corpus
# would throw a derived tier away. Latham 1862 is a 19th-century comparative
# wordlist in Babuza-Favorlang (bzg) and Siraya (fos). A `standard` FORM
# asserts that the text has been transliterated into FormosanBank's common
# orthography, and neither variety has one it could be transliterated into:
# Siraya is under a standing ruling not to standardize to Ortho113 or
# anything else for now, and both varieties' standard_orthography cells in
# the repo-root standards.csv are blank. So the published corpus carries
# only what Latham
# prints. How (or whether) to standardize this material is an open question
# tracked outside the repo.
#
# The snapshot does contain a standard tier — 62 S-level FORMs, a verbatim
# `standardize.py --copy` of the original (letter-for-letter identical,
# diacritics included), i.e. a tier asserting a standardization nobody
# performed. The snapshot is never edited (POL-038); the tier is removed on
# the way out of it, by committed code, on every run. There is
# correspondingly no standardize step here any more.
#
# There is also no add_phonology step, BY DESIGN: a historical lexical table
# with no living pronunciation reference gets no PHON tier (see README
# "Extraction Decisions"). drop_derived_tiers enforces that as an invariant
# rather than leaving it to hold by accident.
#
# Usage:
#   bash CodeAndDocs/make_xml.sh [FORMOSANBANK_ROOT]
#
# FORMOSANBANK_ROOT defaults to the repository root containing this corpus
# (i.e. ../../.. from this script). The interpreter is $PYTHON if set in the
# environment, else the FormosanBank root's .venv if present, else python3.
# The script is idempotent: it always rebuilds from the snapshot.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORPUS_DIR="$(dirname "$SCRIPT_DIR")"                 # Corpora/Latham-1862
BANK_ROOT="${1:-$(cd "$CORPUS_DIR/../.." && pwd)}"    # FormosanBank root

if [ -z "${PYTHON:-}" ]; then
    PYTHON="$BANK_ROOT/.venv/bin/python"
    if [ ! -x "$PYTHON" ]; then
        PYTHON="python3"
    fi
fi

XML_DIR="$CORPUS_DIR/XML"
SNAPSHOT="$SCRIPT_DIR/pre_correction_snapshot"

echo "== Latham-1862 make_xml.sh =="
echo "FormosanBank root: $BANK_ROOT"
echo "Corpus XML:        $XML_DIR"

[ -d "$SNAPSHOT" ] || { echo "missing POL-035 snapshot: $SNAPSHOT" >&2; exit 1; }

# Step 0 — restore XML/ from the POL-035 pre-correction snapshot, so every
# run starts from the same fixed baseline and the pipeline is reproducible
# and idempotent rather than an in-place edit of published data (POL-038).
echo "-- Step 0: restore XML/ from pre_correction_snapshot"
rm -rf "$XML_DIR"
cp -r "$SNAPSHOT" "$XML_DIR"

# Step 1 — clean_xml: character-level cleaning of the original tier
# (entity decoding, dash/quote/null-glyph normalization, ...). Expected to
# be a no-op here: the hand transcription is already clean ASCII + the
# meaningful historical diacritics. bzg/fos have no attestation
# dictionaries, and the corpus has zero apostrophes, so the quote-glottal
# correction machinery never arms (Phase A consolidated review).
"$PYTHON" "$BANK_ROOT/QC/cleaning/clean_xml.py" \
    --corpora_path "$XML_DIR"

# Step 2 — drop_derived_tiers: delete every FORM[@kindOf="standard"] and
# every PHON (see the header for why). The original and alternate tiers are
# left untouched. This replaces the former `standardize.py --copy` step.
"$PYTHON" "$SCRIPT_DIR/drop_derived_tiers.py" \
    --corpora_path "$XML_DIR" --bank "$BANK_ROOT"

echo "== make_xml.sh done =="

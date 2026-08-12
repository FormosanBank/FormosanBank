#!/usr/bin/env bash
# make_xml.sh — Latham-1862 maintenance pipeline.
#
# Runs FormosanBank's cleaning/standardization pipeline over this corpus's
# published XML/, in the canonical order. It does NOT rebuild the XML from
# the source ledger — for that, run build_lexical_xml.py first (see README
# "Reproduce"); this script is the maintenance pass applied to XML/.
#
# Usage:
#   bash CodeAndDocs/make_xml.sh [FORMOSANBANK_ROOT]
#
# FORMOSANBANK_ROOT defaults to the repository root containing this corpus
# (i.e. ../../.. from this script). The interpreter is $PYTHON if set in the
# environment, else the FormosanBank root's .venv if present, else python3.
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

echo "== Latham-1862 make_xml.sh =="
echo "FormosanBank root: $BANK_ROOT"
echo "Corpus XML:        $XML_DIR"

# Step 1 — clean_xml: character-level cleaning of the original tier
# (entity decoding, dash/quote/null-glyph normalization, ...). Expected to
# be a no-op here: the hand transcription is already clean ASCII + the
# meaningful historical diacritics. bzg/fos have no attestation
# dictionaries, and the corpus has zero apostrophes, so the quote-glottal
# correction machinery never arms (Phase A consolidated review).
"$PYTHON" "$BANK_ROOT/QC/cleaning/clean_xml.py" \
    --corpora_path "$XML_DIR"

# Step 2 — standardize --copy: regenerate the standard tier as a verbatim
# copy of the original tier. No TSV conversion table exists for these
# historical varieties, so no letter conversion is applied, and Latham's
# diacritics are meaningful historical attestations, so no accents are
# removed: the standard tier is letter-for-letter identical to the original.
"$PYTHON" "$BANK_ROOT/QC/utilities/standardize.py" --copy \
    --corpora_path "$XML_DIR"

# No add_phonology step, BY DESIGN: a historical lexical table with no
# living pronunciation reference gets no PHON tier (see README "Extraction
# Decisions").

echo "== make_xml.sh done =="

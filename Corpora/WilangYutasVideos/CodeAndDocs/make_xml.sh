#!/usr/bin/env bash
# make_xml.sh — WilangYutasVideos post-scrape pipeline.
#
# Runs every post-scrape processing step, in order, over the published
# XML/ directory of this corpus:
#
#   1. clean_xml.py            — character/punctuation canonicalization
#   2. standardize.py --remove_accents
#                              — rebuild the standard tier: copy of the
#                                original with accents (acute/breve) deleted;
#                                no conversion table exists for this corpus
#   3. add_phonology.py --orthography Ortho94
#                              — regenerate PHON tiers (Ortho94 assumed; see
#                                README)
#
# The scrape itself (scripts/scrape.py) and the initial XML generation from
# the committed raw_scrape/ transcripts (scripts/make_xml.py, which writes to
# Final_XML/ in the dev-repo layout) are NOT run here — see the README's
# reproduction notes. Audio is never touched.
#
# Usage:
#   ./make_xml.sh [FORMOSANBANK_ROOT]
#
# FORMOSANBANK_ROOT defaults to $FORMOSANBANK_ROOT, else the repository this
# corpus sits in (three levels up from CodeAndDocs/). Set PYTHON to pick an
# interpreter (default: python3 on PATH — activate the repo .venv first).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORPUS_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BANK="${1:-${FORMOSANBANK_ROOT:-$(cd "${SCRIPT_DIR}/../../.." && pwd)}}"
XML_DIR="${CORPUS_DIR}/XML"
PY="${PYTHON:-python3}"

for p in "${BANK}/QC/cleaning/clean_xml.py" "${XML_DIR}"; do
    [ -e "$p" ] || { echo "make_xml.sh: not found: $p" >&2; exit 1; }
done

echo "== FormosanBank root: ${BANK}"
echo "== Corpus XML:        ${XML_DIR}"

echo "== Step 1/3: clean_xml.py"
"${PY}" "${BANK}/QC/cleaning/clean_xml.py" --corpora_path "${XML_DIR}"

echo "== Step 2/3: standardize.py --remove_accents"
"${PY}" "${BANK}/QC/utilities/standardize.py" --remove_accents --corpora_path "${XML_DIR}"

echo "== Step 3/3: add_phonology.py --orthography Ortho94"
"${PY}" "${BANK}/QC/utilities/add_phonology.py" --corpora_path "${XML_DIR}" --orthography Ortho94

echo "== Done. Review and delete any warning sidecars under ${XML_DIR} (POL-033):"
found=0
for f in "${XML_DIR}/cleaner_warnings.csv" "${XML_DIR}/standardize_warnings.csv"; do
    [ -e "$f" ] && { echo "   $f"; found=1; }
done
[ "$found" -eq 1 ] || echo "   (none present)"

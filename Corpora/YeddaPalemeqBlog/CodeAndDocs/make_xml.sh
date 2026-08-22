#!/usr/bin/env bash
# Rebuild Corpora/YeddaPalemeqBlog/XML from the committed scrape output.
#
# Usage: CodeAndDocs/make_xml.sh [FORMOSANBANK_ROOT]
#   FORMOSANBANK_ROOT  FormosanBank checkout to take QC scripts from
#                      (env FORMOSANBANK_ROOT, default: the checkout this
#                      corpus lives in)
#   PYTHON             interpreter override (default: $FORMOSANBANK_ROOT/.venv)
#
# Idempotent: every step is a function of committed inputs, so re-running
# reproduces XML/ byte-for-byte. No data file is ever edited by hand
# (POL-038); the /-and-() hand corrections live in manual_edits.xml and are
# re-applied by step 2 (POL-030).
#
# CodeAndDocs/raw_xml/ is refreshed only by re-scraping the blog, which is a
# separate, network-dependent operation and is NOT part of this script:
#     python CodeAndDocs/Scripts/download_html.py     # -> html_cache/
#     python CodeAndDocs/analyze_blog_structure.py --generate-xml
# (needs beautifulsoup4; it is in requirements.txt but an existing .venv
# may predate that pin.)

set -euo pipefail

CORPUS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEFAULT_ROOT="$(cd "$CORPUS_DIR/../.." && pwd)"
ROOT="${1:-${FORMOSANBANK_ROOT:-$DEFAULT_ROOT}}"
PY="${PYTHON:-$ROOT/.venv/bin/python}"

XML_DIR="$CORPUS_DIR/XML"
RAW_DIR="$CORPUS_DIR/CodeAndDocs/raw_xml"

echo "== 0. restore XML/ from the committed scrape output =="
rm -rf "$XML_DIR"
cp -R "$RAW_DIR" "$XML_DIR"

echo "== 1. clean_xml: entity decode, punctuation/Unicode canonicalization =="
"$PY" "$ROOT/QC/cleaning/clean_xml.py" --corpora_path "$XML_DIR"

echo "== 2. apply_manual_edits: the /-and-() hand corrections =="
"$PY" "$ROOT/QC/cleaning/apply_manual_edits.py" --corpora_path "$XML_DIR"

echo "== 3. fix_m_tier: M tier only where the source actually parses (POL-023) =="
"$PY" "$CORPUS_DIR/CodeAndDocs/fix_m_tier.py" --corpora_path "$XML_DIR" \
    --formosanbank_root "$ROOT"

echo "== 4. standardize: standard tier = original minus accents =="
"$PY" "$ROOT/QC/utilities/standardize.py" --remove_accents --corpora_path "$XML_DIR"

echo "== 5. add_phonology: IPA for both tiers (Ortho113) =="
"$PY" "$ROOT/QC/utilities/add_phonology.py" --corpora_path "$XML_DIR" --orthography Ortho113

echo "== done =="

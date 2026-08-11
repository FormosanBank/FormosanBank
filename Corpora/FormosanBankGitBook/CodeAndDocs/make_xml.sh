#!/usr/bin/env bash
set -euo pipefail

# make_xml.sh — run ALL post-scrape pipeline steps, in order, over this
# corpus's published XML/ directory. This is the executable form of the
# pipeline; the per-step explanations live in ../README.md (which remains
# the reference for what each step does and why).
#
# Steps:
#   1. QC/cleaning/clean_xml.py
#   2. QC/utilities/standardize.py --remove_accents
#   3. QC/utilities/add_phonology.py --orthography Ortho113
#
# Usage (from anywhere; paths are resolved from this script's location):
#   ./make_xml.sh [FORMOSANBANK_ROOT]
#
#   FORMOSANBANK_ROOT  a FormosanBank checkout providing the QC scripts.
#                      Default: the repository enclosing this corpus.
#   PYTHON             (env var) interpreter to use. Default: the
#                      FormosanBank root's .venv python if present,
#                      else python3.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORPUS_DIR="$(dirname "$SCRIPT_DIR")"
XML_DIR="$CORPUS_DIR/XML"

FB_ROOT="${1:-$(git -C "$CORPUS_DIR" rev-parse --show-toplevel)}"
FB_ROOT="$(cd "$FB_ROOT" && pwd)"

if [ -z "${PYTHON:-}" ]; then
    if [ -x "$FB_ROOT/.venv/bin/python" ]; then
        PYTHON="$FB_ROOT/.venv/bin/python"
    else
        PYTHON=python3
    fi
fi

echo "== FormosanBankGitBook post-scrape pipeline =="
echo "corpus:           $CORPUS_DIR"
echo "FormosanBank root: $FB_ROOT"
echo "python:           $PYTHON"

echo "-- step 1/3: clean_xml"
"$PYTHON" "$FB_ROOT/QC/cleaning/clean_xml.py" --corpora_path "$XML_DIR"

echo "-- step 2/3: standardize --remove_accents"
"$PYTHON" "$FB_ROOT/QC/utilities/standardize.py" --corpora_path "$XML_DIR" --remove_accents

echo "-- step 3/3: add_phonology --orthography Ortho113"
"$PYTHON" "$FB_ROOT/QC/utilities/add_phonology.py" --corpora_path "$XML_DIR" --orthography Ortho113

echo "== done =="

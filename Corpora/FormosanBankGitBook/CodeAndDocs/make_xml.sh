#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
CORPUS_DIR=$(dirname "$SCRIPT_DIR")
FORMOSANBANK_ROOT=${1:-$(git -C "$CORPUS_DIR" rev-parse --show-toplevel)}
PYTHON=${PYTHON:-python3}

WORK=$(mktemp -d "${TMPDIR:-/tmp}/formosan-gitbook-paiwan.XXXXXX")
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$WORK/reports" "$WORK/published"

"$PYTHON" "$SCRIPT_DIR/process_raw.py" --output "$WORK/XML/Paiwan"
"$PYTHON" "$FORMOSANBANK_ROOT/QC/cleaning/clean_xml.py" \
    --corpora_path "$WORK/XML"
"$PYTHON" "$SCRIPT_DIR/source_audit.py" \
    --repo "$SCRIPT_DIR" --xml "$WORK/XML/Paiwan" --apply
"$PYTHON" "$FORMOSANBANK_ROOT/QC/utilities/standardize.py" \
    --corpora_path "$WORK/XML" --copy
"$PYTHON" "$FORMOSANBANK_ROOT/QC/utilities/add_phonology.py" \
    --corpora_path "$WORK/XML" --orthography Ortho113
"$PYTHON" "$SCRIPT_DIR/source_audit.py" \
    --repo "$SCRIPT_DIR" --xml "$WORK/XML/Paiwan" --require-generated
rm -f "$WORK/XML/cleaner_warnings.csv"

"$PYTHON" "$FORMOSANBANK_ROOT/QC/validation/validate_xml.py" \
    --published-corpora "$WORK/published" \
    --csv "$WORK/reports/validate_xml.csv" \
    by_path --path "$WORK/XML/Paiwan"
"$PYTHON" "$FORMOSANBANK_ROOT/QC/validation/validate_text.py" \
    --csv "$WORK/reports/validate_text.csv" \
    by_path --path "$WORK/XML/Paiwan"
"$PYTHON" "$FORMOSANBANK_ROOT/QC/validation/validate_glosses.py" \
    --csv "$WORK/reports/validate_glosses.csv" \
    by_path --path "$WORK/XML/Paiwan"

diff -ru "$CORPUS_DIR/XML/Paiwan" "$WORK/XML/Paiwan"
printf 'Reproduced 6 XML files and 105 source-aligned records byte-for-byte.\n'

#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
FB="${FORMOSANBANK_ROOT:-$(cd "$HERE/../../.." && pwd)}"
PY="${PYTHON:-python3}"
test -f "$FB/QC/cleaning/clean_xml.py"
"$PY" "$HERE/build_xml.py"
"$PY" "$FB/QC/cleaning/apply_manual_edits.py" --corpora_path "$ROOT/XML"
"$PY" "$FB/QC/cleaning/clean_xml.py" --corpora_path "$ROOT/XML"
"$PY" "$FB/QC/utilities/standardize.py" --corpora_path "$ROOT/XML" \
    --tsv_path "$HERE/wu_source_to_ortho113.tsv" --target_column standard
"$PY" "$FB/QC/utilities/add_phonology.py" --corpora_path "$ROOT/XML" \
    --language Amis --orthography "$HERE/source_orthography"

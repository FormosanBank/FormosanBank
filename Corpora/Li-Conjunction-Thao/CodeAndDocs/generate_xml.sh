#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
FB="${FORMOSANBANK_ROOT:-$(cd "$HERE/../../.." && pwd)}"
PY="${PYTHON:-python3}"

test -f "$FB/QC/cleaning/clean_xml.py"
"$PY" "$HERE/scripts/build_xml.py"
"$PY" "$FB/QC/cleaning/clean_xml.py" --corpora_path "$ROOT/XML"
"$PY" "$FB/QC/utilities/standardize.py" --corpora_path "$ROOT/XML" \
    --tsv_path "$FB/Orthographies/ConversionTables/Thao_Li_113.tsv" \
    --target_column standard --hard-remove-segmentation
"$PY" "$HERE/scripts/flatten_standard_segmentation.py" "$ROOT/XML"
"$PY" "$FB/QC/utilities/add_phonology.py" --corpora_path "$ROOT/XML" --orthography Li

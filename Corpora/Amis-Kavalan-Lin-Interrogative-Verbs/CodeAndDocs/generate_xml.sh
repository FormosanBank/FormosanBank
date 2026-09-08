#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
FB="${FORMOSANBANK_ROOT:-$(cd "$HERE/../../.." && pwd)}"
PY="${PYTHON:-python3}"
test -f "$FB/QC/cleaning/clean_xml.py"
"$PY" "$HERE/build_xml.py"
if [[ -f "$HERE/manual_edits.xml" ]]; then
    "$PY" "$FB/QC/cleaning/apply_manual_edits.py" --corpora_path "$ROOT/XML"
fi
"$PY" "$FB/QC/cleaning/clean_xml.py" --corpora_path "$ROOT/XML"
"$PY" "$FB/QC/utilities/standardize.py" --corpora_path "$ROOT/XML/Amis" \
    --tsv_path "$HERE/Orthographies/ConversionTables/Amis_LinAmis_113.tsv" --target_column Xiuguluan
"$PY" "$FB/QC/utilities/standardize.py" --corpora_path "$ROOT/XML/Kavalan" \
    --remove_accents
"$PY" "$FB/QC/utilities/add_phonology.py" --corpora_path "$ROOT/XML/Amis" \
    --orthography "$HERE/Orthographies/LinAmis"
"$PY" "$FB/QC/utilities/add_phonology.py" --corpora_path "$ROOT/XML/Kavalan" --orthography Ortho113
"$PY" "$HERE/build_xml.py" --restore-brackets

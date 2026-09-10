#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
FB="${FORMOSANBANK_ROOT:-$(cd "$HERE/../../.." && pwd)}"
PY="${PYTHON:-python3}"

test -f "$FB/QC/cleaning/clean_xml.py"
"$PY" "$HERE/process_raw.py"
"$PY" "$FB/QC/cleaning/clean_xml.py" --corpora_path "$ROOT/XML" --warnings_dir "$HERE"
"$PY" "$FB/QC/utilities/standardize.py" --corpora_path "$ROOT/XML" --remove_accents
"$PY" "$FB/QC/utilities/add_phonology.py" --corpora_path "$ROOT/XML" --orthography Ortho113

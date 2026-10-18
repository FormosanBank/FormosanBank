#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
FB="${FORMOSANBANK_ROOT:-$(cd "$HERE/../../.." && pwd)}"
PY="${PYTHON:-python3}"

test -f "$FB/QC/cleaning/clean_xml.py"
"$PY" "$HERE/build_lexical_xml.py"
"$PY" "$FB/QC/cleaning/clean_xml.py" --corpora_path "$ROOT/XML"

# The August 12 corpus ruling omits standard FORM and all PHON.

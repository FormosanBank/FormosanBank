#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
FB="${FORMOSANBANK_ROOT:-$(cd "$HERE/../../.." && pwd)}"
PY="${PYTHON:-python3}"

test -f "$FB/QC/cleaning/clean_xml.py"
"$PY" "$HERE/build_xml.py"
"$PY" "$FB/QC/cleaning/clean_xml.py" --corpora_path "$ROOT/XML"
"$PY" "$FB/QC/utilities/standardize.py" --corpora_path "$ROOT/XML" \
    --tsv_path "$FB/Orthographies/ConversionTables/Rukai_Huteson_113.tsv"
"$PY" "$FB/QC/utilities/add_phonology.py" --corpora_path "$ROOT/XML" \
    --orthography Huteson

# Standard gloss tier (POL-036, additive): Glossing/ConversionTables/Huteson-Rukai-Survey.tsv
"$PY" "$FB/QC/glossing/apply_gloss_standard.py" \
    --path "$ROOT/XML" \
    --table "$FB/Glossing/ConversionTables/Huteson-Rukai-Survey.tsv" \
    --rules "$FB/Glossing/ConversionTables/Huteson-Rukai-Survey.rules.tsv" --write

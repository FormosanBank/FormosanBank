#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
FB="${FORMOSANBANK_ROOT:-$(cd "$HERE/../../.." && pwd)}"
PY="${PYTHON:-python3}"
test -f "$FB/QC/cleaning/clean_xml.py"
"$PY" "$HERE/build_xml.py"
"$PY" "$FB/QC/cleaning/apply_manual_edits.py" --corpora_path "$ROOT/XML"
# --warnings_dir keeps the per-run cleaner report out of published XML/
# (POL-033); without it the default lands it inside the data.
"$PY" "$FB/QC/cleaning/clean_xml.py" --corpora_path "$ROOT/XML" \
    --warnings_dir "$HERE/reports"
# Wu's spelling is Coastal Ortho94, so both tables are the bank's existing
# shared ones (POL-046) — no corpus-local copies, and the rule-application
# sweep already covers them. Amis_94_113.tsv is a per-dialect table with no
# `standard` column, so the target column is the dialect: passing `standard`
# matches nothing and silently skips the conversion.
"$PY" "$FB/QC/utilities/standardize.py" --corpora_path "$ROOT/XML" \
    --tsv_path "$FB/Orthographies/ConversionTables/Amis_94_113.tsv" \
    --target_column Coastal
"$PY" "$FB/QC/utilities/add_phonology.py" --corpora_path "$ROOT/XML" \
    --language Amis --orthography "$FB/Orthographies/Ortho94"

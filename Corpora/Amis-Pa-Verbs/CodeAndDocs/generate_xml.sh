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
# The conversion table and the source orthography are registered under
# Orthographies/ (POL-056), not kept corpus-local: a table outside
# ConversionTables/ escapes the rule-application sweep and derives no
# capital-letter variants.
"$PY" "$FB/QC/utilities/standardize.py" --corpora_path "$ROOT/XML" \
    --tsv_path "$FB/Orthographies/ConversionTables/Amis_Wu_113.tsv" \
    --target_column standard
"$PY" "$FB/QC/utilities/add_phonology.py" --corpora_path "$ROOT/XML" \
    --language Amis --orthography "$FB/Orthographies/Wu"

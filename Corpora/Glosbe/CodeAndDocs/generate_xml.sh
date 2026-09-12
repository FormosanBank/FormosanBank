#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
FB="${FORMOSANBANK_ROOT:-$(cd "$HERE/../../.." && pwd)}"
PY="${PYTHON:-python3}"
XML="$ROOT/XML"
CT="$FB/Orthographies/ConversionTables"

test -f "$FB/QC/cleaning/clean_xml.py"
"$PY" "$HERE/process_source.py" --formosanbank-root "$FB"
"$PY" "$FB/QC/cleaning/apply_manual_edits.py" --corpora_path "$XML"
(cd "$ROOT" && "$PY" "$FB/QC/cleaning/clean_xml.py" --corpora_path XML ${QC_OUTPUT_DIR:+--warnings_dir "$QC_OUTPUT_DIR"})
"$PY" "$HERE/process_source.py" --apply-aliases "$FB"
"$PY" "$FB/QC/cleaning/remove_duplicate_sentences.py" by_path --path "$XML" --tier original --scope file --apply
"$PY" "$FB/QC/utilities/standardize.py" --tsv_path "$CT/Amis_94_113.tsv" --target_column Coastal --corpora_path "$XML/Amis"
"$PY" "$FB/QC/utilities/standardize.py" --tsv_path "$CT/Atayal_Church_113.tsv" --target_column standard --corpora_path "$XML/Atayal"
"$PY" "$FB/QC/utilities/standardize.py" --tsv_path "$CT/Seediq_94_113.tsv" --target_column Truku --corpora_path "$XML/Truku"
"$PY" "$FB/QC/utilities/standardize.py" --tsv_path "$CT/Saisiyat_94_113.tsv" --target_column standard --corpora_path "$XML/Saisiyat"
"$PY" "$FB/QC/utilities/add_phonology.py" --orthography Ortho94 --target_column Coastal --corpora_path "$XML/Amis"
"$PY" "$FB/QC/utilities/add_phonology.py" --orthography Church --corpora_path "$XML/Atayal"
"$PY" "$FB/QC/utilities/add_phonology.py" --orthography Ortho94 --corpora_path "$XML/Truku"
"$PY" "$FB/QC/utilities/add_phonology.py" --orthography Ortho94 --corpora_path "$XML/Saisiyat"
"$PY" "$HERE/process_source.py" --record-provenance "$FB"

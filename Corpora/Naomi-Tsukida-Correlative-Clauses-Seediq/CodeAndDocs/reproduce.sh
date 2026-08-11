#!/usr/bin/env bash
set -euo pipefail

code_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
corpus_root="$(cd "$code_root/.." && pwd -P)"
formosanbank_path="${FORMOSANBANK_PATH:-$(cd "$corpus_root/../.." && pwd -P)}"
formosanbank_path="$(cd "$formosanbank_path" && pwd -P)"
python_bin="${FORMOSANBANK_PYTHON:-$formosanbank_path/.venv/bin/python3}"
xml_path="$corpus_root/XML"
evidence="$code_root/evidence"
snapshot="$(mktemp -d "${TMPDIR:-/tmp}/tsukida-seediq-published.XXXXXX")"

cleanup() {
    rm -rf -- "$snapshot"
}
trap cleanup EXIT

run_pipeline() {
    "$python_bin" "$code_root/scripts/build_xml.py"
    "$python_bin" "$formosanbank_path/QC/cleaning/apply_manual_edits.py" \
        --corpora_path "$xml_path"
    "$python_bin" "$formosanbank_path/QC/cleaning/clean_xml.py" \
        --corpora_path "$xml_path"
    for warning in cleaner_warnings.csv standardize_warnings.csv; do
        if [[ -f "$xml_path/$warning" ]]; then
            cp "$xml_path/$warning" "$snapshot/$warning"
            rm -- "$xml_path/$warning"
        fi
    done
    "$python_bin" "$code_root/scripts/restore_source_notation.py" \
        --path "$xml_path"
    "$python_bin" "$formosanbank_path/QC/validation/validate_conversion_table.py" \
        "$code_root/raw_data/tsukida_source_orthography.tsv" \
        "$formosanbank_path/Orthographies/Ortho113/Seediq.tsv" \
        "$code_root/raw_data/source_to_ortho113.tsv" --dialect Truku \
        --output "$snapshot/conversion_table.md"
    "$python_bin" "$formosanbank_path/QC/utilities/standardize.py" \
        --tsv_path "$code_root/raw_data/source_to_ortho113.tsv" \
        --target_column standard --corpora_path "$xml_path"
    "$python_bin" "$formosanbank_path/QC/utilities/add_phonology.py" \
        --corpora_path "$xml_path" --orthography Ortho94
    "$python_bin" "$code_root/scripts/check_source_alignment.py"
    "$python_bin" "$formosanbank_path/QC/validation/validate_xml.py" \
        --no-exit-on-hard --csv "$snapshot/validate_xml.csv" \
        --published-corpora "$formosanbank_path/Corpora" \
        by_path --path "$xml_path"
    "$python_bin" "$formosanbank_path/QC/validation/validate_text.py" \
        --no-exit-on-hard --csv "$snapshot/validate_text.csv" \
        by_path --path "$xml_path"
    "$python_bin" "$formosanbank_path/QC/validation/validate_glosses.py" \
        --no-exit-on-hard --csv "$snapshot/validate_glosses.csv" \
        by_path --path "$xml_path"
    "$python_bin" - "$snapshot" <<'PY'
import csv
import sys
from pathlib import Path

for name in ("validate_xml.csv", "validate_text.csv", "validate_glosses.csv"):
    with (Path(sys.argv[1]) / name).open(encoding="utf-8-sig", newline="") as handle:
        hard = [row for row in csv.DictReader(handle) if row["severity"] == "HARD"]
    if hard:
        raise SystemExit(f"{name}: {len(hard)} HARD finding(s)")
PY
}

run_pipeline
cp -R "$xml_path" "$snapshot/XML"
cp "$evidence"/{page_inventory.csv,source_alignment_summary.json,source_ledger.csv,source_notation_audit.csv,xml_source_map.csv} "$snapshot/"

run_pipeline
diff -ru "$snapshot/XML" "$xml_path"
for file in page_inventory.csv source_alignment_summary.json source_ledger.csv source_notation_audit.csv xml_source_map.csv; do
    cmp "$snapshot/$file" "$evidence/$file"
done

echo "Published-layout two-pass reproduction and current validators passed."

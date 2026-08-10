#!/usr/bin/env bash
set -euo pipefail

code_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
corpus_root="$(cd "$code_root/.." && pwd -P)"
formosanbank_path="${FORMOSANBANK_PATH:?Set FORMOSANBANK_PATH to a clean FormosanBank checkout}"
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
    "$python_bin" "$formosanbank_path/QC/utilities/standardize.py" \
        --tsv_path "$code_root/raw_data/source_to_ortho113.tsv" \
        --target_column standard --corpora_path "$xml_path"
    "$python_bin" "$code_root/scripts/normalize_standard_sentences.py" \
        --path "$xml_path"
    "$python_bin" "$formosanbank_path/QC/cleaning/clean_xml.py" \
        --corpora_path "$xml_path" --ortho-path "$formosanbank_path/Orthographies/Ortho113"
    "$python_bin" "$code_root/scripts/restore_source_notation.py" \
        --path "$xml_path"
    "$python_bin" "$formosanbank_path/QC/utilities/add_phonology.py" \
        --corpora_path "$xml_path"
    "$python_bin" "$code_root/scripts/normalize_phonology.py" \
        --path "$xml_path"
    "$python_bin" "$code_root/scripts/check_source_alignment.py"
    "$python_bin" "$formosanbank_path/QC/validation/validate_xml.py" \
        by_path --path "$xml_path"
    "$python_bin" "$formosanbank_path/QC/validation/validate_text.py" \
        by_path --path "$xml_path" --no-exit-on-hard \
        --csv "$snapshot/validate_text.csv"
    "$python_bin" "$formosanbank_path/QC/validation/validate_glosses.py" \
        by_path --path "$xml_path" --output_dir "$snapshot/glosses" --no-exit-on-hard
}

run_pipeline
cp -R "$xml_path" "$snapshot/XML"
cp "$evidence"/{page_inventory.csv,source_alignment_summary.json,source_ledger.csv,source_notation_audit.csv,xml_source_map.csv} "$snapshot/"

run_pipeline
diff -ru "$snapshot/XML" "$xml_path"
for file in page_inventory.csv source_alignment_summary.json source_ledger.csv source_notation_audit.csv xml_source_map.csv; do
    cmp "$snapshot/$file" "$evidence/$file"
done

echo "Published-layout reproduction, source alignment, and validators passed."

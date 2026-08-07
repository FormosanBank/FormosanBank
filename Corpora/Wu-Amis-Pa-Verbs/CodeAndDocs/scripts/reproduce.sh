#!/usr/bin/env bash
set -euo pipefail

corpus_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
repo_root="$(cd "$corpus_root/../.." && pwd -P)"
formosanbank_path="${FORMOSANBANK_PATH:-$repo_root}"
formosanbank_path="$(cd "$formosanbank_path" && pwd -P)"
python_bin="${FORMOSANBANK_PYTHON:-$formosanbank_path/.venv/bin/python3}"
expected_formosanbank_commit="14442ea6894e6cff561c6504fbf42ddd873cd14b"
temp_root="$(mktemp -d "${TMPDIR:-/tmp}/wu-amis-pa-verbs.XXXXXX")"
export PYTHONDONTWRITEBYTECODE=1

cleanup() {
    rm -rf -- "$temp_root"
}
trap cleanup EXIT

test -x "$python_bin"
test "$(git -C "$formosanbank_path" rev-parse HEAD)" = "$expected_formosanbank_commit"
test -z "$(git -C "$formosanbank_path" status --porcelain)"

mkdir -p "$temp_root/Final_XML" "$temp_root/CodeAndDocs" "$temp_root/qc"
cp "$corpus_root/CodeAndDocs/manual_edits.xml" "$temp_root/CodeAndDocs/manual_edits.xml"

"$python_bin" "$corpus_root/CodeAndDocs/scripts/build_xml.py" \
    --output "$temp_root/Final_XML/pa-verbs.xml"
"$python_bin" "$formosanbank_path/QC/cleaning/apply_manual_edits.py" \
    --corpora_path "$temp_root/Final_XML"
"$python_bin" "$formosanbank_path/QC/cleaning/clean_xml.py" \
    --corpora_path "$temp_root/Final_XML" \
    --ortho-path "$formosanbank_path/Orthographies/Ortho113"
"$python_bin" "$formosanbank_path/QC/utilities/standardize.py" \
    --copy --corpora_path "$temp_root/Final_XML"
"$python_bin" "$formosanbank_path/QC/cleaning/clean_xml.py" \
    --corpora_path "$temp_root/Final_XML" \
    --ortho-path "$formosanbank_path/Orthographies/Ortho113"
"$python_bin" "$formosanbank_path/QC/utilities/add_phonology.py" \
    --corpora_path "$temp_root/Final_XML"

"$python_bin" "$corpus_root/CodeAndDocs/scripts/audit_source_alignment.py" \
    --xml "$temp_root/Final_XML/pa-verbs.xml"
"$python_bin" "$formosanbank_path/QC/validation/validate_xml.py" by_path \
    --path "$temp_root/Final_XML" --csv "$temp_root/qc/validate_xml.csv"
"$python_bin" "$formosanbank_path/QC/validation/validate_text.py" by_path \
    --path "$temp_root/Final_XML" --csv "$temp_root/qc/validate_text.csv"
"$python_bin" "$formosanbank_path/QC/validation/validate_glosses.py" by_path \
    --path "$temp_root/Final_XML" --csv "$temp_root/qc/validate_glosses.csv"
"$python_bin" "$formosanbank_path/QC/validation/validate_duplicate_sentences.py" by_path \
    --path "$temp_root/Final_XML" --tier original \
    --output "$temp_root/qc/duplicate_original.csv"
"$python_bin" "$formosanbank_path/QC/validation/validate_duplicate_sentences.py" by_path \
    --path "$temp_root/Final_XML" --tier standard \
    --output "$temp_root/qc/duplicate_standard.csv"

cmp "$temp_root/Final_XML/pa-verbs.xml" "$corpus_root/XML/Amis/pa-verbs.xml"
test "$(git -C "$formosanbank_path" rev-parse HEAD)" = "$expected_formosanbank_commit"
test -z "$(git -C "$formosanbank_path" status --porcelain)"
echo "Reproduction passed: rebuilt XML byte-matches the published corpus."

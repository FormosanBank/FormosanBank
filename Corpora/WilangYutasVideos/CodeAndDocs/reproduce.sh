#!/usr/bin/env bash
set -euo pipefail

code_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
corpus_root="$(cd "$code_root/.." && pwd)"
formosanbank_root="$(cd "$corpus_root/../.." && pwd)"
python_bin="${PYTHON:-python3}"
expected_tools_commit="3a3c47c220520113f747e6a2d441494000e13c4b"

if [[ ! -x "$(command -v "$python_bin")" ]]; then
    echo "Python is not executable: $python_bin" >&2
    exit 2
fi
if ! git -C "$formosanbank_root" merge-base --is-ancestor \
    "$expected_tools_commit" HEAD; then
    echo "Required FormosanBank tooling commit is not an ancestor of HEAD." >&2
    exit 2
fi
tool_paths=(
    QC/cleaning/clean_xml.py
    QC/utilities/standardize.py
    QC/utilities/add_phonology.py
    QC/validation/reference/Atayal
)
if ! git -C "$formosanbank_root" diff --quiet \
    "$expected_tools_commit" -- "${tool_paths[@]}"; then
    echo "Required FormosanBank tooling differs from the reviewed commit." >&2
    exit 2
fi

snapshot_dir="$(mktemp -d /tmp/wilang-public-rebuild.XXXXXX)"
cleanup() {
    rm -rf "$snapshot_dir"
}
trap cleanup EXIT

write_hashes() {
    local output="$1"
    find XML -type f -name '*.xml' -print0 \
        | sort -z \
        | xargs -0 shasum -a 256 > "$output"
}

run_build() {
    "$python_bin" CodeAndDocs/make_xml.py
    "$python_bin" CodeAndDocs/audit_source_alignment.py
    "$python_bin" "$formosanbank_root/QC/cleaning/clean_xml.py" \
        --corpora_path XML \
        --reference_dir "$formosanbank_root/QC/validation/reference"

    if [[ ! -f XML/cleaner_warnings.csv ]]; then
        echo "Cleaner did not produce its warning artifact." >&2
        exit 1
    fi
    perl -pi -e 's/\r$//' XML/cleaner_warnings.csv
    expected_warning='c007,XML/Atayal/20190407_Yutas_Wilang_di4duan_Lowsing_Watan_MVI_1702_yiwancheng.xml,Atayal_28,ㄇ,113,,'
    if [[ "$(wc -l < XML/cleaner_warnings.csv)" -ne 2 ]] || \
        ! grep -Fxq "$expected_warning" XML/cleaner_warnings.csv; then
        echo "Cleaner warnings differ from the reviewed C007 finding:" >&2
        cat XML/cleaner_warnings.csv >&2
        exit 1
    fi
    rm XML/cleaner_warnings.csv

    "$python_bin" "$formosanbank_root/QC/utilities/standardize.py" \
        --corpora_path XML --copy
    "$python_bin" "$formosanbank_root/QC/utilities/add_phonology.py" \
        --corpora_path XML --orthography Ortho94
    "$python_bin" -m unittest discover -s CodeAndDocs \
        -p test_pipeline.py -v
}

cd "$corpus_root"
write_hashes "$snapshot_dir/before.sha256"
run_build
write_hashes "$snapshot_dir/first.sha256"
diff -u "$snapshot_dir/before.sha256" "$snapshot_dir/first.sha256"
run_build
write_hashes "$snapshot_dir/second.sha256"
diff -u "$snapshot_dir/first.sha256" "$snapshot_dir/second.sha256"

echo "Reproduced 82 Wilang Yutas XML files in two byte-identical passes."

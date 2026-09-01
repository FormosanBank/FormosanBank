#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

code_docs="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
corpus="$(dirname "$code_docs")"
bank="${1:-${FORMOSANBANK_PATH:-$(cd "$corpus/../.." && pwd -P)}}"
bank="$(cd "$bank" && pwd -P)"
python_bin="${PYTHON:-$bank/.venv/bin/python}"
if [[ ! -x "$python_bin" ]]; then
    python_bin="$(command -v python3)"
fi

scratch_xml="$code_docs/XML"
intermediate="$code_docs/intermediate"
cleanup() {
    rm -rf -- "$scratch_xml" "$intermediate"
}
trap cleanup EXIT
cleanup

"$python_bin" "$code_docs/scripts/build_xml.py"
"$python_bin" "$bank/QC/cleaning/clean_xml.py" --corpora_path "$scratch_xml"
"$python_bin" "$code_docs/scripts/restore_source_notation.py" --path "$scratch_xml"
"$python_bin" "$bank/QC/utilities/standardize.py" \
    --tsv_path "$code_docs/raw_data/source_to_ortho113.tsv" \
    --target_column standard --corpora_path "$scratch_xml"
"$python_bin" "$bank/QC/utilities/add_phonology.py" \
    --corpora_path "$scratch_xml" --orthography Ortho94
for warning in cleaner_warnings.csv standardize_warnings.csv; do
    [[ ! -f "$scratch_xml/$warning" ]] || {
        echo "Unexpected warning sidecar: $scratch_xml/$warning" >&2
        exit 1
    }
done

install -d "$corpus/XML/Seediq"
cp "$scratch_xml/Seediq/tsukida_2014_correlative_clauses_in_seediq.xml" \
    "$corpus/XML/Seediq/"

echo "Rebuilt Tsukida Seediq XML from the reviewed source tables."

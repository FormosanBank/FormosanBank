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

"$python_bin" "$code_docs/build_from_reviewed_ledger.py"
"$python_bin" "$bank/QC/cleaning/clean_xml.py" --corpora_path "$corpus/XML"
"$python_bin" "$bank/QC/utilities/standardize.py" \
    --tsv_path "$code_docs/wu_source_to_ortho113.tsv" \
    --target_column standard --corpora_path "$corpus/XML"
"$python_bin" "$bank/QC/utilities/add_phonology.py" \
    --corpora_path "$corpus/XML" --language Amis \
    --orthography "$bank/Orthographies/Ortho94"
for warning in cleaner_warnings.csv standardize_warnings.csv; do
    [[ ! -f "$corpus/XML/$warning" ]] || {
        echo "Unexpected warning sidecar: $corpus/XML/$warning" >&2
        exit 1
    }
done
echo "Rebuilt Wu Amis XML from the reviewed source ledger."

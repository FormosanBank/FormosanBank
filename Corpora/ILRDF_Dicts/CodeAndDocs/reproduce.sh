#!/usr/bin/env bash
set -euo pipefail

EXPECTED_AUTHORITY_COMMIT="3a3c47c220520113f747e6a2d441494000e13c4b"
CODEDOCS="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CORPUS="$(dirname "$CODEDOCS")"
AUTHORITY="${FORMOSANBANK_AUTHORITY:?Set FORMOSANBANK_AUTHORITY to the pinned FormosanBank authority checkout}"
PYTHON="${FORMOSANBANK_PYTHON:-python3}"
XML_PATH="$CORPUS/XML"

actual_commit="$(git -C "$AUTHORITY" rev-parse HEAD)"
if [[ "$actual_commit" != "$EXPECTED_AUTHORITY_COMMIT" ]]; then
    echo "Authority commit mismatch: expected $EXPECTED_AUTHORITY_COMMIT, found $actual_commit" >&2
    exit 1
fi
test -z "$(git -C "$AUTHORITY" status --porcelain)"

reference_dir="$(mktemp -d)"
trap 'rm -rf -- "$reference_dir"' EXIT

cd "$CODEDOCS"

"$PYTHON" "$CODEDOCS/generate_xml.py" generate
"$PYTHON" "$AUTHORITY/QC/utilities/standardize.py" \
    --corpora_path "$XML_PATH" \
    --tsv_path "$CODEDOCS/source_data/standardization.tsv" \
    --target_column standard \
    --ortho-path "$AUTHORITY/Orthographies/Ortho113"
"$PYTHON" "$AUTHORITY/QC/cleaning/clean_xml.py" \
    --corpora_path "$XML_PATH" \
    --reference_dir "$reference_dir"
"$PYTHON" "$CODEDOCS/generate_xml.py" restore-source
"$PYTHON" "$AUTHORITY/QC/utilities/add_phonology.py" \
    --corpora_path "$XML_PATH"
"$PYTHON" "$CODEDOCS/generate_xml.py" audit

rm -f -- \
    "$XML_PATH/cleaner_warnings.csv" \
    "$XML_PATH/html_entities.log" \
    "$XML_PATH/standardize_warnings.csv"

"$PYTHON" -m unittest discover -s "$CODEDOCS/tests"
test "$(git -C "$AUTHORITY" rev-parse HEAD)" = "$EXPECTED_AUTHORITY_COMMIT"
test -z "$(git -C "$AUTHORITY" status --porcelain)"
echo "Rebuilt and verified $XML_PATH"

#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
source "$(dirname "${BASH_SOURCE[0]}")/formosanbank_path.sh"
python_bin="${FORMOSANBANK_PYTHON:-$formosanbank_path/.venv/bin/python3}"
snapshot="$(mktemp -d "${TMPDIR:-/tmp}/seediq-chang-reproduce.XXXXXX")"

cleanup() {
    rm -rf -- "$snapshot"
}
trap cleanup EXIT

cd "$repo_root"
test "$(wc -l <CodeAndDocs/source_inventory.tsv | tr -d ' ')" = 354

FORMOSANBANK_PATH="$formosanbank_path" FORMOSANBANK_PYTHON="$python_bin" \
    bash CodeAndDocs/generate_xml.sh
FORMOSANBANK_PATH="$formosanbank_path" FORMOSANBANK_PYTHON="$python_bin" \
    bash CodeAndDocs/validate.sh
cp -R XML "$snapshot/XML"
cp CodeAndDocs/extracted_examples.tsv "$snapshot/extracted_examples.tsv"
cp CodeAndDocs/rejected_candidates.tsv "$snapshot/rejected_candidates.tsv"
cp CodeAndDocs/deduplicated_variants.tsv "$snapshot/deduplicated_variants.tsv"
cp CodeAndDocs/chapter5_inventory.tsv "$snapshot/chapter5_inventory.tsv"
cp CodeAndDocs/source_alignment_audit.md "$snapshot/source_alignment_audit.md"
cp qc-output/latest/findings_adjudication.csv "$snapshot/findings_adjudication.csv"
cp qc-output/latest/qc_summary.json "$snapshot/qc_summary.json"

FORMOSANBANK_PATH="$formosanbank_path" FORMOSANBANK_PYTHON="$python_bin" \
    bash CodeAndDocs/generate_xml.sh
FORMOSANBANK_PATH="$formosanbank_path" FORMOSANBANK_PYTHON="$python_bin" \
    bash CodeAndDocs/validate.sh
diff -ru "$snapshot/XML" XML
cmp "$snapshot/extracted_examples.tsv" CodeAndDocs/extracted_examples.tsv
cmp "$snapshot/rejected_candidates.tsv" CodeAndDocs/rejected_candidates.tsv
cmp "$snapshot/deduplicated_variants.tsv" CodeAndDocs/deduplicated_variants.tsv
cmp "$snapshot/chapter5_inventory.tsv" CodeAndDocs/chapter5_inventory.tsv
cmp "$snapshot/source_alignment_audit.md" CodeAndDocs/source_alignment_audit.md
cmp "$snapshot/findings_adjudication.csv" qc-output/latest/findings_adjudication.csv
cmp "$snapshot/qc_summary.json" qc-output/latest/qc_summary.json
"$python_bin" CodeAndDocs/check_wellformed.py

echo "Deterministic clean-clone build, source audit, and current QC passed."

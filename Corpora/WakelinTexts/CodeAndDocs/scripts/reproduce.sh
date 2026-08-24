#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
corpus_dir="$(cd -- "$script_dir/../.." && pwd)"
repo_root="$(cd -- "$corpus_dir/../.." && pwd)"
python_cmd="${WAKELIN_PYTHON:-python3}"
source_pdf="$corpus_dir/CodeAndDocs/Original.pdf"
expected_sha="4ce50f141aa2f90ce97c19fff61454625a308846ac0df5d9632095ac65aa2083"

actual_sha="$(shasum -a 256 "$source_pdf" | awk '{print $1}')"
if [[ "$actual_sha" != "$expected_sha" ]]; then
  echo "Unexpected Wakelin source PDF hash: $actual_sha" >&2
  exit 1
fi
if [[ "$(wc -c < "$source_pdf" | tr -d '[:space:]')" != "1006822" ]]; then
  echo "Unexpected Wakelin source PDF byte count" >&2
  exit 1
fi

"$python_cmd" "$corpus_dir/CodeAndDocs/build_corpus.py" \
  --source-ledger "$corpus_dir/CodeAndDocs/source_records.json" \
  --alternative-decisions "$corpus_dir/CodeAndDocs/alternative_expansions.json" \
  --id-ledger "$corpus_dir/CodeAndDocs/public_id_ledger.json" \
  --xml-dir "$corpus_dir/XML"

"$python_cmd" "$repo_root/QC/cleaning/clean_xml.py" \
  --corpora_path "$corpus_dir/XML" \
  --reference_dir "$repo_root/QC/validation/reference"

"$python_cmd" "$repo_root/QC/utilities/standardize.py" \
  --copy \
  --corpora_path "$corpus_dir" \
  --corpus XML \
  --ortho-path "$repo_root/Orthographies/Ortho113"

for sidecar in cleaner_warnings.csv standardize_warnings.csv; do
  report_path="$corpus_dir/XML/$sidecar"
  if [[ -f "$report_path" ]]; then
    if [[ "$(wc -l < "$report_path")" -gt 1 ]]; then
      echo "Unexpected warnings in $report_path" >&2
      exit 1
    fi
    rm "$report_path"
  fi
done

"$python_cmd" "$corpus_dir/CodeAndDocs/validate_corpus.py" \
  --xml-root "$corpus_dir/XML" \
  --source-ledger "$corpus_dir/CodeAndDocs/source_records.json" \
  --alternative-decisions "$corpus_dir/CodeAndDocs/alternative_expansions.json" \
  --id-ledger "$corpus_dir/CodeAndDocs/public_id_ledger.json" \
  --source-checks "$corpus_dir/CodeAndDocs/source_checks.csv"

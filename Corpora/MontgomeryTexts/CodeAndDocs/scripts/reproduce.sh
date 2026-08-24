#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
corpus_dir="$(cd -- "$script_dir/../.." && pwd)"
repo_root="$(cd -- "$corpus_dir/../.." && pwd)"
python_cmd="${MONTGOMERY_PYTHON:-python3}"
source_pdf="$corpus_dir/CodeAndDocs/Original.pdf"
expected_sha="7a9ad6482f4d1c38a45e2ba50b4a037155d4e771ce4586d64f06852e8bf8e2bd"

actual_sha="$(shasum -a 256 "$source_pdf" | awk '{print $1}')"
if [[ "$actual_sha" != "$expected_sha" ]]; then
  echo "Unexpected Montgomery source PDF hash: $actual_sha" >&2
  exit 1
fi
if [[ "$(wc -c < "$source_pdf" | tr -d '[:space:]')" != "874535" ]]; then
  echo "Unexpected Montgomery source PDF byte count" >&2
  exit 1
fi

"$python_cmd" "$corpus_dir/CodeAndDocs/record_publication_rights.py"

"$python_cmd" "$corpus_dir/CodeAndDocs/build_corpus.py" \
  --source-ledger "$corpus_dir/CodeAndDocs/source_records.json" \
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
  path="$corpus_dir/XML/$sidecar"
  if [[ -f "$path" ]]; then
    if [[ "$(wc -l < "$path")" -gt 1 ]]; then
      echo "Unexpected warnings in $path" >&2
      exit 1
    fi
    rm "$path"
  fi
done

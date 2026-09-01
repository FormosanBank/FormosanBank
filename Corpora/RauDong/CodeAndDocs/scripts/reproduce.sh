#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
corpus_dir="$(cd -- "$script_dir/../.." && pwd)"
repo_root="$(cd -- "$corpus_dir/../.." && pwd)"
python_cmd="${RAUDONG_PYTHON:-python3}"

"$python_cmd" "$corpus_dir/CodeAndDocs/remove_accents.py" \
  --corpora_path "$corpus_dir/XML"

"$python_cmd" "$repo_root/QC/utilities/add_phonology.py" \
  --corpora_path "$corpus_dir/XML" \
  --orthography Ortho94

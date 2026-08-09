#!/usr/bin/env bash
set -euo pipefail

corpus_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
formosanbank_path="${FORMOSANBANK_PATH:-$(cd "$corpus_root/../.." && pwd)}"
python_bin="${PYTHON:-$formosanbank_path/.venv/bin/python3}"
xml_path="$corpus_root/XML"
mapping="$corpus_root/CodeAndDocs/huteson_source_to_ortho113.tsv"

"$python_bin" "$corpus_root/CodeAndDocs/build_xml.py"
"$python_bin" "$formosanbank_path/QC/cleaning/clean_xml.py" \
  --corpora_path "$xml_path" \
  --ortho-path "$formosanbank_path/Orthographies/Ortho113"
"$python_bin" "$formosanbank_path/QC/utilities/standardize.py" \
  --tsv_path "$mapping" --corpora_path "$xml_path" --language Rukai
"$python_bin" "$formosanbank_path/QC/cleaning/clean_xml.py" \
  --corpora_path "$xml_path" \
  --ortho-path "$formosanbank_path/Orthographies/Ortho113"
"$python_bin" "$formosanbank_path/QC/utilities/add_phonology.py" \
  --corpora_path "$xml_path" --language Rukai
"$python_bin" "$formosanbank_path/QC/cleaning/clean_xml.py" \
  --corpora_path "$xml_path" \
  --ortho-path "$formosanbank_path/Orthographies/Ortho113"
"$python_bin" "$corpus_root/CodeAndDocs/preserve_rukai_segmentation.py" \
  --xml-dir "$xml_path/Rukai" --mapping "$mapping"
"$python_bin" "$formosanbank_path/QC/validation/validate_xml.py" by_path \
  --path "$xml_path"

echo "Reproduction complete: 2 XML files validated."

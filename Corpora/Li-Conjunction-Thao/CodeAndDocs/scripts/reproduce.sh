#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# standardize.py and add_phonology.py come from a FormosanBank checkout, which
# also holds the Li and Ortho113 orthography tables. Point FORMOSANBANK_PATH at a
# checkout that contains Orthographies/Li/Thao.tsv and
# Orthographies/ConversionTables/Thao_Li_113.tsv (and whose Python env has lxml).
: "${FORMOSANBANK_PATH:?set FORMOSANBANK_PATH to a FormosanBank checkout with Orthographies/Li}"
STANDARDIZE="$FORMOSANBANK_PATH/QC/utilities/standardize.py"
ADD_PHON="$FORMOSANBANK_PATH/QC/utilities/add_phonology.py"
CONVERSION="$FORMOSANBANK_PATH/Orthographies/ConversionTables/Thao_Li_113.tsv"

XML=XML/Thao/li_2014_conjunction_in_thao.xml
FINAL=Final_XML/Thao/li_2014_conjunction_in_thao.xml

python3 scripts/build_xml.py
# Audit source fidelity on the freshly built XML, whose tiers are still in Li's
# transcription (run before standardize romanizes the standard tier).
python3 scripts/audit_source_fidelity.py
# Finalize each tree: romanize the standard tier to Ortho113 (this also strips
# stress accents), flatten sentence-level segmentation, then add phonology
# (standard PHON via Ortho113, original PHON via Orthographies/Li).
for dir in XML Final_XML; do
  python3 "$STANDARDIZE" --corpora_path "$dir" --tsv_path "$CONVERSION" --target_column standard
  python3 scripts/flatten_standard_segmentation.py "$dir"
  python3 "$ADD_PHON" --corpora_path "$dir" --orthography Li
done
cmp "$XML" "$FINAL"
echo "Reproduction complete: draft and final XML byte-match (Ortho113 standard + phonology); source audit passes."

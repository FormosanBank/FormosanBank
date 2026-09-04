#!/usr/bin/env bash
set -euo pipefail

CODE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORPUS_ROOT="$(cd "$CODE_ROOT/.." && pwd)"
REPO_ROOT="${FORMOSANBANK_ROOT:-$(cd "$CORPUS_ROOT/../.." && pwd)}"
PYTHON_BIN="${PYTHON:-python3}"
SOURCE_PDF="${SOURCE_PDF:-$CODE_ROOT/Private/source/Papers from 12-ICAL, Volume 2.pdf}"

# The expected hash of the published XML — a build self-check, so repeated
# builds are provably byte-identical. It lives here rather than in
# data/provenance.json because it is build logic: provenance.json records
# what this corpus was built against and is never read by the pipeline.
EXPECTED_XML_SHA256="9e7e992230a9c1618f82fd7298dbc06aaf728acac4813f349aafa5abd90683ea"
XML_FILE="$CORPUS_ROOT/XML/Thao/li_2014_conjunction_in_thao.xml"
CONVERSION_DIR="$CODE_ROOT/data/orthographies/ConversionTables"
CONVERSION="$CONVERSION_DIR/Thao_Li2014_113.tsv"
SOURCE_ORTHOGRAPHY="$CODE_ROOT/data/orthographies/Li2014/Thao.tsv"
TARGET_ORTHOGRAPHY="$REPO_ROOT/Orthographies/Ortho113/Thao.tsv"

if [[ ! -f "$SOURCE_PDF" ]]; then
  echo "Missing official source PDF: $SOURCE_PDF" >&2
  echo "Run CodeAndDocs/download_source_data.sh or set SOURCE_PDF." >&2
  exit 1
fi

drop_empty_sidecar() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    return
  fi
  if [[ "$(wc -l < "$path")" -gt 1 ]]; then
    echo "Unexpected warnings in $path" >&2
    sed -n '1,40p' "$path" >&2
    exit 1
  fi
  rm "$path"
}

cd "$CORPUS_ROOT"
"$PYTHON_BIN" CodeAndDocs/scripts/build_xml.py
"$PYTHON_BIN" CodeAndDocs/scripts/audit_source_fidelity.py \
  --source "$SOURCE_PDF" --stage raw

before_clean="$(mktemp "${TMPDIR:-/tmp}/li-thao-before-clean.XXXXXX")"
conversion_report="$(mktemp "${TMPDIR:-/tmp}/li-thao-conversion.XXXXXX.md")"
trap 'rm -f "$before_clean" "$conversion_report"' EXIT
cp "$XML_FILE" "$before_clean"
"$PYTHON_BIN" "$REPO_ROOT/QC/cleaning/clean_xml.py" --corpora_path XML
cmp "$before_clean" "$XML_FILE"
drop_empty_sidecar XML/cleaner_warnings.csv

"$PYTHON_BIN" "$REPO_ROOT/QC/validation/validate_conversion_table.py" \
  "$SOURCE_ORTHOGRAPHY" "$TARGET_ORTHOGRAPHY" "$CONVERSION" \
  --output "$conversion_report"
grep -q "Result: PASS" "$conversion_report"
grep -q "confirmed=12" "$conversion_report"

"$PYTHON_BIN" "$REPO_ROOT/QC/utilities/standardize.py" \
  --corpora_path XML \
  --tsv_path "$CONVERSION" \
  --target_column standard \
  --hard-remove-segmentation
drop_empty_sidecar XML/standardize_warnings.csv

# Only the safe Ortho113 standard PHON tier is generated. The generic Li
# profile cannot represent the source's stress vowels and printed S/D symbols.
"$PYTHON_BIN" "$REPO_ROOT/QC/utilities/add_phonology.py" --corpora_path XML
"$PYTHON_BIN" CodeAndDocs/scripts/audit_source_fidelity.py \
  --source "$SOURCE_PDF" --stage final

ACTUAL_XML_SHA256="$(shasum -a 256 "$XML_FILE" | cut -d' ' -f1)"
if [[ "$ACTUAL_XML_SHA256" != "$EXPECTED_XML_SHA256" ]]; then
  echo "Generated XML hash mismatch" >&2
  echo "expected: $EXPECTED_XML_SHA256" >&2
  echo "actual:   $ACTUAL_XML_SHA256" >&2
  exit 1
fi

echo "Rebuilt source-faithful XML: 27 S, 211 W, 309 M"
echo "XML SHA-256: $ACTUAL_XML_SHA256"

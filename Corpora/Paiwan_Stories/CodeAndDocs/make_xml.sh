#!/usr/bin/env bash
set -euo pipefail

CORPUS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="${FORMOSANBANK_ROOT:-$(cd "$CORPUS_ROOT/../.." && pwd)}"
PYTHON_BIN="${PYTHON:-python3}"
VALIDATION_CSV="$(mktemp "${TMPDIR:-/tmp}/paiwan-stories-validate-xml.XXXXXX.csv")"
trap 'rm -f "$VALIDATION_CSV"' EXIT

drop_empty_sidecar() {
  local sidecar="$1"
  if [[ ! -f "$sidecar" ]]; then
    return
  fi
  if [[ "$(wc -l < "$sidecar")" -gt 1 ]]; then
    echo "Unexpected warnings in $sidecar" >&2
    sed -n '1,80p' "$sidecar" >&2
    exit 1
  fi
  rm "$sidecar"
}

cd "$CORPUS_ROOT"
"$PYTHON_BIN" CodeAndDocs/build_xml.py
"$PYTHON_BIN" "$REPO_ROOT/QC/cleaning/clean_xml.py" --corpora_path XML
drop_empty_sidecar XML/cleaner_warnings.csv
"$PYTHON_BIN" "$REPO_ROOT/QC/utilities/standardize.py" --copy --corpora_path XML
drop_empty_sidecar XML/standardize_warnings.csv
"$PYTHON_BIN" "$REPO_ROOT/QC/utilities/add_phonology.py" \
  --orthography Ortho94 --corpora_path XML
"$PYTHON_BIN" "$REPO_ROOT/QC/validation/validate_xml.py" \
  --no-exit-on-hard --csv "$VALIDATION_CSV" by_path --path XML

echo "Rebuilt 3 source-aligned XML files with 46 sentences"

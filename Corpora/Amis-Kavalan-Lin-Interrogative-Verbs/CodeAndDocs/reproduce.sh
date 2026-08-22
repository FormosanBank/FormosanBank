#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
QC_ROOT="${FORMOSANBANK_QC_ROOT:-${FORMOSANBANK_PATH:-$ROOT/../FormosanBank}}"
PY="${FORMOSANBANK_QC_PYTHON:-$QC_ROOT/.venv/bin/python}"
LOCAL_PY="${PYTHON:-python3}"
REPRO_TMP="$(mktemp -d "${TMPDIR:-/tmp}/lin-reproduce.XXXXXX")"
cleanup_repro() {
  rm -rf -- "$REPRO_TMP"
}
trap cleanup_repro EXIT

if [[ ! -x "$PY" ]] || ! command -v "$LOCAL_PY" >/dev/null 2>&1; then
  printf '%s\n' "QC Python or local Python is not executable." >&2
  exit 2
fi

cd "$ROOT"
FORMOSANBANK_QC_ROOT="$QC_ROOT" \
FORMOSANBANK_QC_PYTHON="$PY" \
PYTHON="$LOCAL_PY" \
QC_RUN_ID="reproduce" \
QC_OUTPUT_DIR="$REPRO_TMP/qc" \
  "$ROOT/CodeAndDocs/run_qc_pipeline.sh"

git diff --exit-code -- \
  XML \
  CodeAndDocs/alignment_omissions.tsv \
  CodeAndDocs/excluded_source_units.tsv \
  CodeAndDocs/extracted_examples.tsv \
  CodeAndDocs/extraction_summary.md \
  CodeAndDocs/source_alignment_audit.md

printf '%s\n' "Reproduction matches the checked-in generated artifacts."

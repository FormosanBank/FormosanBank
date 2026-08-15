#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
OUTPUT=${QC_OUTPUT_DIR:-$(mktemp -d "${TMPDIR:-/tmp}/sakizaya-qc.XXXXXX")}
cd "$ROOT"

./CodeAndDocs/download_source_data.sh
QC_OUTPUT_DIR="$OUTPUT" CodeAndDocs/run_qc_pipeline.sh
printf 'reproduction_complete=1 evidence=%s\n' "$OUTPUT"

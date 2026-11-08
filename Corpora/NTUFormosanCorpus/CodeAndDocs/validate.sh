#!/usr/bin/env bash
# The checks for NTUFormosanCorpus, kept out of the build (POL-047):
# the source-coverage audit, the validators, and the regression check
# against qa/baseline.tsv. Run after generate_xml.sh.
#
#   ./validate.sh
#
# HARD findings do not abort; read the summaries.
set -euo pipefail

CODEDOCS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORPUS="$(dirname "$CODEDOCS")"
BANK="$(cd "$CORPUS/../.." && pwd -P)"

PY="${PYTHON:-$BANK/.venv/bin/python}"
[[ -x "$PY" ]] || PY="$(command -v python3)"
export PYTHON="$PY"

step() { printf '\n=== %s ===\n' "$*"; }

step "Source coverage audit"
"$PY" "$CODEDOCS/scripts/audit_source_coverage.py" --repo-root "$CORPUS"

step "Validation summary (HARD findings do not abort)"
"$PY" "$BANK/QC/validation/validate_text.py" by_path --path "$CORPUS/XML" \
  --no-exit-on-hard --log_dir "$CORPUS/logs"
"$PY" "$BANK/QC/validation/validate_glosses.py" by_path --path "$CORPUS/XML" \
  --no-exit-on-hard --log_dir "$CORPUS/logs"

step "Regression check against the recorded baseline"
if [[ -x "$CODEDOCS/qa/run_regression.sh" ]]; then
  "$CODEDOCS/qa/run_regression.sh" || echo "  regression check reported movement; see qa/README.md"
else
  echo "  qa/ harness not present in this checkout; skipped"
fi

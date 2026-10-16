#!/usr/bin/env bash
# QC for this corpus. Separate from the build, per POL-047.
set -euo pipefail

CODE_DOCS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORPUS="$(dirname "$CODE_DOCS")"
REPO="$(cd "$CORPUS/../.." && pwd)"
PYTHON_BIN="${PYTHON:-python3}"

"$PYTHON_BIN" "$CODE_DOCS/audit_source_alignment.py"
"$PYTHON_BIN" "$REPO/QC/validation/validate_xml.py" by_path --path "$CORPUS/XML"
"$PYTHON_BIN" "$REPO/QC/validation/validate_text.py" by_path --path "$CORPUS/XML"
"$PYTHON_BIN" "$REPO/QC/validation/validate_glosses.py" by_path --path "$CORPUS/XML"
"$PYTHON_BIN" "$REPO/QC/validation/validate_port_readiness.py" --corpus_path "$CORPUS"

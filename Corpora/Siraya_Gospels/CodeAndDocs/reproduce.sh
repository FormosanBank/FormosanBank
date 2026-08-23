#!/usr/bin/env bash
set -euo pipefail

code_root=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
python_bin=${PYTHON:-python3}

"$python_bin" "$code_root/scripts/import_kjv_translations.py"
"$python_bin" "$code_root/scripts/import_cuv_translations.py"
"$python_bin" "$code_root/scripts/apply_review_corrections.py"
"$python_bin" "$code_root/scripts/build_xml.py"
"$python_bin" "$code_root/scripts/build_source_ledger.py"
"$python_bin" "$code_root/scripts/validate_translations.py"
"$python_bin" "$code_root/scripts/verify_source_checks.py"

echo "Reproduced 49 published Siraya Gospel XML files."

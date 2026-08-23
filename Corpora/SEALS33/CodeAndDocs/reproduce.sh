#!/usr/bin/env bash

set -euo pipefail

CODEDOCS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORPUS_ROOT="$(dirname "$CODEDOCS_ROOT")"
BANK="${1:-${FORMOSANBANK_ROOT:-$(cd "$CORPUS_ROOT/../.." && pwd)}}"
BANK="$(cd "$BANK" && pwd)"
PY="${PYTHON:-$BANK/.venv/bin/python}"
[[ -x "$PY" ]] || PY="$(command -v python3)"

step() { printf '\n=== %s ===\n' "$*"; }

step "Build source tiers from committed snapshot"
"$PY" "$CODEDOCS_ROOT/scripts/build_xml.py"

step "Audit source coverage before FormosanBank normalization"
"$PY" "$CODEDOCS_ROOT/scripts/source_audit.py"

step "Apply recorded manual edits (none expected)"
"$PY" "$BANK/QC/cleaning/apply_manual_edits.py" \
  --corpora_path "$CORPUS_ROOT/XML"

step "Apply ruled source-safe cleaning"
"$PY" "$BANK/QC/cleaning/clean_xml.py" --corpora_path "$CORPUS_ROOT/XML"

step "Regenerate standard FORM"
"$PY" "$BANK/QC/utilities/standardize.py" --copy --corpora_path "$CORPUS_ROOT/XML"

step "Regenerate original and standard PHON"
"$PY" "$BANK/QC/utilities/add_phonology.py" \
  --corpora_path "$CORPUS_ROOT/XML" \
  --orthography Ortho94

step "Audit final source alignment"
"$PY" "$CODEDOCS_ROOT/scripts/source_audit.py"

if [[ -f "$CORPUS_ROOT/XML/cleaner_warnings.csv" ]]; then
  step "Remove reviewed ephemeral cleaner warnings"
  wc -l "$CORPUS_ROOT/XML/cleaner_warnings.csv"
  unlink "$CORPUS_ROOT/XML/cleaner_warnings.csv"
fi

step "Done"

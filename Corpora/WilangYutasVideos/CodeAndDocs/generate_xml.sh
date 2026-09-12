#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
FB="${FORMOSANBANK_ROOT:-$(cd "$HERE/../../.." && pwd)}"
PY="${PYTHON:-python3}"
REPORTS="${QC_OUTPUT_DIR:-$(mktemp -d "${TMPDIR:-/tmp}/wilang-build-reports.XXXXXX")}"
STAGE="$(mktemp -d "$HERE/.build.XXXXXX")"
trap 'rm -rf "$STAGE"' EXIT

test -f "$FB/QC/cleaning/clean_xml.py"
"$PY" "$HERE/make_xml.py" --output-dir "$STAGE/XML"
"$PY" "$FB/QC/cleaning/clean_xml.py" --corpora_path "$STAGE/XML" --warnings_dir "$REPORTS"
"$PY" "$FB/QC/utilities/standardize.py" --corpora_path "$STAGE/XML" --remove_accents
"$PY" "$HERE/make_xml.py" --copy-form-notes "$STAGE/XML"
"$PY" "$FB/QC/utilities/add_phonology.py" --corpora_path "$STAGE/XML" --orthography Ortho94

mkdir -p "$ROOT/XML/Atayal"
cp "$STAGE/XML/Atayal/"*.xml "$ROOT/XML/Atayal/"
"$PY" "$HERE/make_xml.py" --record-provenance "$FB"
printf 'Build warnings: %s\n' "$REPORTS"

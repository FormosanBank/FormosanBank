#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
FB="${FORMOSANBANK_ROOT:-$(cd "$HERE/../../.." && pwd)}"
PY="${PYTHON:-python3}"
REPORTS="${QC_OUTPUT_DIR:-$(mktemp -d "${TMPDIR:-/tmp}/siraya-build-reports.XXXXXX")}"
STAGE="$(mktemp -d "$HERE/.build.XXXXXX")"
trap 'rm -rf "$STAGE"' EXIT
export PYTHONDONTWRITEBYTECODE=1

"$PY" "$HERE/generate_xml.py" --output-dir "$STAGE/XML"
"$PY" "$FB/QC/cleaning/apply_manual_edits.py" --corpora_path "$STAGE/XML" --manual_file "$HERE/manual_edits.xml"
"$PY" "$FB/QC/cleaning/clean_xml.py" --corpora_path "$STAGE/XML" --warnings_dir "$REPORTS"
"$PY" "$FB/QC/utilities/standardize.py" --corpora_path "$STAGE/XML" --copy
# Preserve the merged Siraya-specific line-break decisions after the copy step.
"$PY" "$HERE/regenerate_standard_tier.py" --xml-dir "$STAGE/XML/Siraya"

mkdir -p "$ROOT/XML"
rsync -a --delete "$STAGE/XML/" "$ROOT/XML/"
"$PY" - "$FB" "$HERE/provenance.json" <<'PROVENANCE_PY'
import json
import subprocess
import sys
from pathlib import Path

root, destination = Path(sys.argv[1]).resolve(), Path(sys.argv[2])
if (root / ".git").exists():
    commit = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    destination.write_text(json.dumps({"formosanbank_commit": commit}, indent=2) + "\n")
elif not destination.is_file():
    raise SystemExit("The export must retain CodeAndDocs/provenance.json.")
PROVENANCE_PY
printf 'Build warnings: %s\n' "$REPORTS"

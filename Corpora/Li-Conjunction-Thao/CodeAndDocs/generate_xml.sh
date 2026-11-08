#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
FB="${FORMOSANBANK_ROOT:-$(cd "$HERE/../../.." && pwd)}"
PY="${PYTHON:-python3}"

test -f "$FB/QC/cleaning/clean_xml.py"
"$PY" "$HERE/scripts/build_xml.py"
"$PY" "$FB/QC/cleaning/clean_xml.py" --corpora_path "$ROOT/XML"
"$PY" "$FB/QC/utilities/standardize.py" --corpora_path "$ROOT/XML" \
    --tsv_path "$FB/Orthographies/ConversionTables/Thao_Li_113.tsv" \
    --target_column standard --hard-remove-segmentation
"$PY" "$HERE/scripts/flatten_standard_segmentation.py" "$ROOT/XML"
"$PY" "$FB/QC/utilities/add_phonology.py" --corpora_path "$ROOT/XML" --orthography Li
"$PY" - "$FB" "$HERE/provenance.json" <<'PY'
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
PY

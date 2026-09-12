#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FB="${FORMOSANBANK_ROOT:-$(cd "$HERE/../../.." && pwd)}"
PY="${PYTHON:-python3}"
export PYTHONDONTWRITEBYTECODE=1

# Audio-only source: the accepted POL-047 deviation omits text-tier steps.
"$PY" "$HERE/make_xml.py"
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

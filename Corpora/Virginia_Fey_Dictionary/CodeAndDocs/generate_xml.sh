#!/usr/bin/env bash
set -euo pipefail
CODEDOCS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORPUS="$(dirname "$CODEDOCS")"
XML="$CORPUS/XML"

if [[ -n "${FORMOSANBANK_ROOT:-${1:-}}" ]]; then
    BANK="$(cd "${FORMOSANBANK_ROOT:-$1}" && pwd)"
elif [[ -d "$CORPUS/../../QC" ]]; then
    BANK="$(cd "$CORPUS/../.." && pwd)"
else
    BANK="$(cd "$CORPUS/../FormosanBank" && pwd)"
fi
PY="${PYTHON:-python3}"
test -f "$BANK/QC/cleaning/clean_xml.py"
test -f "$CODEDOCS/pre_correction_snapshot/Amis/Amis.xml"

rm -rf "$XML"
mkdir -p "$XML"
cp -R "$CODEDOCS/pre_correction_snapshot/." "$XML/"
"$PY" "$CODEDOCS/fix_duplicate_ids.py" --path "$XML"
"$PY" "$CODEDOCS/reconcile_source.py" --path "$XML/Amis/Amis.xml"
"$PY" "$BANK/QC/cleaning/clean_xml.py" --corpora_path "$XML"
"$PY" "$BANK/QC/utilities/standardize.py" --remove_accents --corpora_path "$XML"
"$PY" "$BANK/QC/utilities/add_phonology.py" --corpora_path "$XML" --orthography Ortho113
"$PY" "$BANK/QC/cleaning/remove_duplicate_sentences.py" by_path --path "$XML" --apply

"$PY" - "$BANK" "$CODEDOCS/provenance.json" <<'PROVENANCE_PY'
import json
import subprocess
import sys
from pathlib import Path

root, destination = Path(sys.argv[1]), Path(sys.argv[2])
if (root / ".git").exists():
    commit = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    destination.write_text(json.dumps({"formosanbank_commit": commit}, indent=2) + "\n")
else:
    print("No Git metadata: retain provenance and verify the export's tools revision separately.")
    if not destination.is_file():
        raise SystemExit("The export must retain CodeAndDocs/provenance.json.")
PROVENANCE_PY

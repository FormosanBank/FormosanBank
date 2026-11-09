#!/usr/bin/env bash
# Rebuild Corpora/Naomi-Tsukida-Correlative-Clauses-Seediq/XML/ from the committed
# transcription tables, with the FormosanBank tools in the checkout this script sits in
# (or FORMOSANBANK_ROOT). Everything is built in a staging directory and installed only
# when every step has succeeded.
#
#   1. build_xml.py                       S/W/M records from raw_data/
#   2. QC/cleaning/clean_xml.py           (report kept out of XML/, POL-033)
#   3. standardize_with_clitic_spaces.py  QC/utilities/standardize.py with the shared
#        Seediq_Tsukida_113.tsv; clitics become separate words in the standard sentence
#   4. QC/utilities/add_phonology.py --orthography Tsukida
#   5. install, then record provenance (POL-052)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
FB="${FORMOSANBANK_ROOT:-$(cd "$HERE/../../.." && pwd)}"
PY="${PYTHON:-python3}"
for f in "$FB/QC/cleaning/clean_xml.py" "$FB/QC/utilities/standardize.py" \
         "$FB/QC/utilities/add_phonology.py" \
         "$FB/Orthographies/ConversionTables/Seediq_Tsukida_113.tsv" \
         "$FB/Orthographies/Tsukida/Seediq.tsv"; do
    [[ -e "$f" ]] || { echo "generate_xml.sh: missing $f (FormosanBank at $FB)" >&2; exit 1; }
done

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
REPORTS="${REPORTS_DIR:-$STAGE/reports}"     # per-run warning reports (POL-033), never installed
mkdir -p "$REPORTS"

"$PY" "$HERE/build_xml.py" --xml-root "$STAGE/XML"
if [[ -f "$HERE/manual_edits.xml" ]]; then
    "$PY" "$FB/QC/cleaning/apply_manual_edits.py" --corpora_path "$STAGE/XML" \
        --manual_file "$HERE/manual_edits.xml"
fi
"$PY" "$FB/QC/cleaning/clean_xml.py" --corpora_path "$STAGE/XML" --warnings_dir "$REPORTS"
"$PY" "$HERE/standardize_with_clitic_spaces.py" "$FB" "$STAGE/XML" --python "$PY"
"$PY" "$FB/QC/utilities/add_phonology.py" --corpora_path "$STAGE/XML" --orthography Tsukida

# per-run reports the shared tools write next to the XML are not published (POL-033)
find "$STAGE/XML" -name '*.csv' -exec mv -t "$REPORTS" {} +
if find "$STAGE/XML" -type f ! -name '*.xml' -print -quit | grep -q .; then
    echo "generate_xml.sh: non-XML file in staging" >&2; exit 1
fi

# Install: the published tree is replaced wholesale, so nothing stale survives a rebuild.
rm -rf "$ROOT/XML"
cp -r "$STAGE/XML" "$ROOT/XML"

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
echo "generate_xml.sh: built $(find "$ROOT/XML" -name '*.xml' | wc -l) XML file(s) with FormosanBank $(git -C "$FB" rev-parse --short HEAD 2>/dev/null || echo '(no Git metadata)')"

#!/usr/bin/env bash
# Rebuild XML/ from the page-checked transcription (extracted_examples.tsv) with the
# FormosanBank tools in the checkout this script sits in (or FORMOSANBANK_ROOT).
# Everything is built in a staging directory and installed only when every step has
# succeeded.
#
#   1. build_xml.py                       S, W and M records from the transcription
#   2. QC/cleaning/apply_manual_edits.py  only if CodeAndDocs/manual_edits.xml exists
#   3. QC/cleaning/clean_xml.py           (report kept out of XML/, POL-033)
#   4. QC/utilities/standardize.py        Amis: Amis_94_113.tsv (Coastal); Kavalan: Kavalan_94_113.tsv
#   5. apply_standard_exceptions.py       example 14a's q -> ' in its standard FORMs
#   6. QC/utilities/add_phonology.py      original PHON from Ortho94; standard PHON from Ortho113
#   7. build_xml.py --restore-brackets    the four printed constituent brackets, original tier only
#   8. install, then record provenance (POL-052)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
FB="${FORMOSANBANK_ROOT:-$(cd "$HERE/../../.." && pwd)}"
PY="${PYTHON:-python3}"
for f in "$FB/QC/cleaning/clean_xml.py" "$FB/QC/utilities/standardize.py" "$FB/QC/utilities/add_phonology.py" \
         "$FB/Orthographies/ConversionTables/Amis_94_113.tsv" "$FB/Orthographies/ConversionTables/Kavalan_94_113.tsv"; do
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
"$PY" "$FB/QC/utilities/standardize.py" --corpora_path "$STAGE/XML/Amis" \
    --tsv_path "$FB/Orthographies/ConversionTables/Amis_94_113.tsv" --target_column Coastal
"$PY" "$FB/QC/utilities/standardize.py" --corpora_path "$STAGE/XML/Kavalan" \
    --tsv_path "$FB/Orthographies/ConversionTables/Kavalan_94_113.tsv"
"$PY" "$HERE/apply_standard_exceptions.py" "$FB" "$STAGE/XML"
"$PY" "$FB/QC/utilities/add_phonology.py" --corpora_path "$STAGE/XML/Amis" --orthography Ortho94
"$PY" "$FB/QC/utilities/add_phonology.py" --corpora_path "$STAGE/XML/Kavalan" --orthography Ortho94
"$PY" "$HERE/build_xml.py" --restore-brackets --xml-root "$STAGE/XML"

# per-run reports the shared tools write next to the XML are not published (POL-033)
find "$STAGE/XML" -name '*.csv' -exec mv -t "$REPORTS" {} +
if find "$STAGE/XML" -type f ! -name '*.xml' -print -quit | grep -q .; then
    echo "generate_xml.sh: non-XML file in staging" >&2; exit 1
fi

# Install: the published tree is replaced wholesale, so nothing stale survives a rebuild.
rm -rf "$ROOT/XML"
cp -r "$STAGE/XML" "$ROOT/XML"

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
echo "generate_xml.sh: built $(find "$ROOT/XML" -name '*.xml' | wc -l) XML file(s) with FormosanBank $(git -C "$FB" rev-parse --short HEAD 2>/dev/null || echo '(no Git metadata)')"

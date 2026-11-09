#!/usr/bin/env bash
# Rebuild Corpora/Sakizaya-Affixes/XML/ from the committed inventories, the expert
# transcription and the maintainer's rulings, with the FormosanBank tools in the
# checkout this script sits in (or FORMOSANBANK_ROOT). Everything is built in a
# staging directory and installed only when every step has succeeded.
#
#   1. generate_xml.py                  fresh S records from the two inventories
#   2. QC/cleaning/apply_manual_edits.py the 670-record expert transcription (W, M, readings)
#   3. generate_xml.py --complete-transcription
#        23c optional reading, footnote/prose supplement, ruled records and corrections,
#        table morphemes in word order with circumfixes written X-Y, no table W/M glosses
#   4. QC/cleaning/clean_xml.py          (report kept out of XML/, POL-033)
#   5. QC/utilities/standardize.py --remove_accents --segmented-without-m-tier
#        the thesis already spells in Ortho113, so the standard tier is the original
#        with segmentation and null morphemes removed; no conversion table
#   6. QC/utilities/add_phonology.py     standard PHON
#   7. install, then record provenance (POL-052)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
FB="${FORMOSANBANK_ROOT:-$(cd "$HERE/../../.." && pwd)}"
PY="${PYTHON:-python3}"
for f in "$FB/QC/cleaning/apply_manual_edits.py" "$FB/QC/cleaning/clean_xml.py" \
         "$FB/QC/utilities/standardize.py" "$FB/QC/utilities/add_phonology.py"; do
    [[ -e "$f" ]] || { echo "generate_xml.sh: missing $f (FormosanBank at $FB)" >&2; exit 1; }
done

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
REPORTS="${REPORTS_DIR:-$STAGE/reports}"     # per-run warning reports (POL-033), never installed
mkdir -p "$REPORTS"

"$PY" "$HERE/generate_xml.py" --xml-root "$STAGE/XML"
"$PY" "$FB/QC/cleaning/apply_manual_edits.py" --corpora_path "$STAGE/XML" \
    --manual_file "$HERE/manual_edits.xml"
"$PY" "$HERE/generate_xml.py" --complete-transcription --xml-root "$STAGE/XML"
"$PY" "$FB/QC/cleaning/clean_xml.py" --corpora_path "$STAGE/XML" --warnings_dir "$REPORTS"
"$PY" "$FB/QC/utilities/standardize.py" --corpora_path "$STAGE/XML" \
    --remove_accents --segmented-without-m-tier
"$PY" "$FB/QC/utilities/add_phonology.py" --corpora_path "$STAGE/XML"

# per-run reports the shared tools write next to the XML are not published (POL-033)
find "$STAGE/XML" -name '*.csv' -exec mv -t "$REPORTS" {} +
if find "$STAGE/XML" -type f ! -name '*.xml' -print -quit | grep -q .; then
    echo "generate_xml.sh: non-XML file in staging" >&2; exit 1
fi

# Install: the published tree is replaced wholesale, so nothing stale survives a rebuild.
rm -rf "$ROOT/XML"
cp -r "$STAGE/XML" "$ROOT/XML"
"$PY" "$HERE/generate_xml.py" --record-provenance "$FB"
echo "generate_xml.sh: built $(find "$ROOT/XML" -name '*.xml' | wc -l) XML file(s) with FormosanBank $(git -C "$FB" rev-parse --short HEAD 2>/dev/null || echo '(no Git metadata)')"

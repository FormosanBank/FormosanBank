#!/usr/bin/env bash
# generate_xml.sh — THE entry point (POL-047): CodeAndDocs/source -> published XML/.
#   1. build_amis_chinese_xml.py               corpus-local; builds the original tier
#   2. QC/cleaning/apply_manual_edits.py       no-op unless CodeAndDocs/manual_edits.xml exists
#   3. QC/cleaning/clean_xml.py
#   4. QC/utilities/standardize.py             Amis: Amis_Church_113 (ruled 2026-10-17: "Church");
#                                              Sakizaya: Sakizaya_Church_113 (ruled 2026-10-17: "Let's go with option 2.")
#   5. QC/utilities/add_phonology.py
#
# Runs from a FormosanBank checkout (Corpora/<Name>/CodeAndDocs/) and from the dev repo alike. It reads only this
# corpus's CodeAndDocs/ and the shared tools (POL-048). It builds into a staging directory and installs XML/ only
# when every step succeeded, so a rerun on a clean checkout leaves `git status` empty. It runs no validator.
# CodeAndDocs/refresh_source.sh (never called from here) re-pulls the two source files.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"        # CodeAndDocs/
CORPUS="$(cd "$HERE/.." && pwd -P)"                              # the corpus root
# The FormosanBank checkout: two levels above the corpus when installed under Corpora/<Name>/, otherwise a sibling
# of the dev repo. Override with FORMOSANBANK_ROOT.
FB="${FORMOSANBANK_ROOT:-}"
if [ -z "$FB" ]; then
  if [ -d "$CORPUS/../../QC" ]; then FB="$(cd "$CORPUS/../.." && pwd -P)"
  elif [ -d "$CORPUS/../FormosanBank/QC" ]; then FB="$(cd "$CORPUS/../FormosanBank" && pwd -P)"
  else echo "generate_xml.sh: cannot find a FormosanBank checkout; set FORMOSANBANK_ROOT" >&2; exit 2; fi
fi
PY="${PYTHON:-$FB/.venv/bin/python3}"
# The table names are written out in the standardize lines below (not kept in variables) so that
# declared_vs_detected.py and validate_text.py's V135 can read the declared source orthography from this script.
for f in "$FB/QC/cleaning/clean_xml.py" "$FB/Orthographies/ConversionTables/Amis_Church_113.tsv" \
         "$FB/Orthographies/ConversionTables/Sakizaya_Church_113.tsv"; do
    [[ -e "$f" ]] || { echo "generate_xml.sh: missing $f (FormosanBank at $FB)" >&2; exit 1; }
done

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
REPORTS="${REPORTS_DIR:-$STAGE/reports}"     # per-run warning reports (POL-033), never installed
mkdir -p "$REPORTS"

"$PY" "$HERE/build_amis_chinese_xml.py" --xml-out-dir "$STAGE/XML"
"$PY" "$FB/QC/cleaning/apply_manual_edits.py" --corpora_path "$STAGE/XML" \
    --manual_file "$HERE/manual_edits.xml" --allow-missing
"$PY" "$FB/QC/cleaning/clean_xml.py" --corpora_path "$STAGE/XML" --warnings_dir "$REPORTS"
"$PY" "$FB/QC/utilities/standardize.py" --tsv_path "$FB/Orthographies/ConversionTables/Amis_Church_113.tsv" --corpora_path "$STAGE/XML/Amis"
"$PY" "$FB/QC/utilities/standardize.py" --tsv_path "$FB/Orthographies/ConversionTables/Sakizaya_Church_113.tsv" --corpora_path "$STAGE/XML/Sakizaya"
"$PY" "$FB/QC/utilities/add_phonology.py" --corpora_path "$STAGE/XML"

# per-run reports the shared tools write next to the XML are not published (POL-033)
find "$STAGE/XML" -name '*.csv' -exec mv -t "$REPORTS" {} +
if find "$STAGE/XML" -type f ! -name '*.xml' -print -quit | grep -q .; then
    echo "generate_xml.sh: non-XML file in staging" >&2; exit 1
fi

# Install: the published tree is replaced wholesale, so nothing stale survives a rebuild.
rm -rf "$CORPUS/XML"
cp -r "$STAGE/XML" "$CORPUS/XML"

# Provenance (POL-052): which FormosanBank commit produced these bytes. Reporting only; nothing reads it.
"$PY" - "$FB" "$HERE/provenance.json" <<'PYEOF'
import datetime, json, subprocess, sys
fb, out = sys.argv[1], sys.argv[2]
commit = subprocess.run(["git", "-C", fb, "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
with open(out, "w", encoding="utf-8") as fh:
    json.dump({"_note": "The FormosanBank commit this corpus was built against. Provenance only — the build does not read this file.",
               "formosanbank_commit": commit, "built": datetime.date.today().isoformat()}, fh, indent=2)
    fh.write("\n")
PYEOF
echo "generate_xml.sh: built $(find "$CORPUS/XML" -name '*.xml' | wc -l) XML file(s) with FormosanBank $(git -C "$FB" rev-parse --short HEAD)"

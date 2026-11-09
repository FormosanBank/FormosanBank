#!/usr/bin/env bash
# generate_xml.sh — THE entry point: source -> published XML/ (POL-047).
#
# Runs from a FormosanBank checkout and from this dev repo alike. It reads only
# this corpus's CodeAndDocs/ and the shared tools (POL-048): no Private/, no
# second clone, no VALIDATOR_ROOT. It builds into a staging directory and
# installs the result, so a rerun on a clean checkout leaves `git status`
# empty (idempotent). It runs no validator — put those in validate.sh.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"          # CodeAndDocs/
CORPUS="$(cd "$HERE/.." && pwd)"                               # the corpus root
# The FormosanBank checkout: three levels up when installed under Corpora/<Name>/,
# otherwise a sibling of the dev repo. Override with FORMOSANBANK_ROOT.
FB="${FORMOSANBANK_ROOT:-}"
if [ -z "$FB" ]; then
  if [ -d "$CORPUS/../../QC" ]; then FB="$(cd "$CORPUS/../.." && pwd)"
  elif [ -d "$CORPUS/../FormosanBank/QC" ]; then FB="$(cd "$CORPUS/../FormosanBank" && pwd)"
  else echo "generate_xml.sh: cannot find a FormosanBank checkout; set FORMOSANBANK_ROOT" >&2; exit 2; fi
fi
PY="${PYTHON:-$FB/.venv/bin/python3}"
STAGE="$(mktemp -d)"; trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/XML"

# 1. Initial parsing: the corpus-local step that builds the original tier.
#    Source material lives in CodeAndDocs/ (a POL-035 snapshot or a pinned,
#    hashed copy); the script also writes the rejected list with a reason per
#    unit, which the source-accounting test reads.
"$PY" "$HERE/generate_xml.py" --source "$HERE/source" --out "$STAGE/XML" --rejected "$HERE/rejected.tsv"

# 2. Recorded hand edits (POL-030). No-op when manual_edits.xml is absent.
"$PY" "$FB/QC/cleaning/apply_manual_edits.py" --corpora_path "$STAGE/XML" --manual_file "$HERE/manual_edits.xml"

# 3. The shared cleaner (dashes, quotes, null glyphs, entities — POL-010/011/012).
#    Its per-run report (POL-033) goes to $REPORTS_DIR when set (a QC run wants
#    to read it), otherwise to the staging directory, which is discarded.
"$PY" "$FB/QC/cleaning/clean_xml.py" --corpora_path "$STAGE/XML" --warnings_dir "${REPORTS_DIR:-$STAGE/reports}"

# 4. The standard tier. The site writes the NR line in the Council of Indigenous
#    Peoples orthography, Ortho113 for Kanakanavu, so there is no letter
#    conversion: --remove_accents copies the original tier and applies the
#    standard-tier markup cleaning (segmentation hyphens, infix brackets, '=',
#    null units removed from the sentence; accents removed unless attested).
"$PY" "$FB/QC/utilities/standardize.py" --corpora_path "$STAGE/XML" --remove_accents
# "$PY" "$FB/QC/utilities/standardize.py" --corpora_path "$STAGE/XML" \
#     --tsv_path "$FB/Orthographies/ConversionTables/<Language>_<Scheme>_113.tsv"

# 5. Phonology for both tiers, from the registered orthography profiles.
#    (The site's own phonetic line, PT, is not in these files; see README.)
"$PY" "$FB/QC/utilities/add_phonology.py" --corpora_path "$STAGE/XML" \
    --language "Kanakanavu" --orthography "Ortho113"

# Install: the published tree is replaced wholesale, so a removed source unit
# disappears from XML/ too (nothing stale survives a rebuild).
rm -rf "$CORPUS/XML"; cp -r "$STAGE/XML" "$CORPUS/XML"

# 6. The PT files (not published XML; README "PT files"): the site's phonetic line,
#    one XML file per text, into CodeAndDocs/PT/, replaced wholesale like XML/.
"$PY" "$HERE/generate_pt.py" --source "$HERE/source" --out "$STAGE/PT"
rm -rf "$HERE/PT"; cp -r "$STAGE/PT" "$HERE/PT"
# Provenance (POL-052): which FormosanBank commit produced these bytes. Reporting
# only — nothing reads it to decide what to do.
"$PY" - "$FB" "$HERE/provenance.json" <<'PYEOF'
import json, subprocess, sys, datetime
fb, out = sys.argv[1], sys.argv[2]
commit = subprocess.run(["git", "-C", fb, "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
# No build date: a date would change the file on every rerun (POL-047 idempotency).
json.dump({"_note": "The FormosanBank commit this corpus was built against. Provenance only — the build does not read this file.",
           "formosanbank_commit": commit}, open(out, "w"), indent=2)
open(out, "a").write("\n")
PYEOF
echo "generate_xml.sh: built $(find "$CORPUS/XML" -name '*.xml' | wc -l) XML file(s) with FormosanBank $(git -C "$FB" rev-parse --short HEAD)"

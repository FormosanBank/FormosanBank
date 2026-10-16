#!/usr/bin/env bash
# REPRODUCTION ENTRY POINT (POL-047). Build only: validators and the id audit
# live in validate.sh.
#
#   CodeAndDocs/generate_xml.sh
#
# Rebuilds Corpora/ILRDF_Dicts/XML/ from committed inputs only (POL-048):
#   source_data/snapshots/          the 2026 ILRDF API snapshots
#   source_data/main_2024/          POL-035 snapshot of the 2024 XML main published
#   source_data/main_id_ledger.csv  frozen main-id matches (match_main_ids.py)
#   source_data/*.json              reviewed repair, exclusion and ruling tables
# No network access. The shared QC tools come from the FormosanBank checkout
# that contains this corpus. PYTHON selects the interpreter.
#
# Every derived tier is produced by the shared QC tools and by nothing else:
# the standard FORM comes from standardize.py, PHON from add_phonology.py.
set -euo pipefail

CODEDOCS="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CORPUS="$(dirname "$CODEDOCS")"
XML_PATH="$CORPUS/XML"
FORMOSANBANK="$(cd -- "$CORPUS/../.." && pwd)"
PYTHON="${PYTHON:-python3}"
export PYTHONDONTWRITEBYTECODE=1

# POL-052: provenance is recorded, never a gate.
HEAD_COMMIT="$(git -C "$FORMOSANBANK" rev-parse HEAD 2>/dev/null || echo unknown)"
RECORDED="$(sed -n 's/.*"formosanbank_commit"[[:space:]]*:[[:space:]]*"\([0-9a-f]\{40\}\)".*/\1/p' "$CODEDOCS/provenance.json" 2>/dev/null || true)"
if [[ -n "$RECORDED" && "$RECORDED" != "$HEAD_COMMIT" ]]; then
    echo "note: FormosanBank at $HEAD_COMMIT; XML/ was last built at $RECORDED" >&2
fi

reference_dir="$(mktemp -d)"
trap 'rm -rf -- "$reference_dir"' EXIT
cd "$CODEDOCS"

step() { printf '\n== %s ==\n' "$*"; }

step "1/8  source tiers: sentences (2026 snapshots + main's ids, 2024 withdrawn sentences, audio)"
"$PYTHON" "$CODEDOCS/generate_xml.py" generate

step "2/8  source tiers: headword dictionaries"
"$PYTHON" "$CODEDOCS/generate_dictionary.py"

# Repairs come before the split: the split rewrites the very text a repair
# matches on (one Thao record is both repaired and split).
step "3/8  render manual_edits.xml from the reviewed repair table"
"$PYTHON" "$CODEDOCS/build_manual_edits.py" --xml-dir "$XML_PATH"

step "4/8  re-apply recorded manual edits (original tier, POL-030)"
"$PYTHON" "$FORMOSANBANK/QC/cleaning/apply_manual_edits.py" --corpora_path "$XML_PATH"

step "5/8  source-side alternatives: maintainer rulings, then automatic resolution"
"$PYTHON" "$CODEDOCS/split_alternatives.py" --apply \
    --xml-dir "$XML_PATH" --report "$CODEDOCS/docs/split_report.csv"

step "6/8  clean_xml"
"$PYTHON" "$FORMOSANBANK/QC/cleaning/clean_xml.py" \
    --corpora_path "$XML_PATH" --reference_dir "$reference_dir"

step "7/8  standardize (Ortho113; accents removed)"
"$PYTHON" "$FORMOSANBANK/QC/utilities/standardize.py" \
    --corpora_path "$XML_PATH" --remove_accents \
    --ortho-path "$FORMOSANBANK/Orthographies/Ortho113"

step "8/8  phonology: original and standard tiers, Ortho113"
"$PYTHON" "$FORMOSANBANK/QC/utilities/add_phonology.py" \
    --corpora_path "$XML_PATH" --orthography Ortho113

# POL-033: warning CSVs are review output, not corpus data.
for f in cleaner_warnings.csv standardize_warnings.csv; do
    if [[ -f "$XML_PATH/$f" ]]; then
        echo "  $f: $(( $(wc -l < "$XML_PATH/$f") - 1 )) rows"
    fi
done
rm -f -- "$XML_PATH/cleaner_warnings.csv" \
         "$XML_PATH/html_entities.log" \
         "$XML_PATH/standardize_warnings.csv"

cat > "$CODEDOCS/provenance.json" <<JSON
{
  "_note": "The FormosanBank commit this corpus was built against (POL-052). Written by generate_xml.sh; provenance only, nothing gates on it.",
  "formosanbank_commit": "$HEAD_COMMIT"
}
JSON

echo
echo "Rebuilt $XML_PATH"
echo "  shared tooling: $HEAD_COMMIT"
echo "  digest:         $(find "$XML_PATH" -name '*.xml' | sort | xargs sha256sum | sha256sum | cut -d' ' -f1)"

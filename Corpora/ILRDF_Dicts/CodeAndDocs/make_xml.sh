#!/usr/bin/env bash
# REPRODUCTION ENTRY POINT.
#
# Rebuilds Corpora/ILRDF_Dicts/XML/ from the committed snapshots in
# source_data/snapshots/. No network access needed — the snapshots are the
# source boundary. Re-scraping is a separate, deliberate act: refresh_source.sh.
#
#   FORMOSANBANK_AUTHORITY   a clean FormosanBank checkout at the pinned commit
#   FORMOSANBANK_PYTHON      python interpreter (default: python3)
#
# Every derived tier is produced by the shared QC tools and by nothing else:
# the standard FORM comes from standardize.py, PHON from add_phonology.py.
# The corpus's own scripts emit source tiers only.
set -euo pipefail

EXPECTED_AUTHORITY_COMMIT="__SET_IN_TASK_12__"

CODEDOCS="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CORPUS="$(dirname "$CODEDOCS")"
XML_PATH="$CORPUS/XML"
PYTHON="${FORMOSANBANK_PYTHON:-python3}"
AUTHORITY="${FORMOSANBANK_AUTHORITY:?Set FORMOSANBANK_AUTHORITY to the pinned FormosanBank checkout}"

if [[ "$EXPECTED_AUTHORITY_COMMIT" != "__SET_IN_TASK_12__" ]]; then
    actual="$(git -C "$AUTHORITY" rev-parse HEAD)"
    if [[ "$actual" != "$EXPECTED_AUTHORITY_COMMIT" ]]; then
        echo "Authority commit mismatch: expected $EXPECTED_AUTHORITY_COMMIT, found $actual" >&2
        exit 1
    fi
    if [[ -n "$(git -C "$AUTHORITY" status --porcelain)" ]]; then
        echo "Authority checkout is dirty; reproduction needs a clean tree" >&2
        exit 1
    fi
fi

reference_dir="$(mktemp -d)"
trap 'rm -rf -- "$reference_dir"' EXIT
cd "$CODEDOCS"

step() { printf '\n== %s ==\n' "$*"; }

step "1/8  source tiers from the snapshots — sentences"
"$PYTHON" "$CODEDOCS/generate_xml.py" generate

step "2/8  source tiers from the snapshots — headword dictionaries"
"$PYTHON" "$CODEDOCS/generate_dictionary.py"

step "3/8  split source-side alternatives into separate records"
"$PYTHON" "$CODEDOCS/split_alternatives.py" --apply \
    --xml-dir "$XML_PATH" --report "$CODEDOCS/docs/split_report.csv"

step "4/8  render manual_edits.xml from the reviewed repair table"
"$PYTHON" "$CODEDOCS/build_manual_edits.py" --xml-dir "$XML_PATH"

step "5/8  re-apply recorded manual edits (original tier, POL-030)"
"$PYTHON" "$AUTHORITY/QC/cleaning/apply_manual_edits.py" --corpora_path "$XML_PATH"

step "6/8  clean_xml — original tier, translations, metadata"
"$PYTHON" "$AUTHORITY/QC/cleaning/clean_xml.py" \
    --corpora_path "$XML_PATH" --reference_dir "$reference_dir"

step "7/8  standardize — builds every standard tier"
"$PYTHON" "$AUTHORITY/QC/utilities/standardize.py" \
    --corpora_path "$XML_PATH" --remove_accents \
    --ortho-path "$AUTHORITY/Orthographies/Ortho113"

step "8/8  phonology"
"$PYTHON" "$AUTHORITY/QC/utilities/add_phonology.py" --corpora_path "$XML_PATH"

# POL-033: warning CSVs are review output, not corpus data. Report the counts
# so a rebuild does not silently discard the signal, then remove them.
for f in cleaner_warnings.csv standardize_warnings.csv; do
    if [[ -f "$XML_PATH/$f" ]]; then
        echo "  $f: $(( $(wc -l < "$XML_PATH/$f") - 1 )) rows"
    fi
done
rm -f -- "$XML_PATH/cleaner_warnings.csv" \
         "$XML_PATH/html_entities.log" \
         "$XML_PATH/standardize_warnings.csv"

step "audit — published ids against source_data/published_ids.csv"
"$PYTHON" "$CODEDOCS/generate_xml.py" audit

step "tests"
"$PYTHON" -m unittest discover -s "$CODEDOCS/tests"

echo
echo "Rebuilt $XML_PATH"

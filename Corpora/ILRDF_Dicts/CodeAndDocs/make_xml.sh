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

EXPECTED_AUTHORITY_COMMIT="b88146902f6a90ab2d73aca0e304d45f565c392e"

CODEDOCS="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CORPUS="$(dirname "$CODEDOCS")"
XML_PATH="$CORPUS/XML"
PYTHON="${FORMOSANBANK_PYTHON:-python3}"
AUTHORITY="${FORMOSANBANK_AUTHORITY:?Set FORMOSANBANK_AUTHORITY to the pinned FormosanBank checkout}"

# The pin is INFORMATIONAL. A rebuild uses whatever shared tooling the
# authority checkout has, and says so: pinning the tooling forever would mean
# the corpus could never be rebuilt with a fixed standardizer or cleaner
# without editing this script, and the pin would rot.
#
# It still earns its keep. docs/reproduction.md records the pin together with
# the digest it produced, so "same pin, different digest" is a real signal
# that something has stopped being reproducible. Set
# FORMOSANBANK_STRICT_AUTHORITY=1 to turn the mismatch back into a hard
# failure — which is what you want when verifying a published digest.
AUTHORITY_HEAD="$(git -C "$AUTHORITY" rev-parse HEAD)"
AUTHORITY_DIRTY=""
[[ -n "$(git -C "$AUTHORITY" status --porcelain)" ]] && AUTHORITY_DIRTY=" (dirty)"

if [[ "$AUTHORITY_HEAD" != "$EXPECTED_AUTHORITY_COMMIT" || -n "$AUTHORITY_DIRTY" ]]; then
    echo "NOTE: building against ${AUTHORITY_HEAD}${AUTHORITY_DIRTY}," >&2
    echo "      not the recorded ${EXPECTED_AUTHORITY_COMMIT}." >&2
    echo "      Expect a different digest; update docs/reproduction.md if this" >&2
    echo "      build is the new reference." >&2
    if [[ -n "${FORMOSANBANK_STRICT_AUTHORITY:-}" ]]; then
        echo "FORMOSANBANK_STRICT_AUTHORITY is set; refusing to continue." >&2
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

# Source-fidelity repairs come before the split, both because that is the
# documented pipeline order and because splitting rewrites the very text the
# repair table matches on: one Thao record is split into two readings, and a
# repair keyed to the unsplit text would find no target.
step "3/8  render manual_edits.xml from the reviewed repair table"
"$PYTHON" "$CODEDOCS/build_manual_edits.py" --xml-dir "$XML_PATH"

step "4/8  re-apply recorded manual edits (original tier, POL-030)"
"$PYTHON" "$AUTHORITY/QC/cleaning/apply_manual_edits.py" --corpora_path "$XML_PATH"

step "5/8  split source-side alternatives into separate records"
"$PYTHON" "$CODEDOCS/split_alternatives.py" --apply \
    --xml-dir "$XML_PATH" --report "$CODEDOCS/docs/split_report.csv"

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
echo "  shared tooling: ${AUTHORITY_HEAD}${AUTHORITY_DIRTY}"
echo "  digest:         $(find "$XML_PATH" -name '*.xml' | sort | xargs sha256sum | sha256sum | cut -d' ' -f1)"

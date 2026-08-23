#!/usr/bin/env bash
# Regenerate Corpora/Wikipedias/XML/ from the POL-035 baseline snapshot.
#
# The Wikipedias corpus is NOT re-scraped (the live wikis have moved on;
# the published XML is the baseline). CodeAndDocs/pre_correction_snapshot/
# holds the pristine pre-correction XML (POL-035); this script restores
# XML/ from it and runs the full documented pipeline. Deterministic and
# idempotent: two consecutive runs produce byte-identical output.
#
# Usage: ./make_xml.sh [path-to-FormosanBank-root]
#        PYTHON=/path/to/python ./make_xml.sh

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
CORPUS="$(dirname "$HERE")"
PYTHON="${PYTHON:-python3}"
XML="$CORPUS/XML"
SNAP="$HERE/pre_correction_snapshot"

if (( $# > 1 )); then
    echo "usage: $0 [path-to-FormosanBank-root]" >&2
    exit 2
elif (( $# == 1 )); then
    ROOT_CANDIDATE="$1"
elif [[ -d "$CORPUS/../../QC" ]]; then
    # Published layout: FormosanBank/Corpora/Wikipedias.
    ROOT_CANDIDATE="$CORPUS/../.."
elif [[ -d "$CORPUS/../FormosanBank/QC" ]]; then
    # Development layout: sibling FormosanBank and Formosan-Wikipedias clones.
    ROOT_CANDIDATE="$CORPUS/../FormosanBank"
else
    echo "cannot locate FormosanBank; pass its repository root as argument 1" >&2
    exit 2
fi

ROOT="$(cd "$ROOT_CANDIDATE" && pwd)"
if [[ ! -d "$ROOT/QC" ]]; then
    echo "not a FormosanBank root (QC/ missing): $ROOT" >&2
    exit 2
fi

# 0. Restore XML/ from the POL-035 snapshot (snapshotting itself is not a
#    pipeline step; the snapshot is the immutable baseline).
for L in Amis Atayal Paiwan Sakizaya Seediq; do
    rm -rf "$XML/$L"
    cp -r "$SNAP/$L" "$XML/$L"
done

# 1. Re-apply recorded hand edits (POL-030). Must run before clean_xml;
#    the records are stored post-canonicalization, and clean_xml is
#    idempotent, so re-cleaning them is a no-op.
"$PYTHON" "$ROOT/QC/cleaning/apply_manual_edits.py" --corpora_path "$XML"

# 2. Delete duplicate-download copies of articles: one file per TEXT id,
#    canonical name kept (maintainer ruling 2026-08-12; clears POL-037/V081).
"$PYTHON" "$HERE/delete_duplicate_articles.py" --corpora_path "$XML"

# 3. Delete articles with no Formosan content (punctuation / wiki markup /
#    CJK only; maintainer ruling 2026-08-12).
"$PYTHON" "$HERE/delete_nonlatin_articles.py" --corpora_path "$XML"

# 4. dialect="unknown" on every TEXT (no Wikipedia article identifies its
#    dialect; maintainer ruling 2026-08-11).
"$PYTHON" "$HERE/add_dialect_attrs.py" --corpora_path "$XML"

# 5. Seediq-only apostrophe normalization (quotation ''/' -> "; must run
#    BEFORE clean_xml). Other languages: ' is glottal by fiat (README).
"$PYTHON" "$HERE/normalize_seediq_quotes.py" --corpora_path "$XML"

# 6. Preserve source asterisks with U+2217 in the active original tier.
#    ASCII * is reserved for acceptability notation by the text validator.
"$PYTHON" "$HERE/normalize_ascii_asterisks.py" --corpora_path "$XML"

# 7. Punctuation/Unicode cleanup (writes per-run cleaner_warnings.csv next
#    to XML/; the immutable baseline's residuals are adjudicated in README).
"$PYTHON" "$ROOT/QC/cleaning/clean_xml.py" --corpora_path "$XML"

# 8. Standard tier: copy of original minus accents (no TSV conversion -
#    dialect unknown).
"$PYTHON" "$ROOT/QC/utilities/standardize.py" --remove_accents --corpora_path "$XML"

# 9. PHON tiers, default IPA column (dialect unknown).
"$PYTHON" "$ROOT/QC/utilities/add_phonology.py" --corpora_path "$XML" --orthography Ortho113

# clean_xml's warning CSV is a run artifact, not corpus data. Its findings for
# this immutable snapshot are reviewed and documented in README.
rm -f "$XML/cleaner_warnings.csv"

#!/usr/bin/env bash
# Rebuild the preserved Wikipedia articles with the current shared tools.
# Usage: PYTHON=python3 ./CodeAndDocs/generate_xml.sh [FormosanBank-root]

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
CORPUS="$(dirname "$HERE")"
PYTHON="${PYTHON:-python3}"
XML="$CORPUS/XML"

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

"$PYTHON" "$HERE/generate_xml.py" --check-provenance "$ROOT"
"$PYTHON" "$HERE/generate_xml.py"

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

# 6. Shared normalization. Keep per-run warning CSVs available for review.
"$PYTHON" "$ROOT/QC/cleaning/clean_xml.py" --corpora_path "$XML"

# Compare reviewed, corrected originals before excluding source redirects.
"$PYTHON" "$HERE/drop_redirect_copies.py" --corpora_path "$XML"

# 7. Standard tier: copy of original minus accents (no TSV conversion -
#    dialect unknown).
"$PYTHON" "$ROOT/QC/utilities/standardize.py" --remove_accents --corpora_path "$XML"

# 8. PHON tiers, default IPA column (dialect unknown).
"$PYTHON" "$ROOT/QC/utilities/add_phonology.py" --corpora_path "$XML" --orthography Ortho113

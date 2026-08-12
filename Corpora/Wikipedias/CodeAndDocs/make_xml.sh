#!/usr/bin/env bash
# Regenerate Corpora/Wikipedias/XML/ from the POL-035 baseline snapshot.
#
# The Wikipedias corpus is NOT re-scraped (the live wikis have moved on;
# the published XML is the baseline). CodeAndDocs/pre_correction_snapshot/
# holds the pristine pre-correction XML (POL-035); this script restores
# XML/ from it and runs the full documented pipeline. Deterministic and
# idempotent: two consecutive runs produce byte-identical output.
#
# Usage: ./make_xml.sh [path-to-FormosanBank-root]   (default: ../../..)
#        PYTHON=/path/to/python ./make_xml.sh

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
CORPUS="$(dirname "$HERE")"
ROOT="$(cd "${1:-$CORPUS/../..}" && pwd)"
PYTHON="${PYTHON:-python3}"
XML="$CORPUS/XML"
SNAP="$HERE/pre_correction_snapshot"

# 0. Restore XML/ from the POL-035 snapshot (snapshotting itself is not a
#    pipeline step; the snapshot is the immutable baseline).
for L in Amis Atayal Paiwan Sakizaya Seediq; do
    rm -rf "$XML/$L"
    cp -r "$SNAP/$L" "$XML/$L"
done

# 1. Delete duplicate-download copies of articles: one file per TEXT id,
#    canonical name kept (maintainer ruling 2026-08-12; clears POL-037/V081).
"$PYTHON" "$HERE/delete_duplicate_articles.py" --corpora_path "$XML"

# 2. Delete articles with no Formosan content (punctuation / wiki markup /
#    CJK only; maintainer ruling 2026-08-12).
"$PYTHON" "$HERE/delete_nonlatin_articles.py" --corpora_path "$XML"

# 3. dialect="unknown" on every TEXT (no Wikipedia article identifies its
#    dialect; maintainer ruling 2026-08-11).
"$PYTHON" "$HERE/add_dialect_attrs.py" --corpora_path "$XML"

# 4. Seediq-only apostrophe normalization (quotation ''/' -> "; must run
#    BEFORE clean_xml). Other languages: ' is glottal by fiat (README).
"$PYTHON" "$HERE/normalize_seediq_quotes.py" --corpora_path "$XML"

# 5. Punctuation/Unicode cleanup (writes per-run cleaner_warnings.csv next
#    to XML/ — review then delete per POL-033; any quote_corrections.csv
#    row here is unexpected: this corpus has no TRANSLs).
"$PYTHON" "$ROOT/QC/cleaning/clean_xml.py" --corpora_path "$XML"

# 6. Standard tier: copy of original minus accents (no TSV conversion —
#    dialect unknown).
"$PYTHON" "$ROOT/QC/utilities/standardize.py" --remove_accents --corpora_path "$XML"

# 7. PHON tiers, default IPA column (dialect unknown).
"$PYTHON" "$ROOT/QC/utilities/add_phonology.py" --corpora_path "$XML" --orthography Ortho113

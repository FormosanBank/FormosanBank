#!/usr/bin/env bash
# Regenerate Corpora/Wikipedias/XML/ from the POL-035 baseline snapshot.
#
# The Wikipedias corpus is NOT re-scraped (the live wikis have moved on;
# the published XML is the baseline). CodeAndDocs/pre_correction_snapshot/
# holds the pristine pre-correction XML (POL-035); this script restores
# XML/ from it and runs the full documented pipeline. Deterministic and
# idempotent: two consecutive runs produce byte-identical output.
# Source acquisition is refresh_source.sh, which this script never calls.
#
# Usage: ./generate_xml.sh [path-to-FormosanBank-root]   (default: ../..)
#        PYTHON=/path/to/python ./generate_xml.sh

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
CORPUS="$(dirname "$HERE")"
ROOT="$(cd "${1:-$CORPUS/../..}" && pwd)"
PYTHON="${PYTHON:-python3}"
XML="$CORPUS/XML"
SNAP="$HERE/pre_correction_snapshot"

# POL-052: provenance.json records the FormosanBank commit the published XML
# was built against. It is documentation, never a gate: on a mismatch, note
# it and build with the tools in this checkout.
RECORDED="$(sed -n 's/.*"formosanbank_commit": *"\([0-9a-f]*\)".*/\1/p' "$HERE/provenance.json" 2>/dev/null || true)"
CURRENT="$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo unknown)"
if [[ "$RECORDED" != "$CURRENT" ]]; then
    echo "note: building with FormosanBank $CURRENT; provenance.json records ${RECORDED:-nothing}" >&2
fi

# 0. Restore XML/ from the POL-035 snapshot (snapshotting itself is not a
#    pipeline step; the snapshot is the immutable baseline).
for L in Amis Atayal Paiwan Sakizaya Seediq; do
    rm -rf "$XML/$L"
    cp -r "$SNAP/$L" "$XML/$L"
done

# 1. Re-apply recorded hand edits (POL-030). Must run before clean_xml;
#    the records are stored post-canonicalization, and clean_xml is
#    idempotent, so re-cleaning them is a no-op. Besides two Sakizaya
#    one-offs, 30 Seediq records restore source text the historical scrape
#    cut off (25 articles) or author credits (5 articles, FORM @notes); see
#    citation_restorations.csv and the README (maintainer ruling 2026-10-18).
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

# 5b. The other four languages: '' (two apostrophes typed for a double quote;
#     the download was plain text, so these are not italics markup) -> ";
#     runs of three or more are left alone (maintainer ruling 2026-10-14).
"$PYTHON" "$HERE/normalize_double_apostrophes.py" --corpora_path "$XML"

# 6. Punctuation/Unicode cleanup (writes per-run cleaner_warnings.csv next
#    to XML/ — review then delete per POL-033; any quote_corrections.csv
#    row here is unexpected: this corpus has no TRANSLs).
"$PYTHON" "$ROOT/QC/cleaning/clean_xml.py" --corpora_path "$XML"

# 6b. Delete the 490 copies of articles that the scrape downloaded a second
#     time under a redirect title (source_redirects.csv: each copy, the kept
#     article, the redirect evidence). Runs after clean_xml because the
#     recorded hashes are of the cleaned original FORM; every copy must still
#     match its kept article exactly, or nothing is deleted. The withdrawn
#     TEXT ids are listed in old_to_new_ids.csv (maintainer ruling 2026-10-18:
#     "Yes, delete (record the ids as withdrawn)").
"$PYTHON" "$HERE/drop_redirect_copies.py" --corpora_path "$XML"

# 7. Standard tier: copy of original minus accents (no TSV conversion —
#    dialect unknown).
"$PYTHON" "$ROOT/QC/utilities/standardize.py" --remove_accents --corpora_path "$XML"

# 8. PHON tiers, default IPA column (dialect unknown).
"$PYTHON" "$ROOT/QC/utilities/add_phonology.py" --corpora_path "$XML" --orthography Ortho113

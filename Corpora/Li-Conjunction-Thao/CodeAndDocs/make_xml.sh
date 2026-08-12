#!/usr/bin/env bash
# make_xml.sh — the single entry point for rebuilding this corpus.
#
# Rebuilds the published corpus-level XML/ from the committed inputs, end to
# end. There is no second script to run and no wrapper layer: everything the
# pipeline does is here, calling the per-step programs under scripts/ and the
# shared QC tools in a FormosanBank checkout.
#
#   1. scripts/build_xml.py                — draft XML/ + Final_XML/ from
#                                            raw_data/reviewed_examples.tsv
#                                            (incl. the two scripted Blust-typo
#                                            corrections, README-documented)
#   2. scripts/audit_source_fidelity.py    — source-fidelity audit, run while
#                                            the tiers are still in Li's
#                                            transcription
#   then, for each of the two trees (draft XML/ and Final_XML/):
#   3. QC/cleaning/clean_xml.py            — shared character-level cleaning of
#                                            the original tier (entity and
#                                            double-encoded-entity decoding,
#                                            dash/tilde/quote canonicalization,
#                                            null-glyph canonicalization,
#                                            Unicode flattening, empty-element
#                                            removal, translation-metadata
#                                            normalization). Currently a no-op
#                                            here — the XML is born clean from
#                                            the reviewed TSV — and the script
#                                            reports whether that still holds.
#                                            Thao's letter `-` is safe: the
#                                            dash rule only maps dash *look-
#                                            alikes* (en/em dash, minus sign,
#                                            ...) onto ASCII `-`.
#   4. QC/utilities/standardize.py         — TSV mode with
#                                            Orthographies/ConversionTables/
#                                            Thao_Li_113.tsv: maps Li's
#                                            transcription to Ortho113 and
#                                            strips the stress accents
#   5. scripts/flatten_standard_segmentation.py
#                                          — strips `- = < >` from S-level
#                                            standard FORMs (required because
#                                            C012 exempts Thao hyphens and
#                                            never touches `<`/`>`)
#   6. QC/utilities/add_phonology.py       — standard PHON from the Ortho113
#                                            standard tier, original PHON from
#                                            Orthographies/Li
#   7. draft/final byte-match (cmp), install Final_XML into ../XML/, clear the
#      scratch trees and per-run sidecars
#
# There is no apply_manual_edits step: this corpus has no manual_edits.xml
# (the only hand-checked fixes are the scripted typo corrections in
# build_xml.py).
#
# Usage, from CodeAndDocs/:
#   FORMOSANBANK_PATH=/path/to/FormosanBank ./make_xml.sh
# FORMOSANBANK_PATH must contain QC/cleaning/clean_xml.py,
# QC/utilities/{standardize,add_phonology}.py, Orthographies/Li/Thao.tsv and
# Orthographies/ConversionTables/Thao_Li_113.tsv, and its Python env
# (python3 on PATH, or $PYTHON) must have lxml.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
: "${FORMOSANBANK_PATH:?set FORMOSANBANK_PATH to a FormosanBank checkout with Orthographies/Li}"

PY="${PYTHON:-python3}"
CLEAN_XML="$FORMOSANBANK_PATH/QC/cleaning/clean_xml.py"
STANDARDIZE="$FORMOSANBANK_PATH/QC/utilities/standardize.py"
ADD_PHON="$FORMOSANBANK_PATH/QC/utilities/add_phonology.py"
CONVERSION="$FORMOSANBANK_PATH/Orthographies/ConversionTables/Thao_Li_113.tsv"

REL=Thao/li_2014_conjunction_in_thao.xml
XML="XML/$REL"
FINAL="Final_XML/$REL"

step() { echo; echo "== $* =="; }

step "1. build_xml.py (draft XML/ + Final_XML/ from the reviewed TSV)"
"$PY" scripts/build_xml.py

step "2. audit_source_fidelity.py"
"$PY" scripts/audit_source_fidelity.py

for dir in XML Final_XML; do
  step "3. clean_xml ($dir)"
  # Keep a copy so the run reports whether clean_xml is still the no-op the
  # README claims. It is not an error for it to act — if it ever does, the
  # change is real cleaning and should be reviewed, not suppressed.
  cp "$dir/$REL" "$dir/$REL.preclean"
  "$PY" "$CLEAN_XML" --corpora_path "$dir"
  if cmp -s "$dir/$REL.preclean" "$dir/$REL"; then
    echo "clean_xml ($dir): no-op (XML born clean from the reviewed TSV)"
  else
    echo "clean_xml ($dir): CHANGED the XML — review the diff and the sidecars"
  fi
  rm -f "$dir/$REL.preclean"

  step "4. standardize.py --tsv_path Thao_Li_113.tsv ($dir)"
  "$PY" "$STANDARDIZE" --corpora_path "$dir" --tsv_path "$CONVERSION" --target_column standard

  step "5. flatten_standard_segmentation.py ($dir)"
  "$PY" scripts/flatten_standard_segmentation.py "$dir"

  step "6. add_phonology.py --orthography Li ($dir)"
  "$PY" "$ADD_PHON" --corpora_path "$dir" --orthography Li
done

step "7. draft/final byte-match, install, clean up"
cmp "$XML" "$FINAL"
echo "draft and final XML byte-match (Ortho113 standard + phonology); source audit passes."

# POL-033: the *_warnings.csv sidecars are per-run reports, never committed.
# Expected content: standardize_warnings.csv holds exactly the Thao c012 hyphen
# warnings (the C012 Thao-hyphen exemption fires; flatten strips those hyphens
# right after, so the warnings are transient); cleaner_warnings.csv should not
# exist at all. Surface counts, then let the cleanup below drop them.
for w in XML/standardize_warnings.csv Final_XML/standardize_warnings.csv \
         XML/cleaner_warnings.csv Final_XML/cleaner_warnings.csv; do
  if [[ -f "$w" ]]; then
    echo "sidecar $w: $(tail -n +2 "$w" | wc -l) rows ($(tail -n +2 "$w" | cut -d, -f1 | sort | uniq -c | tr -s ' ' | tr '\n' ';'))"
  fi
done

# quote_corrections.csv is clean_xml's durable POL-035 log. This corpus has
# never produced one (no quote/glottal rewrite has ever fired), and clean_xml
# derives its location from a published XML/ tree, so a scratch-tree run would
# put it somewhere meaningless. Stop rather than silently discard a real log.
for q in quote_corrections.csv CodeAndDocs/quote_corrections.csv \
         XML/quote_corrections.csv Final_XML/quote_corrections.csv; do
  if [[ -f "$q" ]]; then
    echo "ERROR: clean_xml wrote $q — a quote correction fired for the first time."
    echo "       Review it and decide where the durable log belongs before rebuilding."
    exit 1
  fi
done

# Install the finished Final_XML into the published corpus-level XML/.
install -d ../XML/Thao
cp "$FINAL" "../XML/$REL"

# Clear scratch outputs (draft XML/, Final_XML/, build intermediates, sidecars).
rm -rf XML Final_XML intermediate

echo "make_xml.sh: published ../XML/$REL rebuilt from committed inputs."

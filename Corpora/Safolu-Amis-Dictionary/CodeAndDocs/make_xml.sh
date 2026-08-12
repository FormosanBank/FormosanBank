#!/usr/bin/env bash
# make_xml.sh — the single entry point for regenerating this corpus.
#
#   ./make_xml.sh                 regenerate XML/ from the POL-035 snapshot
#   ./make_xml.sh --from-source   fetch the pinned upstream checkouts, rebuild
#                                 the original tier from source into Final_XML/,
#                                 validate + audit it, then enrich it with the
#                                 same steps (needs network)
#
# The full from-source build needs network access to fetch the pinned upstream
# checkouts into `_sources/`, which are NOT committed — so the corpus is not
# regenerable from committed inputs alone. The reproduction baseline is
# therefore the snapshot at CodeAndDocs/pre_correction_snapshot/ (POL-035),
# taken once before automated corrections first touched this corpus
# (2026-08-12). Taking that snapshot is NOT a pipeline step, and per POL-038
# the snapshot changes only via committed scripts.
#
# Enrichment pipeline (see ../README.md for per-step explanations); the same
# steps run in both modes, on XML/ or on Final_XML/ respectively:
#   1. clean_xml.py               — original-tier cleaning (+ Amis quote-
#                                   correction arming; c031/c032 rewrites
#                                   append to CodeAndDocs/quote_corrections.csv)
#   2. standardize.py --remove_accents — standard tier: copy original,
#                                   strip accents
#   3. add_phonology.py --orthography Ortho113 — regenerate BOTH
#                                   PHON kindOf="original" (from the original
#                                   FORM) and PHON kindOf="standard" (from the
#                                   standard FORM). Both tiers are Ortho113
#                                   Amis, dialect="Coastal" column: the source
#                                   orthography already IS Ortho113, so the
#                                   original tier is phonologized with the same
#                                   table. --preserve-existing-original is NOT
#                                   used: no expert-supplied source PHON exists
#                                   here, so original PHON is always generated.
#   4. remove_duplicate_sentences.py --apply — dedup (reference resource,
#                                   POL-022; declared here, so leftover
#                                   duplicates are HARD findings; distinct
#                                   TRANSLs of removed duplicates merge into
#                                   the survivor as ver="alt", POL-025)
#
# Environment:
#   FORMOSANBANK_ROOT   FormosanBank checkout supplying the QC scripts
#                       (default: the repo this corpus sits in)
#   PYTHON              interpreter (default: $FORMOSANBANK_ROOT/.venv/bin/python)

set -euo pipefail

FROM_SOURCE=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --from-source) FROM_SOURCE=1; shift ;;
    -h|--help) sed -n '2,45p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "ERROR: unknown argument: $1 (usage: $0 [--from-source])" >&2; exit 2 ;;
  esac
done

CODEDOCS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # .../CodeAndDocs
CORPUS="$(dirname "$CODEDOCS")"                            # corpus root
BANK="${FORMOSANBANK_ROOT:-$(cd "$CORPUS/../.." && pwd)}"  # FormosanBank root
SNAPSHOT="$CODEDOCS/pre_correction_snapshot"

PY="${PYTHON:-$BANK/.venv/bin/python}"
[[ -x "$PY" ]] || PY="$(command -v python3)"

step() { printf '\n=== %s ===\n' "$*"; }

# Steps 1–4: turn an original-tier-only tree into the published shape.
enrich() {
  local target="$1"

  step "1. clean_xml"
  "$PY" "$BANK/QC/cleaning/clean_xml.py" --corpora_path "$target"

  step "2. standardize --remove_accents"
  "$PY" "$BANK/QC/utilities/standardize.py" --remove_accents --corpora_path "$target"

  step "3. add_phonology (Ortho113, original + standard tiers)"
  "$PY" "$BANK/QC/utilities/add_phonology.py" --orthography Ortho113 --corpora_path "$target"

  step "4. remove_duplicate_sentences (POL-022 dedup)"
  "$PY" "$BANK/QC/cleaning/remove_duplicate_sentences.py" by_path --path "$target" --apply
}

if [[ "$FROM_SOURCE" -eq 1 ]]; then
  BUILD="$CORPUS/Final_XML"

  step "A. fetch pinned upstream sources (network)"
  "$PY" "$CODEDOCS/fetch_sources.py"

  step "B. build original-tier XML from source"
  "$PY" "$CODEDOCS/build_formosanbank_xml.py"

  step "C. validate build + source-coverage audit"
  "$PY" "$CODEDOCS/validate_formosanbank_xml.py" "$BUILD/Amis/Safolu/amis_safolu_examples.xml"
  "$PY" "$CODEDOCS/audit_source_coverage.py"
  if find "$BUILD" -type f ! -name '*.xml' -print -quit | grep -q .; then
    echo "ERROR: Final_XML contains non-XML files:" >&2
    find "$BUILD" -type f ! -name '*.xml' -print >&2
    exit 1
  fi

  enrich "$BUILD/Amis/Safolu"

  step "Done (from source)"
  echo "Built tree: $BUILD (compare against XML/ before promoting it)."
else
  XML="$CORPUS/XML"
  [[ -d "$SNAPSHOT" ]] || { echo "ERROR: snapshot missing at $SNAPSHOT" >&2; exit 1; }

  step "0. Restore XML/ from POL-035 snapshot"
  rm -rf "$XML"
  mkdir -p "$XML"
  cp -r "$SNAPSHOT/." "$XML/"

  enrich "$XML"

  step "Done"
fi

echo "Review any warning sidecars (cleaner_warnings.csv, standardize_warnings.csv;"
echo "POL-033: per-run reports, never committed) and CodeAndDocs/quote_corrections.csv"
echo "(durable log — commit if rows were added)."

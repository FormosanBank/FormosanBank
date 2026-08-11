#!/usr/bin/env bash
# make_xml.sh — rerun the Glosbe post-scrape processing pipeline over XML/.
#
# Executable form of the "Cleaning, Standardization, and Phonology" section
# of ../readme.md. The initial Glosbe scrape is NOT reproducible (see the
# README's Reproducibility section); this script starts from the published
# original tier in ../XML and regenerates everything derived from it:
# cleaned original FORMs, the standard tier, and both-tier PHON.
#
# The pristine pre-correction XML (before the first automated original-tier
# correction ever ran) is kept in pre_correction_snapshot/ (POL-035).
#
# Usage:
#   ./make_xml.sh
#
# Environment overrides:
#   PYTHON  interpreter to use (default: <FormosanBank>/.venv/bin/python,
#           falling back to python3 on PATH)
#   BANK    FormosanBank repo root (default: derived from this script's
#           location, i.e. ../../..)
#
# All steps are idempotent; rerunning this script is safe.

set -euo pipefail

CODEDOCS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # .../CodeAndDocs
CORPUS="$(dirname "$CODEDOCS")"                            # corpus root
BANK="${BANK:-$(cd "$CORPUS/../.." && pwd)}"               # FormosanBank root
XML="$CORPUS/XML"
CT="$BANK/Orthographies/ConversionTables"

PY="${PYTHON:-$BANK/.venv/bin/python}"
[[ -x "$PY" ]] || PY="$(command -v python3)"

step() { printf '\n=== %s ===\n' "$*"; }

# 1. Shared cleaning pass over the whole corpus (all four languages).
#    Canonicalizes Unicode (dash look-alikes, curly apostrophes, NBSP,
#    entity residue) in original-tier FORMs and TRANSLs, and runs the
#    apostrophe-vs-quotation-mark classifier on sentence-level original
#    FORMs. The classifier arms per language on the existence of
#    QC/validation/reference/<Language>/attestation.txt (currently Amis,
#    Atayal, Saisiyat armed; Truku disarmed — its dictionary was removed).
#    Every '->" rewrite is appended with before/after text to
#    CodeAndDocs/quote_corrections.csv (durable, committed); ambiguity
#    flags land in XML/cleaner_warnings.csv, a per-run report that is
#    reviewed and deleted, never committed (POL-033).
#    Run from the corpus root with a relative path so the durable log's
#    file column carries stable "XML/<lang>/<file>.xml" paths.
step "1. clean_xml (Unicode cleanup + quote/glottal correction)"
(cd "$CORPUS" && "$PY" "$BANK/QC/cleaning/clean_xml.py" --corpora_path XML)

# 2. Standardize each language to Ortho113 (TSV mode). Rebuilds the
#    standard tier from the cleaned original tier; accents (e.g. Glosbe's
#    stress marks) are stripped from the standard tier only. Tables and
#    columns per the README's source-orthography assumptions.
step "2a. standardize Amis (Ortho94 -> Ortho113, Coastal column)"
"$PY" "$BANK/QC/utilities/standardize.py" --tsv_path "$CT/Amis_94_113.tsv"      --target_column Coastal  --corpora_path "$XML/ami"
step "2b. standardize Atayal (Church -> Ortho113)"
"$PY" "$BANK/QC/utilities/standardize.py" --tsv_path "$CT/Atayal_Church_113.tsv" --target_column standard --corpora_path "$XML/tay"
step "2c. standardize Truku (Ortho94 -> Ortho113, Truku column)"
"$PY" "$BANK/QC/utilities/standardize.py" --tsv_path "$CT/Seediq_94_113.tsv"     --target_column Truku    --corpora_path "$XML/trv"
step "2d. standardize Saisiyat (Ortho94 -> Ortho113)"
"$PY" "$BANK/QC/utilities/standardize.py" --tsv_path "$CT/Saisiyat_94_113.tsv"   --target_column standard --corpora_path "$XML/xsy"

# 3. Regenerate IPA on both tiers: standard-tier PHON from
#    Orthographies/Ortho113/<Language>.tsv, original-tier PHON from the
#    source orthography named by --orthography (the `default` column
#    supplies IPA for the unknown-dialect Amis and Atayal originals).
step "3a. add_phonology Amis (original tier: Ortho94/Coastal)"
"$PY" "$BANK/QC/utilities/add_phonology.py" --orthography Ortho94 --target_column Coastal --corpora_path "$XML/ami"
step "3b. add_phonology Atayal (original tier: Church)"
"$PY" "$BANK/QC/utilities/add_phonology.py" --orthography Church                          --corpora_path "$XML/tay"
step "3c. add_phonology Truku (original tier: Ortho94)"
"$PY" "$BANK/QC/utilities/add_phonology.py" --orthography Ortho94                         --corpora_path "$XML/trv"
step "3d. add_phonology Saisiyat (original tier: Ortho94)"
"$PY" "$BANK/QC/utilities/add_phonology.py" --orthography Ortho94                         --corpora_path "$XML/xsy"

step "Done. Review + delete XML/cleaner_warnings.csv (POL-033); commit CodeAndDocs/quote_corrections.csv if new rows were appended."

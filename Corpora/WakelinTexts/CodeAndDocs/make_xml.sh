#!/usr/bin/env bash
# make_xml.sh — rebuild the published XML/ for Corpora/WakelinTexts.
#
# Executable form of the "Processing pipeline" section in ../README.md, and
# the only entry point: everything that shapes the published data happens
# here, in this order.
#
# WakelinTexts was transferred to XML by hand from the 1958 SIL Work Papers
# article (CodeAndDocs/Original.pdf); there is no scrape or OCR stage to
# re-run. The hand-typed XML is therefore the source, preserved verbatim in
# CodeAndDocs/pre_correction_snapshot/XML/ (POL-035), and this script
# rebuilds XML/ from it:
#
#   0. restore XML/ from the pre-correction snapshot
#   1. clean_xml               original-tier canonicalization (typographic
#                              quotes/dashes/tildes, null glyphs, entities)
#   2. drop_derived_tiers      delete every FORM[@kindOf="standard"] and
#                              every PHON, at S, W and M level, leaving the
#                              original tier alone
#
# Step 2 is the whole point of this pipeline, so it is worth stating why a
# corpus would throw derived tiers away. This text's orthography has never
# been identified (see ../README.md, "Orthography"): the article states no
# writing system, and the transcription matches no profile in
# ../../../Orthographies/. A `standard` FORM asserts that the text has been
# transliterated into FormosanBank's common orthography, and a PHON asserts
# a pronunciation. We can support neither claim, so the published corpus
# carries only what the article prints.
#
# The snapshot does contain a standard tier — it was produced years ago by
# Yami_Wakelin_113.tsv, a "conversion table" whose single rule deleted
# hyphens and mapped no letters at all (that table has since been deleted
# from Orthographies/ConversionTables/; nothing referenced it). The
# snapshot is never edited (POL-038); the tier is removed on the way out of
# it, by committed code, on every run.
#
# There is correspondingly no standardize step and no add_phonology step.
# Running add_phonology with the modern Yami profile (Ortho113, Yami's
# standards.csv entry) was tried and produces 4240 PHON values with zero
# `*` markers — i.e. it fails silently: it deletes the source's `?` letter
# (`tau?` -> `tau`) and asserts retroflex/alveolo-palatal sibilants and a
# schwa the 1958 transcription never claimed. That is a fabricated
# pronunciation, not a transcription, so no phonology is generated.
#
# Warning sidecars (cleaner_warnings.csv) are per-run reports (POL-033):
# review them after a run, then delete; never commit them. This corpus
# currently produces none.
#
# Usage:
#   ./make_xml.sh [FORMOSANBANK_ROOT]
#
# The FormosanBank repo root defaults to the checkout this corpus lives in
# (two levels above the corpus directory); pass a path (or set the
# FORMOSANBANK_ROOT environment variable) to use another checkout's QC
# scripts. Set PYTHON to override the interpreter. The script is
# idempotent: it always rebuilds from the snapshot.

set -euo pipefail

CODEDOCS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # .../CodeAndDocs
CORPUS="$(dirname "$CODEDOCS")"                            # corpus root
BANK="${1:-${FORMOSANBANK_ROOT:-$(cd "$CORPUS/../.." && pwd)}}"
BANK="$(cd "$BANK" && pwd)"
XML="$CORPUS/XML"
SNAPSHOT="$CODEDOCS/pre_correction_snapshot/XML"

PY="${PYTHON:-$BANK/.venv/bin/python}"
[[ -x "$PY" ]] || PY="$(command -v python3)"

[[ -d "$SNAPSHOT" ]] || { echo "missing POL-035 snapshot: $SNAPSHOT" >&2; exit 1; }

step() { printf '\n=== %s ===\n' "$*"; }

step "0. Restore XML/ from pre-correction snapshot"
rm -rf "$XML"
cp -r "$SNAPSHOT" "$XML"

step "1. clean_xml"
"$PY" "$BANK/QC/cleaning/clean_xml.py" --corpora_path "$XML"

step "2. drop_derived_tiers (standard FORM + PHON)"
"$PY" "$CODEDOCS/drop_derived_tiers.py" --corpora_path "$XML" --bank "$BANK"

step "Done. Review + delete any $XML/*_warnings.csv sidecars (POL-033)."

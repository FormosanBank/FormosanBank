#!/usr/bin/env bash
# generate_xml.sh — THE entry point for Corpora/RauDong (POL-047): rebuilds the
# published XML/ from the POL-035 snapshot.
#
# Executable form of the "Reproducing XML/" section in ../README.md, and the
# only entry point: everything that shapes the published data happens here,
# in this order.
#
# RauDong's machine-readable text was supplied to FormosanBank already
# digitized; there is no scrape, OCR or parse stage in this repository to
# re-run, and none can be reconstructed. The source of record is therefore a
# snapshot in CodeAndDocs/pre_correction_snapshot/XML/ (POL-035), and this
# script rebuilds XML/ from it. The snapshot is the XML as published at
# 2bed0e22f, NOT the July 2025 delivery (0d0df4710): earlier hand corrections
# (quote normalization, one split sentence, translation edits) are baked into
# it and no script replays them. ../README.md lists what differs.
#
#
#   0. restore XML/ from the pre-correction snapshot
#   1. clean_xml         original-tier canonicalization (typographic quotes,
#                        dashes, tildes, null glyphs, XML entities)
#   2. standardize       --remove_accents: rebuild the standard tier as a copy
#                        of the original with Rau & Dong's lexical acute accent
#                        removed, and (S level only) morpheme-segmentation
#                        hyphens stripped
#   3. add_phonology     original PHON from the Ortho94 Yami profile (the
#                        source orthography); standard PHON from Ortho113, the
#                        scheme standards.csv designates for Yami
#
# Step 2 replaces the corpus's former bespoke remove_accents.py, which stripped
# the acute accent from an already-built standard tier after the fact. The
# shared utility's --remove_accents mode does the same job as one pipeline
# step, so the bespoke script was retired.
#
# On step 3's orthography: Rau & Dong (2006) write Yami in the letters of the
# ROC-94 official orthography (ng p b t d k g ' v c j s z h m n r l w y i e a
# o — no f, q or u), plus an acute accent that marks lexical stress rather
# than a segment. Ortho94 reproduces the published original PHON exactly, so
# the profile is identified rather than assumed; see ../README.md. Ortho94 has
# no letter for the accented vowels; add_phonology folds the stress accent
# before mapping, so accented vowels come out as the plain vowel in original
# PHON (no `*`). The only `*` left in either PHON tier are Chinese characters
# quoted in the text and the `UNK` placeholder morphemes (no Yami `u`).
#
# No apply_manual_edits step: this corpus has no CodeAndDocs/manual_edits.xml
# and no hand edits to re-apply. Per POL-038 nothing here is hand-edited —
# XML/ is a pure function of the snapshot and these three steps.
#
# Warning sidecars (cleaner_warnings.csv, standardize_warnings.csv) are
# per-run reports (POL-033): review them after a run, then delete. Never
# commit them.
#
# Usage:
#   ./generate_xml.sh [FORMOSANBANK_ROOT]
#
# The FormosanBank repo root defaults to the checkout this corpus lives in
# (two levels above the corpus directory); pass a path (or set the
# FORMOSANBANK_ROOT environment variable) to use another checkout's QC
# scripts. Set PYTHON to override the interpreter. The script is idempotent:
# it always rebuilds from the snapshot.

set -euo pipefail

CODEDOCS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # .../CodeAndDocs
CORPUS="$(dirname "$CODEDOCS")"                            # corpus root
BANK="${1:-${FORMOSANBANK_ROOT:-$(cd "$CORPUS/../.." && pwd)}}"
BANK="$(cd "$BANK" && pwd)"
XML="$CORPUS/XML"
SNAPSHOT="$CODEDOCS/pre_correction_snapshot/XML"

PY="${PYTHON:-$BANK/.venv/bin/python}"
[[ -x "$PY" ]] || PY="$(command -v python3)"

# The published XML was last regenerated against the FormosanBank commit in
# provenance.json (POL-052). Informational only: a different commit is fine and
# the build never gates on it; a mismatch is noted on stderr and the build goes on.
RECORDED="$(sed -n 's/.*"formosanbank_commit"[[:space:]]*:[[:space:]]*"\([0-9a-f]\{40\}\)".*/\1/p' "$CODEDOCS/provenance.json" 2>/dev/null || true)"
HEAD_COMMIT="$(git -C "$BANK" rev-parse HEAD 2>/dev/null || echo unknown)"
if [[ "$HEAD_COMMIT" != "$RECORDED" ]]; then
  echo "note: FormosanBank at $HEAD_COMMIT; XML/ was last built at ${RECORDED:-<none recorded>}" >&2
fi

[[ -d "$SNAPSHOT" ]] || { echo "missing POL-035 snapshot: $SNAPSHOT" >&2; exit 1; }

step() { printf '\n=== %s ===\n' "$*"; }

step "0. Restore XML/ from pre-correction snapshot"
rm -rf "$XML"
cp -r "$SNAPSHOT" "$XML"

step "1. clean_xml"
"$PY" "$BANK/QC/cleaning/clean_xml.py" --corpora_path "$XML"

step "2. standardize --remove_accents"
"$PY" "$BANK/QC/utilities/standardize.py" --remove_accents --corpora_path "$XML"

step "3. add_phonology (original: Ortho94; standard: Ortho113)"
"$PY" "$BANK/QC/utilities/add_phonology.py" --orthography Ortho94 --corpora_path "$XML"

step "Done. Review + delete any *_warnings.csv sidecars under $XML (POL-033)."

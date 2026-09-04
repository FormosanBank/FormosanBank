#!/usr/bin/env bash
# Single entry point: rebuild the published XML/ from the committed source and
# ledgers. Usage (from anywhere):
#
#   CodeAndDocs/scripts/make_xml.sh [/path/to/FormosanBank]
#
# The FormosanBank checkout supplying the shared QC utilities defaults to the
# repository that contains this corpus; pass a path (or set FORMOSANBANK_PATH)
# to use another one. PYTHON selects the interpreter.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CORPUS="$(cd "$ROOT/.." && pwd)"
XML_PATH="$CORPUS/XML"
FORMOSANBANK_PATH="${1:-${FORMOSANBANK_PATH:-$CORPUS/../..}}"
FORMOSANBANK_PATH="$(cd "$FORMOSANBANK_PATH" && pwd)"

if [ -n "${PYTHON:-}" ]; then
  :
elif [ -x "$ROOT/.venv/bin/python3" ]; then
  PYTHON="$ROOT/.venv/bin/python3"
else
  PYTHON="python3"
fi
export PYTHONDONTWRITEBYTECODE=1

# The published XML was last regenerated against this FormosanBank commit.
# Informational: the shared utilities move on, and a different commit is fine.
REFERENCE_FORMOSANBANK_COMMIT="3a3c47c220520113f747e6a2d441494000e13c4b"

test -f "$FORMOSANBANK_PATH/QC/cleaning/clean_xml.py"
head_commit="$(git -C "$FORMOSANBANK_PATH" rev-parse HEAD 2>/dev/null || echo unknown)"
if [ "$head_commit" != "$REFERENCE_FORMOSANBANK_COMMIT" ]; then
  echo "note: FormosanBank at $head_commit; XML/ was last built at $REFERENCE_FORMOSANBANK_COMMIT" >&2
fi

# 1. Rebuild the dictionary ledger from the positioned text (barred vowels
#    cross-checked against Appendix 2B; documented OCR corrections applied).
"$PYTHON" "$ROOT/scripts/extract_dictionary.py"

# 2. Confirm the u/ʉ reconciliation between sentence ledger and dictionary.
"$PYTHON" "$ROOT/scripts/reconcile_barred_vowels.py" --check

# 3. Recover the printed interlinear analyses into W/M records.
"$PYTHON" "$ROOT/scripts/extract_interlinear.py"

# 4. Write both XML files (asserts source hashes, ledger counts, sentence IDs).
"$PYTHON" "$ROOT/scripts/build_xml.py"

# 5. Re-apply any recorded hand edits before cleaning. This corpus currently
#    has no manual_edits.xml, so the command is a checked no-op.
"$PYTHON" "$FORMOSANBANK_PATH/QC/cleaning/apply_manual_edits.py" \
  --corpora_path "$XML_PATH"

# 6. Canonical Unicode / entity / punctuation normalization.
"$PYTHON" "$FORMOSANBANK_PATH/QC/cleaning/clean_xml.py" --corpora_path "$XML_PATH"

# 7. The source inventory is Ortho113. It uses ʉ and r, has no l, and its own
#    discussion says r represents the former l/r contrast, so no conversion
#    table is needed. --remove_accents (not --copy) because the book's acute
#    vowels mark stress, not Ortho113 segments: they stay in the original tier
#    and the shared utility folds them out of the standard tier.
"$PYTHON" "$FORMOSANBANK_PATH/QC/utilities/standardize.py" \
  --remove_accents --corpora_path "$XML_PATH"

# 8. Apply the exact reviewed dictionary, punctuation, and lyric decisions. Bound
#    citation forms without an unattached surface intentionally omit standard.
"$PYTHON" "$ROOT/scripts/normalize_standard_forms.py" --corpora_path "$XML_PATH"

# 9. Shared Ortho113 phonology, both tiers. add_phonology folds stress accents
#    itself (PHON is segmental; stress is not a segment), so the original FORM
#    keeps its accents while PHON stays clean IPA. No corpus-specific mapping.
"$PYTHON" "$FORMOSANBANK_PATH/QC/utilities/add_phonology.py" \
  --corpora_path "$XML_PATH" --orthography Ortho113

# Per-run cleaner triage is reviewed during QC and is not canonical corpus data.
rm -f "$XML_PATH/cleaner_warnings.csv"

echo "Rebuilt $XML_PATH/Kanakanavu/"

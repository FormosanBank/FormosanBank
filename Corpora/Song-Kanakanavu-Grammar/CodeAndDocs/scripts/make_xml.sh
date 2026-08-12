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
REFERENCE_FORMOSANBANK_COMMIT="3ce8e7daca2ab7f58a12b8e9b955fec2fc78d1fd"

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

# 5. Canonical Unicode / entity / punctuation normalization.
"$PYTHON" "$FORMOSANBANK_PATH/QC/cleaning/clean_xml.py" --corpora_path "$XML_PATH"

# 6. The source inventory is Ortho113. It uses ʉ and r, has no l, and its own
#    discussion says r represents the former l/r contrast. Standardization is an
#    identity copy before the exact reviewed surface decisions below.
"$PYTHON" "$FORMOSANBANK_PATH/QC/utilities/standardize.py" --copy --corpora_path "$XML_PATH"

# 7. Apply the exact reviewed dictionary, punctuation, and lyric decisions. Bound
#    citation forms without an unattached surface intentionally omit standard.
"$PYTHON" "$ROOT/scripts/normalize_standard_forms.py" --corpora_path "$XML_PATH"

# 8. Acute vowels record stress in the source but are not separate Ortho113
#    segments. Preserve them in original FORM, fold standard and alternate FORM,
#    and fold only a temporary copy when generating original PHON.
"$PYTHON" "$ROOT/scripts/fold_standard_stress.py" --corpora_path "$XML_PATH"

# 9. The wrapper delegates both tiers to the shared Ortho113 utility. It defines
#    no corpus-specific mapping and restores each original FORM byte-for-byte.
"$PYTHON" "$ROOT/scripts/add_shared_phonology.py" \
  --corpora_path "$XML_PATH" \
  --shared-script "$FORMOSANBANK_PATH/QC/utilities/add_phonology.py"

echo "Rebuilt $XML_PATH/Kanakanavu/"

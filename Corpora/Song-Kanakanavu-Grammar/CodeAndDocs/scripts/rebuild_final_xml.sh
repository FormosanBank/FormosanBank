#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-$ROOT/.venv/bin/python3}"
FORMOSANBANK_PATH="${FORMOSANBANK_PATH:-$ROOT/../FormosanBank}"
FORMOSANBANK_PATH="$(cd "$FORMOSANBANK_PATH" && pwd)"
XML_PATH="$ROOT/Final_XML"
EXPECTED_FORMOSANBANK_COMMIT="a20f81b470ed141c12425f3d827227b22d9f9ece"
export PYTHONDONTWRITEBYTECODE=1

test -x "$PYTHON"
test -f "$FORMOSANBANK_PATH/QC/cleaning/clean_xml.py"
test "$(git -C "$FORMOSANBANK_PATH" rev-parse HEAD)" = "$EXPECTED_FORMOSANBANK_COMMIT"
test -z "$(git -C "$FORMOSANBANK_PATH" status --porcelain)"

"$PYTHON" "$ROOT/scripts/extract_dictionary.py"
"$PYTHON" "$ROOT/scripts/reconcile_barred_vowels.py" --check
"$PYTHON" "$ROOT/scripts/extract_interlinear.py"
"$PYTHON" "$ROOT/scripts/build_xml.py"
"$PYTHON" "$FORMOSANBANK_PATH/QC/cleaning/apply_manual_edits.py" --corpora_path "$XML_PATH"
"$PYTHON" "$FORMOSANBANK_PATH/QC/cleaning/clean_xml.py" --corpora_path "$XML_PATH"

# The source inventory is Ortho113. It uses ʉ and r, has no l, and its own
# discussion says r represents the former l/r contrast. Standardization is an
# identity copy before the exact reviewed surface decisions below.
"$PYTHON" "$FORMOSANBANK_PATH/QC/utilities/standardize.py" --copy --corpora_path "$XML_PATH"

# Apply the exact reviewed dictionary, punctuation, and lyric decisions. Bound
# citation forms without an unattached surface intentionally omit standard.
"$PYTHON" "$ROOT/scripts/normalize_standard_forms.py" --corpora_path "$XML_PATH"

# Acute vowels record stress in the source but are not separate Ortho113
# segments. Preserve them in original FORM, fold standard and alternate FORM,
# and fold only a temporary copy when generating original PHON.
"$PYTHON" "$ROOT/scripts/fold_standard_stress.py" --corpora_path "$XML_PATH"

# The wrapper delegates both tiers to the shared Ortho113 utility. It defines no
# corpus-specific mapping and restores each original FORM byte-for-byte.
"$PYTHON" "$ROOT/scripts/add_shared_phonology.py" \
  --corpora_path "$XML_PATH" \
  --shared-script "$FORMOSANBANK_PATH/QC/utilities/add_phonology.py"

rm -f "$XML_PATH/cleaner_warnings.csv"
test "$(git -C "$FORMOSANBANK_PATH" rev-parse HEAD)" = "$EXPECTED_FORMOSANBANK_COMMIT"
test -z "$(git -C "$FORMOSANBANK_PATH" status --porcelain)"
echo "Rebuilt $XML_PATH/Kanakanavu/Song_2018_Kanakanavu_Grammar.xml"

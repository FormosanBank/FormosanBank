#!/usr/bin/env bash
set -euo pipefail

EXPECTED_AUTHORITY_COMMIT="3a3c47c220520113f747e6a2d441494000e13c4b"
EXPECTED_REFERENCE_COMMIT="face1e165d6a19068656a7aaa6e33034a66bb8a8"
CODEDOCS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORPUS="$(dirname "$CODEDOCS")"
AUTHORITY="${FORMOSANBANK_AUTHORITY:?Set FORMOSANBANK_AUTHORITY to the pinned FormosanBank checkout}"
REFERENCE="${GLOSBE_ILRDF_REFERENCE_REPO:?Set GLOSBE_ILRDF_REFERENCE_REPO to the pinned Formosan-Zheng-ACL-2024 checkout}"
PYTHON="${FORMOSANBANK_PYTHON:-python3}"
XML_PATH="$CORPUS/XML"

test "$(git -C "$AUTHORITY" rev-parse HEAD)" = "$EXPECTED_AUTHORITY_COMMIT"
test "$(git -C "$REFERENCE" rev-parse HEAD)" = "$EXPECTED_REFERENCE_COMMIT"
test -z "$(git -C "$AUTHORITY" status --porcelain)"
export FORMOSANBANK_REPOS_ROOT="$(dirname "$REFERENCE")"
export PYTHONDONTWRITEBYTECODE=1

cd "$CODEDOCS"
"$PYTHON" scripts/build_formosanbank_xml.py --config scripts/config.yaml

# Run shared QC from the corpus root so durable audit logs use portable
# XML-relative paths instead of paths from the maintainer's checkout.
cd "$CORPUS"
"$PYTHON" "$AUTHORITY/QC/cleaning/apply_manual_edits.py" --corpora_path XML
"$PYTHON" "$AUTHORITY/QC/cleaning/clean_xml.py" --corpora_path XML
"$PYTHON" "$AUTHORITY/QC/utilities/standardize.py" --copy --corpora_path XML
"$PYTHON" "$CODEDOCS/scripts/apply_duplicate_policy.py" \
  --shared-script "$AUTHORITY/QC/cleaning/remove_duplicate_sentences.py"
"$PYTHON" "$AUTHORITY/QC/utilities/add_phonology.py" --corpora_path XML
rm -f "$XML_PATH/cleaner_warnings.csv"

cd "$CODEDOCS"
"$PYTHON" scripts/validate_formosanbank_xml.py --config scripts/config.yaml
"$PYTHON" -m pytest -q tests
test "$(git -C "$AUTHORITY" rev-parse HEAD)" = "$EXPECTED_AUTHORITY_COMMIT"
test -z "$(git -C "$AUTHORITY" status --porcelain)"
echo "Rebuilt and verified $XML_PATH"

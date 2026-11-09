#!/usr/bin/env bash
# POL-047: validation, kept out of the build (maintainer, audit round 1, 2026-11-09: "Move both to validate.sh").
#
# generate_xml.sh produces XML/ and stops; this script only reads it. Run the build first:
#   CodeAndDocs/generate_xml.sh
#   CodeAndDocs/validate.sh [run-id]
#
# Writes each step's output under qc-output/<run-id>/ (gitignored). A step that fails stops the run. The last step,
# audit_qc_findings.py, requires every FormosanBank finding to be one it expects, with a recorded reason.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
source "$(dirname "${BASH_SOURCE[0]}")/formosanbank_path.sh"
python_bin="${FORMOSANBANK_PYTHON:-$formosanbank_path/.venv/bin/python3}"
run_id="${1:-$(date -u +%Y%m%dT%H%M%SZ)}"
out="$repo_root/qc-output/$run_id"
temp_root="$(mktemp -d "${TMPDIR:-/tmp}/kavalan-chang-validate.XXXXXX")"
trap 'rm -rf -- "$temp_root"' EXIT

[[ -x "$python_bin" ]] || {
    echo "No Python at $python_bin: give the FormosanBank checkout a .venv, or set FORMOSANBANK_PYTHON" >&2
    exit 1
}
[[ -f "$formosanbank_path/QC/validation/validate_xml.py" ]] || { echo "Not a FormosanBank checkout: $formosanbank_path" >&2; exit 1; }
[[ "$run_id" =~ ^[A-Za-z0-9._-]+$ ]] || { echo "Run id contains unsupported characters: $run_id" >&2; exit 2; }
[[ -e "$out" ]] && { echo "QC output already exists: $out" >&2; exit 1; }
[[ -f "$repo_root/XML/Kavalan/chang-2000-kavalan-reference-grammar.xml" ]] || {
    echo "No XML to validate. Run CodeAndDocs/generate_xml.sh first." >&2
    exit 2
}
before_commit="$(git -C "$formosanbank_path" rev-parse HEAD)"
before_status="$(dependency_status)"

cd "$repo_root"
mkdir -p "$out/orthography_info"
export PYTHONDONTWRITEBYTECODE=1
export MPLCONFIGDIR="$temp_root/matplotlib"
mkdir -p "$MPLCONFIGDIR"

run() {
    local output="$1" status=0
    shift
    "$@" >"$out/$output" 2>&1 || status=$?
    if [[ "$status" -ne 0 ]]; then
        echo "QC step $output failed (exit $status); its last lines:" >&2
        tail -n 15 "$out/$output" >&2
        exit "$status"
    fi
}

recorded="$(sed -n 's/.*"formosanbank_commit"[[:space:]]*:[[:space:]]*"\([0-9a-f]\{40\}\)".*/\1/p' CodeAndDocs/provenance.json)"
printf 'formosanbank_commit=%s\nrecorded_build_commit=%s\n' "$before_commit" "$recorded" >"$out/00_reference_state.txt"

# The build's own checks: the XML is what a fresh build gives, and the inventory and conventions hold. The scan is
# private and absent from a FormosanBank checkout, where the audit checks the tracked ledgers only.
run 01_build_check.txt "$python_bin" CodeAndDocs/build_xml.py --check --stats
if [[ -f "Private/source/basecamp/12.original.pdf" ]]; then
    run 02_audit_source.txt "$python_bin" CodeAndDocs/audit_source.py
else
    run 02_audit_source.txt "$python_bin" CodeAndDocs/audit_source.py --source-free
fi
run 03_orthography_detector.txt "$python_bin" "$formosanbank_path/QC/utilities/orthography_detector.py" XML \
    --orthographies "$formosanbank_path/Orthographies" --language ckv --combine
run 04_validate_xml.txt "$python_bin" "$formosanbank_path/QC/validation/validate_xml.py" \
    --csv "$out/04_validate_xml_findings.csv" --published-corpora "$formosanbank_path/Corpora" \
    by_path --path XML --no-exit-on-hard
run 05_validate_text.txt "$python_bin" "$formosanbank_path/QC/validation/validate_text.py" \
    --csv "$out/05_validate_text_findings.csv" by_path --path XML --no-exit-on-hard
run 06_validate_glosses.txt "$python_bin" "$formosanbank_path/QC/validation/validate_glosses.py" \
    --csv "$out/06_validate_glosses_findings.csv" by_path --path XML --no-exit-on-hard
run 07_validate_dialect.txt "$python_bin" "$formosanbank_path/QC/validation/validate_dialect.py" --path XML
run 08_validate_duplicates_original.txt "$python_bin" \
    "$formosanbank_path/QC/validation/validate_duplicate_sentences.py" by_path \
    --path XML --tier original --output "$out/08_duplicate_original.csv"
run 09_adjudicate.txt "$python_bin" CodeAndDocs/audit_qc_findings.py \
    --validate-xml "$out/04_validate_xml_findings.csv" \
    --validate-text "$out/05_validate_text_findings.csv" \
    --validate-glosses "$out/06_validate_glosses_findings.csv" \
    --duplicates-original "$out/08_duplicate_original.csv" \
    --output "$out/09_resolution_ledger.tsv"
run 10_orthography_extract.txt "$python_bin" "$formosanbank_path/QC/orthography/orthography_extract.py" \
    --corpus all --language All --kindOf standard --by_dialect true \
    --corpora_path XML --output_dir "$out/orthography_info"
run 11_validate_orthography.txt "$python_bin" "$formosanbank_path/QC/validation/validate_orthography.py" \
    --o_info "$out/orthography_info" --reference "$formosanbank_path/QC/validation/reference" --quiet
run 12_validate_vocabulary.txt "$python_bin" "$formosanbank_path/QC/validation/validate_vocabulary.py" \
    --o_info "$out/orthography_info" --reference "$formosanbank_path/QC/validation/reference" --quiet
run 13_tests.txt "$python_bin" -m pytest CodeAndDocs/tests -q -p no:cacheprovider

after_commit="$(git -C "$formosanbank_path" rev-parse HEAD)"
after_status="$(dependency_status)"
if [[ "$after_commit" != "$before_commit" || "$after_status" != "$before_status" ]]; then
    echo "FormosanBank dependency changed during QC; refusing success." >&2
    exit 2
fi
# Paths in the reports are written relative, so a run reads the same on any machine.
while IFS= read -r -d '' file; do
    QC_REPO_ROOT="$repo_root" QC_FB="$formosanbank_path" perl -pi -e \
        's/\Q$ENV{QC_REPO_ROOT}\E/<CORPUS>/g; s/\Q$ENV{QC_FB}\E/<FORMOSANBANK>/g; s/\r$//; s/[ \t]+$//' "$file"
done < <(find "$out" -type f \( -name '*.csv' -o -name '*.tsv' -o -name '*.txt' \) -print0)
printf 'qc_dir=%s\n' "$out"

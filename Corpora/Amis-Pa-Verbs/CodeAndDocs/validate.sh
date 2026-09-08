#!/usr/bin/env bash
# Validate existing output; generation is a separate command.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
FB="${FORMOSANBANK_ROOT:-$(cd "$HERE/../../.." && pwd)}"
PY="${PYTHON:-python3}"
export FORMOSANBANK_ROOT="$FB"
REPORT="${QC_REPORT_DIR:?Set QC_REPORT_DIR to a directory outside the corpus}"
mkdir -p "$REPORT"
REPORT="$(cd "$REPORT" && pwd)"
case "$REPORT/" in "$ROOT/"*) echo 'QC_REPORT_DIR must be outside the corpus' >&2; exit 2;; esac
printf 'check,exit_code\n' > "$REPORT/exit_codes.csv"
failed=0
run() {
    local name="$1" code=0
    shift
    "$@" > "$REPORT/$name.log" 2>&1 || code=$?
    printf '%s,%s\n' "$name" "$code" >> "$REPORT/exit_codes.csv"
    if [[ "$code" -ne 0 ]]; then failed=1; fi
}
run source-alignment "$PY" "$HERE/audit_source_alignment.py"
run source-tests "$PY" -m pytest -q -p no:cacheprovider "$HERE/tests"
for name in xml text glosses; do
    run "validate-$name" "$PY" "$FB/QC/validation/validate_$name.py" \
        by_path --path "$ROOT/XML" --no-exit-on-hard --csv "$REPORT/validate-$name.csv"
done
run gloss-structure "$PY" "$FB/QC/validation/audit_gloss_scrape.py" \
    --repo "$ROOT" --no-source --csv "$REPORT/gloss-structure.csv"
for tier in original standard; do
    run "duplicates-$tier" "$PY" "$FB/QC/validation/validate_duplicate_sentences.py" \
        by_path --path "$ROOT/XML" --tier "$tier" --output "$REPORT/duplicates-$tier.csv"
    run "extract-$tier" "$PY" "$FB/QC/orthography/orthography_extract.py" \
        --corpora_path "$ROOT/XML" --corpus all --language All --kindOf "$tier" \
        --by_dialect true --output_dir "$REPORT/orthography-$tier"
    run "orthography-$tier" "$PY" "$FB/QC/validation/validate_orthography.py" \
        --o_info "$REPORT/orthography-$tier" --reference "$FB/QC/validation/reference" --language Amis
done
run vocabulary "$PY" "$FB/QC/validation/validate_vocabulary.py" \
    --o_info "$REPORT/orthography-standard" --reference "$FB/QC/validation/reference" --language Amis
run conversion-Coastal "$PY" "$FB/QC/validation/validate_conversion_table.py" \
    "$HERE/source_orthography/Amis.tsv" "$FB/Orthographies/Ortho113/Amis.tsv" \
    "$HERE/wu_source_to_ortho113.tsv" --dialect Coastal \
    --output "$REPORT/conversion-Coastal.md"
run dialect "$PY" "$FB/QC/validation/validate_dialect.py" --path "$ROOT/XML"
run registries "$PY" "$FB/QC/validation/validate_registries.py" \
    --repo-root "$FB" --csv "$REPORT/registries.csv"
run port-readiness "$PY" "$FB/QC/validation/validate_port_readiness.py" \
    --corpus_path "$ROOT" --repo-root "$FB"
printf 'Review all findings and coverage in %s; command success is not a readiness verdict.\n' "$REPORT"
exit "$failed"

#!/usr/bin/env bash
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
FB="${FORMOSANBANK_ROOT:-$(cd "$HERE/../../.." && pwd)}"
PY="${PYTHON:-python3}"
: "${OUTPUT_DIR:?Set OUTPUT_DIR to a new absolute directory outside the corpus.}"
if [[ "$OUTPUT_DIR" != /* || -e "$OUTPUT_DIR" || ! -f "$FB/QC/validation/validate_xml.py" ]]; then
    echo "Use current FormosanBank and a new absolute OUTPUT_DIR." >&2
    exit 2
fi
case "$OUTPUT_DIR/" in "$ROOT/"*) echo "Keep reports outside the corpus." >&2; exit 2 ;; esac
mkdir -p "$OUTPUT_DIR/published-view" || exit 2
for corpus in "$FB/Corpora"/*; do
    [[ -d "$corpus" ]] || continue
    [[ "$(basename "$corpus")" == "FormosanBankGitBook" ]] && continue
    ln -s "$corpus" "$OUTPUT_DIR/published-view/$(basename "$corpus")" || exit 2
done
failed=0
run() {
    local label="$1"
    shift
    "$@" > "$OUTPUT_DIR/$label.log" 2>&1 || failed=1
    cat "$OUTPUT_DIR/$label.log"
}
run source "$PY" "$HERE/source_audit.py" --formosanbank "$FB"
run tests "$PY" -m unittest discover -s "$HERE/tests" -v
run xml "$PY" "$FB/QC/validation/validate_xml.py" by_path --path "$ROOT/XML" \
    --published-corpora "$OUTPUT_DIR/published-view" --no-exit-on-hard --csv "$OUTPUT_DIR/xml.csv"
for validator in text; do
    run "$validator" "$PY" "$FB/QC/validation/validate_$validator.py" by_path \
        --path "$ROOT/XML" --no-exit-on-hard --csv "$OUTPUT_DIR/$validator.csv"
done
for tier in original standard; do
    run "duplicates-$tier" "$PY" "$FB/QC/validation/validate_duplicate_sentences.py" by_path \
        --path "$ROOT/XML" --tier "$tier" --output "$OUTPUT_DIR/duplicates-$tier.csv"
    run "extract-$tier" "$PY" "$FB/QC/orthography/orthography_extract.py" \
        --corpora_path "$ROOT/XML" --corpus all --language All --kindOf "$tier" \
        --by_dialect true --output_dir "$OUTPUT_DIR/orthography-$tier"
    run "orthography-$tier" "$PY" "$FB/QC/validation/validate_orthography.py" \
        --o_info "$OUTPUT_DIR/orthography-$tier" --reference "$FB/QC/validation/reference"
done
run vocabulary "$PY" "$FB/QC/validation/validate_vocabulary.py" \
    --o_info "$OUTPUT_DIR/orthography-standard" --reference "$FB/QC/validation/reference"
run dialect "$PY" "$FB/QC/validation/validate_dialect.py" --path "$ROOT/XML"
run registries "$PY" "$FB/QC/validation/validate_registries.py" --repo-root "$FB" --csv "$OUTPUT_DIR/registries.csv"
run port "$PY" "$FB/QC/validation/validate_port_readiness.py" --corpus_path "$ROOT" --repo-root "$FB"
echo "No W/M or audio is supplied by this source; gloss, conversion-table, and audio checks do not apply. Review all findings before assigning readiness."
exit "$failed"

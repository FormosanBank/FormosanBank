#!/usr/bin/env bash
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
FB="${FORMOSANBANK_ROOT:-$(cd "$HERE/../../.." && pwd)}"
PY="${PYTHON:-python3}"
: "${OUTPUT_DIR:?Set OUTPUT_DIR to a new absolute directory outside the corpus.}"
if [[ "$OUTPUT_DIR" != /* || -e "$OUTPUT_DIR" || ! -f "$FB/QC/validation/validate_xml.py" ]]; then
    echo "Use a current FormosanBank checkout and a new absolute OUTPUT_DIR." >&2
    exit 2
fi
case "$OUTPUT_DIR/" in "$ROOT/"*) echo "Keep reports outside the corpus." >&2; exit 2 ;; esac
mkdir -p "$OUTPUT_DIR" || exit 2
VIEW="$OUTPUT_DIR/published-view"
mkdir "$VIEW" || exit 2
for corpus in "$FB/Corpora"/*; do
    [[ -d "$corpus" ]] || continue
    [[ "$(basename "$corpus")" == "SEALS33" ]] && continue
    ln -s "$corpus" "$VIEW/$(basename "$corpus")"
done
REFERENCE_VIEW="$OUTPUT_DIR/reference-view"
mkdir -p "$REFERENCE_VIEW/Saisiyat" "$REFERENCE_VIEW/Seediq" || exit 2
ln -s "$FB/QC/validation/reference/Saisiyat/default" "$REFERENCE_VIEW/Saisiyat/Saisiyat" || exit 2
ln -s "$FB/QC/validation/reference/Seediq/Default" "$REFERENCE_VIEW/Seediq/unknown" || exit 2
failed=0
run() {
    local label="$1"
    shift
    "$@" > "$OUTPUT_DIR/$label.log" 2>&1 || failed=1
    cat "$OUTPUT_DIR/$label.log"
}
run tests "$PY" -m pytest -c "$HERE/pyproject.toml" "$HERE/tests" -q
run source "$PY" "$HERE/scripts/source_audit.py" --json
# No --no-exit-on-hard: the S25 reconstruction-title findings are waived in
# CodeAndDocs/qc_waivers.tsv (POL-054) and reported as WAIVED, so these runs
# are genuinely clean. An unwaived HARD finding, or a waiver that matches no
# current finding, now fails here — which is what the corpus-local
# check_hard_findings.py used to do by hand.
run xml "$PY" "$FB/QC/validation/validate_xml.py" by_path --path "$ROOT/XML" \
    --published-corpora "$VIEW" --csv "$OUTPUT_DIR/xml.csv"
run text "$PY" "$FB/QC/validation/validate_text.py" by_path --path "$ROOT/XML" \
    --csv "$OUTPUT_DIR/text.csv"
run dialect "$PY" "$FB/QC/validation/validate_dialect.py" --path "$ROOT/XML"
run duplicates "$PY" "$FB/QC/validation/validate_duplicate_sentences.py" by_path \
    --path "$ROOT/XML" --tier standard --output "$OUTPUT_DIR/duplicates.csv"
for tier in original standard; do
    run "extract-$tier" "$PY" "$FB/QC/orthography/orthography_extract.py" \
        --corpora_path "$ROOT/XML" --corpus all --language All --kindOf "$tier" \
        --by_dialect true --output_dir "$OUTPUT_DIR/orthography-$tier"
    run "orthography-$tier" "$PY" "$FB/QC/validation/validate_orthography.py" \
        --o_info "$OUTPUT_DIR/orthography-$tier" --reference "$REFERENCE_VIEW"
done
run vocabulary "$PY" "$FB/QC/validation/validate_vocabulary.py" \
    --o_info "$OUTPUT_DIR/orthography-standard" --reference "$REFERENCE_VIEW"
run registries "$PY" "$FB/QC/validation/validate_registries.py" \
    --repo-root "$FB" --csv "$OUTPUT_DIR/registries.csv"
run port "$PY" "$FB/QC/validation/validate_port_readiness.py" --corpus_path "$ROOT" --repo-root "$FB"
exit "$failed"

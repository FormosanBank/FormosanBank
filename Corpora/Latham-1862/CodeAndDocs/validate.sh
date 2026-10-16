#!/usr/bin/env bash
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
FB="${FORMOSANBANK_ROOT:-$(cd "$HERE/../../.." && pwd)}"
PY="${PYTHON:-python3}"
: "${OUTPUT_DIR:?Set OUTPUT_DIR to a new absolute directory outside the corpus.}"

if [[ ! -f "$FB/QC/validation/validate_xml.py" ]]; then
    echo "FORMOSANBANK_ROOT must point to a current FormosanBank checkout." >&2
    exit 2
fi

if [[ "$OUTPUT_DIR" != /* || -e "$OUTPUT_DIR" ]]; then
    echo "OUTPUT_DIR must be a new absolute directory." >&2
    exit 2
fi
case "$OUTPUT_DIR/" in
    "$ROOT/"*) echo "Keep validation output outside the corpus." >&2; exit 2 ;;
esac
mkdir -p "$OUTPUT_DIR" || exit 2
VIEW="$OUTPUT_DIR/published-update-view"
mkdir "$VIEW" || exit 2
for corpus in "$FB/Corpora"/*; do
    [[ -d "$corpus" ]] || continue
    [[ "$(basename "$corpus")" == "Latham-1862" ]] && continue
    ln -s "$corpus" "$VIEW/$(basename "$corpus")"
done

failed=0
run() {
    local label="$1"
    shift
    "$@" > "$OUTPUT_DIR/$label.log" 2>&1 || failed=1
    cat "$OUTPUT_DIR/$label.log"
}

run tests "$PY" -m unittest discover -s "$HERE/tests" -v
run source_coverage "$PY" "$HERE/audit_source_coverage.py"
run xml "$PY" "$FB/QC/validation/validate_xml.py" by_path \
    --path "$ROOT/XML" --published-corpora "$VIEW" \
    --csv "$OUTPUT_DIR/validate_xml_findings.csv"
run text "$PY" "$FB/QC/validation/validate_text.py" by_path \
    --path "$ROOT/XML" --csv "$OUTPUT_DIR/validate_text_findings.csv"
run glosses "$PY" "$FB/QC/validation/validate_glosses.py" by_path \
    --path "$ROOT/XML" --csv "$OUTPUT_DIR/validate_glosses_findings.csv"
run dialect "$PY" "$FB/QC/validation/validate_dialect.py" --path "$ROOT/XML"
run duplicates "$PY" "$FB/QC/validation/validate_duplicate_sentences.py" by_path \
    --path "$ROOT/XML" --tier original --output "$OUTPUT_DIR/duplicate_original_findings.csv"
# No orthography extraction or comparison: POL-058. standards.csv leaves
# standard_orthography blank for both Babuza-Favorlang and Siraya, and
# neither has an inventory under QC/validation/reference/, so
# validate_orthography.py had nothing to compare against and skipped
# both. The extraction before it wrote profiles nothing read.
run registries "$PY" "$FB/QC/validation/validate_registries.py" \
    --repo-root "$FB" --csv "$OUTPUT_DIR/validate_registries.csv"
run port "$PY" "$FB/QC/validation/validate_port_readiness.py" \
    --corpus_path "$ROOT" --repo-root "$FB"
run review "$PY" "$HERE/scripts/adjudicate_qc.py" \
    --run-dir "$OUTPUT_DIR" --source-ledger "$HERE/source_ledger.tsv" \
    --duplicate-review "$HERE/duplicate_group_review.csv" --xml-root "$ROOT/XML"

# No audio, and no standard orthography or vocabulary tier to validate.
exit "$failed"

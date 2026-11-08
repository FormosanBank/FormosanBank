#!/usr/bin/env bash
# Committed QC run for this corpus (POL-047: validators live here, never in
# generate_xml.sh). Runs the corpus tests, the handoff checks, the shared
# validators, and adjudicate_qc.py, which fails unless every finding matches
# the reviewed inventory. Uses the tools in the FormosanBank checkout that
# contains this corpus; nothing is pinned (POL-048/POL-052).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORPUS_ROOT="$(cd "$ROOT/.." && pwd)"
FB="$(cd "$CORPUS_ROOT/../.." && pwd -P)"
PY="${PYTHON:-python3}"
OUTPUT_DIR="${OUTPUT_DIR:-$(mktemp -u "${TMPDIR:-/tmp}/yedda-qc.XXXXXX")}"
PORT_REPO_ROOT="${PORT_REPO_ROOT:-$FB}"

test -f "$FB/QC/validation/validate_xml.py"
actual_commit="$(git -C "$FB" rev-parse HEAD 2>/dev/null || echo unknown)"
if [[ "$OUTPUT_DIR" != /* ]]; then
    echo "OUTPUT_DIR must be absolute." >&2
    exit 2
fi
case "$OUTPUT_DIR/" in
    "$CORPUS_ROOT/"*)
        echo "OUTPUT_DIR must be outside this corpus: $OUTPUT_DIR" >&2
        exit 2
        ;;
esac
if [[ -e "$OUTPUT_DIR" ]]; then
    echo "OUTPUT_DIR must not already exist: $OUTPUT_DIR" >&2
    exit 2
fi
mkdir -p "$OUTPUT_DIR"

published_update_view="$OUTPUT_DIR/published-update-view"
mkdir -p "$published_update_view"
for corpus in "$FB/Corpora"/*; do
    [[ -d "$corpus" ]] || continue
    [[ "$(basename "$corpus")" == "YeddaPalemeqBlog" ]] && continue
    ln -s "$corpus" "$published_update_view/$(basename "$corpus")"
done

run_logged() {
    local label="$1"
    shift
    {
        printf 'command:'
        printf ' %q' "$@"
        printf '\nworking_directory: %s\n' "$CORPUS_ROOT"
        cd "$CORPUS_ROOT"
        "$@"
    } 2>&1 | tee "$OUTPUT_DIR/$label.log"
}

{
    echo "timestamp_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "corpus_root: $CORPUS_ROOT"
    echo "formosanbank_root: $FB"
    echo "port_repo_root: $PORT_REPO_ROOT"
    echo "formosanbank_commit: $actual_commit"
    echo "output_dir: $OUTPUT_DIR"
    echo "python: $PY"
    "$PY" --version
} > "$OUTPUT_DIR/00_environment.log"

run_logged 01_tests "$PY" -m unittest discover -s "$ROOT/tests" -v
run_logged 02_verify_handoff "$PY" "$ROOT/scripts/verify_handoff.py"
run_logged 03_issue_review "$PY" "$ROOT/scripts/audit_issue_1.py" --check-only
run_logged 04_validate_xml "$PY" \
    "$FB/QC/validation/validate_xml.py" by_path \
    --path "$CORPUS_ROOT/XML" --published-corpora "$published_update_view" \
    --no-exit-on-hard --csv "$OUTPUT_DIR/validate_xml_findings.csv"
run_logged 05_validate_text "$PY" \
    "$FB/QC/validation/validate_text.py" by_path \
    --path "$CORPUS_ROOT/XML" --no-exit-on-hard \
    --csv "$OUTPUT_DIR/validate_text_findings.csv"
run_logged 06_validate_glosses "$PY" \
    "$FB/QC/validation/validate_glosses.py" \
    --no-exit-on-hard --csv "$OUTPUT_DIR/validate_glosses_findings.csv" \
    by_path --path "$CORPUS_ROOT/XML"
run_logged 07_validate_dialect "$PY" \
    "$FB/QC/validation/validate_dialect.py" --path "$CORPUS_ROOT/XML"
run_logged 08_duplicate_original "$PY" \
    "$FB/QC/validation/validate_duplicate_sentences.py" by_path \
    --path "$CORPUS_ROOT/XML" --tier original \
    --output "$OUTPUT_DIR/duplicate_original_findings.csv"
run_logged 09_duplicate_standard "$PY" \
    "$FB/QC/validation/validate_duplicate_sentences.py" by_path \
    --path "$CORPUS_ROOT/XML" --tier standard \
    --output "$OUTPUT_DIR/duplicate_standard_findings.csv"
run_logged 10_orthography_detector "$PY" \
    "$FB/QC/utilities/orthography_detector.py" "$CORPUS_ROOT/XML" --combine
run_logged 11_port_readiness "$PY" \
    "$FB/QC/validation/validate_port_readiness.py" \
    --corpus_path "$CORPUS_ROOT" --repo-root "$PORT_REPO_ROOT"
run_logged 12_review_findings "$PY" \
    "$ROOT/scripts/adjudicate_qc.py" \
    --run-dir "$OUTPUT_DIR" --xml-root "$CORPUS_ROOT/XML"

echo "QC completed against FormosanBank $actual_commit: $OUTPUT_DIR"

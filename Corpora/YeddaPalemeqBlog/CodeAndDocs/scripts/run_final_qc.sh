#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CORPUS_ROOT="$(cd "$ROOT/.." && pwd)"
: "${VALIDATOR_ROOT:?Set VALIDATOR_ROOT to an isolated pinned validator checkout.}"
: "${VALIDATOR_PYTHON:?Set VALIDATOR_PYTHON to the validator Python executable.}"
: "${OUTPUT_DIR:?Set OUTPUT_DIR to a new absolute directory outside this repository.}"
EXPECTED_VALIDATOR_COMMIT="3a3c47c220520113f747e6a2d441494000e13c4b"

if [[ ! -x "$VALIDATOR_PYTHON" ]]; then
    echo "VALIDATOR_PYTHON is not executable: $VALIDATOR_PYTHON" >&2
    exit 2
fi
if ! git -C "$VALIDATOR_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "VALIDATOR_ROOT is not a Git checkout: $VALIDATOR_ROOT" >&2
    exit 2
fi
VALIDATOR_ROOT="$(cd "$VALIDATOR_ROOT" && pwd -P)"
actual_validator_commit="$(git -C "$VALIDATOR_ROOT" rev-parse HEAD)"
if [[ "$actual_validator_commit" != "$EXPECTED_VALIDATOR_COMMIT" ]]; then
    echo "Validator commit mismatch: expected $EXPECTED_VALIDATOR_COMMIT, got $actual_validator_commit" >&2
    exit 2
fi
if [[ -n "$(git -C "$VALIDATOR_ROOT" status --porcelain)" ]]; then
    echo "Validator checkout is dirty: $VALIDATOR_ROOT" >&2
    exit 2
fi
if [[ -z "${PORT_REPO_ROOT:-}" ]]; then
    PORT_REPO_ROOT="$(git -C "$CORPUS_ROOT" rev-parse --show-toplevel)"
fi
PORT_REPO_ROOT="$(cd "$PORT_REPO_ROOT" && pwd -P)"
if [[ "$OUTPUT_DIR" != /* ]]; then
    echo "OUTPUT_DIR must be absolute." >&2
    exit 2
fi
case "$OUTPUT_DIR/" in
    "$CORPUS_ROOT/"*)
        echo "OUTPUT_DIR must be outside this repository: $OUTPUT_DIR" >&2
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
for corpus in "$VALIDATOR_ROOT/Corpora"/*; do
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
    echo "validator_root: $VALIDATOR_ROOT"
    echo "port_repo_root: $PORT_REPO_ROOT"
    echo "validator_commit: $actual_validator_commit"
    echo "output_dir: $OUTPUT_DIR"
    echo "validator_python: $VALIDATOR_PYTHON"
    "$VALIDATOR_PYTHON" --version
} > "$OUTPUT_DIR/00_environment.log"

run_logged 01_tests "$VALIDATOR_PYTHON" -m unittest discover -s "$ROOT/tests" -v
run_logged 02_verify_handoff "$VALIDATOR_PYTHON" "$ROOT/scripts/verify_handoff.py"
run_logged 03_issue_review "$VALIDATOR_PYTHON" "$ROOT/scripts/audit_issue_1.py" --check-only
run_logged 04_validate_xml "$VALIDATOR_PYTHON" \
    "$VALIDATOR_ROOT/QC/validation/validate_xml.py" by_path \
    --path "$CORPUS_ROOT/XML" --published-corpora "$published_update_view" \
    --no-exit-on-hard --csv "$OUTPUT_DIR/validate_xml_findings.csv"
run_logged 05_validate_text "$VALIDATOR_PYTHON" \
    "$VALIDATOR_ROOT/QC/validation/validate_text.py" by_path \
    --path "$CORPUS_ROOT/XML" --no-exit-on-hard \
    --csv "$OUTPUT_DIR/validate_text_findings.csv"
run_logged 06_validate_glosses "$VALIDATOR_PYTHON" \
    "$VALIDATOR_ROOT/QC/validation/validate_glosses.py" \
    --no-exit-on-hard --csv "$OUTPUT_DIR/validate_glosses_findings.csv" \
    by_path --path "$CORPUS_ROOT/XML"
run_logged 07_validate_dialect "$VALIDATOR_PYTHON" \
    "$VALIDATOR_ROOT/QC/validation/validate_dialect.py" --path "$CORPUS_ROOT/XML"
run_logged 08_duplicate_original "$VALIDATOR_PYTHON" \
    "$VALIDATOR_ROOT/QC/validation/validate_duplicate_sentences.py" by_path \
    --path "$CORPUS_ROOT/XML" --tier original \
    --output "$OUTPUT_DIR/duplicate_original_findings.csv"
run_logged 09_duplicate_standard "$VALIDATOR_PYTHON" \
    "$VALIDATOR_ROOT/QC/validation/validate_duplicate_sentences.py" by_path \
    --path "$CORPUS_ROOT/XML" --tier standard \
    --output "$OUTPUT_DIR/duplicate_standard_findings.csv"
run_logged 10_orthography_detector "$VALIDATOR_PYTHON" \
    "$VALIDATOR_ROOT/QC/utilities/orthography_detector.py" "$CORPUS_ROOT/XML" --combine
run_logged 11_port_readiness "$VALIDATOR_PYTHON" \
    "$VALIDATOR_ROOT/QC/validation/validate_port_readiness.py" \
    --corpus_path "$CORPUS_ROOT" --repo-root "$PORT_REPO_ROOT"
run_logged 12_review_findings "$VALIDATOR_PYTHON" \
    "$ROOT/scripts/adjudicate_qc.py" \
    --run-dir "$OUTPUT_DIR" --xml-root "$CORPUS_ROOT/XML"

echo "Pinned current-authority QC completed: $OUTPUT_DIR"

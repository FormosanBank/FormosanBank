#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CORPUS_ROOT="$(cd "$ROOT/.." && pwd)"
REPO_ROOT="$(git -C "$CORPUS_ROOT" rev-parse --show-toplevel)"
CORPUS_REL="${CORPUS_ROOT#"$REPO_ROOT/"}"
: "${VALIDATOR_ROOT:?Set VALIDATOR_ROOT to an isolated pinned validator checkout.}"
: "${VALIDATOR_PYTHON:?Set VALIDATOR_PYTHON to the validator Python executable.}"
: "${OUTPUT_DIR:?Set OUTPUT_DIR to a new absolute directory outside this repository.}"

if [[ "$OUTPUT_DIR" != /* ]]; then
    echo "OUTPUT_DIR must be absolute." >&2
    exit 2
fi
case "$OUTPUT_DIR/" in
    "$REPO_ROOT/"*)
        echo "OUTPUT_DIR must be outside this repository: $OUTPUT_DIR" >&2
        exit 2
        ;;
esac
if [[ -e "$OUTPUT_DIR" ]]; then
    echo "OUTPUT_DIR must not already exist: $OUTPUT_DIR" >&2
    exit 2
fi
if [[ -n "$(git -C "$REPO_ROOT" status --porcelain)" ]]; then
    echo "Reproduction requires a clean committed checkout." >&2
    exit 2
fi

mkdir -p "$OUTPUT_DIR/first/work" "$OUTPUT_DIR/second/work"
git -C "$REPO_ROOT" archive HEAD -- "$CORPUS_REL" | tar -x -C "$OUTPUT_DIR/first/work"
git -C "$REPO_ROOT" archive HEAD -- "$CORPUS_REL" | tar -x -C "$OUTPUT_DIR/second/work"

for pass in first second; do
    work="$OUTPUT_DIR/$pass/work/$CORPUS_REL"
    VALIDATOR_ROOT="$VALIDATOR_ROOT" \
    VALIDATOR_PYTHON="$VALIDATOR_PYTHON" \
    RUN_LOG_DIR="$OUTPUT_DIR/$pass/rebuild-logs" \
        "$work/CodeAndDocs/scripts/rebuild_xml.sh"
done

first="$OUTPUT_DIR/first/work/$CORPUS_REL"
second="$OUTPUT_DIR/second/work/$CORPUS_REL"
diff -ru "$CORPUS_ROOT/XML" "$first/XML"
diff -ru "$ROOT/data/formosanbank_audit" "$first/CodeAndDocs/data/formosanbank_audit"
diff -ru "$first/XML" "$second/XML"
diff -ru "$first/CodeAndDocs/data/formosanbank_audit" \
    "$second/CodeAndDocs/data/formosanbank_audit"

VALIDATOR_ROOT="$VALIDATOR_ROOT" \
VALIDATOR_PYTHON="$VALIDATOR_PYTHON" \
PORT_REPO_ROOT="$REPO_ROOT" \
OUTPUT_DIR="$OUTPUT_DIR/final-qc" \
    "$second/CodeAndDocs/scripts/run_final_qc.sh"

echo "Reproduction and pinned current-authority QC completed: $OUTPUT_DIR"
echo "REPRO_BASE=$OUTPUT_DIR"

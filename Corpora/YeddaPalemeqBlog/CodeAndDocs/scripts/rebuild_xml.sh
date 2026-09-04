#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CORPUS_ROOT="$(cd "$ROOT/.." && pwd)"
: "${VALIDATOR_ROOT:?Set VALIDATOR_ROOT to an isolated pinned FormosanBank checkout.}"
: "${VALIDATOR_PYTHON:?Set VALIDATOR_PYTHON to the validator Python executable.}"
: "${RUN_LOG_DIR:?Set RUN_LOG_DIR to a new absolute directory outside this repository.}"
EXPECTED_VALIDATOR_COMMIT="e00edf3d83ecfdce37392a73b3d2796446f44195"

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
if [[ "$RUN_LOG_DIR" != /* ]]; then
    echo "RUN_LOG_DIR must be absolute." >&2
    exit 2
fi
case "$RUN_LOG_DIR/" in
    "$CORPUS_ROOT/"*)
        echo "RUN_LOG_DIR must be outside this repository: $RUN_LOG_DIR" >&2
        exit 2
        ;;
esac
if [[ -e "$RUN_LOG_DIR" ]]; then
    echo "RUN_LOG_DIR must not already exist: $RUN_LOG_DIR" >&2
    exit 2
fi
mkdir -p "$RUN_LOG_DIR"

"$VALIDATOR_PYTHON" "$ROOT/scripts/build_xml.py"
"$VALIDATOR_PYTHON" \
    "$VALIDATOR_ROOT/QC/cleaning/clean_xml.py" \
    --corpora_path "$CORPUS_ROOT/XML"
if [[ -f "$CORPUS_ROOT/XML/cleaner_warnings.csv" ]]; then
    mv "$CORPUS_ROOT/XML/cleaner_warnings.csv" "$RUN_LOG_DIR/cleaner_warnings.csv"
fi
"$VALIDATOR_PYTHON" "$ROOT/scripts/fix_m_tier.py" \
    --corpora_path "$CORPUS_ROOT/XML" \
    --formosanbank_root "$VALIDATOR_ROOT"
"$VALIDATOR_PYTHON" \
    "$VALIDATOR_ROOT/QC/utilities/standardize.py" \
    --corpora_path "$CORPUS_ROOT/XML" --remove_accents
"$VALIDATOR_PYTHON" \
    "$VALIDATOR_ROOT/QC/utilities/add_phonology.py" \
    --corpora_path "$CORPUS_ROOT/XML" --orthography Ortho113
"$VALIDATOR_PYTHON" "$ROOT/scripts/audit_issue_1.py" --check-only
"$VALIDATOR_PYTHON" "$ROOT/scripts/finalize_manifest.py"
"$VALIDATOR_PYTHON" -m unittest discover -s "$ROOT/tests" -v
"$VALIDATOR_PYTHON" "$ROOT/scripts/verify_handoff.py"

echo "Rebuilt 671 canonical Yedda records with pinned current authority."

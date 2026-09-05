#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CORPUS_ROOT="$(cd "$ROOT/.." && pwd)"

# The shared QC utilities come from the FormosanBank checkout that contains this
# corpus, so a rebuild picks up the CURRENT tools by default. Point
# VALIDATOR_ROOT at another checkout to reproduce against a specific version.
VALIDATOR_ROOT="${VALIDATOR_ROOT:-$CORPUS_ROOT/../..}"
VALIDATOR_PYTHON="${VALIDATOR_PYTHON:-python3}"
RUN_LOG_DIR="${RUN_LOG_DIR:-$(mktemp -d -t yedda-rebuild-XXXXXX)}"

# The published XML was last regenerated against this FormosanBank commit.
# Informational only: the shared utilities move on, and a newer commit is the
# expected case. Recorded here and in README.md so a reproduction can pin it.
REFERENCE_VALIDATOR_COMMIT="c3ea819d23e6025cfbd9dda7cb7b594c4c2cc304"

if ! command -v "$VALIDATOR_PYTHON" >/dev/null 2>&1 && [[ ! -x "$VALIDATOR_PYTHON" ]]; then
    echo "VALIDATOR_PYTHON is not executable: $VALIDATOR_PYTHON" >&2
    exit 2
fi
if [[ ! -f "$VALIDATOR_ROOT/QC/cleaning/clean_xml.py" ]]; then
    echo "VALIDATOR_ROOT is not a FormosanBank checkout: $VALIDATOR_ROOT" >&2
    exit 2
fi
VALIDATOR_ROOT="$(cd "$VALIDATOR_ROOT" && pwd -P)"
actual_validator_commit="$(git -C "$VALIDATOR_ROOT" rev-parse HEAD 2>/dev/null || echo unknown)"
if [[ "$actual_validator_commit" != "$REFERENCE_VALIDATOR_COMMIT" ]]; then
    echo "note: FormosanBank at $actual_validator_commit; XML/ was last built at $REFERENCE_VALIDATOR_COMMIT" >&2
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

echo "Rebuilt 671 canonical Yedda records against $actual_validator_commit."
echo "Per-run logs: $RUN_LOG_DIR"

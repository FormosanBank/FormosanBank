#!/usr/bin/env bash
# make.sh — regenerate the whole NTUFormosanCorpus from source and check it.
#
# The JSONs under grammar/, sentence/ and story/ are this corpus's source.
# Nothing is scraped, so there is no refresh step: those JSONs are the
# starting point and everything in ../XML/ is derived from them.
#
#   ./make.sh [--with-audio]
#
#   --with-audio   also download the Grammar/Stories audio (slow; needs
#                  network). XML generation does not require it: AUDIO
#                  elements are dropped by sentinel URL, not by checking
#                  files on disk.
#
# This is a thin wrapper. The build itself is pipeline/build.sh, documented
# in pipeline/README.md; make.sh adds the source-coverage audit, the
# re-application of recorded hand edits, and a validation summary.
#
# Rerunning is safe: build.sh regenerates each subcorpus from scratch in a
# temp dir and installs it only on success.

set -euo pipefail

WITH_AUDIO=0
for arg in "$@"; do
  case "$arg" in
    --with-audio) WITH_AUDIO=1 ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "unknown argument: $arg (try --help)" >&2; exit 2 ;;
  esac
done

CODEDOCS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORPUS="$(dirname "$CODEDOCS")"
DEFAULT_BANK="$(cd "$CORPUS/../.." && pwd)"
BANK="${FORMOSANBANK_ROOT:-$DEFAULT_BANK}"

PY="${PYTHON:-$BANK/.venv/bin/python}"
[[ -x "$PY" ]] || PY="$(command -v python3)"
export PYTHON="$PY"

if [[ ! -f "$BANK/QC/cleaning/clean_xml.py" ]]; then
  echo "FormosanBank checkout not found at $BANK; set FORMOSANBANK_ROOT" >&2
  exit 2
fi

step() { printf '\n=== %s ===\n' "$*"; }

if (( WITH_AUDIO )); then
  step "Download audio"
  bash "$CORPUS/download_audio_data.sh"
fi

step "Build XML from the source JSONs (pipeline/build.sh)"
"$CODEDOCS/pipeline/build.sh" all

step "Re-apply recorded hand edits (no-op when manual_edits.xml is absent)"
if [[ -f "$CODEDOCS/manual_edits.xml" ]]; then
  "$PY" "$BANK/QC/cleaning/apply_manual_edits.py" --corpus "$CORPUS"
else
  echo "  no manual_edits.xml; nothing to re-apply"
fi

step "Source coverage audit"
"$PY" "$CODEDOCS/scripts/audit_source_coverage.py" --repo-root "$CORPUS"

step "Validation summary (HARD findings do not abort)"
"$PY" "$BANK/QC/validation/validate_text.py" by_path --path "$CORPUS/XML" \
  --no-exit-on-hard --log_dir "$CORPUS/logs"
"$PY" "$BANK/QC/validation/validate_glosses.py" by_path --path "$CORPUS/XML" \
  --no-exit-on-hard --log_dir "$CORPUS/logs"

step "Regression check against the recorded baseline"
if [[ -x "$CODEDOCS/qa/run_regression.sh" ]]; then
  "$CODEDOCS/qa/run_regression.sh" || echo "  regression check reported movement; see qa/README.md"
else
  echo "  qa/ harness not present in this checkout; skipped"
fi

step "Done. Review 'git diff' before committing."

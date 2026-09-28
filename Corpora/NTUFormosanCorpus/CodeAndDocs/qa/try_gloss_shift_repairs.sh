#!/usr/bin/env bash
# try_gloss_shift_repairs.sh -- trial gloss-shift repairs without publishing them.
#
#   ./try_gloss_shift_repairs.sh <grammar|sentences|stories> [statuses] [report.md]
#
# Builds one subcorpus with the repair rows of the given statuses in force
# (default: accepted,proposed), compares it with the committed XML using
# gloss_shift_blast_radius.py, and puts the committed XML back. Refuses to run
# if that subcorpus's XML has uncommitted changes, since it restores from git.
# Set KEEP_DIR to keep both builds (<KEEP_DIR>/baseline, <KEEP_DIR>/candidate).
set -euo pipefail
SUB="${1:?usage: $0 <grammar|sentences|stories> [statuses] [report.md]}"
STATUSES="${2:-accepted,proposed}"
QA="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEDOCS="$(dirname "$QA")"; CORPUS="$(dirname "$CODEDOCS")"
BANK="$(cd "$CORPUS/../.." && pwd)"
case "$SUB" in grammar) OUT=Grammar ;; sentences) OUT=Sentences ;; stories) OUT=Stories ;;
  *) echo "unknown subcorpus: $SUB" >&2; exit 2 ;; esac
REPORT="${3:-$(mktemp -d)/blast_radius_${SUB}.md}"
PY="${PYTHON:-$BANK/.venv/bin/python}"; [[ -x "$PY" ]] || PY="$(command -v python3)"
export PYTHON="$PY"

if [[ -n "$(git -C "$CORPUS" status --porcelain -- "XML/$OUT")" ]]; then
  echo "XML/$OUT has uncommitted changes; commit or discard them first" >&2; exit 2
fi
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
cp -r "$CORPUS/XML/$OUT" "$WORK/baseline"
restore() { git -C "$CORPUS" checkout -q -- "XML/$OUT"; git -C "$CORPUS" clean -fdq -- "XML/$OUT"; }
trap 'restore; rm -rf "$WORK"' EXIT

echo "=== building $OUT with gloss-shift statuses: $STATUSES"
NTU_GLOSS_SHIFT_STATUSES="$STATUSES" "$CODEDOCS/pipeline/build.sh" "$SUB" > "$WORK/build.log" 2>&1 \
  || { tail -30 "$WORK/build.log"; exit 1; }
grep -E "gloss-shift repairs applied" "$WORK/build.log" || echo "  (no gloss-shift repairs applied)"
cp -r "$CORPUS/XML/$OUT" "$WORK/candidate"

if [[ -n "${KEEP_DIR:-}" ]]; then
  mkdir -p "$KEEP_DIR"; rm -rf "$KEEP_DIR/baseline" "$KEEP_DIR/candidate"
  cp -r "$WORK/baseline" "$WORK/candidate" "$KEEP_DIR/"
fi
echo "=== blast radius"
set +e
"$PY" "$QA/gloss_shift_blast_radius.py" --baseline "$WORK/baseline" --candidate "$WORK/candidate" \
  --statuses "$STATUSES" --report "$REPORT"
rc=$?
exit $rc

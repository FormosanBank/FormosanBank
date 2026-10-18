#!/usr/bin/env bash
# try_gloss_shift_repairs.sh -- trial gloss-shift repairs without publishing them.
#
#   ./try_gloss_shift_repairs.sh <grammar|sentences|stories> [statuses] [report.md]
#
# Builds one subcorpus twice into scratch directories -- a baseline with no
# repair rows in force, and a candidate with the rows of the given statuses
# (default: accepted,proposed) -- and compares them with
# gloss_shift_blast_radius.py. XML/ is never written.
#
# Both builds stop at the pre-cleanup checkpoint (build.sh's
# NTU_BUILD_CHECKPOINT): the steps that withdraw unsupported word and morpheme
# tiers, borrow donor morphemes, and delete empty translations exist to deal
# with what could NOT be fixed, so they should count neither for nor against a
# fix. Set CHECKPOINT=published to compare the full builds instead.
#
# Environment: KEEP_DIR keeps both builds (<KEEP_DIR>/baseline, /candidate);
# NTU_GLOSS_SHIFT_TABLE points at another repairs table; PYTHON as build.sh.
set -euo pipefail
SUB="${1:?usage: $0 <grammar|sentences|stories> [statuses] [report.md]}"
STATUSES="${2:-accepted,proposed}"
QA="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEDOCS="$(dirname "$QA")"; CORPUS="$(dirname "$CODEDOCS")"
BANK="$(cd "$CORPUS/../.." && pwd)"
case "$SUB" in grammar) OUT=Grammar ;; sentences) OUT=Sentences ;; stories) OUT=Stories ;;
  *) echo "unknown subcorpus: $SUB" >&2; exit 2 ;; esac
case "${CHECKPOINT:-pre-cleanup}" in
  pre-cleanup) CP=pre-cleanup ;; published) CP="" ;;
  *) echo "CHECKPOINT must be pre-cleanup or published" >&2; exit 2 ;; esac
REPORT="${3:-$(mktemp -d)/blast_radius_${SUB}.md}"
PY="${PYTHON:-$BANK/.venv/bin/python}"; [[ -x "$PY" ]] || PY="$(command -v python3)"
export PYTHON="$PY"

WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
build() {   # $1 = label, $2 = statuses in force ("none" for the baseline)
  echo "=== building $OUT ($1; checkpoint: ${CP:-published}; statuses: $2)"
  NTU_BUILD_OUT="$WORK/$1" NTU_BUILD_CHECKPOINT="$CP" NTU_GLOSS_SHIFT_STATUSES="$2" \
    "$CODEDOCS/pipeline/build.sh" "$SUB" > "$WORK/$1.log" 2>&1 \
    || { tail -30 "$WORK/$1.log"; exit 1; }
  grep -E "gloss-shift repairs applied" "$WORK/$1.log" || echo "  (no gloss-shift repairs applied)"
}
build baseline none
build candidate "$STATUSES"

if [[ -n "${KEEP_DIR:-}" ]]; then
  mkdir -p "$KEEP_DIR"; rm -rf "$KEEP_DIR/baseline" "$KEEP_DIR/candidate"
  cp -r "$WORK/baseline/$OUT" "$KEEP_DIR/baseline"; cp -r "$WORK/candidate/$OUT" "$KEEP_DIR/candidate"
fi
echo "=== blast radius"
set +e
"$PY" "$QA/gloss_shift_blast_radius.py" --baseline "$WORK/baseline/$OUT" \
  --candidate "$WORK/candidate/$OUT" --statuses "$STATUSES" --report "$REPORT"

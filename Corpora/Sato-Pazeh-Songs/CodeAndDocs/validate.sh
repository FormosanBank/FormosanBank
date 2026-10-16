#!/usr/bin/env bash
# QC for this corpus. Separate from generate_xml.sh on purpose (POL-047):
# a build that a failing validator can abort cannot be used to investigate
# the failure.
#
#   ./validate.sh [/path/to/FormosanBank] [output-dir]
#
# Runs the corpus's own audit and unit tests, then the shared validators.
# Reports every result and exits non-zero if any of them failed, rather than
# stopping at the first.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
FB="${1:-${FORMOSANBANK_ROOT:-$(cd "$HERE/../../.." && pwd)}}"
if [ -z "${FB:-}" ] || [ ! -d "$FB/QC" ]; then
  echo "usage: $0 /path/to/FormosanBank [output-dir]   (or set FORMOSANBANK_ROOT)" >&2
  exit 2
fi
FB="$(cd "$FB" && pwd)"
# Default under logs/, which is gitignored bank-wide (CLAUDE.md: per-corpus
# logs land in gitignored logs/ subdirs). qc-output/ is not ignored and would
# leave the published corpus dirty.
OUT="${2:-$ROOT/logs/$(date -u +%Y%m%dT%H%M%SZ)}"
PY="${PYTHON:-python3}"
XML="$ROOT/XML"

mkdir -p "$OUT"
FAIL=0
run() {
  local name="$1"; shift
  "$@" > "$OUT/$name.log" 2>&1
  local code=$?
  printf '%-34s exit=%s  %s\n' "$name" "$code" "$OUT/$name.log"
  [ "$code" -ne 0 ] && FAIL=1
  return 0
}

run audit_output          "$PY" "$HERE/audit_output.py"
run unit_tests            "$PY" -m unittest discover -s "$HERE/tests"

run validate_xml          "$PY" "$FB/QC/validation/validate_xml.py" \
                             --csv "$OUT/validate_xml.csv" by_path --path "$XML"
run validate_text         "$PY" "$FB/QC/validation/validate_text.py" \
                             --csv "$OUT/validate_text.csv" by_path --path "$XML"
run validate_glosses      "$PY" "$FB/QC/validation/validate_glosses.py" \
                             --csv "$OUT/validate_glosses.csv" by_path --path "$XML"
run validate_dialect      "$PY" "$FB/QC/validation/validate_dialect.py" --path "$XML"
run audit_gloss_scrape    "$PY" "$FB/QC/validation/audit_gloss_scrape.py" \
                             --xml "$XML" --no-source \
                             --csv "$OUT/audit_gloss_scrape.csv"
run validate_duplicates   "$PY" "$FB/QC/validation/validate_duplicate_sentences.py" \
                             by_path --path "$XML" --tier original --verbose \
                             --output "$OUT/duplicate_sentences.csv"
run validate_port_readiness "$PY" "$FB/QC/validation/validate_port_readiness.py" \
                             --corpus_path "$ROOT" --repo-root "$FB"

echo "output=$OUT"
exit "$FAIL"

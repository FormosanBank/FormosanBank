#!/usr/bin/env bash
# POL-047 entry point: committed source tables -> published XML/.
#
#   ./generate_xml.sh [/path/to/FormosanBank]
#
# Offline and self-contained (POL-048). Everything this build reads is either
# under CodeAndDocs/ or in the FormosanBank checkout it is pointed at: no
# second clone, no pinned commit, no Private/ directory, no environment
# variable naming any of those. The private scan is provenance, not an input —
# the original tier is transcribed into CodeAndDocs/intermediate/, and
# check_source.py verifies the PDF's identity separately when someone has it.
#
# Build only. Validators are validate.sh's job and are never invoked here: a
# build that a failing validator can abort cannot be used to investigate the
# failure.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
FB="${1:-${FORMOSANBANK_ROOT:-$(cd "$HERE/../../.." && pwd)}}"
if [ -z "${FB:-}" ] || [ ! -f "$FB/QC/cleaning/clean_xml.py" ]; then
  echo "usage: $0 /path/to/FormosanBank   (or set FORMOSANBANK_ROOT)" >&2
  exit 2
fi
FB="$(cd "$FB" && pwd)"
PY="${PYTHON:-python3}"

# POL-052: report which FormosanBank commit the committed XML was built
# against. Informational only — read from provenance.json so the SHA lives in
# one place, never compared against to decide whether to run, and never used
# to go find another checkout. A different commit is fine; the build proceeds.
REFERENCE_COMMIT="$(sed -n 's/.*"formosanbank_commit"[[:space:]]*:[[:space:]]*"\([0-9a-f]\{40\}\)".*/\1/p' "$HERE/provenance.json")"
HEAD_COMMIT="$(git -C "$FB" rev-parse HEAD 2>/dev/null || echo unknown)"
if [ "$HEAD_COMMIT" != "$REFERENCE_COMMIT" ]; then
  echo "note: FormosanBank at $HEAD_COMMIT; XML/ was last built at $REFERENCE_COMMIT" >&2
fi

# 1. Rebuild the source ledger from the reviewed rows and the excluded blocks.
"$PY" "$HERE/build_ledger.py"

# 2. Corpus-local parsing: reviewed rows -> the original tier (POL-046's
#    standing exception). Overwrites XML/ wholesale, which is what makes the
#    entry point idempotent (POL-047).
"$PY" "$HERE/generate_xml.py"

# 3. Shared cleaner.
"$PY" "$FB/QC/cleaning/clean_xml.py" --corpora_path "$ROOT/XML"

# Steps 4 and 5 of the canonical order are deliberately absent — see the
# POL-047 deviation note in ../README.md.

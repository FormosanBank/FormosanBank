#!/usr/bin/env bash
# POL-047 entry point: committed source snapshot -> published XML/.
#
#   ./generate_xml.sh [/path/to/FormosanBank]
#
# Offline and self-contained (POL-048): reads only CodeAndDocs/, writes only
# XML/. Re-fetching the source page is refresh_source.sh's job and is never
# invoked from here. Validators are validate.sh's job and are never invoked
# from here either — a build that a failing validator can abort cannot be used
# to investigate the failure.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
FB="${1:-${FORMOSANBANK_ROOT:-$(cd "$HERE/../../.." && pwd)}}"
FB="$(cd "$FB" && pwd)"
PY="${PYTHON:-python3}"

test -f "$FB/QC/cleaning/clean_xml.py"

# POL-052: report which FormosanBank commit the published bytes were built
# against, so a rerun's diff is readable. Informational only — read from
# provenance.json so the SHA lives in exactly one place, never compared
# against to decide whether to run, and never used to go find another
# checkout. A different commit is fine; the build proceeds either way.
REFERENCE_COMMIT="$(sed -n 's/.*"formosanbank_commit"[[:space:]]*:[[:space:]]*"\([0-9a-f]\{40\}\)".*/\1/p' "$HERE/provenance.json")"
HEAD_COMMIT="$(git -C "$FB" rev-parse HEAD 2>/dev/null || echo unknown)"
if [ "$HEAD_COMMIT" != "$REFERENCE_COMMIT" ]; then
  echo "note: FormosanBank at $HEAD_COMMIT; XML/ was last built at $REFERENCE_COMMIT" >&2
fi

"$PY" "$HERE/scripts/build_xml.py"
"$PY" "$FB/QC/cleaning/clean_xml.py" --corpora_path "$ROOT/XML"
"$PY" "$FB/QC/utilities/standardize.py" --remove_accents --corpora_path "$ROOT/XML"
"$PY" "$FB/QC/utilities/add_phonology.py" --corpora_path "$ROOT/XML" --orthography Ortho94

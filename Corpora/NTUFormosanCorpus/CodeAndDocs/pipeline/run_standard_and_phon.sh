#!/usr/bin/env bash
# Task B: the standard tier and the phonemic tier, both keyed to Ortho94.
#
# The NTU source documentation states its orthography as Ortho94, so:
#   * the ORIGINAL PHON is generated from Ortho94's letter-to-sound rules;
#   * the STANDARD tier is produced by converting 94 -> 113 per language, 113
#     being FormosanBank's common orthography (add_phonology then derives the
#     standard PHON from it).
# Earlier processing declared the original to be Ortho113 and produced the
# standard tier with --remove_accents, i.e. it described the source as an
# orthography it was not written in.
#
# usage: run_standard_and_phon.sh <xml dir> <conversion-tables dir>
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
XML=${1:?usage: run_standard_and_phon.sh <xml dir> <tables dir>}
TABLES=${2:-$ROOT/Orthographies/ConversionTables}
cd "$ROOT"
# Honour an explicit $PYTHON (build.sh sets it); fall back to the repo venv,
# then to whatever python3 is on PATH. A git worktree has no .venv, so
# sourcing it unconditionally would silently leave the wrong interpreter.
PY="${PYTHON:-$ROOT/.venv/bin/python}"
[[ -x "$PY" ]] || PY="$(command -v python3)"
export PYTHONPATH=$ROOT

for dir in "$XML"/*/; do
  lang=$(basename "$dir")
  tsv="$TABLES/${lang}_94_113.tsv"
  if [[ ! -f "$tsv" ]]; then
    echo "  $lang: NO 94->113 table; skipped (would need --remove_accents, which"
    echo "         loses the dialect-aware handling the table path gives)"
    continue
  fi
  # An empty table (headers only) is not a no-op: standardize still resolves the
  # source profile through the naming convention, so accents are removed and
  # capital variants derived.
  out=$("$PY" "$ROOT/QC/utilities/standardize.py" \
          --tsv_path "$tsv" --corpora_path "$XML" --corpus "$lang" 2>&1)
  echo "  $lang: $(printf '%s' "$out" | grep -cE 'standardized successfully') file(s) standardized"
done

# Original PHON from Ortho94; the standard PHON keeps Ortho113 where a table
# exists, which add_phonology handles itself.
"$PY" "$ROOT/QC/utilities/add_phonology.py" --corpora_path "$XML" --orthography Ortho94 2>&1 | tail -3

# A form with no letters has no phonology: punctuation ',', '.', and the '?'
# uncertain-transcription placeholder (which the analyst may still gloss, e.g.
# NMLZ). add_phonology writes an empty PHON for those, and V073 HARD requires a
# PHON to have content -- so the element is dropped rather than filled with
# something invented.
python3 - "$XML" <<'PY'
import sys, pathlib
from lxml import etree
removed = files = 0
for path in sorted(pathlib.Path(sys.argv[1]).rglob("*.xml")):
    tree = etree.parse(str(path)); changed = False
    for phon in list(tree.getroot().iter("PHON")):
        if not (phon.text or "").strip():
            phon.getparent().remove(phon); removed += 1; changed = True
    if changed:
        tree.write(str(path), encoding="utf-8", xml_declaration=True); files += 1
print(f"  empty PHON removed: {removed} in {files} file(s)")
PY

#!/usr/bin/env bash
# THE entry point (POL-047): rebuild the published XML/ from the PARADISEC
# metadata committed in CodeAndDocs/Metadata/. Usage, from anywhere:
#
#   Corpora/TangRecordingsOfTaroko/CodeAndDocs/generate_xml.sh
#
# PYTHON selects the interpreter. The audio is not an input.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORPUS="$(cd "$ROOT/.." && pwd)"
PYTHON="${PYTHON:-python3}"
export PYTHONDONTWRITEBYTECODE=1

# No FormosanBank-commit check here, unlike corpora that call the shared QC
# utilities: this build runs none of them, so the tool version cannot move the
# output. The commit the published XML was built against is recorded in
# provenance.json for the record (POL-052), and nothing reads it.

# 1. One audio-only TEXT per recording enumerated in Metadata/.
"$PYTHON" "$ROOT/make_xml.py"

# Steps 2-5 of the POL-047 pipeline -- apply_manual_edits.py, clean_xml.py,
# standardize.py, add_phonology.py -- have nothing to act on. The recordings are
# untranscribed, so the XML carries no FORM, PHON, TRANSL, W or M tier to clean,
# standardize or phonologize, and there are no manual edits. See the README.

echo "Rebuilt $CORPUS/XML/Truku/"

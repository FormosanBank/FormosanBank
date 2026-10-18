#!/usr/bin/env bash
# Committed QC run for ILRDF_Dicts (POL-047: kept out of generate_xml.sh).
#
#   CodeAndDocs/validate.sh
#
# 1. the published-id audit against source_data/published_ids.csv
# 2. the corpus's own tests
set -euo pipefail

CODEDOCS="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"
export PYTHONDONTWRITEBYTECODE=1
cd "$CODEDOCS"

printf '\n== audit: published ids against source_data/published_ids.csv ==\n'
"$PYTHON" "$CODEDOCS/generate_xml.py" audit

printf '\n== tests ==\n'
# -o addopts= drops the repo-wide --cov options: no .coverage/coverage.xml here.
"$PYTHON" -m pytest -q -p no:cacheprovider -o addopts= "$CODEDOCS/tests"

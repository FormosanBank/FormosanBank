#!/usr/bin/env bash
# POL-047 source acquisition. Re-fetches the SEALS 33 national-languages page
# and rewrites CodeAndDocs/source_snapshot.json.
#
# NEVER invoked by generate_xml.sh: the build is offline and reads only the
# committed snapshot, so a rebuild can never depend on the page still being up
# or still being the page that was reviewed.
#
#   ./refresh_source.sh --check   compare the live page with the committed
#                                 snapshot; exit 1 and print a diff on any
#                                 difference. Changes nothing. Safe to run.
#   ./refresh_source.sh           overwrite the snapshot from the live page.
#                                 A refresh is a source change: review the
#                                 diff, then re-run generate_xml.sh and
#                                 validate.sh before committing anything.
#
# Requires network access and CodeAndDocs/requirements.txt.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-python3}"

exec "$PY" "$HERE/scripts/scrape_source.py" "$@"

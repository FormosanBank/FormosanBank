#!/usr/bin/env bash
# refresh_source.sh — re-fetch the source from kanakanavu.info (POL-047).
#
#   CodeAndDocs/source/html/   every page, bytes as served          (committed)
#   CodeAndDocs/source/*.tsv   manifest + links not downloaded      (committed)
#   Audio/                     the MP3 and MP4 recordings           (gitignored)
#
# Never invoked by generate_xml.sh. Safe to rerun: pages are overwritten (so
# `git diff CodeAndDocs/source` shows any upstream change) and a recording
# already on disk with the server's byte count is not fetched again.
# Exit status: 0 ok, 1 a fetch failed, 3 a link of an unrecognised type.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"          # CodeAndDocs/
CORPUS="$(cd "$HERE/.." && pwd)"
# Python: $PYTHON, else this repo's .venv, else FormosanBank's (when installed
# under Corpora/<Name>/). Needs requests, beautifulsoup4, lxml.
PY="${PYTHON:-}"
if [ -z "$PY" ]; then
  if [ -x "$CORPUS/.venv/bin/python3" ]; then PY="$CORPUS/.venv/bin/python3"
  elif [ -x "$CORPUS/../../.venv/bin/python3" ]; then PY="$CORPUS/../../.venv/bin/python3"
  else echo "refresh_source.sh: no Python venv found; set PYTHON" >&2; exit 2; fi
fi

exec "$PY" "$HERE/scrape_site.py" --out "$HERE/source" --media-dir "$CORPUS/Audio" --root "$CORPUS" "$@"

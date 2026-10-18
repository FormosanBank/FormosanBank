#!/usr/bin/env bash
# POL-047 source acquisition for the Wikipedias corpus: re-download the
# article text from the five live wikis (ami, tay, pwn, szy, trv) with the
# original scraper, download.py, into CodeAndDocs/Articles/<Language>/.
#
# NEVER invoked by generate_xml.sh. The build reads only the committed POL-035
# snapshot (pre_correction_snapshot/), so a rebuild never depends on the wikis
# being reachable or unchanged. A refresh therefore changes NO published data
# by itself: Articles/ is raw plain text for review (e.g. to see what the wikis
# have added since the June 2026 scrape). Turning it into published XML is a
# re-scrape -- the historical text-to-XML steps (clean_articles.py and the
# others listed in the README) re-run, reviewed, and a new snapshot committed
# -- and needs the maintainer's decision first.
#
#   ./refresh_source.sh               download every title in the committed
#                                     Titles/ lists (the June 2026 inventory).
#   ./refresh_source.sh --new-titles  first delete Titles/* so download.py
#                                     re-lists every article on each wiki
#                                     (Titles/ is tracked: `git diff` shows the
#                                     change, `git checkout` restores it).
#
# Refuses to run if Articles/ already exists: download.py skips any file that
# is already there, so a second run into the same folder would silently mix
# two download dates. Move the old folder aside first.
#
# Requires network access to *.wikipedia.org and the packages in
# CodeAndDocs/requirements.txt (pip install -r CodeAndDocs/requirements.txt).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-python3}"

case "${1:-}" in
    "") ;;
    --new-titles) ;;
    *) sed -n '2,27p' "$0" >&2; exit 2 ;;
esac

"$PY" -c "import wikipediaapi, requests, regex, tqdm" 2>/dev/null || {
    echo "needs: pip install -r $HERE/requirements.txt" >&2; exit 2; }

if [[ -e "$HERE/Articles" ]]; then
    echo "$HERE/Articles already exists; move it aside first (see header)." >&2
    exit 2
fi

if [[ "${1:-}" == "--new-titles" ]]; then
    rm -f "$HERE"/Titles/ami "$HERE"/Titles/tay "$HERE"/Titles/pwn \
          "$HERE"/Titles/szy "$HERE"/Titles/trv
fi

exec "$PY" "$HERE/download.py"

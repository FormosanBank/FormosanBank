#!/usr/bin/env bash
# POL-047 source acquisition. Fetches NTU's published source JSONs at the release
# pinned in source_release.tsv (github.com/liao961120/glossParser, gh-pages),
# writes them into grammar/ sentence/ story/, and rewrites source_snapshot.json.
#
# NEVER invoked by make.sh or pipeline/build.sh: the build reads only the
# committed JSONs, so a rebuild never depends on NTU's site.
#
#   ./refresh_source.sh --check    compare the committed JSONs with the pinned
#                                  release; exit 1 on any difference. Safe.
#   ./refresh_source.sh --latest   report whether NTU has published a newer
#                                  release than the one pinned.
#   ./refresh_source.sh            write the pinned release. A source change:
#                                  rebuild, review the XML diff, then commit.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-python3}"
exec "$PY" "$HERE/scripts/fetch_source_release.py" "$@"

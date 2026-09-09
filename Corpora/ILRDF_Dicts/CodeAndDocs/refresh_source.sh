#!/usr/bin/env bash
# FULL REGENERATION ONLY — this is not part of reproduction.
#
# Re-scrapes the ILRDF dictionary API into source_data/snapshots/*.json.gz and
# rewrites source_data/source_manifest.json with fresh SHA-256 hashes.
#
# Requires network access to https://e-dictionary.ilrdf.org.tw/. Running this
# CHANGES THE SOURCE OF TRUTH: the snapshots are the boundary of this corpus,
# and everything downstream is derived from them. Afterwards:
#
#   1. review the snapshot diff — an upstream edit can add, remove or reword
#      records, and each of those moves published ids;
#   2. run make_xml.sh to rebuild XML/ from the new snapshots;
#   3. regenerate the id ledger and review it:
#        python generate_xml.py ledger --write
#      Every added or removed id must be a deliberate, explained change.
#
# To reproduce the published corpus you do NOT need this script. Use
# make_xml.sh, which works entirely from the committed snapshots.
set -euo pipefail

CODEDOCS="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${FORMOSANBANK_PYTHON:-python3}"

"$PYTHON" "$CODEDOCS/refresh_source.py" "$@"

cat <<'NEXT'

Snapshots refreshed. This changed the source of truth.

Next:
  1. review the snapshot diff
  2. ./make_xml.sh
  3. python generate_xml.py ledger --write   (then review the id diff)
NEXT

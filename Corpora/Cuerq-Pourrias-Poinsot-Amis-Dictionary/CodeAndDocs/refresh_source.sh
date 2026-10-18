#!/usr/bin/env bash
# refresh_source.sh — re-pull the two build inputs from their pinned upstream commits (POL-047, optional step).
# Never called by generate_xml.sh. Needs network access to GitHub.
#
#   source/pourrias-poinsot.txt   wildjcrt/amis-chinese-poinsot-onefile @ 365cfce…
#   source/toufu.sq3              miaoski/amis-chinese-poinsot (branch toufu) @ a35e2cb…
#
# The commits are pinned in fetch_sources.py and repeated, with each file's SHA-256, in build_amis_chinese_xml.py
# (SOURCE_*_COMMIT, SOURCE_*_SHA256); the corpus tests check the files against those hashes. To move to a newer
# upstream commit, change the pin in both places, run this script, then rebuild with generate_xml.sh.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
PY="${PYTHON:-python3}"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
"$PY" "$HERE/fetch_sources.py" --sources-dir "$TMP"
mkdir -p "$HERE/source"
cp "$TMP/amis-chinese-poinsot-onefile/pourrias-poinsot.txt" "$HERE/source/pourrias-poinsot.txt"
cp "$TMP/amis-chinese-poinsot-toufu/toufu.sq3" "$HERE/source/toufu.sq3"
( cd "$HERE/source" && sha256sum pourrias-poinsot.txt toufu.sq3 )

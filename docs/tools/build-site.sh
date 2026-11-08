#!/usr/bin/env bash
# Build every edition of the documentation site into ./site and check it.
set -euo pipefail
exec python "$(dirname "${BASH_SOURCE[0]}")/build_site.py" "$@"

#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

exec "${PYTHON:-python3}" "$REPO_ROOT/QC/utilities/download_audio.py" \
  --corpus WilangYutasVideos "$@"

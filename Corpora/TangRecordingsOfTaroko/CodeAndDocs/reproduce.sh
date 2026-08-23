#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
python_bin=${PYTHON:-python3}

"$python_bin" "$repo_root/verify_sources.py"
"$python_bin" "$repo_root/make_xml.py"

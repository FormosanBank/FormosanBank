#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python3 CodeAndDocs/build_xml.py
cmp XML/Thao/li_2014_conjunction_in_thao.xml Final_XML/Thao/li_2014_conjunction_in_thao.xml
python3 CodeAndDocs/audit_source_fidelity.py
echo "Reproduction complete: draft and final XML byte-match; source audit passes."

#!/usr/bin/env bash
# POL-047: THE entry point. Source -> published XML/, and nothing else.
#
# Build only. No validator runs here: a build that cannot finish because a
# validator failed cannot be used to investigate the failure. Validation lives
# in CodeAndDocs/validate.sh and is run separately.
#
# Runs against whatever FormosanBank checkout it is pointed at -- never a pinned
# commit. The dependency is treated as read-only: the commit is recorded before
# and after, and the run refuses to report success if it changed anything there.
#
#   CodeAndDocs/generate_xml.sh      (finds FormosanBank: see formosanbank_path.sh)
#   FORMOSANBANK_PATH=/path/to/FormosanBank CodeAndDocs/generate_xml.sh
#
# Idempotent: re-running over a clean checkout leaves `git status` empty.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
source "$(dirname "${BASH_SOURCE[0]}")/formosanbank_path.sh"
python_bin="${FORMOSANBANK_PYTHON:-$formosanbank_path/.venv/bin/python3}"
temp_root="$(mktemp -d "${TMPDIR:-/tmp}/seediq-chang-build.XXXXXX")"
trap 'rm -rf -- "$temp_root"' EXIT

test -x "$python_bin"
test -f "$formosanbank_path/QC/cleaning/clean_xml.py"
before_commit="$(git -C "$formosanbank_path" rev-parse HEAD)"
before_status="$(dependency_status)"

cd "$repo_root"
export MPLCONFIGDIR="$temp_root/matplotlib"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONHASHSEED=0
mkdir -p "$MPLCONFIGDIR"

# 1. corpus-local parsing (POL-046's standing exception)
"$python_bin" CodeAndDocs/transcribe_chapter5.py
"$python_bin" CodeAndDocs/build_xml.py

# 2-5. the shared tools, in POL-047's canonical order
"$python_bin" "$formosanbank_path/QC/cleaning/apply_manual_edits.py" \
    --corpora_path XML
"$python_bin" "$formosanbank_path/QC/cleaning/clean_xml.py" \
    --corpora_path XML --warnings_dir CodeAndDocs
"$python_bin" "$formosanbank_path/QC/utilities/standardize.py" \
    --remove_accents --hard-remove-segmentation --corpora_path XML
"$python_bin" "$formosanbank_path/QC/utilities/add_phonology.py" \
    --corpora_path XML

after_commit="$(git -C "$formosanbank_path" rev-parse HEAD)"
after_status="$(dependency_status)"
if [[ "$after_commit" != "$before_commit" || "$after_status" != "$before_status" ]]; then
    echo "FormosanBank dependency changed during the build; refusing success." >&2
    exit 2
fi

# POL-052: record which tools built these bytes.
"$python_bin" - "$formosanbank_path" "$after_commit" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

_, formosanbank_path, commit = sys.argv
root = Path(__file__).resolve().parent if "__file__" in dir() else Path.cwd()
xml_dir = Path("XML/Seediq")
provenance = Path("CodeAndDocs/provenance.json")
data = json.loads(provenance.read_text(encoding="utf-8"))
data["formosanbank_commit"] = commit
data["built"] = __import__("datetime").date.today().isoformat()
data["xml_sha256"] = {
    path.name: hashlib.sha256(path.read_bytes()).hexdigest()
    for path in sorted(xml_dir.glob("*.xml"))
}
provenance.write_text(
    json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(f"provenance.json: FormosanBank {commit}")
PY

echo "Built XML/Seediq/ against FormosanBank $after_commit"

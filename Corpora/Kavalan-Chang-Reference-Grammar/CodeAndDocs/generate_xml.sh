#!/usr/bin/env bash
# POL-047: THE entry point. The reviewed transcription -> published XML/, and nothing else.
#
# Build only. No validator runs here: a build that cannot finish because a check failed cannot be used to
# investigate the failure. The checks are in CodeAndDocs/validate.sh (maintainer, audit round 1, 2026-11-09:
# "Move both to validate.sh").
#
# Runs with the tools of whatever FormosanBank checkout it finds (formosanbank_path.sh), normally main at HEAD, never
# a pinned commit (POL-048, POL-052). That checkout is read-only: the run refuses success if it changed anything there.
#
#   CodeAndDocs/generate_xml.sh
#   FORMOSANBANK_PATH=/path/to/FormosanBank CodeAndDocs/generate_xml.sh
#
# Idempotent: re-running over a clean checkout leaves `git status` empty. provenance.json is rewritten only when
# the XML changes.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
source "$(dirname "${BASH_SOURCE[0]}")/formosanbank_path.sh"
python_bin="${FORMOSANBANK_PYTHON:-$formosanbank_path/.venv/bin/python3}"
temp_root="$(mktemp -d "${TMPDIR:-/tmp}/kavalan-chang-build.XXXXXX")"
trap 'rm -rf -- "$temp_root"' EXIT

[[ -x "$python_bin" ]] || {
    echo "No Python at $python_bin: give the FormosanBank checkout a .venv, or set FORMOSANBANK_PYTHON" >&2
    exit 1
}
[[ -f "$formosanbank_path/QC/cleaning/clean_xml.py" ]] || { echo "Not a FormosanBank checkout: $formosanbank_path" >&2; exit 1; }
before_commit="$(git -C "$formosanbank_path" rev-parse HEAD)"
before_status="$(dependency_status)"

cd "$repo_root"
export PYTHONDONTWRITEBYTECODE=1
export MPLCONFIGDIR="$temp_root/matplotlib"
mkdir -p "$MPLCONFIGDIR"
xml="XML/Kavalan/chang-2000-kavalan-reference-grammar.xml"
before_xml="$(sha256sum "$xml" 2>/dev/null | cut -c1-64 || true)"

# 1. Corpus-local parsing (POL-046's standing exception): the transcription with the review's corrections and the
#    decision tables -> original tier, glosses, translations.
"$python_bin" CodeAndDocs/build_xml.py --stats

# 2. Manual edits: none. Record-level decisions are the content-gated tables build_xml.py reads.

# 3-5. The shared tools, in POL-047's canonical order (maintainer, audit round 1, 2026-11-09: clean_xml "in its
#      canonical place").
"$python_bin" "$formosanbank_path/QC/cleaning/clean_xml.py" \
    --corpora_path XML --warnings_dir "$temp_root"
if [[ -f "$temp_root/cleaner_warnings.csv" ]]; then
    echo "cleaner_warnings.csv: $(( $(wc -l < "$temp_root/cleaner_warnings.csv") - 1 )) rows" >&2
fi
# The book's spelling (TaiwanNandao) differs from Ortho113 in two letters, converted together: r -> l, l -> d.
"$python_bin" "$formosanbank_path/QC/utilities/standardize.py" --corpora_path XML \
    --tsv_path "$formosanbank_path/Orthographies/ConversionTables/Kavalan_TaiwanNandao_113.tsv"
# POL-033: standardize writes its warning report into XML/; it is a per-run report, not corpus data.
if [[ -f XML/standardize_warnings.csv ]]; then
    echo "standardize_warnings.csv: $(( $(wc -l < XML/standardize_warnings.csv) - 1 )) rows" >&2
    mv XML/standardize_warnings.csv "$temp_root/"
fi
# PHON: original from the TaiwanNandao profile, standard from Ortho113 (standards.csv).
"$python_bin" "$formosanbank_path/QC/utilities/add_phonology.py" \
    --corpora_path XML --orthography TaiwanNandao

# Standard gloss tier (POL-036, additive): Glossing/ConversionTables/Kavalan-Chang-Reference-Grammar.tsv
"$python_bin" "$formosanbank_path/QC/glossing/apply_gloss_standard.py" \
    --path XML \
    --table "$formosanbank_path/Glossing/ConversionTables/Kavalan-Chang-Reference-Grammar.tsv" \
    --rules "$formosanbank_path/Glossing/ConversionTables/Kavalan-Chang-Reference-Grammar.rules.tsv" --write

after_commit="$(git -C "$formosanbank_path" rev-parse HEAD)"
after_status="$(dependency_status)"
if [[ "$after_commit" != "$before_commit" || "$after_status" != "$before_status" ]]; then
    echo "FormosanBank dependency changed during the build; refusing success." >&2
    exit 2
fi

# POL-052: record which tools built these bytes, when the bytes change.
after_xml="$(sha256sum "$xml" | cut -c1-64)"
if [[ "$after_xml" != "$before_xml" ]] || ! grep -q '"formosanbank_commit"' CodeAndDocs/provenance.json 2>/dev/null; then
    "$python_bin" - "$after_commit" <<'PY'
import datetime
import json
import sys
from pathlib import Path

path = Path("CodeAndDocs/provenance.json")
data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
data["_note"] = ("The FormosanBank commit this corpus's XML/ was last built against (POL-052). Provenance only: "
                 "generate_xml.sh rewrites it when the XML changes; nothing reads it as an input.")
data["formosanbank_commit"] = sys.argv[1]
data["built"] = datetime.date.today().isoformat()
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"provenance.json: FormosanBank {sys.argv[1]}")
PY
fi

echo "Built XML/Kavalan/ against FormosanBank $after_commit"

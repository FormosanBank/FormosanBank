#!/usr/bin/env bash
# POL-047: validation, kept out of the build.
#
# generate_xml.sh produces XML/ and stops. This script only reads it. The split
# matters because a build that aborts on a validator failure cannot be used to
# investigate that failure -- you need the XML the validator objected to.
#
# Run the build first:
#   FORMOSANBANK_PATH=/path/to/FormosanBank CodeAndDocs/generate_xml.sh
#   FORMOSANBANK_PATH=/path/to/FormosanBank CodeAndDocs/validate.sh
#
# Writes every validator's stdout, stderr and exit code under qc-output/, then
# adjudicate_findings.py requires zero HARD findings and a disposition for every
# SOFT one. Nothing here writes to XML/.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
source "$(dirname "${BASH_SOURCE[0]}")/formosanbank_path.sh"
python_bin="${FORMOSANBANK_PYTHON:-$formosanbank_path/.venv/bin/python3}"
output_dir="$repo_root/qc-output/${QC_RUN:-latest}"
temp_root="$(mktemp -d "${TMPDIR:-/tmp}/seediq-chang-validate.XXXXXX")"

cleanup() {
    rm -rf -- "$temp_root"
}
trap cleanup EXIT

test -x "$python_bin"
test -f "$formosanbank_path/QC/validation/validate_xml.py"
if [[ ! -f "$repo_root/XML/Seediq/chang-2000-seediq-reference-grammar.xml" ]]; then
    echo "No XML to validate. Run CodeAndDocs/generate_xml.sh first." >&2
    exit 2
fi
# Validation runs against whatever FormosanBank checkout it is pointed at
# (POL-047: current tools, never a pinned old commit). The commit is recorded;
# it is not a gate. What IS enforced, below, is that the run leaves that
# checkout byte-identical -- the dependency is read-only.
before_commit="$(git -C "$formosanbank_path" rev-parse HEAD)"
before_status="$(dependency_status)"

cd "$repo_root"
rm -rf -- "$output_dir"
mkdir -p "$output_dir"
printf '%s\n' "${QC_RUN:-latest}" >qc-output/latest_run.txt
export MPLCONFIGDIR="$temp_root/matplotlib"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONHASHSEED=0
mkdir -p "$MPLCONFIGDIR"

printf '{\n  "path": "%s",\n  "before_commit": "%s",\n  "before_dirty": %s\n}\n' \
    "$formosanbank_path" "$before_commit" \
    "$([[ -n "$before_status" ]] && echo true || echo false)" \
    >"$output_dir/public_dependency.json"

failures=0
run() {
    local name="$1"
    shift
    set +e
    "$@" >"$output_dir/$name.stdout.txt" 2>"$output_dir/$name.stderr.txt"
    local code=$?
    set -e
    printf '%s,%s\n' "$name" "$code" >>"$output_dir/exit_codes.csv"
    if [[ "$code" -ne 0 ]]; then
        failures=1
    fi
    return 0
}

printf 'check,exit_code\n' >"$output_dir/exit_codes.csv"
# Diagnostic, not a gate: a human reads the detector's ranking.
run orthography_detector "$python_bin" "$formosanbank_path/QC/utilities/orthography_detector.py" \
    XML --orthographies "$formosanbank_path/Orthographies" --language trv --combine
run source_alignment "$python_bin" CodeAndDocs/audit_source_alignment.py
run wellformed "$python_bin" CodeAndDocs/check_wellformed.py
run validate_xml "$python_bin" "$formosanbank_path/QC/validation/validate_xml.py" by_path \
    --path XML --csv "$output_dir/validate_xml.csv" \
    --published-corpora "$formosanbank_path/Corpora"
run validate_text "$python_bin" "$formosanbank_path/QC/validation/validate_text.py" by_path \
    --path XML --csv "$output_dir/validate_text.csv" --no-exit-on-hard
run validate_glosses "$python_bin" "$formosanbank_path/QC/validation/validate_glosses.py" by_path \
    --path XML --csv "$output_dir/validate_glosses.csv" --no-exit-on-hard
run validate_dialect "$python_bin" "$formosanbank_path/QC/validation/validate_dialect.py" \
    --path XML/Seediq
run duplicate_original "$python_bin" "$formosanbank_path/QC/validation/validate_duplicate_sentences.py" by_path \
    --path XML --tier original --output "$output_dir/duplicate_original.csv"
run duplicate_standard "$python_bin" "$formosanbank_path/QC/validation/validate_duplicate_sentences.py" by_path \
    --path XML --tier standard --output "$output_dir/duplicate_standard.csv"

for tier in original standard; do
    orthography_dir="$temp_root/orthography_$tier"
    run "orthography_extract_$tier" "$python_bin" "$formosanbank_path/QC/orthography/orthography_extract.py" \
        --corpora_path XML --corpus all --language All --kindOf "$tier" \
        --by_dialect true --output_dir "$orthography_dir"
    run "validate_orthography_$tier" "$python_bin" "$formosanbank_path/QC/validation/validate_orthography.py" \
        --o_info "$orthography_dir" --reference "$formosanbank_path/QC/validation/reference" \
        --language Seediq
    run "validate_vocabulary_$tier" "$python_bin" "$formosanbank_path/QC/validation/validate_vocabulary.py" \
        --o_info "$orthography_dir" --reference "$formosanbank_path/QC/validation/reference" \
        --language Seediq
done

after_commit="$(git -C "$formosanbank_path" rev-parse HEAD)"
after_status="$(dependency_status)"
# Read-only assertion: the run must leave the dependency exactly as it found
# it. Compare before/after, rather than demanding a clean tree -- a checkout
# with unrelated untracked files is fine, a checkout this run modified is not.
if [[ "$after_commit" != "$before_commit" || "$after_status" != "$before_status" ]]; then
    echo "FormosanBank dependency changed during QC; refusing success." >&2
    exit 2
fi

python3 - "$output_dir/public_dependency.json" "$after_commit" <<'PY'
import json
import sys

path, after_commit = sys.argv[1:]
with open(path, encoding="utf-8") as handle:
    data = json.load(handle)
data["after_commit"] = after_commit
data["dependency_unchanged"] = True
with open(path, "w", encoding="utf-8") as handle:
    json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
    handle.write("\n")
PY

run adjudicate_findings python3 CodeAndDocs/adjudicate_findings.py --qc-dir "$output_dir"

python3 - "$output_dir" "$repo_root" "$formosanbank_path" "$temp_root" <<'PY'
import sys
from pathlib import Path

output_dir = Path(sys.argv[1])
replacements = {
    sys.argv[2].encode(): b"$REPO_ROOT",
    sys.argv[3].encode(): b"$FORMOSANBANK_PATH",
    sys.argv[4].encode(): b"$TMPDIR",
}
for csv_path in output_dir.rglob("*.csv"):
    csv_path.write_bytes(csv_path.read_bytes().replace(b"\r\n", b"\n"))
for evidence_path in output_dir.rglob("*"):
    if not evidence_path.is_file():
        continue
    data = evidence_path.read_bytes()
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        continue
    for source, replacement in replacements.items():
        data = data.replace(source, replacement)
    if data:
        data = data.rstrip(b"\r\n") + b"\n"
    evidence_path.write_bytes(data)
PY

if [[ "$failures" -ne 0 ]]; then
    echo "One or more QC commands failed; see $output_dir/exit_codes.csv." >&2
    exit 1
fi

echo "Final QC artifacts: $output_dir"

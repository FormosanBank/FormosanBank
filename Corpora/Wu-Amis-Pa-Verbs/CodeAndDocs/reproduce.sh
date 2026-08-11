#!/usr/bin/env bash
set -euo pipefail

corpus_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
formosanbank_path="${FORMOSANBANK_PATH:-$(cd "$corpus_root/../.." && pwd -P)}"
python_bin="${FORMOSANBANK_PYTHON:-${PYTHON:-$formosanbank_path/.venv/bin/python3}}"
ruff_bin="${RUFF_BIN:-ruff}"
run_label="${QC_RUN_LABEL:-$(date -u +%Y%m%dT%H%M%SZ)}"
report_root="${QC_REPORT_ROOT:-$formosanbank_path/../formosan-qc-reports}"
output_dir="$report_root/Wu-Amis-Pa-Verbs/$run_label"
snapshot="$(mktemp -d "${TMPDIR:-/tmp}/wu-amis-public.XXXXXX")"

cleanup() {
    rm -rf -- "$snapshot"
}
trap cleanup EXIT

test -x "$python_bin"
if [[ -e "$output_dir" ]]; then
    echo "Refusing QC: report directory already exists: $output_dir" >&2
    exit 2
fi

mkdir -p "$output_dir" "$snapshot/matplotlib"
export MPLCONFIGDIR="$snapshot/matplotlib"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONHASHSEED=0

cp -R "$corpus_root/XML" "$snapshot/XML"

failures=0
printf 'check,exit_code,gate\n' >"$output_dir/exit_codes.csv"
run() {
    local name="$1"
    shift
    set +e
    "$@" >"$output_dir/$name.stdout.txt" 2>"$output_dir/$name.stderr.txt"
    local code=$?
    set -e
    printf '%s,%s,required\n' "$name" "$code" >>"$output_dir/exit_codes.csv"
    if [[ "$code" -ne 0 ]]; then
        failures=1
    fi
}
run_review() {
    local name="$1"
    shift
    set +e
    "$@" >"$output_dir/$name.stdout.txt" 2>"$output_dir/$name.stderr.txt"
    local code=$?
    set -e
    printf '%s,%s,reviewed\n' "$name" "$code" >>"$output_dir/exit_codes.csv"
}
capture_warning() {
    local name="$1"
    if [[ -f "$corpus_root/XML/$name" ]]; then
        cp "$corpus_root/XML/$name" "$output_dir/$name"
        rm -- "$corpus_root/XML/$name"
    fi
}

run lint "$ruff_bin" check "$corpus_root/CodeAndDocs"
run build_xml "$python_bin" "$corpus_root/CodeAndDocs/build_xml.py"
run apply_manual_edits "$python_bin" \
    "$formosanbank_path/QC/cleaning/apply_manual_edits.py" \
    --corpora_path "$corpus_root/XML"
run clean_xml "$python_bin" "$formosanbank_path/QC/cleaning/clean_xml.py" \
    --corpora_path "$corpus_root/XML"
capture_warning cleaner_warnings.csv
run orthography_detector "$python_bin" \
    "$formosanbank_path/QC/utilities/orthography_detector.py" \
    "$corpus_root/XML" --orthographies "$formosanbank_path/Orthographies" \
    --language ami --combine
run standardize "$python_bin" \
    "$formosanbank_path/QC/utilities/standardize.py" \
    --remove_accents --corpora_path "$corpus_root/XML"
capture_warning standardize_warnings.csv
run add_phonology "$python_bin" \
    "$formosanbank_path/QC/utilities/add_phonology.py" \
    --corpora_path "$corpus_root/XML" --language Amis \
    --orthography "$formosanbank_path/Orthographies/Ortho94"
run source_alignment "$python_bin" \
    "$corpus_root/CodeAndDocs/audit_source_alignment.py"
run xmllint xmllint --noout "$corpus_root/XML/Amis/pa-verbs.xml"
run validate_xml "$python_bin" "$formosanbank_path/QC/validation/validate_xml.py" \
    --csv "$output_dir/validate_xml.csv" \
    --log_dir "$output_dir/validate_xml_logs" \
    --published-corpora "$formosanbank_path/Corpora" --no-exit-on-hard \
    by_path --path "$corpus_root/XML"
run validate_text "$python_bin" \
    "$formosanbank_path/QC/validation/validate_text.py" \
    --csv "$output_dir/validate_text.csv" \
    --log_dir "$output_dir/validate_text_logs" --no-exit-on-hard \
    by_path --path "$corpus_root/XML"
run validate_glosses "$python_bin" \
    "$formosanbank_path/QC/validation/validate_glosses.py" \
    --csv "$output_dir/validate_glosses.csv" --no-exit-on-hard \
    by_path --path "$corpus_root/XML"
run validate_dialect "$python_bin" \
    "$formosanbank_path/QC/validation/validate_dialect.py" \
    --path "$corpus_root/XML"
run duplicate_original "$python_bin" \
    "$formosanbank_path/QC/validation/validate_duplicate_sentences.py" \
    by_path --path "$corpus_root/XML" --tier original \
    --output "$output_dir/duplicate_original.csv"
run duplicate_standard "$python_bin" \
    "$formosanbank_path/QC/validation/validate_duplicate_sentences.py" \
    by_path --path "$corpus_root/XML" --tier standard \
    --output "$output_dir/duplicate_standard.csv"
run audit_gloss_internal "$python_bin" \
    "$formosanbank_path/QC/validation/audit_gloss_scrape.py" \
    --xml "$corpus_root/XML" --no-source \
    --csv "$output_dir/audit_gloss_internal.csv"

orthography_input="$snapshot/orthography-input/Amis"
mkdir -p "$orthography_input"
cp "$corpus_root/XML/Amis/pa-verbs.xml" "$orthography_input/pa-verbs.xml"
for tier in original standard; do
    run "${tier}_orthography_extract" "$python_bin" \
        "$formosanbank_path/QC/orthography/orthography_extract.py" \
        --corpora_path "$(dirname "$orthography_input")" --corpus all \
        --language Amis --kindOf "$tier" --by_dialect true \
        --output_dir "$output_dir/orthography-$tier"
    run "${tier}_orthography" "$python_bin" \
        "$formosanbank_path/QC/validation/validate_orthography.py" \
        --o_info "$output_dir/orthography-$tier" \
        --reference "$formosanbank_path/QC/validation/reference" \
        --language Amis
    run "${tier}_vocabulary" "$python_bin" \
        "$formosanbank_path/QC/validation/validate_vocabulary.py" \
        --o_info "$output_dir/orthography-$tier" \
        --reference "$formosanbank_path/QC/validation/reference" \
        --language Amis
done

run_review registry_consistency "$python_bin" \
    "$formosanbank_path/QC/validation/validate_registries.py" \
    --repo-root "$formosanbank_path" --csv "$output_dir/registry_findings.csv"
run port_readiness "$python_bin" \
    "$formosanbank_path/QC/validation/validate_port_readiness.py" \
    --corpus_path "$corpus_root" --repo-root "$formosanbank_path"
run adjudicate_findings "$python_bin" \
    "$corpus_root/CodeAndDocs/adjudicate_findings.py" --qc-dir "$output_dir"

diff -ru "$snapshot/XML" "$corpus_root/XML"

if [[ "$failures" -ne 0 ]]; then
    echo "One or more required checks failed; see $output_dir/exit_codes.csv." >&2
    exit 1
fi

echo "Reproduction and current QC passed. Artifacts: $output_dir"

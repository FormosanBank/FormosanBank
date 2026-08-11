#!/usr/bin/env bash
set -euo pipefail

corpus_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
formosanbank_path="${FORMOSANBANK_PATH:-$(cd "$corpus_root/../.." && pwd -P)}"
python_bin="${FORMOSANBANK_PYTHON:-${PYTHON:-$formosanbank_path/.venv/bin/python3}}"
run_label="${QC_RUN_LABEL:-$(date -u +%Y%m%dT%H%M%SZ)}"
report_root="${QC_REPORT_ROOT:-$formosanbank_path/../formosan-qc-reports}"
output_dir="$report_root/Huteson-Rukai-Survey/$run_label"
snapshot="$(mktemp -d "${TMPDIR:-/tmp}/huteson-rukai-public.XXXXXX")"

cleanup() {
    rm -rf -- "$snapshot"
}
trap cleanup EXIT

test -x "$python_bin"
mkdir -p "$output_dir" "$snapshot/matplotlib"
export MPLCONFIGDIR="$snapshot/matplotlib"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONHASHSEED=0

cp -R "$corpus_root/XML" "$snapshot/XML"
cp "$corpus_root/CodeAndDocs/extraction_report.tsv" \
    "$snapshot/extraction_report.tsv"

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

run build_xml "$python_bin" "$corpus_root/CodeAndDocs/build_xml.py"
run apply_manual_edits "$python_bin" \
    "$formosanbank_path/QC/cleaning/apply_manual_edits.py" \
    --corpora_path "$corpus_root/XML"
run clean_xml "$python_bin" "$formosanbank_path/QC/cleaning/clean_xml.py" \
    --corpora_path "$corpus_root/XML"
for warning in cleaner_warnings.csv standardize_warnings.csv; do
    if [[ -f "$corpus_root/XML/$warning" ]]; then
        cp "$corpus_root/XML/$warning" "$output_dir/$warning"
        rm -- "$corpus_root/XML/$warning"
    fi
done
for dialect in Maolin Dona; do
    run "conversion_table_${dialect}" "$python_bin" \
        "$formosanbank_path/QC/validation/validate_conversion_table.py" \
        "$corpus_root/CodeAndDocs/source_orthography/Rukai.tsv" \
        "$formosanbank_path/Orthographies/Ortho113/Rukai.tsv" \
        "$corpus_root/CodeAndDocs/huteson_source_to_ortho113.tsv" \
        --dialect "$dialect" \
        --output "$output_dir/conversion_table_${dialect}.md"
done
run standardize "$python_bin" "$formosanbank_path/QC/utilities/standardize.py" \
    --tsv_path "$corpus_root/CodeAndDocs/huteson_source_to_ortho113.tsv" \
    --corpora_path "$corpus_root/XML"
run add_phonology "$python_bin" \
    "$formosanbank_path/QC/utilities/add_phonology.py" \
    --corpora_path "$corpus_root/XML" --language Rukai \
    --orthography "$corpus_root/CodeAndDocs/source_orthography"
run validate_xml "$python_bin" "$formosanbank_path/QC/validation/validate_xml.py" \
    --csv "$output_dir/validate_xml.csv" --no-exit-on-hard \
    --published-corpora "$formosanbank_path/Corpora" \
    by_path --path "$corpus_root/XML"
run validate_text "$python_bin" "$formosanbank_path/QC/validation/validate_text.py" \
    --csv "$output_dir/validate_text.csv" --no-exit-on-hard \
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
run audit_gloss_scrape "$python_bin" \
    "$formosanbank_path/QC/validation/audit_gloss_scrape.py" \
    --xml "$corpus_root/XML" --no-source \
    --csv "$output_dir/audit_gloss_scrape.csv"
for tier in original standard; do
    run "${tier}_orthography_extract" "$python_bin" \
        "$formosanbank_path/QC/orthography/orthography_extract.py" \
        --corpora_path "$corpus_root/XML" --corpus all --language All \
        --kindOf "$tier" --by_dialect true \
        --output_dir "$output_dir/orthography-$tier"
    run "${tier}_orthography" "$python_bin" \
        "$formosanbank_path/QC/validation/validate_orthography.py" \
        --o_info "$output_dir/orthography-$tier" \
        --reference "$formosanbank_path/QC/validation/reference" \
        --language Rukai
    run "${tier}_vocabulary" "$python_bin" \
        "$formosanbank_path/QC/validation/validate_vocabulary.py" \
        --o_info "$output_dir/orthography-$tier" \
        --reference "$formosanbank_path/QC/validation/reference" \
        --language Rukai
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
cmp "$snapshot/extraction_report.tsv" \
    "$corpus_root/CodeAndDocs/extraction_report.tsv"
xmllint --noout "$corpus_root"/XML/Rukai/*.xml

if [[ "$failures" -ne 0 ]]; then
    echo "One or more required checks failed; see $output_dir/exit_codes.csv." >&2
    exit 1
fi

echo "Reproduction and current QC passed. Artifacts: $output_dir"

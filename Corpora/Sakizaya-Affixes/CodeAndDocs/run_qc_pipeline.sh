#!/usr/bin/env bash
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
QC_ROOT="${FORMOSANBANK_QC_ROOT:-}"
OUT="${QC_OUTPUT_DIR:-$ROOT/logs/local/formosanbank_qc}"
FINAL="$ROOT/XML"
REQUIRED_QC_COMMIT=3a3c47c220520113f747e6a2d441494000e13c4b

if [[ -z "$QC_ROOT" && -d "$ROOT/../FormosanBank/QC" ]]; then
  QC_ROOT="$ROOT/../FormosanBank"
fi
if [[ -z "$QC_ROOT" || ! -d "$QC_ROOT/QC" ]]; then
  printf '%s\n' "Set FORMOSANBANK_QC_ROOT to a FormosanBank checkout." >&2
  exit 2
fi
QC_ROOT="$(cd "$QC_ROOT" && pwd -P)"

BEFORE_COMMIT="$(git -C "$QC_ROOT" rev-parse HEAD)"
ORIGIN_MAIN="$(git -C "$QC_ROOT" rev-parse --verify refs/remotes/origin/main)"
BEFORE_STATUS="$(git -C "$QC_ROOT" status --porcelain)"
if [[ -n "$BEFORE_STATUS" ]]; then
  printf '%s\n' "Refusing QC: the read-only FormosanBank dependency must be clean." >&2
  exit 2
fi
if [[ "$BEFORE_COMMIT" != "$REQUIRED_QC_COMMIT" ]]; then
  printf 'Refusing QC: FormosanBank must be pinned to %s; found %s.\n' "$REQUIRED_QC_COMMIT" "$BEFORE_COMMIT" >&2
  exit 2
fi
if ! git -C "$QC_ROOT" diff --quiet origin/main -- QC Orthographies; then
  printf '%s\n' "Refusing QC: checked-out QC/Orthographies differ from fetched origin/main." >&2
  exit 2
fi

PY="${FORMOSANBANK_QC_PYTHON:-$QC_ROOT/.venv/bin/python}"
LOCAL_PY="${PYTHON:-$ROOT/.venv/bin/python3}"
if [[ ! -x "$PY" || ! -x "$LOCAL_PY" ]]; then
  printf '%s\n' "QC Python or local Python is not executable." >&2
  exit 2
fi
if [[ -d "$OUT" && -n "$(find "$OUT" -mindepth 1 -print -quit)" ]]; then
  printf '%s\n' "Refusing QC: output directory is not empty: $OUT" >&2
  exit 2
fi

SCRATCH="$(mktemp -d "${TMPDIR:-/tmp}/sakizaya-affixes-qc.XXXXXX")"
SCRATCH="$(cd "$SCRATCH" && pwd -P)"
cleanup_scratch() {
  rm -rf -- "$SCRATCH"
}
trap cleanup_scratch EXIT

export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$OUT" "$SCRATCH/mpl" "$SCRATCH/clean" "$SCRATCH/standard_phon" "$SCRATCH/ortho/Sakizaya"

SUMMARY="$OUT/run_summary.tsv"
COMMANDS="$OUT/commands.txt"
printf 'name\texit_code\tlog\n' > "$SUMMARY"
printf 'FormosanBank commit: %s\n' "$BEFORE_COMMIT" > "$COMMANDS"
printf 'Fetched FormosanBank origin/main: %s\n' "$ORIGIN_MAIN" >> "$COMMANDS"
printf 'FormosanBank status before: clean\n' >> "$COMMANDS"
printf 'Corpus: %s\nOutput: %s\n\n' "$FINAL" "$OUT" >> "$COMMANDS"

FAIL=0
run_qc() {
  local name="$1"
  shift
  local log="$OUT/$name.log"
  local code arg separator
  {
    printf '[%s] ' "$name"
    separator=""
    for arg in "$@"; do
      printf '%s' "$separator"
      printf '%q' "$arg"
      separator=" "
    done
    printf '\n'
  } >> "$COMMANDS"
  (cd "$ROOT" && "$@") > "$log" 2>&1
  code=$?
  printf '%s\t%s\t%s\n' "$name" "$code" "${log#$ROOT/}" >> "$SUMMARY"
  printf '%-34s exit=%s log=%s\n' "$name" "$code" "$log"
  if [[ "$code" -ne 0 ]]; then FAIL=1; fi
}

write_generated_hashes() {
  find "$ROOT/XML" "$ROOT/CodeAndDocs" -type f \
    \( -name '*.xml' -o -name '*.csv' \) \
    ! -path '*/__pycache__/*' -print0 \
    | sort -z | xargs -0 shasum -a 256 \
    | sed "s#$ROOT/#<CORPUS_ROOT>/#g"
}

run_qc build_all "$LOCAL_PY" "$ROOT/CodeAndDocs/build_all.py"
write_generated_hashes > "$OUT/generated_hashes_first.txt"
run_qc build_all_repeat "$LOCAL_PY" "$ROOT/CodeAndDocs/build_all.py"
write_generated_hashes > "$OUT/generated_hashes_second.txt"
diff -u "$OUT/generated_hashes_first.txt" "$OUT/generated_hashes_second.txt" \
  > "$OUT/determinism_diff.txt" 2>&1
DETERMINISM_CODE=$?
printf 'determinism_diff_exit=%s (must be 0)\n' "$DETERMINISM_CODE" >> "$COMMANDS"
if [[ "$DETERMINISM_CODE" -ne 0 ]]; then FAIL=1; fi

cp -R "$FINAL"/. "$SCRATCH/clean"/
cp -R "$FINAL"/. "$SCRATCH/standard_phon"/
cp "$FINAL"/szy/*.xml "$SCRATCH/ortho/Sakizaya"/

run_qc validate_xml \
  "$PY" "$QC_ROOT/QC/validation/validate_xml.py" by_path --path "$FINAL" \
  --csv "$OUT/validate_xml_findings.csv" --log_dir "$OUT/validate_xml_logs" \
  --published-corpora "$QC_ROOT/Corpora" --no-exit-on-hard
run_qc validate_dialect \
  "$PY" "$QC_ROOT/QC/validation/validate_dialect.py" --path "$FINAL"
run_qc validate_text \
  "$PY" "$QC_ROOT/QC/validation/validate_text.py" by_path --path "$FINAL" \
  --csv "$OUT/validate_text_findings.csv" --log_dir "$OUT/validate_text_logs" --no-exit-on-hard
run_qc validate_glosses \
  "$PY" "$QC_ROOT/QC/validation/validate_glosses.py" by_path --path "$FINAL" \
  --csv "$OUT/validate_glosses_findings.csv" --no-exit-on-hard
run_qc validate_duplicates_original \
  "$PY" "$QC_ROOT/QC/validation/validate_duplicate_sentences.py" by_path \
  --path "$FINAL" --tier original --output "$OUT/duplicate_original_findings.csv" --verbose
run_qc validate_duplicates_standard \
  "$PY" "$QC_ROOT/QC/validation/validate_duplicate_sentences.py" by_path \
  --path "$FINAL" --tier standard --output "$OUT/duplicate_standard_findings.csv" --verbose

run_qc orthography_extract_original \
  env MPLCONFIGDIR="$SCRATCH/mpl" "$PY" "$QC_ROOT/QC/orthography/orthography_extract.py" \
  --corpora_path "$SCRATCH/ortho" --corpus all --language Sakizaya --kindOf original \
  --by_dialect true --output_dir "$OUT/orthography_original"
run_qc validate_orthography_original \
  env MPLCONFIGDIR="$SCRATCH/mpl" "$PY" "$QC_ROOT/QC/validation/validate_orthography.py" \
  --o_info "$OUT/orthography_original" --reference "$QC_ROOT/QC/validation/reference" --language Sakizaya
run_qc validate_vocabulary_original \
  env MPLCONFIGDIR="$SCRATCH/mpl" "$PY" "$QC_ROOT/QC/validation/validate_vocabulary.py" \
  --o_info "$OUT/orthography_original" --reference "$QC_ROOT/QC/validation/reference" --language Sakizaya
run_qc orthography_extract_standard \
  env MPLCONFIGDIR="$SCRATCH/mpl" "$PY" "$QC_ROOT/QC/orthography/orthography_extract.py" \
  --corpora_path "$SCRATCH/ortho" --corpus all --language Sakizaya --kindOf standard \
  --by_dialect true --output_dir "$OUT/orthography_standard"
run_qc validate_orthography_standard \
  env MPLCONFIGDIR="$SCRATCH/mpl" "$PY" "$QC_ROOT/QC/validation/validate_orthography.py" \
  --o_info "$OUT/orthography_standard" --reference "$QC_ROOT/QC/validation/reference" --language Sakizaya
run_qc validate_vocabulary_standard \
  env MPLCONFIGDIR="$SCRATCH/mpl" "$PY" "$QC_ROOT/QC/validation/validate_vocabulary.py" \
  --o_info "$OUT/orthography_standard" --reference "$QC_ROOT/QC/validation/reference" --language Sakizaya

run_qc validate_registries \
  "$PY" "$QC_ROOT/QC/validation/validate_registries.py" \
  --repo-root "$QC_ROOT" --csv "$OUT/validate_registries_findings.csv"

run_qc orthography_detector_original \
  "$PY" "$QC_ROOT/QC/utilities/orthography_detector.py" "$FINAL" --language szy --combine
run_qc orthography_detector_standard \
  "$PY" "$QC_ROOT/QC/utilities/orthography_detector.py" "$FINAL" --language szy --combine --use-standard

run_qc apply_manual_edits_scratch \
  "$PY" "$QC_ROOT/QC/cleaning/apply_manual_edits.py" --corpora_path "$SCRATCH/clean"
run_qc clean_xml_scratch \
  "$PY" "$QC_ROOT/QC/cleaning/clean_xml.py" --corpora_path "$SCRATCH/clean"
if [[ -f "$SCRATCH/clean/cleaner_warnings.csv" ]]; then
  mv "$SCRATCH/clean/cleaner_warnings.csv" "$OUT/cleaner_warnings.csv"
fi
diff -ru "$FINAL" "$SCRATCH/clean" > "$OUT/clean_xml_diff.txt" 2>&1
CLEAN_DIFF_CODE=$?
printf 'clean_xml_diff_exit=%s (must be 0)\n' "$CLEAN_DIFF_CODE" >> "$COMMANDS"
if [[ "$CLEAN_DIFF_CODE" -ne 0 ]]; then FAIL=1; fi

run_qc standardize_source_profile_scratch \
  "$PY" "$QC_ROOT/QC/utilities/standardize.py" \
  --tsv_path "$ROOT/CodeAndDocs/source_data/sakizaya_affixes_standardization.tsv" \
  --target_column standard --corpora_path "$SCRATCH/standard_phon"
run_qc add_phonology_scratch \
  "$PY" "$QC_ROOT/QC/utilities/add_phonology.py" --corpora_path "$SCRATCH/standard_phon"
diff -ru "$FINAL" "$SCRATCH/standard_phon" > "$OUT/standard_phon_diff.txt" 2>&1
STANDARD_PHON_DIFF_CODE=$?
printf 'standard_phon_diff_exit=%s (must be 0)\n' "$STANDARD_PHON_DIFF_CODE" >> "$COMMANDS"
if [[ "$STANDARD_PHON_DIFF_CODE" -ne 0 ]]; then FAIL=1; fi

AFTER_COMMIT="$(git -C "$QC_ROOT" rev-parse HEAD)"
AFTER_STATUS="$(git -C "$QC_ROOT" status --porcelain)"
AFTER_CLEAN=true
MODIFIED=false
if [[ -n "$AFTER_STATUS" ]]; then AFTER_CLEAN=false; fi
if [[ "$AFTER_COMMIT" != "$BEFORE_COMMIT" || -n "$AFTER_STATUS" ]]; then MODIFIED=true; FAIL=1; fi
cat > "$OUT/public_dependency.json" <<JSON
{
  "after_clean": $AFTER_CLEAN,
  "after_commit": "$AFTER_COMMIT",
  "before_clean": true,
  "before_commit": "$BEFORE_COMMIT",
  "modified": $MODIFIED,
  "origin_main": "$ORIGIN_MAIN",
  "path": "<FORMOSANBANK_ROOT>",
  "tool_tree_matches_origin_main": true
}
JSON

run_qc validate_port_readiness \
  "$PY" "$QC_ROOT/QC/validation/validate_port_readiness.py" \
  --corpus_path "$ROOT" --repo-root "$QC_ROOT"

run_qc adjudicate_findings \
  "$LOCAL_PY" "$ROOT/CodeAndDocs/adjudicate_findings.py" --qc-dir "$OUT"

"$LOCAL_PY" "$ROOT/CodeAndDocs/sanitize_qc_evidence.py" \
  --qc-dir "$OUT" \
  --corpus-root "$ROOT" \
  --formosanbank-root "$QC_ROOT" \
  --formosanbank-python "$PY" \
  --scratch-root "$SCRATCH"

printf '\nSummary: %s\n' "$SUMMARY"
exit "$FAIL"

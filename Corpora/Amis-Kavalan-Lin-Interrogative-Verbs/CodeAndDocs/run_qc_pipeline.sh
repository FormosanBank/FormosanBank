#!/usr/bin/env bash
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
QC_ROOT="${FORMOSANBANK_QC_ROOT:-${FORMOSANBANK_PATH:-$ROOT/../FormosanBank}}"
REQUIRED_QC_COMMIT="$(tr -d '[:space:]' < "$ROOT/CodeAndDocs/formosanbank_ref.txt")"
REPO_NAME="$(basename "$ROOT")"
RUN_ID="${QC_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
OUT="${QC_OUTPUT_DIR:-$ROOT/../qc-reports/$REPO_NAME-$RUN_ID}"
FINAL="$ROOT/XML"
SOURCE_PDF="$ROOT/Private/source/basecamp/card-8262349071/lin_2015_amis_kavalan_interrogative_verbs.pdf"
SOURCE_LICENSE="$ROOT/Private/source/basecamp/card-8262349071/source_license_screenshot_2025-01-28.png"
SOURCE_CACHE="$ROOT/Private/cache/lin_2015_amis_kavalan_interrogative_verbs.layout.txt"

if [[ ! "$RUN_ID" =~ ^[A-Za-z0-9._-]+$ ]]; then
  printf '%s\n' "QC_RUN_ID contains unsupported characters." >&2
  exit 2
fi
if [[ ! -d "$QC_ROOT/QC" ]]; then
  printf '%s\n' "Set FORMOSANBANK_QC_ROOT to the governing FormosanBank checkout." >&2
  exit 2
fi
QC_ROOT="$(cd "$QC_ROOT" && pwd -P)"
PY="${FORMOSANBANK_QC_PYTHON:-$QC_ROOT/.venv/bin/python}"
LOCAL_PY="${PYTHON:-python3}"
if [[ ! -x "$PY" ]] || ! command -v "$LOCAL_PY" >/dev/null 2>&1; then
  printf '%s\n' "QC Python or local Python is not executable." >&2
  exit 2
fi
if [[ ! -f "$SOURCE_PDF" || ! -f "$SOURCE_LICENSE" || ! -f "$SOURCE_CACHE" ]]; then
  printf '%s\n' "The canonical source-assisted gate requires the PDF, license screenshot, and text cache." >&2
  exit 2
fi
if [[ -e "$ROOT/Final_XML" ]]; then
  printf '%s\n' "Legacy Final_XML/ must not exist." >&2
  exit 2
fi
if [[ -n "$(git -C "$ROOT" ls-files 'Private/**')" ]]; then
  printf '%s\n' "No file under Private/ may be tracked." >&2
  exit 2
fi

BEFORE_COMMIT="$(git -C "$QC_ROOT" rev-parse HEAD)"
ORIGIN_MAIN="$(git -C "$QC_ROOT" rev-parse --verify refs/remotes/origin/main)"
BEFORE_STATUS="$(git -C "$QC_ROOT" status --porcelain)"
if [[ -n "$BEFORE_STATUS" ]]; then
  printf '%s\n' "The read-only FormosanBank dependency must be clean." >&2
  exit 2
fi
if [[ "$BEFORE_COMMIT" != "$REQUIRED_QC_COMMIT" ]]; then
  printf 'FormosanBank must be pinned to %s; found %s.\n' "$REQUIRED_QC_COMMIT" "$BEFORE_COMMIT" >&2
  exit 2
fi
if ! git -C "$QC_ROOT" diff --quiet origin/main -- QC Orthographies standards.csv dialects.csv languages.csv; then
  printf '%s\n' "The governing tools or registries differ from fetched origin/main." >&2
  exit 2
fi
if [[ -d "$OUT" && -n "$(find "$OUT" -mindepth 1 -print -quit)" ]]; then
  printf 'QC output directory is not empty: %s\n' "$OUT" >&2
  exit 2
fi

SCRATCH="$(mktemp -d "${TMPDIR:-/tmp}/lin-current-qc.XXXXXX")"
cleanup_scratch() {
  rm -rf -- "$SCRATCH"
}
trap cleanup_scratch EXIT

export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$OUT" "$SCRATCH/mpl"
SUMMARY="$OUT/run_summary.tsv"
COMMANDS="$OUT/commands.txt"
printf 'name\texit_code\tlog\n' > "$SUMMARY"
printf 'FormosanBank commit: %s\n' "$BEFORE_COMMIT" > "$COMMANDS"
printf 'Fetched FormosanBank origin/main: %s\n' "$ORIGIN_MAIN" >> "$COMMANDS"
printf 'Corpus: <CORPUS_ROOT>/XML\n\n' >> "$COMMANDS"

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
  if [[ "$code" -ne 0 ]]; then
    FAIL=1
  fi
}

write_generated_hashes() {
  {
    find "$ROOT/XML" -type f -name '*.xml' -print
    printf '%s\n' \
      "$ROOT/CodeAndDocs/alignment_omissions.tsv" \
      "$ROOT/CodeAndDocs/excluded_source_units.tsv" \
      "$ROOT/CodeAndDocs/extracted_examples.tsv" \
      "$ROOT/CodeAndDocs/extraction_summary.md" \
      "$ROOT/CodeAndDocs/source_alignment_audit.md"
  } | LC_ALL=C sort | xargs shasum -a 256 | sed "s#$ROOT/#<CORPUS_ROOT>/#g"
}

run_qc build_all "$LOCAL_PY" "$ROOT/CodeAndDocs/build_all.py"
write_generated_hashes > "$OUT/generated_hashes_first.txt"
run_qc build_all_repeat "$LOCAL_PY" "$ROOT/CodeAndDocs/build_all.py"
write_generated_hashes > "$OUT/generated_hashes_second.txt"
diff -u "$OUT/generated_hashes_first.txt" "$OUT/generated_hashes_second.txt" \
  > "$OUT/determinism_diff.txt" 2>&1
DETERMINISM_CODE=$?
printf 'determinism_diff_exit=%s (must be 0)\n' "$DETERMINISM_CODE" >> "$COMMANDS"
if [[ "$DETERMINISM_CODE" -ne 0 ]]; then
  FAIL=1
fi

run_qc validate_xml \
  "$PY" "$QC_ROOT/QC/validation/validate_xml.py" by_path --path "$FINAL" \
  --csv "$OUT/validate_xml_findings.csv" --published-corpora "$QC_ROOT/Corpora" \
  --no-exit-on-hard
run_qc validate_text \
  "$PY" "$QC_ROOT/QC/validation/validate_text.py" by_path --path "$FINAL" \
  --csv "$OUT/validate_text_findings.csv" --no-exit-on-hard
run_qc validate_glosses \
  "$PY" "$QC_ROOT/QC/validation/validate_glosses.py" by_path --path "$FINAL" \
  --csv "$OUT/validate_glosses_findings.csv" --no-exit-on-hard
run_qc validate_dialect \
  "$PY" "$QC_ROOT/QC/validation/validate_dialect.py" --path "$FINAL"
run_qc validate_duplicates_original \
  "$PY" "$QC_ROOT/QC/validation/validate_duplicate_sentences.py" by_path \
  --path "$FINAL" --tier original --output "$OUT/duplicate_original_findings.csv"
run_qc validate_duplicates_standard \
  "$PY" "$QC_ROOT/QC/validation/validate_duplicate_sentences.py" by_path \
  --path "$FINAL" --tier standard --output "$OUT/duplicate_standard_findings.csv"
run_qc orthography_detector_original \
  "$PY" "$QC_ROOT/QC/utilities/orthography_detector.py" "$FINAL" --combine
run_qc orthography_detector_standard \
  "$PY" "$QC_ROOT/QC/utilities/orthography_detector.py" "$FINAL" --combine --use-standard

run_qc validate_conversion_table \
  "$PY" "$QC_ROOT/QC/validation/validate_conversion_table.py" \
  "$ROOT/CodeAndDocs/Orthographies/LinAmis/Amis.tsv" \
  "$QC_ROOT/Orthographies/Ortho113/Amis.tsv" \
  "$ROOT/CodeAndDocs/Orthographies/ConversionTables/Amis_LinAmis_113.tsv" \
  --dialect Xiuguluan
run_qc source_alignment_audit "$LOCAL_PY" "$ROOT/CodeAndDocs/audit_source_alignment.py"
run_qc gloss_scrape_audit \
  "$PY" "$QC_ROOT/QC/validation/audit_gloss_scrape.py" \
  --repo "$ROOT" --xml "$FINAL" --source "$SOURCE_PDF" \
  --csv "$OUT/gloss_scrape_findings.csv"
run_qc reconcile_gloss_scrape \
  "$LOCAL_PY" "$ROOT/CodeAndDocs/reconcile_gloss_audit.py" \
  --findings "$OUT/gloss_scrape_findings.csv" \
  --examples "$ROOT/CodeAndDocs/extracted_examples.tsv" \
  --exclusions "$ROOT/CodeAndDocs/excluded_source_units.tsv" \
  --output "$OUT/gloss_scrape_reconciliation.csv"
run_qc regression_tests "$LOCAL_PY" -m unittest discover -s "$ROOT/CodeAndDocs/tests" -v
run_qc validate_port_readiness \
  "$PY" "$QC_ROOT/QC/validation/validate_port_readiness.py" \
  --corpus_path "$ROOT" --repo-root "$QC_ROOT"
run_qc adjudicate_findings \
  "$LOCAL_PY" "$ROOT/CodeAndDocs/adjudicate_qc.py" --qc-dir "$OUT"

AFTER_COMMIT="$(git -C "$QC_ROOT" rev-parse HEAD)"
AFTER_STATUS="$(git -C "$QC_ROOT" status --porcelain)"
AFTER_CLEAN=true
MODIFIED=false
if [[ -n "$AFTER_STATUS" ]]; then
  AFTER_CLEAN=false
fi
if [[ "$AFTER_COMMIT" != "$BEFORE_COMMIT" || -n "$AFTER_STATUS" ]]; then
  MODIFIED=true
  FAIL=1
fi
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

if [[ "$FAIL" -eq 0 ]]; then
  printf 'Canonical QC passed with all residual findings adjudicated.\n'
fi
printf 'QC output: %s\n' "$OUT"
exit "$FAIL"

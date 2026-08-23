#!/usr/bin/env bash
set -euo pipefail

readonly EXPECTED_AUTHORITY="3a3c47c220520113f747e6a2d441494000e13c4b"
readonly REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly CORPUS_ROOT="$(cd "$REPO_ROOT/.." && pwd)"
readonly DEFAULT_AUTHORITY="$(cd "$CORPUS_ROOT/../.." && pwd)"
EPARK_AUTHORITY="${EPARK_AUTHORITY:-$DEFAULT_AUTHORITY}"

if [[ ! -d "$EPARK_AUTHORITY" ]]; then
    echo "FormosanBank authority not found at $EPARK_AUTHORITY" >&2
    echo "Set EPARK_AUTHORITY to a checkout at $EXPECTED_AUTHORITY." >&2
    exit 1
fi

if [[ -z "${EPARK_PYTHON:-}" ]]; then
    if [[ -x "$EPARK_AUTHORITY/.venv/bin/python3" ]]; then
        EPARK_PYTHON="$EPARK_AUTHORITY/.venv/bin/python3"
    elif command -v python3 >/dev/null 2>&1; then
        EPARK_PYTHON="$(command -v python3)"
    else
        echo "Python 3 not found; set EPARK_PYTHON to a Python 3 executable." >&2
        exit 1
    fi
fi

readonly EPARK_AUTHORITY EPARK_PYTHON

if ! git -C "$EPARK_AUTHORITY" cat-file -e "$EXPECTED_AUTHORITY^{commit}"; then
    echo "Pinned authority commit is unavailable: $EXPECTED_AUTHORITY" >&2
    exit 1
fi
if ! git -C "$EPARK_AUTHORITY" diff --quiet \
    "$EXPECTED_AUTHORITY" -- QC Orthographies; then
    echo "QC or orthography tooling differs from pinned authority $EXPECTED_AUTHORITY" >&2
    exit 1
fi

EPARK_WORKDIR="$(mktemp -d "${TMPDIR:-/tmp}/formosan-epark-reproduce.XXXXXX")"
readonly EPARK_WORKDIR
trap 'rm -rf -- "$EPARK_WORKDIR"' EXIT

readonly WORK_XML="$EPARK_WORKDIR/XML"
readonly WORK_REPORTS="$EPARK_WORKDIR/reports"
readonly QC="$EPARK_AUTHORITY/QC"
readonly TABLES="$EPARK_AUTHORITY/Orthographies/ConversionTables"

mkdir -p "$WORK_REPORTS" "$EPARK_WORKDIR/empty-published"

"$EPARK_PYTHON" "$REPO_ROOT/build_xml.py" \
    --repo "$REPO_ROOT" --output "$WORK_XML" \
    >"$WORK_REPORTS/01_source_build.json"
"$EPARK_PYTHON" "$REPO_ROOT/source_audit.py" \
    --repo "$REPO_ROOT" --xml "$WORK_XML" \
    --report "$WORK_REPORTS/02_source_audit_raw.json" >/dev/null

(
    cd "$EPARK_WORKDIR"
    "$EPARK_PYTHON" "$QC/cleaning/clean_xml.py" \
        --corpora_path XML >"$WORK_REPORTS/03_clean_xml.log"
)
for cleaner_report in cleaner_warnings.csv html_entities.log; do
    if [[ -f "$WORK_XML/$cleaner_report" ]]; then
        mv "$WORK_XML/$cleaner_report" "$WORK_REPORTS/$cleaner_report"
    fi
done
diff -u \
    <(sed 's/\r$//' "$REPO_ROOT/quote_corrections.csv") \
    <(sed 's/\r$//' "$EPARK_WORKDIR/CodeAndDocs/quote_corrections.csv")
"$EPARK_PYTHON" "$REPO_ROOT/source_audit.py" \
    --repo "$REPO_ROOT" --xml "$WORK_XML" --apply \
    --report "$WORK_REPORTS/04_source_restore_after_clean.json" >/dev/null

"$EPARK_PYTHON" "$QC/utilities/standardize.py" \
    --corpora_path "$WORK_XML" --copy >/dev/null
"$EPARK_PYTHON" "$QC/utilities/standardize.py" \
    --corpora_path "$WORK_XML/hui_ben_ping_tai_picture_book_platform/Amis" \
    --tsv_path "$TABLES/Amis_113lib_113.tsv" >/dev/null
"$EPARK_PYTHON" "$QC/utilities/standardize.py" \
    --corpora_path "$WORK_XML/jiu_jie_jiao_cai_nine_level_materials/Amis" \
    --tsv_path "$TABLES/Amis_113lib_113.tsv" >/dev/null
"$EPARK_PYTHON" "$QC/utilities/standardize.py" \
    --corpora_path "$WORK_XML/jiu_jie_jiao_cai_nine_level_materials/Atayal" \
    --tsv_path "$TABLES/Atayal_94_113.tsv" >/dev/null
"$EPARK_PYTHON" "$QC/utilities/standardize.py" \
    --corpora_path "$WORK_XML/jiu_jie_jiao_cai_nine_level_materials/Puyuma" \
    --tsv_path "$TABLES/Puyuma_94_113.tsv" >/dev/null
"$EPARK_PYTHON" "$QC/utilities/standardize.py" \
    --corpora_path "$WORK_XML/jiu_jie_jiao_cai_nine_level_materials/Rukai" \
    --tsv_path "$TABLES/Rukai_94_113.tsv" >/dev/null
"$EPARK_PYTHON" "$QC/utilities/standardize.py" \
    --corpora_path "$WORK_XML/qing_jing_zu_yu_contextual_indigenous_language/Amis" \
    --tsv_path "$TABLES/Amis_113lib_113.tsv" >/dev/null

"$EPARK_PYTHON" "$QC/utilities/add_phonology.py" \
    --orthography Ortho113 --corpora_path "$WORK_XML" >/dev/null
"$EPARK_PYTHON" "$REPO_ROOT/source_audit.py" \
    --repo "$REPO_ROOT" --xml "$WORK_XML" --apply \
    --report "$WORK_REPORTS/05_source_restore_after_derived.json" >/dev/null
"$EPARK_PYTHON" "$REPO_ROOT/source_audit.py" \
    --repo "$REPO_ROOT" --xml "$WORK_XML" \
    --report "$WORK_REPORTS/06_source_audit.json" >/dev/null

"$EPARK_PYTHON" "$QC/validation/validate_xml.py" by_path \
    --path "$WORK_XML" --published-corpora "$EPARK_WORKDIR/empty-published" \
    --csv "$WORK_REPORTS/validate_xml.csv" >/dev/null
"$EPARK_PYTHON" "$QC/validation/validate_text.py" by_path \
    --path "$WORK_XML" --csv "$WORK_REPORTS/validate_text.csv" >/dev/null
manifest() {
    local directory="$1"
    (
        cd "$directory"
        find . -type f -name '*.xml' | LC_ALL=C sort | while IFS= read -r file; do
            shasum -a 256 "$file"
        done
    )
}

manifest "$CORPUS_ROOT/XML" >"$EPARK_WORKDIR/expected.sha256"
manifest "$WORK_XML" >"$EPARK_WORKDIR/reproduced.sha256"
diff -u "$EPARK_WORKDIR/expected.sha256" "$EPARK_WORKDIR/reproduced.sha256"

echo "Reproduction passed: 436 XML files match pinned authority $EXPECTED_AUTHORITY"

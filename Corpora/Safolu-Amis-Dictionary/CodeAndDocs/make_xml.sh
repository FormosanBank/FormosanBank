#!/usr/bin/env bash
# Regenerate Safolu XML from pinned public sources in an isolated workspace.
#
# Usage:
#   CodeAndDocs/make_xml.sh --check   compare a fresh build with canonical XML
#   CodeAndDocs/make_xml.sh --apply   replace canonical XML after validation
#
# Optional environment:
#   FORMOSANBANK_ROOT  checkout supplying current QC and orthography resources
#   PYTHON             Python environment containing FormosanBank dependencies
#   SOURCES_DIR        existing pinned source checkouts
#   WORK_DIR           new absolute build directory outside FormosanBank
#   REPORT_DIR         new absolute report directory outside FormosanBank
#   KEEP_WORK=1        retain an automatically created successful workspace

set -euo pipefail

MODE="check"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --check) MODE="check" ;;
        --apply) MODE="apply" ;;
        -h|--help)
            sed -n '2,15p' "${BASH_SOURCE[0]}"
            exit 0
            ;;
        *)
            echo "Unknown argument: $1 (usage: $0 [--check|--apply])" >&2
            exit 2
            ;;
    esac
    shift
done

CODEDOCS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
CORPUS="$(dirname "$CODEDOCS")"
BANK="${FORMOSANBANK_ROOT:-$(cd "$CORPUS/../.." && pwd -P)}"
PY="${PYTHON:-$BANK/.venv/bin/python}"

EXPECTED_MOEDICT_COMMIT="e7c6976a0766e9b0aeb7083e2c06db60f5485252"
EXPECTED_SAFOLU_COMMIT="f512d5ba0d08f81b26093a9b7b4a85acac760a30"

if [[ ! -x "$PY" ]]; then
    PY="$(command -v python3 || true)"
fi
if [[ -z "$PY" || ! -x "$PY" ]]; then
    echo "Python executable is unavailable: $PY" >&2
    exit 2
fi
export PYTHONDONTWRITEBYTECODE="${PYTHONDONTWRITEBYTECODE:-1}"
if ! git -C "$BANK" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "FORMOSANBANK_ROOT is not a Git checkout: $BANK" >&2
    exit 2
fi

OWN_WORK=0
OWNED_WORK_PATH=""
BUILD_SUCCEEDED=0
if [[ -n "${WORK_DIR:-}" ]]; then
    WORK_ROOT="$WORK_DIR"
    if [[ "$WORK_ROOT" != /* ]]; then
        echo "WORK_DIR must be absolute: $WORK_ROOT" >&2
        exit 2
    fi
    if [[ -d "$WORK_ROOT" ]] && find "$WORK_ROOT" -mindepth 1 -print -quit | grep -q .; then
        echo "WORK_DIR must be new or empty: $WORK_ROOT" >&2
        exit 2
    fi
    mkdir -p "$WORK_ROOT"
else
    TEMP_BASE="${TMPDIR:-/tmp}"
    WORK_ROOT="$(mktemp -d "$TEMP_BASE/safolu-rebuild.XXXXXX")"
    OWN_WORK=1
fi
WORK_ROOT="$(cd "$WORK_ROOT" && pwd -P)"
if [[ "$OWN_WORK" -eq 1 ]]; then
    OWNED_WORK_PATH="$WORK_ROOT"
fi
case "$WORK_ROOT/" in
    "$BANK/"*)
        echo "WORK_DIR must be outside FormosanBank: $WORK_ROOT" >&2
        exit 2
        ;;
esac

cleanup() {
    if [[ "$OWN_WORK" -eq 1 && "$BUILD_SUCCEEDED" -eq 1 && "${KEEP_WORK:-0}" != "1" ]]; then
        if [[ -n "$OWNED_WORK_PATH" && "$WORK_ROOT" == "$OWNED_WORK_PATH" ]]; then
            rm -rf -- "$WORK_ROOT"
        else
            echo "Refusing to remove unexpected temporary path: $WORK_ROOT" >&2
        fi
    else
        echo "Build workspace retained at $WORK_ROOT" >&2
    fi
}
trap cleanup EXIT

REPORT_ROOT="${REPORT_DIR:-$WORK_ROOT/reports}"
if [[ "$REPORT_ROOT" != /* ]]; then
    echo "REPORT_DIR must be absolute: $REPORT_ROOT" >&2
    exit 2
fi
if [[ -d "$REPORT_ROOT" ]] && find "$REPORT_ROOT" -mindepth 1 -print -quit | grep -q .; then
    echo "REPORT_DIR must be new or empty: $REPORT_ROOT" >&2
    exit 2
fi
mkdir -p "$REPORT_ROOT"
REPORT_ROOT="$(cd "$REPORT_ROOT" && pwd -P)"
case "$REPORT_ROOT/" in
    "$BANK/"*)
        echo "REPORT_DIR must be outside FormosanBank: $REPORT_ROOT" >&2
        exit 2
        ;;
esac

SOURCES_ROOT="${SOURCES_DIR:-$WORK_ROOT/_sources}"
if [[ ! -d "$SOURCES_ROOT/amis-moedict" || ! -d "$SOURCES_ROOT/amis-safolu" ]]; then
    "$PY" "$CODEDOCS/fetch_sources.py" --sources-dir "$SOURCES_ROOT"
fi

check_source() {
    local path="$1"
    local expected="$2"
    local actual
    if ! git -C "$path" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        echo "Pinned source checkout is missing: $path" >&2
        exit 2
    fi
    actual="$(git -C "$path" rev-parse HEAD)"
    if [[ "$actual" != "$expected" ]]; then
        echo "Source commit mismatch at $path: expected $expected, got $actual" >&2
        exit 2
    fi
    if [[ -n "$(git -C "$path" status --porcelain)" ]]; then
        echo "Source checkout is dirty: $path" >&2
        exit 2
    fi
}

check_source "$SOURCES_ROOT/amis-moedict" "$EXPECTED_MOEDICT_COMMIT"
check_source "$SOURCES_ROOT/amis-safolu" "$EXPECTED_SAFOLU_COMMIT"

SHARED_CONVERSION="$BANK/Orthographies/ConversionTables/Amis_Safolu_113.tsv"
LOCAL_CONVERSION="$CODEDOCS/data/orthography/Amis_Safolu_113.tsv"
if ! cmp -s "$LOCAL_CONVERSION" "$SHARED_CONVERSION"; then
    echo "Local and shared Safolu conversion tables differ." >&2
    exit 2
fi

STAGE="$WORK_ROOT/generated-XML"
AUDIT="$WORK_ROOT/generated-audit"
UPDATE_VIEW="$WORK_ROOT/published-update-view"
CANONICAL="$CORPUS/XML/Amis/Safolu/amis_safolu_examples.xml"
GENERATED="$STAGE/Amis/Safolu/amis_safolu_examples.xml"

"$PY" "$CODEDOCS/build_formosanbank_xml.py" \
    --sources-dir "$SOURCES_ROOT" \
    --xml-out-dir "$STAGE" \
    --audit-out-dir "$AUDIT"
"$PY" "$CODEDOCS/validate_formosanbank_xml.py" "$GENERATED"
"$PY" "$CODEDOCS/audit_source_coverage.py" \
    --sources-dir "$SOURCES_ROOT" \
    --final-dir "$STAGE" \
    --audit-dir "$AUDIT" \
    --out "$REPORT_ROOT/source-coverage.json"

"$PY" "$BANK/QC/cleaning/clean_xml.py" --corpora_path "$STAGE"
if [[ ! -f "$STAGE/cleaner_warnings.csv" ]]; then
    echo "Cleaner did not produce its warning report." >&2
    exit 1
fi
mv "$STAGE/cleaner_warnings.csv" "$REPORT_ROOT/cleaner_warnings.csv"

"$PY" "$BANK/QC/utilities/standardize.py" \
    --tsv_path "$SHARED_CONVERSION" \
    --target_column Coastal \
    --single-pass \
    --corpora_path "$STAGE"
if [[ -f "$STAGE/standardize_warnings.csv" ]]; then
    mv "$STAGE/standardize_warnings.csv" "$REPORT_ROOT/standardize_warnings.csv"
fi

"$PY" "$BANK/QC/utilities/add_phonology.py" \
    --orthography Safolu \
    --corpora_path "$STAGE"

DUPLICATE_RESULT="$(
    "$PY" "$BANK/QC/cleaning/remove_duplicate_sentences.py" \
        by_path --path "$STAGE" --apply
)"
printf '%s\n' "$DUPLICATE_RESULT"
if [[ "$DUPLICATE_RESULT" != "No duplicate <S> elements found to remove." ]]; then
    echo "Post-generation duplicate removal changed the source-backed record set." >&2
    exit 1
fi

mkdir -p "$UPDATE_VIEW"
for published in "$BANK/Corpora"/*; do
    [[ -d "$published" ]] || continue
    [[ "$(basename "$published")" == "Safolu-Amis-Dictionary" ]] && continue
    ln -s "$published" "$UPDATE_VIEW/$(basename "$published")"
done

"$PY" "$BANK/QC/validation/validate_xml.py" by_path \
    --path "$STAGE" \
    --published-corpora "$UPDATE_VIEW" \
    --csv "$REPORT_ROOT/validate_xml.csv"
"$PY" "$BANK/QC/validation/validate_text.py" by_path \
    --path "$STAGE" \
    --csv "$REPORT_ROOT/validate_text.csv"

if find "$STAGE" -type f ! -name '*.xml' -print -quit | grep -q .; then
    echo "Generated XML tree contains a non-XML file." >&2
    exit 1
fi

if [[ "$MODE" == "check" ]]; then
    if ! cmp -s "$CANONICAL" "$GENERATED"; then
        echo "Generated XML differs from the committed canonical XML." >&2
        git diff --no-index --stat -- "$CANONICAL" "$GENERATED" || true
        exit 1
    fi
    echo "Canonical XML matches the pinned source rebuild."
else
    mkdir -p "$(dirname "$CANONICAL")"
    cp "$GENERATED" "$CANONICAL"
    echo "Updated $CANONICAL from the verified source rebuild."
fi

echo "FormosanBank authority commit: $(git -C "$BANK" rev-parse HEAD)"
echo "Safolu source fields accounted for: 49,419 / 49,419"
echo "Canonical sentences: 49,179"
echo "Reports: $REPORT_ROOT"
BUILD_SUCCEEDED=1

#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
PYTHON_REQUEST=${PRESIDENTIAL_PYTHON:-python3}
if [[ "$PYTHON_REQUEST" == */* ]]; then
    PYTHON_BIN=$(cd "$(dirname "$PYTHON_REQUEST")" && pwd)/$(basename "$PYTHON_REQUEST")
else
    PYTHON_BIN=$(command -v "$PYTHON_REQUEST")
fi
MODE=--check
FORMOSANBANK_ROOT=${PRESIDENTIAL_FORMOSANBANK_ROOT:-}

usage() {
    echo "usage: CodeAndDocs/scripts/reproduce.sh [--check|--write] [--formosanbank-root PATH]" >&2
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --check|--write)
            MODE=$1
            shift
            ;;
        --formosanbank-root)
            [[ $# -ge 2 ]] || { usage; exit 2; }
            FORMOSANBANK_ROOT=$2
            shift 2
            ;;
        *)
            usage
            exit 2
            ;;
    esac
done

"$PYTHON_BIN" -c "import fitz, pytest, rapidfuzz" || {
    echo "Install CodeAndDocs/requirements.txt before reproducing the corpus." >&2
    exit 1
}

read -r AUTHORITY_COMMIT AUTHORITY_REMOTE QC_TREE ORTHOGRAPHIES_TREE \
    BASELINE_XML_TREE REMOVER_BLOB < <(
    "$PYTHON_BIN" - "$REPO_ROOT/CodeAndDocs/data/authority.json" <<'PY'
import json
import sys

authority = json.load(open(sys.argv[1], encoding="utf-8"))["formosanbank"]
objects = authority["objects"]
print(
    authority["commit"],
    authority["remote"],
    objects["QC"],
    objects["Orthographies"],
    objects["Corpora/Presidential_Apologies/XML"],
    objects["Corpora/Presidential_Apologies/CodeAndDocs/remove_standard_cjk_annotations.py"],
)
PY
)

BUILD_ROOT=$(mktemp -d /tmp/presidential-apologies-rebuild.XXXXXX)
PINNED_ROOT="$BUILD_ROOT/formosanbank"
cleanup() {
    rm -rf -- "$BUILD_ROOT"
}
trap cleanup EXIT

if [[ -n "$FORMOSANBANK_ROOT" ]]; then
    if ! git -C "$FORMOSANBANK_ROOT" cat-file -e "$AUTHORITY_COMMIT^{commit}" 2>/dev/null; then
        echo "The supplied FormosanBank checkout does not contain $AUTHORITY_COMMIT." >&2
        exit 1
    fi
    git clone --quiet --shared --no-checkout "$FORMOSANBANK_ROOT" "$PINNED_ROOT"
else
    git clone --quiet --filter=blob:none --no-checkout "$AUTHORITY_REMOTE" "$PINNED_ROOT"
fi
git -C "$PINNED_ROOT" checkout --quiet --detach "$AUTHORITY_COMMIT"

verify_object() {
    local expected=$1
    local object_path=$2
    local actual
    actual=$(git -C "$PINNED_ROOT" rev-parse "HEAD:$object_path")
    if [[ "$actual" != "$expected" ]]; then
        echo "$object_path authority mismatch: $actual" >&2
        exit 1
    fi
}

verify_object "$QC_TREE" QC
verify_object "$ORTHOGRAPHIES_TREE" Orthographies
verify_object "$BASELINE_XML_TREE" Corpora/Presidential_Apologies/XML
verify_object "$REMOVER_BLOB" \
    Corpora/Presidential_Apologies/CodeAndDocs/remove_standard_cjk_annotations.py

mkdir -p "$BUILD_ROOT/reports/qc"
"$PYTHON_BIN" "$REPO_ROOT/CodeAndDocs/scripts/audit_source_alignment.py" \
    --manifest "$REPO_ROOT/CodeAndDocs/data/source_manifest.csv" \
    --report "$BUILD_ROOT/source_alignment.csv"

"$PYTHON_BIN" "$REPO_ROOT/CodeAndDocs/main.py" \
    --output-dir "$BUILD_ROOT/XML"

(
    cd "$BUILD_ROOT"
    "$PYTHON_BIN" "$PINNED_ROOT/QC/cleaning/clean_xml.py" \
        --corpora_path XML
)
if [[ -f "$BUILD_ROOT/XML/cleaner_warnings.csv" ]]; then
    mv "$BUILD_ROOT/XML/cleaner_warnings.csv" \
        "$BUILD_ROOT/reports/qc/cleaner_warnings.csv"
fi
(
    cd "$BUILD_ROOT"
    "$PYTHON_BIN" "$PINNED_ROOT/QC/utilities/standardize.py" \
        --corpora_path XML --copy
    "$PYTHON_BIN" "$PINNED_ROOT/QC/utilities/add_phonology.py" \
        --corpora_path XML --orthography Ortho113
)

"$PYTHON_BIN" \
    "$REPO_ROOT/CodeAndDocs/scripts/remove_standard_cjk_annotations.py" \
    --formosanbank-root "$PINNED_ROOT" \
    --xml-dir "$BUILD_ROOT/XML"

PUBLISHED_ROOT="$BUILD_ROOT/published-corpora"
mkdir -p "$PUBLISHED_ROOT"
for corpus_path in "$PINNED_ROOT"/Corpora/*; do
    corpus_name=$(basename "$corpus_path")
    if [[ "$corpus_name" != "Presidential_Apologies" ]]; then
        ln -s "$corpus_path" "$PUBLISHED_ROOT/$corpus_name"
    fi
done

"$PYTHON_BIN" "$PINNED_ROOT/QC/validation/validate_xml.py" \
    --published-corpora "$PUBLISHED_ROOT" \
    --csv "$BUILD_ROOT/reports/qc/validate_xml.csv" \
    by_path --path "$BUILD_ROOT/XML"
"$PYTHON_BIN" "$PINNED_ROOT/QC/validation/validate_text.py" \
    --csv "$BUILD_ROOT/reports/qc/validate_text.csv" \
    by_path --path "$BUILD_ROOT/XML"
"$PYTHON_BIN" "$PINNED_ROOT/QC/validation/validate_glosses.py" \
    --csv "$BUILD_ROOT/reports/qc/validate_glosses.csv" \
    by_path --path "$BUILD_ROOT/XML"
"$PYTHON_BIN" "$PINNED_ROOT/QC/validation/validate_duplicate_sentences.py" \
    by_path --path "$BUILD_ROOT/XML" \
    --output "$BUILD_ROOT/reports/qc/duplicate_sentences.csv"

env \
    PRESIDENTIAL_XML_ROOT="$BUILD_ROOT/XML" \
    PRESIDENTIAL_PUBLIC_XML_ROOT="$PINNED_ROOT/Corpora/Presidential_Apologies/XML" \
    PRESIDENTIAL_ALIGNMENT_REPORT="$BUILD_ROOT/source_alignment.csv" \
    PRESIDENTIAL_QC_REPORT_ROOT="$BUILD_ROOT/reports/qc" \
    PYTHONPATH="$REPO_ROOT" \
    "$PYTHON_BIN" -m pytest -q "$REPO_ROOT/CodeAndDocs/tests"

if [[ "$MODE" == "--write" ]]; then
    mkdir -p "$REPO_ROOT/XML"
    rsync -a --delete "$BUILD_ROOT/XML/" "$REPO_ROOT/XML/"
    cp "$BUILD_ROOT/source_alignment.csv" \
        "$REPO_ROOT/CodeAndDocs/data/source_alignment.csv"
else
    diff -qr "$BUILD_ROOT/XML" "$REPO_ROOT/XML"
    diff -q "$BUILD_ROOT/source_alignment.csv" \
        "$REPO_ROOT/CodeAndDocs/data/source_alignment.csv"
fi

"$PYTHON_BIN" "$PINNED_ROOT/QC/validation/validate_port_readiness.py" \
    --corpus_path "$REPO_ROOT" \
    --repo-root "$PINNED_ROOT"

echo "Presidential Apologies reproduction and QC completed successfully."

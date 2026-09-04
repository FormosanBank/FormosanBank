#!/usr/bin/env bash
set -euo pipefail

CODE_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
CORPUS_ROOT=$(cd "$CODE_ROOT/.." && pwd)
SOURCE_ROOT=${PAIWAN_SOURCE_ROOT:-"$CODE_ROOT"}
PYTHON_BIN=${PAIWAN_PYTHON:-python3}
MODE=${1:---write}

if [[ "$MODE" != "--write" && "$MODE" != "--check" ]]; then
    echo "usage: CodeAndDocs/make_xml.sh [--write|--check]" >&2
    exit 2
fi

"$PYTHON_BIN" -c "import docx, lxml, regex" || {
    echo "Install the pinned Python packages with: python3 -m pip install -r CodeAndDocs/requirements.txt" >&2
    exit 1
}

while read -r expected source_name; do
    [[ -n "$expected" ]] || continue
    source_path="$SOURCE_ROOT/$source_name"
    if [[ ! -f "$source_path" ]]; then
        echo "Missing source file: $source_path" >&2
        exit 1
    fi
    actual=$(shasum -a 256 "$source_path" | cut -d ' ' -f 1)
    if [[ "$actual" != "$expected" ]]; then
        echo "Source checksum mismatch: $source_name" >&2
        exit 1
    fi
done < "$CODE_ROOT/data/source_checksums.sha256"

AUTHORITY_VALUES=$("$PYTHON_BIN" - "$CODE_ROOT/data/authority.json" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
values = [
    data["public_baseline"]["commit"],
    data["public_baseline"]["corpus_xml_tree"],
    data["tooling"]["clean_xml_blob"],
    data["tooling"]["standardize_blob"],
    data["tooling"]["add_phonology_blob"],
    data["tooling"]["ferrell_conversion_table_blob"],
    data["tooling"]["ferrell_phonology_profile_blob"],
    data["tooling"]["ortho113_paiwan_blob"],
    data["tooling"]["validate_xml_blob"],
    data["tooling"]["validate_text_blob"],
    data["tooling"]["validate_glosses_blob"],
    data["tooling"]["audit_gloss_scrape_blob"],
    data["tooling"]["validate_conversion_table_blob"],
    data["port_remediation"]["corrected_blob"],
    data["port_remediation"]["corrected_sha256"],
]
print(" ".join(values))
PY
)
read -r AUTHORITY_COMMIT CORPUS_XML_TREE CLEAN_XML_BLOB STANDARDIZE_BLOB \
    ADD_PHONOLOGY_BLOB FERRELL_CONVERSION_BLOB FERRELL_PROFILE_BLOB \
    ORTHO113_PAIWAN_BLOB VALIDATE_XML_BLOB VALIDATE_TEXT_BLOB \
    VALIDATE_GLOSSES_BLOB AUDIT_GLOSS_SCRAPE_BLOB \
    VALIDATE_CONVERSION_TABLE_BLOB CORRECTED_CONVERSION_BLOB \
    CORRECTED_CONVERSION_SHA256 <<<"$AUTHORITY_VALUES"

BUILD_ROOT=$(mktemp -d /tmp/hundred-paiwan-rebuild.XXXXXX)
PINNED_ROOT="$BUILD_ROOT/formosanbank"
cleanup() {
    rm -rf -- "$BUILD_ROOT"
}
trap cleanup EXIT

LOCAL_FORMOSANBANK=${PAIWAN_FORMOSANBANK_ROOT:-$(cd "$CORPUS_ROOT/../.." && pwd)}
if [[ -n "${PAIWAN_FORMOSANBANK_ROOT:-}" ]] \
    && [[ "$(git -C "$LOCAL_FORMOSANBANK" rev-parse HEAD 2>/dev/null || true)" == "$AUTHORITY_COMMIT" ]]; then
    PINNED_ROOT=$(cd "$LOCAL_FORMOSANBANK" && pwd)
elif git -C "$LOCAL_FORMOSANBANK" cat-file -e "$AUTHORITY_COMMIT^{commit}" 2>/dev/null; then
    git clone --quiet --shared --no-checkout "$LOCAL_FORMOSANBANK" "$PINNED_ROOT"
    git -C "$PINNED_ROOT" checkout --quiet --detach "$AUTHORITY_COMMIT"
else
    git clone --quiet --filter=blob:none --no-checkout \
        https://github.com/FormosanBank/FormosanBank.git "$PINNED_ROOT"
    git -C "$PINNED_ROOT" checkout --quiet --detach "$AUTHORITY_COMMIT"
fi

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

if [[ "$(git -C "$PINNED_ROOT" rev-parse HEAD)" != "$AUTHORITY_COMMIT" ]]; then
    echo "FormosanBank authority commit mismatch" >&2
    exit 1
fi
verify_object "$CORPUS_XML_TREE" "Corpora/HundredPaiwanStories/XML"
verify_object "$CLEAN_XML_BLOB" "QC/cleaning/clean_xml.py"
verify_object "$STANDARDIZE_BLOB" "QC/utilities/standardize.py"
verify_object "$ADD_PHONOLOGY_BLOB" "QC/utilities/add_phonology.py"
verify_object "$FERRELL_CONVERSION_BLOB" "Orthographies/ConversionTables/Paiwan_Ferrell_113.tsv"
verify_object "$FERRELL_PROFILE_BLOB" "Orthographies/Ferrell/Paiwan.tsv"
verify_object "$ORTHO113_PAIWAN_BLOB" "Orthographies/Ortho113/Paiwan.tsv"
verify_object "$VALIDATE_XML_BLOB" "QC/validation/validate_xml.py"
verify_object "$VALIDATE_TEXT_BLOB" "QC/validation/validate_text.py"
verify_object "$VALIDATE_GLOSSES_BLOB" "QC/validation/validate_glosses.py"
verify_object "$AUDIT_GLOSS_SCRAPE_BLOB" "QC/validation/audit_gloss_scrape.py"
verify_object "$VALIDATE_CONVERSION_TABLE_BLOB" "QC/validation/validate_conversion_table.py"

CORRECTED_CONVERSION="$CODE_ROOT/data/Paiwan_Ferrell_113.tsv"
if [[ "$(git hash-object "$CORRECTED_CONVERSION")" != "$CORRECTED_CONVERSION_BLOB" ]]; then
    echo "corrected Ferrell conversion table blob mismatch" >&2
    exit 1
fi
if [[ "$(shasum -a 256 "$CORRECTED_CONVERSION" | cut -d ' ' -f 1)" != "$CORRECTED_CONVERSION_SHA256" ]]; then
    echo "corrected Ferrell conversion table checksum mismatch" >&2
    exit 1
fi
"$PYTHON_BIN" "$PINNED_ROOT/QC/validation/validate_conversion_table.py" \
    "$PINNED_ROOT/Orthographies/Ferrell/Paiwan.tsv" \
    "$PINNED_ROOT/Orthographies/Ortho113/Paiwan.tsv" \
    "$CORRECTED_CONVERSION"

BUILD_CONVERSION_ROOT="$BUILD_ROOT/Orthographies"
mkdir -p "$BUILD_CONVERSION_ROOT/ConversionTables" "$BUILD_CONVERSION_ROOT/Ferrell"
cp "$CORRECTED_CONVERSION" \
    "$BUILD_CONVERSION_ROOT/ConversionTables/Paiwan_Ferrell_113.tsv"
ln -s "$PINNED_ROOT/Orthographies/Ferrell/Paiwan.tsv" \
    "$BUILD_CONVERSION_ROOT/Ferrell/Paiwan.tsv"

mkdir -p "$BUILD_ROOT/reports/rebuild" "$BUILD_ROOT/reports/qc"
"$PYTHON_BIN" "$CODE_ROOT/scripts/rebuild_xml.py" \
    --source "$SOURCE_ROOT/Paiwan Ch2 Preprocessed.docx" \
    --baseline "$PINNED_ROOT/Corpora/HundredPaiwanStories/XML" \
    --output "$BUILD_ROOT/XML" \
    --reports "$BUILD_ROOT/reports/rebuild"

(
    cd "$BUILD_ROOT"
    "$PYTHON_BIN" "$PINNED_ROOT/QC/cleaning/clean_xml.py" \
        --corpora_path XML
)
mv "$BUILD_ROOT/XML/cleaner_warnings.csv" \
    "$BUILD_ROOT/reports/qc/cleaner_warnings.csv"
# POL-035: clean_xml writes its durable quote-correction log to
# <corpus root>/CodeAndDocs/. Keep it with the other QC evidence so the
# ' -> " rewrites it made to the original tier stay auditable.
mv "$BUILD_ROOT/CodeAndDocs/quote_corrections.csv" \
    "$BUILD_ROOT/reports/qc/quote_corrections.csv"

# Recorded hand edits. Runs after the cleaner and BEFORE standardize.py and
# add_phonology.py, because apply_manual_edits replaces an S from a record
# that carries no standard FORM and no PHON -- both are regenerated below.
# One edit is expected; a no-op would mean the build now produces it by
# itself and the record is obsolete (POL-030), so treat that as a failure
# rather than a warning.
cp "$CODE_ROOT/manual_edits.xml" "$BUILD_ROOT/CodeAndDocs/manual_edits.xml"
MANUAL_EDITS=$(
    cd "$BUILD_ROOT" && "$PYTHON_BIN" "$PINNED_ROOT/QC/cleaning/apply_manual_edits.py" \
        --corpora_path XML
)
echo "$MANUAL_EDITS"
if [[ "$MANUAL_EDITS" != *"apply: 1 edit(s) across 1 file(s); 0 no-op(s)"* ]]; then
    echo "unexpected manual-edit result" >&2
    exit 1
fi

# Reviewed source-annotation corrections, also BEFORE standardize.py: the
# source's "(?)" uncertain-reading mark is removed from the original FORM
# and recorded in its notes attribute, so the standard tier is derived
# rather than repaired afterwards (standardize would read "?" as a glottal).
CORRECTIONS=$(
    "$PYTHON_BIN" "$CODE_ROOT/scripts/apply_manual_corrections.py" \
        --corpora-path "$BUILD_ROOT/XML"
)
echo "$CORRECTIONS"
EXPECTED_CORRECTIONS=$'reviewed_corrections=11\ncorrected_originals=11'
if [[ "$CORRECTIONS" != "$EXPECTED_CORRECTIONS" ]]; then
    echo "unexpected source-annotation correction result" >&2
    exit 1
fi

(
    cd "$BUILD_ROOT"
    "$PYTHON_BIN" "$PINNED_ROOT/QC/utilities/standardize.py" \
        --corpora_path XML \
        --language Paiwan \
        --tsv_path "$BUILD_CONVERSION_ROOT/ConversionTables/Paiwan_Ferrell_113.tsv"
    "$PYTHON_BIN" "$PINNED_ROOT/QC/utilities/add_phonology.py" \
        --corpora_path XML \
        --orthography Ferrell
)

"$PYTHON_BIN" "$CODE_ROOT/fix_ferrell.py" --corpora-path "$BUILD_ROOT/XML"
FIRST_NORMALIZE=$(
    "$PYTHON_BIN" "$CODE_ROOT/normalize_sentence_standards.py" \
        --corpora-path "$BUILD_ROOT/XML"
)
EXPECTED_FIRST_NORMALIZE=$'exact_decisions=16\ncorrected_forms=0\ncorrected_phon=0\nnormalized_complete_variants=0'
if [[ "$FIRST_NORMALIZE" != "$EXPECTED_FIRST_NORMALIZE" ]]; then
    echo "unexpected first normalization result" >&2
    echo "$FIRST_NORMALIZE" >&2
    exit 1
fi
SECOND_NORMALIZE=$(
    "$PYTHON_BIN" "$CODE_ROOT/normalize_sentence_standards.py" \
        --corpora-path "$BUILD_ROOT/XML"
)
EXPECTED_SECOND_NORMALIZE=$'exact_decisions=16\ncorrected_forms=0\ncorrected_phon=0\nnormalized_complete_variants=0'
if [[ "$SECOND_NORMALIZE" != "$EXPECTED_SECOND_NORMALIZE" ]]; then
    echo "normalization is not idempotent" >&2
    echo "$SECOND_NORMALIZE" >&2
    exit 1
fi

PUBLISHED_ROOT="$BUILD_ROOT/published-corpora"
mkdir -p "$PUBLISHED_ROOT"
for corpus_path in "$PINNED_ROOT"/Corpora/*; do
    corpus_name=$(basename "$corpus_path")
    if [[ "$corpus_name" != "HundredPaiwanStories" ]]; then
        ln -s "$corpus_path" "$PUBLISHED_ROOT/$corpus_name"
    fi
done

(
    cd "$BUILD_ROOT"
    "$PYTHON_BIN" "$PINNED_ROOT/QC/validation/validate_xml.py" by_path \
        --path XML \
        --published-corpora published-corpora \
        --csv reports/qc/xml.csv
    "$PYTHON_BIN" "$PINNED_ROOT/QC/validation/validate_text.py" by_path \
        --path XML \
        --csv reports/qc/text.csv
    "$PYTHON_BIN" "$PINNED_ROOT/QC/validation/validate_glosses.py" by_path \
        --path XML \
        --csv reports/qc/gloss.csv
    # No --exit-on-hard: G001 fires once, by design, on the unglossed -i in
    # 078S4W19 (see review_qc_findings.py). scripts/review_qc_findings.py is
    # the gate -- it pins that finding to that location and rejects any other.
    "$PYTHON_BIN" "$PINNED_ROOT/QC/validation/audit_gloss_scrape.py" \
        --xml XML \
        --no-source \
        --csv reports/qc/scrape.csv
)

"$PYTHON_BIN" - "$BUILD_ROOT/reports" <<'PY'
import sys
from pathlib import Path

root = Path(sys.argv[1])
for pattern in ("*.csv", "*.tsv"):
    for path in root.rglob(pattern):
        content = path.read_bytes()
        path.write_bytes(content.replace(b"\r\n", b"\n"))
PY

(
    cd "$BUILD_ROOT"
    "$PYTHON_BIN" "$CODE_ROOT/scripts/review_qc_findings.py" \
        --xml XML \
        --xml-findings reports/qc/xml.csv \
        --text-findings reports/qc/text.csv \
        --gloss-findings reports/qc/gloss.csv \
        --scrape-findings reports/qc/scrape.csv \
        --decisions "$CODE_ROOT/standard_surface_decisions.tsv" \
        --json-output reports/qc/soft_findings_review.json \
        --markdown-output reports/qc/qc-summary.md
)

env \
    PYTHONPATH="$CODE_ROOT${PYTHONPATH:+:$PYTHONPATH}" \
    PAIWAN_XML_ROOT="$BUILD_ROOT/XML" \
    PAIWAN_REPORTS_ROOT="$BUILD_ROOT/reports" \
    PAIWAN_SOURCE_ROOT="$SOURCE_ROOT" \
    "$PYTHON_BIN" -m unittest discover -s "$CODE_ROOT/tests" -v

if [[ "$MODE" == "--check" ]]; then
    diff -qr "$BUILD_ROOT/XML" "$CORPUS_ROOT/XML"
    diff -qr "$BUILD_ROOT/reports/rebuild" "$CODE_ROOT/reports/rebuild"
    cmp "$BUILD_ROOT/reports/qc/qc-summary.md" "$CODE_ROOT/reports/qc/qc-summary.md"
    cmp "$BUILD_ROOT/reports/qc/soft_findings_review.json" \
        "$CODE_ROOT/reports/qc/soft_findings_review.json"
    cmp "$BUILD_ROOT/reports/qc/cleaner_warnings.csv" \
        "$CODE_ROOT/reports/qc/cleaner_warnings.csv"
    cmp "$BUILD_ROOT/reports/qc/quote_corrections.csv" \
        "$CODE_ROOT/reports/qc/quote_corrections.csv"
    cmp "$BUILD_ROOT/CodeAndDocs/manual_edits.md" "$CODE_ROOT/manual_edits.md"
else
    mkdir -p "$CORPUS_ROOT/XML" "$CODE_ROOT/reports/rebuild" "$CODE_ROOT/reports/qc"
    rsync -a --delete "$BUILD_ROOT/XML/" "$CORPUS_ROOT/XML/"
    rsync -a --delete "$BUILD_ROOT/reports/rebuild/" "$CODE_ROOT/reports/rebuild/"
    cp "$BUILD_ROOT/reports/qc/qc-summary.md" "$CODE_ROOT/reports/qc/qc-summary.md"
    cp "$BUILD_ROOT/reports/qc/soft_findings_review.json" \
        "$CODE_ROOT/reports/qc/soft_findings_review.json"
    cp "$BUILD_ROOT/reports/qc/cleaner_warnings.csv" \
        "$CODE_ROOT/reports/qc/cleaner_warnings.csv"
    cp "$BUILD_ROOT/reports/qc/quote_corrections.csv" \
        "$CODE_ROOT/reports/qc/quote_corrections.csv"
    cp "$BUILD_ROOT/CodeAndDocs/manual_edits.md" "$CODE_ROOT/manual_edits.md"
    diff -qr "$BUILD_ROOT/XML" "$CORPUS_ROOT/XML"
    diff -qr "$BUILD_ROOT/reports/rebuild" "$CODE_ROOT/reports/rebuild"
    cmp "$BUILD_ROOT/reports/qc/qc-summary.md" "$CODE_ROOT/reports/qc/qc-summary.md"
    cmp "$BUILD_ROOT/reports/qc/soft_findings_review.json" \
        "$CODE_ROOT/reports/qc/soft_findings_review.json"
    cmp "$BUILD_ROOT/reports/qc/cleaner_warnings.csv" \
        "$CODE_ROOT/reports/qc/cleaner_warnings.csv"
    cmp "$BUILD_ROOT/reports/qc/quote_corrections.csv" \
        "$CODE_ROOT/reports/qc/quote_corrections.csv"
    cmp "$BUILD_ROOT/CodeAndDocs/manual_edits.md" "$CODE_ROOT/manual_edits.md"
fi

echo "Hundred Paiwan Stories reproduction and QC completed successfully."

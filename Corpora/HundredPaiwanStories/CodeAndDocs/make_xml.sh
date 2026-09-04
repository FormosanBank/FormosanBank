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

BUILD_ROOT=$(mktemp -d /tmp/hundred-paiwan-rebuild.XXXXXX)
cleanup() {
    rm -rf -- "$BUILD_ROOT"
}
trap cleanup EXIT

# Build against the live FormosanBank checkout. The bank's model is that
# shared tooling improves and corpora are regenerated against it, so this
# deliberately does not pin a commit or verify tooling blobs;
# data/provenance.json records what the published output was built
# against, and nothing reads it.
BANK=${PAIWAN_FORMOSANBANK_ROOT:-$(cd "$CORPUS_ROOT/../.." && pwd)}
if [[ ! -d "$BANK/QC" ]]; then
    echo "Not a FormosanBank checkout: $BANK" >&2
    echo "Set PAIWAN_FORMOSANBANK_ROOT to the repository root." >&2
    exit 1
fi

CONVERSION_TABLE="$BANK/Orthographies/ConversionTables/Paiwan_Ferrell_113.tsv"
"$PYTHON_BIN" "$BANK/QC/validation/validate_conversion_table.py" \
    "$BANK/Orthographies/Ferrell/Paiwan.tsv" \
    "$BANK/Orthographies/Ortho113/Paiwan.tsv" \
    "$CONVERSION_TABLE"

mkdir -p "$BUILD_ROOT/reports/rebuild" "$BUILD_ROOT/reports/qc"
"$PYTHON_BIN" "$CODE_ROOT/scripts/rebuild_xml.py" \
    --source "$SOURCE_ROOT/Paiwan Ch2 Preprocessed.docx" \
    --output "$BUILD_ROOT/XML" \
    --reports "$BUILD_ROOT/reports/rebuild"

(
    cd "$BUILD_ROOT"
    "$PYTHON_BIN" "$BANK/QC/cleaning/clean_xml.py" \
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
    cd "$BUILD_ROOT" && "$PYTHON_BIN" "$BANK/QC/cleaning/apply_manual_edits.py" \
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
    "$PYTHON_BIN" "$BANK/QC/utilities/standardize.py" \
        --corpora_path XML \
        --language Paiwan \
        --tsv_path "$CONVERSION_TABLE"
    "$PYTHON_BIN" "$BANK/QC/utilities/add_phonology.py" \
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
for corpus_path in "$BANK"/Corpora/*; do
    corpus_name=$(basename "$corpus_path")
    if [[ "$corpus_name" != "HundredPaiwanStories" ]]; then
        ln -s "$corpus_path" "$PUBLISHED_ROOT/$corpus_name"
    fi
done

(
    cd "$BUILD_ROOT"
    "$PYTHON_BIN" "$BANK/QC/validation/validate_xml.py" by_path \
        --path XML \
        --published-corpora published-corpora \
        --csv reports/qc/xml.csv
    "$PYTHON_BIN" "$BANK/QC/validation/validate_text.py" by_path \
        --path XML \
        --csv reports/qc/text.csv
    "$PYTHON_BIN" "$BANK/QC/validation/validate_glosses.py" by_path \
        --path XML \
        --csv reports/qc/gloss.csv
    # No --exit-on-hard: G001 fires once, by design, on the unglossed -i in
    # 078S4W19 (see review_qc_findings.py). scripts/review_qc_findings.py is
    # the gate -- it pins that finding to that location and rejects any other.
    "$PYTHON_BIN" "$BANK/QC/validation/audit_gloss_scrape.py" \
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

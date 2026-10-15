#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
FB="${FORMOSANBANK_ROOT:-$(cd "$HERE/../../.." && pwd)}"
PY="${PYTHON:-python3}"
REPORTS="${QC_OUTPUT_DIR:-$(mktemp -d "${TMPDIR:-/tmp}/nowbucyang-build-reports.XXXXXX")}"
STAGE="$(mktemp -d "$HERE/.build.XXXXXX")"
trap 'rm -rf "$STAGE"' EXIT
export PYTHONDONTWRITEBYTECODE=1

mkdir -p "$STAGE/CodeAndDocs/data/processed" "$REPORTS"
cp -R "$HERE/scripts" "$STAGE/CodeAndDocs/"
cp -R "$HERE/data/manual" "$STAGE/CodeAndDocs/data/"
for name in quality_filtered_examples.jsonl examples_raw.jsonl examples_clean.jsonl gloss_records.jsonl duplicates.csv source_metadata.csv; do
    cp "$HERE/data/processed/$name" "$STAGE/CodeAndDocs/data/processed/"
done
cp "$HERE/manual_edits.xml" "$STAGE/CodeAndDocs/"

"$PY" "$STAGE/CodeAndDocs/scripts/pipeline.py" --step build_formosanbank_xml --config "$STAGE/CodeAndDocs/scripts/config.yaml"
BUILD="$STAGE/CodeAndDocs/XML"
"$PY" "$FB/QC/cleaning/apply_manual_edits.py" --corpora_path "$BUILD" --manual_file "$STAGE/CodeAndDocs/manual_edits.xml"
cp "$STAGE/CodeAndDocs/manual_edits.md" "$HERE/manual_edits.md"
"$PY" "$FB/QC/cleaning/clean_xml.py" --corpora_path "$BUILD" --warnings_dir "$REPORTS"
"$PY" "$FB/QC/utilities/standardize.py" --corpora_path "$BUILD" --tsv_path "$FB/Orthographies/ConversionTables/Seediq_94_113.tsv"
"$PY" "$HERE/replay_reviewed_merges.py" --formosanbank "$FB" --xml "$BUILD/Truku/Hsu_Lowking_Truku_WordFormation_2008.xml"
"$PY" "$FB/QC/utilities/add_phonology.py" --corpora_path "$BUILD" --orthography Ortho94

cp "$STAGE/CodeAndDocs/data/processed/"*.csv "$REPORTS/"
cp "$STAGE/CodeAndDocs/data/processed/"*.txt "$REPORTS/"
find "$BUILD" -name '*warnings.csv' -exec mv {} "$REPORTS/" \;
if [ -f "$BUILD/quote_corrections.csv" ]; then
    cp "$BUILD/quote_corrections.csv" "$REPORTS/"
    echo 'Unexpected Truku quote correction; review the durable correction evidence.' >&2
    exit 1
fi
mkdir -p "$ROOT/XML"
rsync -a --delete "$BUILD/" "$ROOT/XML/"
"$PY" - "$FB" "$HERE/provenance.json" <<'PROVENANCE_PY'
import json
import subprocess
import sys
from pathlib import Path

root, destination = Path(sys.argv[1]).resolve(), Path(sys.argv[2])
if (root / ".git").exists():
    commit = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    destination.write_text(json.dumps({"formosanbank_commit": commit}, indent=2) + "\n")
elif not destination.is_file():
    raise SystemExit("The export must retain CodeAndDocs/provenance.json.")
PROVENANCE_PY
printf 'Build reports: %s\n' "$REPORTS"

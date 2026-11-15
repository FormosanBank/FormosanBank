#!/usr/bin/env bash
set -euo pipefail
CODEDOCS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORPUS="$(dirname "$CODEDOCS")"
if [[ -n "${FORMOSANBANK_ROOT:-${1:-}}" ]]; then
    BANK="$(cd "${FORMOSANBANK_ROOT:-$1}" && pwd)"
elif [[ -d "$CORPUS/../../QC" ]]; then
    BANK="$(cd "$CORPUS/../.." && pwd)"
else
    BANK="$(cd "$CORPUS/../FormosanBank" && pwd)"
fi
PY="${PYTHON:-python3}"
CONVERSION="$BANK/Orthographies/ConversionTables/Amis_Church_113.tsv"
for required in "$BANK/Orthographies/Church/Amis.tsv" "$CONVERSION"; do
    if [[ ! -f "$required" ]]; then
        echo "Missing shared orthography input: $required" >&2
        exit 2
    fi
done

STAGE="$(mktemp -d "$CODEDOCS/.build-XXXXXX")"
trap 'rm -rf "$STAGE"' EXIT
"$PY" "$CODEDOCS/generate_xml.py" --xml-out-dir "$STAGE/XML"
# Headword entries (CodeAndDocs/headwords/): the switches are the maintainer's rulings (decision log, "Dictionary headwords").
HW="$CODEDOCS/headwords"
"$PY" "$HW/generate_headwords.py" --out "$STAGE/XML/Amis/Safolu/amis_safolu_headwords.xml" \
    --xref drop --label notes --nochinese drop --affix drop --stem-tag notes --syn-rel none --embedded drop \
    --tags norm --label-pos transl --affix-rule --affix-strong --letters drop-desc --headings drop \
    --cuts "$HW/repaired_breaks.tsv" --restore-lost --pos "$HW/pos_labels.tsv" --borrow "$HW/borrow_labels.tsv" \
    --split "$HW/homophone_split.tsv" --restore "$HW/restored_senses.tsv" --replace "$HW/corrected_senses.tsv" \
    --missed "$HW/missed_headwords.tsv" --add-entries "$HW/lost_headwords.tsv" --pieces "$HW/example_pieces_removed.tsv"
"$PY" "$BANK/QC/cleaning/clean_xml.py" --corpora_path "$STAGE/XML"
"$PY" "$BANK/QC/utilities/standardize.py" --tsv_path "$CONVERSION" \
    --target_column Coastal --corpora_path "$STAGE/XML"
"$PY" "$BANK/QC/utilities/add_phonology.py" --orthography Church --corpora_path "$STAGE/XML"
"$PY" "$BANK/QC/cleaning/remove_duplicate_sentences.py" by_path --path "$STAGE/XML" --apply

"$PY" - "$BANK" "$STAGE/provenance.json" "$CODEDOCS/provenance.json" <<'PY'
import json
import subprocess
import sys
from pathlib import Path
bank, destination, previous = map(Path, sys.argv[1:])
if (bank / ".git").exists():
    commit = subprocess.check_output(["git", "-C", str(bank), "rev-parse", "HEAD"], text=True).strip()
    destination.write_text(json.dumps({"formosanbank_commit": commit}, indent=2) + "\n")
else:
    destination.write_bytes(previous.read_bytes())
    print("No Git metadata: verify the export tools revision separately; retain provenance.")
PY
mkdir -p "$CORPUS/XML/Amis/Safolu"
cp "$STAGE/XML/Amis/Safolu/amis_safolu_examples.xml" "$CORPUS/XML/Amis/Safolu/amis_safolu_examples.xml"
cp "$STAGE/XML/Amis/Safolu/amis_safolu_headwords.xml" "$CORPUS/XML/Amis/Safolu/amis_safolu_headwords.xml"
cp "$STAGE/provenance.json" "$CODEDOCS/provenance.json"

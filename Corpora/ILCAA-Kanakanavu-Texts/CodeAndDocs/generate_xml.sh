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
"$PY" - "$CODEDOCS/introduction_lexemes.json" <<'PY'
import json
import sys
from pathlib import Path
profiles = {r["profile"] for r in json.loads(Path(sys.argv[1]).read_text())["records"]}
# Table 2's 16 Tsuchida1976 pronouns use the reviewed Asai2026 grapheme subset.
unsupported = sorted(profiles - {"Asai2026", "SaaroaComparison", "Tsuchida1976"})
if unsupported:
    print("Final generation needs reviewed per-source routes for: " + ", ".join(unsupported), file=sys.stderr)
    sys.exit(2)
PY
SOURCE_ORTHOGRAPHY="$CODEDOCS/scripts/orthographies/Asai2026"
CONVERSION="$CODEDOCS/scripts/orthographies/ConversionTables/Kanakanavu_Asai2026_113.tsv"
SAAROA_ORTHOGRAPHY="$CODEDOCS/scripts/orthographies/SaaroaComparison"
SAAROA_CONVERSION="$CODEDOCS/scripts/orthographies/ConversionTables/Saaroa_SaaroaComparison_113.tsv"
for required in "$SOURCE_ORTHOGRAPHY/Kanakanavu.tsv" "$SOURCE_ORTHOGRAPHY/Kanakanavu.rules.tsv" \
    "$CONVERSION" "$SAAROA_ORTHOGRAPHY/Saaroa.tsv" "$SAAROA_CONVERSION"; do
    if [[ ! -f "$required" ]]; then
        echo "Missing committed Kanakanavu orthography input: $required" >&2
        exit 2
    fi
done

STAGE="$(mktemp -d "$CODEDOCS/.build-XXXXXX")"
trap 'rm -rf "$STAGE"' EXIT
"$PY" "$CODEDOCS/scripts/pipeline.py" --workspace "$STAGE"
XML_STAGE="$STAGE/build/xml_drafts"
"$PY" "$BANK/QC/cleaning/clean_xml.py" --corpora_path "$XML_STAGE"
"$PY" "$BANK/QC/utilities/standardize.py" --tsv_path "$CONVERSION" \
    --target_column standard --corpora_path "$XML_STAGE/Kanakanavu"
"$PY" "$BANK/QC/utilities/add_phonology.py" --orthography "$SOURCE_ORTHOGRAPHY" --corpora_path "$XML_STAGE/Kanakanavu"
if [[ -d "$XML_STAGE/Saaroa" ]]; then
    "$PY" "$BANK/QC/utilities/standardize.py" --tsv_path "$SAAROA_CONVERSION" \
        --target_column standard --corpora_path "$XML_STAGE/Saaroa"
    "$PY" "$BANK/QC/utilities/add_phonology.py" --orthography "$SAAROA_ORTHOGRAPHY" --corpora_path "$XML_STAGE/Saaroa"
fi

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
for language in Kanakanavu Saaroa; do
    if [[ -d "$XML_STAGE/$language" ]]; then
        mkdir -p "$CORPUS/XML/$language"
        cp "$XML_STAGE/$language/"*.xml "$CORPUS/XML/$language/"
    fi
done
cp "$STAGE/provenance.json" "$CODEDOCS/provenance.json"

#!/usr/bin/env bash
# THE entry point (POL-047): frozen source snapshot -> published XML/.
#
# Build only. It runs no validators and no tests; those are in validate.sh,
# so a failing check never stops a rebuild that is needed to investigate it.
# The shared tools come from the FormosanBank checkout that contains this
# corpus (POL-048); the commit they were at is recorded in provenance.json
# (POL-052), which is documentation only -- nothing here compares against it.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORPUS_ROOT="$(cd "$HERE/.." && pwd)"
FB="$(cd "$CORPUS_ROOT/../.." && pwd -P)"
PY="${PYTHON:-python3}"
REPORTS="${BUILD_LOG_DIR:-$(mktemp -d "${TMPDIR:-/tmp}/yedda-build.XXXXXX")}"

test -f "$FB/QC/cleaning/clean_xml.py"
mkdir -p "$REPORTS"

# 1. Corpus-local generator: frozen snapshot + reviewed repairs -> original tier.
"$PY" "$HERE/scripts/build_xml.py"
# 2. No manual_edits.xml in this corpus.
# 3. Shared cleaner; its warnings go outside the published tree.
"$PY" "$FB/QC/cleaning/clean_xml.py" --corpora_path "$CORPUS_ROOT/XML" \
    --warnings_dir "$REPORTS"
# Corpus-local, between 3 and 4: POL-023 per-sentence M tier (see README).
"$PY" "$HERE/scripts/fix_m_tier.py" --corpora_path "$CORPUS_ROOT/XML" \
    --formosanbank_root "$FB"
# 4. Standard tier.
"$PY" "$FB/QC/utilities/standardize.py" --corpora_path "$CORPUS_ROOT/XML" \
    --remove_accents
# 5. Phonology.
"$PY" "$FB/QC/utilities/add_phonology.py" --corpora_path "$CORPUS_ROOT/XML" \
    --orthography Ortho113
# Corpus-local, after 5: hashes and counts of the output, for validate.sh.
"$PY" "$HERE/scripts/finalize_manifest.py" > "$REPORTS/manifest.log"

# POL-052: record the tools commit. A note, never a gate.
commit="$(git -C "$FB" rev-parse HEAD 2>/dev/null || true)"
if [[ -z "$commit" ]]; then
    echo "note: $FB is not a git checkout; provenance.json left as it was" >&2
elif ! grep -q "\"formosanbank_commit\": \"$commit\"" "$HERE/provenance.json" 2>/dev/null; then
    echo "note: recording FormosanBank $commit in provenance.json" >&2
    printf '{\n  "_note": "%s",\n  "formosanbank_commit": "%s",\n  "built": "%s"\n}\n' \
        "The FormosanBank commit this corpus was built against. Provenance only — the build does not read this file." \
        "$commit" "$(date -u +%Y-%m-%d)" > "$HERE/provenance.json"
fi

echo "Built $CORPUS_ROOT/XML with the tools in $FB."
echo "Build logs (cleaner warnings): $REPORTS"

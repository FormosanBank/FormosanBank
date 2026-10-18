#!/usr/bin/env bash
# THE entry point (POL-047): NTU's source JSONs -> published XML/.
#
# The JSONs under grammar/, sentence/ and story/ are this corpus's source:
# NTU's published release pinned in source_release.tsv, fetched by
# refresh_source.sh (never run from here, so a rebuild never depends on NTU's
# site). Everything in ../XML/ is derived from them.
#
#   ./generate_xml.sh
#
# Build only. It runs no validators and no tests; the source-coverage audit,
# the validators and the regression check are in validate.sh, so a failing
# check never stops a rebuild that is needed to investigate it. Audio is not
# part of the build: ../download_audio_data.sh fetches it separately.
#
# The build itself is pipeline/build_subcorpora.sh, documented in
# pipeline/README.md. Each subcorpus is built from scratch in a temp dir and
# installed only on success, so rerunning is safe.
#
# The shared tools come from the FormosanBank checkout that contains this
# corpus (POL-048); the commit they were at is recorded in provenance.json
# (POL-052), which is documentation only -- nothing here compares against it.
set -euo pipefail

CODEDOCS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORPUS="$(dirname "$CODEDOCS")"
BANK="$(cd "$CORPUS/../.." && pwd -P)"

PY="${PYTHON:-$BANK/.venv/bin/python}"
[[ -x "$PY" ]] || PY="$(command -v python3)"
export PYTHON="$PY"

test -f "$BANK/QC/cleaning/clean_xml.py"

step() { printf '\n=== %s ===\n' "$*"; }

step "Build XML from the source JSONs (pipeline/build_subcorpora.sh)"
"$CODEDOCS/pipeline/build_subcorpora.sh" all

step "Re-apply recorded hand edits (no-op when manual_edits.xml is absent)"
if [[ -f "$CODEDOCS/manual_edits.xml" ]]; then
  "$PY" "$BANK/QC/cleaning/apply_manual_edits.py" --corpus "$CORPUS"
else
  echo "  no manual_edits.xml; nothing to re-apply"
fi

# POL-052: record the tools commit. A note, never a gate.
commit="$(git -C "$BANK" rev-parse HEAD 2>/dev/null || true)"
if [[ -z "$commit" ]]; then
  echo "note: $BANK is not a git checkout; provenance.json left as it was" >&2
elif ! grep -q "\"formosanbank_commit\": \"$commit\"" "$CODEDOCS/provenance.json" 2>/dev/null; then
  echo "note: recording FormosanBank $commit in provenance.json" >&2
  printf '{\n  "_note": "%s",\n  "formosanbank_commit": "%s",\n  "built": "%s"\n}\n' \
    "The FormosanBank commit this corpus was built against. Provenance only — the build does not read this file." \
    "$commit" "$(date -u +%Y-%m-%d)" > "$CODEDOCS/provenance.json"
fi

step "Done. Review 'git diff' before committing; run validate.sh for the checks."

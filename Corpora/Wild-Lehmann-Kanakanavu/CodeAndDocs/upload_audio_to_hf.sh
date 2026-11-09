#!/usr/bin/env bash
# upload_audio_to_hf.sh — put this corpus's audio on Hugging Face (private until the port).
#
#   bash CodeAndDocs/upload_audio_to_hf.sh --dry-run   # show what would happen; changes nothing
#   bash CodeAndDocs/upload_audio_to_hf.sh             # do it
#
# Steps: (1) stage exactly the files the XML names into Audio_hf/Kanakanavu/;
# (2) create the dataset from .hf_dataset.yaml as PRIVATE if it does not exist
# (POL-045: not yet published, so not licensed for reuse); (3) upload with the
# bank's QC/utilities/upload_to_hf.py (incremental; --sync removes remote files
# that are not staged); (4) check exact parity and print the revision SHA for
# audio_sources.json at the port.
#
# Needs: a FormosanBank checkout at current main (sibling ../FormosanBank, or set
# FORMOSANBANK_ROOT) with its .venv; the `hf` command from huggingface_hub 1.x
# (pip install 'huggingface_hub<2': 2.x dropped `hf upload-large-folder`, which
# upload_to_hf.py runs); and a login with write access to FormosanBank
# (`hf auth login`).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"          # CodeAndDocs/
CORPUS="$(cd "$HERE/.." && pwd)"
FB="${FORMOSANBANK_ROOT:-}"
if [ -z "$FB" ]; then
  if [ -d "$CORPUS/../../QC" ]; then FB="$(cd "$CORPUS/../.." && pwd)"
  elif [ -d "$CORPUS/../FormosanBank/QC" ]; then FB="$(cd "$CORPUS/../FormosanBank" && pwd)"
  else echo "upload_audio_to_hf.sh: cannot find a FormosanBank checkout; set FORMOSANBANK_ROOT" >&2; exit 2; fi
fi
PY="${PYTHON:-$FB/.venv/bin/python3}"
DRY=""; SYNC=""
for a in "$@"; do
  case "$a" in
    --dry-run) DRY="--dry-run" ;;
    --sync) SYNC="--sync" ;;
    *) echo "unknown option $a (use --dry-run and/or --sync)" >&2; exit 2 ;;
  esac
done
echo "FormosanBank tools: $FB at $(git -C "$FB" rev-parse --short HEAD) ($(git -C "$FB" rev-parse --abbrev-ref HEAD)); use a checkout at current main"
command -v hf >/dev/null || { echo "The 'hf' command is missing: pip install 'huggingface_hub<2' (in its own venv, not FormosanBank's)" >&2; exit 2; }
# upload_to_hf.py runs `hf upload-large-folder`, which huggingface_hub 2.x removed (1.x has it, deprecated).
hf upload-large-folder --help >/dev/null 2>&1 || { echo "This hf ($(hf version 2>&1 | head -1)) has no 'upload-large-folder', which QC/utilities/upload_to_hf.py needs: pip install 'huggingface_hub<2'" >&2; exit 2; }
hf auth whoami >/dev/null 2>&1 || { echo "Not logged in to Hugging Face: run 'hf auth login' with a token that can write to FormosanBank" >&2; exit 2; }

"$PY" "$HERE/hf_audio.py" stage
"$PY" "$HERE/hf_audio.py" create $DRY
if [ -n "$DRY" ] && ! "$PY" -c "from huggingface_hub import HfApi; import yaml,sys; r=yaml.safe_load(open('$CORPUS/.hf_dataset.yaml'))['repo']; sys.exit(0 if HfApi().repo_exists(r, repo_type='dataset') else 1)"; then
  echo "(dry run: the dataset does not exist yet, so upload_to_hf.py cannot be dry-run against it; nothing was changed)"
  exit 0
fi
"$PY" "$FB/QC/utilities/upload_to_hf.py" --path "$CORPUS" --audio-dir Audio_hf $SYNC $DRY
[ -n "$DRY" ] && { echo "(dry run: no upload, so no parity check)"; exit 0; }
"$PY" "$HERE/hf_audio.py" check

#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FB="${FORMOSANBANK_ROOT:-$(cd "$ROOT/../.." && pwd)}"
"${PYTHON:-python3}" - "$ROOT" "$FB" "$@" <<'AUDIO_PY'
import argparse
import sys
from pathlib import Path

parser = argparse.ArgumentParser(description="Download the reviewed published audio revision.")
parser.add_argument("root", type=Path)
parser.add_argument("fb", type=Path)
parser.add_argument("--dry-run", action="store_true")
args = parser.parse_args()
root, fb = args.root, args.fb
sys.path.insert(0, str(fb))
sys.path.insert(0, str(root / "CodeAndDocs"))
from verify_sources import load_manifest, validate_manifest, validate_pin, verify_live, verify_local
from make_xml import load_metadata

source = load_manifest()
validate_manifest(source, load_metadata())
validate_pin(source, fb / "audio_sources.json")
verify_live(source)
from huggingface_hub import snapshot_download
from QC.utilities.download_audio import allow_patterns
from QC.validation.validate_hf_audio import (
    load_contract, selected_datasets, validate_local, validate_online,
)

manifest, extras, _ = load_contract(fb / "audio_sources.json")
datasets = selected_datasets(manifest, "TangRecordingsOfTaroko")
for dataset in datasets:
    dataset["destination"] = str(root / "Audio")
    dataset["xml_root"] = str(root / "XML")
failures = validate_online(datasets, extras)
if failures:
    raise SystemExit("\n".join(failures))
if args.dry_run:
    print("Published audio inventory matches; no files downloaded.")
    raise SystemExit(0)
for dataset in datasets:
    snapshot_download(
        dataset["repo_id"], repo_type="dataset", revision=dataset["revision"],
        local_dir=dataset["destination"], allow_patterns=allow_patterns(), token=False,
    )
failures = validate_local(datasets, extras)
if failures:
    raise SystemExit("\n".join(failures))
verify_local(source, root / "Audio" / "Truku")
print("Original audio downloaded; XML inventory and source bytes match.")
AUDIO_PY

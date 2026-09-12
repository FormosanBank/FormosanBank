#!/usr/bin/env python3
"""Decide whether the hf-audio-parity job needs to run for a set of changes.

The job triggers on any ``Corpora/**/*.xml`` change and then validates the
**whole** Hugging Face organisation — it takes no corpus argument. So a pull
request touching a corpus with no audio at all gated its merge on the state of
an external service it cannot affect, and did so anonymously against 21
datasets with no retry, which is how WakelinTexts (0 AUDIO elements, no
download script, absent from the manifest) came to be blocked by an HF 429.

Only a minority of the bank's corpora have public audio, and
``audio_sources.json`` already says which: each dataset entry names its
``corpus``. Reading the manifest rather than keeping a list in the workflow
means a new audio corpus starts being checked the moment it is manifested.

**The default is to run.** A change to the audio contract itself — the
manifest, the extras, the permissions, the validator, this module, or the
workflow — always runs the job, because those change what parity *means*.
Anything this module cannot classify runs it too: a skip has to be positively
justified, so a path we do not understand is never silently dropped.

    python QC/validation/hf_audio_scope.py --changed-files changed.txt
    -> prints "run=true" or "run=false" plus a one-line reason

Exit status is 0 whether or not the job is needed; the caller reads ``run=``.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

#: Files that define the audio contract. A change to any of them changes what
#: "parity" means, so the job runs regardless of which corpora were touched.
CONTRACT_PATHS = frozenset({
    "audio_sources.json",
    "audio_extras.json",
    "audio_permissions.json",
    "AUDIO-PERMISSIONS.md",
    "QC/validation/validate_hf_audio.py",
    "QC/validation/hf_audio_scope.py",
    ".github/workflows/hf-audio-parity.yaml",
})


def audio_corpora(manifest: dict) -> set[str]:
    """The corpus names that have public audio, per ``audio_sources.json``."""
    return {
        dataset["corpus"]
        for dataset in manifest.get("datasets", [])
        if isinstance(dataset, dict) and dataset.get("corpus")
    }


def _corpus_of(path: str) -> str | None:
    """``Corpora/<name>/...`` -> ``<name>``; anything else -> None."""
    parts = Path(path).parts
    if len(parts) >= 2 and parts[0] == "Corpora":
        return parts[1]
    return None


def needs_run(changed_files, corpora_with_audio: set[str]) -> tuple[bool, str]:
    """Return (run?, one-line reason).

    Runs when the audio contract changed, when a touched corpus has audio, or
    when a path cannot be classified. Skips only when every changed path is
    inside a corpus known to have no audio.
    """
    changed = [str(p).strip() for p in changed_files if str(p).strip()]
    if not changed:
        return True, "no changed files supplied; running to be safe"

    contract = sorted(set(changed) & CONTRACT_PATHS)
    if contract:
        return True, f"audio contract changed: {', '.join(contract)}"

    touched = {c for c in (_corpus_of(p) for p in changed) if c}

    if not touched:
        # Every trigger path is either Corpora/** or a contract file, so a diff
        # naming neither cannot explain why this run happened. That is the
        # shape a new trigger path takes when it is added to the workflow but
        # not to CONTRACT_PATHS, so run rather than guess.
        return True, (
            "nothing in the diff explains the trigger (no corpus, no contract "
            "file); running to be safe"
        )

    # Paths outside Corpora/ are ignored deliberately: they are not trigger
    # paths, so they rode along in the diff and cannot bear on audio parity.
    with_audio = sorted(touched & corpora_with_audio)
    if with_audio:
        return True, f"corpora with public audio touched: {', '.join(with_audio)}"

    return False, (
        "no corpus with public audio touched; only: "
        + ", ".join(sorted(touched))
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--changed-files",
        type=Path,
        required=True,
        help="file holding one changed path per line (git diff --name-only)",
    )
    parser.add_argument(
        "--manifest", type=Path, default=REPO_ROOT / "audio_sources.json"
    )
    args = parser.parse_args(argv)

    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        corpora = audio_corpora(manifest)
        changed = args.changed_files.read_text(encoding="utf-8").splitlines()
    except Exception as exc:  # unreadable input must never mean "skip"
        print(f"run=true\nreason=could not read inputs ({exc}); running to be safe")
        return 0

    run, reason = needs_run(changed, corpora)
    print(f"run={'true' if run else 'false'}")
    print(f"reason={reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

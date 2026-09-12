"""Tests for QC/validation/hf_audio_scope.py — does hf-audio-parity need to run?

The job triggers on any `Corpora/**/*.xml` change and then validates the
*whole* Hugging Face organisation, so a PR touching a corpus with no audio
gates its merge on the state of an external service it cannot affect. Only
9 of the bank's corpora have public audio; `audio_sources.json` is the
source of truth for which, so the decision reads the manifest rather than a
hand-kept list — a new audio corpus starts being checked the moment it is
manifested, with no workflow edit.

The default is to RUN. Anything this module cannot classify, and every
change to the audio contract itself, runs the job.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from QC.validation.hf_audio_scope import (  # noqa: E402
    CONTRACT_PATHS,
    audio_corpora,
    needs_run,
)

_MANIFEST = {
    "schema_version": 1,
    "datasets": [
        {"repo_id": "FormosanBank/a", "corpus": "ePark"},
        {"repo_id": "FormosanBank/b", "corpus": "NTUFormosanCorpus"},
        {"repo_id": "FormosanBank/c", "corpus": "ePark"},
    ],
}


def test_audio_corpora_are_read_from_the_manifest():
    assert audio_corpora(_MANIFEST) == {"ePark", "NTUFormosanCorpus"}


def test_a_corpus_with_no_audio_does_not_need_the_job():
    run, why = needs_run(
        ["Corpora/WakelinTexts/XML/Yami/Kalaku1.xml"], audio_corpora(_MANIFEST)
    )
    assert run is False
    assert "WakelinTexts" in why


def test_a_corpus_with_audio_needs_the_job():
    run, why = needs_run(
        ["Corpora/ePark/XML/Amis/x.xml"], audio_corpora(_MANIFEST)
    )
    assert run is True
    assert "ePark" in why


def test_a_mixed_change_needs_the_job():
    run, _why = needs_run(
        [
            "Corpora/WakelinTexts/XML/Yami/Kalaku1.xml",
            "Corpora/NTUFormosanCorpus/XML/Stories/Tsou/t.xml",
        ],
        audio_corpora(_MANIFEST),
    )
    assert run is True


@pytest.mark.parametrize("path", sorted(CONTRACT_PATHS))
def test_every_contract_path_forces_the_job(path):
    """The manifest, the permissions, the validator and the workflow itself
    all change what 'parity' means, so they always run it."""
    run, why = needs_run([path], audio_corpora(_MANIFEST))
    assert run is True, why


def test_a_path_outside_corpora_rides_along_and_is_ignored():
    """The workflow only triggers on `Corpora/**/*.xml` and the contract
    files, so anything else in the diff did not cause this run and cannot
    bear on audio parity. The real WakelinTexts PR also touches
    `Orthographies/`; that must not drag the job back in."""
    run, why = needs_run(
        [
            "Corpora/WakelinTexts/XML/Yami/Kalaku1.xml",
            "Orthographies/ConversionTables/Yami_Wakelin_113.tsv",
            "Orthographies/Wakelin/README.md",
        ],
        audio_corpora(_MANIFEST),
    )
    assert run is False, why


def test_a_diff_naming_no_corpus_and_no_contract_file_forces_the_job():
    """If nothing in the diff explains why the job triggered, run it. This is
    what catches a new trigger path added to the workflow but not to
    CONTRACT_PATHS."""
    run, why = needs_run(["some/new/thing.json"], audio_corpora(_MANIFEST))
    assert run is True
    assert "nothing" in why.lower() or "explain" in why.lower()


def test_contract_paths_cover_every_non_corpora_trigger_path():
    """The skip is only sound while CONTRACT_PATHS matches what the workflow
    actually triggers on. Tie them together so they cannot drift: add a
    trigger path without adding it here and this fails."""
    import yaml

    workflow = yaml.safe_load(
        (REPO_ROOT / ".github/workflows/hf-audio-parity.yaml").read_text()
    )
    # PyYAML parses the `on:` key as the boolean True.
    triggers = workflow.get("on", workflow.get(True))
    declared = set()
    for event in ("pull_request", "push"):
        declared.update(triggers.get(event, {}).get("paths", []))
    non_corpora = {p for p in declared if not p.startswith("Corpora/")}
    missing = non_corpora - set(CONTRACT_PATHS)
    assert missing == set(), (
        f"workflow triggers on {sorted(missing)} but CONTRACT_PATHS does not "
        "list them, so a PR touching only those would be skipped"
    )


def test_no_changed_files_forces_the_job():
    """An empty diff means the caller could not work out what changed."""
    run, _why = needs_run([], audio_corpora(_MANIFEST))
    assert run is True


def test_corpora_paths_outside_xml_still_count():
    """A corpus-level change that is not XML — a download script, say —
    still belongs to that corpus."""
    run, _why = needs_run(
        ["Corpora/ePark/download_audio_data.sh"], audio_corpora(_MANIFEST)
    )
    assert run is True
    run, _why = needs_run(
        ["Corpora/WakelinTexts/README.md"], audio_corpora(_MANIFEST)
    )
    assert run is False


def test_the_real_manifest_lists_the_expected_audio_corpora():
    """Guard against the manifest shape changing under us."""
    manifest = json.loads((REPO_ROOT / "audio_sources.json").read_text())
    corpora = audio_corpora(manifest)
    assert "ePark" in corpora
    assert "NTUFormosanCorpus" in corpora
    assert "WakelinTexts" not in corpora
    assert len(corpora) >= 5

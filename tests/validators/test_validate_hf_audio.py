from pathlib import Path
import json

import pytest

from QC.validation import validate_hf_audio as parity


def _write_xml(path: Path, filenames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    audio = "".join(f'<S><AUDIO file="{filename}"/></S>' for filename in filenames)
    path.write_text(f"<TEXT>{audio}</TEXT>", encoding="utf-8")


class FakeFileLister:
    def __init__(self, files: dict[str, list[str]]) -> None:
        self.files = files

    def __call__(self, repo_id: str, revision: str):
        assert revision == "abc123"
        return self.files[repo_id]


def test_online_parity_accepts_declared_extra(tmp_path, monkeypatch):
    monkeypatch.setattr(parity, "REPO_ROOT", tmp_path)
    _write_xml(tmp_path / "Corpora/Test/XML/Amis/text.xml", ["clip.wav"])
    dataset = {
        "repo_id": "FormosanBank/Test",
        "revision": "abc123",
        "destination": "Corpora/Test/Audio",
        "path_mode": "language_file",
        "xml_root": "Corpora/Test/XML",
        "expected_audio_files": 2,
    }
    file_lister = FakeFileLister(
        {"FormosanBank/Test": ["Amis/clip.wav", "Amis/public-extra.wav", "README.md"]}
    )

    failures = parity.validate_online(
        [dataset],
        {"FormosanBank/Test": {"Amis/public-extra.wav"}},
        file_lister,
    )

    assert failures == []


def test_online_parity_reports_missing_and_undeclared_files(tmp_path, monkeypatch):
    monkeypatch.setattr(parity, "REPO_ROOT", tmp_path)
    _write_xml(tmp_path / "Corpora/Test/XML/Amis/text.xml", ["expected.wav"])
    dataset = {
        "repo_id": "FormosanBank/Test",
        "revision": "abc123",
        "destination": "Corpora/Test/Audio",
        "path_mode": "language_file",
        "xml_root": "Corpora/Test/XML",
        "expected_audio_files": 1,
    }
    file_lister = FakeFileLister({"FormosanBank/Test": ["Amis/surprise.wav"]})

    failures = parity.validate_online([dataset], {}, file_lister)

    message = "\n".join(failures)
    assert "missing: 1" in message
    assert "Amis/expected.wav" in message
    assert "undeclared extras: 1" in message
    assert "Amis/surprise.wav" in message


def test_local_paiwan_contract_includes_sources_and_generated_clips(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(parity, "REPO_ROOT", tmp_path)
    xml_path = tmp_path / "Corpora/Paiwan/XML/Northern/session.xml"
    xml_path.parent.mkdir(parents=True)
    xml_path.write_text(
        '<TEXT audio="session.wav"><S><AUDIO file="session_S1.wav"/></S></TEXT>',
        encoding="utf-8",
    )
    dataset = {
        "path_mode": "ntu_paiwan_sources",
        "xml_root": "Corpora/Paiwan/XML",
    }

    assert parity.expected_local_paths(dataset) == {
        "Northern/session.wav",
        "Northern/session_S1.wav",
    }


def test_ilrdf_rukai_uses_manifested_batch_routes(tmp_path, monkeypatch):
    monkeypatch.setattr(parity, "REPO_ROOT", tmp_path)
    _write_xml(
        tmp_path / "Corpora/ILRDF/XML/Rukai/Rukai.xml",
        ["first.mp3", "second.mp3"],
    )
    dataset = {
        "path_mode": "ilrdf",
        "xml_root": "Corpora/ILRDF/XML",
        "rukai_batch_2_files": ["second.mp3"],
    }

    assert parity.expected_remote_paths(dataset) == {
        "Rukai/Rukai/batch_1/first.mp3",
        "Rukai/Rukai/batch_2/second.mp3",
    }


def test_contract_requires_pinned_commit_sha(tmp_path, monkeypatch):
    monkeypatch.setattr(parity, "REPO_ROOT", tmp_path)
    (tmp_path / "extras.json").write_text(
        json.dumps({"schema_version": 1, "repositories": {}}),
        encoding="utf-8",
    )
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "declared_extras": "extras.json",
                "datasets": [
                    {
                        "repo_id": "FormosanBank/Test",
                        "revision": "main",
                        "expected_audio_files": 1,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="40-character commit SHA"):
        parity.load_contract(manifest)

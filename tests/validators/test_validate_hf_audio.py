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


def _write_contract(
    root: Path,
    *,
    permission_status: str = "verified_public",
    evidence: list[dict] | None = None,
) -> Path:
    evidence_path = root / "Corpora/Test/README.md"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text("Permission granted.", encoding="utf-8")
    if evidence is None:
        evidence = [
            {
                "type": "repository",
                "path": "Corpora/Test/README.md",
            }
        ]
    (root / "extras.json").write_text(
        json.dumps({"schema_version": 1, "repositories": {}}),
        encoding="utf-8",
    )
    (root / "permissions.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "hf_organization": "FormosanBank",
                "public_non_audio_datasets": ["FormosanBank/formosan-mt"],
                "sources": [
                    {
                        "permission_id": "test-source",
                        "corpus": "Test",
                        "status": permission_status,
                        "license": (
                            "CC BY-NC"
                            if permission_status == "verified_public"
                            else None
                        ),
                        "basis": "Direct permission.",
                        "evidence": evidence,
                        "hf_repositories": [
                            {
                                "repo_id": "FormosanBank/Test",
                                "access": (
                                    "public"
                                    if permission_status == "verified_public"
                                    else "private"
                                ),
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    manifest = root / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "permissions": "permissions.json",
                "declared_extras": "extras.json",
                "datasets": [
                    {
                        "corpus": "Test",
                        "permission_id": "test-source",
                        "repo_id": "FormosanBank/Test",
                        "revision": "a" * 40,
                        "expected_audio_files": 1,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return manifest


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


def test_contract_accepts_source_specific_permission_evidence(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(parity, "REPO_ROOT", tmp_path)
    manifest_path = _write_contract(tmp_path)

    manifest, extras, permissions = parity.load_contract(manifest_path)

    assert manifest["datasets"][0]["permission_id"] == "test-source"
    assert extras == {}
    assert permissions["sources"][0]["status"] == "verified_public"


def test_contract_rejects_pending_permission_in_public_manifest(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(parity, "REPO_ROOT", tmp_path)
    manifest_path = _write_contract(
        tmp_path,
        permission_status="withheld_pending_permission",
    )

    with pytest.raises(ValueError, match="not verified for public distribution"):
        parity.load_contract(manifest_path)


def test_contract_requires_permission_evidence_inside_formosanbank(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(parity, "REPO_ROOT", tmp_path)
    manifest_path = _write_contract(
        tmp_path,
        evidence=[
            {
                "type": "web",
                "url": "https://example.com/license",
            }
        ],
    )

    with pytest.raises(ValueError, match="requires permission evidence in FormosanBank"):
        parity.load_contract(manifest_path)


class FakeInfo:
    def __init__(
        self,
        repo_id: str,
        *,
        private: bool = False,
        gated: bool | str = False,
    ) -> None:
        self.id = repo_id
        self.private = private
        self.gated = gated


class FakeApi:
    def __init__(
        self,
        *,
        extra_dataset: bool = False,
        model_audio: bool = False,
    ) -> None:
        self.extra_dataset = extra_dataset
        self.model_audio = model_audio

    def list_datasets(self, author: str, full: bool):
        assert author == "FormosanBank"
        assert full is True
        result = [
            FakeInfo("FormosanBank/Test"),
            FakeInfo("FormosanBank/formosan-mt"),
            FakeInfo("FormosanBank/Restricted", gated="manual"),
        ]
        if self.extra_dataset:
            result.append(FakeInfo("FormosanBank/Unexpected"))
        return result

    def list_models(self, author: str, full: bool):
        return [FakeInfo("FormosanBank/asr-model")]

    def list_spaces(self, author: str, full: bool):
        return [FakeInfo("FormosanBank/asr-space")]

    def list_repo_files(
        self,
        repo_id: str,
        *,
        repo_type: str,
        token: bool,
    ):
        assert token is False
        if repo_id == "FormosanBank/asr-model" and self.model_audio:
            return ["examples/clip.wav"]
        return ["README.md"]


def test_hf_inventory_accepts_exact_public_allowlist():
    manifest = {"datasets": [{"repo_id": "FormosanBank/Test"}]}
    permissions = {
        "hf_organization": "FormosanBank",
        "public_non_audio_datasets": ["FormosanBank/formosan-mt"],
    }

    failures = parity.validate_hf_inventory(
        manifest,
        permissions,
        api=FakeApi(),
    )

    assert failures == []


def test_hf_inventory_rejects_unapproved_dataset_and_model_audio():
    manifest = {"datasets": [{"repo_id": "FormosanBank/Test"}]}
    permissions = {
        "hf_organization": "FormosanBank",
        "public_non_audio_datasets": ["FormosanBank/formosan-mt"],
    }

    failures = parity.validate_hf_inventory(
        manifest,
        permissions,
        api=FakeApi(extra_dataset=True, model_audio=True),
    )

    message = "\n".join(failures)
    assert "FormosanBank/Unexpected" in message
    assert "examples/clip.wav" in message

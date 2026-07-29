from pathlib import Path
import subprocess

import pytest

from QC.utilities import download_audio


def test_allow_patterns_cover_root_and_nested_audio():
    patterns = download_audio.allow_patterns()

    assert "*.wav" in patterns
    assert "**/*.wav" in patterns
    assert "*.mp3" in patterns
    assert "**/*.mp3" in patterns


def test_post_download_expands_python_and_repository_paths(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(download_audio, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        download_audio.subprocess,
        "run",
        lambda command, cwd, check: calls.append((command, cwd, check)),
    )

    download_audio.run_post_download(
        [["{python}", "Corpora/Test/extract.py", "--audio_root", "Audio"]]
    )

    command, cwd, check = calls[0]
    assert command[0] == download_audio.sys.executable
    assert command[1] == str(tmp_path / "Corpora/Test/extract.py")
    assert command[2:] == ["--audio_root", "Audio"]
    assert cwd == tmp_path
    assert check is True


def test_destination_counts_deduplicates_shared_destinations(tmp_path, monkeypatch):
    monkeypatch.setattr(download_audio, "REPO_ROOT", tmp_path)
    audio = tmp_path / "Corpora/Test/Audio"
    audio.mkdir(parents=True)
    (audio / "source.wav").write_bytes(b"audio")

    counts = download_audio.destination_counts(
        [
            {"destination": "Corpora/Test/Audio"},
            {"destination": "Corpora/Test/Audio"},
        ]
    )

    assert counts == {"Corpora/Test/Audio": 1}


def test_download_uses_pinned_lfs_checkout(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(download_audio, "REPO_ROOT", tmp_path)

    def fake_run(directory, *arguments):
        calls.append(arguments)
        if arguments[:2] == ("lfs", "pull"):
            audio = directory / "Amis" / "clip.wav"
            audio.parent.mkdir(parents=True)
            audio.write_bytes(b"audio")

    monkeypatch.setattr(download_audio, "run_git", fake_run)

    download_audio.download_datasets(
        [
            {
                "repo_id": "FormosanBank/Test",
                "revision": "abc123",
                "destination": "Corpora/Test/Audio",
                "expected_audio_files": 1,
            }
        ],
        workers=17,
    )

    assert (
        "remote",
        "add",
        "origin",
        "https://huggingface.co/datasets/FormosanBank/Test",
    ) in calls
    assert ("config", "lfs.concurrenttransfers", "17") in calls
    assert ("fetch", "--quiet", "--depth=1", "origin", "abc123") in calls
    assert any(call[:2] == ("lfs", "pull") for call in calls)
    assert (tmp_path / "Corpora/Test/Audio/Amis/clip.wav").read_bytes() == b"audio"


def test_run_git_is_noninteractive_and_disables_credentials(tmp_path, monkeypatch):
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured.update(kwargs)

    monkeypatch.setattr(download_audio.subprocess, "run", fake_run)

    download_audio.run_git(tmp_path, "fetch", "origin", "abc123")

    assert captured["command"][:4] == ["git", "-c", "credential.helper=", "fetch"]
    assert captured["env"]["GIT_LFS_SKIP_SMUDGE"] == "1"
    assert captured["env"]["GIT_TERMINAL_PROMPT"] == "0"
    assert captured["check"] is True


def test_failed_lfs_download_preserves_resumable_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(download_audio, "REPO_ROOT", tmp_path)

    def failing_run(directory, *arguments):
        if arguments[:2] == ("init", "--quiet"):
            (directory / ".git").mkdir()
        if arguments[:2] == ("lfs", "pull"):
            raise subprocess.CalledProcessError(1, arguments)

    monkeypatch.setattr(download_audio, "run_git", failing_run)
    dataset = {
        "repo_id": "FormosanBank/Test",
        "revision": "a" * 40,
        "destination": "Corpora/Test/Audio",
    }

    with pytest.raises(subprocess.CalledProcessError):
        download_audio.download_datasets([dataset])

    cache = tmp_path / ".audio-download-cache/FormosanBank__Test-aaaaaaaaaaaa"
    assert (cache / ".git").is_dir()


def test_move_audio_rejects_unresolved_lfs_pointer(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "clip.wav").write_text(
        "version https://git-lfs.github.com/spec/v1\n"
        "oid sha256:abc\n"
        "size 123\n",
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="audio pointers unresolved"):
        download_audio.move_audio_files(source, tmp_path / "destination", 1)


def test_main_reports_permission_pending_corpus_as_withheld(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(
        download_audio,
        "load_contract",
        lambda path: (
            {"datasets": []},
            {},
            {
                "sources": [
                    {
                        "corpus": "Restricted",
                        "status": "withheld_pending_permission",
                    }
                ]
            },
        ),
    )

    result = download_audio.main(
        [
            "--manifest",
            str(tmp_path / "manifest.json"),
            "--corpus",
            "Restricted",
            "--dry-run",
        ]
    )

    assert result == 3
    assert "source-specific redistribution permission is not verified" in (
        capsys.readouterr().err
    )

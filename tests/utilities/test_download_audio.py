from pathlib import Path

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


def test_download_is_pinned_and_explicitly_anonymous(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(download_audio, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        download_audio,
        "snapshot_download",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    download_audio.download_datasets(
        [
            {
                "repo_id": "FormosanBank/Test",
                "revision": "abc123",
                "destination": "Corpora/Test/Audio",
            }
        ]
    )

    args, kwargs = calls[0]
    assert args == ("FormosanBank/Test",)
    assert kwargs["repo_type"] == "dataset"
    assert kwargs["revision"] == "abc123"
    assert kwargs["token"] is False

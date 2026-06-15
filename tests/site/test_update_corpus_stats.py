import os

import pytest

import update_corpus_stats as ucs


def test_resolve_prefers_cli_flag(tmp_path):
    d = tmp_path / "cli_stats"
    d.mkdir()
    out = ucs.resolve_stats_dir(cli_stats_dir=str(d), env={}, repo_root=tmp_path)
    assert out == d.resolve()


def test_resolve_uses_env_when_no_flag(tmp_path):
    d = tmp_path / "env_stats"
    d.mkdir()
    out = ucs.resolve_stats_dir(
        cli_stats_dir=None,
        env={"FORMOSANBANK_STATS_DIR": str(d)},
        repo_root=tmp_path,
    )
    assert out == d.resolve()


def test_resolve_defaults_to_sibling_formosanbank(tmp_path):
    # repo_root is the gitbook checkout; default is ../FormosanBank/statistics
    gitbook_root = tmp_path / "FormosanBankGitbook"
    gitbook_root.mkdir()
    sibling = tmp_path / "FormosanBank" / "statistics"
    sibling.mkdir(parents=True)
    out = ucs.resolve_stats_dir(cli_stats_dir=None, env={}, repo_root=gitbook_root)
    assert out == sibling.resolve()


def test_resolve_hard_errors_when_missing(tmp_path):
    with pytest.raises(SystemExit) as exc:
        ucs.resolve_stats_dir(cli_stats_dir=None, env={}, repo_root=tmp_path)
    assert "stats dir not found" in str(exc.value)

"""sync_hf_audio.py: the XML → clip contract, the Hub listing, and the dry run.

The script had no tests. Nothing here touches the network: the Hub is a fake
`HfApi`, and the slicing/upload half is never reached because every case
stops at the dry-run report or at the write-access check.
"""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "QC" / "utilities" / "sync_hf_audio.py"


def _load():
    spec = importlib.util.spec_from_file_location("sync_hf_audio", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TEXT = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<TEXT id="{tid}" citation="c" BibTeX_citation="b" copyright="CC BY-NC 4.0" '
    'xml:lang="ami" dialect="Coastal" audio="segmented">\n{body}</TEXT>\n'
)
URL = "https://example.org/story.mp3"


def _s(sid: str, audio: str) -> str:
    return (f'<S id="{sid}"><FORM kindOf="original">x</FORM>'
            f'<FORM kindOf="standard">x</FORM>{audio}</S>\n')


def _xml_dir(tmp_path: Path) -> Path:
    xml = tmp_path / "XML"
    (xml / "Amis").mkdir(parents=True)
    (xml / "Amis" / "a.xml").write_text(TEXT.format(tid="a", body=(
        _s("S1", f'<AUDIO file="a_S1.mp3" url="{URL}" start="0" end="1.5"/>')
        + _s("S2", f'<AUDIO file="a_S2.mp3" url="{URL}" start="1.5" end="3"/>')
        + _s("S3", f'<AUDIO file="a_S3.mp3" start="3" end="4"/>')         # no url: skipped
        + _s("S4", f'<AUDIO file="a_S1.mp3" url="{URL}" start="9" end="10"/>')  # duplicate name: first wins
    )), encoding="utf-8")
    (xml / "Puyuma").mkdir()
    (xml / "Puyuma" / "p.xml").write_text(TEXT.format(tid="p", body=
        _s("S1", f'<AUDIO file="p_S1.mp3" url="{URL}" start="0" end="2"/>')), encoding="utf-8")
    return xml


def test_referenced_clips_keys_by_language_dir_and_keeps_the_first_span(tmp_path):
    m = _load()
    clips = m.referenced_clips(_xml_dir(tmp_path))
    assert clips == {
        "Amis/a_S1.mp3": (URL, 0.0, 1.5),
        "Amis/a_S2.mp3": (URL, 1.5, 3.0),
        "Puyuma/p_S1.mp3": (URL, 0.0, 2.0),
    }


class _FakeApi:
    def __init__(self, files, *, writer=True):
        self._files = files
        self._writer = writer

    def list_repo_files(self, repo_id, repo_type):
        assert repo_type == "dataset"
        return list(self._files)

    def whoami(self):
        if not self._writer:
            raise RuntimeError("401")
        return {"name": "tester"}


def test_hub_files_keeps_only_mp3s_case_insensitively():
    m = _load()
    api = _FakeApi(["Amis/a_S1.mp3", "README.md", "Puyuma/P_S9.MP3", ".gitattributes"])
    assert m.hub_files(api, "FormosanBank/X") == {"Amis/a_S1.mp3", "Puyuma/P_S9.MP3"}


def _fake_hub(monkeypatch, files, *, writer=True):
    module = types.ModuleType("huggingface_hub")
    module.HfApi = lambda token=None: _FakeApi(files, writer=writer)
    monkeypatch.setitem(sys.modules, "huggingface_hub", module)


def test_dry_run_reports_missing_and_extra_clips_and_changes_nothing(tmp_path, monkeypatch, capsys):
    m = _load()
    _fake_hub(monkeypatch, ["Amis/a_S1.mp3", "Amis/stale_S7.mp3"])
    monkeypatch.setattr(sys, "argv", ["sync_hf_audio.py", "--repo", "FormosanBank/X",
                                      "--xml", str(_xml_dir(tmp_path))])
    assert m.main() == 0
    out = capsys.readouterr().out
    assert "referenced by the XML : 3" in out
    assert "present on the Hub    : 2" in out
    assert "to slice and upload   : 2" in out and "+ Amis/a_S2.mp3  [1.5-3.0]" in out
    assert "to delete             : 1" in out and "- Amis/stale_S7.mp3" in out
    assert "dry run — nothing was changed" in out


def test_parity_says_so_and_exits_zero(tmp_path, monkeypatch, capsys):
    m = _load()
    _fake_hub(monkeypatch, ["Amis/a_S1.mp3", "Amis/a_S2.mp3", "Puyuma/p_S1.mp3"])
    monkeypatch.setattr(sys, "argv", ["sync_hf_audio.py", "--repo", "FormosanBank/X",
                                      "--xml", str(_xml_dir(tmp_path)), "--apply"])
    assert m.main() == 0
    assert "already in parity; nothing to do" in capsys.readouterr().out


def test_apply_without_write_access_stops_before_touching_anything(tmp_path, monkeypatch):
    m = _load()
    _fake_hub(monkeypatch, ["Amis/a_S1.mp3"], writer=False)
    monkeypatch.setattr(sys, "argv", ["sync_hf_audio.py", "--repo", "FormosanBank/X",
                                      "--xml", str(_xml_dir(tmp_path)), "--apply"])
    with pytest.raises(SystemExit) as exc:
        m.main()
    assert "--apply needs write access" in str(exc.value)


def test_missing_xml_dir_is_an_error(tmp_path, monkeypatch):
    m = _load()
    monkeypatch.setattr(sys, "argv", ["sync_hf_audio.py", "--repo", "FormosanBank/X",
                                      "--xml", str(tmp_path / "nope")])
    with pytest.raises(SystemExit, match="no such XML directory"):
        m.main()

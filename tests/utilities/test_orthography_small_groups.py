"""A language/dialect group too small to profile is skipped, not crashed on.

orthography_extract.py drops every character seen fewer than 5 times as
noise. A group with very little text -- the Poinsot Amis-Chinese
dictionary's Coastal file holds two words, "alomdas podok" -- is left with
no characters at all. Plotting that crashed the extractor, and an
orthographic_info written for it made validate_orthography.py divide by
zero. Both now skip the group with a warning; the rest of the corpus is
still profiled.
"""
import pickle
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EXTRACT = REPO_ROOT / "QC" / "orthography" / "orthography_extract.py"
sys.path.insert(0, str(REPO_ROOT / "QC" / "validation"))

import validate_orthography  # noqa: E402

_TEXT = ('<?xml version="1.0" encoding="utf-8"?>\n'
         '<TEXT id="t" xml:lang="ami" dialect="{dialect}">{sentences}</TEXT>\n')


def _sentence(n: int, text: str) -> str:
    return f'<S id="s{n}"><FORM kindOf="standard">{text}</FORM></S>'


def _corpus(tmp_path: Path) -> Path:
    amis = tmp_path / "corpora" / "C" / "XML" / "Amis"
    amis.mkdir(parents=True)
    (amis / "coastal.xml").write_text(
        _TEXT.format(dialect="Coastal", sentences=_sentence(1, "alomdas podok")), encoding="utf-8")
    big = "".join(_sentence(i, "maolah kako to kaka ako a tamdaw") for i in range(10))
    (amis / "xiuguluan.xml").write_text(_TEXT.format(dialect="Xiuguluan", sentences=big), encoding="utf-8")
    return tmp_path / "corpora"


def test_extract_skips_a_group_with_no_profilable_characters(tmp_path):
    out = tmp_path / "out"
    proc = subprocess.run(
        [sys.executable, str(EXTRACT), "--corpora_path", str(_corpus(tmp_path)), "--corpus", "C",
         "--language", "Amis", "--kindOf", "standard", "--by_dialect", "true", "--output_dir", str(out)],
        capture_output=True, text=True, cwd=str(REPO_ROOT), check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "Amis / Coastal: too little text to profile (2 words" in proc.stdout, proc.stdout
    assert not (out / "Amis" / "Coastal" / "orthographic_info").exists()
    assert (out / "Amis" / "Xiuguluan" / "orthographic_info").is_file(), "the rest is still profiled"


def test_validate_orthography_skips_an_empty_profile(tmp_path, capsys):
    """An orthographic_info written before the extractor skipped such groups."""
    corpus_dir, ref_dir = tmp_path / "corpus", tmp_path / "ref"
    corpus_dir.mkdir()
    ref_dir.mkdir()
    with open(corpus_dir / "orthographic_info", "wb") as fh:
        pickle.dump({"unique_characters": [], "character_frequency": {}, "2-grams": {}}, fh)
    with open(ref_dir / "orthographic_info", "wb") as fh:
        pickle.dump({"unique_characters": ["a"], "character_frequency": {"a": 9}, "2-grams": {}}, fh)
    assert validate_orthography.compare_orthography(str(corpus_dir), str(ref_dir), "Amis / Coastal") is None
    assert "SUMMARY orthography | Amis / Coastal | corpus=too-small" in capsys.readouterr().out

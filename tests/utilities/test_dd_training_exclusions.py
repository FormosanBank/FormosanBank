"""training_exclusions.tsv: labelled files the dialect detector must not train on."""
import fnmatch
from pathlib import Path

import pytest

from QC.utilities.dialect_detector.data import (
    iter_labeled_documents, load_training_exclusions,
)

REPO = Path(__file__).resolve().parents[2]
CORP = REPO / "Corpora"
NTU = CORP / "NTU_Paiwan_ASR" / "XML"


def _write(root: Path, rel: str, dialect: str):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f'<TEXT xml:lang="pwn" dialect="{dialect}">'
                 f'<S id="1"><FORM kindOf="standard">lala</FORM></S></TEXT>',
                 encoding="utf-8")


def test_matching_files_are_left_out_with_a_warning(tmp_path):
    _write(tmp_path, "C/XML/read_1.xml", "Eastern")
    _write(tmp_path, "C/XML/talk_1.xml", "Eastern")
    with pytest.warns(RuntimeWarning, match="1 labelled file"):
        docs, _ = iter_labeled_documents(tmp_path, "pwn", exclusions=["C/XML/read_*.xml"])
    assert [d.path.name for d in docs] == ["talk_1.xml"]


def test_the_shipped_list_parses_and_every_row_has_a_reason():
    pats = load_training_exclusions()
    assert pats, "training_exclusions.tsv is missing or empty"
    tsv = Path(load_training_exclusions.__defaults__[0])
    rows = tsv.read_text(encoding="utf-8").splitlines()[1:]
    assert all(len(r.split("\t")) == 2 and r.split("\t")[1].strip() for r in rows)


@pytest.mark.skipif(not NTU.exists(), reason="NTU_Paiwan_ASR not present")
def test_patterns_match_exactly_the_ntu_read_speech():
    # The builder writes an _untranscribed.xml stub beside every spontaneous
    # recording and none beside read speech, so "no stub" defines read speech.
    transcribed = [p for p in NTU.rglob("*.xml") if not p.name.endswith("_untranscribed.xml")]
    read = {p.relative_to(CORP).as_posix() for p in transcribed
            if not p.with_name(p.stem + "_untranscribed.xml").exists()}
    pats = [p for p in load_training_exclusions() if p.startswith("NTU_Paiwan_ASR/")]
    matched = {p.relative_to(CORP).as_posix() for p in transcribed
               if any(fnmatch.fnmatchcase(p.relative_to(CORP).as_posix(), pat) for pat in pats)}
    assert read, "no read speech found; has the corpus layout changed?"
    assert matched == read, (sorted(matched - read)[:10], sorted(read - matched)[:10])
    for pat in pats:  # no dead rows
        assert any(fnmatch.fnmatchcase(r, pat) for r in read), pat

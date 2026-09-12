"""The rights vocabulary registry and its single loader (POL-042).

The registry is the only place the allowed licence strings live; every
consumer imports load_rights_vocabulary rather than restating them
(POL-039). corpus_license is the one way to ask what licence a corpus
carries, and it refuses to answer when a corpus is inconsistent, because
POL-042 assumes one licence per corpus.
"""
import pytest

from QC.validation._rights import (
    VOCABULARY_PATH,
    corpus_license,
    load_rights_vocabulary,
)

EXPECTED = {
    "CC BY 4.0": "cc-by-4.0",
    "CC BY-SA 4.0": "cc-by-sa-4.0",
    "CC BY-NC 4.0": "cc-by-nc-4.0",
    "CC BY-NC-SA 4.0": "cc-by-nc-sa-4.0",
    "CC BY-NC-ND 4.0": "cc-by-nc-nd-4.0",
    "public domain": "",
}


def test_registry_file_exists_at_repo_root():
    assert VOCABULARY_PATH.name == "rights_vocabulary.csv"
    assert VOCABULARY_PATH.is_file()


def test_loader_returns_the_canonical_vocabulary():
    assert load_rights_vocabulary() == EXPECTED


def test_loader_accepts_an_explicit_path(tmp_path):
    csv_path = tmp_path / "vocab.csv"
    csv_path.write_text(
        "value,hf_license,url,notes\nCC BY 4.0,cc-by-4.0,https://x,\n",
        encoding="utf-8",
    )
    assert load_rights_vocabulary(csv_path) == {"CC BY 4.0": "cc-by-4.0"}


def test_loader_rejects_a_duplicate_value(tmp_path):
    csv_path = tmp_path / "vocab.csv"
    csv_path.write_text(
        "value,hf_license,url,notes\n"
        "CC BY 4.0,cc-by-4.0,,\n"
        "CC BY 4.0,cc-by-4.0,,\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate"):
        load_rights_vocabulary(csv_path)


def _corpus(tmp_path, *copyrights):
    corpus = tmp_path / "MyCorpus" / "XML"
    corpus.mkdir(parents=True)
    for i, value in enumerate(copyrights):
        (corpus / f"f{i}.xml").write_text(
            f'<TEXT id="t{i}" copyright="{value}" xml:lang="ami"></TEXT>',
            encoding="utf-8",
        )
    return tmp_path / "MyCorpus"


def test_corpus_license_reads_the_single_value(tmp_path):
    assert corpus_license(_corpus(tmp_path, "CC BY-NC 4.0", "CC BY-NC 4.0")) == "CC BY-NC 4.0"


def test_corpus_license_is_none_when_there_is_no_xml(tmp_path):
    empty = tmp_path / "Empty"
    empty.mkdir()
    assert corpus_license(empty) is None


def test_corpus_license_refuses_a_mixed_corpus(tmp_path):
    corpus = _corpus(tmp_path, "CC BY-NC 4.0", "CC BY 4.0")
    with pytest.raises(ValueError, match="more than one"):
        corpus_license(corpus)

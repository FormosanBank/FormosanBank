"""Shared tools that read corpus XML must skip CodeAndDocs/.

`CodeAndDocs/` holds reproduction infrastructure -- build scripts, raw
scrapes, and POL-035 pre-correction snapshots -- never published data. A
snapshot is a byte-for-byte ancestor of the corpus beside it, so a tool
that walks a corpus root without excluding it reads the same text twice.

`corpus_counts` has excluded it since the 2026-08-11 counting ruling and
`validation/_discovery` since the finding-based validators landed.
`orthography_extract` did not, and the consequence was live: pointing it
at a corpus root doubled the text and, because the duplicate pushed
characters over the `>= 5` frequency threshold, changed the *shape* of
the resulting profile -- it gained `base_characters` and `diacritics`
keys the correct run does not produce.
"""
import xml.etree.ElementTree as ET

import pytest

from QC.corpus_counts import is_published_xml, is_reproduction_path
from QC.orthography.orthography_extract import generate_corpus

TEXT = """<?xml version='1.0' encoding='UTF-8'?>
<TEXT id="t" citation="c" BibTeX_citation="b" copyright="public domain"
      dialect="Favorlang" xml:lang="bzg">
  <S id="S1"><FORM kindOf="original">bahosa</FORM></S>
</TEXT>
"""


@pytest.fixture()
def corpus(tmp_path):
    """A corpus root holding published XML and a POL-035 snapshot of it."""
    published = tmp_path / "XML" / "Babuza-Favorlang"
    snapshot = tmp_path / "CodeAndDocs" / "pre_correction_snapshot" / "Babuza-Favorlang"
    for d in (published, snapshot):
        d.mkdir(parents=True)
        (d / "corpus.xml").write_text(TEXT, encoding="utf-8")
    return tmp_path


def test_corpus_root_and_xml_root_agree(corpus):
    """The regression: walking the root must not read the snapshot too."""
    from_root = generate_corpus("Babuza-Favorlang", str(corpus), "original", True)
    from_xml = generate_corpus(
        "Babuza-Favorlang", str(corpus / "XML"), "original", True
    )
    assert from_root == from_xml


def test_snapshot_text_is_not_counted_twice(corpus):
    """Stated as the thing a reader cares about: one FORM, counted once."""
    text = generate_corpus(
        "Babuza-Favorlang", str(corpus), "original", True
    )["Favorlang"]
    assert text.split().count("bahosa") == 1


def test_the_snapshot_really_is_a_duplicate(corpus):
    """Guards the fixture itself: if these stopped being identical the
    two tests above would pass for the wrong reason."""
    a, b = sorted(corpus.rglob("corpus.xml"))
    assert a.read_bytes() == b.read_bytes()
    assert ET.parse(a).getroot().findtext("S/FORM") == "bahosa"


def test_predicate_matches_the_counting_rule(corpus):
    published = corpus / "XML" / "Babuza-Favorlang" / "corpus.xml"
    snapshot = (
        corpus / "CodeAndDocs" / "pre_correction_snapshot"
        / "Babuza-Favorlang" / "corpus.xml"
    )
    assert not is_reproduction_path(published)
    assert is_reproduction_path(snapshot)
    # The narrow predicate agrees with is_published_xml wherever that one
    # applies; it just does not also demand an `XML` path segment.
    assert is_published_xml(published)
    assert not is_published_xml(snapshot)


def test_predicate_does_not_require_an_XML_segment(tmp_path):
    """Builds that stage into `Final_XML/` must keep working -- that is
    why this is not simply `is_published_xml`."""
    staged = tmp_path / "Final_XML" / "corpus.xml"
    assert not is_reproduction_path(staged)
    assert not is_published_xml(staged)  # no `XML` segment, by design


def test_predicate_accepts_strings_and_paths(corpus):
    snapshot = corpus / "CodeAndDocs" / "x.xml"
    assert is_reproduction_path(snapshot)
    assert is_reproduction_path(str(snapshot).replace("\\", "/"))

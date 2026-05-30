"""Basic tests for QC/cleaning/clean_xml.py.

This is the BASIC round per the design doc. Corpus-mined positives and
negatives (mining published Corpora/<X>/ for real-world cruft patterns)
are a deferred follow-up round with its own design pass.

clean_xml mutates XML in place. All tests work on a tmp_path copy of
the fixture; never mutate the fixture file itself.
"""
import subprocess
import sys
from pathlib import Path

from lxml import etree


CLEAN_XML = Path(__file__).resolve().parents[2] / "QC" / "cleaning" / "clean_xml.py"


def _run_clean(corpora_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CLEAN_XML), "--corpora_path", str(corpora_path)],
        capture_output=True,
        text=True,
    )


def _form_texts(xml_path: Path) -> list[str]:
    """Return the text content of every FORM element in the file."""
    tree = etree.parse(str(xml_path))
    return [el.text or "" for el in tree.findall(".//FORM")]


def test_already_clean_xml_is_left_intact(tmp_path, fixtures_dir, copy_fixture):
    """valid_minimal.xml is already clean; cleaner must not mutate it (byte-exact)."""
    work = copy_fixture(fixtures_dir / "valid_minimal.xml", tmp_path)
    before = work.read_bytes()
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    assert work.read_bytes() == before, (
        "cleaner modified an already-clean file (byte-level diff)"
    )


def test_html_entities_round_trip_without_double_encoding(tmp_path, fixtures_dir, copy_fixture):
    """Standard XML character references in FORM text round-trip without
    becoming double-encoded after a clean pass.

    Note: this does NOT exercise clean_xml.py's html.unescape branch.
    lxml decodes &amp; -> & during parse, so the unescape branch's
    condition (html.unescape(text) != text) is False for normal XML
    input. Exercising that branch requires double-encoded input on
    disk (literal `&amp;` inside FORM text), which is a separate
    scenario deferred to the corpus-mined round.
    """
    work = copy_fixture(fixtures_dir / "xml_with_html_entities.xml", tmp_path)
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    # Parse the output XML so we inspect FORM text values, not raw serialized
    # bytes. lxml decodes XML entities when parsing, so &amp;amp; in a FORM
    # text would surface as the literal string "&amp;" here. Checking via the
    # parser rather than raw file text avoids false positives from comment text
    # in the fixture (the comment itself contains "&amp;amp;" as illustration).
    forms = _form_texts(work)
    for text in forms:
        assert "&amp;" not in text, (
            f"found double-encoded entity '&amp;' in FORM text after cleaning: {text!r}"
        )


def test_whitespace_is_normalized(tmp_path, fixtures_dir, copy_fixture):
    work = copy_fixture(fixtures_dir / "xml_with_whitespace_problems.xml", tmp_path)
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    # Parse the output XML so we inspect FORM text values, not raw serialized
    # bytes (XML comments and attribute indentation also contain spaces and
    # would produce false positives if we checked the raw file text).
    texts = _form_texts(work)
    for text in texts:
        assert "  " not in text, f"expected all repeated spaces collapsed: {text!r}"
        assert not text.startswith(" "), f"expected leading whitespace stripped: {text!r}"
        assert not text.endswith(" "), f"expected trailing whitespace stripped: {text!r}"


def test_xml_declaration_survives_clean_pass(tmp_path, fixtures_dir, copy_fixture):
    """The XML declaration must survive a clean pass that mutates the file.

    Regression pin for the bug where `tree.write()` defaulted to
    `xml_declaration=False`, silently stripping `<?xml version="1.0"
    encoding="utf-8"?>` from any file the cleaner touched. The fix at
    QC/cleaning/clean_xml.py passed `xml_declaration=True` explicitly;
    this test pins the fix so a future change can't regress it. Uses a
    fixture that triggers `modified=True` so the cleaner actually
    rewrites the file (an already-clean file is untouched and would
    pass for the wrong reason).
    """
    work = copy_fixture(fixtures_dir / "xml_with_whitespace_problems.xml", tmp_path)
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    first_line = work.read_text(encoding="utf-8").splitlines()[0]
    assert first_line.startswith("<?xml"), (
        f"expected cleaned file to start with an XML declaration; "
        f"got first line: {first_line!r}"
    )


def test_cleaner_is_idempotent(tmp_path, fixtures_dir, copy_fixture):
    """Critical for in-place mutators: running twice == running once."""
    once_dir = tmp_path / "once"
    twice_dir = tmp_path / "twice"
    work_a = copy_fixture(fixtures_dir / "xml_with_whitespace_problems.xml", once_dir)
    work_b = copy_fixture(fixtures_dir / "xml_with_whitespace_problems.xml", twice_dir)

    _run_clean(once_dir)
    _run_clean(twice_dir)
    _run_clean(twice_dir)  # second run on the same copy

    assert work_a.read_text() == work_b.read_text(), (
        "cleaner is not idempotent — running twice differs from running once"
    )

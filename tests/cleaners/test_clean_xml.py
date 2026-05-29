"""Basic tests for QC/cleaning/clean_xml.py.

This is the BASIC round per the design doc. Corpus-mined positives and
negatives (mining published Corpora/<X>/ for real-world cruft patterns)
are a deferred follow-up round with its own design pass.

clean_xml mutates XML in place. All tests work on a tmp_path copy of
the fixture; never mutate the fixture file itself.
"""
import shutil
import subprocess
import sys
from pathlib import Path

from lxml import etree


CLEAN_XML = Path(__file__).resolve().parents[2] / "QC" / "cleaning" / "clean_xml.py"


def _copy_fixture(src: Path, dest_dir: Path) -> Path:
    target_dir = dest_dir / "XML"
    target_dir.mkdir(parents=True, exist_ok=True)
    copy = target_dir / src.name
    shutil.copy(src, copy)
    return copy


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


def test_already_clean_xml_is_left_intact(tmp_path, fixtures_dir):
    """A valid_minimal.xml should round-trip with FORM text preserved."""
    work = _copy_fixture(fixtures_dir / "valid_minimal.xml", tmp_path)
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    after = work.read_text()
    # The two distinct FORM texts from the fixture must survive intact.
    assert "Halo (orig)." in after, f"expected 'Halo (orig).' to survive cleaning; got:\n{after}"
    assert "Halo (std)." in after, f"expected 'Halo (std).' to survive cleaning; got:\n{after}"


def test_html_entities_are_resolved(tmp_path, fixtures_dir):
    work = _copy_fixture(fixtures_dir / "xml_with_html_entities.xml", tmp_path)
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


def test_whitespace_is_normalized(tmp_path, fixtures_dir):
    work = _copy_fixture(fixtures_dir / "xml_with_whitespace_problems.xml", tmp_path)
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    # Parse the output XML so we inspect FORM text values, not raw serialized
    # bytes (XML comments and attribute indentation also contain spaces and
    # would produce false positives if we checked the raw file text).
    forms = _form_texts(work)
    for text in forms:
        assert "   " not in text, (
            f"expected repeated spaces to be normalized away in FORM text, got: {text!r}"
        )


def test_cleaner_is_idempotent(tmp_path, fixtures_dir):
    """Critical for in-place mutators: running twice == running once."""
    once_dir = tmp_path / "once"
    twice_dir = tmp_path / "twice"
    work_a = _copy_fixture(fixtures_dir / "xml_with_html_entities.xml", once_dir)
    work_b = _copy_fixture(fixtures_dir / "xml_with_html_entities.xml", twice_dir)

    _run_clean(once_dir)
    _run_clean(twice_dir)
    _run_clean(twice_dir)  # second run on the same copy

    assert work_a.read_text() == work_b.read_text(), (
        "cleaner is not idempotent — running twice differs from running once"
    )

"""Tests for QC/cleaning/clean_xml.py per design at
.claude/plans/2026-05-29-clean-xml-extension-tests-design.md.

This is the EXTENSION round, layered on top of the basic round in
tests/cleaners/test_clean_xml.py. Many rules in the design require new
infrastructure (language-aware cleaning, CSV warning output, canonical-
orthography lookup, --hard-remove-segmentation flag, transformation
counter) that sub-project B will add. Tests for those behaviors are
pytest.mark.xfail(strict=True). When B implements them, the tests
flip to passing and pytest flags XPASS so the marker can be removed.

Test pattern: copy fixture to tmp_path, subprocess-invoke clean_xml.py
via `--corpora_path tmp_path`, assert on parsed FORM/TRANSL text via
lxml (not raw file bytes — fixture comments and re-serialization make
raw bytes unreliable).
"""
import subprocess
import sys
import unicodedata
from pathlib import Path

import pytest
from lxml import etree

from _helpers import csv_warning_exists as _csv_warning_exists
from _helpers import has_marker as _has_warning_signal


CLEAN_XML = Path(__file__).resolve().parents[2] / "QC" / "cleaning" / "clean_xml.py"

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

XFAIL_NOT_YET_IMPLEMENTED = (
    "Per design doc 2026-05-29-clean-xml-extension-tests-design.md: this "
    "behavior is deferred to sub-project B (language-aware cleaning, "
    "CSV warnings, --hard-remove-segmentation, transformation counter)."
)


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _run_clean(corpora_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CLEAN_XML), "--corpora_path", str(corpora_path)],
        capture_output=True,
        text=True,
    )


def _form_texts_with_kindof(xml_path: Path, parent_tag: str, kindOf: str) -> list:
    """Return text values of all FORM elements with the given kindOf that
    are direct children of <parent_tag>.

    parent_tag: "S", "W", or "M".
    """
    tree = etree.parse(str(xml_path))
    return [
        f.text or ""
        for f in tree.findall(f".//{parent_tag}/FORM[@kindOf='{kindOf}']")
    ]


def _all_form_texts_under(xml_path: Path, parent_tag: str) -> list:
    """Return text values of every FORM that is a direct child of parent_tag,
    regardless of kindOf. Used for W/FORM and M/FORM positives (which have
    no kindOf attribute in the fixtures).
    """
    tree = etree.parse(str(xml_path))
    return [f.text or "" for f in tree.findall(f".//{parent_tag}/FORM")]


def _transl_texts(xml_path: Path, parent_tag: str = "S") -> list:
    """Return text values of all <TRANSL> elements directly under parent_tag."""
    tree = etree.parse(str(xml_path))
    return [t.text or "" for t in tree.findall(f".//{parent_tag}/TRANSL")]


def _s_ids(xml_path: Path) -> list:
    tree = etree.parse(str(xml_path))
    return [s.get("id") for s in tree.findall(".//S")]


# -----------------------------------------------------------------------------
# Plain-pass list (drives the C025 idempotency parametrization at end of file)
#
# Fixtures listed here are run through the cleaner twice; the second run
# must produce byte-identical output to the first run. Only include
# fixtures the cleaner can process successfully (no syntax problems);
# do NOT include xfail-target fixtures, because their "expected" result
# is the post-B behavior, not today's behavior.
# -----------------------------------------------------------------------------
IDEMPOTENT_FIXTURES = [
    "c001_fullwidth_paren_in_form.xml",
    "c001_fullwidth_paren_in_W_and_M_FORM.xml",
    "c001_fullwidth_paren_in_chinese_transl.xml",
    "c002_apostrophe_variants_in_form.xml",
    "c002_double_quote_variants_in_form.xml",
    "c002b_ipa_stress_in_form.xml",
    "c003_repeated_terminal_punct.xml",
    "c004_nbsp_in_form_and_transl.xml",
    "c005_fullwidth_space_in_form.xml",
    "c006_caret_variant_in_form_and_transl.xml",
    "c010_nfd_in_form_all_tiers.xml",
    "c011_hyphens_preserved_in_original.xml",
    "c013_W_segmentation_preserved.xml",
    "c014_angle_gloss_in_W_transl.xml",
    "c019_d_stroke_in_bunun_form.xml",
    "c020_underscore_in_form.xml",
    "c024_parens_in_transl_preserved.xml",
]


# Fixtures whose target behavior is xfailed and therefore not idempotent
# under the current cleaner. When B implements a rule, remove its
# fixture from XFAIL_FIXTURES — the import-time drift assertion below
# will then require the fixture to be added to IDEMPOTENT_FIXTURES.
XFAIL_FIXTURES = {
    "c001_fullwidth_paren_in_nonchinese_transl.xml",
    "c002_apostrophe_in_nonchinese_transl.xml",
    "c002_ascii_apostrophe_in_chinese_transl.xml",
    "c002_double_quotes_in_chinese_transl.xml",
    "c002_modifier_apostrophe_in_chinese_transl.xml",
    "c007_bopomofo_in_form.xml",
    "c012_hyphens_in_standard_amis.xml",
    "c012_hyphens_in_standard_bunun.xml",
    "c012_hyphens_in_standard_thao.xml",
    "c022_sentence_initial_asterisk.xml",
}


# Drift guard: enforce that IDEMPOTENT_FIXTURES + XFAIL_FIXTURES exactly
# cover every c-prefix fixture on disk. Adding a new c### fixture without
# updating one of these sets fails at import time, before any test runs.
_FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"
_ALL_C_FIXTURES = {p.name for p in _FIXTURES_DIR.glob("c*_*.xml")}
_EXPECTED_IDEMPOTENT = _ALL_C_FIXTURES - XFAIL_FIXTURES
_UNEXPECTED = set(IDEMPOTENT_FIXTURES) - _EXPECTED_IDEMPOTENT
_MISSING = _EXPECTED_IDEMPOTENT - set(IDEMPOTENT_FIXTURES)
assert not _UNEXPECTED and not _MISSING, (
    "IDEMPOTENT_FIXTURES / XFAIL_FIXTURES drifted from c*_*.xml fixtures on disk.\n"
    f"  In IDEMPOTENT_FIXTURES but not on disk (or are xfail): {sorted(_UNEXPECTED)}\n"
    f"  On disk and not xfail, but missing from IDEMPOTENT_FIXTURES: {sorted(_MISSING)}"
)


# =============================================================================
# C001 — Full-width punctuation (language-aware)
# =============================================================================


def test_C001_fullwidth_paren_in_S_FORM_collapses_to_ASCII(
    tmp_path, fixtures_dir, copy_fixture
):
    """C001 positive: non-Chinese S/FORM has （X） collapsed to (X)."""
    work = copy_fixture(fixtures_dir / "c001_fullwidth_paren_in_form.xml", tmp_path)
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    orig = _form_texts_with_kindof(work, "S", "original")
    std = _form_texts_with_kindof(work, "S", "standard")
    assert orig == ["Halo (X)."], f"original FORM: {orig!r}"
    assert std == ["Halo (X)."], f"standard FORM: {std!r}"


def test_C001_fullwidth_paren_in_W_and_M_FORM_collapses(
    tmp_path, fixtures_dir, copy_fixture
):
    """C001 positive: W/FORM and M/FORM also have full-width parens collapsed.

    Per OQ1 resolution: the cleaner's .//FORM XPath intentionally
    matches W/FORM and M/FORM descendants, so swap_punctuation applies
    at every tier.
    """
    work = copy_fixture(
        fixtures_dir / "c001_fullwidth_paren_in_W_and_M_FORM.xml", tmp_path
    )
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    w_forms = _all_form_texts_under(work, "W")
    m_forms = _all_form_texts_under(work, "M")
    assert w_forms == ["Pa-rakat(X)-en"], f"W/FORM: {w_forms!r}"
    assert m_forms == ["rakat(Y)"], f"M/FORM: {m_forms!r}"


def test_C001_chinese_transl_fullwidth_paren_preserved(
    tmp_path, fixtures_dir, copy_fixture
):
    """C001 positive: full-width parens in Chinese TRANSL are NOT collapsed.

    This passes today because clean_trans never calls swap_punctuation
    (implicit asymmetry, not language-aware). After B lands explicit
    xml:lang branching the assertion should continue to hold for Chinese.
    """
    work = copy_fixture(
        fixtures_dir / "c001_fullwidth_paren_in_chinese_transl.xml", tmp_path
    )
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    transls = _transl_texts(work, "S")
    assert transls == ["你好（世界）。"], f"TRANSL: {transls!r}"


@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_IMPLEMENTED)
def test_C001_nonchinese_transl_fullwidth_paren_collapses(
    tmp_path, fixtures_dir, copy_fixture
):
    """C001 xfail: full-width parens in a non-Chinese TRANSL should collapse.

    Currently clean_trans is xml:lang-blind and skips swap_punctuation
    for ALL TRANSL. After B branches on xml:lang, English (non-Chinese)
    TRANSL should be normalised.
    """
    work = copy_fixture(
        fixtures_dir / "c001_fullwidth_paren_in_nonchinese_transl.xml", tmp_path
    )
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    transls = _transl_texts(work, "S")
    assert transls == ["Hello (world)."], f"TRANSL: {transls!r}"


# =============================================================================
# C002 — Quote and apostrophe rules (language-aware, with warnings)
# =============================================================================


def test_C002_apostrophe_variants_in_form_collapse_to_ascii(
    tmp_path, fixtures_dir, copy_fixture
):
    """C002 Branch A positive (FORM): mixed apostrophe variants → ASCII U+0027."""
    work = copy_fixture(
        fixtures_dir / "c002_apostrophe_variants_in_form.xml", tmp_path
    )
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    orig = _form_texts_with_kindof(work, "S", "original")[0]
    std = _form_texts_with_kindof(work, "S", "standard")[0]
    # Every single-quote-shape character must be U+0027.
    forbidden = {"’", "‘", "ʼ", "ʻ", "`"}
    for text, label in ((orig, "original"), (std, "standard")):
        for ch in forbidden:
            assert ch not in text, (
                f"{label} still contains {ch!r} (U+{ord(ch):04X}): {text!r}"
            )
        # And the visible apostrophe characters should now be ASCII.
        assert text.count("'") == 5, (
            f"{label}: expected 5 ASCII apostrophes; got {text!r}"
        )


def test_C002_double_quote_variants_in_form_collapse_to_ascii(
    tmp_path, fixtures_dir, copy_fixture
):
    """C002 Branch A positive (FORM): mixed double-quote variants → ASCII U+0022."""
    work = copy_fixture(
        fixtures_dir / "c002_double_quote_variants_in_form.xml", tmp_path
    )
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    orig = _form_texts_with_kindof(work, "S", "original")[0]
    std = _form_texts_with_kindof(work, "S", "standard")[0]
    forbidden = {
        "“", "”",  # curly doubles
        "《", "》",  # 《 》
        "「", "」",  # 「 」
        "『", "』",  # 『 』
    }
    for text, label in ((orig, "original"), (std, "standard")):
        for ch in forbidden:
            assert ch not in text, (
                f"{label} still contains {ch!r} (U+{ord(ch):04X}): {text!r}"
            )
        # Eight non-ASCII double-quote shapes in the input → eight ASCII doubles out.
        assert text.count('"') == 8, (
            f"{label}: expected 8 ASCII double quotes; got {text!r}"
        )


@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_IMPLEMENTED)
def test_C002_apostrophe_in_nonchinese_transl_collapses(
    tmp_path, fixtures_dir, copy_fixture
):
    """C002 Branch A xfail (TRANSL): non-Chinese TRANSL should collapse U+2019 → '."""
    work = copy_fixture(
        fixtures_dir / "c002_apostrophe_in_nonchinese_transl.xml", tmp_path
    )
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    transls = _transl_texts(work, "S")
    assert transls == ["It's here."], f"TRANSL: {transls!r}"


@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_IMPLEMENTED)
def test_C002_double_quotes_in_chinese_transl_collapse_to_canonical(
    tmp_path, fixtures_dir, copy_fixture
):
    """C002 Branch B xfail: Chinese TRANSL with U+201C/U+201D → both U+201D."""
    work = copy_fixture(
        fixtures_dir / "c002_double_quotes_in_chinese_transl.xml", tmp_path
    )
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    transls = _transl_texts(work, "S")
    text = transls[0]
    assert "“" not in text, f"U+201C should be collapsed to U+201D: {text!r}"
    # And both quote positions should now be U+201D.
    assert text.count("”") == 2, (
        f"expected two U+201D characters; got {text!r}"
    )


@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_IMPLEMENTED)
def test_C002_modifier_apostrophe_in_chinese_transl_warns(
    tmp_path, fixtures_dir, copy_fixture
):
    """C002 Branch B xfail: U+02BC in Chinese TRANSL should WARN (and not change).

    We assert on warning indicators (stderr text or CSV existence)
    because warn infrastructure is what's deferred. The character
    surviving is already trivially true; the meaningful new behavior
    is the warning.
    """
    work = copy_fixture(
        fixtures_dir / "c002_modifier_apostrophe_in_chinese_transl.xml", tmp_path
    )
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    # Character must survive unchanged.
    transls = _transl_texts(work, "S")
    assert "ʼ" in transls[0], f"TRANSL: {transls!r}"

    # Warning must be emitted (this is the xfail part).
    warned = _has_warning_signal(
        proc, ("c002", "u+02bc", "warning", "modifier apostrophe"), tmp_path
    )
    csv_ok = _csv_warning_exists(tmp_path, "c002")
    assert warned or csv_ok, (
        f"expected warning indicator for U+02BC in Chinese TRANSL; "
        f"stdout={proc.stdout!r}, stderr={proc.stderr!r}"
    )


@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_IMPLEMENTED)
def test_C002_ascii_apostrophe_in_chinese_transl_warns(
    tmp_path, fixtures_dir, copy_fixture
):
    """C002 Branch B xfail: ASCII U+0027 in Chinese TRANSL should WARN.

    Latin apostrophes in Chinese text are typically IME mistakes worth
    flagging.
    """
    work = copy_fixture(
        fixtures_dir / "c002_ascii_apostrophe_in_chinese_transl.xml", tmp_path
    )
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    transls = _transl_texts(work, "S")
    assert "'" in transls[0], f"TRANSL: {transls!r}"

    warned = _has_warning_signal(
        proc, ("c002", "ascii apostrophe", "warning", "latin apostrophe"), tmp_path
    )
    csv_ok = _csv_warning_exists(tmp_path, "c002")
    assert warned or csv_ok, (
        f"expected warning indicator for ASCII apostrophe in Chinese TRANSL; "
        f"stdout={proc.stdout!r}, stderr={proc.stderr!r}"
    )


# =============================================================================
# C002b — U+02C8 IPA primary stress mark
# =============================================================================


def test_C002b_ipa_stress_in_form_collapses_to_apostrophe(
    tmp_path, fixtures_dir, copy_fixture
):
    """C002b positive: U+02C8 in FORM → ASCII U+0027 via swap_punctuation."""
    work = copy_fixture(fixtures_dir / "c002b_ipa_stress_in_form.xml", tmp_path)
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    orig = _form_texts_with_kindof(work, "S", "original")[0]
    std = _form_texts_with_kindof(work, "S", "standard")[0]
    for text, label in ((orig, "original"), (std, "standard")):
        assert "ˈ" not in text, (
            f"{label} still contains U+02C8: {text!r}"
        )
        assert text == "pa'tas", f"{label}: {text!r}"


@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_IMPLEMENTED)
def test_C002b_ipa_stress_warning_emitted(tmp_path, fixtures_dir, copy_fixture):
    """C002b xfail: U+02C8 transformation should also produce a WARN.

    Stress markers should not normally appear in Formosan corpora;
    visibility helps catch unexpected use. Currently no warning infra.
    """
    copy_fixture(fixtures_dir / "c002b_ipa_stress_in_form.xml", tmp_path)
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    warned = _has_warning_signal(
        proc, ("c002b", "u+02c8", "ipa stress", "stress mark"), tmp_path
    )
    csv_ok = _csv_warning_exists(tmp_path, "c002b")
    assert warned or csv_ok, (
        f"expected warning indicator for U+02C8; "
        f"stdout={proc.stdout!r}, stderr={proc.stderr!r}"
    )


# =============================================================================
# C003 — Repeated terminal punctuation
# =============================================================================


def test_C003_repeated_punct_collapses_in_form_and_transl(
    tmp_path, fixtures_dir, copy_fixture
):
    """C003 positive: !!, ??, --- collapse to single in FORM and TRANSL."""
    work = copy_fixture(fixtures_dir / "c003_repeated_terminal_punct.xml", tmp_path)
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    orig = _form_texts_with_kindof(work, "S", "original")[0]
    std = _form_texts_with_kindof(work, "S", "standard")[0]
    transl = _transl_texts(work, "S")[0]

    expected_form = "Halo! Hapinangha? Pa-tas."
    expected_transl = "Hello! How are you? Wri-ting."
    assert orig == expected_form, f"original: {orig!r}"
    assert std == expected_form, f"standard: {std!r}"
    assert transl == expected_transl, f"TRANSL: {transl!r}"


# =============================================================================
# C004 — Non-breaking space (U+00A0)
# =============================================================================


def test_C004_nbsp_collapses_in_form_and_transl(
    tmp_path, fixtures_dir, copy_fixture
):
    """C004 positive: U+00A0 disappears from FORM and TRANSL (raw-text pass)."""
    work = copy_fixture(fixtures_dir / "c004_nbsp_in_form_and_transl.xml", tmp_path)
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    # No NBSP anywhere in the cleaned file bytes.
    assert " " not in work.read_text(encoding="utf-8"), (
        "NBSP survived raw-text pass"
    )

    # And specifically not in any FORM or TRANSL text.
    for text in (
        _form_texts_with_kindof(work, "S", "original")
        + _form_texts_with_kindof(work, "S", "standard")
        + _transl_texts(work, "S")
    ):
        assert " " not in text, f"NBSP survived in: {text!r}"


# =============================================================================
# C005 — Full-width space (U+3000)
# =============================================================================


def test_C005_fullwidth_space_collapses_in_form(
    tmp_path, fixtures_dir, copy_fixture
):
    """C005 positive: U+3000 in FORM disappears via normalize_whitespace.

    U+3000 is not in swap_punctuation's table but matches \\s+, so the
    cleaner incidentally collapses it. Pinning this so a future stricter
    regex doesn't silently break it.
    """
    work = copy_fixture(fixtures_dir / "c005_fullwidth_space_in_form.xml", tmp_path)
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    orig = _form_texts_with_kindof(work, "S", "original")[0]
    std = _form_texts_with_kindof(work, "S", "standard")[0]
    for text, label in ((orig, "original"), (std, "standard")):
        assert "　" not in text, f"{label} still has U+3000: {text!r}"
        assert text == "Halo hapinangha.", f"{label}: {text!r}"


# =============================================================================
# C006 — Caret variant ⌃ (U+2303) → ^ on FORM, NEGATIVE PIN on TRANSL
# =============================================================================


def test_C006_caret_variant_collapses_in_form_only(
    tmp_path, fixtures_dir, copy_fixture
):
    """C006: ⌃ becomes ^ in FORM but NOT in TRANSL (clean_trans skips swap).

    Negative pin on TRANSL: clean_trans does not call swap_punctuation,
    so ⌃ in TRANSL survives. This documents the implicit asymmetry; if
    a future change extends swap_punctuation to TRANSL via the C001/C002
    language-aware path, ⌃ may end up being rewritten there too, in
    which case this pin will need updating.
    """
    work = copy_fixture(
        fixtures_dir / "c006_caret_variant_in_form_and_transl.xml", tmp_path
    )
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    orig = _form_texts_with_kindof(work, "S", "original")[0]
    std = _form_texts_with_kindof(work, "S", "standard")[0]
    assert orig == "a^b", f"original: {orig!r}"
    assert std == "a^b", f"standard: {std!r}"

    # Negative pin: TRANSL ⌃ must survive untouched today.
    transl = _transl_texts(work, "S")[0]
    assert "⌃" in transl, f"TRANSL ⌃ should survive: {transl!r}"


# =============================================================================
# C007 — Bopomofo ㄇ retained with warning (BOTH xfail)
# =============================================================================


@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_IMPLEMENTED)
def test_C007_bopomofo_preserved(tmp_path, fixtures_dir, copy_fixture):
    """C007 xfail: ㄇ should survive unchanged.

    Today the cleaner silently DELETES ㄇ via remove_junk_chars, so this
    test correctly XFAILs. After B reverses the behavior (preserve +
    warn), the assertion will hold.
    """
    work = copy_fixture(fixtures_dir / "c007_bopomofo_in_form.xml", tmp_path)
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    orig = _form_texts_with_kindof(work, "S", "original")[0]
    std = _form_texts_with_kindof(work, "S", "standard")[0]
    assert "ㄇ" in orig, f"original should still contain ㄇ: {orig!r}"
    assert "ㄇ" in std, f"standard should still contain ㄇ: {std!r}"


@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_IMPLEMENTED)
def test_C007_bopomofo_warning_emitted(tmp_path, fixtures_dir, copy_fixture):
    """C007 xfail: ㄇ occurrence should produce a WARN row in CSV."""
    copy_fixture(fixtures_dir / "c007_bopomofo_in_form.xml", tmp_path)
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    warned = _has_warning_signal(proc, ("c007", "bopomofo", "u+3107"), tmp_path)
    csv_ok = _csv_warning_exists(tmp_path, "c007")
    assert warned or csv_ok, (
        f"expected warning indicator for ㄇ; "
        f"stdout={proc.stdout!r}, stderr={proc.stderr!r}"
    )


# =============================================================================
# C010 — NFC normalisation at S, W, M tiers
# =============================================================================


def test_C010_nfc_normalisation_at_all_form_tiers(
    tmp_path, fixtures_dir, copy_fixture
):
    """C010 positive: NFD input at S/FORM, W/FORM, M/FORM → NFC after cleaning."""
    work = copy_fixture(fixtures_dir / "c010_nfd_in_form_all_tiers.xml", tmp_path)
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    s_orig = _form_texts_with_kindof(work, "S", "original")[0]
    s_std = _form_texts_with_kindof(work, "S", "standard")[0]
    w_forms = _all_form_texts_under(work, "W")
    m_forms = _all_form_texts_under(work, "M")

    for text, label in (
        (s_orig, "S/FORM original"),
        (s_std, "S/FORM standard"),
        (w_forms[0], "W/FORM"),
        (m_forms[0], "M/FORM"),
    ):
        nfc = unicodedata.normalize("NFC", text)
        assert text == nfc, (
            f"{label} is not NFC: {text!r} vs NFC {nfc!r}"
        )
        # Specifically: the combining acute U+0301 must not survive as
        # a standalone codepoint.
        assert "́" not in text, (
            f"{label} still contains COMBINING ACUTE ACCENT: {text!r}"
        )


# =============================================================================
# C011 — Hyphens preserved in S/FORM original
# =============================================================================


def test_C011_hyphens_preserved_in_S_FORM_original(
    tmp_path, fixtures_dir, copy_fixture
):
    """C011 positive pin: hyphens in S/FORM[@kindOf="original"] are byte-exact.

    Today this is trivially true (the cleaner has no segmentation rule).
    Pin guards against future "strip segmentation" feature accidentally
    targeting the original tier.
    """
    work = copy_fixture(
        fixtures_dir / "c011_hyphens_preserved_in_original.xml", tmp_path
    )
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    orig = _form_texts_with_kindof(work, "S", "original")[0]
    assert orig == "M-kan =ku n-hapuy.", f"original: {orig!r}"


# =============================================================================
# C012 — Segmentation in S/FORM standard, data-driven (ALL xfail)
# =============================================================================
# Note: the design also calls for a --hard-remove-segmentation variant.
# That flag does NOT exist in clean_xml.py today, and the cleaner has no
# language-aware logic, so there is no way to exercise the flag's
# negative-override behavior. Skip that variant entirely; document the
# gap here and revisit when B adds the flag.


@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_IMPLEMENTED)
def test_C012_amis_standard_hyphens_stripped(
    tmp_path, fixtures_dir, copy_fixture
):
    """C012 xfail (Amis): "-" not a letter in Ortho113/Amis → strip from standard."""
    work = copy_fixture(fixtures_dir / "c012_hyphens_in_standard_amis.xml", tmp_path)
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    std = _form_texts_with_kindof(work, "S", "standard")[0]
    assert std == "Mkan ku nhapuy.", f"standard: {std!r}"


@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_IMPLEMENTED)
def test_C012_bunun_standard_hyphens_preserved_with_warning(
    tmp_path, fixtures_dir, copy_fixture
):
    """C012 xfail (Bunun): "-" IS a letter in Ortho113/Bunun → preserve + WARN."""
    work = copy_fixture(
        fixtures_dir / "c012_hyphens_in_standard_bunun.xml", tmp_path
    )
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    # Preservation: standard text is unchanged.
    std = _form_texts_with_kindof(work, "S", "standard")[0]
    assert std == "ma-baliv-an.", f"standard: {std!r}"

    # Warning: a CSV row or stderr indicator must mention the rule.
    warned = _has_warning_signal(
        proc, ("c012", "hyphen", "segmentation in standard", "ortho"), tmp_path
    )
    csv_ok = _csv_warning_exists(tmp_path, "c012")
    assert warned or csv_ok, (
        f"expected warning indicator for hyphens in Bunun standard tier; "
        f"stdout={proc.stdout!r}, stderr={proc.stderr!r}"
    )


@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_IMPLEMENTED)
def test_C012_thao_standard_hyphens_preserved_with_warning(
    tmp_path, fixtures_dir, copy_fixture
):
    """C012 xfail (Thao): same expectation as Bunun.

    Negative pin against any future hardcoded "Bunun only" implementation.
    Implementation must be data-driven via Orthographies/Ortho113/<lang>.tsv.
    """
    work = copy_fixture(fixtures_dir / "c012_hyphens_in_standard_thao.xml", tmp_path)
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    std = _form_texts_with_kindof(work, "S", "standard")[0]
    assert std == "qa-li-ka-tu.", f"standard: {std!r}"

    warned = _has_warning_signal(
        proc, ("c012", "hyphen", "segmentation in standard", "ortho"), tmp_path
    )
    csv_ok = _csv_warning_exists(tmp_path, "c012")
    assert warned or csv_ok, (
        f"expected warning indicator for hyphens in Thao standard tier; "
        f"stdout={proc.stdout!r}, stderr={proc.stderr!r}"
    )


# =============================================================================
# C013 — W tier segmentation preserved
# =============================================================================


def test_C013_W_segmentation_markers_preserved(
    tmp_path, fixtures_dir, copy_fixture
):
    """C013 positive pin: W/FORM "-", "=", and "<um>" all survive verbatim.

    The angle-bracket form is on disk as "r&lt;um&gt;akat" and parses to
    "r<um>akat"; lxml re-serialises it correctly on write.
    """
    work = copy_fixture(fixtures_dir / "c013_W_segmentation_preserved.xml", tmp_path)
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    w_forms = _all_form_texts_under(work, "W")
    assert w_forms == ["Pa-rakat-en", "r<um>akat", "=ku"], (
        f"W/FORM list: {w_forms!r}"
    )


# =============================================================================
# C014 — Angle-bracket gloss survives cleaning in W/TRANSL
# =============================================================================


def test_C014_angle_gloss_in_W_transl_preserved(
    tmp_path, fixtures_dir, copy_fixture
):
    """C014 positive pin: W/TRANSL "walk<AV>-FAC" survives.

    The cleaner does not iterate W-level TRANSL at all (only direct
    S/TRANSL), so this is currently a free pass. The pin guards against
    a future TRANSL-descent change that might html.unescape or remove
    angle-bracket tokens.
    """
    work = copy_fixture(fixtures_dir / "c014_angle_gloss_in_W_transl.xml", tmp_path)
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    w_transls = _transl_texts(work, "W")
    assert w_transls == ["walk<AV>-FAC"], f"W/TRANSL: {w_transls!r}"


# =============================================================================
# C019 — đ preserved (negative pin)
# =============================================================================


def test_C019_d_stroke_preserved_in_bunun_form(
    tmp_path, fixtures_dir, copy_fixture
):
    """C019 positive pin: đ in Bunun FORM survives cleaning verbatim."""
    work = copy_fixture(fixtures_dir / "c019_d_stroke_in_bunun_form.xml", tmp_path)
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    orig = _form_texts_with_kindof(work, "S", "original")[0]
    std = _form_texts_with_kindof(work, "S", "standard")[0]
    assert "đ" in orig, f"original: đ should survive: {orig!r}"
    assert "đ" in std, f"standard: đ should survive: {std!r}"
    assert orig == "manaq đaiŋaz.", f"original: {orig!r}"
    assert std == "manaq đaiŋaz.", f"standard: {std!r}"


# =============================================================================
# C020 — Underscores preserved (negative pin)
# =============================================================================


def test_C020_underscores_preserved_in_form(
    tmp_path, fixtures_dir, copy_fixture
):
    """C020 positive pin: "_" in FORM survives cleaning."""
    work = copy_fixture(fixtures_dir / "c020_underscore_in_form.xml", tmp_path)
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    orig = _form_texts_with_kindof(work, "S", "original")[0]
    std = _form_texts_with_kindof(work, "S", "standard")[0]
    assert orig == "is_saiv.", f"original: {orig!r}"
    assert std == "is_saiv.", f"standard: {std!r}"


# =============================================================================
# C022 — Sentence-initial * warn but don't remove (xfail)
# =============================================================================


@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_IMPLEMENTED)
def test_C022_sentence_initial_asterisk_warns_and_preserves(
    tmp_path, fixtures_dir, copy_fixture
):
    """C022 xfail: starred S must be PRESERVED with a WARN.

    Today the cleaner has no rule for "*", so the S is preserved
    (this part already passes), but no warn is emitted — that's
    what XFAILs. After B adds warning infra, both halves pass.

    Contrast with C008's "456otca" sentinel which IS structurally
    removed; "*" is a linguistic annotation worth surfacing upstream.
    """
    work = copy_fixture(fixtures_dir / "c022_sentence_initial_asterisk.xml", tmp_path)
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    # Both S elements must still exist (preservation pin).
    ids = _s_ids(work)
    assert "S_1" in ids and "S_2" in ids, f"S ids: {ids!r}"

    # The starred S still carries the "*".
    orig_of_s1 = [
        f.text
        for s in etree.parse(str(work)).findall(".//S")
        if s.get("id") == "S_1"
        for f in s.findall("FORM[@kindOf='original']")
    ]
    assert orig_of_s1 and orig_of_s1[0].startswith("*"), (
        f"S_1 original FORM should still start with '*': {orig_of_s1!r}"
    )

    # And a WARN must be emitted.
    warned = _has_warning_signal(
        proc, ("c022", "ungrammatical", "sentence-initial", "asterisk"), tmp_path
    )
    csv_ok = _csv_warning_exists(tmp_path, "c022")
    assert warned or csv_ok, (
        f"expected warning indicator for sentence-initial *; "
        f"stdout={proc.stdout!r}, stderr={proc.stderr!r}"
    )


# =============================================================================
# C024 — Parentheses in TRANSL preserved (negative pin)
# =============================================================================


def test_C024_parens_in_transl_preserved(tmp_path, fixtures_dir, copy_fixture):
    """C024 negative pin: ASCII parens in TRANSL survive cleaning."""
    work = copy_fixture(fixtures_dir / "c024_parens_in_transl_preserved.xml", tmp_path)
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    transl = _transl_texts(work, "S")[0]
    assert transl == "she (has) gone", f"TRANSL: {transl!r}"


# =============================================================================
# C025 — Idempotency (parametrized over every positive fixture)
# =============================================================================


@pytest.mark.parametrize("fixture_name", IDEMPOTENT_FIXTURES)
def test_C025_idempotency_for_positive_fixtures(
    tmp_path, fixtures_dir, copy_fixture, fixture_name
):
    """C025: running the cleaner twice produces the same result as once.

    For each plain-passing positive fixture we set up two parallel
    corpora directories: one gets a single clean pass, the other gets
    two. The file contents must be byte-identical at the end.
    """
    once_dir = tmp_path / "once"
    twice_dir = tmp_path / "twice"
    work_once = copy_fixture(fixtures_dir / fixture_name, once_dir)
    work_twice = copy_fixture(fixtures_dir / fixture_name, twice_dir)

    proc1 = _run_clean(once_dir)
    assert proc1.returncode == 0, f"first run stderr: {proc1.stderr}"
    proc2a = _run_clean(twice_dir)
    assert proc2a.returncode == 0, f"second-run #1 stderr: {proc2a.stderr}"
    proc2b = _run_clean(twice_dir)
    assert proc2b.returncode == 0, f"second-run #2 stderr: {proc2b.stderr}"

    assert work_once.read_bytes() == work_twice.read_bytes(), (
        f"cleaner is not idempotent for {fixture_name}: "
        f"once vs twice produces different bytes"
    )


# =============================================================================
# Infrastructure unit tests (no xfail — tests the helpers directly)
# =============================================================================

def test_get_xml_lang_from_direct_attribute():
    """_get_xml_lang finds xml:lang on the element itself."""
    from QC.cleaning.clean_xml import _get_xml_lang
    xml = b'<TEXT xml:lang="ami"><S><TRANSL xml:lang="eng">hi</TRANSL></S></TEXT>'
    tree = etree.fromstring(xml)
    transl = tree.find(".//TRANSL")
    assert _get_xml_lang(transl) == "eng"


def test_get_xml_lang_walks_up_to_ancestor():
    """_get_xml_lang walks up to the TEXT root if element has no xml:lang."""
    from QC.cleaning.clean_xml import _get_xml_lang
    xml = b'<TEXT xml:lang="ami"><S><FORM kindOf="original">x</FORM></S></TEXT>'
    tree = etree.fromstring(xml)
    form = tree.find(".//FORM")
    assert _get_xml_lang(form) == "ami"


def test_get_xml_lang_returns_none_when_missing():
    """_get_xml_lang returns None when no ancestor carries xml:lang."""
    from QC.cleaning.clean_xml import _get_xml_lang
    xml = b'<TEXT><S><FORM>x</FORM></S></TEXT>'
    tree = etree.fromstring(xml)
    form = tree.find(".//FORM")
    assert _get_xml_lang(form) is None


def test_cleaner_warnings_appends_rows(tmp_path):
    """CleanerWarnings.add() accumulates rows; write_csv() creates a CSV."""
    from QC.cleaning.clean_xml import CleanerWarnings
    w = CleanerWarnings(tmp_path / "out.csv")
    w.add("c002", str(tmp_path / "foo.xml"), "S_1", "ʼ", 3)
    w.add("c007", str(tmp_path / "bar.xml"), "S_2", "ㄇ", 0)
    w.write_csv()
    text = (tmp_path / "out.csv").read_text(encoding="utf-8").lower()
    assert "c002" in text
    assert "c007" in text
    assert "ʼ".lower() in text or "02bc" in text  # char or unicode point


def test_cleaner_warnings_no_file_when_empty(tmp_path):
    """CleanerWarnings.write_csv() does NOT create the file if no rows."""
    from QC.cleaning.clean_xml import CleanerWarnings
    w = CleanerWarnings(tmp_path / "out.csv")
    w.write_csv()
    assert not (tmp_path / "out.csv").exists()

"""Tests for QC/utilities/add_phonology.py dialect/column resolution.

add_phonology.py adds <PHON> elements by transliterating <FORM> text via
Orthographies/Ortho113/<Language>.tsv. Which column it reads is chosen by
whether the language has multiple dialects (per dialects.csv):

  - single-dialect language (e.g. Yami): the dialect attribute is the
    language name by convention (dialect="Yami"), which is NOT a column in
    Yami.tsv (columns: letter, IPA). The script must ignore the dialect
    label and use the lone value column. This is the regression for the
    2026-06 bug where dialect="Yami" produced
    "Error: Dialect 'Yami' not found and no 'default' column in TSV".
  - multi-dialect language (e.g. Amis): the dialect attribute selects the
    column (Amis.tsv has per-dialect columns + default).

The script mutates XML in place, so each test builds a throwaway corpus
tree under tmp_path and never touches Corpora/. The orthography TSVs are
resolved relative to the repo, so cwd does not matter.
"""
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace

import pytest

import QC.utilities.add_phonology as add_phonology
from QC.utilities.add_phonology import load_profile, phonologize

ADD_PHONOLOGY = (
    Path(__file__).resolve().parents[2] / "QC" / "utilities" / "add_phonology.py"
)


def _write_corpus(root: Path, language_dir: str, filename: str, xml_text: str) -> Path:
    """Place an XML at root/XML/<language_dir>/<filename> and return its path."""
    xml_path = root / "XML" / language_dir / filename
    xml_path.parent.mkdir(parents=True, exist_ok=True)
    xml_path.write_text(xml_text, encoding="utf-8")
    return xml_path


def _run(
    corpora_path: Path,
    *,
    target_column: str | None = None,
    orthography: str = "Ortho113",
    preserve_existing_original: bool = False,
) -> subprocess.CompletedProcess:
    command = [
        sys.executable,
        str(ADD_PHONOLOGY),
        "--corpora_path",
        str(corpora_path),
        "--orthography",
        orthography,
    ]
    if target_column:
        command.extend(["--target_column", target_column])
    if preserve_existing_original:
        command.append("--preserve-existing-original")
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
    )


def _phon_texts(xml_path: Path, kind: str) -> list[str]:
    root = ET.parse(xml_path).getroot()
    return [
        p.text
        for p in root.findall(".//PHON")
        if p.get("kindOf") == kind and p.text is not None
    ]


def test_single_dialect_label_resolves_to_lone_ipa_column(tmp_path):
    """Yami (single-dialect) with dialect="Yami" must use the lone IPA column.

    Before the fix the run printed "Error: Dialect 'Yami' not found and no
    'default' column" and added no PHON. After the fix it resolves to the IPA
    column, adds PHON, and the IPA reflects the Yami.tsv ng -> ŋ mapping.
    """
    corpus = tmp_path / "corpus"
    xml_path = _write_corpus(
        corpus,
        "Yami",
        "y.xml",
        '<TEXT xml:lang="tao" dialect="Yami">'
        '<S id="1">'
        '<FORM kindOf="original">ngaro</FORM>'
        '<FORM kindOf="standard">ngaro</FORM>'
        "</S></TEXT>",
    )
    proc = _run(corpus)
    combined = proc.stdout + proc.stderr
    assert "Error" not in combined, f"unexpected error: {combined!r}"
    # PHON must have been added (resolution succeeded; the file was not skipped).
    standard_phon = _phon_texts(xml_path, "standard")
    assert standard_phon, f"no standard PHON added; output was: {combined!r}"
    # ...and the IPA reflects the Yami.tsv mapping ng -> ŋ.
    assert any("ŋ" in p for p in standard_phon), (
        f"expected ng->ŋ in standard PHON, got {standard_phon!r}"
    )


def test_accepts_single_xml_corpora_path(tmp_path):
    xml_path = tmp_path / "y.xml"
    xml_path.write_text(
        '<TEXT xml:lang="tao" dialect="Yami">'
        '<S id="1">'
        '<FORM kindOf="original">ngaro</FORM>'
        '<FORM kindOf="standard">ngaro</FORM>'
        "</S></TEXT>",
        encoding="utf-8",
    )
    proc = _run(xml_path)
    combined = proc.stdout + proc.stderr
    assert "Error" not in combined, f"unexpected error: {combined!r}"
    assert _phon_texts(xml_path, "standard"), (
        f"no standard PHON added for direct XML path; output: {combined!r}"
    )


def test_multi_dialect_resolves_via_dialect_column(tmp_path):
    """Amis (multi-dialect) with dialect="Coastal" resolves the Coastal column.

    Sanity pin for the multi-dialect branch: a real dialect label that matches
    a TSV column must resolve and produce PHON without error.
    """
    corpus = tmp_path / "corpus"
    xml_path = _write_corpus(
        corpus,
        "Amis",
        "a.xml",
        '<TEXT xml:lang="ami" dialect="Coastal">'
        '<S id="1">'
        '<FORM kindOf="original">cecay</FORM>'
        '<FORM kindOf="standard">cecay</FORM>'
        "</S></TEXT>",
    )
    proc = _run(corpus)
    combined = proc.stdout + proc.stderr
    assert "Error" not in combined, f"unexpected error: {combined!r}"
    assert _phon_texts(xml_path, "standard"), (
        f"no standard PHON added for multi-dialect Amis; output: {combined!r}"
    )


def test_explicit_target_column_overrides_dialect_column(tmp_path):
    corpus = tmp_path / "corpus"
    xml_path = _write_corpus(
        corpus,
        "Bunun",
        "b.xml",
        '<TEXT xml:lang="bnn" dialect="Tanqun">'
        '<S id="1"><FORM kindOf="standard">e</FORM></S>'
        "</TEXT>",
    )

    proc = _run(corpus, target_column="default")

    combined = proc.stdout + proc.stderr
    assert proc.returncode == 0, combined
    assert _phon_texts(xml_path, "standard") == ["e"]


def test_does_not_inject_whitespace_into_partial_UNCLEAR(tmp_path):
    corpus = tmp_path / "corpus"
    xml_path = _write_corpus(
        corpus,
        "Paiwan",
        "p.xml",
        '<TEXT xml:lang="pwn" dialect="Eastern"><S id="1">'
        '<FORM kindOf="original">sa izua<UNCLEAR/></FORM>'
        '<FORM kindOf="standard">sa izua<UNCLEAR/></FORM>'
        "</S></TEXT>",
    )
    proc = _run(corpus)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    proc = _run(corpus)
    assert proc.returncode == 0, f"second run stderr: {proc.stderr}"
    root = ET.parse(xml_path).getroot()
    assert ["".join(form.itertext()) for form in root.findall(".//FORM")] == [
        "sa izua",
        "sa izua",
    ]
    serialized = xml_path.read_text(encoding="utf-8")
    assert "\n    <S id=\"1\">" in serialized
    assert "\n        <FORM" in serialized
    assert serialized.count("sa izua<UNCLEAR/></FORM>") == 2


@pytest.mark.parametrize(
    ("scheme", "language", "dialect", "source", "expected"),
    [
        ("StacyHuang", "Yami", "Yami", "ngedshcjyzo", "ŋəɖʂʁtʃdʒjřo"),
        ("Pgagu", "Seediq", "Truku", "nguy cey", "ŋui tsei"),
        (
            "TaiwanNandao",
            "Amis",
            "Xiuguluan",
            "singsi pisanga' kaolahan ho 'adopen fo'is Kangodoan miowak",
            "ɕiŋɕi pisaŋaʡħ kawɾaha̞n hɔ ʡa̞ɬopən foʡes kaŋoɬowan mijowak",
        ),
        ("TaiwanNandao", "Rukai", "Mantauran", "sici", "ʃitʃi"),
        (
            "Huang",
            "Bunun",
            "Zhuoqun",
            "qi qu si ci au ua ai ia",
            "qe qo ɕi či aw wa aj ja",
        ),
        (
            "Zhang",
            "Kavalan",
            "Kavalan",
            "siqulusay temawaRiku",
            "siəquɬusaj təmawaʁeku",
        ),
        ("Li", "Rukai", "Wutai", "TDcꟈLy", "ʈɖʦðɭj"),
        (
            "TaiwanNandao",
            "Puyuma",
            "Zhiben",
            "sinsi etiv temengez velrvelr semver kaziu zua",
            "ʃinʃi ətif təməŋəʂ vəɮvəɬ s̺əmvər kaʐiju ʐuwa",
        ),
        ("Cauquelin", "Puyuma", "Nanwang", "pakusis", "pakuʃiʃ"),
        (
            "Tsuchida",
            "Pazeh",
            "Pazeh",
            "pa-kizih masi-karum",
            "pakizeħ masikaɾom",
        ),
        ("Ochiai", "Seediq", "Tegudaya", "quy cyz", "ʡui̯ tsjdz"),
        (
            "TaiwanNandao",
            "Paiwan",
            "Central",
            (
                "veljevelj seme'ez zepulj cemas gememegem veneci' "
                "mangetjez tiima naaya pemanaq"
            ),
            (
                "vələvəɬ sɨməʔəz zɨpuɬ tsɨmas gəməmgəm vəntsiʔ "
                "maŋcəz tima naja pənanaq"
            ),
        ),
        (
            "TaiwanNandao",
            "Seediq",
            "Tegudaya",
            "cahang xuy r",
            "tsaħaŋ χuj ɾ",
        ),
    ],
)
def test_reviewed_source_orthography_examples(
    scheme: str,
    language: str,
    dialect: str,
    source: str,
    expected: str,
):
    profile = load_profile(scheme, language, dialect)
    assert profile is not None
    assert phonologize(source, profile) == expected


def test_custom_profile_keeps_source_and_standard_phonology_distinct(tmp_path):
    corpus = tmp_path / "corpus"
    xml_path = _write_corpus(
        corpus,
        "Amis",
        "a.xml",
        '<TEXT xml:lang="ami" dialect="Xiuguluan"><S id="1">'
        '<FORM kindOf="original">singsi</FORM>'
        '<FORM kindOf="standard">singsi</FORM>'
        "</S></TEXT>",
    )

    proc = _run(corpus, orthography="TaiwanNandao")

    assert proc.returncode == 0, proc.stderr
    assert _phon_texts(xml_path, "original") == ["ɕiŋɕi"]
    assert _phon_texts(xml_path, "standard") == ["siŋsi"]


def test_original_phonology_does_not_require_an_ortho113_table(tmp_path):
    xml_path = tmp_path / "pazeh.xml"
    xml_path.write_text(
        '<TEXT xml:lang="pzh" dialect="Pazeh"><S id="1">'
        '<FORM kindOf="original">pa-kizih</FORM>'
        '<FORM kindOf="standard">pakizih</FORM>'
        "</S></TEXT>",
        encoding="utf-8",
    )

    proc = _run(xml_path, orthography="Tsuchida")

    assert proc.returncode == 0, proc.stderr
    assert "Standard orthography TSV not found for Pazeh" in proc.stdout
    assert _phon_texts(xml_path, "original") == ["pakizeħ"]
    assert _phon_texts(xml_path, "standard") == []


def test_can_preserve_source_supplied_original_phonology(tmp_path):
    xml_path = tmp_path / "source-phon.xml"
    xml_path.write_text(
        '<TEXT xml:lang="bnn" dialect="Zhuoqun"><S id="1">'
        '<FORM kindOf="original">madaiŋ</FORM>'
        '<PHON kindOf="original">ma.dájŋ</PHON>'
        '<FORM kindOf="standard">madaing</FORM>'
        "</S></TEXT>",
        encoding="utf-8",
    )

    proc = _run(
        xml_path,
        orthography="Huang",
        preserve_existing_original=True,
    )

    assert proc.returncode == 0, proc.stderr
    assert _phon_texts(xml_path, "original") == ["ma.dájŋ"]
    assert _phon_texts(xml_path, "standard")


def _write_profile(
    monkeypatch,
    tmp_path: Path,
    *,
    language: str,
    tsv: str,
    rules: str | None = None,
    scheme: str = "TestScheme",
) -> str:
    """Create a temp orthography scheme and point add_phonology at it.

    Returns the scheme name so tests can call load_profile(scheme, ...).
    A rule sidecar is written only when ``rules`` is given.
    """
    scheme_dir = tmp_path / "Orthographies" / scheme
    scheme_dir.mkdir(parents=True, exist_ok=True)
    (scheme_dir / f"{language}.tsv").write_text(tsv, encoding="utf-8")
    if rules is not None:
        (scheme_dir / f"{language}.rules.tsv").write_text(rules, encoding="utf-8")
    monkeypatch.setattr(add_phonology, "ORTHOGRAPHIES_PATH", tmp_path / "Orthographies")
    return scheme


# Seediq (multi-dialect) with only a default mapping column, so the rules'
# dialect scoping — not the column selection — is what varies the output.
_SEEDIQ_TSV = "letter\tdefault\nq\tq\ni\ti\n"


def test_dialect_scoped_rule_applies_only_to_that_dialect(tmp_path, monkeypatch):
    scheme = _write_profile(
        monkeypatch,
        tmp_path,
        language="Seediq",
        tsv=_SEEDIQ_TSV,
        rules=(
            "pattern\treplacement\tdescription\tdialect\n"
            "(?<=q)i\te\tlower i after q (Truku only)\tTruku\n"
        ),
    )

    truku = load_profile(scheme, "Seediq", "Truku")
    tegudaya = load_profile(scheme, "Seediq", "Tegudaya")

    assert phonologize("qi", truku) == "qe"
    assert phonologize("qi", tegudaya) == "qi"


def test_blank_dialect_rule_applies_to_every_dialect(tmp_path, monkeypatch):
    scheme = _write_profile(
        monkeypatch,
        tmp_path,
        language="Seediq",
        tsv=_SEEDIQ_TSV,
        rules=(
            "pattern\treplacement\tdescription\tdialect\n"
            "(?<=q)i\te\tuniversal lowering\t\n"
        ),
    )

    truku = load_profile(scheme, "Seediq", "Truku")
    tegudaya = load_profile(scheme, "Seediq", "Tegudaya")

    assert phonologize("qi", truku) == "qe"
    assert phonologize("qi", tegudaya) == "qe"


def test_default_tagged_rule_is_the_fallback_for_unnamed_dialects(
    tmp_path, monkeypatch
):
    scheme = _write_profile(
        monkeypatch,
        tmp_path,
        language="Seediq",
        tsv=_SEEDIQ_TSV,
        rules=(
            "pattern\treplacement\tdescription\tdialect\n"
            "(?<=q)i\te\tTruku-specific\tTruku\n"
            "(?<=q)i\to\tfallback for the rest\tdefault\n"
        ),
    )

    truku = load_profile(scheme, "Seediq", "Truku")
    tegudaya = load_profile(scheme, "Seediq", "Tegudaya")

    # Truku is explicitly named, so it takes the Truku rule, not the default one.
    assert phonologize("qi", truku) == "qe"
    # Tegudaya is not named anywhere, so it falls back to the 'default' rule.
    assert phonologize("qi", tegudaya) == "qo"


def test_rules_without_dialect_column_apply_to_all_dialects(tmp_path, monkeypatch):
    scheme = _write_profile(
        monkeypatch,
        tmp_path,
        language="Seediq",
        tsv=_SEEDIQ_TSV,
        rules=(
            "pattern\treplacement\tdescription\n"
            "(?<=q)i\te\tno dialect column at all\n"
        ),
    )

    truku = load_profile(scheme, "Seediq", "Truku")
    tegudaya = load_profile(scheme, "Seediq", "Tegudaya")

    assert phonologize("qi", truku) == "qe"
    assert phonologize("qi", tegudaya) == "qe"


# ---------------------------------------------------------------------------
# Engine regression tests: these pin behaviours that differ from the pre-rewrite
# (main) mapper, which re-scanned the whole string after every replacement. Each
# assertion below would have produced the "old" value noted in its comment, so
# the test fails if the single-pass / casefold / unknown-char behaviour regresses.
# ---------------------------------------------------------------------------


def test_generated_ipa_is_not_remapped_by_a_later_letter(tmp_path, monkeypatch):
    """Longest-grapheme single pass: a symbol emitted by one mapping must not be
    re-consumed by a later mapping. This is the Paiwan `tj -> c` case, where the
    old sequential mapper then re-hit the generated `c` with `c -> ʦ`."""
    scheme = _write_profile(
        monkeypatch,
        tmp_path,
        language="Yami",  # single-dialect -> the lone value column is used
        tsv="letter\tIPA\ntj\tc\nc\tʦ\n",
    )
    profile = load_profile(scheme, "Yami", "Yami")

    # `tj` -> `c` (the generated `c` is NOT re-mapped to `ʦ`; old gave "ʦ"),
    # while a source `c` still maps to `ʦ`.
    assert phonologize("tjc", profile) == "cʦ"


def test_real_paiwan_tj_is_not_double_mapped_to_ts(tmp_path, monkeypatch):
    """Anchor the above against the shipped Ortho113 Paiwan table (the ~15% of
    Paiwan standard PHON that this fix changes)."""
    profile = load_profile("Ortho113", "Paiwan", "Central")
    assert profile is not None
    # old (main) produced "ʦaʎaʎak"; the single-pass mapper keeps the `c`.
    assert phonologize("tjaljaljak", profile) == "caʎaʎak"


def test_casefold_fallback_maps_lowercase_onto_uppercase_only_row(
    tmp_path, monkeypatch
):
    """When a source character has no exact-case row, it casefolds onto the
    other-case row (Kavalan lowercase `r` -> the `R -> ʁ` row; old left it as a
    bare `r`). But an exact-case row always wins over the fallback."""
    uppercase_only = _write_profile(
        monkeypatch,
        tmp_path,
        language="Yami",
        tsv="letter\tIPA\nR\tʁ\n",
        scheme="UpperOnly",
    )
    profile = load_profile(uppercase_only, "Yami", "Yami")
    assert phonologize("r", profile) == "ʁ"

    both_cases = _write_profile(
        monkeypatch,
        tmp_path,
        language="Yami",
        tsv="letter\tIPA\nR\tʁ\nr\tɾ\n",
        scheme="BothCases",
    )
    profile = load_profile(both_cases, "Yami", "Yami")
    assert phonologize("r", profile) == "ɾ"  # exact match preferred, not ʁ


def test_unknown_characters_star_marks_survive_punctuation_dropped(
    tmp_path, monkeypatch
):
    """Unmapped characters become `*`, combining marks (M*) survive, and
    unmapped punctuation — ASCII and Unicode P* alike — is dropped (the
    2026-08-09 null-morpheme/punctuation spec; previously punctuation was
    copied through to PHON)."""
    scheme = _write_profile(
        monkeypatch,
        tmp_path,
        language="Yami",
        tsv="letter\tIPA\na\tɑ\n",
    )
    profile = load_profile(scheme, "Yami", "Yami")

    # a -> ɑ; `…` (Po) dropped; space survives; `卐` (Lo) and `◇` (So) -> `*`.
    assert phonologize("a… 卐◇", profile) == "ɑ **"
    # a combining acute (Mn, U+0301) rides through rather than being starred,
    # whereas a precomposed accented letter (a base Ll not in the table) is
    # unknown and becomes `*`. (Use the escape sequences verbatim — NFC
    # á and NFD a+combining are visually identical in source code.)
    assert phonologize("a\u0301", profile) == "\u0251\u0301"
    assert phonologize("\u00e1", profile) == "*"


def test_unmapped_punctuation_dropped_from_phon(tmp_path, monkeypatch):
    """PHON is a phonetic tier: punctuation that no mapping consumed is
    deleted, not copied through. Mapped punctuation (the orthographic
    apostrophe here) is consumed by the tokenizer and unaffected."""
    scheme = _write_profile(
        monkeypatch,
        tmp_path,
        language="Yami",
        tsv="letter\tIPA\nk\tk\na\tɑ\nu\tu\nc\tʦ\ny\tj\n'\tʔ\n",
    )
    profile = load_profile(scheme, "Yami", "Yami")
    assert phonologize("kaku, ca'ay.", profile) == "kɑku ʦɑʔɑj"


def test_dash_punctuation_dropped_from_phon(tmp_path, monkeypatch):
    """Typographic dashes (en dash here) are punctuation, not segmentation:
    they are dropped by the punctuation filter, not hyphen handling."""
    scheme = _write_profile(
        monkeypatch, tmp_path, language="Yami", tsv="letter\tIPA\na\tɑ\n"
    )
    profile = load_profile(scheme, "Yami", "Yami")
    assert phonologize("a–a", profile) == "ɑɑ"


# ---------------------------------------------------------------------------
# Per-language standard orthography registry (standards.csv). The standard
# tier's scheme comes from standard_orthography(language), not a hardcoded
# "Ortho113"; a None value means the language has no designated standard yet.
# ---------------------------------------------------------------------------


def _process(xml_path, *, orthography=None):
    add_phonology.process_file(
        str(xml_path),
        SimpleNamespace(
            orthography=orthography,
            target_column=None,
            preserve_existing_original=False,
        ),
    )


def test_standard_tier_uses_the_designated_standard_scheme(tmp_path, monkeypatch):
    """add_phonology loads the standard tier from the registry-designated scheme,
    not a hardcoded Ortho113. The temp dir has no Ortho113 table, so producing
    standard PHON proves the CustomStd scheme was used."""
    _write_profile(
        monkeypatch,
        tmp_path,
        language="Yami",
        tsv="letter\tIPA\na\tX\n",
        scheme="CustomStd",
    )
    monkeypatch.setattr(add_phonology, "standard_orthography", lambda language: "CustomStd")

    xml_path = tmp_path / "y.xml"
    xml_path.write_text(
        '<TEXT xml:lang="tao" dialect="Yami"><S id="1">'
        '<FORM kindOf="standard">a</FORM></S></TEXT>',
        encoding="utf-8",
    )
    _process(xml_path)

    assert _phon_texts(xml_path, "standard") == ["X"]


def test_no_designated_standard_skips_standard_but_keeps_original(
    tmp_path, monkeypatch, capsys
):
    """When the registry declares no standard (None), the standard tier is
    skipped with a warning, while the original tier is still produced."""
    _write_profile(
        monkeypatch,
        tmp_path,
        language="Yami",
        tsv="letter\tIPA\na\tX\n",
        scheme="Src",
    )
    monkeypatch.setattr(add_phonology, "standard_orthography", lambda language: None)

    xml_path = tmp_path / "y.xml"
    xml_path.write_text(
        '<TEXT xml:lang="tao" dialect="Yami"><S id="1">'
        '<FORM kindOf="original">a</FORM>'
        '<FORM kindOf="standard">a</FORM></S></TEXT>',
        encoding="utf-8",
    )
    _process(xml_path, orthography="Src")

    assert _phon_texts(xml_path, "original") == ["X"]
    assert _phon_texts(xml_path, "standard") == []
    assert "no designated standard orthography for yami" in capsys.readouterr().out.lower()


def test_add_phonology_runs_with_only_an_original_tier(tmp_path):
    """A file with an original FORM but no standard FORM produces only original
    PHON (via --orthography); the standard tier has nothing to do."""
    xml_path = tmp_path / "amis.xml"
    xml_path.write_text(
        '<TEXT xml:lang="ami" dialect="Xiuguluan"><S id="1">'
        '<FORM kindOf="original">singsi</FORM></S></TEXT>',
        encoding="utf-8",
    )

    proc = _run(xml_path, orthography="TaiwanNandao")

    assert proc.returncode == 0, proc.stderr
    assert _phon_texts(xml_path, "original")
    assert _phon_texts(xml_path, "standard") == []


def test_whole_null_form_gets_visible_null_phon(tmp_path, monkeypatch):
    """A FORM that IS a null morpheme (the M-level case) gets PHON '∅' —
    never an empty PHON element."""
    scheme = _write_profile(
        monkeypatch, tmp_path, language="Yami", tsv="letter\tIPA\na\tɑ\nk\tk\n"
    )
    profile = load_profile(scheme, "Yami", "Yami")
    assert phonologize("∅", profile) == "∅"
    assert phonologize(" ∅ ", profile) == "∅"


def test_embedded_null_units_are_silent(tmp_path, monkeypatch):
    """Null units inside a larger form are dropped as units (marker +
    bridging hyphen) before mapping, so PHON is clean IPA with no '*'."""
    scheme = _write_profile(
        monkeypatch, tmp_path, language="Yami", tsv="letter\tIPA\na\tɑ\nk\tk\n"
    )
    profile = load_profile(scheme, "Yami", "Yami")
    assert phonologize("∅-aka", profile) == "ɑkɑ"
    assert phonologize("aka-∅", profile) == "ɑkɑ"
    assert phonologize("aka ∅ aka", profile) == "ɑkɑ ɑkɑ"


def test_foreign_o_slash_is_not_treated_as_null(tmp_path, monkeypatch):
    """Only canonical '∅' is null. A Danish 'ø' (foreign letter, e.g.
    'Grønland') follows the normal unknown-letter path — starred, never
    silently deleted."""
    scheme = _write_profile(
        monkeypatch,
        tmp_path,
        language="Yami",
        tsv="letter\tIPA\ng\tg\nr\tr\nn\tn\nl\tl\na\tɑ\nd\td\n",
    )
    profile = load_profile(scheme, "Yami", "Yami")
    assert phonologize("Grønland", profile) == "gr*nlɑnd"

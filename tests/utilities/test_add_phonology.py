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

import pytest

from QC.utilities.add_phonology import load_profile, phonologize
from QC.validation._dialect_inventory import valid_dialects

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
        ("Li", "Rukai", "Wutai", "TDcꟈLy", "ʈɖtsðɭj"),
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


def test_pazeh_is_a_supported_single_dialect_language():
    assert valid_dialects("pzh") == frozenset({"Pazeh", "unknown"})


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


def test_null_morpheme_is_silent_in_phonology(tmp_path):
    corpus = tmp_path / "corpus"
    xml_path = _write_corpus(
        corpus,
        "Amis",
        "a.xml",
        '<TEXT xml:lang="ami" dialect="Coastal"><S id="1">'
        '<FORM kindOf="standard">∅-fangcal ø-ci</FORM>'
        '<W id="1-W1"><FORM kindOf="standard">∅-fangcal</FORM>'
        '<M id="1-W1-M1"><FORM kindOf="standard">∅</FORM></M>'
        '<M id="1-W1-M2"><FORM kindOf="standard">fangcal</FORM></M>'
        "</W>"
        '<W id="1-W2"><FORM kindOf="standard">ø-ci</FORM>'
        '<M id="1-W2-M1"><FORM kindOf="standard">ø</FORM></M>'
        '<M id="1-W2-M2"><FORM kindOf="standard">ci</FORM></M>'
        "</W></S></TEXT>",
    )

    proc = _run(corpus)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    root = ET.parse(xml_path).getroot()
    assert root.findtext("./S/PHON[@kindOf='standard']") == "faŋʦaɾ ʦi"
    assert root.findtext("./S/W/PHON[@kindOf='standard']") == "faŋʦaɾ"
    assert root.findtext("./S/W/M/PHON[@kindOf='standard']") == "∅"
    assert root.findtext("./S/W[2]/PHON[@kindOf='standard']") == "ʦi"
    assert root.findtext("./S/W[2]/M/PHON[@kindOf='standard']") == "∅"
    assert "*" not in xml_path.read_text(encoding="utf-8")


def test_non_orthographic_punctuation_is_not_copied_to_phon(tmp_path):
    corpus = tmp_path / "corpus"
    xml_path = _write_corpus(
        corpus,
        "Amis",
        "a.xml",
        '<TEXT xml:lang="ami" dialect="Coastal"><S id="1">'
        '<FORM kindOf="standard">kaku, ca\'ay.</FORM>'
        "</S></TEXT>",
    )

    proc = _run(corpus)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _phon_texts(xml_path, "standard") == ["kaku ʦaʡaj"]


def test_lowercase_o_slash_is_not_a_global_null_marker(tmp_path):
    corpus = tmp_path / "corpus"
    xml_path = _write_corpus(
        corpus,
        "Yami",
        "y.xml",
        '<TEXT xml:lang="tao" dialect="Yami"><S id="1">'
        '<FORM kindOf="standard">ø</FORM>'
        "</S></TEXT>",
    )

    proc = _run(corpus)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _phon_texts(xml_path, "standard") == ["*"]

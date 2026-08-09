"""Tests for QC/utilities/standardize.py.

Standardize copies the `original` tier to a `standard` tier (with --copy)
or transliterates via a TSV mapping. It mutates XML in place, so all
tests work on a tmp_path copy of the fixture, never on the fixture
file itself.

CLI shape notes:
  --corpora_path is treated as a *collection* root: the script does
  os.listdir(corpora_path) to enumerate corpus directories, then walks
  each one for XML files. To point at a single fixture file, arrange
  tmp_path/ as the collection root and place the file in tmp_path/XML/.

  --tsv_path mode uses a column named "original" (not "source") as the
  lookup key; the target column is named via --target_column.
"""
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

STANDARDIZE = Path(__file__).resolve().parents[2] / "QC" / "utilities" / "standardize.py"
CONVERSION_TABLES = STANDARDIZE.parents[2] / "Orthographies" / "ConversionTables"


def _run_standardize(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(STANDARDIZE), *args],
        capture_output=True,
        text=True,
    )


def _standard_forms(xml_path: Path) -> list[str]:
    """All standard FORM texts in document order, across S, W, and M levels.

    standardize.py walks `.//FORM/..` so it operates on every element with a
    FORM child. The test helpers mirror that scope rather than restricting
    to sentence-level FORMs only.
    """
    root = ET.parse(xml_path).getroot()
    return [
        f.text
        for f in root.findall(".//FORM")
        if f.get("kindOf") == "standard" and f.text is not None
    ]


def _original_forms(xml_path: Path) -> list[str]:
    """All original FORM texts in document order, across S, W, and M levels."""
    root = ET.parse(xml_path).getroot()
    return [
        f.text
        for f in root.findall(".//FORM")
        if f.get("kindOf") == "original" and f.text is not None
    ]


def test_copy_adds_standard_tier_when_only_original_exists(tmp_path, fixtures_dir, copy_fixture):
    work = copy_fixture(fixtures_dir / "valid_original_only.xml", tmp_path)
    proc = _run_standardize(["--copy", "--corpora_path", str(tmp_path)])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    # standardize.py must add a standard tier at every element with a FORM
    # child (S, W, M) — not just at the sentence level.
    assert _standard_forms(work) == _original_forms(work)
    assert _standard_forms(work) == [
        "Halo, hapinangha.",
        "Nawhani kako tayni i toron.",
        "Nawhani",
        "Naw",
        "hani",
        "kako",
    ]


def test_copy_accepts_single_xml_corpora_path(tmp_path, fixtures_dir, copy_fixture):
    work = copy_fixture(fixtures_dir / "valid_original_only.xml", tmp_path)
    proc = _run_standardize(["--copy", "--corpora_path", str(work)])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    assert _standard_forms(work) == _original_forms(work)


def test_copy_overwrites_existing_standard_tier(tmp_path, fixtures_dir, copy_fixture):
    work = copy_fixture(fixtures_dir / "valid_both_tiers.xml", tmp_path)
    proc = _run_standardize(["--copy", "--corpora_path", str(tmp_path)])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    standard = _standard_forms(work)
    # No level (S, W, M) may retain the divergent "REPLACE ME *" content
    # — overwrite must happen at every level.
    assert not any("REPLACE ME" in s for s in standard), (
        f"some standard tier was not overwritten: {standard}"
    )
    assert standard == _original_forms(work)


def test_tsv_mapping_transforms_standard_tier(tmp_path, fixtures_dir, copy_fixture):
    work = copy_fixture(fixtures_dir / "valid_original_only.xml", tmp_path)
    tsv = fixtures_dir / "tiny_mapping.tsv"
    proc = _run_standardize([
        "--tsv_path", str(tsv),
        "--target_column", "target",
        "--corpora_path", str(tmp_path),
    ])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    standard = _standard_forms(work)
    # apply_standard runs per-element, doing substring .replace() on each
    # standard FORM. Only S_1's text contains the TSV's source tokens; the
    # other elements (S_2 sentence, W, Ms, W_2) pass through unchanged.
    assert standard == [
        "Hello, greeting.",
        "Nawhani kako tayni i toron.",
        "Nawhani",
        "Naw",
        "hani",
        "kako",
    ], f"expected mapped sentence in standard tier, got: {standard!r}"


def test_copy_preserves_UNCLEAR_child_when_creating_standard(
    tmp_path, fixtures_dir, copy_fixture
):
    """--copy must preserve <UNCLEAR/> children when adding a standard tier.

    Pins the 2026-06-08 fix to create_standard. Before that fix, the
    code did `standard_form.text = original_form.text`, which only
    copies text and silently dropped mixed-content children like
    <UNCLEAR/>. After --copy on an original-only FORM containing only
    <UNCLEAR/>, the resulting standard FORM must also contain
    <UNCLEAR/> (not be empty), otherwise V017 fires on it under the
    new schema.
    """
    work = copy_fixture(
        fixtures_dir / "valid_original_only_with_UNCLEAR.xml", tmp_path
    )
    proc = _run_standardize(["--copy", "--corpora_path", str(tmp_path)])
    assert proc.returncode == 0, (
        f"standardize --copy exited {proc.returncode}; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )
    root = ET.parse(work).getroot()
    standard_forms = [
        f for f in root.findall(".//FORM") if f.get("kindOf") == "standard"
    ]
    assert len(standard_forms) == 1, (
        f"expected one standard FORM after --copy; got {len(standard_forms)}"
    )
    standard = standard_forms[0]
    assert standard.find("UNCLEAR") is not None, (
        f"standard FORM is missing <UNCLEAR/> child; serialization is "
        f"{ET.tostring(standard, encoding='unicode')!r}"
    )
    # And no spurious text content snuck in.
    assert (standard.text or "").strip() == "", (
        f"standard FORM should have no text content (UNCLEAR-only), got "
        f"{standard.text!r}"
    )


def test_copy_does_not_inject_whitespace_into_partial_UNCLEAR(tmp_path):
    corpus = tmp_path / "corpus"
    work = _write_corpus_xml(
        corpus,
        "partial.xml",
        '<TEXT xml:lang="pwn" dialect="Eastern"><S id="1">'
        '<FORM kindOf="original">sa izua<UNCLEAR/></FORM>'
        "</S></TEXT>",
    )
    proc = _run_standardize(["--copy", "--corpora_path", str(corpus)])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    proc = _run_standardize(["--copy", "--corpora_path", str(corpus)])
    assert proc.returncode == 0, f"second run stderr: {proc.stderr}"
    root = ET.parse(work).getroot()
    forms = root.findall(".//FORM")
    assert len(forms) == 2
    assert ["".join(form.itertext()) for form in forms] == ["sa izua", "sa izua"]
    serialized = work.read_text(encoding="utf-8")
    assert "\n    <S id=\"1\">" in serialized
    assert "\n        <FORM" in serialized
    assert "sa izua<UNCLEAR/></FORM>" in serialized


def test_errors_when_no_original_tier(tmp_path, fixtures_dir, copy_fixture):
    work = copy_fixture(fixtures_dir / "valid_no_original_tier.xml", tmp_path)
    before = work.read_text()
    proc = _run_standardize(["--copy", "--corpora_path", str(tmp_path)])
    assert proc.returncode != 0, (
        f"expected non-zero exit; got returncode={proc.returncode}, "
        f"stdout={proc.stdout!r}, stderr={proc.stderr!r}"
    )
    combined = (proc.stderr + proc.stdout).lower()
    assert "no original" in combined or "missing original" in combined, (
        f"expected error message naming the missing original tier; "
        f"got stdout={proc.stdout!r}, stderr={proc.stderr!r}"
    )
    # Atomicity: the script should not mutate the file when it errors out.
    assert work.read_text() == before, (
        "standardize.py modified the input file even though it errored on "
        "missing original tier"
    )


def _write_corpus_xml(corpus_root: Path, name: str, xml_text: str) -> Path:
    """Place a standalone XML at corpus_root/XML/<name> and return its path.

    Mirrors the layout copy_fixture produces, but lets a test control the
    TEXT xml:lang/dialect attributes inline (which drive column resolution).
    """
    xml_dir = corpus_root / "XML"
    xml_dir.mkdir(parents=True, exist_ok=True)
    path = xml_dir / name
    path.write_text(xml_text, encoding="utf-8")
    return path


def test_auto_resolves_single_dialect_to_lone_column(tmp_path):
    """Single-dialect language: dialect attribute == the language name (e.g.
    "Yami"), which is not a TSV column. Without --target_column the script must
    use the lone value column ('standard') rather than warning or erroring.

    Regression for the 2026-06 bug where a single-dialect language with
    dialect="<language name>" failed column resolution.
    """
    corpus = tmp_path / "corpus"
    work = _write_corpus_xml(
        corpus,
        "y.xml",
        '<TEXT xml:lang="tao" dialect="Yami">'
        '<S id="1"><FORM kindOf="original">amaama</FORM></S></TEXT>',
    )
    tsv = tmp_path / "single.tsv"
    tsv.write_text("original\tstandard\na\tA\n", encoding="utf-8")
    proc = _run_standardize(["--tsv_path", str(tsv), "--corpora_path", str(corpus)])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    combined = (proc.stdout + proc.stderr).lower()
    assert "not found" not in combined, (
        f"single-dialect run should not warn about a missing dialect column: {combined!r}"
    )
    # The 'standard' column was applied: a -> A.
    assert _standard_forms(work) == ["AmAAmA"]


def test_auto_resolves_multi_dialect_to_dialect_column(tmp_path):
    """Multi-dialect language: the dialect attribute selects the column. With
    dialect="Coastal" and a TSV carrying both 'Coastal' and 'standard', the
    Coastal column must win over the 'standard' fallback.
    """
    corpus = tmp_path / "corpus"
    work = _write_corpus_xml(
        corpus,
        "a.xml",
        '<TEXT xml:lang="ami" dialect="Coastal">'
        '<S id="1"><FORM kindOf="original">amaama</FORM></S></TEXT>',
    )
    tsv = tmp_path / "multi.tsv"
    tsv.write_text("original\tCoastal\tstandard\na\tC\tA\n", encoding="utf-8")
    proc = _run_standardize(["--tsv_path", str(tsv), "--corpora_path", str(corpus)])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    assert "Using dialect-specific column: Coastal" in proc.stdout, (
        f"expected Coastal column selection; stdout: {proc.stdout!r}"
    )
    # The Coastal column was applied (a -> C), not 'standard' (a -> A).
    assert _standard_forms(work) == ["CmCCmC"]


# --- Accent handling during standardization -----------------------------------
#
# No Formosan orthography uses accents phonemically, so an accented vowel in the
# source (e.g. Glosbe marks stress: "máduk") is just the plain vowel wearing a
# diacritic. If the standard tier keeps the accent, a conversion-table entry
# keyed on the plain vowel never matches. standardize.py must therefore strip
# accents from the standard tier *before* applying the mapping — while leaving
# the original tier's spelling (accents included) untouched.

# A fake conversion table that rewrites every vowel to a distinct *unaccented*
# vowel. Targets are uppercase so the sequential substring .replace() in
# apply_standard cannot chain (an uppercase target is never a lowercase source).
_VOWEL_SHIFT_TSV = "original\tstandard\na\tU\ne\tO\ni\tA\no\tE\nu\tI\n"

# Accented lowercase vowels (acute on a e i o u, plus a breve u) — every vowel
# the table rewrites, each carrying a diacritic. If accents are stripped first,
# each becomes its plain vowel and then the table applies.
_ACCENTED_PHRASE = "áéíóú ŭ"
_EXPECTED_STANDARD = "UOAEI I"  # á→a→U é→e→O í→i→A ó→o→E ú→u→I  ŭ→u→I


def test_accents_are_stripped_before_mapping_is_applied(tmp_path):
    """An accented vowel must be standardized as if it were the plain vowel:
    the accent is removed, then the conversion table maps the bare vowel."""
    corpus = tmp_path / "corpus"
    work = _write_corpus_xml(
        corpus,
        "accented.xml",
        '<TEXT xml:lang="ami" dialect="unknown">'
        f'<S id="1"><FORM kindOf="original">{_ACCENTED_PHRASE}</FORM></S></TEXT>',
    )
    tsv = tmp_path / "vowel_shift.tsv"
    tsv.write_text(_VOWEL_SHIFT_TSV, encoding="utf-8")
    proc = _run_standardize(["--tsv_path", str(tsv), "--corpora_path", str(corpus)])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    assert _standard_forms(work) == [_EXPECTED_STANDARD], (
        "standard tier should have accents stripped AND the table applied to the "
        f"bare vowels; got {_standard_forms(work)!r}"
    )
    # No combining accent survives in the standard tier.
    import unicodedata
    decomposed = unicodedata.normalize("NFD", _standard_forms(work)[0])
    assert "́" not in decomposed and "̆" not in decomposed, (
        "standard tier still contains a combining acute/breve accent"
    )


def test_explicit_diacritic_letter_mapping_precedes_accent_cleanup(tmp_path):
    corpus = tmp_path / "corpus"
    work = _write_corpus_xml(
        corpus,
        "saisiyat.xml",
        '<TEXT xml:lang="xsy" dialect="Saisiyat">'
        '<S id="1"><FORM kindOf="original">söwäy má</FORM></S></TEXT>',
    )
    tsv = tmp_path / "source_letters.tsv"
    tsv.write_text(
        "original\tstandard\nö\to:e\nä\tae\na\tA\n",
        encoding="utf-8",
    )

    proc = _run_standardize(
        ["--tsv_path", str(tsv), "--corpora_path", str(corpus)]
    )

    assert proc.returncode == 0, proc.stderr
    assert _standard_forms(work) == ["so:ewaey mA"]


@pytest.mark.parametrize(
    ("lang", "dialect", "table", "source", "expected"),
    [
        ("xsy", "Saisiyat", "Saisiyat_Tsuchida_113.tsv", "βŋöäʔš’", "bngo:eae'S"),
        ("bnn", "Zhuoqun", "Bunun_Huang_113.tsv", "ʔaðaŋ", "'azang"),
        ("dru", "Wutai", "Rukai_Li_113.tsv", "a:TDeꟈə", "aatrdrédhe"),
        ("pzh", "Pazeh", "Pazeh_Tsuchida_113.tsv", "du?ay", "du'ay"),
        ("trv", "Tegudaya", "Seediq_Ochiai_113.tsv", "ŋuy", "nguy"),
    ],
)
def test_reviewed_source_conversion_tables(
    tmp_path,
    lang: str,
    dialect: str,
    table: str,
    source: str,
    expected: str,
):
    corpus = tmp_path / "corpus"
    work = _write_corpus_xml(
        corpus,
        "source.xml",
        f'<TEXT xml:lang="{lang}" dialect="{dialect}">'
        f'<S id="1"><FORM kindOf="original">{source}</FORM></S></TEXT>',
    )

    proc = _run_standardize(
        [
            "--tsv_path",
            str(CONVERSION_TABLES / table),
            "--corpora_path",
            str(corpus),
        ]
    )

    assert proc.returncode == 0, proc.stderr
    assert _standard_forms(work) == [expected]


def test_standardization_leaves_original_tier_accents_untouched(tmp_path):
    """Stripping accents is a standard-tier operation only: the original tier
    must keep its exact source spelling, diacritics and all."""
    corpus = tmp_path / "corpus"
    work = _write_corpus_xml(
        corpus,
        "accented.xml",
        '<TEXT xml:lang="ami" dialect="unknown">'
        f'<S id="1"><FORM kindOf="original">{_ACCENTED_PHRASE}</FORM></S></TEXT>',
    )
    tsv = tmp_path / "vowel_shift.tsv"
    tsv.write_text(_VOWEL_SHIFT_TSV, encoding="utf-8")
    proc = _run_standardize(["--tsv_path", str(tsv), "--corpora_path", str(corpus)])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    assert _original_forms(work) == [_ACCENTED_PHRASE], (
        "original tier must be byte-for-byte preserved (accents included); "
        f"got {_original_forms(work)!r}"
    )


# --- --remove_accents mode: copy + delete accents (no TSV, no dialectal conv) --
#
# For a corpus whose dialect is unknown or mixed we cannot apply a dialect-
# specific conversion table, but we can still produce a standard tier by
# removing accents (the one dialect-independent normalization, since no Formosan
# orthography uses accents phonemically). --remove_accents is that mode: like
# --copy, but it deletes accents from the standard tier.


def test_remove_accents_mode_deletes_accents_without_a_tsv(tmp_path):
    """--remove_accents creates the standard tier as the original with accents
    removed, requiring no TSV and doing no dialectal letter conversion."""
    corpus = tmp_path / "corpus"
    work = _write_corpus_xml(
        corpus,
        "acc.xml",
        '<TEXT xml:lang="trv" dialect="Truku">'
        '<S id="1"><FORM kindOf="original">máduk dálix dourŭk</FORM></S></TEXT>',
    )
    proc = _run_standardize(["--remove_accents", "--corpora_path", str(corpus)])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    # accents gone; every base letter (including o/u) left exactly as written
    assert _standard_forms(work) == ["maduk dalix douruk"], (
        f"expected accent-free copy with no letter conversion; got {_standard_forms(work)!r}"
    )


def test_remove_accents_mode_leaves_original_tier_untouched(tmp_path):
    """--remove_accents is a standard-tier operation only; original keeps accents."""
    corpus = tmp_path / "corpus"
    work = _write_corpus_xml(
        corpus,
        "acc.xml",
        '<TEXT xml:lang="trv" dialect="Truku">'
        '<S id="1"><FORM kindOf="original">máduk dálix</FORM></S></TEXT>',
    )
    proc = _run_standardize(["--remove_accents", "--corpora_path", str(corpus)])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    assert _original_forms(work) == ["máduk dálix"]


# --- Capital-letter variant derivation via the source orthography profile -----
#
# standardize.py applies conversion-table rules with literal, case-sensitive
# str.replace, so a rule "o -> u" never converts sentence-initial "O". These
# tests wire derive_case_variants into --tsv_path mode: when the table's
# filename resolves to a real source profile, rules are expanded with
# Title-case/ALL-CAPS variants (suppressed where the profile declares the
# capital a distinct phonemic grapheme). Non-conforming filenames or a
# missing profile fall back to the exact old (no-derivation) behavior.


def _write_case_fixture(tmp_path, xml_text):
    """Build Orthographies/{ConversionTables,Ortho94}/ + a collection root.

    Table rules: o->u, ng->ŋ, t->c. Profile declares T a distinct
    grapheme, so t must not spawn a T variant.
    Returns (table_path, collection_root, xml_path).
    """
    conv = tmp_path / "Orthographies" / "ConversionTables"
    prof = tmp_path / "Orthographies" / "Ortho94"
    conv.mkdir(parents=True)
    prof.mkdir(parents=True)
    table = conv / "Amis_94_113.tsv"
    table.write_text(
        "original\tstandard\no\tu\nng\tŋ\nt\tc\n", encoding="utf-8"
    )
    prof.joinpath("Amis.tsv").write_text(
        "letter\tstandard\nT\tʈ\no\to\nng\tŋ\nt\tt\n",
        encoding="utf-8",
    )
    collection = tmp_path / "collection"
    xml_dir = collection / "XML"
    xml_dir.mkdir(parents=True)
    xml_path = xml_dir / "doc.xml"
    xml_path.write_text(xml_text, encoding="utf-8")
    return table, collection, xml_path


_CASE_XML = (
    '<?xml version="1.0"?>\n'
    '<TEXT id="t" xml:lang="ami">\n'
    '  <S id="s1"><FORM kindOf="original">O to ngi NGA Ti</FORM></S>\n'
    "</TEXT>\n"
)


def test_case_variants_applied_from_conforming_table(tmp_path):
    table, collection, xml_path = _write_case_fixture(tmp_path, _CASE_XML)
    proc = _run_standardize([
        "--tsv_path", str(table),
        "--target_column", "standard",
        "--corpora_path", str(collection),
    ])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    # o->u converts 'o' and (derived) 'O'; ng->ŋ converts 'ngi' and
    # (derived ALL-CAPS) 'NGA' -> 'ŊA'; t->c converts lowercase 't'
    # ('to' became 'tu' after o->u, then 'cu') but the profile's phonemic
    # 'T' in 'Ti' must survive untouched.
    assert _standard_forms(xml_path) == ["U cu ŋi ŊA Ti"]


def test_nonconforming_table_name_warns_and_derives_nothing(tmp_path):
    table, collection, xml_path = _write_case_fixture(tmp_path, _CASE_XML)
    plain = table.with_name("tiny_mapping.tsv")
    table.rename(plain)
    proc = _run_standardize([
        "--tsv_path", str(plain),
        "--target_column", "standard",
        "--corpora_path", str(collection),
    ])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    assert "Warning:" in proc.stdout and "NOT be derived" in proc.stdout
    # Status quo: lowercase rules apply, capitals pass through.
    assert _standard_forms(xml_path) == ["O cu ŋi NGA Ti"]


def test_missing_profile_warns_and_derives_nothing(tmp_path):
    table, collection, xml_path = _write_case_fixture(tmp_path, _CASE_XML)
    (tmp_path / "Orthographies" / "Ortho94" / "Amis.tsv").unlink()
    proc = _run_standardize([
        "--tsv_path", str(table),
        "--target_column", "standard",
        "--corpora_path", str(collection),
    ])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    assert "Warning:" in proc.stdout and "NOT be derived" in proc.stdout
    assert _standard_forms(xml_path) == ["O cu ŋi NGA Ti"]


def test_profile_missing_letter_column_warns_and_derives_nothing(tmp_path):
    """A present-but-malformed profile (no 'letter' column) must degrade
    the same way a missing profile does, not silently derive with zero
    suppression."""
    table, collection, xml_path = _write_case_fixture(tmp_path, _CASE_XML)
    (tmp_path / "Orthographies" / "Ortho94" / "Amis.tsv").write_text(
        "grapheme\tstandard\nT\tʈ\no\to\nng\tŋ\nt\tt\n",
        encoding="utf-8",
    )
    proc = _run_standardize([
        "--tsv_path", str(table),
        "--target_column", "standard",
        "--corpora_path", str(collection),
    ])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    assert "Warning:" in proc.stdout and "NOT be derived" in proc.stdout
    assert "not found" not in proc.stdout
    # Status quo: lowercase rules apply, capitals pass through.
    assert _standard_forms(xml_path) == ["O cu ŋi NGA Ti"]


# --- Null-morpheme unit removal -----------------------------------------------
#
# Null morphemes are written as ∅ (U+2205) in both original and standard tiers.
# In the S-level standard FORM, they are meaningless — a null morpheme position
# in a sentence-level representation adds no information and breaks downstream
# tokenization. They are removed as a unit: ∅- (prefix marker + hyphen),
# -∅ (suffix marker + hyphen), or standalone ∅ (inter-word null).
# W/M tiers retain ∅ because the morpheme tier is where a null is meaningful.
# --copy mode is a pure duplication and must never remove anything.

_NULL_XML = (
    '<TEXT id="T_NULL" citation="t" BibTeX_citation="@t{t}" copyright="t" '
    'xml:lang="szy" dialect="unknown">'
    '<S id="1"><FORM kindOf="original">∅-sitangah kero-∅ ∅ misa</FORM>'
    '<W id="1-W1"><FORM kindOf="original">∅-sitangah</FORM>'
    '<M id="1-W1-M1"><FORM kindOf="original">∅</FORM></M>'
    '<M id="1-W1-M2"><FORM kindOf="original">sitangah</FORM></M>'
    "</W></S></TEXT>"
)


def test_remove_accents_strips_null_units_from_S_standard_only(tmp_path):
    """Non-copy modes remove null units (∅-, -∅, standalone ∅) from the
    S-level standard FORM before any other transformation; W/M standard
    FORMs and the original tier retain them."""
    corpus = tmp_path / "corpus"
    work = _write_corpus_xml(corpus, "n.xml", _NULL_XML)
    proc = _run_standardize(["--remove_accents", "--corpora_path", str(corpus)])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    root = ET.parse(work).getroot()
    assert root.findtext("./S/FORM[@kindOf='standard']") == "sitangah kero misa"
    assert root.findtext("./S/W/FORM[@kindOf='standard']") == "∅-sitangah"
    assert root.findtext("./S/W/M/FORM[@kindOf='standard']") == "∅"
    assert (
        root.findtext("./S/FORM[@kindOf='original']") == "∅-sitangah kero-∅ ∅ misa"
    )


def test_tsv_mode_strips_null_units_from_S_standard(tmp_path):
    corpus = tmp_path / "corpus"
    work = _write_corpus_xml(corpus, "n.xml", _NULL_XML)
    tsv = tmp_path / "map.tsv"
    tsv.write_text("original\ttarget\nkero\tkiro\n", encoding="utf-8")
    proc = _run_standardize([
        "--tsv_path", str(tsv),
        "--target_column", "target",
        "--corpora_path", str(corpus),
    ])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    root = ET.parse(work).getroot()
    assert root.findtext("./S/FORM[@kindOf='standard']") == "sitangah kiro misa"
    assert root.findtext("./S/W/FORM[@kindOf='standard']") == "∅-sitangah"
    assert root.findtext("./S/W/M/FORM[@kindOf='standard']") == "∅"


def test_copy_mode_retains_null_units_in_S_standard(tmp_path):
    """--copy is a pure duplication: the standard tier keeps null units."""
    corpus = tmp_path / "corpus"
    work = _write_corpus_xml(corpus, "n.xml", _NULL_XML)
    proc = _run_standardize(["--copy", "--corpora_path", str(corpus)])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    root = ET.parse(work).getroot()
    assert (
        root.findtext("./S/FORM[@kindOf='standard']") == "∅-sitangah kero-∅ ∅ misa"
    )

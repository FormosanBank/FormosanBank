"""Quote/glottal correction inside clean_xml (original tier).

clean_xml is run via subprocess against a tmp corpus. A tiny attestation
dictionary is written into a tmp reference dir passed with --reference_dir,
so tests do not depend on the full generated Amis dictionary.
"""
import subprocess
import sys
from pathlib import Path

from lxml import etree

CLEAN_XML = Path(__file__).resolve().parents[2] / "QC" / "cleaning" / "clean_xml.py"


def _run(corpora_path, reference_dir):
    return subprocess.run(
        [sys.executable, str(CLEAN_XML),
         "--corpora_path", str(corpora_path),
         "--reference_dir", str(reference_dir)],
        capture_output=True, text=True)


def _write_dict(reference_dir, language, words):
    d = reference_dir / language
    d.mkdir(parents=True)
    (d / "attestation.txt").write_text("\n".join(words) + "\n", encoding="utf-8")


def _form_originals(xml_path):
    tree = etree.parse(str(xml_path))
    return [f.text or "" for f in tree.findall(".//S/FORM")
            if f.get("kindOf") == "original"]


def _warnings_rows(corpora_path):
    csv_path = corpora_path / "cleaner_warnings.csv"
    if not csv_path.exists():
        return []
    import csv as _csv
    with open(csv_path, encoding="utf-8") as fh:
        return list(_csv.DictReader(fh))


def _make_corpus(tmp_path, sub, form_original, transl=None):
    xdir = tmp_path / sub
    xdir.mkdir(parents=True)
    transl_xml = f'<TRANSL xml:lang="eng">{transl}</TRANSL>' if transl else ""
    (xdir / "t.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<TEXT id="t" citation="c" copyright="p" xml:lang="ami">\n'
        f'  <S id="1"><FORM kindOf="original">{form_original}</FORM>{transl_xml}</S>\n'
        '</TEXT>\n', encoding="utf-8")
    return xdir


def test_quotation_pair_rewritten_to_doublequote(tmp_path):
    ref = tmp_path / "reference"
    _write_dict(ref, "Amis", ["faloco'", "loma'", "'ayam", "romi'ad"])
    # 'zzq (after ':') ... wqx' -> neither attested, opener after punct ->
    # QUOTATION. zzq/wqx are synthetic tokens, never in any real dictionary.
    _make_corpus(tmp_path, "Corpora/Toy/XML", "pasowal: 'zzq wqx'")
    proc = _run(tmp_path, ref)
    assert proc.returncode == 0, proc.stderr
    (orig,) = _form_originals(tmp_path / "Corpora/Toy/XML/t.xml")
    assert "'" not in orig.split(":")[1]         # both quotes converted
    assert orig.count('"') == 2
    rows = _warnings_rows(tmp_path)
    assert sum(r["rule_id"] == "c024" for r in rows) == 2


def test_glottal_pair_left_intact_no_warning(tmp_path):
    ref = tmp_path / "reference"
    _write_dict(ref, "Amis", ["faloco'", "loma'", "'ayam", "romi'ad", "cima"])
    _make_corpus(tmp_path, "Corpora/Toy/XML", "o 'ayam ko faloco' iso")
    proc = _run(tmp_path, ref)
    assert proc.returncode == 0, proc.stderr
    (orig,) = _form_originals(tmp_path / "Corpora/Toy/XML/t.xml")
    assert orig == "o 'ayam ko faloco' iso"
    rows = _warnings_rows(tmp_path)
    assert not any(r["rule_id"] in ("c023", "c024") for r in rows)


def test_ambiguous_emits_c023(tmp_path):
    ref = tmp_path / "reference"
    _write_dict(ref, "Amis", ["faloco'", "'ayam"])
    _make_corpus(tmp_path, "Corpora/Toy/XML", "'ayam faloco',")
    proc = _run(tmp_path, ref)
    assert proc.returncode == 0, proc.stderr
    (orig,) = _form_originals(tmp_path / "Corpora/Toy/XML/t.xml")
    assert orig == "'ayam faloco',"                 # unchanged
    rows = _warnings_rows(tmp_path)
    assert sum(r["rule_id"] == "c023" for r in rows) == 2


def test_wikipedia_suppresses_c023(tmp_path):
    ref = tmp_path / "reference"
    _write_dict(ref, "Amis", ["faloco'", "'ayam"])
    _make_corpus(tmp_path, "Corpora/Wikipedias/XML/Amis", "'ayam faloco',")
    proc = _run(tmp_path, ref)
    assert proc.returncode == 0, proc.stderr
    rows = _warnings_rows(tmp_path)
    assert not any(r["rule_id"] == "c023" for r in rows)


def test_transl_no_quotes_leaves_form_intact(tmp_path):
    ref = tmp_path / "reference"
    _write_dict(ref, "Amis", ["faloco'", "'ayam"])
    # Would be QUOTATION on its own, but the TRANSL has no quotes -> all glottal.
    _make_corpus(tmp_path, "Corpora/Toy/XML", "pasowal: 'zzq wqx'",
                 transl="he spoke")
    proc = _run(tmp_path, ref)
    assert proc.returncode == 0, proc.stderr
    (orig,) = _form_originals(tmp_path / "Corpora/Toy/XML/t.xml")
    assert orig == "pasowal: 'zzq wqx'"             # TRANSL first pass -> glottal
    rows = _warnings_rows(tmp_path)
    assert not any(r["rule_id"] in ("c023", "c024") for r in rows)


def test_stranded_glottal_whitespace_repaired_c025(tmp_path):
    ref = tmp_path / "reference"
    _write_dict(ref, "Amis", ["faloco'", "'ayam"])
    # "o ' ayam ko faloco ' iso" -> spaces removed -> "o 'ayam ko faloco' iso"
    _make_corpus(tmp_path, "Corpora/Toy/XML", "o ' ayam ko faloco ' iso")
    proc = _run(tmp_path, ref)
    assert proc.returncode == 0, proc.stderr
    (orig,) = _form_originals(tmp_path / "Corpora/Toy/XML/t.xml")
    assert orig == "o 'ayam ko faloco' iso"
    rows = _warnings_rows(tmp_path)
    assert sum(r["rule_id"] == "c025" for r in rows) == 2
    assert not any(r["rule_id"] == "c023" for r in rows)


def test_missing_dictionary_is_noop(tmp_path):
    ref = tmp_path / "reference"       # no Amis/ subdir
    ref.mkdir()
    _make_corpus(tmp_path, "Corpora/Toy/XML", "pasowal: 'cima tayni'")
    proc = _run(tmp_path, ref)
    assert proc.returncode == 0, proc.stderr
    (orig,) = _form_originals(tmp_path / "Corpora/Toy/XML/t.xml")
    assert orig == "pasowal: 'cima tayni'"          # untouched
    rows = _warnings_rows(tmp_path)
    assert not any(r["rule_id"] in ("c023", "c024") for r in rows)

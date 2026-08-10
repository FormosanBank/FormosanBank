"""Quote/glottal correction inside clean_xml (original tier).

clean_xml is run via subprocess against a tmp corpus. A tiny attestation
dictionary is written into a tmp reference dir passed with --reference_dir,
so tests do not depend on the full generated Amis dictionary.

Log split per POL-035 merge reconciliation (2026-08-10): actual rewrites
(c031 corrected, c032 stranded-repair) go to the durable, committed
quote_corrections.csv; ambiguous audit flags (c030) stay in the ephemeral
cleaner_warnings.csv (POL-033). Codes renumbered from the branch's
c024/c025/c023 to avoid colliding with existing cleaner rule numbers.
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


def _rows(corpora_path, name):
    csv_path = corpora_path / name
    if not csv_path.exists():
        return []
    import csv as _csv
    with open(csv_path, encoding="utf-8") as fh:
        return list(_csv.DictReader(fh))


def _warnings_rows(corpora_path):
    return _rows(corpora_path, "cleaner_warnings.csv")


def _corrections_rows(corpora_path):
    return _rows(corpora_path, "quote_corrections.csv")


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
    # Rule 2: one word-initial ' + one ' after a period ('.' is unambiguous).
    _make_corpus(tmp_path, "Corpora/Toy/XML", "'zzq wqx.'")
    proc = _run(tmp_path, ref)
    assert proc.returncode == 0, proc.stderr
    (orig,) = _form_originals(tmp_path / "Corpora/Toy/XML/t.xml")
    assert orig == '"zzq wqx."'
    rows = _corrections_rows(tmp_path)
    assert sum(r["rule_id"] == "c031" for r in rows) == 2


def test_glottal_pair_left_intact_no_warning(tmp_path):
    ref = tmp_path / "reference"
    _write_dict(ref, "Amis", ["faloco'", "loma'", "'ayam", "romi'ad", "cima"])
    _make_corpus(tmp_path, "Corpora/Toy/XML", "o 'ayam ko faloco' iso")
    proc = _run(tmp_path, ref)
    assert proc.returncode == 0, proc.stderr
    (orig,) = _form_originals(tmp_path / "Corpora/Toy/XML/t.xml")
    assert orig == "o 'ayam ko faloco' iso"
    assert not any(r["rule_id"] == "c030" for r in _warnings_rows(tmp_path))
    assert _corrections_rows(tmp_path) == []


def test_ambiguous_emits_c030_warning(tmp_path):
    ref = tmp_path / "reference"
    _write_dict(ref, "Amis", ["faloco'", "'ayam"])
    # Both boundary words attested + a quoting TRANSL -> no rule fires, but the
    # unplaced ' are flagged c030 (audit, ephemeral warning), never edited.
    _make_corpus(tmp_path, "Corpora/Toy/XML", "'ayam faloco'", transl='he said "x"')
    proc = _run(tmp_path, ref)
    assert proc.returncode == 0, proc.stderr
    (orig,) = _form_originals(tmp_path / "Corpora/Toy/XML/t.xml")
    assert orig == "'ayam faloco'"                   # unchanged
    rows = _warnings_rows(tmp_path)
    assert sum(r["rule_id"] == "c030" for r in rows) == 2
    assert _corrections_rows(tmp_path) == []


def test_wikipedia_suppresses_c030(tmp_path):
    ref = tmp_path / "reference"
    _write_dict(ref, "Amis", ["faloco'", "'ayam"])
    _make_corpus(tmp_path, "Corpora/Wikipedias/XML/Amis", "'ayam faloco',")
    proc = _run(tmp_path, ref)
    assert proc.returncode == 0, proc.stderr
    rows = _warnings_rows(tmp_path)
    assert not any(r["rule_id"] == "c030" for r in rows)


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
    assert not any(r["rule_id"] == "c030" for r in _warnings_rows(tmp_path))
    assert _corrections_rows(tmp_path) == []


def test_stranded_glottal_whitespace_repaired_c032(tmp_path):
    ref = tmp_path / "reference"
    _write_dict(ref, "Amis", ["faloco'", "'ayam"])
    # floating ' -> remove the space so 'zzq is word-initial and Rule 2 fires.
    _make_corpus(tmp_path, "Corpora/Toy/XML", "x ' zzq wqx.'")
    proc = _run(tmp_path, ref)
    assert proc.returncode == 0, proc.stderr
    (orig,) = _form_originals(tmp_path / "Corpora/Toy/XML/t.xml")
    assert orig == 'x "zzq wqx."'
    rows = _corrections_rows(tmp_path)
    assert sum(r["rule_id"] == "c032" for r in rows) == 1
    assert not any(r["rule_id"] == "c030" for r in _warnings_rows(tmp_path))


def test_missing_dictionary_is_noop(tmp_path):
    ref = tmp_path / "reference"       # no Amis/ subdir
    ref.mkdir()
    _make_corpus(tmp_path, "Corpora/Toy/XML", "pasowal: 'cima tayni'")
    proc = _run(tmp_path, ref)
    assert proc.returncode == 0, proc.stderr
    (orig,) = _form_originals(tmp_path / "Corpora/Toy/XML/t.xml")
    assert orig == "pasowal: 'cima tayni'"          # untouched
    assert not any(r["rule_id"] == "c030" for r in _warnings_rows(tmp_path))
    assert _corrections_rows(tmp_path) == []


def test_corrections_log_is_durable_across_runs(tmp_path):
    """quote_corrections.csv is a committed log (POL-035): a later run
    that corrects nothing must neither delete it nor lose its rows."""
    ref = tmp_path / "reference"
    _write_dict(ref, "Amis", ["faloco'", "loma'", "'ayam", "romi'ad"])
    _make_corpus(tmp_path, "Corpora/Toy/XML", "'zzq wqx.'")
    assert _run(tmp_path, ref).returncode == 0
    first = _corrections_rows(tmp_path)
    assert len(first) == 2

    # Second run: text already corrected, nothing new to log.
    assert _run(tmp_path, ref).returncode == 0
    assert _corrections_rows(tmp_path) == first

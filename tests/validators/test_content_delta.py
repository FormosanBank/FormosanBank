"""content_delta: removed, renamed or relabelled published content is red (POL-037, POL-051)."""
from pathlib import Path

from QC.validation.content_delta import compare, inventory

TEXT = ('<TEXT id="{tid}" xml:lang="ami" dialect="{dialect}" copyright="{cp}" citation="c" BibTeX_citation="b">{body}</TEXT>')


def _s(sid, text, audio=False, w=0):
    extra = ('<AUDIO file="a.mp3" start="0" end="1"/>' if audio else "") + "".join(
        f'<W id="{sid}w{i}"><FORM kindOf="original">x</FORM><TRANSL xml:lang="eng">x</TRANSL>'
        f'<M id="{sid}w{i}m0"><FORM kindOf="original">x</FORM></M></W>' for i in range(w))
    return (f'<S id="{sid}"><FORM kindOf="original">{text}</FORM><FORM kindOf="standard">{text}</FORM>'
            f'<PHON kindOf="standard">{text}</PHON><TRANSL xml:lang="eng">t</TRANSL>{extra}</S>')


def _tree(root: Path, corpus: str, files: dict) -> Path:
    xml_dir = root / corpus / "XML"
    xml_dir.mkdir(parents=True, exist_ok=True)
    for name, xml in files.items():
        (xml_dir / name).write_text(xml, encoding="utf-8")
    return root


def _base(tmp_path):
    return _tree(tmp_path / "base", "C", {
        "t1.xml": TEXT.format(tid="t1", dialect="Coastal", cp="CC BY-NC 4.0",
                              body=_s("S1", "Maolah kako.", audio=True, w=2) + _s("S2", "Tayra ko wawa.", audio=True)),
        "t2.xml": TEXT.format(tid="t2", dialect="Coastal", cp="CC BY-NC 4.0", body=_s("S1", "O wawa.")),
    })


def test_identical_trees_report_nothing(tmp_path):
    base = _base(tmp_path)
    head = _tree(tmp_path / "head", "C", {p.name: p.read_text(encoding="utf-8") for p in (base / "C" / "XML").glob("*.xml")})
    assert compare(inventory(base), inventory(head)) == []


def test_removed_text_and_sentence_and_count_drops_are_red(tmp_path):
    base = _base(tmp_path)
    head = _tree(tmp_path / "head", "C", {
        "t1.xml": TEXT.format(tid="t1", dialect="Coastal", cp="CC BY-NC 4.0",
                              body=_s("S1", "Maolah kako.", audio=False, w=0)),   # S2 gone, AUDIO and W/M gone
    })                                                                                # t2 gone
    lines = [c.line() for c in compare(inventory(base), inventory(head))]
    assert "RED C: TEXT ids removed ×1 — t2" in lines
    assert "RED C: S removed ×1 — t1/S2" in lines
    assert any(l.startswith("RED C: AUDIO count down ×2") for l in lines), lines
    assert any(l.startswith("RED C: W count down ×2") for l in lines) and any(l.startswith("RED C: M count down ×2") for l in lines)
    assert all(c.red for c in compare(inventory(base), inventory(head)))


def test_renamed_text_and_renumbered_sentences_are_recognised_by_content(tmp_path):
    base = _base(tmp_path)
    head = _tree(tmp_path / "head", "C", {
        "x.xml": TEXT.format(tid="t1-new", dialect="Coastal", cp="CC BY-NC 4.0",
                             body=_s("S1", "Maolah kako.", audio=True, w=2) + _s("S2", "Tayra ko wawa.", audio=True)),
        "t2.xml": TEXT.format(tid="t2", dialect="Coastal", cp="CC BY-NC 4.0", body=_s("S9", "O wawa.")),
    })
    lines = [c.line() for c in compare(inventory(base), inventory(head))]
    assert "RED C: TEXT ids renamed (same sentences) ×1 — t1 → t1-new" in lines
    assert "RED C: S ids renumbered (same text, new id) ×1 — POL-037: ids are stable" in lines
    assert not any("removed" in l for l in lines), lines


def test_relabelled_dialect_and_copyright_are_red(tmp_path):
    base = _base(tmp_path)
    head = _tree(tmp_path / "head", "C", {
        "t1.xml": TEXT.format(tid="t1", dialect="unknown", cp="CC BY-NC 4.0",
                              body=_s("S1", "Maolah kako.", audio=True, w=2) + _s("S2", "Tayra ko wawa.", audio=True)),
        "t2.xml": TEXT.format(tid="t2", dialect="Coastal", cp="CC BY 4.0", body=_s("S1", "O wawa.")),
    })
    lines = [c.line() for c in compare(inventory(base), inventory(head))]
    assert "RED C: TEXT/@dialect changed ×1 — t1: Coastal → unknown" in lines
    assert "RED C: TEXT/@copyright changed ×1 — t2: 'CC BY-NC 4.0' → 'CC BY 4.0'" in lines


def test_additions_are_reported_but_not_red(tmp_path):
    base = _base(tmp_path)
    head = _tree(tmp_path / "head", "C", {p.name: p.read_text(encoding="utf-8") for p in (base / "C" / "XML").glob("*.xml")})
    (head / "C" / "XML" / "t3.xml").write_text(TEXT.format(tid="t3", dialect="Coastal", cp="CC BY-NC 4.0", body=_s("S1", "New.")), encoding="utf-8")
    _tree(head, "D", {"d.xml": TEXT.format(tid="d", dialect="Thao", cp="CC BY 4.0", body=_s("S1", "x"))})
    changes = compare(inventory(base), inventory(head))
    assert [c.line() for c in changes] == ["    C: TEXT ids added ×1 — t3", "    D: corpus added ×1 — 1 TEXT(s)"]
    assert not any(c.red for c in changes)


def test_corpus_filter_limits_the_inventory(tmp_path):
    base = _base(tmp_path)
    _tree(base, "D", {"d.xml": TEXT.format(tid="d", dialect="Thao", cp="CC BY 4.0", body=_s("S1", "x"))})
    assert set(inventory(base)) == {"C", "D"}
    assert set(inventory(base, {"D"})) == {"D"}

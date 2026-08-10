import importlib.util
from pathlib import Path

_MODULE = (Path(__file__).resolve().parents[2] / "QC" / "utilities"
           / "build_attestation_dict.py")
_spec = importlib.util.spec_from_file_location("build_attestation_dict", _MODULE)
bad = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bad)


def test_build_set_unions_singleword_and_frequent_interior():
    # sentence tokenizations (already whitespace-split):
    forms = [
        ["faloco'"],                       # single-word S-FORM -> included
        ["o", "wawa", "no", "tao"],        # interior: wawa, no
        ["o", "wawa", "ko", "'ayam"],      # interior: wawa, ko
        ["a", "wawa", "sa", "ira"],        # interior: wawa, sa
    ]
    result = bad.build_attestation_set(forms, min_freq=3)
    assert "faloco'" in result          # single-word S-FORM (any length)
    assert "wawa" in result             # interior freq 3 >= 3
    assert "no" not in result           # interior freq 1 < 3
    assert "o" not in result            # sentence-initial, never counted
    assert "tao" not in result          # sentence-final, never counted


def test_build_set_is_casefolded():
    forms = [["Wawa"], ["o", "WAWA", "ko", "x"], ["a", "wawa", "sa", "y"]]
    result = bad.build_attestation_set(forms, min_freq=2)
    assert "wawa" in result
    assert "Wawa" not in result and "WAWA" not in result


def test_generator_writes_reference_file(tmp_path):
    # Build a tiny Amis corpus and run the generator end-to-end.
    corp = tmp_path / "Corpora" / "Toy" / "XML"
    corp.mkdir(parents=True)
    (corp / "t.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<TEXT id="t" citation="c" copyright="p" xml:lang="ami">\n'
        '  <S id="1"><FORM kindOf="original">faloco\'</FORM></S>\n'
        '  <S id="2"><FORM kindOf="original">o wawa no tao</FORM></S>\n'
        '  <S id="3"><FORM kindOf="original">o wawa ko ira</FORM></S>\n'
        '  <S id="4"><FORM kindOf="original">a wawa sa nay</FORM></S>\n'
        '</TEXT>\n', encoding="utf-8")
    ref = tmp_path / "reference"
    bad.main([
        "--language", "Amis", "--min-freq", "3",
        "--corpora_path", str(tmp_path / "Corpora"),
        "--reference_dir", str(ref),
    ])
    out = (ref / "Amis" / "attestation.txt").read_text(encoding="utf-8")
    words = out.split()
    assert "faloco'" in words
    assert "wawa" in words
    assert "no" not in words

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
        ["faloco'"],                        # single-word S-FORM -> included
        ["o", "'ayam", "no", "tao'"],       # interior: 'ayam, no
        ["o", "'ayam", "ko", "wawa"],       # interior: 'ayam, ko
        ["a", "'ayam", "sa", "ira"],        # interior: 'ayam, sa
    ]
    result = bad.build_attestation_set(forms, min_freq=3, include_interior=True)
    assert "faloco'" in result          # single-word S-FORM (any length)
    assert "'ayam" in result            # interior freq 3 >= 3, edge apostrophe
    assert "no" not in result           # interior freq 1 < 3
    assert "o" not in result            # sentence-initial, never counted
    assert "tao'" not in result         # sentence-final, never counted


def test_build_set_keeps_only_edge_apostrophe_words():
    # Only plausible Formosan words with a word-initial or word-final `'`
    # survive — nothing else can ever match a classifier lookup
    # (maintainer ruling 2026-08-11).
    forms = [
        ["wawa"],            # no apostrophe -> dropped
        ["hla'alua"],        # interior-only apostrophe -> dropped
        ["'oka'"],           # both edges -> kept
        ["kapayaka:i'"],     # final ' with length colon -> kept
        ["'afadeng/'afo"],   # slash-joined variant list -> dropped
        ["ttu%27"],          # URL-encoding residue -> dropped
        ["'aviki(日語"],     # CJK annotation -> dropped
        ["'"],               # no letters -> dropped
        ["021'"],            # digits -> dropped
    ]
    result = bad.build_attestation_set(forms)
    assert result == {"'oka'", "kapayaka:i'"}


def test_build_set_is_casefolded():
    forms = [["Wawa'"], ["o", "WAWA'", "ko", "x"], ["a", "wawa'", "sa", "y"]]
    result = bad.build_attestation_set(forms, min_freq=2, include_interior=True)
    assert "wawa'" in result
    assert "Wawa'" not in result and "WAWA'" not in result


def test_generator_writes_reference_file(tmp_path):
    # Build a tiny Amis corpus and run the generator end-to-end.
    corp = tmp_path / "Corpora" / "Toy" / "XML"
    corp.mkdir(parents=True)
    (corp / "t.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<TEXT id="t" citation="c" copyright="p" xml:lang="ami">\n'
        '  <S id="1"><FORM kindOf="original">faloco\'</FORM></S>\n'
        '  <S id="2"><FORM kindOf="original">o \'ayam no tao</FORM></S>\n'
        '  <S id="3"><FORM kindOf="original">o \'ayam ko ira</FORM></S>\n'
        '  <S id="4"><FORM kindOf="original">a \'ayam sa nay</FORM></S>\n'
        '</TEXT>\n', encoding="utf-8")
    ref = tmp_path / "reference"
    bad.main([
        "--language", "Amis", "--min-freq", "3", "--include-interior",
        "--corpora_path", str(tmp_path / "Corpora"),
        "--reference_dir", str(ref),
    ])
    out = (ref / "Amis" / "attestation.txt").read_text(encoding="utf-8")
    words = out.split()
    assert "faloco'" in words
    assert "'ayam" in words             # interior, frequent, edge apostrophe
    assert "no" not in words
    assert "ira" not in words           # no apostrophe -> filtered


def test_both_edge_words_come_from_running_text_and_consonant_glottals_go():
    # Maintainer, 2026-10-14: include words that begin AND end in ' (from any
    # position), then drop any word with ' + consonant or consonant + '.
    forms = [
        ["ka", "'aehoe'", "sahae'", "ila"],      # 'aehoe' interior, both edges
        ["'izo'"],                               # single-word, both edges
        ["o", "'madimadiay'", "ko"],              # a quoted word: ' + consonant
        ["'ayam"],                               # one edge, single word: kept
        ["kakay'"],                              # y + ' : consonant -> dropped
    ]
    result = bad.build_attestation_set(forms)
    assert {"'aehoe'", "'izo'", "'ayam"} <= result
    assert "'madimadiay'" not in result and "kakay'" not in result
    assert "sahae'" not in result                # one edge, interior: not added


def test_frequent_both_edge_words_need_50_uses_and_rare_variants():
    forms = [["'aehoe'"]] * 60 + [["aehoe'"]] * 5 + [["'izo'"]] * 49 + [["'ima'"]] * 50 + [["ima"]] * 6
    got = bad.frequent_both_edge_words(forms)
    assert got == {"'aehoe'"}     # 'izo' too rare; 'ima': 6 bare uses > 50/10


def test_consonant_headwords_are_the_one_word_forms_the_filter_removes():
    # The "attested with that spelling" exceptions for the consonant
    # preference: dictionary headwords whose ' stands next to a consonant.
    forms = [["'wacogo"], ["'aehoe'"], ["o", "'tatini", "ka"], ["kamatortoroe''omaling'"]]
    assert bad.consonant_headwords(forms) == {"'wacogo", "kamatortoroe''omaling'"}

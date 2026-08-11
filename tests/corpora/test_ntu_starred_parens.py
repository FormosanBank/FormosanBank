"""Grammaticality-parenthesis handling in the NTUFormosanCorpus parsers.

Linguistics sources use two opposite conventions that must not be conflated
with ordinary optional parentheses:

    *(X)  – X is OBLIGATORY: the sentence is ungrammatical WITHOUT X, so the
            attested sentence includes X. The content must be kept.
    (*X)  – X is FORBIDDEN: ungrammatical WITH X. Marking and content must
            both be removed.

Regression tests for the 2026-08-10 starred-parentheses audit
(claudeplans/2026-08-10-starred-parentheses-audit.md), where the parsers
deleted the obligatory verb *(malra) from a published Rukai sentence.
"""
import copy
import sys
from pathlib import Path

NTU_SCRIPTS = (
    Path(__file__).resolve().parents[2]
    / "Corpora" / "NTUFormosanCorpus" / "CodeAndDocs" / "scripts"
)
sys.path.insert(0, str(NTU_SCRIPTS))

from utils import extract_notes, resolve_ungrammatical_parens  # noqa: E402
from parse_sentences import get_sentences  # noqa: E402


# ---------------------------------------------------------------------------
# resolve_ungrammatical_parens (token-level)
# ---------------------------------------------------------------------------

def test_obligatory_paren_keeps_content():
    assert resolve_ungrammatical_parens("*(malra)") == "malra"


def test_obligatory_paren_keeps_content_in_gloss():
    assert resolve_ungrammatical_parens("*(take)") == "take"


def test_forbidden_paren_drops_content():
    assert resolve_ungrammatical_parens("(*sua)") == ""


def test_forbidden_paren_inside_larger_token():
    assert resolve_ungrammatical_parens("arivuree(*=cu/ci)=maku") == "arivuree=maku"


def test_optional_paren_is_untouched():
    assert resolve_ungrammatical_parens("(kara)") == "(kara)"


def test_mixed_optional_and_forbidden():
    assert resolve_ungrammatical_parens("(na)(*sua)") == "(na)"


def test_plain_token_is_untouched():
    assert resolve_ungrammatical_parens("karadrare.") == "karadrare."


# ---------------------------------------------------------------------------
# get_sentences (sentence-level, real Rukai Vedai record 20200529-FW-Lixing-2/2)
# ---------------------------------------------------------------------------

RUKAI_OBLIGATORY_RECORD = [
    2,
    {
        "ori": ["kay", "tatulru", "muavaevaeva", "*(malra)", "kay", "karadrare."],
        "gloss": [
            ["kay", "this", "這"],
            ["ta-tulru", "HUM-three", "人-三"],
            ["mu-a-vae-vaeva", "go-RLS-RED-one", "去-實現-重疊-一"],
            ["*(malra)", "*(take)", "*(拿)"],
            ["kay", "this", "這"],
            ["karadrare.", "bamboo.basket", "竹籃"],
        ],
        "free": ["#e Three people went and took one basket.", "#c三個人合拿一個籃子。"],
        "s_end": True,
        "iu_a_span": [None, None],
        "meta": {"type": "Sentence"},
    },
]


def test_obligatory_word_survives_into_sentence():
    sentences = get_sentences([copy.deepcopy(RUKAI_OBLIGATORY_RECORD)])
    assert len(sentences) == 1, "sentence must not be dropped as ungrammatical"
    s = sentences[0]
    assert s["ori"] == "kay tatulru muavaevaeva malra kay karadrare."
    word_forms = [w[0] for w in s["words"]]
    assert "malra" in word_forms
    malra = s["words"][word_forms.index("malra")]
    assert malra[1] == "take"
    assert malra[2] == "拿"


def test_forbidden_word_is_removed_from_sentence():
    record = copy.deepcopy(RUKAI_OBLIGATORY_RECORD)
    record[1]["ori"][3] = "(*malra)"
    record[1]["gloss"][3] = ["(*malra)", "(*take)", "(*拿)"]
    sentences = get_sentences([record])
    assert len(sentences) == 1, "sentence itself is grammatical and must be kept"
    s = sentences[0]
    assert s["ori"] == "kay tatulru muavaevaeva kay karadrare."
    assert "malra" not in [w[0] for w in s["words"]]


# ---------------------------------------------------------------------------
# extract_notes (TRANSL cleaning; nested parentheses)
# ---------------------------------------------------------------------------

def test_extract_notes_nested_parens_leave_no_remnant():
    text = "Teacher(s) hit all students. (*All teachers hit student(s).)"
    cleaned, notes = extract_notes(text)
    assert cleaned == "Teacher hit all students."
    assert notes == text


def test_extract_notes_simple_paren():
    cleaned, notes = extract_notes("All the children took fish. (*Children took all the fish.)")
    assert cleaned == "All the children took fish."
    assert notes == "All the children took fish. (*Children took all the fish.)"


def test_extract_notes_no_parens():
    cleaned, notes = extract_notes("Three people went and took one basket.")
    assert cleaned == "Three people went and took one basket."
    assert notes is None

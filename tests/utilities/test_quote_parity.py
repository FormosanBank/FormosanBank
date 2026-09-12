"""quote_parity: the translation as a witness for the FORM's quotation marks."""

from QC.utilities.classify_quotes import quote_parity

# Blust writes the root "steal" with a word-final glottal stop, which looks
# exactly like a closing quotation mark.
THAO = {"qriu'", "riu'", "q-un-riu'"}


def test_matching_marks_on_both_sides_are_balanced():
    assert (
        quote_parity("mu-tusi dai `s-m-apuk rusaw'", ["he said `to catch fish'"])[
            "verdict"
        ]
        == "balanced"
    )


def test_no_quotation_anywhere_is_balanced():
    assert quote_parity("yaku mu-nay", ["I came here"])["verdict"] == "balanced"


def test_a_form_that_opens_without_closing_is_reported():
    result = quote_parity(
        "zai-n sa i-zay `qazi ita, ug-qca ita mu-tana-utu",
        ["the elders said `Let us try to move there'"],
    )
    assert result["verdict"] == "form_unclosed"
    assert (result["form_open"], result["form_close"]) == (1, 0)


def test_a_form_that_closes_without_opening_is_reported():
    result = quote_parity(
        "uka sa lhqaribush sinapuk'.", ["there were no forest animals to catch'."]
    )
    assert result["verdict"] == "form_unopened"


def test_a_translation_missing_its_opening_mark_is_reported():
    # The PDF's text layer drops the opening glyph; the closer survives.
    assert (
        quote_parity("yaku iza ya ikahi", ["After you' (a polite deferral)"])[
            "verdict"
        ]
        == "transl_unopened"
    )


def test_an_attested_word_final_glottal_is_not_a_closing_mark():
    form = "ya qriu'-in sa aniamin, tima sa a q-un-riu'"
    assert quote_parity(form, ["Who has stolen my things?"])["verdict"] != "balanced"
    assert (
        quote_parity(form, ["Who has stolen my things?"], dictionary=THAO)["verdict"]
        == "balanced"
    )


def test_the_dictionary_does_not_apply_to_the_translation():
    # qriu' is a Thao word; an English translation is not checked against it.
    result = quote_parity("yaku mu-nay", ["he said `qriu''"], dictionary=THAO)
    assert result["transl_open"] == 1

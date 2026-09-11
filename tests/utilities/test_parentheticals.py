"""QC/utilities/parentheticals.py — what a parenthesis in a gloss actually is."""

import pytest

from QC.utilities.parentheticals import (
    INLINE,
    NOTE,
    NOTE_MARKERS,
    PAIRED,
    classify,
    pairs_with_source,
    parentheticals,
    split_in_step,
    take_notes,
)


class TestPairing:
    def test_equal_non_zero_counts_pair(self):
        # The maintainer's rule: same count means same subject, so the
        # translation's parenthesis is not the translator talking.
        assert pairs_with_source(
            "yaku m-agqaqili sa azazak (sa pagka)",
            "I was carrying a child (a chair) on my hip",
        )

    def test_a_parenthesis_on_one_side_only_does_not_pair(self):
        assert not pairs_with_source("yaku mu-nay", "I came here (yesterday)")
        assert not pairs_with_source("ata (tu) karkar-i", "Don't chew it!")

    def test_no_parentheses_anywhere_does_not_pair(self):
        assert not pairs_with_source("yaku mu-nay", "I came here")

    def test_a_paired_parenthesis_is_never_taken_as_a_note(self):
        # Long enough to trip the length rule, and paired, so it stays.
        source = "yaku m-ilu (i-say lhalhuzu a wazaqan i-nay)"
        translation = "I bathed (in the lake beside the fish trap over there)"
        assert [s.kind for s in classify(source, translation)] == [PAIRED]
        assert take_notes(source, translation) == (translation, [])

    def test_one_source_word_does_not_render_a_note(self):
        # Printed p.445 of Blust's Thao dictionary. One parenthetical a side, so
        # the counts pair - but a single bracketed `ihu` cannot be rendered by
        # six words of English about how to use the sentence. Paired, the second
        # reading came out "You will eat some rice polite invitation to someone
        # to eat".
        source = "a ma-kan (ihu) afu"
        translation = "You will eat some rice (polite invitation to someone to eat)"
        assert [s.kind for s in classify(source, translation)] == [NOTE]
        assert take_notes(source, translation) == (
            "You will eat some rice",
            ["polite invitation to someone to eat"],
        )
        assert split_in_step(source, translation) is None

    def test_a_marker_may_follow_one_clause_of_its_own(self):
        # Printed p.280 of Blust's Thao dictionary: `modern` qualifies the
        # headword, and the literal translation follows it behind a semicolon.
        # Anchoring the marker to the very start left the whole thing in the
        # gloss, so a published TRANSL read `cemetery (modern; lit. "burial
        # meadow")`.
        source = "m-in-acay a buqan"
        translation = 'cemetery (modern; lit. "burial meadow")'
        assert [s.kind for s in classify(source, translation)] == [NOTE]
        assert take_notes(source, translation) == (
            "cemetery", ['modern; lit. "burial meadow"'])

    def test_the_marker_allows_one_clause_and_no_more(self):
        # One clause before the marker, not any number of them; and a
        # semicolon on its own is not a marker.
        assert NOTE_MARKERS.match("lit. x")
        assert NOTE_MARKERS.match('modern; lit. "y"')
        assert not NOTE_MARKERS.match("one; two; lit. z")
        assert not NOTE_MARKERS.match("a cat; a dog")

    def test_one_source_word_still_pairs_with_a_short_gloss(self):
        # The scale rule is about a note's worth of English, not about every
        # bracketed word: `(sa pagka)` glossed `(a chair)` still pairs.
        source = "yaku m-agqaqili sa azazak (pagka)"
        translation = "I was carrying a child (a chair) on my hip"
        assert [s.kind for s in classify(source, translation)] == [PAIRED]
        assert split_in_step(source, translation) == [
            ("yaku m-agqaqili sa azazak", "I was carrying a child on my hip"),
            ("yaku m-agqaqili sa azazak pagka",
             "I was carrying a child a chair on my hip"),
        ]


class TestNotes:
    @pytest.mark.parametrize(
        "inner",
        [
            "lit. Clothes lice are easy to be caught",
            "answer to What are you going to do?",
            "said, e.g., in anger, when fighting with someone",
            "e.g. as company",
            "viz. had no wrinkles",
            "recorded with [duwan] for what I take to be shdu uan",
            "considered more polite than i-hala",
            "seems to apply not only to stupidity",
        ],
    )
    def test_an_editorial_marker_is_a_note_at_any_length(self, inner):
        assert [s.kind for s in classify("yaku mu-nay", f"I came ({inner})")] == [NOTE]

    def test_a_long_unpaired_parenthetical_is_a_note(self):
        long = "part of the ritual of the Thao New Year ceremony"
        assert [s.kind for s in classify("yaku mu-nay", f"I came ({long})")] == [NOTE]

    def test_supplied_words_stay_inline(self):
        for inner in ("and", "it", "he", "them", "a chair"):
            assert [
                s.kind for s in classify("yaku mu-nay", f"I came ({inner}) here")
            ] == [INLINE]

    def test_short_naturalistic_elaboration_stays_inline(self):
        # POL-024 says explicitly not to flag these.
        assert [
            s.kind
            for s in classify(
                "yaku mu-tusi Porto", "Sally went to Porto (a town in Portugal)"
            )
        ] == [INLINE]

    def test_take_notes_removes_the_note_and_tidies_what_is_left(self):
        kept, notes = take_notes(
            "yaku m-in-ara", "I took it (answer to Where were you?) yesterday"
        )
        assert kept == "I took it yesterday"
        assert notes == ["answer to Where were you?"]

    def test_take_notes_keeps_several_in_printed_order(self):
        kept, notes = take_notes(
            "yaku mu-nay",
            "I came (lit. I arrived) here (said when returning home)",
        )
        assert kept == "I came here"
        assert notes == ["lit. I arrived", "said when returning home"]

    def test_the_length_threshold_belongs_to_the_caller(self):
        translation = "I came (with my brother)"
        assert [s.kind for s in classify("yaku mu-nay", translation)] == [INLINE]
        assert [
            s.kind for s in classify("yaku mu-nay", translation, note_words=3)
        ] == [NOTE]


class TestSplitInStep:
    def test_one_paired_parenthetical_expands_on_both_sides(self):
        assert split_in_step(
            "yaku m-agqaqili sa azazak (sa pagka)",
            "I was carrying a child (a chair) on my hip",
        ) == [
            ("yaku m-agqaqili sa azazak", "I was carrying a child on my hip"),
            (
                "yaku m-agqaqili sa azazak sa pagka",
                "I was carrying a child a chair on my hip",
            ),
        ]

    def test_it_declines_when_nothing_pairs(self):
        assert split_in_step("ata (tu) karkar-i", "Don't chew it!") is None

    def test_it_declines_on_two_parentheticals_a_side(self):
        # Nothing says which renders which.
        assert (
            split_in_step("a (b) c (d)", "A (B) C (D)") is None
        )


def test_parentheticals_finds_innermost_spans_only():
    spans = parentheticals("one (two) three (four five)")
    assert [s.inner for s in spans] == ["two", "four five"]
    assert [s.words for s in spans] == [1, 2]
    assert spans[0].text == "(two)"


def test_a_bare_grammatical_label_stays_in_the_translation():
    """`(pl.)` is attached to a pronoun, not the author writing about the gloss.

    "We (incl.) are early" loses its sense without it, so it is not a note
    however metalinguistic it looks.
    """
    for inner in ("pl.", "sg.", "incl.", "excl."):
        assert [
            s.kind for s in classify("yamin mu-nay", f"We ({inner}) came here")
        ] == [INLINE]


# The maintainer's rulings of 2026-09-11, on Blust's Thao Dictionary.
#
# The discriminator is not length, it is whether the parenthesis is
# grammatically part of the English or a comment about the example. Supplied
# material - a pronoun, a verb phrase, an agent - completes the sentence and
# stays; an elaboration reads as an aside and the sentence is whole without it.
# Five words turned out to be where that line falls in this book, and `etc.`
# marks an elaboration at any length.
@pytest.mark.parametrize(
    "translation, kept, note",
    [
        # elaborations - the sentence stands without them
        ("I fell through (a floor, etc.)", "I fell through", "a floor, etc."),
        (
            "What is it? (response when called by someone)",
            "What is it?",
            "response when called by someone",
        ),
        (
            "be moved (further from the speaker than m-in-un-saháy)",
            "be moved",
            "further from the speaker than m-in-un-saháy",
        ),
    ],
)
def test_an_elaboration_becomes_a_note(translation, kept, note):
    assert take_notes("x", translation) == (kept, [note])


@pytest.mark.parametrize(
    "translation",
    [
        "We'll start (to walk) on the gentle slope",      # supplied verb phrase
        "He will be knocked on the head (by someone)",    # supplied agent
        "If we are going to make a fence (we) cut down some bamboo",  # supplied pronoun
        "We (incl.) are early",                           # grammatical label
        "Extinguish the fire (so) that it spreads no further",  # supplied conjunction
    ],
)
def test_supplied_material_stays_in_situ(translation):
    kept, notes = take_notes("x", translation)
    assert kept == translation
    assert notes == []


# Nested parentheticals (maintainer, 2026-09-11).
#
# A literal paraphrase often contains a supplied word of its own, and the old
# innermost-match regex could not span one - so all 25 of the `(lit. ...)`
# remarks left inline in the published Thao Dictionary were the nested ones.
# The OUTERMOST span is the unit: the note is the whole remark.
def test_a_parenthetical_may_contain_one():
    text = "I put bananas in to ripen (lit. I am ripening bananas, (I) put them in)"
    spans = parentheticals(text)
    assert [p.inner for p in spans] == [
        "lit. I am ripening bananas, (I) put them in"
    ]


def test_a_nested_literal_paraphrase_becomes_a_note():
    kept, notes = take_notes(
        "yaku pim-bulaw fizfiz",
        "I put bananas in to ripen (lit. I am ripening bananas, (I) put them in)",
    )
    assert kept == "I put bananas in to ripen"
    assert notes == ["lit. I am ripening bananas, (I) put them in"]


def test_an_unclosed_bracket_yields_nothing():
    # V111 is what reports it; this must not run to the end of the string.
    assert parentheticals("a translation with one (unclosed bracket") == []


def test_two_separate_parentheticals_are_still_two():
    spans = parentheticals("Level (that place) over there (and) we will plant")
    assert [p.inner for p in spans] == ["that place", "and"]


def test_an_editorial_marker_beats_the_pairing_count():
    """Equal counts are a default, not a proof (maintainer, 2026-09-11).

    `m-ara (sa) apiq` has one parenthetical and so does its translation, but
    `(sa)` is an optional Thao word and `(lit. ...)` paraphrases the whole
    sentence. They are not about the same thing, and three notes stayed in the
    translation because the count said they were.
    """
    kept, notes = take_notes(
        "m-ara (sa) apiq",
        "marry off one's son (lit. get a daughter-inlaw, a calque from Taiwanese)",
    )
    assert kept == "marry off one's son"
    assert notes == ["lit. get a daughter-inlaw, a calque from Taiwanese"]


def test_genuinely_paired_material_still_pairs():
    # No marker: `(sa pagka)` and `(a chair)` ARE about the same thing.
    kept, notes = take_notes(
        "yaku m-agqaqili sa azazak (sa pagka)",
        "I was carrying a child (a chair) on my hip",
    )
    assert kept == "I was carrying a child (a chair) on my hip"
    assert notes == []


# Words that are optional so often they say nothing about the translation
# (maintainer, 2026-09-11). Which words those are is a fact about a language,
# so the set belongs to the caller, not to this module.
THAO_PARTICLES = frozenset({"tu", "sa", "a", "ya", "wa"})


def test_a_bracketed_particle_does_not_pair():
    # `(tu)` is a Thao particle with no clear gloss; `(it)` is the translator
    # supplying an object. The counts match and the two are unrelated.
    assert pairs_with_source("ata (tu) karkar-i", "Don't chew (it)!")
    assert not pairs_with_source(
        "ata (tu) karkar-i", "Don't chew (it)!", never_pairs=THAO_PARTICLES
    )


def test_contentful_optional_material_still_pairs():
    assert pairs_with_source(
        "yaku m-agqaqili sa azazak (sa pagka)",
        "I was carrying a child (a chair) on my hip",
        never_pairs=THAO_PARTICLES,
    )


def test_take_notes_passes_the_set_through():
    kept, notes = take_notes(
        "a mu-ntua ihu (ya) simaq",
        "Where will you go tomorrow? (said to be better with /ya/)",
        never_pairs=THAO_PARTICLES,
    )
    assert kept == "Where will you go tomorrow?"
    assert notes == ["said to be better with /ya/"]


def test_the_default_is_empty_so_nothing_else_changes():
    assert pairs_with_source("ata (tu) karkar-i", "Don't chew (it)!")

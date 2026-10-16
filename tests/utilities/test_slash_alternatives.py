"""QC/utilities/slash_alternatives.py — scope resolution and curation audit."""

import pytest

from QC.utilities.slash_alternatives import audit, resolve_scope


class TestResolveScope:
    def test_morpheme_tier_beats_the_naive_split(self):
        # NTU's case: the slash scope is M1, so `lebe` is shared.
        scope = resolve_scope(
            "pua/mua/mu-lebe", morphemes=[["pua/mua/mu", "lebe"]]
        )
        assert scope.options == ["pua-lebe", "mua-lebe", "mu-lebe"]
        assert scope.confidence == "high"

    def test_a_word_order_variant_alternates_as_a_whole(self):
        scope = resolve_scope("yaku min-ayaw/min-ayaw yaku")
        assert scope.options == ["yaku min-ayaw", "min-ayaw yaku"]
        assert "different order" in scope.evidence

    def test_shared_material_on_both_sides_is_kept_in_both_readings(self):
        scope = resolve_scope(
            "yaku a ma-kan fizfiz/bailu m-ruqit shapa",
            translation="I'll peel a banana/husk a peanut and eat it",
        )
        assert scope.options == [
            "yaku a ma-kan fizfiz m-ruqit shapa",
            "yaku a ma-kan bailu m-ruqit shapa",
        ]
        assert scope.prefix == "yaku a ma-kan"
        assert scope.suffix == "m-ruqit shapa"

    def test_shared_material_printed_on_both_sides_is_not_doubled(self):
        # `a qamishan` is printed twice, once per side.
        scope = resolve_scope("ma-pitu-'un iza nak a qamishan/ yaku a qamishan")
        assert scope.options == [
            "ma-pitu-'un iza nak a qamishan",
            "ma-pitu-'un iza yaku a qamishan",
        ]
        assert scope.suffix == "a qamishan"

    def test_a_split_that_would_repeat_a_word_is_rejected(self):
        # `kan` heads both alternants; cutting one word off each side would
        # glue the two copies together.
        scope = resolve_scope("kukulay i-say bukhaz kan qca-i/kan p-acay-i ihu")
        assert scope.options == [
            "kukulay i-say bukhaz kan qca-i ihu",
            "kukulay i-say bukhaz kan p-acay-i ihu",
        ]

    def test_balanced_alternants_beat_shorter_lopsided_ones(self):
        # `kan qca-i` / `kan p-acay-i` (2 and 2) is preferred over
        # `kan qca-i` / `kan` (2 and 1), which is shorter overall.
        scope = resolve_scope("kukulay i-say bukhaz kan qca-i/kan p-acay-i ihu")
        assert [len(a.split()) for a in scope.alternants] == [2, 2]

    def test_a_disagreeing_translation_lowers_confidence(self):
        scope = resolve_scope("a b/c d", translation="one/two/three")
        assert scope.confidence == "low"
        assert "not" in scope.evidence


class TestAudit:
    def test_a_clean_two_way_substitution_has_no_findings(self):
        assert (
            audit(
                "nak a qati/qumqum ar-ara-n",
                ["nak a qati ar-ara-n", "nak a qumqum ar-ara-n"],
                "My granddaughter married an Atayal",
            )
            == []
        )

    def test_a_reading_that_still_holds_a_slash_is_hard(self):
        findings = audit("a b/c", ["a b/c", "a c"])
        assert [f.rule for f in findings if f.severity == "HARD"] == ["SA002"]

    def test_source_material_in_no_reading_is_hard(self):
        findings = audit("a b/c d", ["a b", "c"])
        assert any(f.rule == "SA004" for f in findings)
        assert "d" in next(f for f in findings if f.rule == "SA004").detail

    def test_shared_material_counted_once_is_not_a_loss(self):
        # The source prints shared material once per side, so the readings'
        # token counts legitimately exceed the source's.
        findings = audit(
            "yaku shi-tana-utu/shi-tana-utu iza yaku",
            ["yaku shi-tana-utu", "shi-tana-utu iza yaku"],
        )
        assert not any(f.rule == "SA004" for f in findings)

    def test_a_lengthwise_uneven_substitution_is_reported(self):
        findings = audit(
            "yaku a ma-kan fizfiz/bailu m-ruqit shapa",
            ["yaku a ma-kan fizfiz", "bailu m-ruqit shapa"],
        )
        assert any(f.rule == "SA005" for f in findings)

    def test_a_word_order_variant_is_not_reported_for_length(self):
        findings = audit(
            "ruza pia-biskaw/pia-biskaw sa ruza",
            ["ruza pia-biskaw", "pia-biskaw sa ruza"],
        )
        assert not any(f.rule == "SA005" for f in findings)

    def test_one_shared_translation_with_a_slash_is_reported(self):
        findings = audit(
            "yaku t-m-uqar atu/fafuy/ranaw",
            ["yaku t-m-uqar atu", "yaku t-m-uqar fafuy", "yaku t-m-uqar ranaw"],
            "I called the dog/pig/chicken",
        )
        assert [f.rule for f in findings] == ["SA006"]

    def test_a_single_reading_is_hard(self):
        assert audit("a/b", ["a b"])[0].rule == "SA001"


# Two shapes the resolver got wrong, both found by the maintainer reviewing
# Blust's Thao Dictionary translations (2026-09-11). The resolver is
# token-based and language-agnostic, so it is the right tool for the English
# side of a slash record as well as the Thao.
def test_sentence_final_punctuation_belongs_to_the_frame():
    # `Why do you hate me/us?` split into `... me` and `us?`, and the reading
    # that lost its question mark is not a sentence.
    scope = resolve_scope("Why do you hate me/us?")
    assert scope.options == ["Why do you hate me?", "Why do you hate us?"]


def test_a_closing_quote_closes_the_frame_too():
    scope = resolve_scope("Father ordered the child `Don't fight/quarrel'")
    assert scope.options == [
        "Father ordered the child `Don't fight'",
        "Father ordered the child `Don't quarrel'",
    ]


def test_three_alternants_share_the_frame_printed_once():
    # The frame is printed on the first part only; the printed split left
    # `pig` and `chicken` as bare fragments.
    scope = resolve_scope("I called the dog/pig/chicken")
    assert scope.options == [
        "I called the dog", "I called the pig", "I called the chicken"
    ]
    assert scope.confidence == "medium"


def test_a_multi_word_alternation_is_a_known_limitation():
    """The one shape the resolver gets wrong, recorded rather than hidden.

    "I'll peel a banana / husk a peanut and eat it" alternates THREE tokens on
    each side. The ranking prefers the shortest balanced candidate, which is
    right almost everywhere - the Thao of this very record,
    `yaku a ma-kan fizfiz/bailu m-ruqit shapa`, needs `fizfiz`/`bailu` - but
    here it takes `banana`/`husk` and produces nonsense, at medium confidence.

    Nothing in the string distinguishes the two: no word repeats, and both
    candidates are balanced. It needs a ruling, and Blust's build carries one.
    """
    scope = resolve_scope("I'll peel a banana/husk a peanut and eat it")
    assert scope.options == [
        "I'll peel a banana a peanut and eat it",
        "I'll peel a husk a peanut and eat it",
    ]
    # The right reading is among the candidates it considered and rejected.
    assert [
        "I'll peel a banana and eat it", "I'll husk a peanut and eat it"
    ] in scope.rejected


def test_the_thao_side_of_that_record_is_resolved_correctly():
    scope = resolve_scope("yaku a ma-kan fizfiz/bailu m-ruqit shapa")
    assert scope.options == [
        "yaku a ma-kan fizfiz m-ruqit shapa",
        "yaku a ma-kan bailu m-ruqit shapa",
    ]

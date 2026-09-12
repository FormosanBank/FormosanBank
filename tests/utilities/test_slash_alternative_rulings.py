"""The eight slash scopes the maintainer ruled on, 2026-09-10.

These are regression cases, not unit tests of a mechanism. Each is a printed
example from Blust's *Thao Dictionary* whose hand-curated expansion gave one
reading material the other needed, and each carries the reading the maintainer
ruled correct. `resolve_scope` has to reproduce all eight, and `audit` has to
find the curated version wrong and the ruled version right.

Seven were mis-split the same way: the alternation is one word and the material
around it is shared, but the curation cut the sentence at the slash and left the
trailing words with only one reading. `blust-dict-p0881-e009` is the maintainer's
own correction to the auditor: the alternation there is `taun` / `mapa-ki-bariz`
with `nam a` shared, not `nam a taun` / `mapa-ki-bariz`.

Two of the eight also exercise the shapes that make a naive split repeat a word.
`blust-dict-p0727-e001` prints `a qamishan` on both sides of the slash;
`blust-dict-p0446-e019` prints `kan` at the head of both alternants. Without the
handling for those, the readings come out as `... qamishan a qamishan` and
`... kan kan p-acay-i ihu`.
"""

import pytest

from QC.utilities.slash_alternatives import audit, resolve_scope

# (record, printed source, curated reading that was wrong, ruled readings)
RULINGS = [
    (
        "blust-dict-p0848-e005",
        "yaku a ma–kan fizfiz/bailu m–ruqit shapa",
        ["yaku a ma–kan fizfiz", "bailu m–ruqit shapa"],
        [
            "yaku a ma–kan fizfiz m–ruqit shapa",
            "yaku a ma–kan bailu m–ruqit shapa",
        ],
    ),
    (
        "blust-dict-p0727-e001",
        "ma–pitu–'un iza nak a qamishan/ yaku a qamishan",
        ["ma–pitu–'un iza nak a qamishan", "yaku a qamishan"],
        ["ma–pitu–'un iza nak a qamishan", "ma–pitu–'un iza yaku a qamishan"],
    ),
    (
        "blust-dict-p0881-e009",
        "tilha mu–nay a shput kahiwan m–in–ia–sun nam a taun/mapa–ki–bariz",
        [
            "tilha mu–nay a shput kahiwan m–in–ia–sun nam a taun",
            "tilha mu–nay a shput kahiwan mapa–ki–bariz",
        ],
        [
            "tilha mu–nay a shput kahiwan m–in–ia–sun nam a taun",
            "tilha mu–nay a shput kahiwan m–in–ia–sun nam a mapa–ki–bariz",
        ],
    ),
    (
        "blust-dict-p0924-e006",
        "balinuqaz ya q–in–usaz iza i–say ma–braq muqay mu–apaw cicu a punuq, "
        "numa ya pin–shkash–in ita kun–na–tmaz/pish–na–tmaz cicu a punuq",
        [
            "balinuqaz ya q–in–usaz iza i–say ma–braq muqay mu–apaw cicu a punuq, "
            "numa ya pin–shkash–in ita kun–na–tmaz",
            "balinuqaz ya q–in–usaz iza i–say ma–braq muqay mu–apaw cicu a punuq, "
            "numa ya pin–shkash–in ita pish–na–tmaz cicu a punuq",
        ],
        [
            "balinuqaz ya q–in–usaz iza i–say ma–braq muqay mu–apaw cicu a punuq, "
            "numa ya pin–shkash–in ita kun–na–tmaz cicu a punuq",
            "balinuqaz ya q–in–usaz iza i–say ma–braq muqay mu–apaw cicu a punuq, "
            "numa ya pin–shkash–in ita pish–na–tmaz cicu a punuq",
        ],
    ),
    (
        "blust-dict-p0996-e003",
        "fukish ya ma–pulha–pulhash tiuz–an/tiuz–i maní",
        ["fukish ya ma–pulha–pulhash tiuz–an", "fukish ya ma–pulha–pulhash tiuz–i maní"],
        [
            "fukish ya ma–pulha–pulhash tiuz–an maní",
            "fukish ya ma–pulha–pulhash tiuz–i maní",
        ],
    ),
    (
        "blust-dict-p0925-e005",
        "nak a kuskus lh–m–im–bakbak, shlaup/pish–qitan iza",
        [
            "nak a kuskus lh–m–im–bakbak, shlaup",
            "nak a kuskus lh–m–im–bakbak, pish–qitan iza",
        ],
        [
            "nak a kuskus lh–m–im–bakbak, shlaup iza",
            "nak a kuskus lh–m–im–bakbak, pish–qitan iza",
        ],
    ),
    (
        "blust-dict-p1027-e009",
        "pin–tusha sa i–nay ma–dahun, lhay tata wa magkaci/qbit suma",
        [
            "pin–tusha sa i–nay ma–dahun, lhay tata wa magkaci",
            "pin–tusha sa i–nay ma–dahun, lhay tata wa qbit suma",
        ],
        [
            "pin–tusha sa i–nay ma–dahun, lhay tata wa magkaci suma",
            "pin–tusha sa i–nay ma–dahun, lhay tata wa qbit suma",
        ],
    ),
    (
        "blust-dict-p0446-e019",
        "kukulay i–say bukhaz kan qca–i/kan p–acay–i ihu",
        ["kukulay i–say bukhaz kan qca–i", "kukulay i–say bukhaz kan p–acay–i ihu"],
        ["kukulay i–say bukhaz kan qca–i ihu", "kukulay i–say bukhaz kan p–acay–i ihu"],
    ),
]

IDS = [record for record, _raw, _was, _ruled in RULINGS]


@pytest.mark.parametrize("record,raw,was,ruled", RULINGS, ids=IDS)
def test_resolve_scope_reproduces_the_ruling(record, raw, was, ruled):
    assert resolve_scope(raw).options == ruled


@pytest.mark.parametrize("record,raw,was,ruled", RULINGS, ids=IDS)
def test_audit_reports_the_curation_that_was_wrong(record, raw, was, ruled):
    assert any(finding.rule == "SA005" for finding in audit(raw, was))


@pytest.mark.parametrize("record,raw,was,ruled", RULINGS, ids=IDS)
def test_audit_accepts_the_ruled_reading(record, raw, was, ruled):
    assert audit(raw, ruled) == []


@pytest.mark.parametrize("record,raw,was,ruled", RULINGS, ids=IDS)
def test_no_ruled_reading_says_a_word_twice(record, raw, was, ruled):
    for reading in ruled:
        words = reading.split()
        assert not any(
            a.casefold() == b.casefold() for a, b in zip(words, words[1:])
        ), reading

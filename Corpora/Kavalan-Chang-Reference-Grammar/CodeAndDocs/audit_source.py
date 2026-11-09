#!/usr/bin/env python3
"""Audit the generated Kavalan XML against the reviewed source ledgers."""

from __future__ import annotations

import argparse
import hashlib
import re
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

import build_xml


SOURCE_PDF = build_xml.ROOT / "Private/source/basecamp/12.original.pdf"
SOURCE_SHA = build_xml.ROOT / "CodeAndDocs/source_pdf.sha256"
# The transcription (source_units.tsv) alone. Morphemes rose from 2,402 to 2,408 on
# 2026-11-06 when the six words the book leaves unglossed inside a glossed sentence
# were glossed <UNCLEAR/> (POL-061) and given one morpheme, as every unsegmented word
# in the analysed line is (see build_xml.unglossed_word_morphemes); words and
# sentences did not change. They rose again, to 2,419, on 2026-11-07 with the
# circumfix ruling (build_xml.CIRCUMFIX_WORDS): the four ta-/sa-...-an words with a
# trailing empty slot gain two morphemes each, and ta=paw-an-su (p100r-e002), which
# had none, gains three; their FORMs count too (4,465 -> 4,476). Also on 2026-11-07, 8 of the 18 alternative
# readings became a second FORM (ver="alt") on the word that varies instead of a sentence of their own
# (build_xml.WORD_VARIANT): alternative sentences 18 -> 10. FORMs stay 4,476 (8 sentence FORMs out, 8 word FORMs
# in); PHON drops by 8, because a variant FORM has no PHON of its own (FormosanBank's schema gives PHON no ver
# attribute, so a word has one PHON, written from its base FORM).
TRANSCRIPTION = {
    "source_units": 755,
    "included_occurrences": 478,
    "primary_sentences": 436,
    "variant_sentences": 11,
    "words": 1636,
    "morphemes": 2465,
    "original_forms": 4556,
    "original_phon": 4468,
}
# Examples the transcription missed, added from the scan after review
# (source_units_additions.tsv): 30b, footnote 31 example i and footnote 13's example
# (2026-11-06); nine examples from the phonology chapter and footnote 41's two
# answers (2026-11-07).
ADDED_EXAMPLES = 14
# Alternative sentences, all with a word tier: 'nay/wi'u, saraq/tengen, zau/'nay x2, (u) x2, (ya) x2 (round 5,
# 2026-11-08), 28's =b. and =c. and footnote 19's ia. (round 6, 2026-11-08).
ALTERNATIVES_WITH_WORDS = 11
EXPECTED = dict(
    TRANSCRIPTION,
    source_units=TRANSCRIPTION["source_units"] + ADDED_EXAMPLES,
    included_occurrences=TRANSCRIPTION["included_occurrences"] + ADDED_EXAMPLES,
    primary_sentences=TRANSCRIPTION["primary_sentences"] + ADDED_EXAMPLES,
)
# The published corpus: the transcription with the student's corrections as ruled and
# the added examples.
REVIEWED = dict(EXPECTED, words=1661, morphemes=2502, original_forms=4632, original_phon=4624)
# miaori(q) 苗栗 (Miaoli, a place name) in three sentences, at sentence, word and morpheme level: Ortho113 Kavalan
# has no o.
STANDARD_PHON_STARS = 9
# A morpheme FORM holds letters and the apostrophe (a Kavalan letter), with = on a
# clitic, -x- for an infix, or root-root around an infix.
MORPHEME_FORM = r"=?[A-Za-z']+|[A-Za-z']+=|-[A-Za-z']+-|[A-Za-z']+-[A-Za-z']+"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audit(source_free: bool) -> dict[str, int | str]:
    units = build_xml.load_source_units()
    build_xml.validate_coverage(units)
    decisions = build_xml.load_variant_decisions(units)
    groups = build_xml.group_source_units(units)

    if not source_free:
        require(SOURCE_PDF.is_file(), f"private source PDF is missing: {SOURCE_PDF}")
        expected_sha = SOURCE_SHA.read_text(encoding="utf-8").strip()
        require(sha256(SOURCE_PDF) == expected_sha, "private source PDF digest changed")

    require(build_xml.OUT_XML.is_file(), f"generated XML is missing: {build_xml.OUT_XML}")
    require(
        build_xml.source_stage_from_generated() == build_xml.render(),
        "generated XML does not match a fresh source-stage render",
    )
    root = ET.parse(build_xml.OUT_XML).getroot()
    sentences = root.findall("S")
    variants = [sentence for sentence in sentences if "accepted source alternative" in sentence.get("source", "")]
    require(all(re.fullmatch(r"S-p\d{3}[lr]-e\d{3}-(opt|b|c|ia)", s.get("id")) for s in variants),
            "alternative sentence ids are the example's id plus -opt or a printed label (POL-028; round 6)")
    primary = [sentence for sentence in sentences if sentence not in variants]
    words = root.findall(".//W")
    morphemes = root.findall(".//M")
    original_forms = root.findall(".//FORM[@kindOf='original']")
    original_phon = root.findall(".//PHON[@kindOf='original']")

    actual = {
        "source_units": len(units),
        "included_occurrences": sum(unit.decision == "include" for unit in units),
        "primary_sentences": len(primary),
        "variant_sentences": len(variants),
        "words": len(words),
        "morphemes": len(morphemes),
        "original_forms": len(original_forms),
        "original_phon": len(original_phon),
    }
    corrections = build_xml.load_review_corrections()
    require(bool(corrections), "the student review corrections are missing")
    # Two inventories are pinned: the transcription alone, rebuilt in memory with none of
    # the student review's data (no corrections, added examples, student notes or
    # adjudication rows), and the published, reviewed corpus. Build rules the maintainer
    # ruled apply to both (the circumfix words, the trailing hyphens, final punctuation,
    # the book notes in build_xml.BOOK_NOTES).
    raw = build_xml.build_tree(
        build_xml.load_source_units(corrections={}, additions=None), review=False).getroot()
    raw_counts = {
        "words": len(raw.findall(".//W")),
        "morphemes": len(raw.findall(".//M")),
        "original_forms": len(raw.findall(".//FORM[@kindOf='original']")),
    }
    require(raw_counts == {k: TRANSCRIPTION[k] for k in raw_counts},
            f"transcription inventory changed: {raw_counts!r}")
    require(not any(build_xml.REVIEW_NOTE_PREFIX in (f.get("notes") or "") for f in raw.iter("FORM")),
            "the transcription-only rebuild carries review notes")
    require(actual == REVIEWED, f"inventory changed: {actual!r}")
    print(f"review_corrections={sum(map(len, corrections.values()))} fields; "
          f"transcription words={TRANSCRIPTION['words']} -> reviewed words={actual['words']}")
    require(len(groups) == EXPECTED["primary_sentences"], "source grouping changed")
    require(
        Counter(row.decision for row in decisions.values())
        == {
            "include": 12,
            "word_variant": 8,
            "exclude_analysis_notation": 1,
            "exclude_unacceptable": 1,
        },
        "source variant decisions changed",
    )
    # The standard tier comes from FormosanBank's standardize.py with Kavalan_TaiwanNandao_113.tsv: each original FORM
    # (variants included) has one standard FORM, spelled with r -> l and l -> d applied together; a sentence's also
    # drops the segmentation marks - = < >, which C012 removes from any sentence with a morpheme tier (all but three
    # here, none of which has one).
    to_113 = str.maketrans({"r": "l", "l": "d"})
    for element in (e for e in root.iter() if e.tag in ("S", "W", "M")):
        originals = [f for f in element.findall("FORM") if f.get("kindOf") == "original"]
        standards = [f for f in element.findall("FORM") if f.get("kindOf") == "standard"]
        require([f.get("ver") for f in originals] == [f.get("ver") for f in standards],
                f"{element.get('id')}: its standard FORMs do not pair with its original ones")
        for original, standard in zip(originals, standards):
            expected = (original.text or "").translate(to_113)
            if element.tag == "S":
                expected = re.sub(r"[-=<>]", "", expected)
            require(standard.text == expected, f"{element.get('id')}: standard FORM {standard.text!r}, not {expected!r}")
    # Standard PHON (add_phonology.py, Ortho113): '*' only for the o of miaori(q), a letter Ortho113 Kavalan lacks.
    starred = [(element, phon) for element in root.iter() for phon in element.findall("PHON[@kindOf='standard']")
               if "*" in (phon.text or "")]
    require(len(starred) == STANDARD_PHON_STARS
            and all("o" in (element.findtext("FORM[@kindOf='standard']") or "") for element, _ in starred),
            f"standard PHON stars changed: {[(e.get('id'), p.text) for e, p in starred]!r}")
    require(not root.findall(".//FORM[@kindOf='alternate']"), "the deprecated kindOf='alternate' is not used (POL-028)")
    # A one-word alternative is a second FORM on its word (build_xml.WORD_VARIANT): ver="alt", original tier, on a W
    # that keeps exactly one base FORM; every other alternative is a sentence of its own. (standardize.py gives each
    # its standard counterpart, checked with the standard tier above.)
    variant_forms = [(w, f) for w in words for f in w.findall("FORM")
                     if f.get("ver") is not None and f.get("kindOf") == "original"]
    require(len(variant_forms) == sum(row.decision == build_xml.WORD_VARIANT for row in decisions.values()),
            f"{len(variant_forms)} variant FORMs, not one per word_variant decision")
    require(all(f.get("ver") == "alt"
                and len([g for g in w.findall("FORM") if g.get("ver") is None and g.get("kindOf") == "original"]) == 1
                for w, f in variant_forms),
            "a variant FORM must be ver='alt' on the original tier of a W with one base FORM")
    require(not any(f.get("notes") for _, f in variant_forms),
            "a variant FORM carries no note: ver='alt' says it (maintainer, round 5)")
    require(not any(f.get("ver") is not None for s in sentences for f in s.findall("FORM"))
            and not any(f.get("ver") is not None for m in morphemes for f in m.findall("FORM")),
            "variant FORMs belong on the word only")
    # The word's one PHON spells its base FORM, not the variant: each of these words is one morpheme spelled like the
    # base, so the word's PHON must equal the morpheme's. (FormosanBank tools older than 2026-09-10 wrote the
    # variant's pronunciation here.)
    for word, variant in variant_forms:
        parts = word.findall("M")
        require(len(parts) == 1 and parts[0].findtext("FORM[@kindOf='original']") == word.findtext("FORM")
                and all(word.findtext(f"PHON[@kindOf='{kind}']") == parts[0].findtext(f"PHON[@kindOf='{kind}']")
                        for kind in ("original", "standard")),
                f"{word.get('id')}: its PHON does not spell its base FORM")
    require(
        all(translation.get("kindOf") is None for s in sentences for translation in s.findall("TRANSL")),
        "direct S TRANSL must not have kindOf",
    )
    require(
        all(
            translation.get("kindOf") == "original"
            for tag in ("W", "M")
            for node in root.findall(f".//{tag}")
            for translation in node.findall("TRANSL")
        ),
        "W/M source gloss TRANSL must have kindOf=original",
    )
    require(
        all("*" not in (phon.text or "") for phon in original_phon),
        "the shared TaiwanNandao phonology profile produced an unresolved star",
    )
    # An alternative sentence has a word tier exactly when its decision row gives its gloss line
    # (build_xml.ALTERNATIVE_WORD_GLOSSES): one W per word of the alternative; the others (28's =b. and =c.) none.
    glossed_forms = {build_xml.sentence_line(row.alternate_form)
                     for row in decisions.values() if row.decision == "include" and row.glosses}
    for sentence in variants:
        form = (sentence.findtext("FORM[@kindOf='original']") or "")[:-1]
        has_words = form in glossed_forms
        require(len(sentence.findall("W")) == (len(form.split()) if has_words else 0),
                f"{sentence.get('id')}: its word tier does not match its decision row's gloss line")
    require(sum(bool(sentence.findall("W")) for sentence in variants) == ALTERNATIVES_WITH_WORDS,
            "alternative sentences with a word tier changed")

    # The maintainer's rulings on the student review (2026-11-06), checked in the output.
    zho = "{http://www.w3.org/XML/1998/namespace}lang"
    sentence_forms = [s.find("FORM[@kindOf='original']") for s in sentences]
    # Song lines end in a comma, their Kavalan line and its translation alike (round 6, 2026-11-08).
    song = {build_xml.sentence_id(u) for u in units if u.unit_id in build_xml.SONG_LINE_COMMA_UNITS}
    require(len(song) == len(build_xml.SONG_LINE_COMMA_UNITS), "song lines are not each their own sentence")
    require(all((f.text or "")[-1:] in (",", ) if s.get("id") in song else (f.text or "")[-1:] in build_xml.LATIN_SENTENCE_END
                for s, f in zip(sentences, sentence_forms)),
            "every Kavalan sentence ends in . ? or !, a song line in ,")
    sentence_translations = [t for s in sentences for t in s.findall("TRANSL") if t.get(zho) == "zho"]
    require(all("".join(t.itertext())[-1:] in ("，" if s.get("id") in song else build_xml.CHINESE_SENTENCE_END)
                for s in sentences for t in s.findall("TRANSL") if t.get(zho) == "zho"),
            "every Chinese translation ends in 。？！, a song line's in ，")
    # A Kavalan line ends as its first Chinese translation does: ? after ？, ! after ！, else . (ruled 2026-11-07).
    mismatched = []
    for s in sentences:
        translations = [t for t in s.findall("TRANSL") if t.get(zho) == "zho"]
        last = "".join(translations[0].itertext())[-1:] if translations else ""
        if (s.findtext("FORM[@kindOf='original']") or "")[-1:] != build_xml.KAVALAN_END_OF.get(last, "."):
            mismatched.append(s.get("id"))
    require(not mismatched, f"Kavalan lines that do not end as their translation does: {mismatched}")
    require(not any(ch in "()" for t in root.iter("TRANSL") if t.get(zho) == "zho" for ch in "".join(t.itertext())),
            "Chinese glosses and translations use full-width parentheses")
    require(not any(ch in "（）" for f in original_forms for ch in (f.text or "")),
            "Kavalan FORMs use ASCII parentheses")
    require(not any(ch in build_xml.MORPHEME_PUNCTUATION for m in morphemes
                    for ch in (m.findtext("FORM[@kindOf='original']") or "")),
            "morpheme FORMs carry no punctuation")
    morpheme_forms = {m.findtext("FORM[@kindOf='original']") or "" for m in morphemes}
    odd = sorted(form for form in morpheme_forms if not re.fullmatch(MORPHEME_FORM, form))
    require(not odd, f"morpheme FORMs with characters other than letters, ' and the markers: {odd}")
    notes = build_xml.load_review_notes()
    published = sum((f.get("notes") or "").count(build_xml.REVIEW_NOTE_PREFIX) for f in sentence_forms)
    require(published == len(notes), f"{len(notes)} student notes, {published} published")
    require(not any("#" in "".join(t.itertext()) for t in sentence_translations),
            "the #-marked (unacceptable) translation is not published")
    actual["student_notes_published"] = published
    actual["mode"] = "tracked-ledger" if source_free else "full-source"
    return actual


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-free",
        action="store_true",
        help="audit tracked ledgers without requiring the ignored private scan",
    )
    args = parser.parse_args()
    result = audit(args.source_free)
    for key, value in result.items():
        print(f"{key}={value}")
    print("source_audit=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

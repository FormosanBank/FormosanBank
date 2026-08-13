#!/usr/bin/env python3
"""Build FormosanBank XML from Huteson 2003 Appendix B.

The PDF has a usable text layer, but the embedded font maps several source
symbols to legacy glyph bytes. The examples below are therefore keyed to the
appendix/page numbers and preserve the printed forms checked against rendered
page images.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom


REPO_ROOT = Path(__file__).resolve().parents[1]
XML_DIR = REPO_ROOT / "XML" / "Rukai"
REPORT_PATH = REPO_ROOT / "CodeAndDocs" / "extraction_report.tsv"

XML_NS = "http://www.w3.org/XML/1998/namespace"
ET.register_namespace("xml", XML_NS)

CITATION = (
    "Huteson, Greg. 2003. Sociolinguistic Survey Report for the Tona and Maga "
    "Dialects of the Rukai Language. SIL International."
)
BIBTEX = (
    "@techreport{huteson2003rukaiSurvey, author = {Huteson, Greg}, "
    "title = {Sociolinguistic Survey Report for the Tona and Maga Dialects of "
    "the Rukai Language}, institution = {SIL International}, year = {2003}}"
)
COPYRIGHT = (
    "CC BY-NC-SA 4.0 via SIL International terms screenshot attached to "
    "Basecamp card 8255603132."
)

UNGLOSSED_WORD_INDEXES = {
    ("maga", 7): frozenset({1}),
    ("maga", 11): frozenset({3}),
    ("maga", 13): frozenset({3}),
    ("maga", 14): frozenset({3}),
    ("tona", 9): frozenset({3}),
    ("tona", 10): frozenset({3}),
    ("tona", 14): frozenset({1, 4}),
}

REVIEWED_WORD_ALIGNMENTS = {
    ("tona", 4): (
        ("saokwamamitə", "very fat"),
        ("valak-ili", "child-1S.GEN"),
    ),
    ("tona", 9): (
        ("akakə", "1S.TOP"),
        ("ka", "TOP"),
        ("wakanə", "eat"),
        ("na", None),
        ("bələbələ", "banana"),
    ),
}

REVIEWED_WORD_IDS = {
    ("tona", 4): (1, 3),
}

WORD_EDGE_PUNCTUATION = '.,!?"“”'


@dataclass(frozen=True)
class Example:
    number: int
    form: str
    gloss: str
    translation: str
    test_page: int
    translation_page: int
    alternate_translation: str | None = None
    alternate_translation_notes: str | None = None
    expanded_translations: tuple[str, ...] = ()


@dataclass(frozen=True)
class Corpus:
    key: str
    title: str
    dialect: str
    source_label: str
    xml_id: str
    output_name: str
    examples: tuple[Example, ...]


MAGA = Corpus(
    key="maga",
    title="Maga Dialect Imitation Test",
    dialect="Maolin",
    source_label="Maga",
    xml_id="huteson_2003_rukai_maga_imitation_test",
    output_name="huteson_2003_rukai_maga_imitation_test.xml",
    examples=(
        Example(1, "aɖi ŋulu!", "NEG drink", "Don't drink!", 38, 39),
        Example(2, "abrele kɨkɨ.", "tired 1S.NOM", "I am tired.", 38, 39),
        Example(
            3,
            "traɖo-ŋa musu.",
            "big-already 2S.NOM",
            "You have gotten big.",
            38,
            39,
        ),
        Example(
            4,
            "sakroɖu-ŋa tubi.",
            "start-already cry",
            "(S/he) started to cry.",
            38,
            39,
            expanded_translations=("He started to cry.", "She started to cry."),
        ),
        Example(
            5,
            "saokura maucuru gili nma.",
            "very fat younger.sibling 1S.GEN",
            "My younger sibling is very fat.",
            38,
            39,
        ),
        Example(
            6,
            "uputakɨ knee icoo.",
            "run this person",
            "This person ran/is running.",
            38,
            39,
            expanded_translations=(
                "This person ran.",
                "This person is running.",
            ),
        ),
        Example(
            7,
            "ko-sa-tepruu na aŋatu.",
            "1S.NOM-use-make brushwood",
            "I want to use brushwood to make a fire.",
            38,
            39,
        ),
        Example(
            8,
            "i-sierkɨ ki mamaa.",
            "NEG-sleep NOM father",
            "Father did not sleep.",
            38,
            40,
        ),
        Example(
            9,
            "u-rgu ki kanaw luŋluŋee.",
            "ACT/REAL-know NOM Kanaw swim",
            "Kanaw knows (how to) swim.",
            38,
            40,
        ),
        Example(
            10,
            "astita-li kɖoo vlavlakɨ.",
            "NOM:beat-1S.NOM that child",
            "It is I who beat that child.",
            38,
            40,
        ),
        Example(
            11,
            "ukpuslɨ kɨkɨ kwonɨ na broo.",
            "twice 1S.NOM eat rice",
            "I ate rice twice.",
            38,
            40,
        ),
        Example(
            12,
            "ikee blatɨ ki ninaa.",
            "exist outside NOM mother",
            "Mother is outside.",
            38,
            40,
        ),
        Example(
            13,
            "marimuru pkee danɨ na sosisu.",
            "forget put house key",
            "He forgot (his) keys at home.",
            38,
            40,
        ),
        Example(
            14,
            "n-udu maa kɨkɨ na vlisnɨ pwabreve.",
            "will-carry.on.back will 1S.NOM wild.pig to:village",
            "I will bring the wild pig back to the village.",
            38,
            40,
        ),
    ),
)

TONA = Corpus(
    key="tona",
    title="Tona Dialect Imitation Test",
    dialect="Dona",
    source_label="Tona",
    xml_id="huteson_2003_rukai_tona_imitation_test",
    output_name="huteson_2003_rukai_tona_imitation_test.xml",
    examples=(
        Example(1, "abaili kakə.", "tired 1S.NOM", "I am tired.", 41, 42),
        Example(2, "taomomoa koso.", "grown.up 2S.NOM", "You are grown up.", 41, 42),
        Example(
            3,
            "siakiaoɖo-ŋa tobi.",
            "start-already cry",
            "(S/he) started to cry.",
            41,
            42,
            expanded_translations=("He started to cry.", "She started to cry."),
        ),
        Example(
            4,
            "saokwamamitə valak-ili.",
            "very fat child-1S.GEN",
            "My child is very fat.",
            41,
            42,
        ),
        Example(
            5,
            "tyaiday koɖay maoɖaŋə.",
            "run that old.person",
            "That old person ran/is running.",
            41,
            42,
            expanded_translations=(
                "That old person ran.",
                "That old person is running.",
            ),
        ),
        Example(
            6,
            "ko-sya-tiapoy nakay ʔaŋato.",
            "1S.NOM-use-make.a.fire this brushwood",
            "I want to use this brushwood to make a fire.",
            41,
            42,
        ),
        Example(
            7,
            "i-siaəkə ki tatava.",
            "NEG-sleep NOM father",
            "Father did not sleep.",
            41,
            42,
        ),
        Example(
            8,
            "w-a-igoʔo ki takanaw loaŋolaŋoi.",
            "ACT-REAL-know NOM Takanaw swim",
            "Takanaw knows (how to) swim.",
            41,
            43,
        ),
        Example(
            9,
            "a-kakə ka wakanə na bələbələ.",
            "1S.TOP TOP eat banana",
            "As for me, I ate a banana.",
            41,
            43,
        ),
        Example(
            10,
            "wakoposalə kakə kwanə na doʔo.",
            "twice 1S.NOM eat rice",
            "I ate rice twice.",
            41,
            43,
        ),
        Example(
            11,
            "i-kaʔacə nakoa naɖooay sosoaʔa.",
            "NEG-bite 1S.OBL that snake",
            "The snake did not bite me.",
            41,
            43,
        ),
        Example(
            12,
            "yakai balatə ki titina.",
            "exist outside NOM mother",
            "Mother is outside.",
            41,
            43,
        ),
        Example(
            13,
            "yakai balatə titina doʔodoʔo.",
            "exist outside mother cook",
            "Mother is cooking outside.",
            41,
            43,
        ),
        Example(
            14,
            "amwa ki takanaw kwanə na bələbələ.",
            "go Takanao eat banana",
            "Takanao went to eat the banana.",
            41,
            43,
        ),
        Example(
            15,
            '"ʔaokay-a nosiʔa" mi kakə ɖianə.',
            "come-IMP tomorrow so 1S.NOM 3S.OBL",
            "I asked him to come tomorrow.",
            42,
            44,
            alternate_translation='"Come tomorrow," I said to him.',
            alternate_translation_notes="literal translation",
        ),
    ),
)


def align_words(corpus: Corpus, example: Example) -> tuple[tuple[str, str | None], ...]:
    """Return the visually reviewed word and gloss columns for one example."""
    reviewed = REVIEWED_WORD_ALIGNMENTS.get((corpus.key, example.number))
    if reviewed is not None:
        return reviewed
    words = tuple(word.strip(WORD_EDGE_PUNCTUATION) for word in example.form.split())
    glosses = iter(example.gloss.split())
    unglossed = UNGLOSSED_WORD_INDEXES.get((corpus.key, example.number), frozenset())
    aligned: list[tuple[str, str | None]] = []
    for index, word in enumerate(words):
        aligned.append((word, None if index in unglossed else next(glosses, None)))
    missing_gloss = any(
        gloss is None
        for index, (_, gloss) in enumerate(aligned)
        if index not in unglossed
    )
    if any(not word for word, _ in aligned) or missing_gloss:
        raise ValueError(f"Incomplete word alignment for {corpus.key} {example.number}")
    if next(glosses, None) is not None:
        raise ValueError(f"Extra gloss token for {corpus.key} {example.number}")
    return tuple(aligned)


def add_word_tiers(sentence: ET.Element, corpus: Corpus, example: Example) -> None:
    aligned = align_words(corpus, example)
    word_ids = REVIEWED_WORD_IDS.get(
        (corpus.key, example.number), tuple(range(1, len(aligned) + 1))
    )
    if len(word_ids) != len(aligned):
        raise ValueError(f"Incomplete word IDs for {corpus.key} {example.number}")
    for word_index, (word_form, word_gloss) in zip(word_ids, aligned, strict=True):
        word_id = f"{sentence.get('id')}_W_{word_index:03d}"
        word = ET.SubElement(sentence, "W", {"id": word_id})
        form = ET.SubElement(word, "FORM", {"kindOf": "original"})
        form.text = word_form
        if word_gloss is not None:
            translation = ET.SubElement(
                word,
                "TRANSL",
                {f"{{{XML_NS}}}lang": "eng"},
            )
            translation.text = word_gloss
        else:
            translation = ET.SubElement(
                word,
                "TRANSL",
                {
                    f"{{{XML_NS}}}lang": "eng",
                    "kindOf": "standard",
                    "notes": "source gloss cell is blank",
                },
            )
            translation.text = "?"

        form_morphemes = word_form.split("-")
        gloss_morphemes = word_gloss.split("-") if word_gloss is not None else []
        aligned_glosses: list[str | None]
        if word_gloss is None:
            aligned_glosses = [None] * len(form_morphemes)
        elif len(form_morphemes) == len(gloss_morphemes):
            aligned_glosses = gloss_morphemes
        else:
            raise ValueError(
                f"Unresolved morpheme alignment for {corpus.key} {example.number}: "
                f"{word_form!r} / {word_gloss!r}"
            )
        for morph_index, (morph_form, morph_gloss) in enumerate(
            zip(form_morphemes, aligned_glosses, strict=True), start=1
        ):
            morph = ET.SubElement(word, "M", {"id": f"{word_id}_M_{morph_index:02d}"})
            form = ET.SubElement(morph, "FORM", {"kindOf": "original"})
            form.text = morph_form
            if morph_gloss is not None:
                translation = ET.SubElement(
                    morph,
                    "TRANSL",
                    {f"{{{XML_NS}}}lang": "eng"},
                )
                translation.text = morph_gloss
            else:
                notes = (
                    "source gloss cell is blank"
                    if word_gloss is None
                    else "source morpheme gloss is unresolved"
                )
                translation = ET.SubElement(
                    morph,
                    "TRANSL",
                    {
                        f"{{{XML_NS}}}lang": "eng",
                        "kindOf": "standard",
                        "notes": notes,
                    },
                )
                translation.text = "?"


def make_text(corpus: Corpus) -> ET.Element:
    root = ET.Element(
        "TEXT",
        {
            "id": corpus.xml_id,
            "citation": CITATION,
            "BibTeX_citation": BIBTEX,
            "copyright": COPYRIGHT,
            "dialect": corpus.dialect,
            "source": (
                f"Huteson 2003 Appendix B, {corpus.title}; source label "
                f"{corpus.source_label}; Basecamp card 8255603132."
            ),
            f"{{{XML_NS}}}lang": "dru",
        },
    )
    for example in corpus.examples:
        sentence = ET.SubElement(
            root,
            "S",
            {
                "id": f"S_{corpus.key}_{example.number:03d}",
                "source": (
                    f"Appendix B {corpus.key.upper()} {example.number}; "
                    f"test list p. {example.test_page}; translation p. "
                    f"{example.translation_page}"
                ),
            },
        )
        form = ET.SubElement(sentence, "FORM", {"kindOf": "original"})
        form.text = example.form
        translations = example.expanded_translations or (example.translation,)
        for translation_index, translation_text in enumerate(translations):
            attributes = {f"{{{XML_NS}}}lang": "eng"}
            if translation_index:
                attributes["ver"] = "alt"
            transl = ET.SubElement(sentence, "TRANSL", attributes)
            transl.text = translation_text
        if example.alternate_translation:
            alternate_attributes = {
                f"{{{XML_NS}}}lang": "eng",
                "ver": "alt",
            }
            if example.alternate_translation_notes:
                alternate_attributes["notes"] = example.alternate_translation_notes
            alternate = ET.SubElement(sentence, "TRANSL", alternate_attributes)
            alternate.text = example.alternate_translation
        add_word_tiers(sentence, corpus, example)
    return root


def pretty_xml(root: ET.Element) -> str:
    raw = ET.tostring(root, encoding="utf-8")
    return minidom.parseString(raw).toprettyxml(indent="    ", encoding="UTF-8").decode(
        "utf-8"
    )


def write_report(corpora: tuple[Corpus, ...]) -> None:
    with REPORT_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            delimiter="\t",
            lineterminator="\n",
            fieldnames=[
                "dialect",
                "source_label",
                "example_number",
                "test_list_page",
                "translation_page",
                "form",
                "alternate_translation",
                "alternate_translation_notes",
                "gloss",
                "translation",
            ],
        )
        writer.writeheader()
        for corpus in corpora:
            for example in corpus.examples:
                writer.writerow(
                    {
                        "dialect": corpus.dialect,
                        "source_label": corpus.source_label,
                        "example_number": example.number,
                        "test_list_page": example.test_page,
                        "translation_page": example.translation_page,
                        "form": example.form,
                        "gloss": example.gloss,
                        "translation": example.translation,
                        "alternate_translation": example.alternate_translation or "",
                        "alternate_translation_notes": (
                            example.alternate_translation_notes or ""
                        ),
                    }
                )


def main() -> None:
    XML_DIR.mkdir(parents=True, exist_ok=True)
    corpora = (MAGA, TONA)
    for corpus in corpora:
        target = XML_DIR / corpus.output_name
        target.write_text(pretty_xml(make_text(corpus)), encoding="utf-8")
    write_report(corpora)
    count = sum(len(corpus.examples) for corpus in corpora)
    print(f"Wrote {len(corpora)} XML files and {count} sentence records.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build canonical Yedda XML from the frozen complete scrape snapshot."""

from __future__ import annotations

import copy
import csv
import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORPUS_ROOT = ROOT.parent
SOURCE = ROOT / "data/source_snapshot/Paiwan_Yedda_Blog.xml"
OUTPUT = CORPUS_ROOT / "XML/Paiwan/Paiwan_Yedda_Blog.xml"
AUDIT = ROOT / "data/formosanbank_audit"
EXPECTED_SOURCE_SHA256 = (
    "e18d0aa67893278cb7754e9725e68a81075760961391b3db941eca7d873ddba6"
)
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


ISSUE_REPAIRS = {
    "S493_1": (
        "target_linguistic_analysis",
        "Where is the soup spoon? I use it to serve soup. Where is my pen?",
        "separated_free_translation_from_word_gloss",
        "The source page has three free-translation sentences followed by a separately labeled word gloss.",
    ),
    "S491_1": (
        "target_annotation_gloss",
        "In the past herding cattles was considered a taboo.",
        "separated_free_translation_from_word_gloss",
        "The source page labels this sentence as the free translation and lists the analysis under Word gloss.",
    ),
    "S481_1": (
        "target_linguistic_analysis",
        "The kid is eating.",
        "separated_free_translation_from_word_gloss",
        "The source page labels this sentence as the free translation and lists the analysis under Word gloss.",
    ),
    "S413_1": (
        "target_linguistic_analysis",
        "I saw our elders.",
        "separated_free_translation_from_word_gloss",
        "The source page labels this sentence as the free translation and lists the analysis under Word gloss.",
    ),
    "S412_1": (
        "target_linguistic_analysis",
        "I saw you and your girlfriend.",
        "separated_free_translation_from_word_gloss",
        "The source page labels this sentence as the free translation and lists the analysis under Word gloss.",
    ),
    "S305_1": (
        "non_formosan_script_in_source",
        "稲葉浩志いなばこうし is very handsome!",
        "retained_source_code_switching",
        "The source sentence and translation intentionally name Japanese singer Inaba Koshi in Kanji and Hiragana.",
    ),
    "S169_1": (
        "obvious_alignment_mismatch",
        "What is nose-flute? That is something our ancestors create to make sound.",
        "restored_omitted_translation_line",
        "The source page prints two Paiwan sentences and two English translation lines; the frozen scrape retained only the first translation.",
    ),
    "S159_1": (
        "target_linguistic_analysis",
        "We do not see horses in our place.",
        "moved_source_analysis_to_notes",
        "The source prints patient focus in parentheses after the free translation; the full source target is retained in notes.",
    ),
    "S62_1": (
        "obvious_alignment_mismatch",
        "Let's sing. Let all of us dance. Everybody, come play. Come, everybody, let's play swing.",
        "restored_omitted_translation_lines",
        "The source page prints four Paiwan lines and four English translation lines; the frozen scrape retained only the first translation.",
    ),
}


VARIANTS = {
    "S24_1": {
        "output_ids": "S24_1;S24_1b",
        "source_form": "a kipaparangez tua mareka qali/drava maru tjalja semeljecan a tja kava nu kaljavuceleljan.",
        "resolution": "split_qali_drava",
        "evidence": "The source glossary defines qali as male friend and drava as female friend.",
    },
    "S483_1": {
        "output_ids": "S483_1;S483_1b",
        "source_form": "liyaw a talem ni kama a abar (yasi).",
        "resolution": "split_abar_yasi",
        "evidence": "The source sentence presents yasi as the parenthetical alternative to abar.",
    },
    "S535_1": {
        "output_ids": "S535_1;S535_1b",
        "source_form": "izua tucu a kinarupurupung, tjangtjang / siyak, asaw na vurasi 'ata runi.",
        "resolution": "split_tjangtjang_siyak",
        "evidence": "The source sentence presents tjangtjang and siyak as alternatives.",
    },
}


SOURCE_TRANSLATION_REPAIRS = {
    "S664665_1": (
        "restored_omitted_source_translation",
        "thus, hence, thereupon, consequently, accordingly, as a result",
        "The live source defines the standalone pai entry with this English gloss.",
    ),
    "S545_1": (
        "restored_omitted_source_translation",
        "like this, as follows",
        "The live source gives this definition beside the maya tucu example.",
    ),
    "S545_2": (
        "restored_omitted_source_translation",
        "like that, that is the way",
        "The live source gives this definition beside the maya tuazua example.",
    ),
    "S545_3": (
        "restored_omitted_source_translation",
        "the same as",
        "The live source gives this definition beside the namaya example.",
    ),
    "S545_4": (
        "restored_omitted_source_translation",
        "alright then, if it is this way",
        "The live source gives this definition beside the ui, nu maya example.",
    ),
    "S545_5": (
        "restored_omitted_source_translation",
        "don't leave!",
        "The live source gives this definition beside the maya vaik example.",
    ),
    "S545_6": (
        "restored_omitted_source_translation",
        "there is no restriction on it.",
        "The live source gives this definition beside the inika pumaya example.",
    ),
    "S545_7": (
        "restored_omitted_source_translation",
        "I don't care; it doesn't matter",
        "The live source gives this definition beside the pumayan example.",
    ),
    "S545_8": (
        "restored_omitted_source_translation",
        "not yet! wait a bit!",
        "The live source gives this definition beside the mayanan example.",
    ),
    "S538_1": (
        "separated_free_translation_from_word_gloss",
        "Clouded-leopard roars, then the little girl got scared, and look, she "
        "runs to hide in the hut. There is a lot of bamboos here.",
        "The live source gives two free translations and labels qau: bamboo "
        "separately before the second example.",
    ),
    "S168_1": (
        "restored_omitted_translation_lines",
        "How many are you as a family? How many siblings do you have? How many "
        "friends do you have?",
        "The live source prints three Paiwan questions and three English lines.",
    ),
    "S170_1": (
        "restored_omitted_translation_lines",
        "What are you doing? I am studying the Paiwan language.",
        "The live source prints two Paiwan sentences and two English lines.",
    ),
    "S85_1": (
        "restored_omitted_translation_lines",
        "Do not hurt others. Do not abuse our own.",
        "The live source prints two Paiwan clauses and two English lines.",
    ),
    "S78_1": (
        "restored_omitted_translation_lines",
        "Let us all sing, Hope we will have fun. Let us dance together, We are "
        "all Paiwan.",
        "The live source prints four Paiwan lines and four English lines.",
    ),
    "S71_1": (
        "restored_omitted_translation_lines",
        "Do you know what's happening with COVID-19 in the United States now? "
        "How are the people, those who are infected? Those who have died of "
        "COVID-19 in the United States amount to 85,905.",
        "The live source prints three questions or statements and three English lines.",
    ),
    "S39_1": (
        "restored_truncated_source_translation",
        "The custom that we take naming people seriously has a very long history.",
        "The frozen scrape stopped at a source line break inside the English sentence.",
    ),
    "S38_1": (
        "restored_truncated_source_translation",
        "There are many different indigenous peoples here in Taiwan.",
        "The frozen scrape stopped at a source line break inside the English sentence.",
    ),
    "S37_1": (
        "restored_omitted_translation_lines",
        "Where are you from? (polite) Who are you? (unexpected and annoyed)",
        "The live source prints two Paiwan questions and two English lines.",
    ),
    "S35_1": (
        "restored_omitted_translation_lines",
        "I am a child of Paiwan in Taiwan. My skin is dark too, but I didn't "
        "accuse Director-General Tedros (of being a nigger). Please do not "
        "mislead the world, DG Tedros. Come to visit our village in Taiwan. "
        "Thank you.",
        "The live source prints five Paiwan lines and five English lines; the "
        "source bracketed aside is normalized to parentheses.",
    ),
    "S34_1": (
        "restored_omitted_translation_lines",
        "What is this? This is a book. What is this? This is pineapple. What is "
        "this? This is a telephone. What is this? This is a river.",
        "The live source prints four Paiwan pairs and four English pairs.",
    ),
    "S21_1": (
        "restored_omitted_translation_lines",
        "What can I do if you don't want me? I can do nothing if you don't want "
        "me, my love. Whether far away or close by, my love, I will not forget "
        "about you.",
        "The live source prints three song lines and three English lines.",
    ),
    "S19_1": (
        "restored_omitted_translation_lines",
        "kuliw: Is it difficult to learn the Paiwan language? yedda: Yes, I find "
        "it difficult to speak Paiwan because I don't get to use the language "
        "of Paiwan often.",
        "The live source prints both speakers in Paiwan and English.",
    ),
    "S9_1": (
        "restored_omitted_translation_lines",
        "As the sun sets, it becomes dark on earth. As it darkens on earth, "
        "crickets start to sing. As crickets sing, the moon shows her face. As "
        "the moon appears, the Owl wakes up.",
        "The live source prints four Paiwan lines and four English lines.",
    ),
    "Sunknown_1": (
        "restored_omitted_translation_lines",
        "What happened with you? Why are you crying by yourself?",
        "The live source prints two Paiwan questions and two English lines.",
    ),
}


SOURCE_WORD_TRANSLATION_REPAIRS = {
    "S623_1W2": ("'uyulj or quyulj", "bundle"),
    "S592_1W9": ("'i-valit or ki-valit", "to get change"),
    "S592_1W10": ("a'en or aken", "I, 1st person SIN NOM"),
    "S569_1W25": ("kata or katua", "with, and"),
    "S551552553_1W7": ("tua or ta", "OBL"),
    "S535_1W11": ("'ata or kata", "and"),
    "S535_1bW11": ("'ata or kata", "and"),
    "S510_1W4": ("kama or ama", "father, or male elder"),
    "S507_1W10": ("na or nua", "of, GEN"),
    "S506_1W5": ("alay or kala", "thin thread"),
    "S502_1W2": ("sa-(a)ladi or pa-sa-(a)ladji", "I don't want to."),
    "S500_1W5": (
        "qata or 'ata",
        "sglass bead. Another word is mulimulitan, which really refers to the "
        "most significant and precious bead among all glass beads. However, in "
        "Ferrel (p. 55), he had drungaljisan 'glass bead, specific type from "
        "Dutch trade. I could not find drung in any dictionary, but aljis is "
        "tooth, and -an is the end marker for nominalization.",
    ),
    "S499_1W4": (
        "ta-tiyaw or ka-tiyaw",
        "yesterday. ta- or ka- 'prefix which indicates past time'.",
    ),
    "S493_1W1": ("ainu or inu", "where"),
    "S493_1W7": ("siyaw or siav", "soup"),
    "S493_1W8": ("ainu or inu", "where"),
    "S491_1W6": (
        "'a-si-cuai-yan or kasicuaiyan",
        "from a long time ago. The root is cuai 'long'.",
    ),
    "S478_1W27": (
        "'ivavadaqan or ki-va-va-daq-an",
        "were asking, AV. The root is vadaq 'ask, question' in RED.",
    ),
    "S448_1W1": (
        "avan or mavan",
        "is, 'be' verb. In the study of Paiwan, the common knowledge is there "
        "is no 'be' verb.",
    ),
    "S412_1W4": ("kata or katua", "and, conjunction (CONJ)"),
    "S404_1W9": ("ka-ta or ka-tua", "and"),
    "S401_1W8": ("nua or na", "of, genitive (GEN) case marker"),
    "S374_1W6": (
        "kenamain*",
        "breakfast. I don't know how to break the word until the root kan. How?",
    ),
    "S368_1W3": (
        "aken or a'en",
        "I, 1st person singular nominative (NOM)",
    ),
    "S362_1W5": ("katua or kata", "and"),
    "S361_1W5": ("aken or a'en", "I, 1st person singular NOM"),
    "S346_1W3": (
        "a'en or aken",
        "I, 1st person singular nominative (NOM)",
    ),
    "S346_1W5": (
        "a'en or aken",
        "I, 1st person singular nominative (NOM)",
    ),
    "S318_1W9": ("tua or ta", "oblique (OBL) case marker"),
    "S316_1W2": (
        "a'en or aken",
        "I, 1st person singular nominative (NOM)",
    ),
    "S309_1W10": (
        "kata or katua",
        "and. This is also like a combination of the OBL ta or tua and ka. But "
        "I don't claim authority here.",
    ),
    "S303_1W4": (
        "a'en or aken",
        "I, 1st person singular nominative (NOM)",
    ),
    "S303_1W6": ("'ivadaq or kivadaq", "ask"),
    "S303_1W13": (
        "lingaw or lingav",
        "time. In our dialect, we use more /w/ than /v/ in the ending of a word.",
    ),
    "S303_1W15": (
        "i-caqu-an-an or kicaquan-an",
        "learn or study. The root is caqu 'talen, knowledge'. I listened for "
        "many times and I am sure Mom Naluku has the extra ending -an, which I "
        "do not know how to explain. Why did she use a undergoer voice (UV) "
        "case marker with the nominative subject case marker ti?",
    ),
    "S303_1W27": (
        "i-caqu-an-an or kicaquan-an",
        "learn or study. The root is caqu 'talen, knowledge'. I listened for "
        "many times and I am sure Mom Naluku has the extra ending -an, which I "
        "do not know how to explain. Why did she use a undergoer voice (UV) "
        "case marker with the nominative subject case marker ti?",
    ),
    "S281_1W5": ("tua / ta", "oblique (OBL) case marker"),
    "S275_1W1": ("titjen / itjen", "we inclusive (INCL)"),
    "S275_1W5": ("titjen / itjen", "we inclusive (INCL)"),
    "S154_1W6": ("tua or ta", "oblique (OBL) case marker"),
    "S39_1W4": (
        "ka-kuda- (a)n",
        "custom, culture, rule. The root is kuda 'rule, what'.",
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_sentence(root: ET.Element, sentence_id: str) -> ET.Element:
    sentence = root.find(f"S[@id='{sentence_id}']")
    if sentence is None:
        raise RuntimeError(f"Missing source sentence {sentence_id}")
    return sentence


def find_word(sentence: ET.Element, word_id: str) -> ET.Element:
    word = sentence.find(f"W[@id='{word_id}']")
    if word is None:
        raise RuntimeError(f"Missing source word {word_id}")
    return word


def original_form(element: ET.Element) -> ET.Element:
    forms = [
        form for form in element.findall("FORM") if form.get("kindOf") == "original"
    ]
    if len(forms) != 1:
        raise RuntimeError(
            f"Expected one original FORM under {element.tag} {element.get('id')}"
        )
    return forms[0]


def set_original_form(element: ET.Element, text: str, notes: str | None = None) -> None:
    form = original_form(element)
    form.text = text
    if notes:
        form.set("notes", notes)


def strip_derived_tiers(root: ET.Element) -> None:
    for parent in root.iter():
        for child in list(parent):
            if child.tag == "PHON" or (
                child.tag == "FORM" and child.get("kindOf") == "standard"
            ):
                parent.remove(child)


def remove_audio(sentence: ET.Element) -> None:
    sentence.attrib.pop("audio_url", None)
    for audio in sentence.findall("AUDIO"):
        sentence.remove(audio)


def rename_descendant_ids(sentence: ET.Element, old: str, new: str) -> None:
    for element in list(sentence.iter())[1:]:
        element_id = element.get("id")
        if element_id and element_id.startswith(old):
            element.set("id", new + element_id[len(old) :])
    sentence.set("id", new)


def add_word_translation(
    word: ET.Element,
    text: str,
    notes: str | None = None,
) -> None:
    for translation in word.findall("TRANSL"):
        word.remove(translation)
    translation = ET.Element("TRANSL", {XML_LANG: "eng"})
    translation.text = text
    if notes:
        translation.set("notes", notes)
    insert_at = len(word)
    for index, child in enumerate(word):
        if child.tag == "M":
            insert_at = index
            break
    word.insert(insert_at, translation)


def remove_word(sentence: ET.Element, word_id: str) -> None:
    sentence.remove(find_word(sentence, word_id))


def replace_with_variants(
    root: ET.Element, source_id: str, variants: list[ET.Element]
) -> None:
    source = find_sentence(root, source_id)
    index = list(root).index(source)
    root.remove(source)
    for offset, variant in enumerate(variants):
        root.insert(index + offset, variant)


def split_alternatives(root: ET.Element) -> None:
    source = copy.deepcopy(find_sentence(root, "S24_1"))
    qali = copy.deepcopy(source)
    drava = copy.deepcopy(source)
    rename_descendant_ids(drava, "S24_1", "S24_1b")
    note = (
        'Source prints "a kipaparangez tua mareka qali/drava maru tjalja '
        'semeljecan a tja kava nu kaljavuceleljan."; source-defined alternatives '
        "are emitted as separate records. The shared recording pronounces both alternatives and is omitted."
    )
    for sentence, word_id, value, gloss in (
        (qali, "S24_1W5", "qali", "male friend"),
        (drava, "S24_1bW5", "drava", "female friend"),
    ):
        remove_audio(sentence)
        set_original_form(
            sentence,
            f"a kipaparangez tua mareka {value} maru tjalja semeljecan a tja kava nu kaljavuceleljan.",
            note,
        )
        word = find_word(sentence, word_id)
        set_original_form(word, value, note)
        morpheme = word.find("M")
        if morpheme is None:
            raise RuntimeError(f"Missing morpheme under {word_id}")
        set_original_form(morpheme, value, note)
        add_word_translation(word, gloss)
    replace_with_variants(root, "S24_1", [qali, drava])

    source = copy.deepcopy(find_sentence(root, "S483_1"))
    abar = copy.deepcopy(source)
    yasi = copy.deepcopy(source)
    rename_descendant_ids(yasi, "S483_1", "S483_1b")
    note = (
        'Source prints "liyaw a talem ni kama a abar (yasi)."; source-defined '
        "alternatives are emitted as separate records. The shared recording pronounces both alternatives and is omitted."
    )
    remove_audio(abar)
    set_original_form(abar, "liyaw a talem ni kama a abar.", note)
    remove_word(abar, "S483_1W8")
    add_word_translation(find_word(abar, "S483_1W7"), "coconut tree")
    remove_audio(yasi)
    set_original_form(yasi, "liyaw a talem ni kama a yasi.", note)
    remove_word(yasi, "S483_1bW7")
    add_word_translation(find_word(yasi, "S483_1bW8"), "coconut tree")
    for sentence in (abar, yasi):
        for translation in sentence.findall("TRANSL"):
            sentence.remove(translation)
        main = ET.Element(
            "TRANSL",
            {
                XML_LANG: "eng",
                "notes": "Source prints both free-translation versions in one parenthetical target.",
            },
        )
        main.text = "The coconut trees planted by father are a lot."
        alt = ET.Element("TRANSL", {XML_LANG: "eng", "ver": "alt"})
        alt.text = "Father plants many coconut trees."
        first_word = next(i for i, child in enumerate(sentence) if child.tag == "W")
        sentence.insert(first_word, main)
        sentence.insert(first_word + 1, alt)
    replace_with_variants(root, "S483_1", [abar, yasi])

    source = copy.deepcopy(find_sentence(root, "S535_1"))
    tjangtjang = copy.deepcopy(source)
    siyak = copy.deepcopy(source)
    rename_descendant_ids(siyak, "S535_1", "S535_1b")
    note = (
        'Source prints "izua tucu a kinarupurupung, tjangtjang / siyak, asaw '
        "na vurasi 'ata runi." + '"; source-defined alternatives are emitted as '
        "separate records. The shared recording pronounces both alternatives and is omitted."
    )
    remove_audio(tjangtjang)
    set_original_form(
        tjangtjang,
        "izua tucu a kinarupurupung, tjangtjang, asaw na vurasi 'ata runi.",
        note,
    )
    remove_word(tjangtjang, "S535_1W7")
    add_word_translation(find_word(tjangtjang, "S535_1W5"), "pumpkin")
    remove_audio(siyak)
    set_original_form(
        siyak,
        "izua tucu a kinarupurupung, siyak, asaw na vurasi 'ata runi.",
        note,
    )
    remove_word(siyak, "S535_1bW5")
    add_word_translation(find_word(siyak, "S535_1bW7"), "pumpkin")
    replace_with_variants(root, "S535_1", [tjangtjang, siyak])


def repair_issue_rows(root: ET.Element) -> list[dict[str, str]]:
    rows = []
    for finding, (sentence_id, values) in enumerate(ISSUE_REPAIRS.items(), 1):
        rule, repaired, resolution, evidence = values
        sentence = find_sentence(root, sentence_id)
        translations = sentence.findall("TRANSL")
        if len(translations) != 1:
            raise RuntimeError(f"Expected one source translation in {sentence_id}")
        translation = translations[0]
        frozen = translation.text or ""
        translation.text = repaired
        translation.set("notes", f"Frozen scrape target: {frozen}")
        rows.append(
            {
                "finding": str(finding),
                "rule": rule,
                "s_id": sentence_id,
                "resolution": resolution,
                "source_url": sentence.get("source", ""),
                "evidence": evidence,
            }
        )
    return rows


def restore_source_translations(root: ET.Element) -> list[dict[str, str]]:
    rows = []
    for sentence_id, (resolution, text, evidence) in SOURCE_TRANSLATION_REPAIRS.items():
        sentence = find_sentence(root, sentence_id)
        translations = sentence.findall("TRANSL")
        if len(translations) > 1:
            raise RuntimeError(
                f"Expected at most one source translation in {sentence_id}"
            )
        frozen = translations[0].text or "" if translations else ""
        for existing in translations:
            sentence.remove(existing)
        note = (
            f"Frozen scrape target: {frozen}"
            if frozen
            else "Restored from the live source after frozen-scrape review."
        )
        translation = ET.Element(
            "TRANSL",
            {
                XML_LANG: "eng",
                "notes": note,
            },
        )
        translation.text = text
        first_word = next(
            (index for index, child in enumerate(sentence) if child.tag == "W"),
            len(sentence),
        )
        sentence.insert(first_word, translation)
        rows.append(
            {
                "s_id": sentence_id,
                "resolution": resolution,
                "source_url": sentence.get("source", ""),
                "frozen_translation": frozen,
                "translation": text,
                "evidence": evidence,
            }
        )
    return rows


def restore_source_word_translations(root: ET.Element) -> list[dict[str, str]]:
    rows = []
    note = "Restored from the live source after frozen-scrape review."
    for word_id, (source_head, text) in SOURCE_WORD_TRANSLATION_REPAIRS.items():
        sentence_id = word_id.rsplit("W", 1)[0]
        sentence = find_sentence(root, sentence_id)
        word = find_word(sentence, word_id)
        if word.findall("TRANSL"):
            raise RuntimeError(f"Expected no source word translation in {word_id}")
        add_word_translation(word, text, note)
        rows.append(
            {
                "s_id": sentence_id,
                "w_id": word_id,
                "resolution": "restored_exact_live_word_gloss",
                "source_url": sentence.get("source", ""),
                "source_head": source_head,
                "translation": text,
            }
        )
    return rows


def write_tsv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def write_audits(
    source_ids: list[str],
    issue_rows: list[dict[str, str]],
    translation_rows: list[dict[str, str]],
    word_translation_rows: list[dict[str, str]],
) -> None:
    AUDIT.mkdir(parents=True, exist_ok=True)
    coverage = []
    for sentence_id in source_ids:
        variant = VARIANTS.get(sentence_id)
        coverage.append(
            {
                "source_s_id": sentence_id,
                "output_s_ids": variant["output_ids"] if variant else sentence_id,
                "status": "expanded_source_alternatives" if variant else "included",
                "reason": variant["resolution"]
                if variant
                else "source_record_preserved",
            }
        )
    write_tsv(
        AUDIT / "source_coverage.tsv",
        coverage,
        ["source_s_id", "output_s_ids", "status", "reason"],
    )
    write_tsv(
        AUDIT / "issue_1_review.tsv",
        issue_rows,
        ["finding", "rule", "s_id", "resolution", "source_url", "evidence"],
    )
    variant_rows = [
        {
            "source_s_id": sentence_id,
            "output_s_ids": values["output_ids"],
            "source_form": values["source_form"],
            "resolution": values["resolution"],
            "evidence": values["evidence"],
            "audio_disposition": "omitted_shared_multi_alternative_recording",
        }
        for sentence_id, values in VARIANTS.items()
    ]
    write_tsv(
        AUDIT / "source_variant_review.tsv",
        variant_rows,
        [
            "source_s_id",
            "output_s_ids",
            "source_form",
            "resolution",
            "evidence",
            "audio_disposition",
        ],
    )
    write_tsv(
        AUDIT / "source_translation_review.tsv",
        translation_rows,
        [
            "s_id",
            "resolution",
            "source_url",
            "frozen_translation",
            "translation",
            "evidence",
        ],
    )
    write_tsv(
        AUDIT / "source_word_translation_review.tsv",
        word_translation_rows,
        [
            "s_id",
            "w_id",
            "resolution",
            "source_url",
            "source_head",
            "translation",
        ],
    )
    (AUDIT / "source_review_summary.md").write_text(
        "# Yedda source review summary\n\n"
        "- Frozen source records: 668\n"
        "- Canonical records after three source-defined alternative expansions: 671\n"
        "- Source records omitted: 0\n"
        "- Audit issue findings reviewed: 9/9\n"
        "- Live-source sentence translation repairs: 24\n"
        "- Exact live-source word glosses restored: 41\n"
        "- Unresolved source or issue findings: 0\n"
        "- Shared recordings omitted from split alternatives: 3\n\n"
        "All other original FORM, W, M, and word-gloss content is carried from "
        "the frozen complete scrape snapshot. Missing source glosses remain "
        "missing rather than being invented. Standard FORM and both PHON tiers "
        "are regenerated with pinned current FormosanBank authority.\n",
        encoding="utf-8",
    )


def main() -> None:
    actual_hash = sha256(SOURCE)
    if actual_hash != EXPECTED_SOURCE_SHA256:
        raise SystemExit(
            f"Source snapshot hash mismatch: expected {EXPECTED_SOURCE_SHA256}, got {actual_hash}"
        )
    tree = ET.parse(SOURCE)
    root = tree.getroot()
    source_sentences = root.findall("S")
    source_ids = [sentence.get("id", "") for sentence in source_sentences]
    if len(source_ids) != 668 or len(set(source_ids)) != 668 or "" in source_ids:
        raise SystemExit("Frozen source snapshot must contain 668 unique sentence IDs")

    strip_derived_tiers(root)
    split_alternatives(root)
    issue_rows = repair_issue_rows(root)
    translation_rows = restore_source_translations(root)
    word_translation_rows = restore_source_word_translations(root)
    output_ids = [sentence.get("id", "") for sentence in root.findall("S")]
    if len(output_ids) != 671 or len(set(output_ids)) != 671:
        raise SystemExit("Canonical pre-QC output must contain 671 unique sentence IDs")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(tree, space="  ")
    tree.write(OUTPUT, encoding="utf-8", xml_declaration=True)
    write_audits(source_ids, issue_rows, translation_rows, word_translation_rows)
    print(
        f"Built 671 source-backed pre-QC records from {len(source_ids)} frozen records."
    )


if __name__ == "__main__":
    main()

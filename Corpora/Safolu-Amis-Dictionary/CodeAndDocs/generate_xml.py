#!/usr/bin/env python3
"""Build FormosanBank XML from the Safolu (Tsai Chung-Han) Amis dictionary.

Source: the generated g0v/amis-moedict docs/s JSON (the Safolu Kacaw Lalanges /
蔡中涵 dictionary). Each Moedict example field (U+FFF9 form / U+FFFA / U+FFFB
final-translation) becomes one S element.

The Poinsot/Pourrias Amis-French dictionary that used to live alongside this one
now has its own repository, Formosan-Poinsot-Amis-Dictionary, because it needs OCR-correction
work that should not block publishing Safolu.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from moedict_formosanbank import (
    ROOT,
    Corpus,
    ExampleRecord,
    Translation,
    clean_moedict_link_markup,
    clean_text,
    collapse_space,
    parse_marked_example,
    write_metadata,
    write_xml,
)

from source_snapshot import MANIFEST, load_rows


DEFAULT_XML_OUT_DIR = ROOT / "XML"
DEFAULT_OVERRIDES_PATH = ROOT / "CodeAndDocs" / "safolu_source_overrides.json"
PRINTED_ADDITIONS_PATH = ROOT / "CodeAndDocs" / "printed_additions.json"

# The canonical XML is grouped language-first (XML/Amis/<Source>/) to match
# FormosanBank's Corpora/<Name>/XML/<Language>/ convention.
LANGUAGE_SUBDIR = "Amis"

SAFOLU_TEXT_ID = "amis_safolu_examples"
CJK_RE = re.compile(r"[㐀-鿿]")


# Leading source annotations that precede the Amis phrase, e.g. loanword notes
# like "〔閩南語借詞〕", "(漢語借詞)", or "（英語借詞）". They are kept with the
# translation, not treated as the FORM.
_LEADING_ANNOTATIONS = (("〔", "〕"), ("﹝", "﹞"), ("(", ")"), ("（", "）"))


def strip_leading_annotation(candidate: str) -> tuple[str, str]:
    """Peel a single leading bracketed annotation off the front of a field.

    Returns (remainder, annotation). When no leading annotation is present the
    remainder is the input and the annotation is empty.
    """
    candidate = candidate.strip()
    for open_bracket, close_bracket in _LEADING_ANNOTATIONS:
        if candidate.startswith(open_bracket) and close_bracket in candidate:
            annotation, remainder = candidate.split(close_bracket, 1)
            return remainder.strip(), annotation + close_bracket
    return candidate, ""


def recover_form_from_translation(translation: str) -> tuple[str, str, str] | None:
    """Recover source rows where U+FFF9/U+FFFA/U+FFFB left FORM empty.

    Some Safolu examples put the Amis phrase at the start of the Chinese field,
    e.g. "panayan 稻子的種類。". When there is a clear non-CJK prefix before the
    first CJK character, use that prefix as the FORM and keep the remainder as
    the Chinese translation. A single leading bracketed annotation (loanword
    note, etc.) is peeled off first and kept with the translation; without this
    step a leading "(閩南語借詞)" would be mis-read as the FORM.
    """
    candidate = clean_text(translation)
    candidate, annotation = strip_leading_annotation(candidate)

    match = CJK_RE.search(candidate)
    if not match or match.start() == 0:
        return None

    form = clean_text(candidate[: match.start()].strip(" .。．,，;；:："))
    recovered_translation = clean_text(annotation + candidate[match.start() :])

    # Repair a "（…）" annotation that straddled the split point, e.g.
    # "Ma'araw … hikoki（外來語）.孩子看見很多的飛機。": the first CJK falls inside
    # the loanword note, leaving a dangling "（" on the form and the orphaned
    # "外來語）" head on the translation. Drop both so the form stays pure Amis.
    if form and form[-1] in "(（" and re.match(r"[^)）]*[)）]", recovered_translation):
        form = clean_text(form[:-1])
        recovered_translation = clean_text(
            re.sub(r"^[^)）]*[)）][\s。．.,，;；:：]*", "", recovered_translation)
        )

    if not form or not recovered_translation:
        return None
    return form, recovered_translation, annotation


# A Moedict example field marks Amis tokens with `…~ link markup. In some
# entries the FORM field is empty and the Amis lives *inside* the Chinese
# definition, e.g. "如`ha~`sapakaen~ 飼養、餵養用的。" (gloss intro 如 = "e.g.").
VOWEL_RE = re.compile(r"[aeiouAEIOU]")
MOEDICT_LINK_TOKEN_RE = re.compile(r"`([^`~]*)~|([^`]+)")
# Chinese intro words that precede an embedded example ("e.g." / "same as").
_GLOSS_INTRO_CHARS = "如同"


def _backtick_amis_runs(raw_field: str) -> list[str]:
    """Group adjacent `…~-marked tokens into whitespace-joined Amis phrases.

    Non-markup runs that are pure whitespace keep a phrase together; any other
    non-markup text (Chinese, punctuation) breaks it. Only runs that contain a
    Latin letter are returned.
    """
    runs: list[str] = []
    current: list[str] = []
    for token, separator in MOEDICT_LINK_TOKEN_RE.findall(raw_field):
        if token:
            current.append(token)
        elif separator.strip() == "":
            current.append(separator)
        elif current:
            runs.append("".join(current))
            current = []
    if current:
        runs.append("".join(current))
    return [collapse_space(run) for run in runs if re.search(r"[A-Za-z]", run)]


def recover_embedded_example(raw_final_translation: str) -> tuple[str, str] | None:
    """Recover an empty-FORM row whose Amis is embedded in the Chinese field.

    Conservative, high-precision: only fires when the field contains exactly one
    `…~-marked Amis phrase (so multi-phrase grammar/synonym notes are skipped),
    that phrase has at least two characters and a vowel (so single pronunciation
    symbols like "h" are skipped), and a non-empty Chinese gloss follows it.
    Returns (amis_form, chinese_gloss) or None.
    """
    runs = _backtick_amis_runs(raw_final_translation)
    if len(runs) != 1:
        return None
    amis = runs[0]
    if len(amis) < 2 or not VOWEL_RE.search(amis):
        return None

    plain = clean_moedict_link_markup(raw_final_translation)
    index = plain.find(amis)
    if index < 0:
        return None
    gloss = clean_text(plain[index + len(amis) :]).strip(" .。．,，;；:：、" + _GLOSS_INTRO_CHARS)
    if not gloss or not CJK_RE.search(gloss):
        return None
    return amis, gloss


# Some source example fields packed a list of "Amis 中文gloss" pairs into the
# U+FFF9 form slot (leaving the translation slot empty), often a "；"-separated
# derivational paradigm prefixed 如/同 ("e.g."), e.g.
#   "kalacokap 當鞋子穿；kalasakaen 當菜餚吃；…"
# or a single glued "Amis sentence + Chinese translation" like "Itira 在那裡.".
# split_glued_form recovers them into (Amis, Chinese) pairs: a new pair begins
# wherever a CJK / CJK-punctuation char is followed by a fresh Amis (Latin) token,
# and within a pair the Amis precedes its Chinese gloss. Returns None when the
# field cannot be cleanly segmented (pure-Chinese notes included) -- the caller
# then drops the whole entry.
_PAIR_BOUNDARY_RE = re.compile(r"(?<=[㐀-鿿。．.，,；;、])\s*(?=[A-Za-z'’ʔ^])")
_GLUED_PAIR_RE = re.compile(r"^([A-Za-z'’ʔ^ \-]+?)[\s。．.，,；;:：、]*([㐀-鿿].*)$")


def split_glued_form(form: str) -> list[tuple[str, str]] | None:
    text = re.sub(r"^[如同\s]+", "", form).strip()
    pairs: list[tuple[str, str]] = []
    for segment in _PAIR_BOUNDARY_RE.split(text):
        segment = re.sub(r"^[如同\s]+", "", segment).strip()
        if not segment:
            continue
        match = _GLUED_PAIR_RE.match(segment)
        if not match:
            return None
        amis = collapse_space(match.group(1)).strip(" -")
        gloss = clean_text(match.group(2)).strip(" 。．.，,；;:：、")
        if len(amis) < 2 or not VOWEL_RE.search(amis) or CJK_RE.search(amis):
            return None
        if not gloss or not CJK_RE.search(gloss):
            return None
        pairs.append((amis, gloss))
    return pairs or None


# Maintainer rulings 2026-10-16/17 (Safolu review): "For spacing, we should assume spacing after ! and ?
# everywhere in this corpus. If we don't see it in the original tier, add it." and "There should be no space
# before a ? or a ! and there should be space between any ! or ? and a following Amis character."
# A closing quote or bracket directly after ! or ? stays attached. In Amis ' is a letter (the glottal stop).
_SPACE_BEFORE_BANG = re.compile(r"\s+([?!？！])")
_NO_SPACE_AFTER_BANG = re.compile(r"([?!？！])(?=[A-Za-z0-9'’ʼ^“「『])")


def normalize_bang_spacing(form: str) -> str:
    return _NO_SPACE_AFTER_BANG.sub(r"\1 ", _SPACE_BEFORE_BANG.sub(r"\1", form))


def extract_generated_moedict_examples(
    source_rows: list[dict],
    text_id: str,
    final_translation_lang: str,
    middle_translation_lang: str | None = None,
    overrides: dict[str, dict[str, object]] | None = None,
) -> tuple[list[ExampleRecord], list[dict[str, object]]]:
    records: list[ExampleRecord] = []
    rejected_records: list[dict[str, object]] = []
    source_ordinal = 0
    overrides = overrides or {}
    applied_overrides: set[str] = set()

    legacy_expansions = json.loads((ROOT / "CodeAndDocs" / "legacy_expansion_ids.json").read_text())
    for source_row in source_rows:
        source_ordinal = source_row["source_ordinal"]
        source_file = source_row["source_file"]
        title = clean_text(source_row["entry_title"])
        definition_text = clean_moedict_link_markup(source_row["definition"])
        raw_example = source_row["raw_example"]
        raw_form, raw_middle_translation, raw_final_translation = parse_marked_example(raw_example)
        form = clean_moedict_link_markup(raw_form)
        # A few source form fields begin with a stray ")" / "）" (an
        # orphaned close-paren in the original digitization); drop it.
        form = re.sub(r"^[)）]+\s*", "", form)
        final_translation = clean_moedict_link_markup(raw_final_translation)
        middle_translation = clean_moedict_link_markup(raw_middle_translation)

        notes: dict[str, object] = {
            "heteronym_index": source_row["heteronym_index"],
            "definition_index": source_row["definition_index"],
            "example_index": source_row["example_index"],
        }
        override = overrides.get(str(source_ordinal))
        if override:
            expected_form = str(override["expected_cleaned_form"])
            expected_translation = str(override["expected_cleaned_final_translation"])
            if form != expected_form or final_translation != expected_translation:
                raise ValueError(
                    f"Source override {source_ordinal} no longer matches upstream: "
                    f"expected {(expected_form, expected_translation)!r}, "
                    f"found {(form, final_translation)!r}"
                )
            applied_overrides.add(str(source_ordinal))
            notes["manual_source_override"] = True
            notes["manual_source_override_reason"] = str(override["reason"])

        if not form and not override:
            recovered = recover_form_from_translation(final_translation)
            if recovered:
                form, final_translation, annotation = recovered
                notes["recovered_form_from_translation"] = True
                if annotation:
                    notes["recovered_translation_annotation"] = annotation
            else:
                embedded = recover_embedded_example(raw_final_translation)
                if embedded:
                    form, final_translation = embedded
                    notes["recovered_form_from_note"] = True

        translations = [Translation(final_translation_lang, final_translation)] if final_translation else []
        if middle_translation:
            if middle_translation_lang and middle_translation.lower() != "undefined":
                translations.insert(0, Translation(middle_translation_lang, middle_translation))
            else:
                notes["discarded_middle_translation"] = middle_translation

        notes["source_ordinal"] = source_ordinal

        def reject(reason: str) -> None:
            rejected_records.append(
                {
                    "source_ordinal": source_ordinal,
                    "source_file": source_file,
                    "entry_title": title,
                    "definition": definition_text,
                    "raw_example": raw_example,
                    "cleaned_form": form,
                    "cleaned_final_translation": final_translation,
                    "cleaned_middle_translation": middle_translation,
                    "reject_reasons": [reason],
                    "notes": notes,
                }
            )

        if not form and not override:
            reject("empty_form")
            continue

        if override:
            emitted = []
            for item in override["emitted"]:
                if "translations" in item:
                    # several translations, e.g. an alternative one (ver="alt", POL-025)
                    item_translations = [
                        Translation(final_translation_lang, str(t["text"]), t.get("notes"), t.get("ver"))
                        for t in item["translations"]
                    ]
                else:
                    replacement_translation = str(item.get("translation", ""))
                    translation_notes = str(item.get("translation_notes", "")) or None
                    item_translations = (
                        [Translation(final_translation_lang, replacement_translation, translation_notes)]
                        if replacement_translation
                        else []
                    )
                emitted.append((str(item["form"]), item_translations))
        # The source sometimes packed Amis + Chinese (a single glued
        # pair, or a "；"-separated list) into the form slot. Split it
        # into (Amis, Chinese) pairs; drop the entry when it cannot be
        # cleanly segmented (this also catches pure-Chinese notes).
        elif CJK_RE.search(form):
            pairs = split_glued_form(form)
            if not pairs:
                reject("cjk_in_form_unsplittable")
                continue
            emitted = [(amis, [Translation(final_translation_lang, gloss)]) for amis, gloss in pairs]
            notes["split_from_cjk_form"] = len(pairs)
        else:
            emitted = [(form, translations)]

        # Historical expansion IDs are retained; new readings keep the base.
        for index, (emit_form, emit_translations) in enumerate(emitted, 1):
            base_id = f"S{source_ordinal:05d}"
            established = legacy_expansions.get(str(source_ordinal), [])
            if index <= len(established):
                sentence_id = established[index - 1]
            else:
                suffix = "" if index == 1 else "-opt" if index == 2 else f"-opt{index}"
                sentence_id = base_id + suffix
            record_notes = dict(notes)
            if not emit_translations:
                record_notes["no_translation"] = True
            records.append(
                ExampleRecord(
                    sentence_id=sentence_id,
                    source_file=source_file,
                    source_line=None,
                    entry_title=title,
                    definition=definition_text,
                    form=normalize_bang_spacing(emit_form),
                    translations=emit_translations,
                    raw_example=raw_example,
                    notes=record_notes,
                    variants=tuple(normalize_bang_spacing(v) for v in override["emitted"][index - 1].get("variants", [])) if override else (),
                )
            )


    unused_overrides = sorted(set(overrides) - applied_overrides, key=int)
    if unused_overrides:
        raise ValueError(f"Source overrides were not applied: {', '.join(unused_overrides)}")
    return records, rejected_records


def load_source_overrides(path: Path = DEFAULT_OVERRIDES_PATH) -> dict[str, dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    overrides = payload.get("overrides")
    if not isinstance(overrides, dict):
        raise ValueError(f"{path} must contain an object named 'overrides'")
    return overrides



def safolu_corpus():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    corpus = Corpus(
        text_id=SAFOLU_TEXT_ID, folder_name="Safolu",
        citation="Tsai, Chung-Han (Safolu Kacaw Lalanges). (n.d.). Amis dictionary. Provided to the g0v Amis Moedict project.",
        bibtex_citation="@misc{tsai_amis_dictionary, author={{Tsai Chung-Han (Safolu Kacaw Lalanges)}}, title={Amis dictionary}, year={n.d.}, note={Provided to the g0v Amis Moedict project}}",
        copyright="CC BY-NC-SA 3.0 TW",
        source=f"Safolu/Tsai dictionary, g0v/amis-moedict@{manifest['source_commit']} docs/s.",
        glottocode="amis1246", dialect="Coastal",
        extraction_note="Every source example field is retained or recorded as unresolved or apparatus. Shared tools own downstream processing.",
        source_repositories={"g0v/amis-moedict": manifest["source_commit"]},
    )
    records, rejected = extract_generated_moedict_examples(
        load_rows(), SAFOLU_TEXT_ID, "zho", "eng", load_source_overrides()
    )
    records += printed_additions()
    return corpus, records, rejected


def printed_additions(path: Path = PRINTED_ADDITIONS_PATH) -> list[ExampleRecord]:
    """Printed examples the pinned source lacks (see printed_additions.json), appended with new ids."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    added = []
    for item in payload["additions"]:
        added.append(ExampleRecord(
            sentence_id=item["sentence_id"],
            source_file=f"docs/s/{item['entry']}.json@{payload['upstream_commit']}",
            source_line=None,
            entry_title=item["entry"],
            definition=item["definition"],
            form=normalize_bang_spacing(item["form"]),
            translations=[Translation("zho", item["translation"])],
            raw_example="",
            notes={"source_ordinal": None, "added_from_print": item["printed"], "upstream_commit": payload["upstream_commit"]},
        ))
    return added


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml-out-dir", type=Path, required=True, help="Fresh staging XML/ directory")
    parser.add_argument("--report-dir", type=Path, help="Optional external source-audit directory")
    args = parser.parse_args()
    corpus, records, rejected = safolu_corpus()
    output = args.xml_out_dir / LANGUAGE_SUBDIR / corpus.folder_name / f"{corpus.text_id}.xml"
    write_xml(corpus, records, output)
    if args.report_dir:
        report = args.report_dir.resolve()
        if report.is_relative_to(ROOT):
            raise ValueError("Per-run source reports belong outside the repository")
        write_metadata(corpus, records, report / "source-records.json", rejected)
        (report / "excluded-fields.json").write_text(json.dumps(rejected, ensure_ascii=False, indent=2) + "\n")
    print(f"Source generation: {len(records)} records; {len(rejected)} excluded fields. Final shared processing and QC remain separate.")


if __name__ == "__main__":
    main()

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
import csv
import json
import re
import unicodedata
from dataclasses import replace
from functools import lru_cache
from pathlib import Path

from moedict_formosanbank import (
    ROOT,
    Corpus,
    ExampleRecord,
    Translation,
    clean_moedict_link_markup,
    clean_text,
    collapse_space,
    git_commit,
    iter_moedict_json_files,
    parse_marked_example,
    relative_to_root,
    write_metadata,
    write_rejected_records,
    write_xml,
)


DEFAULT_SOURCES_DIR = ROOT / "_sources"
DEFAULT_XML_OUT_DIR = ROOT / "XML"
CODEDOCS_DIR = ROOT / "CodeAndDocs"
DEFAULT_AUDIT_OUT_DIR = CODEDOCS_DIR / "_generated_audit"
DEFAULT_OVERRIDES_PATH = CODEDOCS_DIR / "data" / "safolu_source_overrides.json"
DEFAULT_CONVERSION_PATH = CODEDOCS_DIR / "data" / "orthography" / "Amis_Safolu_113.tsv"

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


def extract_generated_moedict_examples(
    source_dir: Path,
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

    for source_file in iter_moedict_json_files(source_dir):
        try:
            entry = json.loads(source_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {source_file}: {exc}") from exc
        if not isinstance(entry, dict):
            continue

        title = clean_text(str(entry.get("t", "")))
        for heteronym_index, heteronym in enumerate(entry.get("h", []), 1):
            for definition_index, definition in enumerate(heteronym.get("d", []), 1):
                definition_text = clean_moedict_link_markup(str(definition.get("f", "")))
                for example_index, raw_example in enumerate(definition.get("e", []), 1):
                    source_ordinal += 1
                    raw_form, raw_middle_translation, raw_final_translation = parse_marked_example(raw_example)
                    form = clean_moedict_link_markup(raw_form)
                    # A few source form fields begin with a stray ")" / "）" (an
                    # orphaned close-paren in the original digitization); drop it.
                    form = re.sub(r"^[)）]+\s*", "", form)
                    final_translation = clean_moedict_link_markup(raw_final_translation)
                    middle_translation = clean_moedict_link_markup(raw_middle_translation)

                    notes: dict[str, object] = {
                        "heteronym_index": heteronym_index,
                        "definition_index": definition_index,
                        "example_index": example_index,
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
                                "source_file": relative_to_root(source_file),
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
                            replacement_translation = str(item.get("translation", ""))
                            translation_notes = str(item.get("translation_notes", "")) or None
                            emitted.append(
                                (
                                    str(item["form"]),
                                    (
                                        [
                                            Translation(
                                                final_translation_lang,
                                                replacement_translation,
                                                translation_notes,
                                            )
                                        ]
                                        if replacement_translation
                                        else []
                                    ),
                                )
                            )
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

                    # Stable id derived from the source ordinal (position among ALL
                    # example fields, including rejected ones), so ids are
                    # non-contiguous but stable across rebuilds (mirrors Virginia
                    # Fey). A field that splits into N pairs gets "_1".."_N" suffixes.
                    for index, (emit_form, emit_translations) in enumerate(emitted, 1):
                        sentence_id = f"S{source_ordinal:05d}"
                        if len(emitted) > 1:
                            sentence_id = f"{sentence_id}_{index}"
                        record_notes = dict(notes)
                        if not emit_translations:
                            record_notes["no_translation"] = True
                        records.append(
                            ExampleRecord(
                                sentence_id=sentence_id,
                                source_file=relative_to_root(source_file),
                                source_line=None,
                                entry_title=title,
                                definition=definition_text,
                                form=emit_form,
                                translations=emit_translations,
                                raw_example=raw_example,
                                notes=record_notes,
                            )
                        )

    unused_overrides = sorted(set(overrides) - applied_overrides, key=int)
    if unused_overrides:
        raise ValueError(f"Source overrides were not applied: {', '.join(unused_overrides)}")
    return records, rejected_records


def sentence_id_sort_key(sentence_id: str) -> tuple[str, int]:
    """Match FormosanBank's duplicate-removal ordering exactly."""
    match = re.match(r"^(.*?)(\d+)$", sentence_id)
    if match:
        return match.group(1), int(match.group(2))
    return sentence_id, 0


_FORM_CLEAN_TRANSLATION = str.maketrans(
    {
        "⌃": "^",
        "‸": "^",
        "ˆ": "^",
        "＾": "^",
        "（": "(",
        "）": ")",
        "：": ":",
        "，": ",",
        "？": "?",
        "！": "!",
        "。": ".",
        "》": '"',
        "《": '"',
        "」": '"',
        "「": '"',
        "、": ",",
        "】": ")",
        "【": "(",
        "]": ")",
        "[": "(",
        "〔": "(",
        "〕": ")",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "ˈ": "'",
        "`": "'",
        "ʼ": "'",
        "ʻ": "'",
        "『": '"',
        "』": '"',
    }
)


def normalize_form_for_dedupe(form: str) -> str:
    """Mirror the shared clean_xml FORM normalization used before duplicate QC."""
    normalized = form.translate(_FORM_CLEAN_TRANSLATION)
    normalized = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", normalized)
    normalized = collapse_space(normalized)
    normalized = re.sub(r"([?!])\1+", r"\1", normalized)
    return re.sub(r"--+", "-", normalized)


@lru_cache(maxsize=None)
def load_standardization_mapping(
    path: Path = DEFAULT_CONVERSION_PATH,
) -> tuple[tuple[str, str], ...]:
    """Load the reviewed Safolu-to-Ortho113 table and derive case variants."""
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if not reader.fieldnames or "original" not in reader.fieldnames or "Coastal" not in reader.fieldnames:
            raise ValueError(f"{path} must have original and Coastal columns")
        rows = [
            ((row.get("original") or "").strip(), (row.get("Coastal") or "").strip())
            for row in reader
        ]

    mapping: dict[str, str] = {}
    for source, target in rows:
        if not source:
            continue
        variants: dict[str, str] = {source: target}
        if source.islower() and source.upper() != source:
            variants.setdefault(source.title(), target.title())
            variants.setdefault(source.upper(), target.upper())
        for variant_source, variant_target in variants.items():
            previous = mapping.get(variant_source)
            if previous is not None and previous != variant_target:
                raise ValueError(
                    f"Conflicting mapping for {variant_source!r}: "
                    f"{previous!r} and {variant_target!r}"
                )
            mapping.setdefault(variant_source, variant_target)
    return tuple(sorted(mapping.items(), key=lambda item: len(item[0]), reverse=True))


def standardize_coastal_form(form: str) -> str:
    """Apply the reviewed single-pass Safolu-to-Ortho113 FORM mapping."""
    decomposed = unicodedata.normalize("NFD", form)
    without_accents = "".join(
        character
        for character in decomposed
        if not unicodedata.category(character).startswith("M")
    )
    normalized = unicodedata.normalize("NFC", without_accents)
    mapping = dict(load_standardization_mapping())
    pattern = re.compile(
        "|".join(re.escape(source) for source in mapping)
    )
    return pattern.sub(lambda match: mapping[match.group(0)], normalized)


def normalize_standard_form_for_dedupe(form: str) -> str:
    """Mirror cleaning plus the reviewed standard FORM derivation."""
    return standardize_coastal_form(normalize_form_for_dedupe(form))


def merge_group_translations(group: list[ExampleRecord]) -> list[Translation]:
    """Preserve every distinct reading in source order per POL-025."""
    merged: list[Translation] = []
    seen: set[tuple[str, str]] = set()
    seen_languages: set[str] = set()
    for record in sorted(group, key=lambda item: sentence_id_sort_key(item.sentence_id)):
        for translation in record.translations:
            key = (translation.lang, translation.text)
            if key in seen:
                continue
            ver = translation.ver
            if translation.lang in seen_languages and not ver:
                ver = "alt"
            merged.append(replace(translation, ver=ver))
            seen.add(key)
            seen_languages.add(translation.lang)
    return merged


def deduplicate_records(records: list[ExampleRecord]) -> tuple[list[ExampleRecord], list[dict[str, object]]]:
    """Keep the first id per standard FORM and merge translations per POL-025."""
    groups: dict[str, list[ExampleRecord]] = {}
    for record in records:
        groups.setdefault(normalize_standard_form_for_dedupe(record.form), []).append(record)

    kept_ids: set[str] = set()
    kept_by_form: dict[str, ExampleRecord] = {}
    merged_by_id: dict[str, ExampleRecord] = {}
    for normalized_form, group in groups.items():
        kept = min(group, key=lambda record: sentence_id_sort_key(record.sentence_id))
        kept_ids.add(kept.sentence_id)
        kept_by_form[normalized_form] = kept
        merged_by_id[kept.sentence_id] = replace(
            kept,
            translations=merge_group_translations(group),
        )

    duplicates: list[dict[str, object]] = []
    for record in records:
        if record.sentence_id in kept_ids:
            continue
        standard_form = normalize_standard_form_for_dedupe(record.form)
        kept = kept_by_form[standard_form]
        duplicates.append(
            {
                "dropped_sentence_id": record.sentence_id,
                "kept_sentence_id": kept.sentence_id,
                "normalized_standard_form": standard_form,
                "dropped_record": record.to_metadata(),
            }
        )
    return [merged_by_id[record.sentence_id] for record in records if record.sentence_id in kept_ids], duplicates


def load_source_overrides(path: Path = DEFAULT_OVERRIDES_PATH) -> dict[str, dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    overrides = payload.get("overrides")
    if not isinstance(overrides, dict):
        raise ValueError(f"{path} must contain an object named 'overrides'")
    return overrides


def safolu_corpus(
    sources_dir: Path,
) -> tuple[Corpus, list[ExampleRecord], list[dict[str, object]], list[dict[str, object]]]:
    amis_moedict = sources_dir / "amis-moedict"
    amis_safolu = sources_dir / "amis-safolu"
    amis_moedict_commit = git_commit(amis_moedict)
    amis_safolu_commit = git_commit(amis_safolu)
    corpus = Corpus(
        text_id=SAFOLU_TEXT_ID,
        folder_name="Safolu",
        citation=(
            "Tsai, Chung-Han (Safolu Kacaw Lalanges). (n.d.). Amis dictionary. "
            "Provided to the g0v Amis Moedict project."
        ),
        bibtex_citation=(
            "@misc{tsai_amis_dictionary, "
            "author={{Tsai Chung-Han (Safolu Kacaw Lalanges)}}, "
            "title={Amis dictionary}, "
            "year={n.d.}, "
            "note={Provided to the g0v Amis Moedict project}}"
        ),
        copyright=(
            "CC BY-NC according to the frozen amis-safolu README; current data source is "
            "g0v/amis-moedict docs/s."
        ),
        source=(
            f"Current Safolu/Tsai generated Moedict JSON from g0v/amis-moedict@{amis_moedict_commit} docs/s; "
            f"deprecated generator repository miaoski/amis-safolu@{amis_safolu_commit} documents the pipeline."
        ),
        glottocode="amis1246",
        dialect="Coastal",
        extraction_note=(
            "Extracted every example field from g0v/amis-moedict docs/s JSON. "
            "Virginia Fey docs/p is intentionally excluded because it was already processed separately. "
            "Confirmed source-digitization errors are corrected by fail-closed, ordinal-keyed overrides."
        ),
        source_repositories={
            "g0v/amis-moedict": amis_moedict_commit,
            "miaoski/amis-safolu": amis_safolu_commit,
        },
    )
    records, rejected_records = extract_generated_moedict_examples(
        amis_moedict / "docs" / "s",
        text_id=SAFOLU_TEXT_ID,
        final_translation_lang="zho",
        middle_translation_lang="eng",
        overrides=load_source_overrides(),
    )
    records, duplicates = deduplicate_records(records)
    return corpus, records, rejected_records, duplicates


def write_corpus(
    corpus: Corpus,
    records: list[ExampleRecord],
    rejected_records: list[dict[str, object]],
    duplicates: list[dict[str, object]],
    xml_out_dir: Path,
    audit_out_dir: Path,
) -> None:
    xml_corpus_dir = xml_out_dir / LANGUAGE_SUBDIR / corpus.folder_name
    audit_corpus_dir = audit_out_dir / corpus.folder_name
    xml_path = xml_corpus_dir / f"{corpus.text_id}.xml"
    metadata_path = audit_corpus_dir / f"{corpus.text_id}.metadata.json"
    rejected_path = audit_corpus_dir / f"{corpus.text_id}.rejected.json"
    duplicates_path = audit_corpus_dir / f"{corpus.text_id}.duplicates.json"
    write_xml(corpus, records, xml_path)
    write_metadata(corpus, records, metadata_path, rejected_records)
    write_rejected_records(rejected_records, rejected_path)
    duplicates_path.write_text(
        json.dumps(
            {
                "description": (
                    "Source rows excluded because their reviewed Safolu-to-Ortho113 standard FORM "
                    "duplicates an earlier sentence id. Distinct translations are merged into the "
                    "survivor as alternative readings under POL-025."
                ),
                "duplicate_count": len(duplicates),
                "duplicates": duplicates,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_corpus_readme(corpus, records, rejected_records, duplicates, audit_corpus_dir)
    print(f"Wrote {len(records)} examples to {xml_path}")
    print(f"Wrote metadata to {metadata_path}")
    print(f"Wrote {len(rejected_records)} rejected source records to {rejected_path}")
    print(f"Wrote {len(duplicates)} duplicate records to {duplicates_path}")


def write_corpus_readme(
    corpus: Corpus,
    records: list[ExampleRecord],
    rejected_records: list[dict[str, object]],
    duplicates: list[dict[str, object]],
    corpus_dir: Path,
) -> None:
    corpus_dir.mkdir(parents=True, exist_ok=True)
    translation_languages = ", ".join(
        sorted({translation.lang for record in records for translation in record.translations})
    )
    text = f"""# {corpus.folder_name} Audit

Audit package for `{corpus.text_id}`.

- XML: `XML/{LANGUAGE_SUBDIR}/{corpus.folder_name}/{corpus.text_id}.xml`
- Metadata: `{corpus.text_id}.metadata.json`
- Rejected source records: `{corpus.text_id}.rejected.json`
- Duplicate records: `{corpus.text_id}.duplicates.json`
- XML sentence count: {len(records):,}
- Rejected source-record count: {len(rejected_records):,}
- Duplicate sentence count: {len(duplicates):,}
- Translation languages: {translation_languages}

The XML file is the canonical FormosanBank artifact. This audit folder documents provenance and source coverage without placing non-XML files in `XML`.
"""
    (corpus_dir / "README.md").write_text(text, encoding="utf-8")


def write_root_readme(
    corpora: list[
        tuple[Corpus, list[ExampleRecord], list[dict[str, object]], list[dict[str, object]]]
    ],
    out_dir: Path,
) -> None:
    rows = "\n".join(
        f"- `{LANGUAGE_SUBDIR}/{corpus.folder_name}/{corpus.text_id}.xml`: {len(records):,} sentences; "
        f"{len(rejected_records):,} rejected source records; {len(duplicates):,} duplicates audited"
        for corpus, records, rejected_records, duplicates in corpora
    )
    text = f"""# FormosanBank Audit

Audit files for the finalized FormosanBank XML export of the Safolu Amis dictionary.

{rows}

These XML files contain example sentence / phrase translation pairs. Headwords and definitions are preserved in metadata.

Virginia Fey (`g0v/amis-moedict/docs/p`) is intentionally excluded because it was already processed separately. The Poinsot dictionary (`docs/m`) lives in the Formosan-Poinsot-Amis-Dictionary repository.

Final XML files live under `XML`, which intentionally contains only `.xml` files. The JSON files in this directory are durable source-provenance ledgers. Per-run audit and QC reports are written outside the repository.
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources-dir", type=Path, default=DEFAULT_SOURCES_DIR)
    parser.add_argument("--xml-out-dir", type=Path, default=DEFAULT_XML_OUT_DIR)
    parser.add_argument("--audit-out-dir", type=Path, default=DEFAULT_AUDIT_OUT_DIR)
    args = parser.parse_args()

    sources_dir = args.sources_dir.resolve()
    xml_out_dir = args.xml_out_dir.resolve()
    audit_out_dir = args.audit_out_dir.resolve()

    selected = [safolu_corpus(sources_dir)]
    for corpus, records, rejected_records, duplicates in selected:
        write_corpus(corpus, records, rejected_records, duplicates, xml_out_dir, audit_out_dir)
    write_root_readme(selected, audit_out_dir)


if __name__ == "__main__":
    main()

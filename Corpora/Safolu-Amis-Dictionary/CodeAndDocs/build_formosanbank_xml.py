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
import hashlib
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
    git_commit,
    iter_moedict_json_files,
    parse_marked_example,
    relative_to_root,
    write_metadata,
    write_rejected_records,
    write_xml,
)


DEFAULT_SOURCES_DIR = ROOT / "_sources"
DEFAULT_XML_OUT_DIR = ROOT / "Final_XML"
DEFAULT_AUDIT_OUT_DIR = ROOT / "data" / "formosanbank_audit"

# The finalized XML is grouped language-first (Final_XML/Amis/<Source>/) to match
# FormosanBank's Corpora/<Name>/XML/<Language>/ convention.
LANGUAGE_SUBDIR = "Amis"

SAFOLU_TEXT_ID = "amis_safolu_examples"
CJK_RE = re.compile(r"[㐀-鿿]")


# Leading source annotations that precede the Amis phrase, e.g. loanword notes
# like "〔閩南語借詞〕", "(漢語借詞)", or "（英語借詞）". They are kept with the
# translation, not treated as the FORM.
_LEADING_ANNOTATIONS = (("〔", "〕"), ("(", ")"), ("（", "）"))


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
) -> tuple[list[ExampleRecord], list[dict[str, object]]]:
    records: list[ExampleRecord] = []
    rejected_records: list[dict[str, object]] = []
    source_ordinal = 0

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
                    if not form:
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

                    if not form:
                        reject("empty_form")
                        continue

                    # The source sometimes packed Amis + Chinese (a single glued
                    # pair, or a "；"-separated list) into the form slot. Split it
                    # into (Amis, Chinese) pairs; drop the entry when it cannot be
                    # cleanly segmented (this also catches pure-Chinese notes).
                    if CJK_RE.search(form):
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

    return records, rejected_records


def safolu_corpus(sources_dir: Path) -> tuple[Corpus, list[ExampleRecord], list[dict[str, object]]]:
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
        extraction_note=(
            "Extracted every example field from g0v/amis-moedict docs/s JSON. "
            "Virginia Fey docs/p is intentionally excluded because it was already processed separately."
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
    )
    return corpus, records, rejected_records


def write_corpus(
    corpus: Corpus,
    records: list[ExampleRecord],
    rejected_records: list[dict[str, object]],
    xml_out_dir: Path,
    audit_out_dir: Path,
) -> None:
    xml_corpus_dir = xml_out_dir / LANGUAGE_SUBDIR / corpus.folder_name
    audit_corpus_dir = audit_out_dir / corpus.folder_name
    xml_path = xml_corpus_dir / f"{corpus.text_id}.xml"
    metadata_path = audit_corpus_dir / f"{corpus.text_id}.metadata.json"
    rejected_path = audit_corpus_dir / f"{corpus.text_id}.rejected.json"
    write_xml(corpus, records, xml_path)
    write_metadata(corpus, records, metadata_path, rejected_records)
    write_rejected_records(rejected_records, rejected_path)
    write_corpus_readme(corpus, records, rejected_records, audit_corpus_dir)
    print(f"Wrote {len(records)} examples to {xml_path}")
    print(f"Wrote metadata to {metadata_path}")
    print(f"Wrote {len(rejected_records)} rejected source records to {rejected_path}")


def write_corpus_readme(
    corpus: Corpus,
    records: list[ExampleRecord],
    rejected_records: list[dict[str, object]],
    corpus_dir: Path,
) -> None:
    corpus_dir.mkdir(parents=True, exist_ok=True)
    translation_languages = ", ".join(
        sorted({translation.lang for record in records for translation in record.translations})
    )
    text = f"""# {corpus.folder_name} Audit

Audit package for `{corpus.text_id}`.

- XML: `Final_XML/{LANGUAGE_SUBDIR}/{corpus.folder_name}/{corpus.text_id}.xml`
- Metadata: `{corpus.text_id}.metadata.json`
- Rejected source records: `{corpus.text_id}.rejected.json`
- XML sentence count: {len(records):,}
- Rejected source-record count: {len(rejected_records):,}
- Translation languages: {translation_languages}

The XML file is the finalized FormosanBank artifact. This audit folder documents provenance and source coverage without placing non-XML files in `Final_XML`.
"""
    (corpus_dir / "README.md").write_text(text, encoding="utf-8")


def write_manifest(
    corpora: list[tuple[Corpus, list[ExampleRecord], list[dict[str, object]]]],
    xml_out_dir: Path,
    audit_out_dir: Path,
) -> None:
    audit_out_dir.mkdir(parents=True, exist_ok=True)

    def file_info(base_dir: Path, relative_path: str) -> dict[str, object]:
        path = base_dir / relative_path
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return {
            "path": str(path.relative_to(ROOT)),
            "size_bytes": path.stat().st_size,
            "sha256": digest,
        }

    manifest = {
        "description": "FormosanBank XML export of the Safolu (Tsai) Amis dictionary from g0v amis-moedict docs/s.",
        "excluded_sources": [
            {"path": "g0v/amis-moedict/docs/p", "reason": "Virginia Fey dictionary already processed separately"},
            {"path": "g0v/amis-moedict/docs/m", "reason": "Poinsot dictionary moved to the Formosan-Poinsot-Amis-Dictionary repository"},
        ],
        "corpora": [
            {
                "text_id": corpus.text_id,
                "folder": corpus.folder_name,
                "xml": file_info(xml_out_dir, f"{LANGUAGE_SUBDIR}/{corpus.folder_name}/{corpus.text_id}.xml"),
                "metadata": file_info(audit_out_dir, f"{corpus.folder_name}/{corpus.text_id}.metadata.json"),
                "rejected": file_info(audit_out_dir, f"{corpus.folder_name}/{corpus.text_id}.rejected.json"),
                "example_count": len(records),
                "rejected_example_count": len(rejected_records),
                "translation_languages": sorted(
                    {translation.lang for record in records for translation in record.translations}
                ),
                "source_repositories": corpus.source_repositories,
            }
            for corpus, records, rejected_records in corpora
        ],
    }
    manifest_path = audit_out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_root_readme(corpora, audit_out_dir)
    print(f"Wrote manifest to {manifest_path}")


def write_root_readme(corpora: list[tuple[Corpus, list[ExampleRecord], list[dict[str, object]]]], out_dir: Path) -> None:
    rows = "\n".join(
        f"- `{LANGUAGE_SUBDIR}/{corpus.folder_name}/{corpus.text_id}.xml`: {len(records):,} sentences; "
        f"{len(rejected_records):,} rejected source records audited"
        for corpus, records, rejected_records in corpora
    )
    text = f"""# FormosanBank Audit

Audit files for the finalized FormosanBank XML export of the Safolu Amis dictionary.

{rows}

These XML files contain example sentence / phrase translation pairs. Headwords and definitions are preserved in metadata.

Virginia Fey (`g0v/amis-moedict/docs/p`) is intentionally excluded because it was already processed separately. The Poinsot dictionary (`docs/m`) lives in the Formosan-Poinsot-Amis-Dictionary repository.

Final XML files live under `Final_XML`, which intentionally contains only `.xml` files. For coverage details, see `coverage_audit.json` and the repository-level `SOURCE_AUDIT.md`.
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
    for corpus, records, rejected_records in selected:
        write_corpus(corpus, records, rejected_records, xml_out_dir, audit_out_dir)
    write_manifest(selected, xml_out_dir, audit_out_dir)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Verify that every emitted NTU sentence retains its source ``#n`` notes."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import parse_grammar
import parse_sentences
import parse_stories


HERE = Path(__file__).resolve().parent
CODEDOCS = HERE.parent


class NoteAudit:
    def __init__(self, xml_dir: Path):
        self.xml_dir = xml_dir
        self.roots: dict[Path, ET.Element] = {}
        self.stats = Counter()

    def sentence(self, relative: Path, sentence_id: str) -> ET.Element:
        path = self.xml_dir / relative
        if path not in self.roots:
            if not path.is_file():
                raise AssertionError(f"expected parser XML missing: {path}")
            self.roots[path] = ET.parse(path).getroot()
        matches = [
            sentence for sentence in self.roots[path].findall("S")
            if sentence.get("id") == sentence_id
        ]
        if len(matches) != 1:
            raise AssertionError(
                f"expected one {sentence_id!r} in {relative}; "
                f"found {len(matches)}"
            )
        return matches[0]

    def check(self, category: str, relative: Path, sentence_id: str,
              expected: str | None) -> None:
        sentence = self.sentence(relative, sentence_id)
        form = sentence.find("FORM[@kindOf='original']")
        if form is None:
            raise AssertionError(
                f"original FORM missing for {relative}:{sentence_id}"
            )
        actual = form.get("notes", "")
        # XML 1.0 normalizes literal tabs and line breaks in attribute values
        # to spaces when a document is parsed. Compare against that required
        # representation while retaining every non-whitespace source byte.
        expected_xml = (expected or "").translate(
            {ord("\t"): " ", ord("\r"): " ", ord("\n"): " "}
        )
        expected_count = expected_xml.count("source note: ")
        actual_count = actual.count("source note: ")
        if expected_xml and expected_xml not in actual:
            raise AssertionError(
                f"source note text missing for {relative}:{sentence_id}; "
                f"expected {expected_xml!r}, found {actual!r}"
            )
        if actual_count != expected_count:
            raise AssertionError(
                f"source note count drifted for {relative}:{sentence_id}; "
                f"expected {expected_count}, found {actual_count}"
            )
        self.stats[f"{category} sentences"] += 1
        self.stats[f"{category} source notes"] += expected_count


def audit_stories(audit: NoteAudit) -> None:
    for folder in sorted((CODEDOCS / "story").iterdir()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        language = folder.name.split("_", 1)[0]
        for source in sorted(folder.glob("*.json")):
            data = json.loads(source.read_text(encoding="utf-8"))["glosses"]
            data = parse_stories.apply_story_gloss_repairs(data, source.name)
            with contextlib.redirect_stdout(io.StringIO()):
                story = parse_stories.get_story(data, src=str(source))[1:]
            relative = Path("Stories", language,
                             f"{language}_{source.stem}.xml")
            for sentence in story:
                audit.check(
                    "Stories", relative,
                    f"{source.stem}_S_{sentence['id']}",
                    sentence.get("source_notes"),
                )


def audit_grammar(audit: NoteAudit) -> None:
    for folder in sorted((CODEDOCS / "grammar").iterdir()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        language = folder.name.split("_", 1)[0]
        relative = Path("Grammar", language, f"{language}.xml")
        for source in sorted(folder.glob("*.json")):
            data = json.loads(source.read_text(encoding="utf-8"))["glosses"]
            with contextlib.redirect_stdout(io.StringIO()):
                sentences = parse_grammar.get_grammar(
                    data, src=str(source), lang=language,
                    is_wordlist="A2" in source.name,
                )
            for sentence in sentences:
                base = f"{source.stem}_S_{sentence['id']}"
                if "sentence_variants" in sentence:
                    ids = [
                        f"{base}{chr(ord('a') + index)}"
                        for index, _ in enumerate(sentence["sentence_variants"])
                    ]
                elif "A2" in source.name and "ori_variants" in sentence:
                    ids = [
                        f"{base}{chr(ord('a') + index)}"
                        for index, _ in enumerate(sentence["ori_variants"])
                    ]
                else:
                    ids = [base]
                for sentence_id in ids:
                    audit.check(
                        "Grammar", relative, sentence_id,
                        sentence.get("source_notes"),
                    )


def audit_sentences(audit: NoteAudit) -> None:
    for folder_name in os.listdir(CODEDOCS / "sentence"):
        folder = CODEDOCS / "sentence" / folder_name
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        language = folder.name.split("_", 1)[0]
        relative = Path("Sentences", language, f"{language}.xml")
        seen_ids: Counter[str] = Counter()
        with tempfile.NamedTemporaryFile(suffix=".csv") as slash_log:
            for source_name in os.listdir(folder):
                source = folder / source_name
                if not source.is_file() or source.suffix != ".json":
                    continue
                data = json.loads(source.read_text(encoding="utf-8"))["glosses"]
                with contextlib.redirect_stdout(io.StringIO()):
                    sentences = parse_sentences.get_sentences(
                        data, src=str(source)
                    )
                for sentence in sentences:
                    if language == "Kanakanavu":
                        with contextlib.redirect_stdout(io.StringIO()):
                            expanded = parse_sentences.expand_sentence_alternatives(
                                sentence, language, source.stem, slash_log.name
                            )
                        if expanded == []:
                            continue
                        variants = expanded if expanded is not None else [sentence]
                    else:
                        variants = [sentence]

                    for variant in variants:
                        sentence_id = f"{source.stem}_S_{variant['id']}"
                        seen_ids[sentence_id] += 1
                        if seen_ids[sentence_id] > 1:
                            sentence_id += f"-{seen_ids[sentence_id]}"
                        audit.check(
                            "Sentences", relative, sentence_id,
                            variant.get("source_notes"),
                        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--xml_dir", type=Path, default=CODEDOCS / "Final_XML"
    )
    args = parser.parse_args()
    audit = NoteAudit(args.xml_dir.resolve())
    audit_stories(audit)
    audit_grammar(audit)
    audit_sentences(audit)

    print("Source-note audit passed")
    for label in (
        "Grammar sentences", "Grammar source notes",
        "Sentences sentences", "Sentences source notes",
        "Stories sentences", "Stories source notes",
    ):
        print(f"  {label}: {audit.stats[label]:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

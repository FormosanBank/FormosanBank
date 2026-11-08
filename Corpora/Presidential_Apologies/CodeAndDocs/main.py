#!/usr/bin/env python3
"""Generate source-tier XML for the Presidential Apologies corpus."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
CONFIG_PATH = HERE / "data" / "dialect_authority.tsv"


@dataclass(frozen=True)
class LanguageSpec:
    language: str
    iso_639_3: str
    dialect: str
    sections: int
    text_id: str
    glottocode: str
    source_file: Path
    chinese_file: Path
    english_file: Path


def load_specs(path: Path = CONFIG_PATH) -> tuple[LanguageSpec, ...]:
    """Load the external language, source, and dialect mapping."""
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if not rows:
        raise ValueError(f"no language rows in {path}")

    specs = tuple(
        LanguageSpec(
            language=row["language"],
            iso_639_3=row["iso_639_3"],
            dialect=row["dialect"],
            sections=int(row["sections"]),
            text_id=row["text_id"],
            glottocode=row.get("glottocode") or "",
            source_file=HERE / row["source_file"],
            chinese_file=HERE / row["chinese_file"],
            english_file=HERE / row["english_file"],
        )
        for row in rows
    )
    languages = [spec.language for spec in specs]
    text_ids = [spec.text_id for spec in specs]
    if len(languages) != len(set(languages)):
        raise ValueError("language names must be unique")
    if len(text_ids) != len(set(text_ids)):
        raise ValueError("TEXT IDs must be unique")
    return specs


def read_sections(path: Path, expected: int) -> list[str]:
    """Read non-empty source sections and enforce the recorded count."""
    sections = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    if len(sections) != expected:
        raise ValueError(f"{path}: expected {expected} sections, found {len(sections)}")
    empty = [index for index, text in enumerate(sections) if not text]
    if empty:
        raise ValueError(f"{path}: empty sections at zero-based indexes {empty}")
    return sections


def prettify(root: Element) -> str:
    """Serialize XML in the stable FormosanBank indentation style."""
    parsed = minidom.parseString(tostring(root, encoding="utf-8"))
    lines = parsed.toprettyxml(indent="    ").splitlines()
    return "\n".join(line for line in lines if line.strip())


def build_document(spec: LanguageSpec) -> Element:
    """Build one source-tier TEXT element from the recorded source mapping."""
    original = read_sections(spec.source_file, spec.sections)
    chinese = read_sections(spec.chinese_file, spec.sections)
    english = read_sections(spec.english_file, spec.sections)
    citation = (
        "Tsai, I. W. (2016, August 1). President Tsai Ing-wen's apology "
        "to the Indigenous Peoples on behalf of the government "
        f"[Speech transcript, {spec.language} translation]. "
        "https://indigenous-justice.president.gov.tw/"
    )
    bibtex = (
        f"@misc{{PA_{spec.language}, author = {{Tsai, Ing-Wen}}, "
        "title = {President Tsai Ing-wen's apology to the Indigenous Peoples "
        "on behalf of the government}, year = {2016}, month = {August}, "
        "day = {1}, note = {[Speech transcript, "
        f"{spec.language} translation]}}, "
        "url = {https://indigenous-justice.president.gov.tw/} }"
    )
    root = Element(
        "TEXT",
        {
            "id": spec.text_id,
            "xml:lang": spec.iso_639_3,
            "source": f"Presidential apology to indigenous people in {spec.language}",
            "copyright": "public domain",
            "citation": citation,
            "BibTeX_citation": bibtex,
            "dialect": spec.dialect,
        },
    )
    if spec.glottocode:
        root.set("glottocode", spec.glottocode)

    for index, (form_text, chinese_text, english_text) in enumerate(
        zip(original, chinese, english, strict=True)
    ):
        sentence = SubElement(root, "S", {"id": str(index)})
        form = SubElement(sentence, "FORM", {"kindOf": "original"})
        form.text = form_text
        translation = SubElement(sentence, "TRANSL", {"xml:lang": "zho"})
        translation.text = chinese_text
        translation = SubElement(sentence, "TRANSL", {"xml:lang": "eng"})
        translation.text = english_text
    return root


def generate_all(output_dir: Path, specs: tuple[LanguageSpec, ...] | None = None) -> int:
    """Write all configured XML files and return the sentence count."""
    configured = specs or load_specs()
    total = 0
    for spec in configured:
        destination = output_dir / spec.language / f"{spec.language}.xml"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(prettify(build_document(spec)), encoding="utf-8")
        total += spec.sections
    return total


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "XML",
        help="destination for canonical language subdirectories",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    specs = load_specs()
    total = generate_all(args.output_dir, specs)
    print(f"generated {len(specs)} XML files with {total} sentences")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

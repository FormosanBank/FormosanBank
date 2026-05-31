#!/usr/bin/env python3
"""sample_sentences.py — output N randomly chosen <S> elements for manual review.

A maintainer-facing spot-check tool. Picks N <S> elements at random from a
corpus and formats them as a readable markdown report suitable for printing
or emailing to an expert reviewer. Per roadmap B9.7.

Per-S output: id, language, source file, original FORM, standard FORM (if
different), TRANSL text by language, and AUDIO file references.

Usage:
    python QC/utilities/sample_sentences.py --corpus_path Corpora/ePark
    python QC/utilities/sample_sentences.py --corpus_path Corpora/ePark --n 30 --seed 42
    python QC/utilities/sample_sentences.py --corpus_path Corpora/ePark --output sample.md

If `<corpus_path>/XML/` exists, only that subdirectory is walked (matches the
validator's canonical-walk convention). Otherwise `<corpus_path>/` is walked
in full, for corpora that haven't been re-laid-out into the canonical
structure yet.
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

from lxml import etree


XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def collect_sentences(corpus_path: Path) -> list[dict]:
    """Walk corpus_path and return a list of S-element records.

    A record is a dict with keys: file, text_id, s_id, lang, original,
    standard, translations (dict lang -> text), audio_files (list).

    Files that fail XML parse are skipped silently.
    """
    xml_dir = corpus_path / "XML"
    walk_root = xml_dir if xml_dir.is_dir() else corpus_path
    records: list[dict] = []
    for xml_path in sorted(walk_root.rglob("*.xml")):
        try:
            tree = etree.parse(str(xml_path))
        except etree.XMLSyntaxError:
            continue
        root = tree.getroot()
        if root.tag != "TEXT":
            continue
        text_lang = root.get(XML_LANG) or ""
        text_id = root.get("id") or ""
        for s in tree.iter("S"):
            record: dict = {
                "file": str(xml_path),
                "text_id": text_id,
                "s_id": s.get("id") or "",
                "lang": text_lang,
                "original": "",
                "standard": "",
                "translations": {},
                "audio_files": [],
            }
            for form in s.findall("FORM"):
                kind = form.get("kindOf") or ""
                txt = (form.text or "").strip()
                if kind == "original":
                    record["original"] = txt
                elif kind == "standard":
                    record["standard"] = txt
            for transl in s.findall("TRANSL"):
                lang = transl.get(XML_LANG) or "(unset)"
                txt = (transl.text or "").strip()
                # Multiple TRANSLs in the same language get joined with " | ".
                if lang in record["translations"]:
                    record["translations"][lang] += " | " + txt
                else:
                    record["translations"][lang] = txt
            for audio in s.findall("AUDIO"):
                file_attr = audio.get("file")
                if file_attr:
                    record["audio_files"].append(file_attr)
            records.append(record)
    return records


def format_markdown(records: list[dict], corpus_path: Path) -> str:
    """Format a sample as a markdown report ready to print or email."""
    lines: list[str] = [
        f"# Random sentence sample — `{corpus_path}`",
        "",
        f"Sample size: **{len(records)}** sentences.",
        "",
        "---",
        "",
    ]
    for i, r in enumerate(records, 1):
        lines.append(f"## {i}. S id `{r['s_id']}` ({r['lang'] or 'lang unset'})")
        lines.append("")
        lines.append(f"- **File:** `{r['file']}`")
        if r["text_id"]:
            lines.append(f"- **TEXT id:** `{r['text_id']}`")
        if r["original"]:
            lines.append(f"- **Original:** {r['original']}")
        if r["standard"] and r["standard"] != r["original"]:
            lines.append(f"- **Standard:** {r['standard']}")
        for lang, txt in sorted(r["translations"].items()):
            lines.append(f"- **TRANSL ({lang}):** {txt}")
        if r["audio_files"]:
            lines.append(f"- **Audio:** {', '.join(r['audio_files'])}")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Sample N random S elements from a corpus and format them for "
            "manual expert review. Output is markdown by default."
        ),
    )
    p.add_argument(
        "--corpus_path",
        required=True,
        type=Path,
        help=(
            "Path to a corpus directory (typically Corpora/<Name>/). If "
            "<corpus_path>/XML/ exists, only that subdirectory is walked."
        ),
    )
    p.add_argument(
        "--n",
        type=int,
        default=20,
        help="Number of S elements to sample (default: 20). Capped at "
             "the corpus's total S count if smaller.",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility (default: nondeterministic).",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write the report to this file instead of stdout.",
    )
    args = p.parse_args(argv)

    if not args.corpus_path.is_dir():
        print(
            f"corpus_path {args.corpus_path} is not a directory",
            file=sys.stderr,
        )
        return 1

    records = collect_sentences(args.corpus_path)
    if not records:
        print(
            f"No <S> elements found under {args.corpus_path}",
            file=sys.stderr,
        )
        return 1

    rng = random.Random(args.seed)
    n = min(args.n, len(records))
    sample = rng.sample(records, n)
    sample.sort(key=lambda r: (r["file"], r["s_id"]))
    report = format_markdown(sample, args.corpus_path)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print(f"Wrote {n} sentences to {args.output}", file=sys.stderr)
    else:
        print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())

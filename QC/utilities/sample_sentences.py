#!/usr/bin/env python3
"""sample_sentences.py — output N randomly chosen <S> elements for manual review.

A maintainer-facing spot-check tool. Picks N <S> elements at random from a
corpus and formats them as a readable markdown report suitable for printing
or emailing to an expert reviewer. Per roadmap B9.7.

Per-S output: id, language, source file, FORM by kindOf
(original/standard/alternate), PHON, TRANSL by language, AUDIO file
references, and the full W (word) tier including each W's
FORM/PHON/TRANSL/AUDIO and its M (morpheme) children with the same fields.

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

# The three FORM/@kindOf values enumerated by xml_template.xsd. Anything else
# would be schema-invalid; the validator catches it, so we silently drop it
# here rather than inventing a fourth bucket.
FORM_KINDS = ("original", "standard", "alternate")


def _collect_forms(elem) -> dict[str, str]:
    """Return {kindOf: text} for FORM children of `elem`. Unknown kinds dropped."""
    out: dict[str, str] = {}
    for form in elem.findall("FORM"):
        kind = form.get("kindOf") or ""
        if kind not in FORM_KINDS:
            continue
        out[kind] = (form.text or "").strip()
    return out


def _collect_translations(elem) -> dict[str, str]:
    """Return TRANSL text grouped by xml:lang. Missing xml:lang -> '(unset)'.
    Multiple TRANSLs in the same language are joined with ' | '."""
    translations: dict[str, str] = {}
    for transl in elem.findall("TRANSL"):
        lang = transl.get(XML_LANG) or "(unset)"
        txt = (transl.text or "").strip()
        if lang in translations:
            translations[lang] += " | " + txt
        else:
            translations[lang] = txt
    return translations


def _collect_phons(elem) -> list[tuple[str, str]]:
    """Return list of (kindOf, text) for PHON children of `elem`."""
    out: list[tuple[str, str]] = []
    for phon in elem.findall("PHON"):
        kind = phon.get("kindOf") or ""
        txt = (phon.text or "").strip()
        out.append((kind, txt))
    return out


def _collect_audio(elem) -> list[str]:
    """Return AUDIO file= attributes for AUDIO children of `elem`."""
    files: list[str] = []
    for audio in elem.findall("AUDIO"):
        file_attr = audio.get("file")
        if file_attr:
            files.append(file_attr)
    return files


def _collect_morpheme(m) -> dict:
    return {
        "id": m.get("id") or "",
        "class": m.get("class") or "",
        "sclass": m.get("sclass") or "",
        "forms": _collect_forms(m),
        "translations": _collect_translations(m),
        "phons": _collect_phons(m),
        "audio_files": _collect_audio(m),
    }


def _collect_word(w) -> dict:
    return {
        "id": w.get("id") or "",
        "class": w.get("class") or "",
        "sclass": w.get("sclass") or "",
        "forms": _collect_forms(w),
        "translations": _collect_translations(w),
        "phons": _collect_phons(w),
        "audio_files": _collect_audio(w),
        "morphemes": [_collect_morpheme(m) for m in w.findall("M")],
    }


def collect_sentences(corpus_path: Path) -> list[dict]:
    """Walk corpus_path and return a list of S-element records.

    A record is a dict with keys: file, text_id, s_id, lang, forms,
    translations, phons, audio_files, words. `forms` is a dict keyed by
    kindOf (original/standard/alternate); missing kinds are absent.

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
            records.append({
                "file": str(xml_path),
                "text_id": text_id,
                "s_id": s.get("id") or "",
                "lang": text_lang,
                "forms": _collect_forms(s),
                "translations": _collect_translations(s),
                "phons": _collect_phons(s),
                "audio_files": _collect_audio(s),
                "words": [_collect_word(w) for w in s.findall("W")],
            })
    return records


def _format_form_inline(forms: dict[str, str]) -> str:
    """Inline rendering of a forms dict for W/M lines.

    Collapses to a single quoted form when all present forms share the same
    text. Otherwise labels every present form. Empty string when no FORM at all.
    """
    present = [(k, forms[k]) for k in FORM_KINDS if forms.get(k)]
    if not present:
        return ""
    texts = {text for _, text in present}
    if len(texts) == 1:
        return f': "{present[0][1]}"'
    return ": " + ", ".join(f'{k}="{t}"' for k, t in present)


def _format_attr_suffix(class_: str, sclass: str) -> str:
    bits = []
    if class_:
        bits.append(f"class={class_}")
    if sclass:
        bits.append(f"sclass={sclass}")
    return f" ({', '.join(bits)})" if bits else ""


def _format_morpheme_lines(m: dict) -> list[str]:
    lines: list[str] = []
    attr_str = _format_attr_suffix(m["class"], m["sclass"])
    form_str = _format_form_inline(m["forms"])
    transl_inline = ""
    if m["translations"]:
        transl_inline = " — " + "; ".join(
            f"{lang}: {txt}" for lang, txt in sorted(m["translations"].items())
        )
    lines.append(f"      - M `{m['id']}`{attr_str}{form_str}{transl_inline}")
    for kind, txt in m["phons"]:
        label = f"PHON ({kind})" if kind else "PHON"
        lines.append(f"        - {label}: {txt}")
    if m["audio_files"]:
        lines.append(f"        - Audio: {', '.join(m['audio_files'])}")
    return lines


def _format_word_lines(w: dict) -> list[str]:
    lines: list[str] = []
    attr_str = _format_attr_suffix(w["class"], w["sclass"])
    form_str = _format_form_inline(w["forms"])
    lines.append(f"  - W `{w['id']}`{attr_str}{form_str}")
    for lang, txt in sorted(w["translations"].items()):
        lines.append(f"    - TRANSL ({lang}): {txt}")
    for kind, txt in w["phons"]:
        label = f"PHON ({kind})" if kind else "PHON"
        lines.append(f"    - {label}: {txt}")
    if w["audio_files"]:
        lines.append(f"    - Audio: {', '.join(w['audio_files'])}")
    if w["morphemes"]:
        lines.append("    - Morphemes:")
        for m in w["morphemes"]:
            lines.extend(_format_morpheme_lines(m))
    return lines


# Sentence-tier FORM display labels.
_FORM_LABELS = {
    "original": "Original",
    "standard": "Standard",
    "alternate": "Alternate",
}


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
        # Skip a FORM line when its text duplicates an earlier kind we've
        # already printed (e.g. standard==original is common when a corpus
        # only really has one orthography).
        printed_forms: list[str] = []
        for kind in FORM_KINDS:
            txt = r["forms"].get(kind, "")
            if not txt or txt in printed_forms:
                continue
            lines.append(f"- **{_FORM_LABELS[kind]}:** {txt}")
            printed_forms.append(txt)
        for kind, txt in r["phons"]:
            label = f"PHON ({kind})" if kind else "PHON"
            lines.append(f"- **{label}:** {txt}")
        for lang, txt in sorted(r["translations"].items()):
            lines.append(f"- **TRANSL ({lang}):** {txt}")
        if r["audio_files"]:
            lines.append(f"- **Audio:** {', '.join(r['audio_files'])}")
        if r["words"]:
            lines.append(f"- **Words ({len(r['words'])}):**")
            for w in r["words"]:
                lines.extend(_format_word_lines(w))
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

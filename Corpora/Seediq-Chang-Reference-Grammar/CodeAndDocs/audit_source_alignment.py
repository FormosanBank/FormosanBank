#!/usr/bin/env python3
"""Audit the complete reviewed inventory and generated canonical XML."""

from __future__ import annotations

import csv
import hashlib
import re
import json
import subprocess
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "CodeAndDocs" / "source_inventory.tsv"
ACCEPTED = ROOT / "CodeAndDocs" / "extracted_examples.tsv"
REJECTED = ROOT / "CodeAndDocs" / "rejected_candidates.tsv"
DEDUPLICATED = ROOT / "CodeAndDocs" / "deduplicated_variants.tsv"
XML_PATH = ROOT / "XML" / "Seediq" / "chang-2000-seediq-reference-grammar.xml"
CHAPTER5 = ROOT / "CodeAndDocs" / "chapter5_inventory.tsv"
XML_LONG = ROOT / "XML" / "Seediq" / "chang-2000-seediq-long-texts.xml"
REPORT = ROOT / "CodeAndDocs" / "source_alignment_audit.md"

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
PRIMARY_HASH = "81b2a4a109c2151b6bc9f8dc09f882a4e4f2996ef05bf5b9692df15f933f355e"
SECONDARY_HASH = "e20e0ea80929b0b2b591f2ddec41fc4ce6a4b9076fde3d467f97de1bedc27836"
COINDEX_MARK = "\u1d62"  # the source's coindexation subscript; FORM/@notes only

# Declared shape of the published corpus. 366 variants expand from the 273
# included records; 15 of those are exact duplicates of an earlier variant and
# are merged by build_xml.deduplicate (POL-022), leaving 351 published.
# (Was 369/354 until 2026-10-15: da/di in R181-R185 became one S each with a
# ver="alt" FORM, -5; R275's optional (um) became separate S blocks, +2.)
EXPECTED_VARIANTS = 366
EXPECTED_MERGED = 15
EXPECTED_SENTENCES = 351
# The fixed numbers guard the transcription itself: words in the included
# inventory rows, which review corrections and processing never edit. The XML's
# own W/M totals legitimately move when review lands or POL-060 joins two words
# under one gloss, so they are reported, not pinned (ruled 2026-10-14).
EXPECTED_SOURCE_WORDS = 1195

# Chapter 5, the narrative. 40 transcribed blocks; the story title carries a
# gloss but no free translation and is excluded, as chapters 3-4 exclude such
# blocks, and two pairs of blocks share one gloss bracket and are merged into one
# example each (transcribe_chapter5.bracketed_examples, ruled 2026-10-14/15).
# No expansion and no dedup: the narrative has no alternations.
EXPECTED_CH5_BLOCKS = 40
EXPECTED_CH5_SENTENCES = 37
EXPECTED_CH5_SOURCE_WORDS = 281
PRIVATE_SOURCES = {
    ROOT / "Private/source/basecamp/Chang_2000_Seediq_RG.original.pdf": (
        PRIMARY_HASH,
        208,
    ),
    ROOT / "Private/source/basecamp/6.original.pdf": (SECONDARY_HASH, 105),
}
OLIVER_FORMS = {
    "R001": "holi s-usa-un-mu klaali",
    "R002": "mupu-puhulis-nami",
    "R004": "k-um-ubunux heya",
    "R006": "mugu-huling pawan kusun",
    "R008": "mun-teru-ku m-eyah hini",
    "R010": "pukubunux-ku di",
    "R011": "peekan ido laqi ka bubu",
    "R012": "mu-puhuling pawan kusun",
    "R014": "gaga sudara riyung pawan",
    "R016": "egu tulaqi-un na awe",
}


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pdf_pages(path: Path) -> int | None:
    """Page count of a PDF, or None when no counter is available.

    `pdfinfo` (poppler-utils) is not part of the documented environment -- the
    build only promises a FormosanBank checkout and its Python -- so it is tried
    first but never required. `pypdf` from that venv is the fallback. Returning
    None means "not verified here", which the caller records as a warning; it
    must not abort an otherwise clean audit, and it must not be mistaken for a
    page-count mismatch.
    """
    try:
        result = subprocess.run(
            ["pdfinfo", str(path)], check=True, capture_output=True, text=True
        )
        for line in result.stdout.splitlines():
            if line.startswith("Pages:"):
                return int(line.split(":", 1)[1])
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass
    try:
        # pdfplumber is pinned in FormosanBank's requirements.txt, so it is
        # guaranteed by the documented interpreter; pypdf only arrives as its
        # transitive dependency, so it is the second choice, not the first.
        import pdfplumber

        with pdfplumber.open(str(path)) as document:
            return len(document.pages)
    except Exception:
        pass
    try:
        import pypdf

        return len(pypdf.PdfReader(str(path)).pages)
    except Exception:
        return None


def as_printed(word_form: str) -> str:
    """A W FORM read back the way the source prints it. Under POL-060 one W may
    hold two words (ani naq), and a pronoun printed inside such a pair is written
    as an infix (ani<ku>naq for the printed ani-ku naq), so the W tier spells the
    sentence's words in order, but not one W per word."""
    # POL-014 at the word tier (ruled 2026-10-15, Q1a): a verbal infix after the
    # root's first letter, b<n>eebu / s<um><un>ebuc, prints as b-n-eebu /
    # s-um-un-ebuc.
    if re.match(r"^[^<]<", word_form):
        return re.sub(r"<([^>]+)>", r"-\1-", word_form).replace("--", "-")
    infix = re.fullmatch(r"([^<]+)<([^>]+)>(.+)", word_form)
    return f"{infix[1]}-{infix[2]} {infix[3]}" if infix else word_form


def check(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def audit() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    for path in (INVENTORY, ACCEPTED, REJECTED, DEDUPLICATED, XML_PATH,
                 CHAPTER5, XML_LONG):
        check(
            path.exists(),
            f"Missing required artifact: {path.relative_to(ROOT)}",
            errors,
        )
    if errors:
        return [
            "# Source Alignment Audit",
            "",
            *[f"- ERROR: {e}" for e in errors],
            "",
        ], errors

    inventory = read_tsv(INVENTORY)
    accepted = read_tsv(ACCEPTED)
    rejected = read_tsv(REJECTED)
    deduplicated = read_tsv(DEDUPLICATED)
    included = [row for row in inventory if row["decision"] == "include"]
    excluded = [row for row in inventory if row["decision"] == "exclude"]
    by_id = {row["record_id"]: row for row in inventory}

    check(len(inventory) == 353, "Expected 353 reviewed source blocks", errors)
    check(len(by_id) == 353, "Source record ids are not unique", errors)
    check(
        [row["record_id"] for row in inventory]
        == [f"R{number:03d}" for number in range(1, 354)],
        "Source record ids/order changed",
        errors,
    )
    check(
        len(included) == 273 and len(excluded) == 80,
        "Inventory decision counts changed",
        errors,
    )
    check(
        all(not row["exclusion_reason"] for row in included)
        and all(row["exclusion_reason"] for row in excluded),
        "Inventory decisions and exclusion reasons disagree",
        errors,
    )
    check(
        Counter(row["exclusion_reason"] for row in excluded)
        == {
            "ungrammatical_source": 47,
            "not_interlinear_example": 27,
            "marginal_source": 5,
            "missing_source_translation": 1,
        },
        "Exclusion reason counts changed",
        errors,
    )
    check(
        len(rejected) == len(excluded)
        and [row["source_id"] for row in rejected]
        == [row["record_id"] for row in excluded],
        "Rejected table does not cover every excluded inventory row",
        errors,
    )
    for row in included:
        pairs = json.loads(row["word_gloss_json"])
        check(
            bool(row["form"] and row["gloss"] and row["translation"]),
            f"Incomplete included row {row['record_id']}",
            errors,
        )
        check(
            len(pairs) == len(row["form"].split()),
            f"Word/gloss alignment drift at {row['record_id']}",
            errors,
        )
        check(
            all(len(pair) == 2 and pair[1] for pair in pairs),
            f"Empty aligned gloss at {row['record_id']}",
            errors,
        )

    for source_id, form in OLIVER_FORMS.items():
        check(
            by_id[source_id]["form"] == form,
            f"Oliver hand form drift at {source_id}",
            errors,
        )
    check(
        by_id["R012"]["translation"] == "pawan 明天要（用狗）打獵",
        "R012 parenthetical source translation changed",
        errors,
    )

    root = ET.parse(XML_PATH).getroot()
    sentences = root.findall("S")
    words = root.findall(".//W")
    morphs = root.findall(".//M")
    check(
        root.get("id") == "chang-2000-seediq-reference-grammar",
        "TEXT id changed",
        errors,
    )
    check(
        root.get(XML_LANG) == "trv" and root.get("dialect") == "Tegudaya",
        "Language/dialect changed",
        errors,
    )
    check(
        PRIMARY_HASH in root.get("source", ""),
        "Primary scan hash missing from TEXT source",
        errors,
    )
    duplicate_forms = Counter(
        sentence.findtext("FORM[@kindOf='original']", "") for sentence in sentences
    )
    repeated = {form: count for form, count in duplicate_forms.items() if count > 1}
    check(
        len(sentences) == len(accepted) == EXPECTED_SENTENCES,
        f"Expected {EXPECTED_SENTENCES} published sentences",
        errors,
    )
    check(
        len(deduplicated) == EXPECTED_MERGED
        and len(accepted) + len(deduplicated) == EXPECTED_VARIANTS,
        f"Expected {EXPECTED_MERGED} merged duplicates out of "
        f"{EXPECTED_VARIANTS} expanded variants",
        errors,
    )
    source_words = sum(len(json.loads(row["word_gloss_json"]))
                       for row in inventory if row["decision"] == "include")
    check(source_words == EXPECTED_SOURCE_WORDS,
          f"Transcribed word inventory changed: {source_words}", errors)
    # POL-022: dedup is declared, so a duplicate left in the output is a defect.
    check(
        not repeated,
        f"Duplicate published FORMs survived dedup: {sorted(repeated)[:3]}",
        errors,
    )
    check(
        all(word.findall("M") for word in words),
        "A W element lacks an M analysis",
        errors,
    )

    ids = [element.get("id", "") for element in [*sentences, *words, *morphs]]
    check(
        all(ids) and len(ids) == len(set(ids)),
        "S/W/M ids are missing or duplicated",
        errors,
    )
    check(
        all(set(sentence.attrib) <= {"id", "source"} for sentence in sentences)
        and all(set(element.attrib) == {"id"} for element in [*words, *morphs]),
        "S/W/M elements contain non-spec attributes",
        errors,
    )
    check(
        all(sentence.get("source") for sentence in sentences),
        "A published sentence has no S/@source locator",
        errors,
    )
    # POL-028: one base id per source record; extra readings take -opt, then
    # -opt3, -opt4. There is no -opt2, and an -opt never outlives its base.
    sentence_ids = [sentence.get("id", "") for sentence in sentences]
    bases = {sid for sid in sentence_ids if "-opt" not in sid}
    check(
        all(re.fullmatch(r"R\d{3}(-opt[3-9]?\d*)?", sid) for sid in sentence_ids),
        "An S id does not match the shape RNNN[-opt[N]] (record id, POL-028/POL-037)",
        errors,
    )
    check(
        not any(sid.endswith("-opt2") for sid in sentence_ids),
        "POL-028 has no -opt2: the second block stays unnumbered",
        errors,
    )
    check(
        all(sid.split("-opt")[0] in bases for sid in sentence_ids if "-opt" in sid),
        "An -opt id has no base sentence",
        errors,
    )
    check(
        all(
            word.get("id", "").startswith(sentence.get("id", "") + "W")
            for sentence in sentences
            for word in sentence.findall("W")
        ),
        "A W id is not composed from its sentence id",
        errors,
    )
    # The coindex subscript is dropped at intake and recorded nowhere.
    check(
        not any(
            COINDEX_MARK in (form.text or "") for form in root.iter("FORM")
        ),
        "A coindexation subscript survived in FORM text",
        errors,
    )
    check(
        COINDEX_MARK not in XML_PATH.read_text(encoding="utf-8"),
        "A coindexation subscript survived somewhere in the published file",
        errors,
    )

    for sentence, row in zip(sentences, accepted, strict=True):
        form = sentence.findtext("FORM[@kindOf='original']", "")
        check(
            form == row["form"],
            f"XML/accepted FORM drift at {row['source_id']} variant {row['variant']}",
            errors,
        )
        check(
            " ".join(
                as_printed(word.findtext("FORM[@kindOf='original']", ""))
                for word in sentence.findall("W")
            )
            == form,
            f"Sentence/W alignment drift at {row['source_id']} variant {row['variant']}",
            errors,
        )
        check(
            not any(marker in form for marker in "*/()[]{}"),
            f"Unexpanded source notation in {row['source_id']} variant {row['variant']}",
            errors,
        )

    r012_rows = [
        (sentence, row)
        for sentence, row in zip(sentences, accepted, strict=True)
        if row["source_id"] == "R012"
    ]
    check(len(r012_rows) == 1, "R012 expanded unexpectedly", errors)
    if r012_rows:
        translations = [item.text or "" for item in r012_rows[0][0].findall("TRANSL")]
        check(
            # Published without spaces beside the Chinese (ruled 2026-10-15).
            translations == ["pawan明天要打獵", "pawan明天要用狗打獵"],
            "R012 alternate translation was not preserved correctly",
            errors,
        )

    tracked = set(
        subprocess.run(
            ["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True
        ).stdout.splitlines()
    )
    check(
        not any(str(path.relative_to(ROOT)) in tracked for path in PRIVATE_SOURCES),
        "Private source PDFs remain tracked by Git",
        errors,
    )
    check(
        not (ROOT / "Final_XML").exists(),
        "Legacy Final_XML directory still exists",
        errors,
    )

    # ---- chapter 5, the narrative -------------------------------------
    chapter5 = read_tsv(CHAPTER5)
    long_root = ET.parse(XML_LONG).getroot()
    long_sentences = long_root.findall("S")
    long_words = long_root.findall(".//W")
    long_morphs = long_root.findall(".//M")
    included5 = [row for row in chapter5 if row["decision"] == "include"]
    check(len(chapter5) == EXPECTED_CH5_BLOCKS,
          f"Expected {EXPECTED_CH5_BLOCKS} transcribed chapter 5 blocks", errors)
    check(len(long_sentences) == len(included5) == EXPECTED_CH5_SENTENCES,
          f"Expected {EXPECTED_CH5_SENTENCES} chapter 5 sentences", errors)
    ch5_words = sum(len(json.loads(row["word_gloss_json"])) for row in included5)
    check(ch5_words == EXPECTED_CH5_SOURCE_WORDS,
          f"Transcribed chapter 5 word inventory changed: {ch5_words}", errors)
    check(long_root.get("id") == "chang-2000-seediq-long-texts",
          "Chapter 5 TEXT id changed", errors)
    check(long_root.get(XML_LANG) == "trv"
          and long_root.get("dialect") == "Tegudaya",
          "Chapter 5 language or dialect changed", errors)
    check(long_root.get("copyright") == root.get("copyright")
          and long_root.get("citation") == root.get("citation"),
          "The two published files disagree about rights or citation", errors)
    check(all(int(row["printed_page"]) in range(151, 160) for row in chapter5),
          "A chapter 5 block is outside printed pp. 151-159", errors)
    # Every block's alignment is one gloss per whitespace word.
    for row in chapter5:
        pairs = json.loads(row["word_gloss_json"])
        check(len(pairs) == len(row["form"].split()),
              f"Chapter 5 word/gloss misalignment at {row['record_id']}", errors)
    # The footnote markers (15 on sa-an-daha, 16 on pizu) must not have leaked
    # into the text; no FORM in the narrative carries a digit at all.
    check(not any(re.search(r"[0-9]", form.text or "")
                  for form in long_root.iter("FORM")),
          "A digit appears in a chapter 5 FORM -- check for a footnote leak",
          errors)
    check(all(sentence.get("source") for sentence in long_sentences),
          "A chapter 5 sentence has no S/@source locator", errors)
    check([s.get("id") for s in long_sentences]
          == [row["record_id"] for row in included5],
          "Chapter 5 sentence ids are not the included block ids in narrative order", errors)

    source_rows: list[str] = []
    for path, (expected_hash, expected_pages) in PRIVATE_SOURCES.items():
        if path.exists():
            actual_hash = sha256(path)
            actual_pages = pdf_pages(path)
            check(
                actual_hash == expected_hash,
                f"Local source hash changed: {path.name}",
                errors,
            )
            check(
                actual_pages is not None,
                f"Could not count pages in {path.name}: no pdfinfo, pdfplumber "
                "or pypdf available. Run with the FormosanBank interpreter.",
                errors,
            )
            check(
                actual_pages is None or actual_pages == expected_pages,
                f"Local source page count changed: {path.name} "
                f"({actual_pages} vs {expected_pages})",
                errors,
            )
        source_rows.append(
            f"| `{path.relative_to(ROOT)}` | optional private evidence, verified when present | `{expected_hash}` | {expected_pages} |"
        )

    lines = [
        "# Source Alignment Audit",
        "",
        "Audit date: 2026-09-11",
        "",
        "Verdict: ready for QC" if not errors else "Verdict: needs remediation",
        "",
        "## Source evidence",
        "",
        "| File | Status | SHA-256 | Pages |",
        "|---|---|---|---:|",
        *source_rows,
        "",
        "The private scans are optional verification inputs. The reviewed `source_inventory.tsv` is the earliest redistributable authoritative layer for a clean clone.",
        "",
        "## Complete inventory",
        "",
        f"- Reviewed marked blocks: {len(inventory)}",
        f"- Included source records: {len(included)}",
        f"- Excluded source records: {len(excluded)}",
        f"- Expanded grammatical variants: {len(accepted)}",
        "- Every source block has an explicit decision. Every exclusion has a reason.",
        "- Leading `*`, `?`, and `??` examples are excluded. Internal grammatical alternatives and optional material are expanded.",
        "",
        "## XML shape",
        "",
        f"- chapters 3-4: {len(sentences)} S / {len(words)} W / {len(morphs)} M",
        f"- chapter 5 narrative: {len(long_sentences)} S / {len(long_words)} W "
        f"/ {len(long_morphs)} M, from {len(chapter5)} transcribed blocks",
        "- Every W has a source-aligned gloss and at least one M analysis.",
        "- Language `trv`; dialect `Tegudaya`; canonical output under "
        "`XML/Seediq/` (POL-059).",
        f"- Exact repeated FORM groups: {len(repeated)} (dedup is declared, so "
        "this must be zero). "
        f"{len(deduplicated)} duplicate variants were merged into an earlier "
        "sentence; every merged locator rides along in that sentence's "
        "`S/@source` and the merges are listed in `deduplicated_variants.tsv`.",
        "",
        "## Source-specific decisions",
        "",
        "- Oliver Sun's ten hand-transcribed forms are retained.",
        "- The R012 parenthetical `用狗` reading is an alternate translation, not a FORM expansion.",
        "- Cross-page examples and the three explicit shared/cross-reference translations carry review notes in the inventory.",
        "- A gloss printed under two words makes them one W (POL-060); a word the source leaves unglossed has the gloss `<UNCLEAR/>` (POL-061 `?`, published as `<UNCLEAR/>` per the 2026-10-17 ruling). No lexical gloss was invented.",
        "",
        "## Result",
        "",
        f"- Errors: {len(errors)}",
        "- Warnings: 0",
        "- Notices: 0",
        "",
    ]
    if errors:
        lines.extend(["### Errors", "", *[f"- {error}" for error in errors], ""])
    return lines, errors


def main() -> int:
    lines, errors = audit()
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT}")
    print(f"errors={len(errors)} warnings=0 notices=0")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Fail QC unless Wu findings match the reviewed source evidence."""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
XML_PATH = ROOT / "XML/Amis/pa-verbs.xml"


def rows(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def tsv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def require_empty(path: Path) -> None:
    findings = rows(path)
    if findings:
        counts = Counter((row["severity"], row["rule_id"]) for row in findings)
        raise ValueError(f"Unexpected findings in {path.name}: {dict(counts)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qc-dir", type=Path, required=True)
    args = parser.parse_args()
    qc_dir = args.qc_dir.resolve()

    required_exits = [
        row for row in rows(qc_dir / "exit_codes.csv") if row.get("gate") == "required"
    ]
    require(
        required_exits and all(row["exit_code"] == "0" for row in required_exits),
        "one or more required QC commands failed",
    )
    require(
        "errors=0 warnings=0 notices=0"
        in (qc_dir / "source_alignment.stdout.txt").read_text(encoding="utf-8"),
        "structured source-alignment audit did not pass",
    )
    require(
        "port-readiness: 0 HARD, 0 WARN"
        in (qc_dir / "port_readiness.stdout.txt").read_text(encoding="utf-8"),
        "port-readiness did not pass cleanly",
    )

    require_empty(qc_dir / "validate_xml.csv")
    require_empty(qc_dir / "duplicate_original.csv")
    require_empty(qc_dir / "duplicate_standard.csv")

    text_findings = rows(qc_dir / "validate_text.csv")
    text_counts = Counter((row["severity"], row["rule_id"]) for row in text_findings)
    require(
        text_counts == {("SOFT", "V116"): 14, ("SOFT", "V122"): 2},
        f"text finding set changed: {dict(text_counts)}",
    )
    require(
        all(
            row["character"] == "∅" for row in text_findings if row["rule_id"] == "V116"
        ),
        "V116 includes a character other than the canonical null",
    )
    paren_findings = Counter(
        (row["location"], row["character"])
        for row in text_findings
        if row["rule_id"] == "V122"
    )
    require(
        paren_findings == {("S=s30c", "("): 1, ("S=s30c", ")"): 1},
        f"V122 finding set changed: {dict(paren_findings)}",
    )

    gloss_findings = rows(qc_dir / "validate_glosses.csv")
    gloss_counts = Counter((row["severity"], row["rule_id"]) for row in gloss_findings)
    require(
        gloss_counts == {("SOFT", "V061"): 1},
        f"unexpected gloss findings: {dict(gloss_counts)}",
    )
    gloss_row = gloss_findings[0]
    require(
        re.search(r"W=s32aw0$", gloss_row["location"]) is not None,
        "V061 is not the source-underanalyzed Pa-fli word",
    )

    internal_findings = rows(qc_dir / "audit_gloss_internal.csv")
    internal_counts = Counter(
        (row["severity"], row["rule_id"]) for row in internal_findings
    )
    require(
        internal_counts
        == {
            ("HARD", "G001"): 3,
            ("SOFT", "G002"): 2,
            ("SOFT", "G003"): 1,
            ("WARN", "G010"): 1,
        },
        f"generic internal gloss-audit set changed: {dict(internal_counts)}",
    )
    expected_internal_locations = {
        "S=s32a W=s32aw0",
        "S=s33c W=s33cw1",
        "S=s33c W=s33cw3",
    }
    require(
        {row["location"] for row in internal_findings}
        == expected_internal_locations | {"W=s32aw0 M=s32aw0m0", ""},
        "generic gloss-audit locations changed",
    )
    mixed_marker = next(row for row in internal_findings if row["rule_id"] == "G010")
    require(
        mixed_marker["count"] == "7" and "∅-ci" in mixed_marker["message"],
        "G010 is not the reviewed S-original null propagation pattern",
    )

    root = ET.parse(XML_PATH).getroot()
    require(
        (len(root.findall("S")), len(root.findall(".//W")), len(root.findall(".//M")))
        == (29, 153, 263),
        "unexpected final S/W/M counts",
    )
    form_count = len(root.findall(".//FORM[@kindOf='original']"))
    require(form_count == 445, "unexpected original FORM count")
    require(
        len(root.findall(".//PHON[@kindOf='original']")) == form_count
        and len(root.findall(".//PHON[@kindOf='standard']")) == form_count,
        "original or standard PHON coverage is incomplete",
    )
    pa_fli = root.find("S[@id='s32a']/W[@id='s32aw0']")
    require(pa_fli is not None and len(pa_fli.findall("M")) == 1, "Pa-fli M changed")
    require(
        len(tsv_rows(ROOT / "CodeAndDocs/source_coverage.tsv")) == 13
        and len(tsv_rows(ROOT / "CodeAndDocs/direct_source_checks.tsv")) == 30
        and len(tsv_rows(ROOT / "CodeAndDocs/rejected_source_examples.tsv")) == 16,
        "source evidence inventory changed",
    )

    report = [
        "# QC finding adjudication",
        "",
        "- XML findings: 0",
        "- Validator HARD findings: 0",
        "- Duplicate findings: 0",
        "- Text findings: 14 SOFT V116 and 2 SOFT V122, reviewed",
        "- Gloss findings: 1 SOFT V061, reviewed",
        "- Generic internal gloss audit: 3 G001, 2 G002, 1 G003, and 1 G010 row, source-confirmed",
        "- Structured source inventory: 13 pages, 29 included variants, 16 exclusions, and 30 direct checks",
        "",
        "The V116 rows are the canonical analytic null `∅` propagated through "
        "S original and W/M under POL-012. The V122 pair is the source translation "
        "`(other people's)`, retained under POL-024. V061 and G001/G003 for "
        "`Pa-fli` reflect the paper's hyphenated word with only the whole-word "
        "gloss `give`; the single whole-word M preserves that analysis under "
        "POL-023 and POL-036. The remaining G001/G002 rows are "
        "source words `ni` and `ku` with unsplit forms but compound glosses "
        "`GEN-NCM` and `NOM-NCM`. Splitting them would invent source segmentation. "
        "G010 counts the seven S-original `∅-ci` forms whose bridging hyphen is "
        "required to keep the analytic null distinct under POL-012.",
        "",
        "The private development repository contains the source PDF and full "
        "PDF-mode heuristic audit. The public port retains only the reviewed, "
        "source-free ledgers needed to reproduce and check the published XML.",
        "",
    ]
    (qc_dir / "adjudication.md").write_text("\n".join(report), encoding="utf-8")
    print("All validator and gloss-audit findings match reviewed source evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Cross-file registry consistency checks (SOFT findings; POL-034).

The QC pipeline depends on agreement among loosely-coupled data files:
standards.csv, dialects.csv, orthography profiles, conversion-table
headers, and rules sidecars. The first validate_conversion_table run
found 5 tables that crash purely on dialect-name drift; this validator
surfaces that class *before* anything crashes on it.

All consistency findings are SOFT by maintainer ruling (2026-08-10):
registries may be legitimately out of sync mid-migration. Exit 1 only
when a registry file itself is missing or unparseable.

This is a repo-level validator (no corpus argument) — run it from CI or
before a release, not per corpus.
"""
import argparse
import csv
import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
sys.path.insert(0, str(_HERE.parents[2]))

from QC.validation._finding import (  # noqa: E402
    Finding, Severity, summarize, write_findings_csv,
)

TITLES = {
    "V150": "language_missing_from_standards",
    "V151": "standards_scheme_folder_missing",
    "V152": "conversion_table_dialect_unknown",
    "V153": "rules_sidecar_dialect_unknown",
    "V154": "legacy_variant_notation_in_profile",
    "V155": "languages_registry_inconsistent",
}
_NON_DIALECT_COLUMNS = {"original", "standard"}

# Legacy phonemic-variant notation: a whole cell of two-plus alternatives
# joined by bare tildes ('b~v'). POL-013 (2026-08-10): canonical is
# '[b|v]'. The exclusion of parens/brackets/pipes keeps this away from
# rules-sidecar regex cells like 'ʦ~ʨ(?=i)' — those migrate by hand.
import re as _re  # noqa: E402

_LEGACY_VARIANT_RE = _re.compile(r"^[^\s~()|\[\]]+(~[^\s~()|\[\]]+)+$")


def _read_two_column_csv(path: Path) -> list:
    """(col0, col1) pairs from a comma CSV, header skipped."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            raise ValueError(f"{path}: empty registry")
        return [
            (row[0].strip(), row[1].strip() if len(row) > 1 else "")
            for row in reader
            if row and row[0].strip()
        ]


def check(repo_root: Path) -> list:
    findings: list[Finding] = []
    standards_path = repo_root / "standards.csv"
    dialects_path = repo_root / "dialects.csv"
    standards = dict(_read_two_column_csv(standards_path))
    dialects = {d for _, d in _read_two_column_csv(dialects_path) if d}

    # V150: every known language has a standards.csv row. Uses the live
    # ISO map so adding a language to the code forces a registry entry.
    from QC.validation._dialect_inventory import ISO_TO_LANGUAGE  # noqa: E402
    for language in sorted(set(ISO_TO_LANGUAGE.values())):
        if language not in standards:
            findings.append(Finding(
                rule_id="V150", severity=Severity.SOFT,
                message=(f"V150 SOFT: {language} is in ISO_TO_LANGUAGE but "
                         f"has no standards.csv row (a blank scheme means "
                         f"'no standard yet'; a missing row is drift)"),
                path=standards_path, language=language))

    # V155: languages.csv <-> dialects.csv consistency (POL-040). The two
    # registries must name languages identically, and ISO codes must be
    # unique lowercase — languages.csv is the single ISO->language source
    # every consumer loads (POL-039).
    languages_path = repo_root / "languages.csv"
    lang_rows = _read_two_column_csv(languages_path)
    lang_names = {name for _, name in lang_rows if name}
    seen_codes: set[str] = set()
    for code, name in lang_rows:
        if code != code.lower():
            findings.append(Finding(
                rule_id="V155", severity=Severity.SOFT,
                message=(f"V155 SOFT: languages.csv ISO code {code!r} is "
                         f"not lowercase"),
                path=languages_path, language=name))
        if code.lower() in seen_codes:
            findings.append(Finding(
                rule_id="V155", severity=Severity.SOFT,
                message=(f"V155 SOFT: languages.csv ISO code {code!r} "
                         f"appears more than once"),
                path=languages_path, language=name))
        seen_codes.add(code.lower())
    dialect_langs = {lang for lang, _ in _read_two_column_csv(dialects_path)}
    # dialects.csv names Seediq's sibling Truku only implicitly (trv);
    # "Truku" as a Language row is fine because resolve_language emits it.
    known_names = lang_names | {"Truku"}
    for lang in sorted(dialect_langs - known_names):
        findings.append(Finding(
            rule_id="V155", severity=Severity.SOFT,
            message=(f"V155 SOFT: dialects.csv names language {lang!r} "
                     f"which has no languages.csv row — the registries "
                     f"must name languages identically (POL-040)"),
            path=dialects_path, language=lang))

    # V151: non-blank scheme folders exist.
    for language, scheme in sorted(standards.items()):
        if scheme and not (repo_root / "Orthographies" / scheme).is_dir():
            findings.append(Finding(
                rule_id="V151", severity=Severity.SOFT,
                message=(f"V151 SOFT: standards.csv maps {language} -> "
                         f"{scheme} but Orthographies/{scheme}/ does not "
                         f"exist"),
                path=standards_path, language=language))

    # V152: conversion-table value columns name a canonical variety.
    #
    # A variety label is either an Official dialect in dialects.csv or a
    # *language* name: single-dialect languages write the language name
    # itself in @dialect (dialect="Tsou"), and so do languages that share
    # an ISO code with another — "Truku" under trv is Seediq's sibling,
    # named in languages.csv (via trv) and carrying its own dialects.csv
    # Language row. Those columns resolve fine at run time
    # (validate_conversion_table --dialect Truku passes), so flagging them
    # was a defect in the rule, not registry drift. Language names not in
    # languages.csv are V155's business, not V152's; a genuine typo
    # ('Nanwan') is in neither set and still fires.
    accepted_columns = dialects | lang_names | dialect_langs
    tables_dir = repo_root / "Orthographies" / "ConversionTables"
    for table in sorted(tables_dir.glob("*.tsv")) if tables_dir.is_dir() else []:
        with open(table, newline="", encoding="utf-8") as f:
            header = f.readline().rstrip("\n").split("\t")
        for column in header[1:]:
            column = column.strip()
            if column and column not in _NON_DIALECT_COLUMNS \
                    and column not in accepted_columns:
                findings.append(Finding(
                    rule_id="V152", severity=Severity.SOFT,
                    message=(f"V152 SOFT: {table.name} value column "
                             f"{column!r} names neither a canonical dialect "
                             f"in dialects.csv nor a language in "
                             f"languages.csv (the class that crashes "
                             f"validate_conversion_table)"),
                    path=table, character=column))

    # V154: profile cells still using legacy x~y variant notation.
    orthographies_dir = repo_root / "Orthographies"
    if orthographies_dir.is_dir():
        for profile in sorted(orthographies_dir.rglob("*.tsv")):
            if profile.parent.name == "ConversionTables" \
                    or profile.name.endswith(".rules.tsv"):
                continue
            with open(profile, newline="", encoding="utf-8") as f:
                for row in csv.reader(f, delimiter="\t"):
                    for cell in row:
                        cell = cell.strip()
                        if _LEGACY_VARIANT_RE.match(cell):
                            findings.append(Finding(
                                rule_id="V154", severity=Severity.SOFT,
                                message=(f"V154 SOFT: {profile.name} uses "
                                         f"legacy variant notation {cell!r}; "
                                         f"POL-013 canonical is "
                                         f"'[{cell.replace(chr(126), '|')}]'"),
                                path=profile, character=cell))

    # V153: rules-sidecar dialect values are canonical.
    # Use the same accepted variety labels as V152. A rules sidecar may scope
    # a rule to a language-valued dialect such as Truku, which is represented
    # by a Language row in dialects.csv because it shares ISO trv with Seediq.
    accepted_rule_dialects = dialects | lang_names | dialect_langs
    orthographies = repo_root / "Orthographies"
    sidecars = sorted(orthographies.rglob("*.rules.tsv")) \
        if orthographies.is_dir() else []
    for sidecar in sidecars:
        with open(sidecar, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            if reader.fieldnames is None or "dialect" not in reader.fieldnames:
                continue
            seen: set = set()
            for row in reader:
                # The rules engine splits this cell on commas
                # ("Zhuoqun,Kaqun" scopes to two dialects) — check each
                # name, not the whole cell (2026-08-10 baseline false
                # positive).
                for value in (row.get("dialect") or "").split(","):
                    value = value.strip()
                    if value and value != "default" \
                            and value not in accepted_rule_dialects \
                            and value not in seen:
                        seen.add(value)
                        findings.append(Finding(
                            rule_id="V153", severity=Severity.SOFT,
                            message=(f"V153 SOFT: {sidecar.name} scopes "
                                     f"rules to dialect {value!r}, not "
                                     f"canonical per dialects.csv"),
                            path=sidecar, character=value))
    return findings


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Cross-file registry consistency (SOFT; POL-034)")
    parser.add_argument("--repo-root", type=Path, default=_HERE.parents[2],
                        help="repository root (default: this checkout)")
    parser.add_argument("--csv", type=Path, default=None,
                        help="findings CSV path (default: "
                             "<repo-root>/logs/registry_findings.csv)")
    args = parser.parse_args(argv)

    try:
        findings = check(args.repo_root)
    except (OSError, ValueError) as error:
        print(f"HARD: unreadable registry: {error}", file=sys.stderr)
        return 1

    csv_path = args.csv or (args.repo_root / "logs" / "registry_findings.csv")
    for severity, by_rule in summarize(findings).items():
        for rule_id, count in sorted(by_rule.items()):
            print(f"{rule_id} {TITLES.get(rule_id, '')}: {count}")
    if findings:
        write_findings_csv(csv_path, findings, TITLES)
        print(f"Details: {csv_path}")
    else:
        print("Registries consistent: no findings.")
    return 0  # SOFT findings never fail the run (POL-034)


if __name__ == "__main__":
    raise SystemExit(main())

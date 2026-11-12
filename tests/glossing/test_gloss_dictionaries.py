"""Every gloss code a conversion table maps TO must be defined in the
per-language gloss dictionaries (Glossing/GlossDictionaries/<Language>.tsv).

A code absent from a language's dictionary is, by definition, an
unconverted source code whose meaning is still TBD — so a table that
produces a code the dictionary does not define is an error.
"""

import csv
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TABLES = ROOT / "Glossing" / "ConversionTables"
DICTS = ROOT / "Glossing" / "GlossDictionaries"

# Atoms inside a composite standard (OV.PFV, PV/LV, PST/PFV) are looked
# up individually; the X/Y and category-dot notations themselves are
# defined in Glossing/README.md.
ATOM_SPLIT = re.compile(r"[./／]")
OVERRIDE = re.compile(r"(\w+)→([#A-Za-z0-9./]+)")


def conversion_tables():
    return sorted(p for p in TABLES.glob("*.tsv") if not p.name.endswith(".rules.tsv"))


def load_corpus_languages():
    path = DICTS / "corpus_languages.tsv"
    assert path.exists(), f"missing {path}"
    pairs = {}
    with path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            pairs.setdefault(row["corpus"], set()).add(row["language"])
    return pairs


def load_dictionary(language):
    path = DICTS / f"{language}.tsv"
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    return {row["gloss"]: row["definition"] for row in rows}


def mapped_atoms(table_path):
    """Yield (language_or_None, atom): None means every language of the corpus."""
    with table_path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            status = (row.get("status") or "").strip()
            standard = (row.get("standard") or "").strip()
            if status in ("CONVERT", "KEEP") and standard:
                for atom in ATOM_SPLIT.split(standard):
                    if atom:
                        yield None, atom
            for lang, target in OVERRIDE.findall(row.get("language_overrides") or ""):
                for atom in ATOM_SPLIT.split(target):
                    if atom:
                        yield lang, atom


def test_every_corpus_has_language_rows():
    pairs = load_corpus_languages()
    missing = [t.stem for t in conversion_tables() if t.stem not in pairs]
    assert not missing, f"corpora missing from corpus_languages.tsv: {missing}"


def test_dictionaries_have_definitions():
    tsvs = sorted(DICTS.glob("*.tsv"))
    assert tsvs, f"no dictionaries in {DICTS}"
    for path in tsvs:
        if path.name == "corpus_languages.tsv":
            continue
        with path.open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        assert rows, f"{path.name} is empty"
        undefined = [r["gloss"] for r in rows if not (r.get("definition") or "").strip()]
        assert not undefined, f"{path.name}: glosses without definitions: {undefined}"


@pytest.mark.parametrize("table", conversion_tables(), ids=lambda p: p.stem)
def test_mapped_codes_are_in_language_dictionaries(table):
    pairs = load_corpus_languages()
    languages = pairs[table.stem]
    problems = []
    for lang, atom in mapped_atoms(table):
        targets = [lang] if lang else sorted(languages)
        for language in targets:
            dictionary = load_dictionary(language)
            if dictionary is None:
                problems.append(f"no dictionary for language {language!r}")
            elif atom not in dictionary:
                problems.append(f"{language}: mapped-to code {atom!r} not in {language}.tsv")
    assert not problems, f"{table.stem}: " + "; ".join(sorted(set(problems)))

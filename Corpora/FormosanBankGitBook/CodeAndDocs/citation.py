"""The corpus citation: every contributor, alphabetically, and a version.

Maintainer, 2026-10-18: "it should list all contributors in alphabetical order.
Title is just 'Translations of the FormosanBank documentation vX' going forward.
For now, Xuan Ruan is the only author and it is v1. BibTex will need to be
updated as well. This does mean the citation changes over time, but that's OK."

Contributors are the people in contributors.tsv whose work is in the corpus:
Xuan Ruan's 2025 translation, plus every translator with an approved
translation in docs/translations/ (pwn, ami, bnn for Formosan text; zho, whose
approved Mandarin is attached to those sentences). A translator who is not in
contributors.tsv stops the build: how a person is cited is recorded, not
guessed. The version is 1 plus the number of distinct dates on which approved
translations were added, so it is reproducible from the store; the year is the
year of the latest such date (2025 for v1).
"""

from __future__ import annotations

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
TITLE = "Translations of the FormosanBank documentation v{version}"
BIBTEX_KEY = "formosanbank_doc_translations"
BASE_YEAR = 2025
BASE_CONTRIBUTORS = ("Xuan Ruan",)
CITED_STORES = ("pwn", "ami", "bnn", "zho")


def read_contributors(path: Path = HERE / "contributors.tsv") -> dict[str, dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as handle:
        return {row["name"]: row for row in csv.DictReader(handle, delimiter="\t")}


def approved_rows(store_dir: Path) -> list[dict[str, str]]:
    rows = []
    for code in CITED_STORES:
        path = store_dir / f"{code}.tsv"
        if path.is_file():
            with open(path, newline="", encoding="utf-8") as handle:
                rows += [
                    {**row, "code": code}
                    for row in csv.DictReader(handle, delimiter="\t")
                    if row["approved"] == "yes" and row["translation"].strip() and row["translator"].strip()
                ]
    return rows


def citation(store_dir: Path, contributors: dict[str, dict[str, str]] | None = None) -> tuple[str, str]:
    """(APA citation, BibTeX) for the current state of the translation store."""
    contributors = contributors if contributors is not None else read_contributors()
    rows = approved_rows(store_dir)
    names = set(BASE_CONTRIBUTORS) | {row["translator"] for row in rows}
    missing = sorted(n for n in names if n not in contributors)
    if missing:
        raise KeyError(
            f"add these translators to {HERE / 'contributors.tsv'} (how they are cited): {missing}"
        )
    people = sorted((contributors[n] for n in names), key=lambda p: (p["surname"].casefold(), p["given"].casefold()))
    dates = sorted({row["date"] for row in rows})
    version = 1 + len(dates)
    year = int(dates[-1][:4]) if dates else BASE_YEAR
    title = TITLE.format(version=version)
    apa_names = [f"{p['surname']}, {p['initials']}" for p in people]
    authors = apa_names[0] if len(apa_names) == 1 else ", ".join(apa_names[:-1]) + ", & " + apa_names[-1]
    apa = f"{authors} ({year}). {title}."
    bib_names = " and ".join(f"{p['surname']}, {p['given']}" for p in people)
    bibtex = f"@misc{{{BIBTEX_KEY}, author={{{bib_names}}}, title={{{title}}}, year={{{year}}}}}"
    return apa, bibtex

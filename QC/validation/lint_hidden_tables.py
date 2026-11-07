#!/usr/bin/env python3
"""lint_hidden_tables.py — language data hiding in build code (POL-039), advisory.

POL-039: data that critical steps depend on lives in prominent, human-readable
registries, never hard-coded in Python. It keeps reappearing anyway: Seediq-
Chang's build_xml.py carried a 36-row translation table, 115 overrides, 27
exclusions and 12 OCR fixes as literals until 2026-10-15, and silently
ignored a student's fix to one of them; NTU's apply_manual_corrections.py is
575 lines of tables; ILRDF's xmlify.py keys a dict on sentence text.

The signal is not clean — Song's override dicts are deliberate, keyed by S id,
page-cited and documented — so this is a lint that warns and never fails
(maintainer, 2026-10-17: "Advisory lint (warn, never fail)"). For every
Python file under a corpus's CodeAndDocs/ it counts the tokens inside string
literals (docstrings excluded) that look like language data: tokens with CJK
characters, or words attested in the reference vocabulary of a language the
corpus publishes. Files over the threshold are listed with sample tokens.

    python QC/validation/lint_hidden_tables.py --corpus Corpora/<Name> [--threshold 30]
"""
from __future__ import annotations

import argparse
import ast
import pickle
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from QC.corpus_counts import load_language_codes, resolve_language  # noqa: E402

REFERENCE = REPO_ROOT / "QC" / "validation" / "reference"
_CJK = re.compile(r"[㐀-䶿一-鿿豈-﫿]")
_XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
DEFAULT_THRESHOLD = 30
# Everyday English that also sits in some reference vocabularies (loans,
# language names, scrape leftovers); counting it would make every log message
# look like a table.
_ENGLISH_NOISE = frozenset(
    "the a an and or of to in on at for with from by is are was were be been this that these those it "
    "its he she they them his her their we you our your not no yes as if then than but so because when "
    "while where who which what how there here have has had do does did can could will would should may "
    "might must also very into out up down over under about after before name same gone none file files "
    "path line lines text word words source target output input data table tables xml json csv tsv".split())


def reference_vocabulary(language: str) -> frozenset[str]:
    words: set[str] = set()
    for info in (REFERENCE / language).glob("**/orthographic_info"):
        try:
            with info.open("rb") as fp:
                words.update(w for w in pickle.load(fp).get("word_frequency", {}) if len(w) >= 4)
        except Exception:
            continue
    return frozenset(words)


def corpus_languages(corpus: Path) -> set[str]:
    """Language names the corpus publishes, from its XML roots (trv resolved by dialect)."""
    from lxml import etree
    names: set[str] = set()
    for path in (corpus / "XML").rglob("*.xml"):
        if "CodeAndDocs" in path.parts:
            continue
        try:
            for _event, root in etree.iterparse(str(path), events=("start",)):
                name = resolve_language(root.get(_XML_LANG), root.get("dialect"))
                if name:
                    names.add(name)
                break
        except etree.XMLSyntaxError:
            continue
    return names


def _string_literals(source: str) -> list[str]:
    """String constants in the file, docstrings left out."""
    tree = ast.parse(source)
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                docstrings.add(id(body[0].value))
    return [node.value for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings]


def data_tokens(source: str, vocab: frozenset[str]) -> Counter:
    """Tokens inside the file's string literals that read as language data."""
    found: Counter = Counter()
    for literal in _string_literals(source):
        for token in literal.split():
            word = token.strip("“”\"'.,;:!?()[]{}<>=/\\").lower()
            if not word:
                continue
            if word in _ENGLISH_NOISE:
                continue
            if _CJK.search(word) or word in vocab:
                found[word] += 1
    return found


def lint_corpus(corpus: Path, threshold: int = DEFAULT_THRESHOLD, vocab: frozenset[str] | None = None) -> list[tuple[Path, int, list[str]]]:
    """(file, data-token count, sample tokens) for files over the threshold."""
    if vocab is None:
        vocab = frozenset().union(*(reference_vocabulary(l) for l in corpus_languages(corpus))) if (corpus / "XML").is_dir() else frozenset()
    hits = []
    for path in sorted((corpus / "CodeAndDocs").rglob("*.py")):
        if "tests" in path.parts:
            continue
        try:
            found = data_tokens(path.read_text(encoding="utf-8", errors="replace"), vocab)
        except SyntaxError:
            continue
        total = sum(found.values())
        if total >= threshold:
            hits.append((path, total, [w for w, _n in found.most_common(8)]))
    return hits


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", required=True, type=Path, help="Corpora/<Name>")
    ap.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD)
    a = ap.parse_args(argv)
    hits = lint_corpus(a.corpus, a.threshold)
    if not hits:
        print(f"{a.corpus.name}: no build file holds {a.threshold}+ language-data tokens in string literals")
        return 0
    print(f"{a.corpus.name}: build files holding language data as Python literals (POL-039, advisory):")
    for path, total, sample in hits:
        print(f"  {total:5d}  {path.relative_to(a.corpus)}   e.g. {', '.join(sample)}")
    print("Deliberate, documented override tables are fine; a table nobody can review or edit without reading code is not.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

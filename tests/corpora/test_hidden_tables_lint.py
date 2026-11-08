"""POL-039 advisory: build files holding language data as Python literals (warns, never fails).

Maintainer, 2026-10-17: "Advisory lint (warn, never fail)". Song's override
dicts are deliberate and page-cited; Seediq-Chang's were not; the lint cannot
tell them apart, so a human reads the warning.
"""
import importlib.util
import warnings

import pytest

from tests._helpers import REPO_ROOT

_spec = importlib.util.spec_from_file_location("lint", REPO_ROOT / "QC" / "validation" / "lint_hidden_tables.py")
lint = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lint)

CORPORA = sorted(d.name for d in (REPO_ROOT / "Corpora").iterdir()
                 if (d / "XML").is_dir() and (d / "CodeAndDocs").is_dir())


@pytest.mark.parametrize("corpus", CORPORA)
def test_build_code_holds_no_hidden_language_tables(corpus):
    hits = lint.lint_corpus(REPO_ROOT / "Corpora" / corpus)
    if hits:
        listed = "; ".join(f"{p.relative_to(REPO_ROOT / 'Corpora' / corpus)} ({n} tokens, e.g. {', '.join(s[:4])})"
                           for p, n, s in hits)
        warnings.warn(
            f"POL-039: {corpus} keeps language data in build code: {listed}. If deliberate "
            "(documented, keyed by id, page-cited), ignore; otherwise move it to a reviewable table.",
            stacklevel=1,
        )

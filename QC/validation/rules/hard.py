"""HARD-severity rules: violations cause the validator to exit nonzero.

Each rule is a function with signature:
    rule(tree: etree._ElementTree, path: Path, index: CorpusIndex | None) -> list[Finding]

Rules that do NOT consult `index` go in RULES; the runner calls them
in pass 1. Rules that DO consult `index` go in CROSS_FILE_RULES; the
runner calls them in pass 2 after the index is built.
"""
from QC.validation._finding import Finding

RULES: list = []
CROSS_FILE_RULES: list = []

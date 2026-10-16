"""A row whose continuation lines land at the top of the next page keeps them.

`_row_starts` only ever recognises a row start from a column-1 line. When an
entry's column-1 cell ends on one page and its other cells run on to the next,
those lines start no row: they sit above the next page's first detected start
and, before this fix, belonged to no band and were discarded in silence.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import extract_source as es

BANDS = {1: 75.0, 2: 145.0, 3: 220.0, 4: 285.0, 5: 365.0}
HEADER = (
    "level\tpage_num\tpar_num\tblock_num\tline_num\tword_num"
    "\tleft\ttop\twidth\theight\tconf\ttext"
)


def _tsv(cells):
    """cells: (page, top, column, text) -> a pdftotext -tsv document."""
    out = [HEADER]
    for block, (page, top, column, text) in enumerate(cells, start=1):
        out.append(
            f"5\t{page}\t1\t{block}\t0\t1"
            f"\t{BANDS[column]}\t{top}\t40\t10\t96\t{text}"
        )
    return "\n".join(out) + "\n"


CELLS = [
    # page 1, a normal entry
    (1, 153.28, 1, "alpha"), (1, 153.28, 2, "een"),
    (1, 153.28, 3, "een"), (1, 153.28, 5, "one"),
    # page 1, the last entry. Only its two Siraya cells fit on the page --
    # exactly the shape of row 822 kmoulaling, which has column 1 and column 4
    # and neither gloss. (A start is recognised only when a column 2-5 word sits
    # beside the column-1 one, so column 4 is what makes this a row at all.)
    (1, 521.80, 1, "beta"), (1, 521.80, 4, "beta"),
    # page 2, that entry's remaining cells -- no column-1 word, so no row start
    (2, 153.28, 2, "twee"), (2, 153.28, 3, "twee"), (2, 153.28, 5, "two"),
    # page 2, the first entry that does start a row
    (2, 175.60, 1, "gamma"), (2, 175.60, 2, "drie"),
    (2, 175.60, 3, "drie"), (2, 175.60, 5, "three"),
]


def _rows(monkeypatch=None):
    es.EXPECTED_PAGES, es.EXPECTED_ROWS = 2, 3
    return es.extract_rows(_tsv(CELLS))


def test_the_orphaned_lines_are_not_dropped():
    rows = _rows()
    beta = next(r for r in rows if r["um_formosana"] == "beta")
    assert beta["vdv_siraya"] == "beta"
    assert beta["um_belgica"] == "twee"
    assert beta["vdv_dutch"] == "twee"
    assert beta["english"] == "two"


def test_row_detection_is_unchanged():
    rows = _rows()
    assert [r["um_formosana"] for r in rows] == ["alpha", "beta", "gamma"]
    assert [r["pdf_page"] for r in rows] == [1, 1, 2]


def test_the_next_page_keeps_its_own_first_row():
    rows = _rows()
    gamma = next(r for r in rows if r["um_formosana"] == "gamma")
    assert gamma["english"] == "three"
    assert gamma["vdv_dutch"] == "drie"

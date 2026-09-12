"""How a conversion table's rules are applied to a standard FORM.

Rules are staged through placeholders, longest source first, so that no rule
can rewrite another rule's output. Before that, a table written in the ordinary
digraph-first idiom misconverted silently: `ll -> ll` guarding `l -> lr` still
produced `lrlr`, because sequential replacement re-scanned the output.

The same change retires the escape-and-restore idiom, which existed only
because ordering was the only tool available: a table that wanted `g -> ng`
without `ng -> nng` had to hop through a spare symbol. `Amis_Church_113` did
exactly that and now says `ng -> ng` instead.

The bank-wide sweep at the bottom is the regression guard: every rule in every
committed conversion table must produce exactly its own replacement.
"""
import csv
import glob
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from QC.utilities.standardize import apply_standard

REPO_ROOT = Path(__file__).resolve().parents[2]


def convert(table, text, keep=frozenset()):
    s = ET.fromstring('<S id="t"><FORM kindOf="standard">%s</FORM></S>' % text)
    apply_standard(s, table, keep=keep)
    return s.find("FORM").text


# --- the idiom that used to fail -------------------------------------------

def test_digraph_rule_is_not_rewritten_by_a_later_single_letter_rule():
    """Puyuma MinEd: `ll -> ll` exists to guard `ll` from `l -> lr`."""
    assert convert([("ll", "ll"), ("l", "lr")], "ll") == "ll"
    assert convert([("ll", "ll"), ("l", "lr")], "lal") == "lralr"


def test_digraph_rule_wins_even_when_listed_after_the_short_rule():
    """Longest-first, so the table author need not order by hand."""
    assert convert([("l", "lr"), ("ll", "ll")], "ll") == "ll"


def test_a_rules_output_is_never_matched_by_another_rule():
    """Rukai Church: `lh -> l` must not then be caught by `l -> lr`."""
    assert convert([("lh", "l"), ("l", "lr")], "lh") == "l"


def test_length_rule_output_is_not_recoloured():
    """Rukai Li: `ə: -> ee` must not then be caught by `e -> é`."""
    table = [("e:", "éé"), ("ə:", "ee"), ("e", "é"), ("ə", "e")]
    assert convert(table, "kə:") == "kee"
    assert convert(table, "ke:") == "kéé"
    assert convert(table, "kə") == "ke"
    assert convert(table, "ke") == "ké"


def test_shield_idiom_replaces_escape_and_restore():
    """Amis Church wants `g -> ng` without turning `ng` into `nng`.

    Under sequential replacement the only way to express that was to escape:
    `ng -> ɟ`, then `g -> ng`, then `ɟ -> ng` to restore. Longest-first
    shielding says it directly — `ng -> ng` guards the digraph — and the
    escape hop is no longer needed or available, because a rule's output is
    never revisited.
    """
    table = [("ng", "ng"), ("g", "ng")]
    assert convert(table, "ng") == "ng"
    assert convert(table, "g") == "ng"
    assert convert(table, "gami") == "ngami"
    assert convert(table, "migagai") == "mingangai"
    assert convert(table, "gngg") == "ngngng"


# --- NA is not a rule; empty is --------------------------------------------

def test_empty_replacement_still_deletes():
    """Bunun `w`, Sakizaya `x` and Wakelin `?` rely on this."""
    assert convert([("w", "")], "awa") == "aa"


def test_na_cell_is_not_a_rule(tmp_path):
    """End to end, because the reading lives in the loader.

    'NA' means the letter does not occur in this dialect. Read as a rule it
    splices the letters N and A into the text — and it only ever stayed
    harmless because the NA'd letter genuinely does not occur. Here it does.
    """
    xml = tmp_path / "XML" / "Test"
    xml.mkdir(parents=True)
    (xml / "t.xml").write_text(
        '<?xml version="1.0" ?>\n'
        '<TEXT id="t" citation="c" BibTeX_citation="b" copyright="public domain"'
        ' dialect="Dona" xml:lang="dru">'
        '<S id="S_1"><FORM kindOf="original">kakə</FORM></S></TEXT>',
        encoding="utf-8",
    )
    table = tmp_path / "conv.tsv"
    table.write_text("original\tMaolin\tDona\ne\té\tNA\nə\te\te\n", encoding="utf-8")

    subprocess.run(
        [sys.executable, str(REPO_ROOT / "QC" / "utilities" / "standardize.py"),
         "--corpora_path", str(tmp_path / "XML"), "--tsv_path", str(table)],
        check=True, capture_output=True, cwd=REPO_ROOT,
    )
    standard = ET.parse(xml / "t.xml").getroot().findtext("S/FORM[@kindOf='standard']")
    assert standard == "kake", standard
    assert "NA" not in standard


# --- placeholders do not leak ----------------------------------------------

def test_private_use_input_is_rejected_rather_than_silently_corrupted():
    with pytest.raises(ValueError, match="Private Use Area"):
        convert([("a", "b")], "ab")


def test_diacritic_sources_survive_accent_stripping():
    """The original reason placeholders exist: a table may map a real letter
    such as ä while unlisted stress marks are still stripped."""
    assert convert([("ä", "ae")], "bäd á") == "baed a"


# --- bank-wide regression ---------------------------------------------------

def _committed_rules():
    root = os.path.join(os.path.dirname(__file__), "..", "..")
    for path in sorted(glob.glob(os.path.join(root, "Orthographies", "ConversionTables", "*.tsv"))):
        with open(path, newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            columns = [c for c in (reader.fieldnames or []) if c != "original"]
            rows = list(reader)
        for column in columns:
            table = [
                (r["original"].strip(), (r.get(column) or "").strip())
                for r in rows
                if r.get("original", "").strip()
                and (r.get(column) or "").strip() != "NA"
            ]
            for source, replacement in table:
                yield os.path.basename(path), column, table, source, replacement


@pytest.mark.parametrize(
    "name,column,table,source,replacement",
    list(_committed_rules()),
    ids=lambda v: v if isinstance(v, str) else "",
)
def test_every_committed_rule_produces_its_own_replacement(
    name, column, table, source, replacement
):
    """No rule in any committed table may be altered by another rule.

    This caught 17 real misconversions across five tables when the placeholder
    was generalized: Amis_Church `ng`, Puyuma_Cauquelin `L`/`ɭ`,
    Puyuma_MinEd `ll`, Rukai_Church `lh`, and Rukai_Li `ə:`.
    """
    assert convert(table, source) == replacement, (
        f"{name} [{column}]: {source!r} should convert to {replacement!r}"
    )

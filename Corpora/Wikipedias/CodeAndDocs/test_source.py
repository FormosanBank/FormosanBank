"""August 11–12 Wikipedia rulings, checked against preserved source records."""

import csv
import hashlib
import subprocess
import sys
from collections import Counter
from pathlib import Path

from lxml import etree
import pytest

from QC.validation.rules.text import (
    v129_asterisk_in_standard_FORM,
    v146_phon_variant_group_malformed,
)
from normalize_seediq_quotes import normalize_text
from drop_redirect_copies import remove_redirect_copies

HERE = Path(__file__).resolve().parent
XML = HERE.parent / "XML"
SNAPSHOT = HERE / "pre_correction_snapshot"


@pytest.fixture(scope="module")
def articles():
    return {str(p.relative_to(XML)): etree.parse(str(p))
            for p in sorted(XML.rglob("*.xml"))}


def test_complete_reviewed_article_inventory(articles):
    with (HERE / "source_exclusions.csv").open() as stream:
        exclusions = list(csv.DictReader(stream))
    source = {str(p.relative_to(SNAPSHOT)) for p in SNAPSHOT.rglob("*.xml")}
    with (HERE / "source_redirects.csv").open() as stream:
        redirects = list(csv.DictReader(stream))
    final_counterparts = {row["file"]: row["retained"] for row in redirects}
    assert len(source) == 13278
    assert len(exclusions) == 40
    assert len(redirects) == 490
    assert set(articles) == source - {row["file"] for row in exclusions + redirects}
    assert Counter(p.split("/")[0] for p in articles) == {
        "Amis": 1892, "Atayal": 2935, "Paiwan": 455,
        "Sakizaya": 5498, "Seediq": 1968,
    }
    for row in exclusions:
        if row["retained"]:
            assert (SNAPSHOT / row["file"]).read_bytes() == (SNAPSHOT / row["retained"]).read_bytes()
            assert final_counterparts.get(row["retained"], row["retained"]) in articles
    for row in redirects:
        assert row["file"] not in articles
        survivor = articles[row["retained"]].getroot()
        assert survivor.get("id") == row["retained_id"]
        form = survivor.find('S/FORM[@kindOf="original"]').text
        assert hashlib.sha256(form.encode()).hexdigest() == row["original_sha256"]


def test_source_metadata_and_tier_coverage(articles):
    languages = {"Amis": "ami", "Atayal": "tay", "Paiwan": "pwn",
                 "Sakizaya": "szy", "Seediq": "trv"}
    ids = []
    for name, tree in articles.items():
        root = tree.getroot()
        source = etree.parse(str(SNAPSHOT / name)).getroot()
        assert root.get("id") == source.get("id")
        assert root.get("source") == source.get("source")
        assert root.get("citation") == source.get("citation")
        assert root.get("copyright") == "CC BY-SA 4.0"
        assert root.get("{http://www.w3.org/XML/1998/namespace}lang") == languages[name.split("/")[0]]
        assert root.get("dialect") == "unknown"
        assert [s.get("id") for s in root.iter("S")] == ["0"]
        assert not root.xpath(".//W | .//M | .//TRANSL | .//AUDIO")
        assert Counter(f.get("kindOf") for f in root.iter("FORM")) == {"original": 1, "standard": 1}
        assert Counter(f.get("kindOf") for f in root.iter("PHON")) == {"original": 1, "standard": 1}
        ids.append(root.get("id"))
    assert len(set(ids)) == 12748


def test_exact_source_residue_exceptions(articles):
    with (HERE / "source_exceptions.csv").open() as stream:
        records = list(csv.DictReader(stream))
    assert Counter(r["rule"] for r in records) == {"V129": 34, "V146": 35}
    with (HERE / "source_redirects.csv").open() as stream:
        redirects = {row["file"]: row["retained"] for row in csv.DictReader(stream)}
    expected = Counter()
    for row in records:
        filename = redirects.get(row["file"], row["file"])
        tree = articles[filename]
        if row["file"] not in redirects:
            assert tree.getroot().get("id") == row["text_id"]
        form = tree.find(f'S[@id="{row["s_id"]}"]/FORM[@kindOf="original"]')
        assert hashlib.sha256(form.text.encode()).hexdigest() == row["original_sha256"]
        assert form.text.count(row["marker"]) == int(row["count"])
        expected[row["rule"], filename, f'S={row["s_id"]}'] = 2
    actual = Counter()
    for name, tree in articles.items():
        for check in (v129_asterisk_in_standard_FORM, v146_phon_variant_group_malformed):
            for finding in check(tree, XML / name, None):
                actual[finding.rule_id, name, finding.location] += 1
    assert actual == expected


def test_recorded_question_mark_correction(articles):
    name = "Sakizaya/miladlad_tu_udip.xml"
    assert etree.parse(str(SNAPSHOT / name)).find('S/FORM[@kindOf="original"]').text.startswith("? ")
    assert articles[name].find('S/FORM[@kindOf="original"]').text.startswith("makatukuh i lalud,")
    assert (HERE / "manual_edits.xml").is_file()


@pytest.mark.parametrize(("source", "expected"), [
    ("''patas''", '"patas"'),
    ("'patas'", '"patas"'),
    ("b'anux hla'alua mu'izzaddin", "b'anux hla'alua mu'izzaddin"),
    ("cinkhulan sa knita' sa brbiru'.", "cinkhulan sa knita' sa brbiru'."),
])
def test_reviewed_seediq_quote_boundaries(source, expected):
    assert normalize_text(source) == expected


@pytest.mark.parametrize("differing", [False, True])
def test_duplicate_downloads_require_identical_content(tmp_path, differing):
    # An earlier exact-copy group must survive if a later group differs.
    for name, identifier, form in [
        ("Haba.xml", "a", "haba"), ("Haba (1).xml", "a", "haba"),
        ("msin (1).xml", "z", "msin"),
        ("msin (2).xml", "z", "changed" if differing else "msin"),
    ]:
        (tmp_path / name).write_text(
            f'<TEXT id="{identifier}"><S id="0"><FORM kindOf="original">{form}</FORM></S></TEXT>'
        )
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    result = subprocess.run([sys.executable, str(HERE / "delete_duplicate_articles.py"),
                             "--corpora_path", str(tmp_path)], capture_output=True, text=True)
    if differing:
        assert result.returncode != 0
        assert "CONTENT DIFFERS" in result.stderr
        assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before
    else:
        assert result.returncode == 0, result.stderr
        assert {p.name for p in tmp_path.iterdir()} == {"Haba.xml", "msin (1).xml"}


def test_redirect_source_changes_stop_all_removals(tmp_path):
    text = "article text"
    rows = []
    for n in range(2):
        source, target = f"alias{n}.xml", f"article{n}.xml"
        for name, value in ((source, text), (target, text if n == 0 else "different")):
            (tmp_path / name).write_text(
                f'<TEXT id="{name}"><S id="0"><FORM kindOf="original">{value}</FORM></S></TEXT>'
            )
        rows.append(dict(file=source, text_id=source, retained=target, retained_id=target,
                         original_sha256=hashlib.sha256(text.encode()).hexdigest()))
    manifest = tmp_path / "redirects.csv"
    with manifest.open("w") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    before = {p.name: p.read_bytes() for p in tmp_path.glob("*.xml")}
    with pytest.raises(ValueError, match="Changed redirect content"):
        remove_redirect_copies(tmp_path, manifest)
    assert {p.name: p.read_bytes() for p in tmp_path.glob("*.xml")} == before

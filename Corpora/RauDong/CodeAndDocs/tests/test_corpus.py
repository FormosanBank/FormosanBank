from __future__ import annotations

import sys
from pathlib import Path

from lxml import etree


REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from QC.utilities.add_phonology import load_profile, phonologize  # noqa: E402


CORPUS_ROOT = Path(__file__).resolve().parents[2]
XML_ROOT = CORPUS_ROOT / "XML"


def _form_text(element: etree._Element) -> str:
    return "".join(element.itertext())


def test_inventory_is_the_twenty_2006_texts() -> None:
    paths = sorted(XML_ROOT.glob("Yami/*.xml"))
    assert len(paths) == 20

    counts = {"S": 0, "W": 0, "M": 0}
    for path in paths:
        root = etree.parse(str(path)).getroot()
        assert root.get("{http://www.w3.org/XML/1998/namespace}lang") == "tao"
        assert root.get("dialect") == "Yami"
        assert "2006" in root.get("citation", "")
        assert "2018" not in root.get("citation", "")
        for tag in counts:
            counts[tag] += sum(1 for _ in root.iter(tag))

    assert counts == {"S": 794, "W": 13295, "M": 16731}


def test_phonology_matches_reviewed_profiles() -> None:
    original = load_profile("Ortho94", "Yami", "Yami")
    standard = load_profile("Ortho113", "Yami", "Yami")
    assert original is not None
    assert standard is not None

    for path in sorted(XML_ROOT.glob("Yami/*.xml")):
        root = etree.parse(str(path)).getroot()
        for parent in root.iter():
            if parent.tag not in {"S", "W", "M"}:
                continue
            for kind, profile in (("original", original), ("standard", standard)):
                form = parent.find(f'FORM[@kindOf="{kind}"]')
                phon = parent.find(f'PHON[@kindOf="{kind}"]')
                assert form is not None
                assert phon is not None
                expected = phonologize(_form_text(form), profile)
                assert phon.text == expected, (
                    f"{path.name}: {parent.tag} {parent.get('id')} {kind}"
                )
                assert "~" not in phon.text

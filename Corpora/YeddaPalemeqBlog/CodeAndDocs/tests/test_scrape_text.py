"""The scraper must keep the spaces the blog shows around italic words.

The fixtures under ``fixtures/blog_posts/`` are the ``post-body`` divs of three
real posts, copied unchanged from the HTML that ``scrape/download_html.py``
saved on 2026-11-25. The expected glosses below were typed by hand from the
text a reader sees on the blog (runs of whitespace shown as one space, ends
trimmed); they do not come from the scraper.

Before this fix the scraper read each list item with
``get_text(strip=True)``, which trims every text fragment and joins the
fragments with nothing between them, so ``the root is <i>nasi </i>'breath'``
became ``the root isnasi'breath'``. The frozen snapshot carries that output.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures/blog_posts"
sys.path.insert(0, str(ROOT / "scrape"))

import analyze_blog_structure as scraper  # noqa: E402

BLOG = "https://yeddapalemeq.blogspot.com"


def blocks_for(slug: str, month: str) -> list[dict]:
    soup = BeautifulSoup((FIXTURES / f"{slug}.html").read_text(encoding="utf-8"), "html.parser")
    return scraper.find_example_blocks(soup, f"{BLOG}/{month}/{slug}.html")


class GlossWhitespaceTests(unittest.TestCase):
    def test_italic_affixes_and_roots_post_471(self) -> None:
        # <i>ka- </i>'inchoative'; <i>mi</i>- ...; the root is <i>nasi </i>'breath'
        blocks = blocks_for("paiwan-every-day-471-nasi-minasinasi", "2021/06")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(
            blocks[0]["glosses"],
            [
                "nu: if",
                "ini'(a)-anga: no longer, not anymore",
                "ka-mi-nasi-nasi: is breathing, AV. ka- 'inchoative'; mi- 'anget marker'; "
                "the root is nasi 'breath' in RED",
                "a: subject case marker",
                "caucau: people, human",
                "a: LIG",
                "qemuzimuzip: animal",
                "tja-san-na-ma-cai-(y)anga: we consider dead. tja- 'our'; san- 'construct'; "
                "na- 'PRF'; ma- 'to be in the condition of'; the root is cai 'death'; -anga 'COS'.",
            ],
        )

    def test_nbsp_and_italic_links_post_451(self) -> None:
        # trailing &nbsp; inside the item; italic <a> links mid-sentence
        blocks = blocks_for("paiwan-every-day-451-kuda-namakuda", "2021/06")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(
            blocks[0]["glosses"],
            [
                "na-ma-kuda: what happend with or what's wrong with AV. na- 'PRF'; "
                "ma- 'in the condition of'; the root is kuda 'rule, work, what'.",
                "a: subject case marker",
                "su: your, 2nd person singular GEN",
                "liqu: neck. I was looking for throat, it is tjigeraw or driaqulan in southern "
                "Paiwan. But in norther Paiwan, liqu is used to also mean throat.",
            ],
        )

    def test_space_inside_empty_italic_post_525(self) -> None:
        # <i>a</i>:<i> </i>subject ...; the root is <i>caljedj </i>'sting ...'
        blocks = blocks_for("paiwan-every-day-525-angac-pangac", "2021/08")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(
            blocks[0]["glosses"],
            [
                "saqetju: hurt",
                "a: subject case marker",
                "caljedj-en: be stung, UV. The root is caljedj 'sting, the sting of a bee'.",
                "na: of, GEN",
                "pangac: bee, wasp. There are several Paiwan words for different kinds of bees. "
                "More interestingly, the same word may mean different things depending on when "
                "and where the word was collected from.",
                "pangac: bee/wasp (generic) in Ferrell, hornet (in genus Vespa) in ILRDF Online "
                "Paiwan Dictionary.",
                "tjidriyulj: hornet (in genus Vespa) in klokah Paiwan Glossary",
                "lucluc: wasp",
                "tjainan: honeybee in klokah Paiwan Glossary and ILRDF Online Paiwan Dictionary "
                "pualju a tjainan.",
                "karuvenan: Scollid wasp in klokah Paiwan Glossary",
            ],
        )


class VisibleTextHelperTests(unittest.TestCase):
    def text(self, fragment: str) -> str:
        return scraper.visible_text(BeautifulSoup(fragment, "html.parser"))

    def test_keeps_spaces_at_tag_boundaries(self) -> None:
        self.assertEqual(
            self.text("<li>the root is <i>kan </i>'eat'.</li>"), "the root is kan 'eat'."
        )

    def test_adds_no_space_where_the_blog_has_none(self) -> None:
        # get_text(" ", strip=True) would give "ki-vava : to drink"
        self.assertEqual(self.text("<li><i>ki-vava</i>: to drink</li>"), "ki-vava: to drink")
        self.assertEqual(self.text("<li><i>mi</i>- 'marker'</li>"), "mi- 'marker'")

    def test_nbsp_and_whitespace_runs(self) -> None:
        self.assertEqual(self.text("<li> a  b\n\tc </li>"), "a b c")

    def test_line_break_reads_as_a_space(self) -> None:
        # No <br> occurs inside a gloss list item in the posts checked so far;
        # a browser shows one as a line break, which must not glue two words.
        self.assertEqual(self.text("<li>one<br/>two</li>"), "one two")


if __name__ == "__main__":
    unittest.main()

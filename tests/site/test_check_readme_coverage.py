"""check_readme_coverage: nothing the old README or GitBook page said may be lost."""

import check_readme_coverage as cov

OLD_README = """# Corpus

The source is a 1902 grammar. It has 40 pages.

* Item one is kept.
* Item two is dropped.

```bash
./CodeAndDocs/generate_xml.sh
```
"""

OLD_PAGE = """# Corpus

<!-- CORPUS STATS START -->
| Word count | 5 |
<!-- CORPUS STATS END -->

## **Access Details**

* The repo containing this corpus in FormosanBank as well as the code can be found [here](https://x).

In accordance with our [Terms of Use](../../t.md), cite FormosanBank.

A plain-language summary only the page had.
"""

NEW = """# Corpus

## Source

The source is a **1902 grammar**; it has 40 pages. A plain-language summary only the page had.

- Item one is kept.

## Reproduction and processing

    ./CodeAndDocs/generate_xml.sh
"""


def test_moved_and_repunctuated_sentences_are_covered():
    flagged, _ = cov.uncovered([OLD_README, OLD_PAGE], NEW)
    assert "The source is a 1902 grammar." not in flagged
    assert "A plain-language summary only the page had." not in flagged
    assert "./CodeAndDocs/generate_xml.sh" not in flagged


def test_dropped_sentence_is_flagged():
    flagged, _ = cov.uncovered([OLD_README, OLD_PAGE], NEW)
    assert flagged == ["Item two is dropped."]


def test_stats_block_access_details_and_terms_boilerplate_skipped():
    flagged, skipped = cov.uncovered([OLD_PAGE], NEW)
    assert flagged == []
    assert any("repo containing this corpus" in s for s in skipped)
    assert any("Terms of Use" in s for s in skipped)
    assert not any("Word count" in s for s in skipped + flagged)

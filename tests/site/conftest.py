import textwrap
from pathlib import Path

import pytest


SUMMARY_TEMPLATE = """\
# Table of contents

* [Welcome](README.md)

## The Bank Architecture

* [Corpora](the-bank-architecture/corpora/README.md)
  * [ePark](the-bank-architecture/corpora/epark.md)
  * [Wikipedias](the-bank-architecture/corpora/wikipedias.md)
* [Developers](the-bank-architecture/developers/README.md)
  * [Folder structure](the-bank-architecture/developers/folder-structure.md)
"""

CORPORA_README_TEMPLATE = """\
---
icon: subtitles
---

# Corpora

Below is a list of the current corpora:

* [ePark](epark.md) (text, audio, English, Mandarin)
* [Wikipedias](wikipedias.md) (text)

***

<!-- CORPUS STATS START -->
### Corpus Statistics
<!-- CORPUS STATS END -->

### Coming Soon

* Some Future Corpus (Amis)
"""

UPDATE_STATS_TEMPLATE = '''\
"""Fake update_corpus_stats.py for tests."""

CSV_TO_MD = {
    'ePark_corpora_stats.csv':      'epark.md',
    'Wikipedias_corpora_stats.csv': 'wikipedias.md',
}


def main():
    pass
'''


@pytest.fixture
def gitbook(tmp_path):
    """Build a miniature GitBook repo + sibling FormosanBank/Corpora.

    Returns an object with .root (gitbook), .corpora (FB Corpora dir),
    and helpers to read SUMMARY/update_corpus_stats back.
    """
    root = tmp_path / "FormosanBankGitbook"
    corpora_pages = root / "en-us" / "the-bank-architecture" / "corpora"
    corpora_pages.mkdir(parents=True)

    # Two existing, fully-wired corpora: ePark, Wikipedias
    (corpora_pages / "epark.md").write_text("# ePark\n\nText.\n", encoding="utf-8")
    (corpora_pages / "wikipedias.md").write_text("# Wikipedias\n\nText.\n", encoding="utf-8")
    (corpora_pages / "README.md").write_text(CORPORA_README_TEMPLATE, encoding="utf-8")
    (root / "en-us" / "SUMMARY.md").write_text(SUMMARY_TEMPLATE, encoding="utf-8")
    (root / "update_corpus_stats.py").write_text(UPDATE_STATS_TEMPLATE, encoding="utf-8")

    # parallel translation trees (pwn missing wikipedias -> translation lag)
    pwn = root / "pwn" / "the-bank-architecture" / "corpora"
    pwn.mkdir(parents=True)
    (pwn / "epark.md").write_text("# ePark\n", encoding="utf-8")
    zh = root / "zh-TW" / "the-bank-architecture" / "corpora"
    zh.mkdir(parents=True)
    (zh / "epark.md").write_text("# ePark\n", encoding="utf-8")

    # fake FormosanBank Corpora with ePark + Wikipedias shipped
    corpora = tmp_path / "FormosanBank" / "Corpora"
    for name in ("ePark", "Wikipedias"):
        (corpora / name / "XML").mkdir(parents=True)

    # per-corpus stats CSVs live in the canonical FormosanBank/statistics
    fb_statistics = tmp_path / "FormosanBank" / "statistics"
    fb_statistics.mkdir(parents=True)
    for name in ("ePark", "Wikipedias"):
        (fb_statistics / f"{name}_corpora_stats.csv").write_text("x\n", encoding="utf-8")

    class GB:
        pass

    gb = GB()
    gb.root = root
    gb.corpora = corpora
    gb.fb_statistics = fb_statistics
    gb.summary = root / "en-us" / "SUMMARY.md"
    gb.stats_script = root / "update_corpus_stats.py"
    gb.pages = corpora_pages
    gb.corpora_readme = corpora_pages / "README.md"
    gb.template = Path(__file__).parent / "fixtures" / "corpus_page.template.md"
    return gb

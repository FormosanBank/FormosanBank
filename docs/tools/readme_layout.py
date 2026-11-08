"""The corpus README layout (POL-044, POL-052 and POL-055 as amended 2026-10-18).

Each corpus README is the single copy of that corpus's documentation; the
documentation site renders it as the corpus page. Shared by the corpus tests
(tests/corpora/test_readme_sections.py) and the corpus-page lint
(docs/tools/manage_corpus_pages.py), so the rule exists once.
"""

import re

REQUIRED_HEADINGS = (
    "## Languages and dialects",
    "## Source",
    "## Statistics",
    "## How to cite",
    "## License",
    "## Notes and caveats",
    "## Reproduction and processing",
    "### How to reproduce",
    "### What each step does",
)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$", re.M)
LICENSE_LINE_RE = re.compile(r"^\*\*License:\*\*\s*(.+?)\s*$", re.M)
SOURCE_LINE_RE = re.compile(r"^\*\*Rights source:\*\*\s*\S", re.M)
FENCE_RE = re.compile(r"(?ms)^(`{3,}|~{3,}).*?^\1\s*$")


def _headings(readme: str) -> list[str]:
    """Level-1 to level-3 headings outside code blocks, normalised to '## Text'."""
    text = FENCE_RE.sub("", readme)
    return [
        f"{hashes} {title.strip('* ')}"
        for hashes, title in HEADING_RE.findall(text)
        if len(hashes) <= 3
    ]


def _section(readme: str, heading: str) -> str:
    """Text under ``heading`` up to the next heading of the same or higher level."""
    level = heading.split(" ", 1)[0]
    pattern = re.compile(rf"(?m)^{re.escape(heading)}\s*$")
    match = pattern.search(FENCE_RE.sub("", readme))
    if not match:
        return ""
    text = FENCE_RE.sub("", readme)
    following = re.compile(rf"(?m)^#{{1,{len(level)}}}\s").search(text, match.end())
    return text[match.end(): following.start() if following else len(text)]


def structure_problems(readme: str) -> list[str]:
    """What is wrong with the heading structure, as a list (empty = fine)."""
    headings = _headings(readme)
    problems = []
    if not headings or not headings[0].startswith("# "):
        problems.append("does not open with a '# <Corpus name>' title")
    found = [h for h in headings if h in REQUIRED_HEADINGS]
    for heading in REQUIRED_HEADINGS:
        count = found.count(heading)
        if count != 1:
            problems.append(f"'{heading}' appears {count} times (needs exactly 1)")
    if not problems and found != list(REQUIRED_HEADINGS):
        problems.append(f"headings out of order: {found}")
    if "## Notes and caveats" in found and not _section(readme, "## Notes and caveats").strip():
        problems.append("'## Notes and caveats' is empty (write 'None known.')")
    return problems


def rights_problems(readme: str, copyrights: set[str]) -> list[str]:
    """POL-044: what is wrong with the licence lines, as a list (empty = fine)."""
    section = _section(readme, "## License")
    problems = []
    if not section:
        return ["no '## License' section"]
    match = LICENSE_LINE_RE.search(section)
    if not match:
        problems.append("no '**License:** <value>' line under '## License'")
    elif copyrights != {match.group(1)}:
        problems.append(
            f"License line says {match.group(1)!r} but the XML @copyright is "
            f"{sorted(copyrights)}"
        )
    if not SOURCE_LINE_RE.search(section):
        problems.append("no '**Rights source:** <grantor>, <date>; evidence: ...' line under '## License'")
    return problems



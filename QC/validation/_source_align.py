"""Two-way alignment between scraped XML and the source document.

Backs the Group C rules of `audit_gloss_scrape.py`:

- G020 HARD: an XML sentence with no plausible source match (mangled/fabricated).
- G021 HARD: a source example with no XML match (silently dropped).
- G022 SOFT: character-fidelity loss on a matched pair.
- G013 SOFT: source shows several translations, XML kept one.
- G023 WARN: extraction self-report.

G023 is a precondition, not a footnote. Interlinear PDFs shred badly under
text extraction — columns interleave, ligatures drop — and when they do,
G021's "dropped example" bucket is an artifact of the extractor rather than a
finding about the corpus. The caller is expected to surface the G023 numbers
before quoting any coverage claim.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

from QC.validation._finding import Finding, Severity

# Default fuzzy-match acceptance, on a 0-100 scale.
DEFAULT_THRESHOLD = 82
# Skeletons shorter than this are too short to match reliably; a 4-letter
# sentence fuzzy-matches half the document.
MIN_SKELETON = 10

# Characters whose loss between source and XML is worth reporting: every
# non-ASCII character (orthographic diacritics, ʉ, ṟ, curly apostrophes) plus
# the ASCII characters that carry phonemic weight in Formosan orthographies.
_ASCII_OF_INTEREST = set("^_:'*")

# An interlinear example is conventionally introduced by a bracketed number.
_EXAMPLE_LABEL = re.compile(r"^\s*\(?(\d{1,3})([a-z])?\)")
# Free translations are conventionally single-quoted.
_QUOTED = re.compile(r"['‘’“”\"]([^'‘’“”\"]{4,})['‘’“”\"]")


# ---------------------------------------------------------------------------
# Source extraction
# ---------------------------------------------------------------------------

def extract_lines(source: Path) -> tuple[list[str], str]:
    """Return (lines, extractor_name) for a .txt or .pdf source.

    Raises RuntimeError with an actionable message when a PDF is given but
    pdfplumber is unavailable, rather than silently degrading to an empty
    source — an empty source would make every sentence look unmatched.
    """
    suffix = source.suffix.lower()
    if suffix == ".pdf":
        try:
            import pdfplumber
        except ImportError as exc:  # pragma: no cover - environment-dependent
            raise RuntimeError(
                f"Reading {source} requires pdfplumber (pip install pdfplumber)"
            ) from exc
        lines: list[str] = []
        with pdfplumber.open(str(source)) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                lines.extend(text.splitlines())
        return lines, "pdfplumber"
    return source.read_text(encoding="utf-8", errors="replace").splitlines(), "plaintext"


def skeleton(text: str | None) -> str:
    """Letters and digits only, casefolded, whitespace collapsed.

    Alignment must survive the notation differences between a source gloss
    line ('mi-lingatu ø-ci aki') and its XML sentence ('milingatu ci aki'),
    so every marker, space and punctuation mark is discarded before matching.
    """
    if not text:
        return ""
    kept = [
        ch.casefold()
        for ch in unicodedata.normalize("NFC", text)
        if ch.isalnum()
    ]
    return "".join(kept)


@dataclass
class SourceCandidate:
    """A source line, or a window of adjacent lines, matchable against an S."""
    start: int
    end: int
    text: str
    skel: str = field(default="", repr=False)

    def __post_init__(self) -> None:
        if not self.skel:
            self.skel = skeleton(self.text)


@dataclass
class ExampleRegion:
    """A numbered interlinear example, e.g. '(3) ...'."""
    label: str
    start: int
    end: int
    lines: list[str]
    matched: bool = False

    @property
    def text(self) -> str:
        return " ".join(self.lines)

    @property
    def translations(self) -> list[str]:
        return [m.group(1).strip() for line in self.lines for m in _QUOTED.finditer(line)]


def build_candidates(lines: list[str], window: int = 2) -> list[SourceCandidate]:
    """Single lines plus adjacent-line windows.

    Windows exist because interlinear examples wrap: a sentence occupying two
    physical lines matches neither line on its own.
    """
    candidates: list[SourceCandidate] = []
    non_empty = [(i, ln) for i, ln in enumerate(lines) if ln.strip()]
    for i, ln in non_empty:
        candidates.append(SourceCandidate(i, i, ln))
    for span in range(2, window + 1):
        for pos in range(len(non_empty) - span + 1):
            chunk = non_empty[pos:pos + span]
            candidates.append(SourceCandidate(
                chunk[0][0], chunk[-1][0], " ".join(c[1] for c in chunk),
            ))
    return [c for c in candidates if len(c.skel) >= MIN_SKELETON]


def find_example_regions(lines: list[str]) -> list[ExampleRegion]:
    """Split the source into numbered example regions.

    A region runs from one '(N)' label to the next. Regions are the unit of
    coverage for G021: a source example is 'present in the XML' when at least
    one XML sentence matched somewhere inside it.
    """
    starts: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        match = _EXAMPLE_LABEL.match(line)
        if match:
            starts.append((i, match.group(0).strip()))
    regions: list[ExampleRegion] = []
    for pos, (idx, label) in enumerate(starts):
        end = starts[pos + 1][0] - 1 if pos + 1 < len(starts) else len(lines) - 1
        regions.append(ExampleRegion(
            label=label, start=idx, end=end,
            lines=[ln for ln in lines[idx:end + 1] if ln.strip()],
        ))
    return regions


# ---------------------------------------------------------------------------
# Alignment
# ---------------------------------------------------------------------------

@dataclass
class Alignment:
    """Result of aligning one corpus against one source document."""
    extractor: str
    total_lines: int
    candidates: int
    regions: list[ExampleRegion]
    matched: dict[str, tuple[SourceCandidate, float]]
    unmatched_sentences: list[tuple[str, str]]
    sentence_count: int


def _s_text_for_matching(s: etree._Element) -> str:
    """The S's original FORM, falling back to the concatenated W tier.

    The W tier is the fallback because a scrape that leaves the S-level FORM
    empty still carries the sentence, just distributed across its words.
    """
    form = s.find('./FORM[@kindOf="original"]')
    if form is not None and form.text and form.text.strip():
        return form.text.strip()
    words = []
    for w in s.iter("W"):
        wf = w.find('./FORM[@kindOf="original"]') or w.find("./FORM")
        if wf is not None and wf.text:
            words.append(wf.text.strip())
    return " ".join(words)


def align(
    trees: list[tuple[Path, etree._ElementTree]],
    lines: list[str],
    extractor: str,
    threshold: int = DEFAULT_THRESHOLD,
) -> Alignment:
    """Match every XML sentence to its best source candidate.

    Uses rapidfuzz partial_ratio over letter skeletons. partial_ratio (rather
    than ratio) because a source line frequently carries trailing material the
    XML sentence does not — a citation, an example label, a page number.
    """
    from rapidfuzz import fuzz, process

    candidates = build_candidates(lines)
    regions = find_example_regions(lines)
    choices = [c.skel for c in candidates]

    matched: dict[str, tuple[SourceCandidate, float]] = {}
    unmatched: list[tuple[str, str]] = []
    sentence_count = 0

    for path, tree in trees:
        for s in tree.iter("S"):
            sentence_count += 1
            s_id = s.get("id") or ""
            key = f"{path}::{s_id}"
            text = _s_text_for_matching(s)
            skel = skeleton(text)
            if len(skel) < MIN_SKELETON or not choices:
                continue  # too short to align; not evidence of anything
            hit = process.extractOne(
                skel, choices, scorer=fuzz.partial_ratio, score_cutoff=threshold,
            )
            if hit is None:
                unmatched.append((key, text))
                continue
            _, score, idx = hit
            candidate = candidates[idx]
            matched[key] = (candidate, score)
            for region in regions:
                if region.start <= candidate.start <= region.end:
                    region.matched = True

    return Alignment(
        extractor=extractor,
        total_lines=len(lines),
        candidates=len(candidates),
        regions=regions,
        matched=matched,
        unmatched_sentences=unmatched,
        sentence_count=sentence_count,
    )


# ---------------------------------------------------------------------------
# Group C rules
# ---------------------------------------------------------------------------

def _xml_charset(s: etree._Element) -> Counter:
    """Every character the XML holds for this sentence, across S and W tiers.

    Markers legitimately live at the W tier while the S tier may be
    unsegmented, so a fidelity check that looked only at the S FORM would
    report every '-' in the source as lost.
    """
    chars: Counter = Counter()
    for form in s.iter("FORM"):
        chars.update(unicodedata.normalize("NFC", form.text or ""))
    return chars


def _interesting(ch: str) -> bool:
    return (ord(ch) > 127 and not ch.isspace()) or ch in _ASCII_OF_INTEREST


def source_findings(
    trees: list[tuple[Path, etree._ElementTree]],
    alignment: Alignment,
    source: Path,
) -> list[Finding]:
    """Emit G013/G020/G021/G022/G023 from a completed alignment."""
    findings: list[Finding] = []

    # --- G023: extraction self-report (always emitted) --------------------
    region_count = len(alignment.regions)
    matched_regions = sum(1 for r in alignment.regions if r.matched)
    findings.append(Finding(
        rule_id="G023",
        severity=Severity.WARN,
        message=(
            f"source={source.name} extractor={alignment.extractor}: "
            f"{alignment.total_lines} lines, {alignment.candidates} matchable "
            f"candidates, {region_count} numbered example region(s) detected. "
            f"XML sentences: {alignment.sentence_count}, of which "
            f"{len(alignment.matched)} matched and "
            f"{len(alignment.unmatched_sentences)} did not. "
            f"Example regions matched: {matched_regions}/{region_count}. "
            "Judge G020/G021 only after judging these extraction numbers."
        ),
        path=source,
        location="",
        count=1,
    ))

    # --- G020: XML sentence with no source match --------------------------
    for key, text in alignment.unmatched_sentences:
        path_str, _, s_id = key.partition("::")
        findings.append(Finding(
            rule_id="G020",
            severity=Severity.HARD,
            message=(
                f"S {s_id!r} has no match in {source.name} above the "
                f"similarity threshold; text was {text[:120]!r}"
            ),
            path=Path(path_str),
            location=f"S={s_id}",
        ))

    # --- G021: source example with no XML match ---------------------------
    for region in alignment.regions:
        if region.matched:
            continue
        preview = region.text.strip()[:120]
        findings.append(Finding(
            rule_id="G021",
            severity=Severity.HARD,
            message=(
                f"source example {region.label} (line {region.start + 1}) has no "
                f"matching sentence in the XML; possibly dropped. Text: {preview!r}"
            ),
            path=source,
            location=f"line={region.start + 1}",
        ))

    # --- G013 / G022: per matched pair ------------------------------------
    by_key = {}
    for path, tree in trees:
        for s in tree.iter("S"):
            by_key[f"{path}::{s.get('id') or ''}"] = (path, s)

    for key, (candidate, score) in alignment.matched.items():
        entry = by_key.get(key)
        if entry is None:
            continue
        path, s = entry
        s_id = s.get("id") or ""

        # G022: characters of interest present in source, absent from XML.
        src_chars = Counter(
            ch for ch in unicodedata.normalize("NFC", candidate.text)
            if _interesting(ch)
        )
        xml_chars = _xml_charset(s)
        lost = {
            ch: n - xml_chars.get(ch, 0)
            for ch, n in src_chars.items()
            if n > xml_chars.get(ch, 0)
        }
        if lost:
            rendered = ", ".join(
                f"{ch!r} (U+{ord(ch):04X}) x{n}" for ch, n in sorted(lost.items())
            )
            findings.append(Finding(
                rule_id="G022",
                severity=Severity.SOFT,
                message=(
                    f"S {s_id!r}: source line {candidate.start + 1} has "
                    f"character(s) the XML lacks: {rendered}. "
                    f"Source: {candidate.text.strip()[:120]!r}"
                ),
                path=path,
                location=f"S={s_id}",
                count=sum(lost.values()),
            ))

        # G013: source region offers several translations, XML kept one.
        region = next(
            (r for r in alignment.regions if r.start <= candidate.start <= r.end),
            None,
        )
        if region is None:
            continue
        transl_count = sum(1 for c in s if c.tag == "TRANSL")
        if len(region.translations) > 1 and transl_count == 1:
            findings.append(Finding(
                rule_id="G013",
                severity=Severity.SOFT,
                message=(
                    f"S {s_id!r} has 1 TRANSL but source example {region.label} "
                    f"offers {len(region.translations)}: {region.translations!r}. "
                    "Extra translations belong as alt TRANSL elements"
                ),
                path=path,
                location=f"S={s_id}",
                count=1,
            ))

    return findings


G_SOURCE_TITLES = {
    "G013": "translations_collapsed",
    "G020": "xml_sentence_unmatched_in_source",
    "G021": "source_example_missing_from_xml",
    "G022": "character_lost_vs_source",
    "G023": "extraction_self_report",
}

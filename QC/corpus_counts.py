"""Single source of truth for FormosanBank corpus counting rules.

Both statistics pipelines import from here:
  - QC/utilities/get_corpus_stats.py (per-corpus CSVs for the Gitbook)
  - QC/corpus_metrics.py and QC/count_tokens.py (size tracker + PR deltas)

Rules (decided 2026-06-10):
  - A token is a whitespace-separated chunk containing at least one
    Unicode letter or digit. "123" counts; "?" does not.
  - Per sentence, count the `standard` FORM if non-empty, else the
    `original` FORM, else 0. Word counts come from the S tier only —
    W and M FORMs are never counted as tokens.
  - Language identity comes from xml:lang + dialect attributes only:
    trv + dialect "Truku" is Truku; trv + anything else is Seediq.
"""
from __future__ import annotations

import csv
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

_REPO_ROOT = Path(__file__).resolve().parents[1]

# This module is imported both as `QC.corpus_counts` and, by callers that
# put QC/ itself on sys.path, as bare `corpus_counts`. Make the repo root
# importable so the shared FORM selector resolves either way.
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from QC.xml_forms import find_base_form, iter_base_forms  # noqa: E402


def load_language_codes(path: Path | None = None) -> dict[str, str]:
    """ISO 639-3 code -> display name, from the repo-root languages.csv.

    languages.csv is the single source of truth for language identity
    (POL-039: data that critical steps depend on lives in prominent
    human-readable registries, never hardcoded in python).
    """
    p = Path(path) if path else _REPO_ROOT / "languages.csv"
    with open(p, newline="", encoding="utf-8") as f:
        return {row["ISO639-3"].strip().lower(): row["Language"].strip()
                for row in csv.DictReader(f) if row["ISO639-3"].strip()}


LANG_CODE_TO_NAME = load_language_codes()

# All display names a record can resolve to (every code in
# languages.csv, plus Truku, which is distinguished from Seediq by
# dialect rather than by ISO code).
LANGUAGE_NAMES = sorted(set(LANG_CODE_TO_NAME.values()) | {"Truku"})

ENG_CODES = {"eng", "en"}
ZHO_CODES = {"zho", "zh", "zh-hant", "zh-hans"}
JPN_CODES = {"jpn", "ja"}
NLD_CODES = {"nld", "nl"}


def count_words(text: str | None) -> int:
    """Count whitespace-separated chunks containing >=1 letter or digit."""
    if not text:
        return 0
    return sum(1 for chunk in text.split() if any(c.isalnum() for c in chunk))


def select_sentence_form(sentence) -> str | None:
    """Return the text to count for one <S>: standard tier, else original.

    Only direct FORM children of S are considered (S-tier rule), and only
    each tier's *base* FORM — a POL-028 ``ver="alt"`` variant is a second
    reading of the same sentence, so counting one would double-count a
    reading the corpus never asserts as primary. A tier with variants but
    no base counts as absent (maintainer ruling 2026-09-10); V149 (HARD)
    reports that shape."""
    for kind in ("standard", "original"):
        for form in iter_base_forms(sentence, kind):
            if form.text and form.text.strip():
                return form.text
    return None


def resolve_language(language_code: str | None, dialect: str | None) -> str | None:
    """Resolve (xml:lang, dialect) to a display language name.

    trv + dialect 'Truku' is Truku; trv + anything else is Seediq.
    Returns None for unknown or missing codes (caller decides how to
    label those)."""
    code = (language_code or "").strip().lower()
    if not code:
        return None
    if code == "trv" and (dialect or "").strip().lower() == "truku":
        return "Truku"
    return LANG_CODE_TO_NAME.get(code)


COUNT_FIELDS = (
    "word_count",
    "sentences",
    "segmented_words",
    "glossed_words",
    "eng_transl_count",
    "zho_transl_count",
    "transcribed_audio_count",
    "untranscribed_audio_count",
    "word_elements",
    "morpheme_elements",
    "translation_elements",
    "audio_elements",
    "file_count",
    # Appended 2026-09-10: the bank's first Japanese material (Sato-Pazeh-Songs)
    # was reported as untranslated because only eng and zho were counted.
    "jpn_transl_count",
    # Appended 2026-09-10: same gap, older. Siraya_Gospels and
    # UtrechtManuscriptWordList have carried Dutch translations all along.
    "nld_transl_count",
)


def split_audio_elements(root) -> tuple[list, list]:
    """Return (transcribed, untranscribed) AUDIO elements with a file attr.

    Transcribed = nested in S or W; untranscribed = direct child of TEXT."""
    transcribed = [e for e in root.findall(".//S/AUDIO") if "file" in e.attrib]
    transcribed += [e for e in root.findall(".//W/AUDIO") if "file" in e.attrib]
    untranscribed = [e for e in root.findall("AUDIO") if "file" in e.attrib]
    return transcribed, untranscribed


def analyze_root(root) -> dict:
    """Compute the per-file statistics record from a parsed TEXT element."""
    language = (root.get(XML_LANG) or "").strip().lower()
    dialect = (root.get("dialect") or "").strip()
    warnings = []
    if not language:
        warnings.append("missing xml:lang attribute")
    if not dialect:
        warnings.append("missing dialect attribute")

    record: dict[str, Any] = {field: 0 for field in COUNT_FIELDS}
    record.update({"language": language, "dialect": dialect, "file_count": 1})

    for sentence in root.findall(".//S"):
        record["sentences"] += 1
        text = select_sentence_form(sentence)
        if text is None:
            if find_base_form(sentence) is None:
                warnings.append(
                    f"sentence {sentence.get('id', '?')} has no countable FORM at the S level"
                )
            n = 0
        else:
            n = count_words(text)
        record["word_count"] += n

        transl_langs = {
            (t.get(XML_LANG) or "").strip().lower()
            for t in sentence.findall("TRANSL")
            if t.text and t.text.strip()
        }
        if transl_langs & ENG_CODES:
            record["eng_transl_count"] += n
        if transl_langs & ZHO_CODES:
            record["zho_transl_count"] += n
        if transl_langs & JPN_CODES:
            record["jpn_transl_count"] += n
        if transl_langs & NLD_CODES:
            record["nld_transl_count"] += n
        if sentence.find(".//M") is not None:
            record["segmented_words"] += n
        if sentence.find(".//M/TRANSL") is not None:
            record["glossed_words"] += n

    transcribed, untranscribed = split_audio_elements(root)
    record["transcribed_audio_count"] = len(transcribed)
    record["untranscribed_audio_count"] = len(untranscribed)
    record["word_elements"] = len(root.findall(".//W"))
    record["morpheme_elements"] = len(root.findall(".//M"))
    record["translation_elements"] = len(root.findall(".//TRANSL"))
    record["audio_elements"] = len(root.findall(".//AUDIO"))
    record["warnings"] = warnings
    return record


def analyze_file(xml_path) -> dict:
    """Parse one XML file and return its statistics record.

    Raises xml.etree.ElementTree.ParseError on malformed XML — callers
    decide whether to collect or abort."""
    root = ET.parse(xml_path).getroot()
    record = analyze_root(root)
    record["path"] = str(xml_path)
    return record


def collect_records(xml_dir) -> tuple[list[dict], list[dict]]:
    """Analyze every *.xml under xml_dir. Returns (records, parse_errors).

    Files under a CodeAndDocs/ directory are skipped: that folder holds
    reproduction infrastructure — scripts, raw scrapes, and POL-035
    pre-correction snapshots — never published corpus data, and counting
    a snapshot would double a corpus's apparent size.
    """
    records, parse_errors = [], []
    for xml_file in sorted(Path(xml_dir).rglob("*.xml")):
        if "CodeAndDocs" in xml_file.parts:
            continue
        try:
            records.append(analyze_file(xml_file))
        except Exception as exc:
            parse_errors.append({"path": str(xml_file), "error": str(exc)})
    return records, parse_errors


# ---------------------------------------------------------------------------
# Shared corpus/file discovery. EVERY consumer that counts tokens or builds
# statistics must go through these helpers so that no two counting scripts
# can ever arrive at different file sets (maintainer ruling 2026-08-11).
# ---------------------------------------------------------------------------

def is_published_xml(path) -> bool:
    """Is this path a published corpus XML file?

    The one predicate every counter must agree on (maintainer ruling
    2026-08-11). Two conditions, both load-bearing:

    - a path segment `XML`, because some corpora nest folders between the
      corpus root and `XML/`; and
    - no path segment `CodeAndDocs`, because that folder holds reproduction
      infrastructure -- scripts, raw scrapes, and POL-035 pre-correction
      snapshots -- never published data. A snapshot is a byte-for-byte
      ancestor of the corpus beside it, so counting one doubles that
      corpus's apparent size.

    Accepts a Path or a `/`-joined string, so callers walking the filesystem
    and callers reading `git ls-tree` output can share it.
    """
    parts = Path(path).parts if not isinstance(path, str) else tuple(path.split("/"))
    return (
        str(path).endswith(".xml")
        and "XML" in parts
        and "CodeAndDocs" not in parts
    )


def is_reproduction_path(path, root=None) -> bool:
    """Does this path sit inside a corpus's CodeAndDocs/ directory?

    The narrow half of `is_published_xml`, split out because every tool
    that reads corpus XML needs it while only counters need the rest.
    `CodeAndDocs/` holds reproduction infrastructure -- build scripts, raw
    scrapes, and POL-035 pre-correction snapshots -- never published data.
    A snapshot is a byte-for-byte ancestor of the corpus beside it, so a
    tool that walks a corpus root without this check reads the same text
    twice, and a tool that writes will rewrite a baseline that exists
    precisely to stay untouched.

    `root` is the directory the caller was pointed at, and it matters:
    several builds stage into `<corpus>/CodeAndDocs/Final_XML/` and clean
    there before installing into `XML/` (NTUFormosanCorpus does exactly
    this). When the root is itself inside CodeAndDocs the caller meant
    that tree, and refusing to process what it was explicitly handed
    would turn the build into a silent no-op. So the rule is "do not
    wander into CodeAndDocs", not "refuse to touch CodeAndDocs".

    Deliberately does NOT require an `XML` path segment the way
    `is_published_xml` does, for the same staging-directory reason.
    """
    parts = Path(path).parts if not isinstance(path, str) else tuple(path.split("/"))
    if "CodeAndDocs" not in parts:
        return False
    if root is not None:
        root_parts = (Path(root).parts if not isinstance(root, str)
                      else tuple(root.split("/")))
        if "CodeAndDocs" in root_parts:
            return False
    return True


def corpus_xml_dirs(corpus_path) -> list[Path]:
    """Every XML/ directory of a corpus, at ANY depth (Corpora/.../XML —
    some corpora nest folders between the corpus root and XML/), skipping
    CodeAndDocs. Empty list when the corpus has no XML/ directory."""
    return sorted(p for p in Path(corpus_path).rglob("XML")
                  if p.is_dir() and "CodeAndDocs" not in p.parts)


def collect_corpus_records(corpus_path) -> tuple[list[dict], list[dict]]:
    """collect_records over all of one corpus's XML/ dirs (fallback: the
    corpus dir itself, for dev-repo layouts without an XML/ folder)."""
    records, parse_errors = [], []
    for d in corpus_xml_dirs(corpus_path) or [Path(corpus_path)]:
        r, e = collect_records(d)
        records.extend(r)
        parse_errors.extend(e)
    return records, parse_errors


def iter_corpus_dirs(corpora_root) -> list[Path]:
    """Immediate subdirectories of corpora_root that contain an XML/ dir."""
    root = Path(corpora_root)
    return sorted(d for d in root.iterdir()
                  if d.is_dir() and corpus_xml_dirs(d))


def collect_tree_records(root) -> tuple[list[dict], list[dict]]:
    """Records for a whole Corpora tree OR a single corpus, via the same
    per-corpus discovery either way."""
    corpus_dirs = iter_corpus_dirs(root)
    if not corpus_dirs:
        return collect_corpus_records(root)
    records, parse_errors = [], []
    for d in corpus_dirs:
        r, e = collect_corpus_records(d)
        records.extend(r)
        parse_errors.extend(e)
    return records, parse_errors

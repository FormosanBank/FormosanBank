"""SOFT-severity rules: violations populate the SOFT CSV but do not
affect exit code.

Each rule pre-aggregates per (rule_id, file, language, character).
Returning thousands of un-aggregated Findings per file would flood
the CSV writer.

Signature: same as HARD rules.
"""
import difflib
import unicodedata
from pathlib import Path

from lxml import etree

from QC.validation._corpus_index import CorpusIndex
from QC.validation._finding import Finding, Severity


_XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

# POL-028 alternate-FORM thresholds. Deliberately here rather than in
# POLICIES.md: the policy states the requirement in words so these can be
# tuned from evidence without a re-ruling.
_ALT_OVERLAP_RATIO = 0.6      # below this, the pair does not look related
_ALT_SHORT_EXEMPT = 2         # shorter form <= this: ratio is meaningless
_ALT_LENGTH_FACTOR = 2        # longer form may not exceed this * shorter


def _fold(text: str | None) -> str:
    """Casefold and drop combining marks, so 'tâu' compares as 'tau'."""
    decomposed = unicodedata.normalize("NFD", (text or "").strip().lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def v010_count_s_without_form(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V010 SOFT: count S elements that have no FORM children.

    Per design, this is informational rather than fatal: the S has no
    sentence-level text but the file is still well-formed (e.g., a
    diarized-audio S that has not yet been transcribed). Aggregated per
    (rule, file, language) — one Finding per file with the total count.

    Does NOT consult index; runs in pass 1.
    """
    count = sum(
        1 for s in tree.iter("S")
        if not any(child.tag == "FORM" for child in s)
    )
    if count == 0:
        return []
    # Resolve language: from index if available, else from tree root.
    if index is not None and path in index.langs:
        lang = index.langs[path]
    else:
        lang = tree.getroot().get(_XML_LANG) or ""
    return [Finding(
        rule_id="V010",
        severity=Severity.SOFT,
        message=f"V010 SOFT: count={count} S elements missing FORM",
        path=path,
        count=count,
        language=lang,
        character="",
    )]


def v014_count_missing_standard_form(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V014 SOFT: count S/W/M elements that have FORM children but none
    with kindOf='standard'.

    Per design, missing a standard-tier FORM is informational rather
    than fatal. Some corpora legitimately lack a standard tier because
    the orthography is unsettled. Aggregated per (rule, file, language)
    — one Finding per file with the total count.

    Does NOT consult index; runs in pass 1.
    """
    count = 0
    for elem in tree.iter("S", "W", "M"):
        forms = [child for child in elem if child.tag == "FORM"]
        if not forms:
            # No FORMs at all — V010 (SOFT) handles this case for S;
            # V011/V012 (HARD) handle it for W/M.
            continue
        has_standard = any(f.get("kindOf") == "standard" for f in forms)
        if not has_standard:
            count += 1
    if count == 0:
        return []
    # Resolve language: from index if available, else from tree root.
    if index is not None and path in index.langs:
        lang = index.langs[path]
    else:
        lang = tree.getroot().get(_XML_LANG) or ""
    return [Finding(
        rule_id="V014",
        severity=Severity.SOFT,
        message=f"V014 SOFT: count={count} S/W/M elements missing standard FORM (missing-standard tier)",
        path=path,
        count=count,
        language=lang,
        character="",
    )]


def _children(elem: etree._Element, tag: str) -> list:
    """Direct children of `elem` with the given tag."""
    return [child for child in elem if child.tag == tag]


def _sentence_words(tree: etree._ElementTree) -> list:
    """Per sentence, its direct-child W elements (sentences with W only)."""
    return [ws for ws in (_children(s, "W") for s in tree.iter("S")) if ws]


def _first_form_text(elem: etree._Element) -> str:
    """Text of the element's first FORM child, whitespace-stripped."""
    for child in elem:
        if child.tag == "FORM":
            return (child.text or "").strip()
    return ""


def _carries_parsing(ws: list) -> bool:
    """Does this sentence carry *some* morphological analysis?

    Two clauses, either one sufficient — the same criterion applied by
    YeddaPalemeqBlog's CodeAndDocs/fix_m_tier.py, kept identical so a
    corpus fixed by that script validates clean:

    1. some W has two or more M children; or
    2. some M's FORM differs from its parent W's FORM (an infix split
       such as ``l<em>angeda`` -> ``l-angeda`` / ``-em-`` carries an
       analysis even at one M per W).

    Anything else is an all-single-M mirror tier: no analysis at all.
    """
    for w in ws:
        ms = _children(w, "M")
        if len(ms) >= 2:
            return True
        w_form = _first_form_text(w)
        if any(_first_form_text(m) != w_form for m in ms):
            return True
    return False


def _tree_language(tree: etree._ElementTree, path: Path,
                   index: CorpusIndex | None) -> str:
    if index is not None and path in index.langs:
        return index.langs[path]
    return tree.getroot().get(_XML_LANG) or ""


def v144_M_less_W_in_parsed_sentence(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V144 SOFT (POL-023): a morphologically parsed sentence with M-less Ws.

    Ruling 2026-08-12 (re-scoped from per file to **per sentence**): the
    unit of morphological analysis is the sentence, not the file. In a
    sentence that carries *some* parsing every W needs at least one M (a
    single M there reads "analyzed as monomorphemic"); a sentence the
    author simply never analyzed carries no M tier at all, and demanding
    M there would fake an analysis. The old file-scoped reading punished
    exactly that honest mixed state — one parsed sentence made every
    unparsed sentence in the file a finding.

    Aggregated per file (one Finding, counting the M-less Ws inside
    parsed sentences). SOFT because existing corpora trip this and need
    fixing over time.
    """
    parsed = [ws for ws in _sentence_words(tree) if _carries_parsing(ws)]
    if not parsed:
        return []
    missing = 0
    sentences = 0
    for ws in parsed:
        m_less = sum(1 for w in ws if not _children(w, "M"))
        if m_less:
            missing += m_less
            sentences += 1
    if missing == 0:
        return []
    return [Finding(
        rule_id="V144",
        severity=Severity.SOFT,
        message=(
            f"V144 SOFT: {missing} W elements in {sentences} of "
            f"{len(parsed)} morphologically parsed sentences have no M "
            f"child (POL-023: within a parsed sentence every W gets at "
            f"least one M; an unparsed sentence carries no M tier)"
        ),
        path=path,
        count=missing,
        language=_tree_language(tree, path, index),
        character="",
    )]


def v145_degenerate_all_single_M_tier(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V145 SOFT (POL-023): M level present but the file carries no parsing.

    Ruling 2026-08-10: corpora without morpheme segmentation should have
    no M level at all — an M tier where every M-bearing W has exactly
    one M identical in role to its W adds no information (historically:
    ~100 spurious M shells shipped in YeddaPalemeqBlog).

    Deliberately kept **file-scoped** when V144 went per-sentence
    (2026-08-12). "Every M mirrors its W" is only evidence of a fake
    tier in bulk: a single sentence whose handful of words really are
    monomorphemic is indistinguishable from a mirror tier, and POL-023
    explicitly blesses single-M Ws as "analyzed as monomorphemic". A
    whole file with no multi-morphemic word anywhere is the reliable
    signal; one sentence is not. Same severity as before.
    """
    sentences = _sentence_words(tree)
    if not sentences or any(_carries_parsing(ws) for ws in sentences):
        return []
    singles = sum(1 for ws in sentences for w in ws if _children(w, "M"))
    if singles == 0:
        return []
    return [Finding(
        rule_id="V145",
        severity=Severity.SOFT,
        message=(
            f"V145 SOFT: M level present but no sentence in the file "
            f"carries any morphological parsing ({singles} mirror single-M "
            f"Ws) — unsegmented corpora should have no M level (POL-023)"
        ),
        path=path,
        count=singles,
        language=_tree_language(tree, path, index),
        character="",
    )]


def v148_W_less_S_in_segmented_file(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V148 SOFT (POL-041): a partially word-segmented file.

    The W tier asks the same question as the M tier (POL-023) one level
    up, and gets the same answer at file scope: a corpus with no word
    segmentation has **no W level at all**, and that is the normal state
    for most of the bank — never a finding. But a file where *some*
    sentences carry a W tier and others do not is an incomplete
    segmentation pass, and the unsegmented sentences are worth
    surfacing.

    Deliberately **file-scoped**, unlike V144. V144 can be per sentence
    because a parsed sentence announces itself (a W with 2+ M, or an M
    FORM differing from its W FORM). A sentence with no W announces
    nothing at all — there is no per-sentence signal distinguishing
    "not segmented yet" from "not segmented, by design". Only the
    presence of segmented siblings in the same file makes the omission
    legible, so the file is the unit.

    An S with no FORM is never counted: an untranscribed-audio shell has
    no text to segment (V010 already reports it). Aggregated per file.
    """
    with_form = [s for s in tree.iter("S") if s.find("./FORM") is not None]
    if not with_form:
        return []
    w_less = [s for s in with_form if s.find("./W") is None]
    # No W anywhere -> not a segmented corpus. All W -> nothing to report.
    if not w_less or len(w_less) == len(with_form):
        return []
    return [Finding(
        rule_id="V148",
        severity=Severity.SOFT,
        message=(
            f"V148 SOFT: {len(w_less)} of {len(with_form)} sentences have "
            f"no W tier while others in the file do — incomplete word "
            f"segmentation (POL-041)"
        ),
        path=path,
        count=len(w_less),
        language=_tree_language(tree, path, index),
        character="",
    )]


def v150_alternate_FORM_low_overlap(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V150 SOFT (POL-028): an alternate FORM that does not look like a
    spelling variant of its sibling.

    Two independent conditions, either of which flags:

    * **overlap** — the similarity ratio against the closest non-alternate
      sibling is below 0.6. Pairs whose *shorter* form is 2 characters or
      fewer are exempt, because a one- or two-letter form cannot produce a
      meaningful ratio (Wakelin's `a`/`u` scores 0.00 and is correct).
    * **proportion** — the longer form is more than twice the shorter.
      Catches *disproportionate* pairs specifically: on its own the overlap
      exemption above would wave through any short form paired with a long
      one, and a truncation or expansion is not a spelling variant however
      it scores. It does not close every hole that exemption opens — any
      pair with the shorter form <=2 chars and the longer at most 2x that
      escapes both conditions regardless of overlap; those are left to
      review by design (see POL-028).

    The two conditions are asymmetric on purpose, not by oversight: the
    overlap condition has a short-form floor (`lo > _ALT_SHORT_EXEMPT`) so
    a 1- or 2-character pair is never judged on an unmeasurable ratio, but
    the proportion condition has no such floor. At length 1, doubling is a
    difference of a single extra character, so `a`/`aya` (1 vs 3) fails
    proportion while POL-028's own worked example `a`/`u` (1 vs 1) passes
    both. This is deliberate — proportion is about the *ratio* of lengths,
    which is genuinely more volatile at length 1 — and is not to be
    "fixed" by adding a floor here without a re-ruling.

    SOFT, not HARD: legitimate pairs sit below the ratio and cannot be
    separated by any threshold (`pipangn-epen`/`pipangengne-eben`, 0.57).
    A reviewer resolves each; confirmed-fine pairs are recorded in the
    worklist so they are not re-litigated.

    Emits one Finding per offending alternate rather than aggregating: the
    population is ~12 bank-wide, and an aggregate count tells a reviewer
    nothing about which pair to look at.
    """
    findings: list[Finding] = []
    for parent in tree.iter("S", "W", "M"):
        forms = [child for child in parent if child.tag == "FORM"]
        alternates = [f for f in forms if f.get("kindOf") == "alternate"]
        bases = [f for f in forms if f.get("kindOf") != "alternate"]
        if not alternates or not bases:
            continue          # bare alternates are V149's business
        for alt in alternates:
            alt_text = (alt.text or "").strip()
            ratio, base_text = max(
                (
                    (
                        difflib.SequenceMatcher(
                            None, _fold(alt_text), _fold(base.text),
                            autojunk=False,
                        ).ratio(),
                        (base.text or "").strip(),
                    )
                    for base in bases
                ),
                key=lambda pair: pair[0],
            )
            lo = min(len(alt_text), len(base_text))
            hi = max(len(alt_text), len(base_text))
            reasons: list[str] = []
            if ratio < _ALT_OVERLAP_RATIO and lo > _ALT_SHORT_EXEMPT:
                reasons.append(f"overlap {ratio:.2f} < {_ALT_OVERLAP_RATIO}")
            if hi > _ALT_LENGTH_FACTOR * lo:
                reasons.append(
                    f"lengths {lo} vs {hi}, more than "
                    f"{_ALT_LENGTH_FACTOR}x apart"
                )
            if not reasons:
                continue
            p_id = parent.get("id")
            findings.append(Finding(
                rule_id="V150",
                severity=Severity.SOFT,
                message=(
                    f"{parent.tag} id={p_id!r}: alternate {alt_text!r} does "
                    f"not look like a spelling variant of {base_text!r} "
                    f"({'; '.join(reasons)}) — POL-028"
                ),
                path=path,
                location=f"{parent.tag}={p_id}" if p_id else parent.tag,
                language=_tree_language(tree, path, index),
                character="",
            ))
    return findings


def v151_S_TRANSL_has_no_kindOf(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V151 SOFT: an S-level TRANSL must not carry @kindOf.

    `kindOf` on a TRANSL is a gloss-level distinction. At W and M level a
    TRANSL carries a gloss, and `kindOf` separates the source's own gloss
    (`original`) from a standardized one (`standard`) — the axis a future
    gloss-standardization pass will use, and the reason
    HundredPaiwanStories' 61,493 W/M uses are correct and must not be
    stripped. At S level a TRANSL is a free translation: there is no
    original-vs-standard axis and the attribute carries no information.

    SOFT while Glosbe's 4,157 legacy S-level attributes remain in published
    XML. This is not about CI: `.github/workflows/xml-validation.yaml`'s
    PR job only blocks HARD fingerprints newly introduced in files a PR
    actually touches, and its full-corpus job runs with
    --no-exit-on-hard, so a HARD V151 would block only PRs that themselves
    touch Glosbe's three `_tmem.xml` files. The real cost is local and
    tooling-wide: a HARD rule firing 4,157 times makes validate_xml.py
    exit 1 on every local run over Glosbe (or the whole corpus) and on
    every run-qc-pipeline invocation that includes it, and it poisons the
    longitudinal finding baseline with 4,157 entries that never clear. It
    is promoted to HARD by the Glosbe remediation, not here.

    Aggregated per file — unlike V150, the population is in the thousands
    and the fix is one scripted strip per file.
    """
    count = sum(
        1 for s in tree.iter("S")
        for child in s
        if child.tag == "TRANSL" and child.get("kindOf") is not None
    )
    if count == 0:
        return []
    return [Finding(
        rule_id="V151",
        severity=Severity.SOFT,
        message=(
            f"{count} S-level TRANSL elements carry @kindOf; kindOf is a "
            "gloss-level distinction and is meaningless on a free "
            "translation (POL-025 amendment)"
        ),
        path=path,
        count=count,
        language=_tree_language(tree, path, index),
        character="",
    )]


RULES: list = [
    v010_count_s_without_form,
    v014_count_missing_standard_form,
    # POL-023 M-tier consistency (2026-08-10; V144 per-sentence 2026-08-12)
    v144_M_less_W_in_parsed_sentence,
    v145_degenerate_all_single_M_tier,
    # POL-041 W-tier presence (2026-09-03), file-scoped
    v148_W_less_S_in_segmented_file,
    # POL-028 alternate FORMs (2026-09-08)
    v150_alternate_FORM_low_overlap,
    # POL-025 S-level TRANSL @kindOf (2026-09-08)
    v151_S_TRANSL_has_no_kindOf,
]
CROSS_FILE_RULES: list = []

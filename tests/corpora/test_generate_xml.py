"""POL-047/POL-048: one reproduction entry point, one canonical step order.

Everything checked here is static, because everything the 2026-09-05 pipeline
audit found was findable by reading the scripts: eight entry-point conventions,
twelve step orderings, validators inside builds, builds that demand a second
pinned checkout. Actually running a build -- the idempotency half of POL-047 --
is not attempted, since some corpora are millions of operations. This is the
cheap half, and its value is that a new or re-ported corpus cannot add
divergence.

Two escape hatches, deliberately different:

* `generate_xml_pending.txt` (repo root) lists corpora that predate POL-047.
  They are skipped whole. The list only shrinks.
* A corpus that has migrated but departs from the shape on purpose declares it
  with a `**POL-047 deviation:**` line in its README. POL-047 permits deviation
  and requires it to be stated; this enforces the stating, and a human does the
  interrogating.

Self-containment (POL-048) has no deviation clause and cannot be waived.
"""
import re

import pytest

from tests._helpers import REPO_ROOT

ENTRY_POINT = "generate_xml.sh"
PENDING_FILE = REPO_ROOT / "generate_xml_pending.txt"
DEVIATION_MARKER = "**POL-047 deviation:**"

#: Older entry-point names. A migrated corpus has exactly one entry point, so
#: leaving the previous name behind is the ambiguity POL-047 exists to remove.
COMPETING_NAMES = (
    "make_xml.sh", "make.sh", "reproduce.sh", "rebuild_xml.sh",
    "run_qc_pipeline.sh", "build.sh", "Makefile", "makefile",
)

#: POL-048: a build reads its own CodeAndDocs/ and the shared repo, nothing else.
NOT_SELF_CONTAINED = (
    "VALIDATOR_ROOT", "VALIDATOR_PYTHON", "FORMOSANBANK_AUTHORITY",
    "FORMOSANBANK_QC_ROOT", "FORMOSANBANK_QC_PYTHON",
    "GLOSBE_ILRDF_REFERENCE_REPO", "EXPECTED_AUTHORITY_COMMIT",
    "EXPECTED_VALIDATOR_COMMIT", "Private/",
)

#: Shared steps whose relative order POL-047 fixes.
DERIVED_CHAIN = ("clean_xml", "standardize", "add_phonology")


def _pending() -> set[str]:
    if not PENDING_FILE.exists():
        return set()
    return {
        line.strip()
        for line in PENDING_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def _corpora() -> list[str]:
    return sorted(d.name for d in (REPO_ROOT / "Corpora").iterdir() if d.is_dir())


CORPORA = _corpora()


def _readme_text(corpus: str) -> str:
    for name in ("README.md", "readme.md"):
        path = REPO_ROOT / "Corpora" / corpus / name
        if path.exists():
            return path.read_text(encoding="utf-8")
    return ""


def _declares_deviation(corpus: str) -> bool:
    return DEVIATION_MARKER in _readme_text(corpus)


def _entry_path(corpus: str):
    return REPO_ROOT / "Corpora" / corpus / "CodeAndDocs" / ENTRY_POINT


#: A line that actually runs something names an interpreter: "$PY", $PYTHON,
#: "$PAIWAN_PYTHON", python3. Lines that merely *mention* a script path do not
#: — `test -f ".../clean_xml.py"` preflight guards and the bare-path lists some
#: builds check up front. Counting those as invocations is not cosmetic: a
#: preflight `test -f` sitting above the real calls reads as the first
#: occurrence of its step and hides a genuine order inversion underneath it.
INVOCATION_RE = re.compile(r"python|\$\{?PY[A-Z_]*\}?", re.IGNORECASE)


def _code(corpus: str) -> str:
    """Entry-point body with whole-line comments dropped.

    Comments name the steps they introduce, so scanning raw text would read a
    corpus's own documentation as if it were an invocation.
    """
    text = _entry_path(corpus).read_text(encoding="utf-8")
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("#")
    )


def _invocations(corpus: str) -> str:
    """Comment-stripped body, keeping only lines that invoke an interpreter."""
    return "\n".join(
        line for line in _code(corpus).splitlines() if INVOCATION_RE.search(line)
    )


def _require_migrated(corpus: str):
    if _entry_path(corpus).exists():
        return
    if corpus in _pending():
        pytest.skip(f"{corpus} predates POL-047 (generate_xml_pending.txt)")
    pytest.fail(
        f"POL-047: {corpus} has no CodeAndDocs/{ENTRY_POINT}. Give it one entry "
        "point with the canonical name, or — only for a corpus that predates "
        "the policy — add it to generate_xml_pending.txt."
    )


def test_pending_list_names_real_corpora():
    """A pending entry that no longer names a corpus hides a missing script."""
    unknown = sorted(_pending() - set(CORPORA))
    assert not unknown, (
        f"generate_xml_pending.txt names corpora that do not exist: {unknown}. "
        "Remove the stale lines — the list only shrinks."
    )


def test_pending_list_has_no_migrated_corpora():
    """The list shrinks by itself, rather than quietly going out of date.

    A corpus that has since gained an entry point is still fully checked -- the
    pending list only matters when the file is absent -- so a stale line breaks
    nothing. It does misdescribe the backlog, and the backlog is the reason the
    list exists, so say so here instead of letting it rot.
    """
    migrated = sorted(c for c in _pending() if _entry_path(c).exists())
    assert not migrated, (
        f"generate_xml_pending.txt still lists corpora that now have "
        f"CodeAndDocs/{ENTRY_POINT}: {migrated}. Delete those lines."
    )


@pytest.mark.parametrize("corpus", CORPORA)
def test_entry_point_is_executable(corpus):
    _require_migrated(corpus)
    assert _entry_path(corpus).stat().st_mode & 0o111, (
        f"POL-047: {corpus}/CodeAndDocs/{ENTRY_POINT} is not executable "
        "(git update-index --chmod=+x)."
    )


@pytest.mark.parametrize("corpus", CORPORA)
def test_no_competing_entry_point(corpus):
    _require_migrated(corpus)
    code_docs = REPO_ROOT / "Corpora" / corpus / "CodeAndDocs"
    leftovers = sorted(
        str(p.relative_to(code_docs))
        for name in COMPETING_NAMES
        for p in code_docs.rglob(name)
    )
    assert not leftovers, (
        f"POL-047: {corpus} has {ENTRY_POINT} alongside older entry points "
        f"{leftovers}. One corpus, one entry point — delete or fold in the rest."
    )


@pytest.mark.parametrize("corpus", CORPORA)
def test_build_is_self_contained(corpus):
    """POL-048 — no deviation clause; this one cannot be waived."""
    _require_migrated(corpus)
    code = _code(corpus)
    found = sorted({token for token in NOT_SELF_CONTAINED if token in code})
    assert not found, (
        f"POL-048: {corpus}'s {ENTRY_POINT} depends on something outside this "
        f"checkout ({found}). A published corpus rebuilds from a FormosanBank "
        "checkout alone — dev repos are permanently private. POL-048 has no "
        "deviation clause."
    )


@pytest.mark.parametrize("corpus", CORPORA)
def test_build_does_not_run_validators(corpus):
    _require_migrated(corpus)
    if "QC/validation/" not in _invocations(corpus):
        return
    assert _declares_deviation(corpus), (
        f"POL-047: {corpus}'s {ENTRY_POINT} runs QC/validation/. A build that "
        "cannot complete because a validator fails cannot be used to "
        "investigate the failure — move them to validate.sh, or state the "
        f"reason in the README with a '{DEVIATION_MARKER}' line."
    )


@pytest.mark.parametrize("corpus", CORPORA)
def test_shared_steps_run_in_canonical_order(corpus):
    """Relative order only — corpora legitimately omit steps and repeat them."""
    _require_migrated(corpus)
    code = _invocations(corpus)
    at = {
        step: [m.start() for m in re.finditer(re.escape(step + ".py"), code)]
        for step in (*DERIVED_CHAIN, "apply_manual_edits")
    }

    problems = []
    present = [step for step in DERIVED_CHAIN if at[step]]
    for earlier, later in zip(present, present[1:]):
        if at[earlier][0] > at[later][0]:
            problems.append(f"{earlier} runs after {later}")
    # An edit record carries no standard FORM and no PHON, so both are
    # regenerated after it. Position relative to clean_xml is deliberately free.
    if at["apply_manual_edits"] and at["standardize"]:
        if at["apply_manual_edits"][0] > at["standardize"][-1]:
            problems.append("apply_manual_edits runs after the last standardize")

    if not problems:
        return
    assert _declares_deviation(corpus), (
        f"POL-047: {corpus}'s {ENTRY_POINT} departs from the canonical step "
        f"order ({'; '.join(problems)}). Reorder it, or state the reason in the "
        f"README with a '{DEVIATION_MARKER}' line."
    )

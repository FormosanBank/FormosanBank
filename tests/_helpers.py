"""Shared test helpers for FormosanBank's pytest suite.

The path-strip pattern and marker-matching convention were originally
duplicated in tests/validators/test_validate_xml.py and tests/cleaners/
test_clean_xml_extensions.py. Centralizing them here keeps the convention
in a single source of truth so a regex update or marker-matching tweak
applies uniformly across the suite.
"""
import re
import subprocess
from pathlib import Path


# Match any non-whitespace token that ends in ".xml" or ".csv", with or
# without a leading slash. The broad pattern catches both full paths
# ("/tmp/.../v051_AUDIO_empty_file_attr.xml") and bare basenames
# ("v051_AUDIO_empty_file_attr.xml") that scripts may print. Stripping
# these before marker matching prevents fixture filenames (which encode
# the rule ID) and SOFT-CSV output paths (which include the pytest test
# function name, also encoding the rule ID) from falsely satisfying
# rule-specific assertions and turning xfail tests into XPASSes for
# the wrong reason.
FILE_PATH_RE = re.compile(r"\S*\.(?:xml|csv)")


def combined_output(
    proc: subprocess.CompletedProcess, corpora_path: Path | None = None
) -> str:
    """Return stdout+stderr lowercased, with file paths stripped.

    Two strip passes:
    1. The corpora_path itself, because pytest's tmp_path includes the
       test function name, which often includes the rule ID — without
       stripping, every rule-marker check would trivially match the path.
    2. Any token ending in .xml (fixture basenames also encode the rule
       ID and would similarly cause false matches).

    Lowercasing makes marker matching case-insensitive.
    """
    raw = proc.stdout + proc.stderr
    if corpora_path is not None:
        raw = raw.replace(str(corpora_path), "<corpora_path>")
    return FILE_PATH_RE.sub("<path>", raw).lower()


def has_marker(
    proc: subprocess.CompletedProcess,
    markers,
    corpora_path: Path | None = None,
) -> bool:
    """Did the script's combined output contain any of the given markers?

    Markers are matched case-insensitively against the path-stripped
    combined output. Use this for both rule-specific assertions
    (e.g., `("v015", "duplicate kindof")`) and generic finding-class
    assertions (e.g., `("error", "violation", "invalid")`). Pass
    `corpora_path` whenever the script's output can include the
    tmp_path under test.
    """
    combined = combined_output(proc, corpora_path)
    return any(m.lower() in combined for m in markers)


def csv_warning_exists(corpora_path: Path, rule_id: str) -> bool:
    """Did any CSV under corpora_path mention the rule_id?

    Used by cleaner-extension xfail tests targeting warning-CSV output
    that sub-project B will add. Looks for the rule_id case-insensitively
    inside any .csv file under corpora_path.

    `rule_id` is REQUIRED. A previous version of this helper fell back
    to generic "warning"/"rule" keyword matching when rule_id was None,
    but that fallback would XPASS every per-rule call once B's cleaner
    starts emitting any CSV containing those keywords (including
    unrelated CSVs like a transformation counter). Per-rule callers
    must pin the rule they care about.
    """
    for path in corpora_path.rglob("*.csv"):
        try:
            content = path.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        if rule_id.lower() in content:
            return True
    return False

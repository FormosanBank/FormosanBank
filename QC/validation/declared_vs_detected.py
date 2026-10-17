#!/usr/bin/env python3
"""declared_vs_detected.py — does the corpus's text say what its pipeline says?

Two declarations are made about every corpus, and both fail silently when wrong:

  * the DIALECT the build writes into TEXT/@dialect;
  * the SOURCE ORTHOGRAPHY the build names — the `--orthography <name>` that
    add_phonology.py gets, or the `<Lang>_<Source>_113.tsv` conversion table
    standardize.py gets, in CodeAndDocs/generate_xml.sh — and the README repeats.

This script sets each declaration beside what the two detectors say about the
text, one table per question, so a port audit can quote it:

  dialect      QC/utilities/dialect_detector, per file on the standard tier,
               against TEXT/@dialect (languages with a trained model only)
  orthography  QC/utilities/orthography_detector on the ORIGINAL tier, files
               pooled per declared dialect, against the declared source
               orthography; and on the STANDARD tier against Ortho113, which
               is what standardize.py is meant to produce

It exits 0 whatever it finds: the tables are evidence for a human, not a gate.
Rows marked MISMATCH are the ones to read.

    python QC/validation/declared_vs_detected.py --xml Corpora/<Corpus>/XML \\
        [--generate-xml Corpora/<Corpus>/CodeAndDocs/generate_xml.sh] \\
        [--declared-orthography Ortho94] [--skip-dialect] [--skip-orthography]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from QC.corpus_counts import is_reproduction_path  # noqa: E402

DEFAULT_MODELS = REPO_ROOT / "QC" / "utilities" / "dialect_models"
DEFAULT_ORTHOGRAPHIES = REPO_ROOT / "Orthographies"
STANDARD_TARGET = "Ortho113"

_ORTHO_FLAG = re.compile(r'--orthography[ =]+"?([^"\s]+)"?')
_TABLE_FLAG = re.compile(r'--tsv_path[ =]+"?([^"\s]+)"?')
_TABLE_NAME = re.compile(r"^[A-Za-z]+_([A-Za-z0-9]+)_113\.tsv$")


# ---------------------------------------------------------------------------
# the declarations
# ---------------------------------------------------------------------------

def declared_orthography_from_script(text: str) -> tuple[str | None, str]:
    """(orthography name, how it was read) from a generate_xml.sh body.

    Reads `--orthography <path-or-name>` (basename) first, then the conversion
    table `--tsv_path …/<Lang>_<Source>_113.tsv` (the <Source> part; `94` is
    Ortho94). A value that is still a shell variable cannot be resolved here.
    """
    unresolved: list[str] = []
    # A shell variable as a path PREFIX ($FB/Orthographies/Ortho94) still has a
    # readable basename; only a variable in the basename itself ($TABLE) is opaque.
    for m in _ORTHO_FLAG.finditer(text):
        value = m.group(1)
        name = Path(value).name
        if "$" in name:
            unresolved.append(value)
            continue
        return name, f"--orthography {value}"
    for m in _TABLE_FLAG.finditer(text):
        value = m.group(1)
        if "$" in Path(value).name:
            unresolved.append(value)
            continue
        n = _TABLE_NAME.match(Path(value).name)
        if n:
            source = n.group(1)
            if source.isdigit():
                source = "Ortho" + source
            return source, f"--tsv_path {value}"
    if unresolved:
        return None, "unresolved shell variable(s): " + ", ".join(unresolved) + " — pass --declared-orthography"
    return None, "no --orthography or --tsv_path in the script — pass --declared-orthography"


def xml_files(xml_dir: Path) -> list[Path]:
    return sorted(p for p in xml_dir.rglob("*.xml") if not is_reproduction_path(p, xml_dir))


# ---------------------------------------------------------------------------
# dialect: declared (TEXT/@dialect) vs detected (dialect_detector)
# ---------------------------------------------------------------------------

def dialect_rows(files: list[Path], predict) -> Counter:
    """Count (language code, declared dialect, detected label) over files.

    `predict(root)` returns the detector's label, "unknown" when it is below
    the model's commitment threshold, or None when no verdict is possible
    (no model for the language, no standard tier).
    """
    rows: Counter = Counter()
    for path in files:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            rows[("?", "(unparseable)", "-")] += 1
            continue
        if root.tag != "TEXT":
            continue
        lang = (root.get("{http://www.w3.org/XML/1998/namespace}lang") or "").strip().lower()
        declared = (root.get("dialect") or "").strip() or "(missing)"
        detected = predict(root)
        rows[(lang, declared, detected if detected is not None else "(no verdict)")] += 1
    return rows


def format_dialect_table(rows: Counter) -> str:
    out = ["== Dialect: declared (TEXT/@dialect) vs detected (dialect_detector, standard tier) ==",
           f"{'xml:lang':<9}{'declared':<16}{'detected':<16}{'files':>6}  note"]
    mismatches = 0
    for (lang, declared, detected), n in sorted(rows.items()):
        if detected in ("(no verdict)", "-"):
            note = "no model / no standard tier"
        elif detected == "unknown":
            note = "detector below its threshold"
        elif detected == declared:
            note = "agree"
        else:
            note = "MISMATCH"
            mismatches += n
        out.append(f"{lang:<9}{declared:<16}{detected:<16}{n:>6}  {note}")
    out.append(f"dialect mismatches: {mismatches} file(s)")
    return "\n".join(out)


def _model_predictor(models_dir: Path):
    from QC.utilities.dialect_detector import model as M
    from QC.utilities.dialect_detector.data import xml_lang
    cache: dict[str, object] = {}

    def predict(root):
        name = M.language_name_for(xml_lang(root))
        if name is None:
            return None
        if name not in cache:
            path = models_dir / f"{name}.json"
            cache[name] = None
            if path.exists():
                try:
                    cache[name] = M.load_model(path)
                except (json.JSONDecodeError, KeyError, OSError):
                    cache[name] = None
        model = cache[name]
        if model is None:
            return None
        pred = M.predict_root(model, root)
        if pred.top is None:
            return None
        return "unknown" if pred.is_unknown else pred.top
    return predict


# ---------------------------------------------------------------------------
# orthography: declared (pipeline) vs detected (orthography_detector)
# ---------------------------------------------------------------------------

def orthography_rows(combined: dict, declared: str | None) -> list[dict]:
    """One row per pooled dialect group from orthography_detector's combined analysis."""
    rows = []
    for key, result in sorted(combined.items()):
        if key == "error_info" or not result.get("best_match"):
            continue
        best = result["best_match"]
        ranked = result.get("orthography_analysis") or []
        rows.append({
            "group": key,
            "files": result.get("file_count", 0),
            "declared": declared,
            "detected": best["orthography"],
            "score": best["score"],
            "unexpected_pct": best["unexpected_percentage"],
            # the detector scores every dialect column, so the same orthography can
            # appear twice; name the column when it is not the single default one
            "runners_up": [(r["orthography"] + ("" if r.get("dialect") in (None, "", "default") else f"/{r['dialect']}"), r["score"])
                           for r in ranked[1:3]],
        })
    return rows


def format_orthography_table(rows: list[dict], tier: str, expectation: str) -> str:
    out = [f"== Orthography, {tier} tier: {expectation} vs detected (orthography_detector) ==",
           f"{'group':<16}{'files':>6}  {'declared':<12}{'detected':<12}{'score':>6}{'unexpected%':>12}  note"]
    mismatches = 0
    for r in rows:
        declared = r["declared"] or "(unresolved)"
        if r["declared"] is None:
            note = "declaration unresolved"
        elif r["detected"] == r["declared"]:
            note = "agree"
        else:
            note = "MISMATCH"
            mismatches += 1
        runners = ", ".join(f"{o} {s:.2f}" for o, s in r["runners_up"])
        out.append(f"{r['group']:<16}{r['files']:>6}  {declared:<12}{r['detected']:<12}"
                   f"{r['score']:>6.2f}{r['unexpected_pct']:>12.1f}  {note}"
                   + (f"  (next: {runners})" if runners else ""))
    out.append(f"orthography mismatches ({tier}): {mismatches} group(s)")
    return "\n".join(out)


# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xml", required=True, type=Path, help="published XML directory of one corpus")
    ap.add_argument("--generate-xml", type=Path, default=None,
                    help="CodeAndDocs/generate_xml.sh to read the declared source orthography from")
    ap.add_argument("--declared-orthography", default=None,
                    help="the source orthography the pipeline declares (overrides --generate-xml)")
    ap.add_argument("--models_dir", type=Path, default=DEFAULT_MODELS)
    ap.add_argument("--orthographies", type=Path, default=DEFAULT_ORTHOGRAPHIES)
    ap.add_argument("--skip-dialect", action="store_true")
    ap.add_argument("--skip-orthography", action="store_true")
    a = ap.parse_args(argv)

    if not a.xml.is_dir():
        ap.error(f"no such XML directory: {a.xml}")
    files = xml_files(a.xml)
    print(f"{a.xml}: {len(files)} XML file(s)")

    if not a.skip_dialect:
        print()
        print(format_dialect_table(dialect_rows(files, _model_predictor(a.models_dir))))

    if not a.skip_orthography:
        from QC.utilities import orthography_detector as OD
        if a.declared_orthography:
            declared, how = a.declared_orthography, "--declared-orthography"
        elif a.generate_xml and a.generate_xml.is_file():
            declared, how = declared_orthography_from_script(a.generate_xml.read_text(encoding="utf-8"))
        elif a.generate_xml:
            declared, how = None, f"{a.generate_xml} not found — pass --declared-orthography"
        else:
            declared, how = None, "no --generate-xml / --declared-orthography given"
        print()
        print(f"declared source orthography: {declared or '(unresolved)'}  [{how}]")
        combined = OD.analyze_xml_files_combined(str(a.xml), str(a.orthographies), use_standard=False)
        print(format_orthography_table(orthography_rows(combined, declared), "original", "declared source orthography"))
        print()
        combined = OD.analyze_xml_files_combined(str(a.xml), str(a.orthographies), use_standard=True)
        print(format_orthography_table(orthography_rows(combined, STANDARD_TARGET), "standard", STANDARD_TARGET))
    return 0


if __name__ == "__main__":
    sys.exit(main())

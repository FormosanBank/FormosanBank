#!/usr/bin/env python3
"""Rebuild the canonical XML with the FormosanBank tools in the checkout you run.

POL-048: the build takes no pinned second checkout and no hash lock. It uses
whatever FormosanBank is in the surrounding tree (once ported) or the one named
by --formosanbank / $FORMOSANBANK_PATH (while this corpus still lives in its dev
repo). POL-052: the commit the published bytes were built against is recorded in
CodeAndDocs/provenance.json; a mismatch is noted on stderr and the build
proceeds.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PROVENANCE_PATH = ROOT / "CodeAndDocs" / "provenance.json"
OUTPUT_DIR = ROOT / "XML" / "Thao"
#: Both tables are registered in FormosanBank's own Orthographies/ (POL-056),
#: so the build reads them from the surrounding checkout like every other
#: corpus does. They lived under CodeAndDocs/ only while this corpus was
#: outside one; a corpus-local conversion table escapes the repo-wide symbol
#: sweep, which is exactly what POL-056 exists to prevent.
SOURCE_PROFILE_NAME = "Blust2003"
CONVERSION_TABLE_NAME = "Thao_Blust2003_113.tsv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def note_provenance(formosanbank: Path) -> None:
    """POL-052: record, never gate. Print the difference and carry on."""
    try:
        recorded = json.loads(PROVENANCE_PATH.read_text(encoding="utf-8"))[
            "formosanbank_commit"
        ]
    except (OSError, KeyError, ValueError):
        print("no provenance.json to compare against", file=sys.stderr)
        return
    try:
        current = subprocess.run(
            ["git", "-C", str(formosanbank), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        print("could not read the FormosanBank HEAD", file=sys.stderr)
        return
    if current == recorded:
        print(f"FormosanBank at the recorded commit {recorded}", file=sys.stderr)
    else:
        print(
            f"NOTE: FormosanBank is at {current}; the published XML was built "
            f"against {recorded}. Building with the current tools.",
            file=sys.stderr,
        )


def find_formosanbank(explicit: Path | None) -> Path:
    """Surrounding checkout first (POL-048), then --formosanbank/$FORMOSANBANK_PATH."""
    for parent in ROOT.parents:
        if (parent / "QC" / "utilities" / "standardize.py").is_file():
            return parent
    if explicit is not None:
        return explicit.resolve()
    env = os.environ.get("FORMOSANBANK_PATH")
    if env:
        return Path(env).resolve()
    raise SystemExit(
        "This corpus is not yet inside a FormosanBank checkout. Pass "
        "--formosanbank /path/to/FormosanBank or set $FORMOSANBANK_PATH."
    )


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, check=True)


def compare_tree(expected: Path, generated: Path) -> list[str]:
    expected_files = {
        path.relative_to(expected): path for path in expected.rglob("*.xml")
    }
    generated_files = {
        path.relative_to(generated): path for path in generated.rglob("*.xml")
    }
    differences: list[str] = []
    for relative in sorted(expected_files.keys() | generated_files.keys()):
        if relative not in expected_files:
            differences.append(f"unexpected generated file: {relative}")
        elif relative not in generated_files:
            differences.append(f"missing generated file: {relative}")
        elif expected_files[relative].read_bytes() != generated_files[relative].read_bytes():
            differences.append(f"content differs: {relative}")
    return differences


def shared_pipeline(formosanbank: Path, python: Path, temporary: Path,
                    xml_root: Path) -> None:
    """The four shared FormosanBank steps, in POL-047 order, over one tree.

    Factored out because two callers need exactly this: the canonical build,
    and test_xml.py, which builds the OTHER pipeline's full tree to check it
    without publishing it.
    """
    run(
        [
            str(python),
            str(formosanbank / "QC" / "cleaning" / "apply_manual_edits.py"),
            "--corpora_path",
            str(xml_root),
            "--manual_file",
            str(temporary / "no-manual-edits.xml"),
        ]
    )
    run(
        [
            str(python),
            str(formosanbank / "QC" / "cleaning" / "clean_xml.py"),
            "--corpora_path",
            str(xml_root),
            "--reference_dir",
            str(formosanbank / "QC" / "validation" / "reference"),
        ]
    )
    run(
        [
            str(python),
            str(formosanbank / "QC" / "utilities" / "standardize.py"),
            "--tsv_path",
            str(formosanbank / "Orthographies" / "ConversionTables"
                / CONVERSION_TABLE_NAME),
            "--corpora_path",
            str(xml_root),
            "--ortho-path",
            str(formosanbank / "Orthographies" / "Ortho113"),
        ]
    )
    run(
        [
            str(python),
            str(formosanbank / "QC" / "utilities" / "add_phonology.py"),
            "--corpora_path",
            str(xml_root),
            "--orthography",
            SOURCE_PROFILE_NAME,
        ]
    )


def canonical_build(
    formosanbank: Path,
    python: Path,
    temporary: Path,
) -> Path:
    corpus_root = temporary / "corpus"
    xml_root = corpus_root / "XML"
    output_dir = xml_root / "Thao"
    corpus_root.mkdir(parents=True, exist_ok=True)

    # One tree, two builders, in this order and no other.
    #
    # build_xml.py writes its output directory atomically - it builds into a
    # scratch directory and REPLACES the target - so it has to go first or it
    # would delete what build_entry_xml.py had just put there. It contributes
    # the five interlinear texts, which are the only part of the book it is
    # still the source for.
    #
    # build_entry_xml.py is additive, and contributes the headword entries and
    # the example sentences from the schema parse - the parse that knows which
    # entry each example belongs to.
    #
    # The four shared pipeline steps below then run ONCE over the union, which
    # is both simpler and what POL-047 asks for. Publishing the two builds side
    # by side instead would put 8,621 sentences in the corpus twice, and POL-022
    # makes a duplicate in a reference resource a HARD finding (maintainer,
    # 2026-09-11).
    run(
        [
            str(python),
            str(ROOT / "CodeAndDocs" / "build_xml.py"),
            "--output-dir",
            str(output_dir),
            "--texts-only",
        ]
    )
    run(
        [
            str(python),
            str(ROOT / "CodeAndDocs" / "build_entry_xml.py"),
            "--output-dir",
            str(output_dir),
        ]
    )
    shared_pipeline(formosanbank, python, temporary, xml_root)
    # 6. dedup (POL-022: a reference resource runs one).
    #
    # Blust lists every derived form twice - once as a numbered sub-entry under
    # its root, once as an alphabetical index entry in its own place - and both
    # are real entries with identical FORM and gloss. Only one belongs in the
    # corpus.
    #
    # Which one: the remover keeps the first by (file, S id), and an index entry
    # can be printed before or after its root, so left alone it would keep the
    # index entry about half the time. That costs nothing except in the 38 cases
    # where the root's entry carries an ETYMOLOGY the index entry does not - so
    # those losers are dropped first, by preference, and the remover then has
    # only interchangeable copies to choose between (maintainer, 2026-09-11).
    run([str(python), str(ROOT / "CodeAndDocs" / "prefer_the_etymology.py"),
         "--path", str(output_dir)])
    run([str(python),
         str(formosanbank / "QC" / "cleaning" / "remove_duplicate_sentences.py"),
         "by_path", "--path", str(output_dir), "--scope", "corpus", "--apply"])
    # 6c. What the dedup deliberately cannot touch: same FORM, DIFFERENT gloss.
    # The tool leaves those alone so homophones survive, and no rule can settle
    # them - only a reader knows whether `dadu` "leader" and `dadu` "correct"
    # are two words or one word glossed twice. They were ruled one at a time on
    # a review page; same-form-rulings.json records the verdicts.
    run([str(python), str(ROOT / "CodeAndDocs" / "apply_same_form_rulings.py"),
         "--path", str(output_dir)])
    for warning in (
        xml_root / "cleaner_warnings.csv",
        xml_root / "standardize_warnings.csv",
    ):
        if warning.exists():
            warning.unlink()
    return output_dir


def install_tree(generated: Path) -> None:
    staging = ROOT / "XML" / ".Thao-canonical-build"
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(generated, staging)
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    staging.replace(OUTPUT_DIR)
    print(f"installed canonical XML at {OUTPUT_DIR}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--formosanbank",
        type=Path,
        default=None,
        help=(
            "FormosanBank checkout to build with. Only needed while this corpus "
            "lives outside one; the surrounding checkout is used when present."
        ),
    )
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    formosanbank = find_formosanbank(args.formosanbank)
    python = args.python.resolve()
    note_provenance(formosanbank)
    with tempfile.TemporaryDirectory(prefix="thao-dictionary-build-") as directory:
        temporary = Path(directory)
        generated = canonical_build(formosanbank, python, temporary)
        if args.check:
            differences = compare_tree(OUTPUT_DIR, generated)
            if differences:
                print("reproduction check failed:", file=sys.stderr)
                for difference in differences:
                    print(f"- {difference}", file=sys.stderr)
                return 1
            print("canonical XML reproduces exactly")
            return 0
        install_tree(generated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""fix_dialects.py — populate missing TEXT/@dialect attributes in XMLs under a path.

For every .xml file under --path:
  - If the root <TEXT> already has a non-empty `dialect` attribute,
    skip the file (no change).
  - Otherwise, set `dialect` to:
      * the language name itself, for single-dialect languages (e.g.,
        xml:lang="tsu" -> dialect="Tsou"),
      * "unknown" for multi-dialect languages or for xml:lang="trv"
        (ambiguous between Truku and Seediq).
    The choice is driven by QC/validation/_dialect_inventory.py.

The script is idempotent: re-running it never touches a file that already
has a dialect set. Files are rewritten in place (matching the convention
used by standardize.py and clean_xml.py); diff before committing.

Non-XML files, parse errors, and roots that aren't <TEXT> are skipped and
reported on stderr; they do not abort the run.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from lxml import etree

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from QC.validation._dialect_inventory import default_dialect_for_lang_code

_XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

# Match the opening <TEXT ...> tag. We use lxml only to *decide* whether a
# fix is needed and to read xml:lang; the actual write is byte-level so we
# don't perturb whitespace, encoding casing, quote style, or trailing
# newlines in the rest of the file.
_TEXT_OPEN_TAG = re.compile(
    rb'<TEXT\b((?:\s+[\w:.-]+\s*=\s*(?:"[^"]*"|\'[^\']*\'))*)(\s*/?>)',
    re.DOTALL,
)


def _discover_xml(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if path.suffix == ".xml" else []
    return sorted(path.rglob("*.xml"))


def fix_file(file: Path) -> tuple[str, str | None]:
    """Mutate `file` in place if its TEXT root is missing @dialect.

    Returns (status, dialect_set):
      ("set", "<value>")   — dialect was added; value is what was written.
      ("kept", None)       — dialect already present, no change.
      ("skipped:<reason>", None) — file ignored (not TEXT root, parse error, etc.).
    """
    try:
        tree = etree.parse(str(file))
    except etree.XMLSyntaxError as e:
        return f"skipped:parse-error ({e})", None
    root = tree.getroot()
    if root.tag != "TEXT":
        return f"skipped:root-is-{root.tag}", None
    if root.get("dialect"):
        return "kept", None
    lang_code = root.get(_XML_LANG) or ""
    new_value = default_dialect_for_lang_code(lang_code)

    raw = file.read_bytes()
    match = _TEXT_OPEN_TAG.search(raw)
    if not match:
        # lxml could parse it but our regex couldn't locate the opening tag.
        # Most likely an attribute name or value shape we don't anticipate;
        # report rather than do anything risky.
        return "skipped:could-not-locate-TEXT-opening-tag", None
    attrs = match.group(1)
    close = match.group(2)
    insert = b' dialect="' + new_value.encode("utf-8") + b'"'
    new_tag = b"<TEXT" + attrs + insert + close
    file.write_bytes(raw[: match.start()] + new_tag + raw[match.end():])
    return "set", new_value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Populate missing TEXT/@dialect attributes in XMLs under a path.",
    )
    parser.add_argument(
        "--path",
        required=True,
        type=Path,
        help="File or directory to walk recursively for .xml files.",
    )
    args = parser.parse_args(argv)

    if not args.path.exists():
        print(f"Error: path does not exist: {args.path}", file=sys.stderr)
        return 1

    files = _discover_xml(args.path)
    if not files:
        print(f"No .xml files found under {args.path}", file=sys.stderr)
        return 0

    set_count = 0
    kept_count = 0
    skipped_count = 0
    set_by_value: dict[str, int] = {}
    for file in files:
        status, value = fix_file(file)
        if status == "set":
            set_count += 1
            set_by_value[value or ""] = set_by_value.get(value or "", 0) + 1
            print(f"set dialect={value!r}: {file}", file=sys.stderr)
        elif status == "kept":
            kept_count += 1
        else:
            skipped_count += 1
            print(f"{status}: {file}", file=sys.stderr)

    print(file=sys.stderr)
    print(f"Files scanned:  {len(files)}", file=sys.stderr)
    print(f"Files updated:  {set_count}", file=sys.stderr)
    print(f"Already set:    {kept_count}", file=sys.stderr)
    print(f"Skipped:        {skipped_count}", file=sys.stderr)
    if set_by_value:
        print("Updates by new dialect value:", file=sys.stderr)
        for v, n in sorted(set_by_value.items()):
            print(f"  {v}: {n}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

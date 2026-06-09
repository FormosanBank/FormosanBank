"""fix_multiple_translations.py — mark redundant TRANSL siblings with ver="alt".

Within each parent element (S, W, or M), TRANSL children are grouped by their
xml:lang. When a parent has more than one TRANSL for the same language, the
FIRST (in document order) is treated as the primary translation and left
untouched; every later same-language sibling gets a ver="alt" attribute added.

Rationale: corpora like Virginia_Fey_Dictionary routinely carry several
translations into the same language for one entry (e.g. two English glosses,
two Chinese glosses). Without ver="alt", downstream tooling can't tell the
primary translation from the alternates.

Conservative + idempotent:
  - A non-first TRANSL that ALREADY has a `ver` attribute (of any value) is
    left untouched and reported; we never clobber an existing `ver`.
  - Re-running never changes a file twice: after the first run the alternates
    carry ver="alt", so they're skipped on subsequent runs.

Like standardize.py, clean_xml.py, and fix_dialects.py, files are rewritten in
place — diff before committing. The write is byte-level (we splice ` ver="alt"`
into the specific opening tags) so whitespace, quote style, the XML
declaration, and trailing newline elsewhere in the file are left exactly as
they were.

Non-XML files and parse errors are skipped and reported on stderr; they do not
abort the run.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from lxml import etree

# Match any opening/closing S/W/M tag or any TRANSL tag (the loop distinguishes
# TRANSL opening tags from `</TRANSL>` closings via the `close` group). The attribute
# sub-pattern mirrors fix_dialects.py: name="..." or name='...', so a stray
# '>' inside an attribute value can't end the tag prematurely.
_TAG = re.compile(
    rb"<(?P<close>/?)(?P<name>S|W|M|TRANSL)\b"
    rb"(?P<attrs>(?:\s+[\w:.-]+\s*=\s*(?:\"[^\"]*\"|'[^']*'))*)"
    rb"\s*(?P<selfclose>/?)>",
    re.DOTALL,
)
_LANG = re.compile(rb"""\bxml:lang\s*=\s*(?:"([^"]*)"|'([^']*)')""")
_HAS_VER = re.compile(rb"\bver\s*=")


def _discover_xml(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if path.suffix == ".xml" else []
    return sorted(path.rglob("*.xml"))


def fix_file(file: Path) -> tuple[str, int, int]:
    """Mutate `file` in place, adding ver="alt" to redundant TRANSL siblings.

    Returns (status, added, kept_existing_ver):
      ("changed", n, k)            — n attributes added; k alternates already had a ver.
      ("unchanged", 0, k)          — nothing to add (k alternates already had a ver).
      ("skipped:<reason>", 0, 0)   — file ignored (not XML / parse error / not TEXT root).
    """
    try:
        # Parse only to confirm the file is well-formed XML before we touch
        # bytes; the actual edit is byte-level below.
        etree.parse(str(file))
    except etree.XMLSyntaxError as e:
        return f"skipped:parse-error ({e})", 0, 0

    raw = file.read_bytes()

    # Stack of grouping scopes. Each frame is a dict mapping a language key
    # (bytes, or None for a TRANSL with no xml:lang) to how many TRANSLs of
    # that language we've seen so far in the current container instance. A
    # base frame catches any TRANSL that isn't inside S/W/M.
    stack: list[dict[bytes | None, int]] = [{}]
    out = bytearray()
    pos = 0
    added = 0
    kept_existing_ver = 0

    for m in _TAG.finditer(raw):
        name = m.group("name")
        if name == b"TRANSL":
            if m.group("close"):
                continue  # `</TRANSL>` — not an element start, ignore.
            lang_m = _LANG.search(m.group("attrs"))
            lang = (lang_m.group(1) or lang_m.group(2)) if lang_m else None
            frame = stack[-1]
            frame[lang] = frame.get(lang, 0) + 1
            if frame[lang] > 1:  # not the first of this language in this parent
                if _HAS_VER.search(m.group("attrs")):
                    kept_existing_ver += 1
                else:
                    # Splice ` ver="alt"` in just before the tag's '>' (or '/>').
                    out += raw[pos:m.start()]
                    out += (
                        b"<TRANSL"
                        + m.group("attrs")
                        + b' ver="alt"'
                        + m.group("selfclose")
                        + b">"
                    )
                    pos = m.end()
                    added += 1
            continue

        # Container tag: maintain the scope stack.
        if m.group("close"):
            if len(stack) > 1:
                stack.pop()
        elif not m.group("selfclose"):
            stack.append({})

    if added == 0:
        return "unchanged", 0, kept_existing_ver

    out += raw[pos:]
    file.write_bytes(bytes(out))
    return "changed", added, kept_existing_ver


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Add ver=\"alt\" to every TRANSL that is not the first of its "
            "language within its parent (S/W/M)."
        ),
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

    changed_files = 0
    total_added = 0
    total_kept = 0
    skipped = 0
    for file in files:
        status, added, kept = fix_file(file)
        total_kept += kept
        if status == "changed":
            changed_files += 1
            total_added += added
            print(f"added {added} ver=\"alt\" (kept {kept} existing): {file}",
                  file=sys.stderr)
        elif status == "unchanged":
            if kept:
                print(f"no change (kept {kept} existing ver): {file}",
                      file=sys.stderr)
        else:
            skipped += 1
            print(f"{status}: {file}", file=sys.stderr)

    print(file=sys.stderr)
    print(f"Files scanned:            {len(files)}", file=sys.stderr)
    print(f"Files changed:            {changed_files}", file=sys.stderr)
    print(f"ver=\"alt\" added:          {total_added}", file=sys.stderr)
    print(f"Alternates already set:   {total_kept}", file=sys.stderr)
    print(f"Files skipped:            {skipped}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

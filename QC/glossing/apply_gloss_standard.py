"""Write the standard gloss tier from a conversion table + rules file.

For every W/M-level TRANSL gloss in the target XML:
  * stamps ``kindOf="original"`` where the attribute is absent (the bare
    forms are legal; stamping is the maintainer's g5 decision), and
  * adds a sibling ``TRANSL kindOf="standard"`` in the same ``xml:lang``,
    whose text is the gloss with every CONVERT atom mapped to its standard
    (honoring per-language ``language_overrides``), KEEP and UNDECIDED atoms
    copied as-is, separators and infix angle-brackets preserved.

A gloss the rules cannot segment (it contains characters the rules mark
INVESTIGATE/RESIDUE, e.g. parentheses) is copied verbatim and listed in the
residue report. Elements that already carry a standard TRANSL for that
language are left exactly as they are (preexisting hand-made standards are
never overwritten). Originals are never modified beyond the kindOf stamp
(POL-036/POL-062). S-level TRANSLs are never touched (V151).

Dry-run by default; ``--write`` modifies the XML in place. Run:

  python QC/glossing/apply_gloss_standard.py --corpus NTUFormosanCorpus [--write]
  python QC/glossing/apply_gloss_standard.py --path <XML dir> --table T.tsv --rules R.tsv [--write]
"""
from __future__ import annotations

import argparse
import collections
import csv
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

XMLLANG = "{http://www.w3.org/XML/1998/namespace}lang"
GLOSS_LANGS = {"eng", "zho"}
ISO_TO_LANGUAGE = {
    "ami": "Amis", "tay": "Atayal", "bnn": "Bunun", "xnb": "Kanakanavu",
    "ckv": "Kavalan", "pwn": "Paiwan", "pyu": "Puyuma", "dru": "Rukai",
    "sxr": "Saaroa", "xsy": "Saisiyat", "szy": "Sakizaya", "ssf": "Thao",
    "tsu": "Tsou", "tao": "Yami",
}


def language_of(root: ET.Element) -> str:
    iso = root.get(XMLLANG) or ""
    if iso == "trv":  # trv is Seediq-or-Truku; the dialect attribute decides
        return "Truku" if root.get("dialect") == "Truku" else "Seediq"
    return ISO_TO_LANGUAGE.get(iso, iso)


class Table:
    def __init__(self, path: pathlib.Path):
        self.map: dict[str, tuple[str, str, dict[str, str]]] = {}
        with open(path, newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                code = row["source_code"]
                overrides = {}
                for part in re.findall(r"(\S+?)→(\S+)", row.get("language_overrides") or ""):
                    overrides[part[0]] = part[1]
                self.map[code] = (row["status"], row.get("standard") or "", overrides)

    def standard_for(self, atom: str, language: str) -> str:
        entry = self.map.get(atom)
        if entry is None:
            return atom                      # unknown atom: copied as-is
        status, standard, overrides = entry
        if language in overrides:
            return overrides[language]
        if status == "CONVERT" and standard:
            return standard
        return atom                          # KEEP and UNDECIDED copy


class Rules:
    """Separator and residue behavior from the corpus's .rules.tsv."""

    def __init__(self, path: pathlib.Path):
        self.separators: list[str] = []
        self.keep_brackets = False
        self.residue_chars = ""
        with open(path, newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                repl = row["replacement"]
                pat = row["pattern"]
                if repl in ("KEEP-SEPARATOR", "INFIX-BREAK"):
                    self.separators.append(pat)
                elif repl == "KEEP-BRACKETS":
                    self.keep_brackets = True
                elif repl in ("INVESTIGATE", "RESIDUE") and pat not in ("…",):
                    self.residue_chars += pat.strip("[]")
        sep = "|".join(self.separators) or r"\."
        self.split_re = re.compile(f"({sep})")
        self.residue_re = re.compile(f"[{re.escape(self.residue_chars)}]") \
            if self.residue_chars else None


def convert_gloss(gloss: str, table: Table, rules: Rules, language: str):
    """Returns (standard_text, is_residue)."""
    if rules.residue_re and rules.residue_re.search(gloss):
        return gloss, True
    out = []
    for part in re.split(r"(<[^<>]+>)", gloss) if rules.keep_brackets else [gloss]:
        if part.startswith("<") and part.endswith(">") and rules.keep_brackets:
            inner = part[1:-1]
            pieces = [table.standard_for(a, language) if i % 2 == 0 and a else a
                      for i, a in enumerate(rules.split_re.split(inner))]
            out.append("<" + "".join(pieces) + ">")
        else:
            pieces = [table.standard_for(a, language) if i % 2 == 0 and a else a
                      for i, a in enumerate(rules.split_re.split(part))]
            out.append("".join(pieces))
    return "".join(out), False


def process_file(path: pathlib.Path, table: Table, rules: Rules, write: bool,
                 stats: collections.Counter, residue: collections.Counter):
    tree = ET.parse(path)
    root = tree.getroot()
    language = language_of(root)
    changed = False
    for parent in root.iter():
        if parent.tag not in ("W", "M"):
            continue
        existing_standard = {t.get(XMLLANG) for t in parent.findall("TRANSL")
                             if t.get("kindOf") == "standard"}
        for transl in list(parent.findall("TRANSL")):
            kind = transl.get("kindOf")
            lang = transl.get(XMLLANG)
            if kind == "standard" or lang not in GLOSS_LANGS \
                    or not (transl.text or "").strip():
                continue
            if kind is None:
                transl.set("kindOf", "original")   # g5 stamp
                stats["stamped"] += 1
                changed = True
            if lang in existing_standard:
                stats["preexisting_standard_kept"] += 1
                continue
            std, is_res = convert_gloss(transl.text.strip(), table, rules,
                                        language)
            if is_res:
                stats["residue"] += 1
                residue[transl.text.strip()[:60]] += 1
            elif std != transl.text.strip():
                stats["converted"] += 1
            else:
                stats["copied"] += 1
            new = ET.Element("TRANSL")
            new.set(XMLLANG, lang)
            new.set("kindOf", "standard")
            new.text = std
            new.tail = transl.tail
            idx = list(parent).index(transl)
            parent.insert(idx + 1, new)
            existing_standard.add(lang)
            changed = True
            stats["standard_added"] += 1
    if write and changed:
        tree.write(path, encoding="UTF-8", xml_declaration=True)
    return changed


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", help="corpus name under Corpora/ (uses the "
                    "repo's Glossing/ConversionTables/<corpus>[.rules].tsv)")
    ap.add_argument("--corpora_path", default="Corpora")
    ap.add_argument("--path", help="explicit XML file/dir (with --table/--rules)")
    ap.add_argument("--table")
    ap.add_argument("--rules")
    ap.add_argument("--write", action="store_true",
                    help="modify XML in place (default: dry run)")
    args = ap.parse_args()

    repo = pathlib.Path(__file__).resolve().parents[2]
    if args.corpus:
        xml_root = pathlib.Path(args.corpora_path) / args.corpus / "XML"
        table_p = repo / "Glossing" / "ConversionTables" / f"{args.corpus}.tsv"
        rules_p = repo / "Glossing" / "ConversionTables" / f"{args.corpus}.rules.tsv"
    else:
        if not (args.path and args.table and args.rules):
            ap.error("need --corpus, or --path with --table and --rules")
        xml_root, table_p, rules_p = (pathlib.Path(args.path),
                                      pathlib.Path(args.table),
                                      pathlib.Path(args.rules))
    table, rules = Table(table_p), Rules(rules_p)
    files = ([xml_root] if xml_root.is_file()
             else sorted(xml_root.rglob("*.xml")))
    stats: collections.Counter = collections.Counter()
    residue: collections.Counter = collections.Counter()
    nfiles = 0
    for f in files:
        try:
            process_file(f, table, rules, args.write, stats, residue)
            nfiles += 1
        except ET.ParseError as err:
            print(f"PARSE ERROR {f}: {err}", file=sys.stderr)
    mode = "WROTE" if args.write else "DRY RUN"
    print(f"{mode}: {nfiles} files | " +
          " ".join(f"{k}={v}" for k, v in sorted(stats.items())))
    if residue:
        print(f"residue ({sum(residue.values())} glosses copied verbatim; "
              "top 10):")
        for g, n in residue.most_common(10):
            print(f"  {g!r} ×{n}")


if __name__ == "__main__":
    main()

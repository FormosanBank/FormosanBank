#!/usr/bin/env python3
"""repair_l2_markers.py

Repair code-switch (L2) markup damage in the published XML.

The NTU source marks code-switched words with tags like
``<L2JjidenshaL2J>`` (J/M/T/... = source language of the switch). The
parsers strip well-formed tags, but the source contains ~30 malformed
spellings -- transposed closers (``<L2MpiaocunLM2>``), missing ``>``
(``<L2JjidenshaL2J``), letterless tags (``<L2siyencL2>``, where the
stripper ate the word-initial letter: published ``iyenc`` for source
``siyenc``), square-bracket variants (``[L2JmaemotteL2J]``), bare
markers, and tags inside gloss strings (TRANSL), which were never
stripped at all. The result is residue (``jidenshaL2J``), intact tags in
translations (``<L2M訂婚L2M>``), entity-escaped tags (``&lt;L2J...``),
and two words with a stolen first letter (``siyenc``, ``haiya``).

This script applies an explicit, hand-audited token map (every
contaminated token that occurs in the corpus -> its correct form,
derived from and verified against the source JSONs; see the README).
Tokens are replaced only on exact match, so clean text cannot be
affected. Gloss notation like ``2SG``/``2PL`` is untouched.

For S/W/M elements whose FORM changed, PHON (both tiers) is recomputed
through the Ortho113 mapping, gated by a pre-change witness check
(converting the old original FORM must reproduce the old original PHON
exactly). Elements failing the witness keep their PHON and are
reported.

A file is rewritten only if its unmodified tree first re-serializes
byte-identically (lxml, xml declaration, UTF-8). Idempotent: applied
replacements stop matching.

Usage
-----
    python repair_l2_markers.py            # corpus XML/ by default
    python repair_l2_markers.py --dry-run
"""

import argparse
import collections
import os
import sys
from pathlib import Path

import lxml.etree as etree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _phon_regen import language_of, load_mappings, convert  # noqa: E402

TOKEN_MAP = {
    # 2026-06-12 additions: residue surfaced by the V067 infix-notation sweep
    # (convert_infix_notation.py skip list). Three families, all verified
    # against the source JSONs: (a) bracket-closed L2 variants the stripper
    # half-ate (source <L2J>ciuru<L2J> -> published '>ciuru>'; <L2M>嗯<L2M>;
    # <L2JgonenseL2J> -> '<gonense>'; CJK-letter 日..日 Japanese marker);
    # (b) prosody span markers split across words (source <HIGH.PITCH ...
    # HIGH.PITCH> / <LOW.VOLUME ... LOW.VOLUME>, dots eaten by punctuation
    # cleaning); (c) stray span-closer remnants (source ‘nay==(0.6)A>X>,_).
    'jyurokusai>': 'jyurokusai',
    '<gonense>': 'gonense',
    '<gonense>=ku': 'gonense=ku',
    '<Mpi-jiaoM>': 'pi-jiao',
    '<Mpi': 'pi',
    'jiaoM>': 'jiao',
    '<LMJnazua': 'nazua',
    'shiaolingLM>': 'shiaoling',
    '<JgekiJ>': 'geki',
    '<日wa日>': 'wa',
    '<JapwaJap>': 'wa',
    '>嗯>': '嗯',
    '>ciuru>': 'ciuru',
    "'nayA>": "'nay",
    '<HIGHPITCHtayta-an-na': 'tayta-an-na',
    '<HIGHPITCHtayta': 'tayta',
    'naniHIGHPITCH>': 'nani',
    '<LOWVOLUMEqalimek-ka': 'qalimek-ka',
    '<LOWVOLUMEqalimek': 'qalimek',
    's<m>uniLOWVOLUME>': 's<m>uni',
    's-uniLOWVOLUME>': 's-uni',
    # S-tier spellings of the same residue (the ori rows lack the brackets
    # and boundary dashes of the gloss rows):
    'MpijiaoM': 'pijiao',
    'JgekiJ': 'geki',
    'LMJnazua': 'nazua',
    'HIGHPITCHtaytaanna': 'taytaanna',
    'naniHIGHPITCH': 'nani',
    'LOWVOLUMEqalimekka': 'qalimekka',
    'smuniLOWVOLUME': 'smuni',
    "'nayA.": "'nay.",
    '日wa日': 'wa',

    # 2026-06-11 additions: escapees of the original contamination census,
    # whose patterns lack an 'L2' substring (trailing 'LM2', L3 third-language
    # tags, T2 openers). The census regex was widened accordingly.
    '<L3JsiukaiL3J>': 'siukai',
    'L3JsiukaiL3J': 'siukai',
    'piaocunLM2': 'piaocun',
    'piaocunLM2>': 'piaocun',
    'T2mijio.': 'mijio.',
    '<T2mi-jio': 'mi-jio',
    '<T2mi': 'mi',

    '&lt;L2JchurchL2J&gt;': 'church',
    '&lt;L2JclockL2J&gt;': 'clock',
    '&lt;L2JphotoL2J&gt;': 'photo',
    '&lt;L2JtribeL2J&gt;': 'tribe',
    '&lt;L2JtribeL2J&gt;=MED.OBL': 'tribe=MED.OBL',
    '&lt;L2J部落L2J&gt;': '部落',
    '&lt;L2J部落L2J&gt;=中距.斜格': '部落=中距.斜格',
    "'untoML2.": "'unto.",
    "'untoML2>": "'unto",
    "<L2'uang'uang": "'uang'uang",
    '<L2BtuL2B>': 'tu',
    '<L2J>luckily<L2J>': 'luckily',
    '<L2J>剛好<L2J>': '剛好',
    '<L2JchurchL2J>': 'church',
    '<L2JclockL2J>': 'clock',
    '<L2JhetoL2J>': 'heto',
    '<L2JphotoL2J>': 'photo',
    '<L2JshoesL2J>': 'shoes',
    '<L2JshoesL2J>=NOM': 'shoes=NOM',
    '<L2JteenageL2J>': 'teenage',
    '<L2JtimeL2J>': 'time',
    '<L2JtribeL2J>': 'tribe',
    '<L2JtribeL2J>=MED.OBL': 'tribe=MED.OBL',
    '<L2J十幾歲L2J>': '十幾歲',
    '<L2J時間L2J>': '時間',
    '<L2J部落L2J>': '部落',
    '<L2J部落L2J>=中距.斜格': '部落=中距.斜格',
    '<L2J靴子L2J>': '靴子',
    '<L2J靴子L2J>=主格': '靴子=主格',
    '<L2J鞋子L2J>': '鞋子',
    '<L2M': '',
    '<L2M>FIL<L2M>': 'FIL',
    '<L2M>tomorrow<L2M>': 'tomorrow',
    '<L2M>明天<L2M>': '明天',
    '<L2MAnpingL2M>': 'Anping',
    '<L2McisanL2M>': 'cisan',
    '<L2MdinghunL2M>': 'dinghun',
    '<L2MhaoL2M>': 'hao',
    '<L2MleaderL2M>': 'leader',
    '<L2MmeinonL2M>': 'meinon',
    '<L2MnansiL2M>': 'nansi',
    '<L2MohL2M>': 'oh',
    '<L2MsoL2M>': 'so',
    '<L2MsyesyeL2M>.': 'syesye.',
    '<L2MtainanL2M>': 'tainan',
    '<L2MwoofL2M>': 'woof',
    '<L2MwoofwoofL2M>': 'woofwoof',
    '<L2M喔L2M>': '喔',
    '<L2M所以L2M>': '所以',
    '<L2M汪L2M>': '汪',
    '<L2M汪汪L2M>': '汪汪',
    '<L2M訂婚L2M>': '訂婚',
    '<L2M頭目L2M>': '頭目',
    '<L2RhlacʉnaL2R>': 'hlacʉna',
    '<L2RhlcʉnaL2R>': 'hlcʉna',
    '<L2woofwoofL2M>': 'woofwoof',
    '<L2汪汪L2M>': '汪汪',
    '<M2JtokuvecuM2J>': 'tokuvecu',
    '<l2Mzhangjie': 'zhangjie',
    'JiaML2>': 'Jia',
    'L2': '',
    "L2'uang'uang": "'uang'uang",
    "L2'uang'uang.": "'uang'uang.",
    'L2JmaemotteL2J': 'maemotte',
    'L2JmaemotteL2J=ta': 'maemotte=ta',
    'L2JmaemotteL2Jta': 'maemotteta',
    'L2M-L2M': '',
    'L2M<jiuhaole>L2M': 'jiuhaole',
    'L2M>': '',
    'L2MjiuhaoleL2M.': 'jiuhaole.',
    'Lao-JiaML2>': 'Lao-Jia',
    'LaoJiaML2': 'LaoJia',
    'M2JtokuvecuM2J': 'tokuvecu',
    'aML2>': 'a',
    'abinL2>': 'abin',
    'aiyaL2': 'haiya',
    'aiyaL2>': 'haiya',
    'bijiaoML2': 'bijiao',
    'bijiaoML2>': 'bijiao',
    'ciuduL2JL': 'ciudu',
    'erhaoML2>': 'erhao',
    'erhaoML2>=pa=iku': 'erhao=pa=iku',
    'erhaoML2paiku': 'erhaopaiku',
    'hitayL2': 'hitay',
    'hitayL2>': 'hitay',
    'hoN2T.': 'hoN.',
    'hoN2T>': 'hoN',
    'honL2M': 'hon',
    'iyencL2': 'siyenc',
    'iyencL2>': 'siyenc',
    'jidenshaL2J': 'jidensha',
    'keyimaML2>?': 'keyima?',
    'keyimaML2?': 'keyima?',
    'kulacingTL2': 'kulacing',
    'kulacingTL2>': 'kulacing',
    'l2Mzhangjie': 'zhangjie',
    'sanjiL2': 'sanji',
    'sanjiL2>': 'sanji',
    'shenfuL2': 'shenfu',
    'shenfuL2>': 'shenfu',
    'shiML2>': 'shi',
    'sonoaidaniL2LJ': 'sonoaidani',
    'sonoaidaniL2LJ>': 'sonoaidani',
    'suoyiML2': 'suoyi',
    'suoyiML2>': 'suoyi',
    'tapanML2.': 'tapan.',
    'tapanML2>': 'tapan',
    'ti-abinL2>': 'ti-abin',
    'tiabinL2': 'tiabin',
    'tianL2>': 'tian',
    'toushiL2M': 'toushi',
    'toushiL2M.': 'toushi.',
    'xinlangL2M': 'xinlang',
    'yuan-lai-shiML2>': 'yuan-lai-shi',
    'yuanlaishiML2': 'yuanlaishi',
    'zhe-liang-tianL2>': 'zhe-liang-tian',
    'zheliangtianL2': 'zheliangtian',
    'zo-lu-shang-lai-aML2>': 'zo-lu-shang-lai-a',
    'zolushanglaiaML2.': 'zolushanglaia.',
}


def fix_text(text):
    if not text:
        return text, 0
    out = []
    n = 0
    for tok in text.split(" "):
        if tok in TOKEN_MAP:
            rep = TOKEN_MAP[tok]
            n += 1
            if rep:
                out.append(rep)
            # deleted tokens are simply dropped
        else:
            out.append(tok)
    return " ".join(out), n


def serialize(tree):
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8")


def _tier(el, tag, kind):
    for c in el.findall(tag):
        if c.get("kindOf") == kind:
            return c
    return None


def process_file(path, dry_run, stats):
    original_bytes = open(path, "rb").read()
    tree = etree.parse(path)
    if serialize(tree) != original_bytes:
        stats["file skipped: round-trip guard"] += 1
        return False
    root = tree.getroot()
    mp = load_mappings(language_of(root))
    modified = False
    for el in root.iter():
        if el.tag not in ("S", "W", "M"):
            continue
        # TRANSL fixes (no PHON impact). A gloss that was only a marker
        # becomes a properly empty TRANSL (text=None), matching the
        # corpus's existing empty-gloss convention.
        for tr in el.findall("TRANSL"):
            new, n = fix_text(tr.text)
            if n:
                tr.text = new if new.strip() else None
                if not new.strip():
                    stats["TRANSL emptied (marker-only gloss)"] += 1
                stats["TRANSL tokens fixed"] += n
                modified = True
        # FORM fixes with witness-gated PHON regen
        forms = {k: _tier(el, "FORM", k) for k in ("original", "standard")}
        if any(f is not None and f.text and any(t in TOKEN_MAP
               for t in f.text.split(" ")) for f in forms.values()):
            of, op = forms["original"], _tier(el, "PHON", "original")
            witness = (mp is not None and of is not None and op is not None
                       and (of.text or "").strip() and (op.text or "").strip()
                       and convert(of.text, mp) == op.text)
            for kind, f in forms.items():
                if f is None or not f.text:
                    continue
                new, n = fix_text(f.text)
                if n:
                    if not new.strip():
                        # never empty a FORM (would recreate the
                        # empty-form-M class); leave for manual repair
                        stats["FORM left as-is (would empty)"] += 1
                        continue
                    f.text = new
                    stats[f"FORM tokens fixed ({el.tag})"] += n
                    modified = True
            if witness:
                for kind in ("original", "standard"):
                    f, p = _tier(el, "FORM", kind), _tier(el, "PHON", kind)
                    if f is not None and p is not None and (f.text or "").strip():
                        newp = convert(f.text, mp)
                        if newp != p.text:
                            p.text = newp
                            stats["PHON regenerated"] += 1
            else:
                stats["PHON left (witness failed/absent)"] += 1
    if modified and not dry_run:
        with open(path, "wb") as fh:
            fh.write(serialize(tree))
    return modified


def main():
    corpus = Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xml_dir", default=str(corpus / "XML"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    stats = collections.Counter()
    files = 0
    for dirpath, _, filenames in os.walk(args.xml_dir):
        for fn in sorted(filenames):
            if not fn.endswith(".xml"):
                continue
            if process_file(os.path.join(dirpath, fn), args.dry_run, stats):
                files += 1
                print(f"  modified: {fn}")
    print(f"\nfiles {'that would be ' if args.dry_run else ''}modified: {files}")
    for k, v in stats.most_common():
        print(f"  {v:5d}  {k}")


if __name__ == "__main__":
    main()

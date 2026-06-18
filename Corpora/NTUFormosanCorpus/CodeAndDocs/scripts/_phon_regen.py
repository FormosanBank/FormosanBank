"""Shared helper: regenerate standard-tier PHON after standard-FORM edits.

Used by remove_null_symbols.py and remove_stress_accents.py.

Mechanism: the *original* tier is the witness. If converting the
element's original FORM through the Ortho113 mapping reproduces its
original PHON exactly, the mapping provably generated this file's PHON,
and the standard PHON can safely be recomputed from the (edited)
standard FORM. Elements failing the witness check are left alone and
counted, never guessed.

If an element has no PHON children (e.g. when running before
add_phonology.py during a regeneration), there is nothing to do.
"""

import csv
import string
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from QC.utilities.add_phonology import apply_phonology_mappings  # noqa: E402
from QC.validation._dialect_inventory import is_multi_dialect_language  # noqa: E402

LANG_MAP = {
    'ami': 'Amis', 'tay': 'Atayal', 'bnn': 'Bunun', 'ckv': 'Kavalan',
    'pwn': 'Paiwan', 'pyu': 'Puyuma', 'dru': 'Rukai', 'sxr': 'Saaroa',
    'xsy': 'Saisiyat', 'szy': 'Sakizaya', 'trv': 'Seediq', 'ssf': 'Thao',
    'tsu': 'Tsou', 'tao': 'Yami', 'xnb': 'Kanakanavu',
}

_XLANG = "{http://www.w3.org/XML/1998/namespace}lang"
_cache = {}


def language_of(root):
    text_el = root if root.tag == "TEXT" else root.find(".//TEXT")
    if text_el is None:
        return None
    code = (text_el.get(_XLANG) or text_el.get("xml:lang") or "").strip()
    return LANG_MAP.get(code, code) or None


def load_mappings(language):
    if language in _cache:
        return _cache[language]
    tsv = _REPO_ROOT / "Orthographies" / "Ortho113" / f"{language}.tsv"
    result = None
    if tsv.exists():
        with open(tsv, encoding="utf-8") as f:
            rows = list(csv.DictReader(f, delimiter="\t"))
        cols = [c for c in (rows[0].keys() if rows else []) if c != "letter"]
        if cols:
            column = cols[0] if not is_multi_dialect_language(language) else (
                "default" if "default" in cols else cols[0])
            mappings = [(r["letter"], r[column]) for r in rows
                        if r.get("letter") and r.get(column) is not None]
            # add_phonology.py's unknown-character handling: any character
            # not found in the mapping's IPA output alphabet (nor ASCII
            # punctuation / whitespace) is rendered as '*'.
            ipa_chars = set("".join(v for _, v in mappings))
            result = (mappings, dict(mappings), ipa_chars)
    _cache[language] = result
    return result


def convert(text, mp):
    mappings, cdict, ipa_chars = mp
    out = apply_phonology_mappings(text, mappings, cdict)
    return "".join(
        ch if (ch in ipa_chars or ch in string.punctuation or ch.isspace())
        else "*"
        for ch in out)


def _tier(el, tag, kind):
    for c in el.findall(tag):
        if c.get("kindOf") == kind:
            return c
    return None


def regen_standard_phon(el, mp, stats):
    """Recompute el's standard PHON from its standard FORM, if the
    original tier witnesses the mapping. Returns True if PHON changed."""
    if mp is None:
        stats["phon: no orthography TSV"] += 1
        return False
    of = _tier(el, "FORM", "original")
    op = _tier(el, "PHON", "original")
    sf = _tier(el, "FORM", "standard")
    sp = _tier(el, "PHON", "standard")
    if sp is None or sf is None or not (sf.text or "").strip():
        return False  # nothing to regenerate
    if of is None or op is None or not (of.text or "").strip() \
            or not (op.text or "").strip():
        stats["phon: no original-tier witness"] += 1
        return False
    if convert(of.text, mp) != op.text:
        stats["phon: witness check failed"] += 1
        return False
    new = convert(sf.text, mp)
    if new != sp.text:
        sp.text = new
        stats["phon: regenerated"] += 1
        return True
    return False

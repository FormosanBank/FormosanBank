"""Shared helper: regenerate standard-tier PHON after standard-FORM edits.

Used by remove_annotation_codes.py, apply_manual_corrections.py and
repair_l2_markers.py (and the retired remove_stress_accents.py /
remove_null_symbols.py).

Mechanism: the *original* tier is the witness. If converting the
element's original FORM through the Ortho113 profile reproduces its
original PHON exactly, the mapping provably generated this file's PHON,
and the standard PHON can safely be recomputed from the (edited)
standard FORM. Elements failing the witness check are left alone and
counted, never guessed.

Since 2026-08-10 the conversion IS add_phonology's own ``phonologize``
(same profile loading, contextual rules, dialect column selection and
marker/punctuation policy), so the witness passes on any file whose
PHON the current pipeline generated. Files carrying an older PHON
vintage (e.g. the pre-2026-08 style that kept '='/'-'/'<>' and rendered
nulls as '*') fail the witness and are conservatively skipped —
make.sh's final add_phonology refresh canonicalizes those instead.

If an element has no PHON children (e.g. when running before
add_phonology.py during a regeneration), there is nothing to do.
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from QC.utilities.add_phonology import load_profile, phonologize  # noqa: E402

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


def dialect_of(root):
    text_el = root if root.tag == "TEXT" else root.find(".//TEXT")
    return (text_el.get("dialect") or "") if text_el is not None else ""


def load_mappings(language, dialect=None):
    """Ortho113 PhonologyProfile for language/dialect (None if no table)."""
    key = (language, dialect or "")
    if key not in _cache:
        _cache[key] = (load_profile("Ortho113", language, dialect or "")
                       if language else None)
    return _cache[key]


def convert(text, mp):
    return phonologize(text, mp)


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

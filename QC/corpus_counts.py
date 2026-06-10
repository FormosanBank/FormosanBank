"""Single source of truth for FormosanBank corpus counting rules.

Both statistics pipelines import from here:
  - QC/utilities/get_corpus_stats.py (per-corpus CSVs for the Gitbook)
  - QC/corpus_metrics.py and QC/count_tokens.py (size tracker + PR deltas)

Rules (decided 2026-06-10):
  - A token is a whitespace-separated chunk containing at least one
    Unicode letter or digit. "123" counts; "?" does not.
  - Per sentence, count the `standard` FORM if non-empty, else the
    `original` FORM, else 0. Word counts come from the S tier only —
    W and M FORMs are never counted as tokens.
  - Language identity comes from xml:lang + dialect attributes only:
    trv + dialect "Truku" is Truku; trv + anything else is Seediq.
"""
from __future__ import annotations

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

LANG_CODE_TO_NAME = {
    "ami": "Amis",
    "tay": "Atayal",
    "pwn": "Paiwan",
    "bnn": "Bunun",
    "pyu": "Puyuma",
    "dru": "Rukai",
    "tsu": "Tsou",
    "xsy": "Saisiyat",
    "tao": "Yami",
    "ssf": "Thao",
    "ckv": "Kavalan",
    "trv": "Seediq",
    "szy": "Sakizaya",
    "sxr": "Saaroa",
    "xnb": "Kanakanavu",
    "fos": "Siraya",
}

# All display names a record can resolve to (the 16 codes plus Truku,
# which is distinguished from Seediq by dialect rather than ISO code).
LANGUAGE_NAMES = sorted(set(LANG_CODE_TO_NAME.values()) | {"Truku"})

ENG_CODES = {"eng", "en"}
ZHO_CODES = {"zho", "zh", "zh-hant", "zh-hans"}


def count_words(text: str | None) -> int:
    """Count whitespace-separated chunks containing >=1 letter or digit."""
    if not text:
        return 0
    return sum(1 for chunk in text.split() if any(c.isalnum() for c in chunk))


def select_sentence_form(sentence) -> str | None:
    """Return the text to count for one <S>: standard tier, else original.

    Only direct FORM children of S are considered (S-tier rule)."""
    for kind in ("standard", "original"):
        for form in sentence.findall("FORM"):
            if form.get("kindOf") == kind and form.text and form.text.strip():
                return form.text
    return None


def resolve_language(language_code: str | None, dialect: str | None) -> str | None:
    """Resolve (xml:lang, dialect) to a display language name.

    trv + dialect 'Truku' is Truku; trv + anything else is Seediq.
    Returns None for unknown or missing codes (caller decides how to
    label those)."""
    code = (language_code or "").strip().lower()
    if not code:
        return None
    if code == "trv" and (dialect or "").strip().lower() == "truku":
        return "Truku"
    return LANG_CODE_TO_NAME.get(code)

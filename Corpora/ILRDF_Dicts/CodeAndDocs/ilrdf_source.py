"""Source-backed ILRDF dictionary sentence extraction.

The committed snapshots are the reproducibility boundary.  This module does
not contact the live site and does not infer or rewrite source content beyond
the documented question-mark recovery and outer-whitespace removal.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import gzip
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlparse


XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
SOURCE_NAME = "Indigenous Languages Research and Development Foundation Dictionaries"
SOURCE_URL = "https://e-dictionary.ilrdf.org.tw/"
RIGHTS_STATEMENT = "Copyrighted; permission required outside applicable fair use"
PLACEHOLDERS = {"", "-", "---"}
RECOVERABLE_QUESTION_LANGUAGES = {"Kanakanavu", "Saaroa", "Tsou"}
FORM_QUOTE_TRANSLATION = str.maketrans(
    {
        "‘": "'",
        "’": "'",
        "“": '"',
        "”": '"',
        "「": '"',
        "」": '"',
        "『": '"',
        "』": '"',
        "《": '"',
        "》": '"',
    }
)


@dataclass(frozen=True)
class LanguageInfo:
    iso: str
    chinese_name: str


LANGUAGES: dict[str, LanguageInfo] = {
    "Amis": LanguageInfo("ami", "阿美語"),
    "Atayal": LanguageInfo("tay", "泰雅語"),
    "Bunun": LanguageInfo("bnn", "布農語"),
    "Kanakanavu": LanguageInfo("xnb", "卡那卡那富語"),
    "Kavalan": LanguageInfo("ckv", "噶瑪蘭語"),
    "Paiwan": LanguageInfo("pwn", "排灣語"),
    "Puyuma": LanguageInfo("pyu", "卑南語"),
    "Rukai": LanguageInfo("dru", "魯凱語"),
    "Saaroa": LanguageInfo("sxr", "拉阿魯哇語"),
    "Saisiyat": LanguageInfo("xsy", "賽夏語"),
    "Sakizaya": LanguageInfo("szy", "撒奇萊雅語"),
    "Seediq": LanguageInfo("trv", "賽德克語"),
    "Thao": LanguageInfo("ssf", "邵語"),
    "Truku": LanguageInfo("trv", "太魯閣語"),
    "Tsou": LanguageInfo("tsu", "鄒語"),
    "Yami": LanguageInfo("tao", "雅美語"),
}


@dataclass
class Sentence:
    original: str
    translations: list[tuple[str, str]] = field(default_factory=list)
    audio_urls: list[str] = field(default_factory=list)
    source_ids: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class ExtractionStats:
    query_count: int
    published_word_occurrences: int
    sentence_occurrences: int
    unique_sentences: int
    skipped_source: int
    skipped_translation: int
    excluded_translation: int
    question_repairs: int
    excluded_audio: int


def normalize_source_text(value: object) -> str:
    """Preserve source spelling while making Unicode and layout space stable."""
    if not isinstance(value, str):
        return ""
    text = unicodedata.normalize("NFC", value).replace("\u200b", "")
    return re.sub(r"[ \t]+(?=\r?\n)", "", text).strip()


def normalize_source_form(value: object) -> str:
    """Apply current FormosanBank FORM punctuation and spacing conventions."""
    text = normalize_source_text(value).translate(FORM_QUOTE_TRANSLATION)
    return re.sub(r"\s+", " ", text)


def sentence_id(language: str, original: str) -> str:
    digest = hashlib.sha256(original.encode("utf-8")).hexdigest()[:16]
    return f"{language}_{digest}"


def is_published(word: dict[str, object]) -> bool:
    frequency = word.get("frequency", 0)
    return (isinstance(frequency, (int, float)) and frequency > 0) or bool(
        word.get("sources")
    )


def _is_formosan_letter(char: str) -> bool:
    return char.isalpha() and ord(char) < 0x2E00


def _add_clean_words(text: str, vocabulary: Counter[str]) -> None:
    for raw in text.split():
        token = re.sub(r"^[^\w]+", "", raw)
        token = re.sub(r"[^\w]+$", "", token)
        if (
            token
            and "?" not in token
            and any(_is_formosan_letter(char) for char in token)
            and not any(ord(char) >= 0x2E00 for char in token)
        ):
            vocabulary[token.lower()] += 1


def build_recovery_vocabulary(snapshot: dict[str, object]) -> Counter[str]:
    vocabulary: Counter[str] = Counter()
    for response in snapshot.get("responses", []):
        if not isinstance(response, dict):
            continue
        for word in response.get("words", []):
            if not isinstance(word, dict):
                continue
            for explanation in word.get("explanationItems") or []:
                if not isinstance(explanation, dict):
                    continue
                for item in explanation.get("sentenceItems") or []:
                    if isinstance(item, dict):
                        text = normalize_source_form(item.get("originalSentence"))
                        if text:
                            _add_clean_words(text, vocabulary)
    return vocabulary


def _has_internal_question(token: str) -> bool:
    return any(
        0 < index < len(token) - 1
        and _is_formosan_letter(token[index - 1])
        and _is_formosan_letter(token[index + 1])
        for index, char in enumerate(token)
        if char == "?"
    )


def _question_candidates(core: str, replacement: str) -> list[str]:
    base = core.replace("?", replacement)
    candidates = [base]
    while base.endswith(replacement):
        base = base[:-1]
        candidates.append(base)
    return list(dict.fromkeys(candidate for candidate in candidates if candidate))


def repair_question_token(token: str, vocabulary: Counter[str]) -> tuple[str, bool]:
    """Recover a destroyed vowel only when an intact corpus token attests it."""
    if not _has_internal_question(token):
        return token, False
    match = re.match(r"^([^\w?]*)([\w?].*?[\w?]|[\w?])([^\w?]*)$", token, re.S)
    if match is None:
        return token, False
    lead, core, trail = match.groups()
    best: tuple[str, int, str] | None = None
    for replacement in ("ʉ", "ɨ"):
        for candidate in _question_candidates(core, replacement):
            count = vocabulary.get(candidate.lower(), 0)
            if count and (best is None or count > best[1]):
                best = (candidate, count, replacement)
    if best is None:
        return token, False
    recovered, _, replacement = best
    substituted = core.replace("?", replacement)
    trailing_questions = len(substituted) - len(recovered)
    return lead + recovered + "?" * trailing_questions + trail, True


def repair_source_questions(text: str, vocabulary: Counter[str]) -> tuple[str, int]:
    parts = re.split(r"(\s+)", text)
    repaired = 0
    for index, part in enumerate(parts):
        if not part or part.isspace():
            continue
        parts[index], changed = repair_question_token(part, vocabulary)
        repaired += int(changed)
    return "".join(parts), repaired


def storage_id(audio_url: str) -> str | None:
    parts = [part for part in urlparse(audio_url).path.split("/") if part]
    if len(parts) >= 2 and parts[-1].lower() == "download":
        return parts[-2].lower()
    return None


def load_audio_exclusions(path: Path) -> set[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    result = {
        str(value).lower()
        for value in payload["all_zero_source_files"]["storage_ids"]
    }
    result.update(
        str(item["storage_id"]).lower()
        for item in payload["confirmed_transcript_mismatches"]
    )
    result.update(
        str(value).lower()
        for value in payload["cross_language_sentence_collisions"]["storage_ids"]
    )
    return result


def load_translation_overrides(path: Path) -> dict[tuple[str, str, str], str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    overrides: dict[tuple[str, str, str], str] = {}
    for item in payload["overrides"]:
        key = (
            item["language"],
            normalize_source_form(item["form"]),
            normalize_source_text(item["translation"]),
        )
        if key in overrides:
            raise ValueError(f"duplicate translation-language override: {key!r}")
        overrides[key] = item["xml_lang"]
    return overrides


def load_translation_exclusions(path: Path) -> set[tuple[str, str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    exclusions: set[tuple[str, str, str]] = set()
    for item in payload["translation_exclusions"]:
        key = (
            item["language"],
            normalize_source_form(item["form"]),
            normalize_source_text(item["translation"]),
        )
        if key in exclusions:
            raise ValueError(f"duplicate translation exclusion: {key!r}")
        exclusions.add(key)
    return exclusions


def verify_and_load_snapshot(
    language: str, snapshot_dir: Path, manifest: dict[str, object]
) -> dict[str, object]:
    entries = {
        item["language"]: item
        for item in manifest.get("languages", [])
        if isinstance(item, dict) and "language" in item
    }
    if language not in entries:
        raise ValueError(f"{language}: absent from source manifest")
    entry = entries[language]
    path = snapshot_dir.parent / str(entry["file"])
    compressed = path.read_bytes()
    actual_compressed = hashlib.sha256(compressed).hexdigest()
    if actual_compressed != entry["sha256"]:
        raise ValueError(f"{language}: compressed snapshot hash mismatch")
    raw = gzip.decompress(compressed)
    actual_raw = hashlib.sha256(raw).hexdigest()
    if actual_raw != entry["uncompressed_sha256"]:
        raise ValueError(f"{language}: uncompressed snapshot hash mismatch")
    payload = json.loads(raw)
    if payload.get("language") != language:
        raise ValueError(f"{language}: snapshot language mismatch")
    return payload


def _translation_language(
    language: str,
    original: str,
    translation: str,
    overrides: dict[tuple[str, str, str], str],
    used_overrides: set[tuple[str, str, str]],
) -> str:
    key = (language, original, translation)
    if key in overrides:
        used_overrides.add(key)
        return overrides[key]
    if normalize_source_form(translation) == original:
        return LANGUAGES[language].iso
    return "zho"


def extract_sentences(
    language: str,
    snapshot: dict[str, object],
    excluded_audio_ids: set[str],
    translation_overrides: dict[tuple[str, str, str], str],
    used_overrides: set[tuple[str, str, str]],
    translation_exclusions: set[tuple[str, str, str]] | None = None,
    used_exclusions: set[tuple[str, str, str]] | None = None,
) -> tuple[list[Sentence], ExtractionStats]:
    vocabulary = (
        build_recovery_vocabulary(snapshot)
        if language in RECOVERABLE_QUESTION_LANGUAGES
        else Counter()
    )
    grouped: dict[str, Sentence] = {}
    published_words = sentence_occurrences = skipped_source = 0
    skipped_translation = excluded_translation = question_repairs = excluded_audio = 0
    translation_exclusions = translation_exclusions or set()
    used_exclusions = used_exclusions if used_exclusions is not None else set()

    responses = snapshot.get("responses", [])
    if not isinstance(responses, list):
        raise ValueError(f"{language}: responses is not a list")
    for response in responses:
        if not isinstance(response, dict) or not isinstance(response.get("words"), list):
            raise ValueError(f"{language}: malformed response record")
        for word in response["words"]:
            if not isinstance(word, dict) or not is_published(word):
                continue
            published_words += 1
            for explanation in word.get("explanationItems") or []:
                if not isinstance(explanation, dict):
                    continue
                for item in explanation.get("sentenceItems") or []:
                    if not isinstance(item, dict):
                        continue
                    sentence_occurrences += 1
                    original = normalize_source_form(item.get("originalSentence"))
                    translation = normalize_source_text(item.get("chineseSentence"))
                    if original in PLACEHOLDERS or not any(
                        char.isalnum() for char in original
                    ):
                        skipped_source += 1
                        continue
                    if translation in PLACEHOLDERS:
                        skipped_translation += 1
                        continue
                    if vocabulary:
                        original, repairs = repair_source_questions(original, vocabulary)
                        question_repairs += repairs
                    record = grouped.setdefault(original, Sentence(original=original))
                    source_id = item.get("id")
                    if source_id:
                        record.source_ids.add(str(source_id))
                    translation_key = (language, original, translation)
                    if translation_key in translation_exclusions:
                        used_exclusions.add(translation_key)
                        excluded_translation += 1
                    else:
                        lang_code = _translation_language(
                            language,
                            original,
                            translation,
                            translation_overrides,
                            used_overrides,
                        )
                        translation_record = (lang_code, translation)
                        if translation_record not in record.translations:
                            record.translations.append(translation_record)
                    for audio in item.get("audioItems") or []:
                        if not isinstance(audio, dict):
                            continue
                        url = normalize_source_text(audio.get("audioUrl"))
                        if not url:
                            continue
                        token = storage_id(url)
                        if token and token in excluded_audio_ids:
                            excluded_audio += 1
                            continue
                        if url not in record.audio_urls:
                            record.audio_urls.append(url)

    sentences = sorted(grouped.values(), key=lambda item: (item.original.casefold(), item.original))
    ids: dict[str, str] = {}
    for sentence in sentences:
        current_id = sentence_id(language, sentence.original)
        if current_id in ids and ids[current_id] != sentence.original:
            raise ValueError(f"{language}: stable ID collision for {current_id}")
        ids[current_id] = sentence.original
    stats = ExtractionStats(
        query_count=len(responses),
        published_word_occurrences=published_words,
        sentence_occurrences=sentence_occurrences,
        unique_sentences=len(sentences),
        skipped_source=skipped_source,
        skipped_translation=skipped_translation,
        excluded_translation=excluded_translation,
        question_repairs=question_repairs,
        excluded_audio=excluded_audio,
    )
    return sentences, stats


def root_attributes(language: str, snapshot_date: str) -> dict[str, str]:
    info = LANGUAGES[language]
    citation = (
        "Council of Indigenous Peoples, & Indigenous Languages Research and "
        f"Development Foundation. (n.d.). 原住民族語言線上辭典: {info.chinese_name} "
        f"[Indigenous Languages Online Dictionary: {language} language]. "
        f"Retrieved {snapshot_date}, from {SOURCE_URL}"
    )
    bibtex = (
        f"@misc{{ILRDF_{language}, author = {{{{Council of Indigenous Peoples}} and "
        "{{Indigenous Languages Research and Development Foundation}}}, "
        f"title = {{原住民族語言線上辭典: {info.chinese_name} "
        f"[Indigenous Languages Online Dictionary: {language} language]}}, "
        f"note = {{Retrieved {snapshot_date}}}, url = {{{SOURCE_URL}}}}}"
    )
    return {
        "id": f"ILRDF_Dicts_{language}",
        XML_LANG: info.iso,
        "source": SOURCE_NAME,
        "audio": "segmented",
        "dialect": "unknown",
        "copyright": RIGHTS_STATEMENT,
        "citation": citation,
        "BibTeX_citation": bibtex,
    }

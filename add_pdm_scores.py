from eval_align import phone_align
import os
import shutil
import tempfile
import xml.etree.ElementTree as ET
import urllib.request
from urllib.parse import unquote, urlparse
import torchaudio
import torch

CORPORA_PATH = "Corpora/"
BATCH_SIZE = int(os.environ.get("PDM_BATCH_SIZE", "256"))
FORCE_RECOMPUTE_SCORES = os.environ.get("PDM_FORCE_RECOMPUTE", "0") == "1"
TEMP_ROOT_DIR = "temp"

AVAILABLE_AUDIO_BACKENDS = tuple(torchaudio.list_audio_backends())

ISO_TO_LANGUAGE: dict[str, str] = {
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

def get_xml_lang(tree_root):
    attrs = tree_root.attrib
    for key in ("xml:lang", "{http://www.w3.org/XML/1998/namespace}lang"):
        value = attrs.get(key)
        if value:
            return value
    return ""


def is_published_xml_path(file_path):
    normalized = os.path.normpath(file_path)
    parts = [part.lower() for part in normalized.split(os.sep)]
    return "xml" in parts and "codeanddocs" not in parts


def download_audio_from_url(audio_url, destination_dir):
    parsed = urlparse(audio_url)
    filename = os.path.basename(parsed.path)
    if not filename:
        filename = "downloaded_audio"
    local_name = os.path.join(destination_dir, unquote(filename))
    request = urllib.request.Request(
        audio_url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
    )
    with urllib.request.urlopen(request) as response, open(local_name, "wb") as out_file:
        out_file.write(response.read())
    return local_name


def _guess_binary_signature(path):
    try:
        with open(path, "rb") as in_file:
            head = in_file.read(256).lower()
    except OSError:
        return "unreadable"
    if b"<html" in head or b"<!doctype" in head:
        return "html"
    if head.startswith(b"{") or head.startswith(b"["):
        return "json"
    return "binary"


def _load_audio_with_torchaudio(audio_path):
    ext = os.path.splitext(audio_path)[1].lower().lstrip(".")
    format_hint = ext if ext else None
    attempts: list[dict[str, str | None]] = [{"backend": None, "format": None}]
    if format_hint:
        attempts.append({"backend": None, "format": format_hint})

    for backend in AVAILABLE_AUDIO_BACKENDS:
        attempts.append({"backend": backend, "format": None})
        if format_hint:
            attempts.append({"backend": backend, "format": format_hint})

    errors = []
    for attempt in attempts:
        kwargs = {}
        if attempt["backend"] is not None:
            kwargs["backend"] = attempt["backend"]
        if attempt["format"] is not None:
            kwargs["format"] = attempt["format"]
        try:
            waveform, sample_rate = torchaudio.load(audio_path, **kwargs)
            return waveform, sample_rate, None
        except TypeError:
            # Older torchaudio builds may not accept backend/format kwargs.
            if kwargs:
                continue
            errors.append("TypeError while calling torchaudio.load")
        except Exception as exc:
            errors.append(f"backend={attempt['backend']} format={attempt['format']} -> {exc}")

    return None, None, errors


def convert_audio_to_wav(audio_path, destination_dir):
    stem = os.path.splitext(os.path.basename(audio_path))[0] or "audio"
    with tempfile.NamedTemporaryFile(
        prefix=f"{stem}_", suffix=".wav", delete=False, dir=destination_dir
    ) as tmp:
        wav_path = tmp.name

    try:
        waveform, sample_rate, errors = _load_audio_with_torchaudio(audio_path)
        if waveform is None or sample_rate is None:
            signature = _guess_binary_signature(audio_path)
            backend_info = ", ".join(AVAILABLE_AUDIO_BACKENDS) or "none"
            last_error = errors[-1] if errors else "unknown decode error"
            print(
                f"Warning: torchaudio could not decode {audio_path} "
                f"(signature={signature}, backends={backend_info}). Last error: {last_error}"
            )
            if os.path.exists(wav_path):
                os.remove(wav_path)
            return None
        if waveform.ndim == 1:
            waveform = waveform.unsqueeze(0)
        # allosaurus expects a PCM WAV readable via Python's wave module.
        if waveform.dtype != torch.float32:
            waveform = waveform.to(torch.float32)
        torchaudio.save(
            wav_path,
            waveform,
            sample_rate,
            format="wav",
            encoding="PCM_S",
            bits_per_sample=16,
        )
        return wav_path
    except Exception as exc:
        print(f"Warning: torchaudio conversion failed for {audio_path}: {exc}")
        if os.path.exists(wav_path):
            os.remove(wav_path)
        return None


def get_corpus_dir_from_xml_path(xml_path):
    parts = os.path.normpath(xml_path).split(os.sep)
    parts_lower = [part.lower() for part in parts]
    if "xml" not in parts_lower:
        return None
    xml_index = parts_lower.index("xml")
    if xml_index <= 0:
        return None
    return os.sep.join(parts[:xml_index])


def resolve_local_audio_path(xml_path, audio_filename, language_name, dialect):
    if not audio_filename:
        return None
    audio_filename = unquote(audio_filename.strip())
    if not audio_filename:
        return None
    if os.path.isabs(audio_filename) and os.path.isfile(audio_filename):
        return audio_filename

    xml_dir = os.path.dirname(xml_path)
    corpus_dir = get_corpus_dir_from_xml_path(xml_path)
    subdir = f"{dialect}_{language_name}" if dialect else language_name

    candidates = [
        os.path.join(xml_dir, audio_filename),
        os.path.join(xml_dir, "Audio", audio_filename),
        os.path.join(xml_dir, "audio", audio_filename),
    ]

    if corpus_dir:
        candidates.extend(
            [
                os.path.join(corpus_dir, "Audio", audio_filename),
                os.path.join(corpus_dir, "audio", audio_filename),
                os.path.join(corpus_dir, "Audio", language_name, subdir, audio_filename),
                os.path.join(corpus_dir, "audio", language_name, subdir, audio_filename),
            ]
        )

    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return None


def _cleanup_audio_artifacts(converted_wav, downloaded_audio, audio_file):
    if converted_wav and os.path.exists(converted_wav):
        os.remove(converted_wav)
    if downloaded_audio and audio_file and os.path.exists(audio_file):
        os.remove(audio_file)


def _process_score_batch(batch, language_name):
    if not batch:
        return False, 0

    try:
        phone_align([item["entry"] for item in batch], language_name)
    except Exception as exc:
        for item in batch:
            _cleanup_audio_artifacts(
                item["converted_wav"],
                item["downloaded_audio"],
                item["audio_file"],
            )
        print(f"Warning: audio alignment batch failed: {exc}")
        return False, 0

    file_changed = False
    written_scores = 0
    for item in batch:
        entry = item["entry"]
        if "score" not in entry:
            _cleanup_audio_artifacts(
                item["converted_wav"],
                item["downloaded_audio"],
                item["audio_file"],
            )
            continue

        score_elem = item["sentence_elem"].find("SCORE")
        if score_elem is None:
            score_elem = ET.SubElement(item["sentence_elem"], "SCORE")
        score_elem.text = str(entry.get("score", 0))
        file_changed = True
        written_scores += 1
        _cleanup_audio_artifacts(
            item["converted_wav"],
            item["downloaded_audio"],
            item["audio_file"],
        )

    return file_changed, written_scores


def _iter_score_batches(items):
    if BATCH_SIZE <= 0:
        yield items
        return
    for start in range(0, len(items), BATCH_SIZE):
        yield items[start : start + BATCH_SIZE]


def main():
    updated_xml_files = 0
    written_scores = 0
    temp_root_path = os.path.abspath(TEMP_ROOT_DIR)
    os.makedirs(temp_root_path, exist_ok=True)
    run_temp_dir = tempfile.mkdtemp(prefix="pdm_", dir=temp_root_path)

    try:
        for root, dirs, files in os.walk(CORPORA_PATH):
            for file in files:
                if file.endswith(".xml"):
                    xml_path = os.path.join(root, file)
                    if not is_published_xml_path(xml_path):
                        continue
                    try:
                        tree = ET.parse(xml_path)
                    except ET.ParseError as exc:
                        print(f"Warning: skipping malformed XML {xml_path}: {exc}")
                        continue
                    tree_root = tree.getroot()
                    lang = get_xml_lang(tree_root)
                    language_name = ISO_TO_LANGUAGE.get(lang, lang)
                    dialect = tree_root.attrib.get("dialect", "")
                    file_changed = False
                    pending_entries = []
                    audio_path_cache = {}
                    downloaded_url_cache = {}
                    converted_audio_cache = {}

                    for s in tree_root.findall(".//S"):
                        if not FORCE_RECOMPUTE_SCORES:
                            existing_score = s.find("SCORE")
                            if existing_score is not None and (existing_score.text or "").strip():
                                continue

                        form = s.find(f"FORM[@kindOf='standard']")
                        sentence_text = form.text if form is not None and form.text is not None else ""
                        audio_elem = s.find("AUDIO")
                        audio_file = None
                        downloaded_audio = False
                        converted_wav = None
                        if audio_elem is None:
                            print(f"Warning: no AUDIO element found for sentence in {xml_path} for id {s.attrib.get('id', 'unknown')}")
                            continue
                        audio_filename = audio_elem.get("file") or (audio_elem.text or "").strip()
                        if audio_filename in audio_path_cache:
                            audio_file = audio_path_cache[audio_filename]
                        else:
                            audio_file = resolve_local_audio_path(xml_path, audio_filename, language_name, dialect)
                            audio_path_cache[audio_filename] = audio_file
                        audio_url = audio_elem.get("url")
                        if audio_file is None and audio_url:
                            if audio_url in downloaded_url_cache:
                                audio_file = downloaded_url_cache[audio_url]
                                downloaded_audio = bool(audio_file)
                            else:
                                try:
                                    audio_file = download_audio_from_url(audio_url, run_temp_dir)
                                    downloaded_audio = True
                                    downloaded_url_cache[audio_url] = audio_file
                                except OSError as exc:
                                    downloaded_url_cache[audio_url] = None
                                    print(f"Warning: failed to download audio from {audio_url}: {exc}")
                                    continue
                        if audio_file and os.path.isfile(audio_file):
                            if not audio_file.lower().endswith(".wav"):
                                if audio_file in converted_audio_cache:
                                    converted_wav = converted_audio_cache[audio_file]
                                else:
                                    converted_wav = convert_audio_to_wav(audio_file, run_temp_dir)
                                    converted_audio_cache[audio_file] = converted_wav
                                if not converted_wav:
                                    print(f"Warning: failed to convert non-wav audio file {audio_file} to wav")
                                    if downloaded_audio and audio_file and os.path.exists(audio_file):
                                        os.remove(audio_file)
                                    continue
                            align_path = converted_wav if converted_wav is not None else audio_file
                            pending_entries.append(
                                {
                                    "sentence_elem": s,
                                    "entry": {"ref": align_path, "sentence": sentence_text},
                                    "converted_wav": converted_wav,
                                    "downloaded_audio": downloaded_audio,
                                    "audio_file": audio_file,
                                }
                            )

                    for pending_batch in _iter_score_batches(pending_entries):
                        batch_changed, batch_written = _process_score_batch(pending_batch, language_name)
                        file_changed = file_changed or batch_changed
                        written_scores += batch_written

                    if file_changed:
                        tree.write(xml_path, encoding="utf-8", xml_declaration=True)
                        updated_xml_files += 1
                        print(f"Updated XML file: {xml_path}")
                    else:
                        print(f"Skipped writing {xml_path} because file_changed was False")
    finally:
        shutil.rmtree(run_temp_dir, ignore_errors=True)
        try:
            if os.path.isdir(temp_root_path) and not os.listdir(temp_root_path):
                os.rmdir(temp_root_path)
        except OSError:
            pass

    print(f"Updated XML files: {updated_xml_files}")
    print(f"Scores written: {written_scores}")


if __name__ == "__main__":
    main()
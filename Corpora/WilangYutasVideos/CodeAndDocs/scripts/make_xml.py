import os
import re
from lxml import etree
from pathlib import Path
from html import unescape
from pypinyin import lazy_pinyin, Style
import yt_dlp

def chinese_to_pinyin(text):
    """Replace every Chinese character in text with its pinyin (no tones)."""
    result = []
    for char in text:
        if '\u4e00' <= char <= '\u9fff' or '\u3400' <= char <= '\u4dbf':
            result.extend(lazy_pinyin(char, style=Style.NORMAL))
        else:
            result.append(char)
    return ''.join(result)

_PUNCT_SPACING_RE = re.compile(r"(?<=[a-zA-Z'\u2019])(,|\.)(?=[a-zA-Z'\u2019])")
_PAREN_BEFORE_RE = re.compile(r"(?<=[^\s(])\(")   # missing space before (
_PAREN_AFTER_RE  = re.compile(r"\)(?=[^\s),.:;!?'\u2019])")  # missing space after )
_MULTI_SPACE_RE  = re.compile(r" {2,}")
_TRAIL_SPACE_BEFORE_PUNCT_RE = re.compile(r" +([,\.!?:;]+)\s*$")  # space(s) before trailing punctuation (trailing whitespace also eaten)
_OPEN_PAREN_WORD_RE  = re.compile(r"(?<=[\w''])\s*\(")   # ( preceded by a word char (with optional space)
_CLOSE_PAREN_RE      = re.compile(r" *\)[,\.!?:;]*")       # optional space before ), ) itself, optionally followed by punctuation → all consumed together
_LEADING_COMMA_RE    = re.compile(r"(?<=\S) +(,+) *")             # space(s) + comma(s) [+ optional space] after a word → move comma to previous word
_LEADING_PERIOD_RE   = re.compile(r"(?<=\S) +(\.+)(?=[^\s,\.])" )  # space(s) + period(s) directly before a word char → move period to previous word (not ellipsis)
_UNCLEAR_RE          = re.compile(r"[?\uff1f]{3,}")                  # three or more ?/？ → <UNCLEAR/>

def set_form_text(elem, text):
    """Set the text content of a FORM element, inserting <UNCLEAR/> child elements
    wherever the text contains three or more consecutive question marks."""
    parts = _UNCLEAR_RE.split(text)
    elem.text = parts[0]
    for part in parts[1:]:
        unclear = etree.SubElement(elem, "UNCLEAR")
        unclear.tail = part

def _close_paren_repl(m):
    """Replace (optional space +) ) with ". " unless the content before it already ends with sentence-ending punctuation."""
    preceding = m.string[:m.start()].rstrip()  # look before the leading space(s) the regex consumed
    if preceding and preceding[-1] in '?!.':
        return ' '   # already ends a sentence — just add a space, no extra period
    return '. '
def fix_punctuation_spacing(text):
    """Ensure proper spacing around punctuation.

    - Space after comma/period when directly abutting a letter.
    - Space before ( when not already preceded by whitespace or another (.
    - Space after ) when not already followed by whitespace or punctuation.
    - No space before punctuation at the end of the string.
    - Comma/period that leads a word (space before, no space after) is moved to attach to the previous word.
    """
    text = _PUNCT_SPACING_RE.sub(r"\1 ", text)
    text = _PAREN_BEFORE_RE.sub(r" (", text)
    text = _PAREN_AFTER_RE.sub(r") ", text)
    text = _LEADING_COMMA_RE.sub(r"\1 ", text)
    text = _LEADING_PERIOD_RE.sub(r"\1 ", text)
    text = _TRAIL_SPACE_BEFORE_PUNCT_RE.sub(r"\1", text)
    return text

def remove_parens(text):
    """Remove bare parentheses from text, keeping the content inside them.

    - An opening ( preceded by a word character ends that word with a period:
      "word (second)" → "word. second. "
    - An opening ( at the start of the string or after punctuation is just removed.
    - A closing ) is replaced by ". " (period + space).

    Returns (cleaned_text, had_parens). Double spaces are collapsed.
    """
    had_parens = "(" in text or ")" in text
    # ( after a word/apostrophe: strip any preceding space and add ". "
    cleaned = _OPEN_PAREN_WORD_RE.sub(". ", text)
    # remaining ( (at start of string or after punctuation): just remove
    cleaned = cleaned.replace("(", "")
    # ) → ". " (or just " " if already preceded by ?/!/.), consuming any trailing punctuation after )
    cleaned = _CLOSE_PAREN_RE.sub(_close_paren_repl, cleaned)
    cleaned = _MULTI_SPACE_RE.sub(" ", cleaned).strip()
    return cleaned, had_parens

def _has_chinese(text):
    """Return True if text contains any CJK character."""
    return any('\u4e00' <= c <= '\u9fff' or '\u3400' <= c <= '\u4dbf' for c in text)

# Set current working directory to that of this script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Define XML namespace – this will be consistent across all files
XML_NS = "http://www.w3.org/XML/1998/namespace"

def create_xml_header(language_name, lang_code, dialect, youtube_url, video_id, video_title):
    """Create XML root with proper header information."""
    root = etree.Element("TEXT")
    
    citation = unescape(
        f"劉宇陽. (2024, December 26). Permission for use of {language_name} video transcriptions and related media"
    )

    bibtex = unescape(
        f"@misc{{Liu2024_{language_name}, "
        "author = {劉宇陽}, "
        f"title = {{Permission for use of {language_name} video transcriptions and related media}}, "
        "year = {2024}, "
        "month = {December 26}, "
        "note = {{Permission granted under a CC BY‐NC license for materials from qmalup.wixsite.com/pinsgayan and Yutas Wilang Videos: https://www.youtube.com/channel/UCaIhCF9rsKDlVo1xzfCU7nA}}"
        "}"
    )
    
    # Set attributes in specific order
    root.set("id", f"{video_title}")
    root.set("{" + XML_NS + "}lang", lang_code)
    root.set("dialect", dialect)
    root.set("audio", unescape(youtube_url))
    root.set("source", "Wilang Yutas Atayal Videos")
    root.set("copyright", "CC-BY-NC")
    root.set("citation", "")
    root.set("BibTeX_citation", "")
    
    return root

def convert_txt_to_xml(txt_path, language_name="Atayal", lang_code="tay", dialect="UNKNOWN"):
    """
    Convert a single transcript .txt file into XML.
    
    Expects the .txt file to be named in the format:
        {video_title}_{video_id}.txt
        
    Each line in the file should be of the format:
        start_time: transcript text
    """
    # Extract video title and video id from the file name.
    # YouTube IDs are always exactly 11 base64url characters [A-Za-z0-9_-] and
    # may themselves contain underscores, so we cannot simply split on the last
    # underscore — we always take the last 11 characters as the ID.
    stem = txt_path.stem
    if len(stem) < 12:
        raise ValueError(f"Filename {txt_path} is too short to contain a YouTube ID.")
    video_id = stem[-11:]
    video_title = stem[:-12]  # strip trailing underscore + 11-char ID
    
    # Build YouTube URL using the video_id
    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    
    # Create XML header using the fixed values (you can adjust as needed)
    root = create_xml_header(language_name, lang_code, dialect, youtube_url, video_id, video_title)
    
    # Read and process each line in the .txt file
    with open(txt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Parse ALL lines, preserving every timestamp for accurate stop times.
    # Each entry is a mutable list: [start_time, text, translation_or_None].
    # A line that follows a timestamped entry and contains Chinese characters
    # is treated as the Mandarin translation of that entry.
    all_entries = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        colon_pos = stripped.find(":")
        if colon_pos > 0 and stripped[:colon_pos].replace(".", "").isdigit():
            # Timestamped line
            start_time = stripped[:colon_pos].strip()
            text = stripped[colon_pos + 1:].strip()
            all_entries.append([start_time, text, None])
        elif all_entries and _has_chinese(stripped):
            # Non-timestamp line containing Chinese → translation for previous entry
            all_entries[-1][2] = stripped
        # else: non-Chinese continuation (e.g. wrapped Atayal caption) — ignored

    # Build the list of XML-worthy entries, keeping track of their raw index
    # so we can look up the immediately-following timestamp for stop.
    xml_entries = [(raw_i, start, text, transl)
                   for raw_i, (start, text, transl) in enumerate(all_entries) if text]

    for sentence_number, (raw_i, start_time, text, translation) in enumerate(xml_entries, start=1):
        # Create a sentence element
        s = etree.SubElement(root, "S")
        s.set("id", f"{language_name}_{sentence_number}")

        # Normalize punctuation spacing, then strip parentheses.
        # fix_punctuation_spacing runs first so parens are space-padded before
        # removal, avoiding words being concatenated across the boundary.
        # Trailing-space-before-punctuation is re-applied last because paren
        # removal can expose " ." patterns (e.g. "(text .)" → "text .").
        normalized_text, had_parens = remove_parens(fix_punctuation_spacing(text))
        normalized_text = _TRAIL_SPACE_BEFORE_PUNCT_RE.sub(r"\1", normalized_text)

        # Add original text under FORM element, plus an identical standard copy
        form = etree.SubElement(s, "FORM")
        form.set("kindOf", "original")
        if had_parens:
            form.set("notes", "multiple speakers")
        set_form_text(form, normalized_text)

        form_std = etree.SubElement(s, "FORM")
        form_std.set("kindOf", "standard")
        if had_parens:
            form_std.set("notes", "multiple speakers")
        set_form_text(form_std, normalized_text)

        if translation:
            transl = etree.SubElement(s, "TRANSL")
            transl.set("{" + XML_NS + "}lang", "zho")
            transl.text = translation

        # Add Chinese translation (empty here; update if you have translation)
        '''
        transl = etree.SubElement(s, "TRANSL")
        transl.set("{" + XML_NS + "}lang", "zho")
        transl.text = ""
        '''

        # Add AUDIO tag with start and stop times.
        # stop is the start of the immediately next raw entry (empty or not),
        # so gaps in the caption upload don't inflate the stop time.
        # Omitted for the final entry.
        audio = etree.SubElement(s, "AUDIO")
        audio.set("start", start_time)
        if raw_i + 1 < len(all_entries):
            audio.set("stop", all_entries[raw_i + 1][0])
    
    return root, video_title, video_id

def save_xml(root, output_path):
    """Save XML tree to file with proper formatting."""
    tree = etree.ElementTree(root)
    tree.write(output_path, encoding="utf-8", pretty_print=True, xml_declaration=True)

def process_all_txt():
    """
    Process all .txt files (expected to be named as {video_title}_{video_id}.txt)
    in the current directory and convert them into XML files.

    Also creates empty XML stubs (no <S> entries) for every channel video that
    has no corresponding .txt file (e.g. transcript unavailable or deleted).

    The XML files will be saved in a directory one level up in 'Final_XML/Atayal'.
    """
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    txt_dir = Path("../raw_scrape")
    xml_dir = Path("../Final_XML/Atayal")
    xml_dir.mkdir(parents=True, exist_ok=True)

    # --- Pass 1: convert every .txt with transcript data ---
    # Track which video IDs we already have a transcript for.
    scraped_ids = set()
    for txt_file in txt_dir.glob("*.txt"):
        try:
            xml_root, video_title, video_id = convert_txt_to_xml(txt_file, dialect="Sekolik")
            xml_stem = chinese_to_pinyin(video_title)
            xml_root.set("id", xml_stem)  # id matches filename stem
            xml_filename = xml_stem + ".xml"
            xml_path = xml_dir / xml_filename
            save_xml(xml_root, xml_path)
            print(f"Converted {txt_file.name} → {xml_path.name}")
            scraped_ids.add(video_id)
        except Exception as e:
            print(f"Error processing {txt_file}: {e}")

    # --- Pass 2: create empty XML stubs for videos with no transcript ---
    channel_url = "https://www.youtube.com/@wilangyutas9297/videos"
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'skip_download': True,
        'dump_single_json': True,
    }
    print("\nFetching full channel video list for stub generation...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        channel_info = ydl.extract_info(channel_url, download=False)

    for video in channel_info.get('entries', []):
        video_id = video.get('id') or video.get('url')
        if not video_id or video_id in scraped_ids:
            continue  # already has a full transcript XML

        # Sanitize title the same way scrape.py does
        video_title = video.get('title', 'untitled')
        video_title = re.sub(r'[^\w\s-]', '', video_title).strip()
        video_title = re.sub(r'[-\s]+', '_', video_title)

        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        root = create_xml_header("Atayal", "tay", "Sekolik", youtube_url, video_id, video_title)
        xml_stem = chinese_to_pinyin(video_title)
        root.set("id", xml_stem)  # id matches filename stem
        xml_filename = xml_stem + ".xml"
        xml_path = xml_dir / xml_filename
        save_xml(root, xml_path)
        print(f"  Stub created for {video_id} → {xml_path.name}")

if __name__ == "__main__":
    process_all_txt()

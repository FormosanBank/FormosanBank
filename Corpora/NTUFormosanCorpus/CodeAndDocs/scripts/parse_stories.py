"""
create_xml_stories.py

Step 1 of 2.  Reads the story JSON files and writes one XML file per story
to Final_XML/Stories/<lang>/.  Each <AUDIO> element records the segment
file name, the source URL, and the start/end timestamps so that
download_stories_audio.py (step 2) can work entirely from the XML.

Run this script first, then run download_stories_audio.py.
"""

import csv
import itertools
import json
import os
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import clean_punctuation, add_transl_element, strip_speaker_labels_from_translation, filter_punct_words, is_punct_only, join_ori_tokens, insert_xxxx_tokens, strip_l2m, strip_prosodic_markers, expand_infixes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Maps the folder-derived dialect token to the display name used in the XML
# dialect attribute.  Languages whose folder suffix equals their language name
# (e.g. Kanakanavu_Kanakanavu, Tsou_Tsou, Sakizaya_Sakizaya) are excluded and
# receive no dialect attribute.  Unlisted suffixes also get no attribute.
DIALECT_NAMES = {
    'Ciwkangan': 'Coastal',   # Amis
    'Mayrinax':  'Wenshui',   # Atayal
    'Isbukun':   'Junqun',    # Bunun
    'Vedai':     'Wutai',     # Rukai
    'Tgdaya':    'Tegudaya',  # Seediq
}


def prettify(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="    ")


def clean_origin(ori):
    """Remove annotation artifacts from a reconstructed sentence string."""
    ori = re.sub(r"<L2[A-Za-z]", "", ori)   # opening code-switch tag
    ori = re.sub(r"L2[A-Za-z]>", "", ori)   # closing code-switch tag
    ori = re.sub(r"[\\/^,<>@_\[\]]+", "", ori)
    ori = re.sub("==", "", ori)              # prosodic marker
    ori = re.sub("=", "", ori)              # clitic boundary
    ori = re.sub(r"\.\.\.", "", ori)        # pause marker
    ori = re.sub(r"\.\.", "", ori)
    ori = re.sub(r"…", "", ori)
    ori = re.sub("-", "", ori)
    ori = ori.replace(".", "")
    ori = ori.strip()
    ori = re.sub(r'\s+', ' ', ori)
    if not ori.endswith(('.', '?', '!')):
        ori += "."
    return ori


def _build_form(gloss):
    """Return the cleaned form field for a gloss triple.

    ``clean_punctuation`` strips ``={2,}`` runs (discourse / prosodic
    markers), but ``===`` can also encode a clitic boundary (``==`` DM
    followed immediately by the ``=`` clitic marker).  We detect that case
    by checking whether either gloss column contains a bare ``=`` (clitic
    indicator) and, if so, pre-collapse ``===+`` → ``=`` *before* calling
    ``clean_punctuation``, so the clitic boundary survives into the FORM.
    """
    raw = strip_prosodic_markers(gloss[0])
    if re.search(r'={3,}', raw):
        has_clitic = any(
            '=' in (gloss[j] if j < len(gloss) and gloss[j] else '')
            for j in (1, 2)
        )
        if has_clitic:
            raw = re.sub(r'={3,}', '=', raw)
    return re.sub(r"[\\\\,\.\[\]/]+", "", clean_punctuation(raw))


# ---------------------------------------------------------------------------
# JSON → sentence dicts
# ---------------------------------------------------------------------------

def get_story(data, src=""):
    """
    Walk the gloss data and return a list whose first item is the audio
    filename (or None) followed by one dict per sentence.
    """
    to_return = []
    idx = s_id = 0

    while idx < len(data):
        s = data[idx][1]
        tmp = {}
        tmp['id'] = s_id

        # The very first entry carries the audio filename in its metadata.
        if idx == 0:
            video = s.get('meta', {}).get('video', "None")
            to_return.append(None if video == "None" else video)

        tmp['ori'] = clean_punctuation(
            join_ori_tokens([strip_prosodic_markers(gloss[0]) for gloss in s["gloss"] if len(gloss[1]) > 1])
        )
        tmp['ori_fallback'] = [strip_prosodic_markers(str(t)) for t in s.get('ori', [])]
        tmp['ori_id'] = [data[idx][0]]
        tmp['words'] = []
        for gloss in s["gloss"]:
            if not gloss[1]:
                continue
            tmp['words'].append([
                _build_form(gloss),
                clean_punctuation(gloss[1]),
                clean_punctuation(gloss[2]),
            ])
        tmp['words'] = filter_punct_words(tmp['words'], s_id=f"story_{idx}", src=src)

        tmp['audio_stamp'] = [s['iu_a_span'][0]]

        # Accumulate intonation units that belong to the same sentence.
        while not s['s_end']:
            idx += 1
            if idx == len(data):
                break
            s = data[idx][1]
            tmp['ori_id'].append(data[idx][0])
            tmp['ori'] += " " + clean_punctuation(
                join_ori_tokens([strip_prosodic_markers(gloss[0]) for gloss in s["gloss"] if len(gloss[1]) > 1])
            )
            tmp['ori_fallback'] += [strip_prosodic_markers(str(t)) for t in s.get('ori', [])]
            continuation = []
            for gloss in s["gloss"]:
                if not gloss[1]:
                    continue
                continuation.append([
                    _build_form(gloss),
                    clean_punctuation(gloss[1]),
                    clean_punctuation(gloss[2]),
                ])
            tmp['words'] += filter_punct_words(continuation, s_id=f"story_{idx}", src=src)

        if s['s_end']:
            tmp["audio_stamp"] = s.get('s_a_span', [None])
        else:
            tmp["audio_stamp"].append(s['iu_a_span'][1])

        if 'free' in s:
            for tran in s['free']:
                if tran[:2] == "#e":
                    tmp['en'] = strip_speaker_labels_from_translation(clean_punctuation(tran[2:]))
                elif tran[:2] == "#c":
                    tmp['zh'] = strip_speaker_labels_from_translation(clean_punctuation(tran[2:]))

        if tmp['ori'] == "XX":
            idx += 1
            continue
        tmp['ori'] = tmp['ori'].replace('XX', "")
        tmp['ori'] = clean_origin(tmp['ori'])

        # Fallback for utterances fully in a code-switched language (L2): the
        # gloss filter leaves ori empty.  Recover from the IU 'ori' token list.
        if tmp['ori'] == "." and tmp.get('ori_fallback'):
            fallback = clean_punctuation(" ".join(str(t) for t in tmp['ori_fallback']))
            if fallback and fallback != ".":
                if not fallback.endswith(('.', '?', '!')):
                    fallback += "."
                tmp['ori'] = fallback
        del tmp['ori_fallback']

        if len(tmp['ori_id']) > 1:
            tmp['ori_id'] = [tmp['ori_id'][0], tmp['ori_id'][-1]]

        to_return.append(tmp)
        idx += 1
        s_id += 1

    return to_return


# ---------------------------------------------------------------------------
# XML construction
# ---------------------------------------------------------------------------

def process_words(s, s_element, issues, lang_name, file_name, s_id_str):
    """
    Add <W> / <M> elements for every word in the sentence.
    Returns False (and logs to issues CSV) if morpheme counts do not match.
    """
    for i, w in enumerate(s['words']):
        if w[0] == 'XX' or not w[0]:
            continue

        w_element = ET.SubElement(s_element, "W")
        w_element.set("id", f"{s_id_str}_W{i}")

        # Clean up double-hyphens, then strip leading/trailing hyphens.
        for idx in range(3):
            w[idx] = w[idx].replace("--", "")
        w[0], is_cs = strip_l2m(w[0])
        if is_punct_only(w[0]):
            s_element.remove(w_element)
            continue
        w_form = ET.SubElement(w_element, "FORM")
        w_form.set("kindOf", "original")
        w_form.text = w[0]
        if is_cs:
            w_form.set("notes", "code-switch")
        for idx in range(3):
            if w[idx] and w[idx][-1] == '-':
                w[idx] = w[idx][:-1]
            if w[idx] and w[idx][0] == '-':
                w[idx] = w[idx][1:]

        # W-level full gloss TRANSL (before M elements)
        zh_full = clean_punctuation(w[2])
        en_full = clean_punctuation(w[1])
        if zh_full and zh_full != '_':
            add_transl_element(w_element, "zho", zh_full)
        if en_full and en_full != '_':
            add_transl_element(w_element, "en", en_full)

        # Amis: "satu" glossed "SA=PFV" — insert clitic boundary for splitting
        # only; the word-level FORM element above is left as-is.
        form_for_split = w[0]
        if lang_name.startswith('Amis'):
            if (clean_punctuation(w[0]) == 'satu'
                    and clean_punctuation(w[1]) == 'SA=PFV'):
                form_for_split = form_for_split.replace('satu', 'sa=tu')

        m    = clean_punctuation(form_for_split).split('-')
        m_en = clean_punctuation(w[1].replace('so-called', 'so.called')).split('-')
        m_zh = clean_punctuation(w[2]).split('-')

        if len(m) != len(m_en) or len(m) != len(m_zh):
            with open(issues, mode='a', newline='') as f:
                csv.writer(f).writerow([lang_name, file_name, s['ori_id'], m, m_en, m_zh])

        for j, (mf, me, mc) in enumerate(
                itertools.zip_longest(m, m_en, m_zh, fillvalue='')):
            part_f = re.split(r'(?<!=)=(?!=)', mf) if mf else ['']
            part_e = re.split(r'(?<!=)=(?!=)', me) if me else ['']
            part_c = re.split(r'(?<!=)=(?!=)', mc) if mc else ['']

            if len(part_f) != len(part_e) or len(part_f) != len(part_c):
                with open(issues, mode='a', newline='') as f:
                    csv.writer(f).writerow([lang_name, file_name, s['ori_id'],
                                            part_f, part_e, part_c])

            for k, (pf, pe, pc) in enumerate(
                    itertools.zip_longest(part_f, part_e, part_c, fillvalue='')):
                # Skip empty trailing slots produced by a bare trailing '='
                # (proclitic marker with no separate gloss), e.g. "isaa=" splits
                # into ['isaa', ''] but the gloss has no second entry.
                if not pf and not pe and not pc:
                    continue
                # Expand infixes: a form like q<n>qda yields two M elements —
                # one for the infix <n> and one for the base qqda.
                sub_morphemes = expand_infixes(pf, pe, pc)
                for n, (sf, se, sc) in enumerate(sub_morphemes):
                    m_elem = ET.SubElement(w_element, "M")
                    if len(sub_morphemes) > 1:
                        m_elem.set("id", f"{s_id_str}_W{i}_M{j}_{k}_{n}")
                    else:
                        m_elem.set("id", f"{s_id_str}_W{i}_M{j}_{k}")
                    m_f = ET.SubElement(m_elem, "FORM")
                    m_f.set("kindOf", "original")
                    m_f.text = sf
                    tr_en = ET.SubElement(m_elem, "TRANSL")
                    tr_en.set('xml:lang', 'en')
                    tr_en.text = se
                    tr_zh = ET.SubElement(m_elem, "TRANSL")
                    tr_zh.set('xml:lang', 'zho')
                    tr_zh.text = sc

    return True


def process_story(story, file_name, audio_name, root, issues, lang_name, missing_issues):
    """
    Build <S> elements for every sentence and attach them to root.
    <AUDIO> elements carry start= and end= attributes (in seconds) so
    download_stories_audio.py can extract segments without re-reading the JSON.
    """
    if not story:
        return

    shift = story[0]['audio_stamp'][0] or 0.0

    for s in story:
        s_id_str = f"{file_name}_S_{s['id']}"
        s_element = ET.SubElement(root, "S")
        s_element.set("id", s_id_str)
        s_f = ET.SubElement(s_element, "FORM")
        s_f.set("kindOf", "original")
        s_f.text = insert_xxxx_tokens(s['ori'], s.get('words', []))

        if 'zh' in s:
            add_transl_element(s_element, "zho", s['zh'])
        if 'en' in s:
            add_transl_element(s_element, "en", s['en'])

        has_stamp = s['audio_stamp'][0] is not None
        if has_stamp and audio_name:
            start = s['audio_stamp'][0] - shift
            end   = s['audio_stamp'][1] - shift
            if lang_name == "Bunun":   # Bunun timestamps are absolute
                start += shift
                end   += shift
            audio_elem = ET.SubElement(s_element, "AUDIO")
            audio_elem.set("file",  f"{file_name}_S{s['id']}.mp3")
            audio_elem.set("url",   f"https://formosanbank.linguistics.ntu.edu.tw/files/audio/{audio_name}")
            audio_elem.set("start", str(round(start, 3)))
            audio_elem.set("end",   str(round(end,   3)))

        if 'words' in s:
            process_words(s, s_element, issues, lang_name, file_name, s_id_str)

        if not has_stamp and audio_name:
            with open(missing_issues, mode='a', newline='') as f:
                csv.writer(f).writerow([lang_name, file_name, s['ori_id'], s['ori']])


def process_file(lang_name, file, lang_stories_dir, xml_output, lang_codes, issues, missing_issues, dialect=''):
    """Read one JSON file and write its XML to xml_output."""
    file_name = file.split('.')[0]

    root = ET.Element("TEXT")
    root.set("id",              f"NTU_Stry_{lang_name}_{file_name}")
    root.set("xml:lang",        lang_codes[lang_name])
    root.set("source",          f"NTU Corpus stories for {lang_name}, story: {file_name}")
    root.set("audio",           "diarized")
    root.set("copyright",       "CC BY-NC")
    root.set("citation",        "Sung, L. M., Lily, I., Hsieh, F., & Lin, Z. (2008). Developing an online corpus of Formosan languages. Taiwan Journal of Linguistics, 6(2.).")
    root.set("BibTeX_citation", "@article{sung2008developing,title={Developing an online corpus of Formosan languages.},author={Sung, Li-May and Lily, I and Hsieh, Fuhui and Lin, Zhemin and others},journal={Taiwan Journal of Linguistics},volume={6},number={2},year={2008}}")
    if dialect:
        root.set("dialect", dialect)

    with open(os.path.join(lang_stories_dir, file), 'r') as js_file:
        data = json.load(js_file)

    story = get_story(data['glosses'], src=os.path.join(lang_stories_dir, file))
    print(f"  Processing: {file}")

    audio_name = story[0]
    story = story[1:]
    if not story:
        return
    if not audio_name:
        print(f"    No audio for {file_name}")

    process_story(story, file_name, audio_name, root, issues, lang_name, missing_issues)

    try:
        xml_string = prettify(root)
    except Exception as e:
        xml_string = ""
        print(f"    XML error for {lang_name}/{file}: {e}")

    with open(os.path.join(xml_output, f"{lang_name}_{file_name}.xml"), "w", encoding="utf-8") as xmlfile:
        xmlfile.write(xml_string)


def process_language(lang, stories_dir, project_dir, lang_codes, issues, missing_issues):
    """Process all JSON files in one language directory."""
    lang_stories_dir = os.path.join(stories_dir, lang)
    lang_name = lang.split('_')[0]
    _folder_dialect = lang.split('_')[1] if '_' in lang else ''
    if _folder_dialect == lang_name:
        _folder_dialect = ''
    dialect = DIALECT_NAMES.get(_folder_dialect, '')
    xml_output = os.path.join(project_dir, "Final_XML", "Stories", lang_name)
    os.makedirs(xml_output, exist_ok=True)

    for file in sorted(os.listdir(lang_stories_dir)):
        full_path = os.path.join(lang_stories_dir, file)
        if os.path.isdir(full_path) or file.startswith('.'):
            continue
        process_file(lang_name, file, lang_stories_dir, xml_output,
                     lang_codes, issues, missing_issues, dialect=dialect)


def main(lang_codes):
    curr_dir    = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(curr_dir)
    stories_dir = os.path.join(project_dir, "story")

    os.makedirs(os.path.join(project_dir, "Final_XML", "Stories"), exist_ok=True)

    issues = os.path.join(project_dir, "Final_XML", "Stories", "mismatch_issues.csv")
    with open(issues, mode='w', newline='') as f:
        csv.writer(f).writerow(["language", "file_name", "Sentence_id", "Formosan", "En", "Ch"])

    missing_issues = os.path.join(project_dir, "Final_XML", "Stories", "missing_issues.csv")
    with open(missing_issues, mode='w', newline='') as f:
        csv.writer(f).writerow(["language", "file_name", "Sentence_id", "sentence"])

    for lang in sorted(os.listdir(stories_dir)):
        if lang.startswith('.'):
            continue
        print(f"Language: {lang}")
        process_language(lang, stories_dir, project_dir, lang_codes, issues, missing_issues)


if __name__ == "__main__":
    lang_codes = {
        "Amis": "ami", "Atayal": "tay", "Saisiyat": "xsy", "Thao": "ssf", "Seediq": "trv",
        "Bunun": "bnn", "Paiwan": "pwn", "Rukai": "dru", "Truku": "trv", "Kavalan": "ckv",
        "Tsou": "tsu", "Kanakanavu": "xnb", "Saaroa": "sxr", "Puyuma": "pyu", "Yami": "tao",
        "Sakizaya": "szy",
    }
    main(lang_codes)

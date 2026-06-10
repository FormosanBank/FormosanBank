"""
create_xml_grammar.py

Step 1 of 2.  Reads the grammar JSON files and writes one XML file per
language to Final_XML/Grammar/<lang>/.  Each <AUDIO> element records the
segment file name and the source URL so that download_grammar_audio.py
(step 2) can work entirely from the XML.

Run this script first, then run download_grammar_audio.py.
"""

import itertools
import json
import os
import csv
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import clean_punctuation, add_transl_element, SPEAKER_TOKENS, is_speaker_token, strip_speaker_labels_from_translation, PAREN_TOKEN_RE, UNGRAMMATICAL_PAREN_RE, _drop_starred_slash, filter_punct_words, is_punct_only, fill_propername_gloss, _norm_paren, join_ori_tokens, insert_xxxx_tokens, strip_l2m, strip_prosodic_markers, expand_infixes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Matches CJK characters and CJK punctuation used as annotation labels in the
# form column (e.g. 'seto]謂語' → 'seto]', '人們在喝酒。' → '').  Only
# applied to non-wordlist entries; A2 wordlist glosses legitimately store
# Chinese text in column 0.
_CJK_RE = re.compile(
    r'[\u4e00-\u9fff'    # CJK Unified Ideographs
    r'\u3400-\u4dbf'    # CJK Extension A
    r'\u3000-\u303f'    # CJK Symbols and Punctuation (includes 。)
    r'\uff00-\uffef]+'  # Halfwidth and Fullwidth Forms
)

# Maps the folder-derived dialect token to the display name used in the XML
# dialect attribute.  Languages whose folder suffix equals their language name
# (e.g. Kanakanavu_Kanakanavu, Sakizaya_Sakizaya) are excluded and receive no
# dialect attribute.  Any folder suffix not listed here also gets no attribute.
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
    ori = re.sub(r"<L2[A-Za-z]", "", ori)
    ori = re.sub(r"L2[A-Za-z]>", "", ori)
    ori = re.sub(r"[\\/^,<>@_\[\]]+", "", ori)
    ori = re.sub("==", "", ori)
    ori = re.sub("=", "", ori)
    ori = re.sub(r"\.\.\.", "", ori)
    ori = re.sub(r"\.\.", "", ori)
    ori = re.sub(r"…", "", ori)
    ori = re.sub("-", "", ori)
    ori = ori.replace(".", "")
    ori = ori.strip()
    ori = re.sub(r'\s+', ' ', ori)
    if not ori.endswith(('.', '?', '!')):
        ori += "."
    return ori


# ---------------------------------------------------------------------------
# Per-sentence FORM overrides
# Key: (filename_stem, sentence_id)  e.g. ("ap2", 24)
# Value: corrected ori string (will be used verbatim as <FORM> text)
# ---------------------------------------------------------------------------

_FORM_OVERRIDES = {
    # Key: (lang_name, filename_stem, sentence_id)
    # ap2 S_24: source token "“kati...kati...”" is missing a space between the
    # two repetitions; the gloss correctly splits them as two separate words.
    ("Sakizaya", "ap2", 24): "“kati... kati...” sa misalisin.",
    ("Sakizaya", "15", 1): "manamuh mukan tu paza' ci Aki aci Imi.",
    ("Kanakanavu", "14", 24): "vanai tia 'apacangcangarʉʉn Pi'i, tia paracani Pani nukai 'utori.",
    ("Kanakanavu", "14", 27): "vanai tia 'apacangcangarʉʉn 'aree, paracani mataa 'utori Piori.",
    ("Kanakanavu", "15", 7): "vanai tia 'apacangcangarʉʉn 'aree, paracani mataa 'utori Piori.",
    ("Kanakanavu", "15", 24): "vanai tia 'apacangcangarʉʉn Pi'i, tia paracani Pani nukai 'utori.",
    ("Kanakanavu", "15", 25): "vanai tia 'apacangcangarʉ Pi'i, tia paracani Pani saa 'utori?",
}


# ---------------------------------------------------------------------------
# Entries that must expand into multiple <S> elements, each with its own
# FORM and word-gloss list.  This is used for the rare case where the source
# JSON encodes two full sentence variants (separated by an embedded slash in
# the ori list) AND the gloss has a single slash-delimited entry covering
# both variants, so neither the A2 variant path nor _strip_slash_variant
# produces correct output.
#
# Key:   (lang_name, filename_stem, sentence_id)
# Value: list of variant dicts, each with 'ori', optionally 'zh'/'en', and
#        'words' (list of [form, gloss_zh, notes] rows, same format as the
#        gloss lists in the JSON).
# ---------------------------------------------------------------------------

_SENTENCE_SPLIT_OVERRIDES = {
    # Kanakanavu 04.json id=37
    # The ori encodes two full sentences: one with 'Pani' (proper name) and
    # one with 'kasua' (2sg oblique).  The gloss has a single entry
    # 'Pani/kasua延伸名詞組' / '人名／你.斜格' and the free translation is
    # likewise slash-delimited.  Expand to two labelled sentences.
    ("Kanakanavu", "04", 37): [
        {
            'ori':   "tinituru cu maku Pani \u2019angai tamna c\u0289p\u0289ng\u0289.",
            'zh':    "我已經告訴Pani \u2019angai 的想法。",
            'words': [
                ['t<in>ituru=cu=maku', '<完成貌.受事焦點>告知=狀態改變=我.屬格', '_'],
                ['Pani',              '人名',                                    '_'],
                ['\u2019angai',       '人名',                                    '_'],
                ['tamna',             '屬於',                                    '_'],
                ['c\u0289p\u0289ng\u0289', '心',                               '_'],
            ],
        },
        {
            'ori':   "tinituru cu maku kasua \u2019angai tamna c\u0289p\u0289ng\u0289.",
            'zh':    "我已經告訴你\u2019angai的想法。",
            'words': [
                ['t<in>ituru=cu=maku', '<完成貌.受事焦點>告知=狀態改變=我.屬格', '_'],
                ['kasua',             '你.斜格',                                 '_'],
                ['\u2019angai',       '人名',                                    '_'],
                ['tamna',             '屬於',                                    '_'],
                ['c\u0289p\u0289ng\u0289', '心',                               '_'],
            ],
        },
    ],
}


# ---------------------------------------------------------------------------
# JSON → sentence dicts
# ---------------------------------------------------------------------------

def _strip_slash_variant(tok):
    """For tokens with slash-separated phonological variants (e.g. 'saa/sua'),
    keep only the first non-starred variant.  If one alternative is marked
    ungrammatical with a leading '*' (e.g. 'word/*other' or '*bad/good'),
    it is dropped and the remaining grammatical alternative is used.
    Standalone '/' tokens (A2 sentence separators) are handled upstream and
    never reach this function."""
    if tok and '/' in tok:
        parts = tok.split('/')
        good = [p for p in parts if not p.startswith('*')]
        return good[0] if good else parts[0]
    return tok


def get_grammar(data, src="", lang="", is_wordlist=False):
    """
    Process the data and extract grammatical information.

    Args:
        data (list): A list of sentences with grammatical information.
        src (str): Source file path, used for override lookups.
        lang (str): Language name, used for override lookups.
        is_wordlist (bool): True for A2 vocabulary-list files, where slashes
            in ori tokens are variant separators (not phonological variants
            within a single word).  Causes embedded slashes (e.g. 'icin/'
            or '/musa') to be normalised into standalone '/' tokens before
            the variant-splitting logic runs.

    Returns:
        list: A list of dicts, each containing processed data for a sentence.
    """
    to_return = []

    for s in data:
        tmp = {}
        tmp['id'] = s[0]
        s = s[1]

        if s['ori'] and s['ori'] != ['.']:
            raw_ori = [t for t in s['ori'] if not is_speaker_token(t)]
            raw_ori = [strip_prosodic_markers(t) for t in raw_ori]
            raw_ori = [t for t in raw_ori if t.strip()]

            # For word-list (A2) entries every slash — whether standalone or
            # embedded inside a token like 'icin/' or '/musa' — is a variant
            # separator.  Normalise them all to standalone '/' tokens so the
            # variant-splitting logic below handles them uniformly.
            if is_wordlist:
                normalised = []
                for tok in raw_ori:
                    if '/' in tok and tok != '/':
                        parts = tok.split('/')
                        for i, p in enumerate(parts):
                            if i > 0:
                                normalised.append('/')
                            if p:  # skip empty strings from leading/trailing slash
                                normalised.append(p)
                    else:
                        normalised.append(tok)
                raw_ori = normalised

            if '/' in raw_ori:
                # Split into variant groups separated by '/'
                variants = []
                current = []
                for token in raw_ori:
                    if token == '/':
                        if current:
                            variants.append(clean_punctuation(join_ori_tokens(current)))
                            current = []
                    else:
                        current.append(token)
                if current:
                    variants.append(clean_punctuation(join_ori_tokens(current)))
                tmp['ori'] = variants[0]
                tmp['ori_variants'] = variants
            else:
                # Strip slash-variants from individual tokens (e.g. 'saa/sua' → 'saa').
                raw_ori = [_strip_slash_variant(t) for t in raw_ori]
                # Remove *(text) / (*text) ungrammatical parentheticals before any further processing.
                raw_ori = [t for t in raw_ori if not UNGRAMMATICAL_PAREN_RE.search(t)]
                gloss_words = [g for g in s.get('gloss', [])
                               if not is_speaker_token(g[0], g[1], g[2])
                               and not UNGRAMMATICAL_PAREN_RE.search(g[0])]
                paren_toks = [t for t in raw_ori if PAREN_TOKEN_RE.match(t)]
                if paren_toks:
                    gloss_set = {_norm_paren(g[0]) for g in gloss_words}
                    editorial = [t for t in paren_toks
                                 if _norm_paren(t) not in gloss_set]
                    if editorial:
                        editorial_set = set(editorial)
                        ori_stripped = [t for t in raw_ori if t not in editorial_set]
                        tmp['ori']       = clean_punctuation(join_ori_tokens(ori_stripped))
                        tmp['ori_notes'] = clean_punctuation(" ".join(raw_ori))
                    else:
                        tmp['ori'] = clean_punctuation(join_ori_tokens(raw_ori))
                else:
                    tmp['ori'] = clean_punctuation(join_ori_tokens(raw_ori))
        else:
            tmp['ori'] = clean_origin(join_ori_tokens([strip_prosodic_markers(l[0]) for l in s['gloss']]))

        # Skip sentences marked ungrammatical anywhere: if any ori token or any
        # gloss form starts with '*', the whole sentence is ungrammatical and dropped.
        if (any(t.startswith('*') for t in s.get('ori', []))
                or any(g[0].startswith('*') for g in s.get('gloss', []) if g)):
            continue

        if s['gloss'] and s['gloss'] != [["_", "", ""]]:
            norm_gloss = []
            for w in s['gloss']:
                # Check for speaker labels on the RAW form before strip_prosodic_markers,
                # because that function strips ':' and 'A:' would become 'A', evading detection.
                if is_speaker_token(w[0], w[1] if len(w) > 1 else '', w[2] if len(w) > 2 else ''):
                    continue
                form_raw = strip_prosodic_markers(w[0])
                if not is_wordlist:
                    # Strip Chinese annotation labels embedded in form columns
                    # (e.g. 'seto]謂語' → 'seto]', '人們在喝酒。' → '').
                    form_raw = _CJK_RE.sub('', form_raw)
                if not form_raw.strip():
                    continue
                if UNGRAMMATICAL_PAREN_RE.search(form_raw):
                    continue
                form_res = _drop_starred_slash(form_raw)
                if form_res is None:
                    continue  # all slash alternatives starred — drop entry
                cols = [clean_punctuation(form_res)]
                for j in range(1, len(w)):
                    col_res = _drop_starred_slash(w[j] if j < len(w) else '')
                    cols.append(clean_punctuation(col_res if col_res is not None else ''))
                norm_gloss.append(cols)
            tmp['words'] = filter_punct_words(norm_gloss, s_id=str(tmp['id']), src=src)

        for tran in s['free']:
            if tran[:2] == "#e":
                tmp['en'] = strip_speaker_labels_from_translation(clean_punctuation(tran[2:]))
            elif tran[:2] == "#c":
                tmp['zh'] = strip_speaker_labels_from_translation(clean_punctuation(tran[2:]))

        if 'audio_url' in s:
            tmp['audio'] = s['audio_url']

        # Apply any manual overrides keyed by (lang_name, file_stem, sentence_id).
        file_stem = os.path.splitext(os.path.basename(src))[0] if src else ""
        override_key = (lang, file_stem, tmp['id'])
        if override_key in _SENTENCE_SPLIT_OVERRIDES:
            tmp['sentence_variants'] = _SENTENCE_SPLIT_OVERRIDES[override_key]
        if override_key in _FORM_OVERRIDES:
            tmp['ori'] = _FORM_OVERRIDES[override_key]

        to_return.append(tmp)

    return to_return


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(lang_codes):
    curr_dir    = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(curr_dir)
    grammar_dir = os.path.join(project_dir, "grammar")

    os.makedirs(os.path.join(project_dir, "Final_XML", "Grammar"), exist_ok=True)

    issues = os.path.join(project_dir, "Final_XML", "Grammar", "mismatch_issues.csv")
    with open(issues, mode='w', newline='') as f:
        csv.writer(f).writerow(["language", "file_name", "Sentence_id", "Formosan", "Ch"])

    for lang in os.listdir(grammar_dir):
        lang_grammar_dir = os.path.join(grammar_dir, lang)
        lang_name = lang.split('_')[0]
        _folder_dialect = lang.split('_')[1] if '_' in lang else ''
        if _folder_dialect == lang_name:
            _folder_dialect = ''
        dialect = DIALECT_NAMES.get(_folder_dialect, '')

        xml_output = os.path.join(project_dir, "Final_XML", "Grammar", lang_name)
        os.makedirs(xml_output, exist_ok=True)

        root = ET.Element("TEXT")
        root.set("id",              f"NTU_Gram_{lang_name}")
        root.set("xml:lang",        lang_codes[lang_name])
        root.set("source",          f"NTU Corpus, grammar, {lang_name}")
        root.set("audio",           "diarized")
        root.set("copyright",       "CC BY-NC")
        root.set("citation",        "Sung, L. M., Lily, I., Hsieh, F., & Lin, Z. (2008). Developing an online corpus of Formosan languages. Taiwan Journal of Linguistics, 6(2.).")
        root.set("BibTeX_citation", "@article{sung2008developing,title={Developing an online corpus of Formosan languages.},author={Sung, Li-May and Lily, I and Hsieh, Fuhui and Lin, Zhemin and others},journal={Taiwan Journal of Linguistics},volume={6},number={2},year={2008}}")
        if dialect:
            root.set("dialect", dialect)

        for file in os.listdir(lang_grammar_dir):
            full_path = os.path.join(lang_grammar_dir, file)
            with open(full_path, 'r') as js_file:
                data = json.load(js_file)
            grammar = get_grammar(data['glosses'], src=full_path, lang=lang_name,
                                   is_wordlist='A2' in file)

            for s in grammar:
                base_id = f"{file.split('.')[0]}_S_{s['id']}"

                # Entries that expand to multiple <S> with per-variant glosses.
                if 'sentence_variants' in s:
                    for vi, var in enumerate(s['sentence_variants']):
                        s_id_str = f"{base_id}{chr(ord('a') + vi)}"
                        s_element = ET.SubElement(root, "S")
                        s_element.set("id", s_id_str)
                        form_elem = ET.SubElement(s_element, "FORM")
                        form_elem.set("kindOf", "original")
                        form_elem.text = insert_xxxx_tokens(var['ori'], var.get('words', []))
                        if 'zh' in var:
                            add_transl_element(s_element, "zho", clean_punctuation(var['zh']))
                        if 'en' in var:
                            add_transl_element(s_element, "en",  clean_punctuation(var['en']))
                        fill_propername_gloss(var.get('words', []), col_zh=1, col_en=2)
                        for wi, w in enumerate(var.get('words', [])):
                            w[0], is_cs = strip_l2m(w[0])
                            if is_punct_only(w[0]):
                                continue
                            w_element = ET.SubElement(s_element, "W")
                            w_element.set("id", f"{s_id_str}_W{wi}")
                            w_f = ET.SubElement(w_element, "FORM")
                            w_f.set("kindOf", "original")
                            w_f.text = w[0]
                            if is_cs:
                                w_f.set("notes", "code-switch")
                            # W-level full gloss TRANSL (before M elements)
                            zh_full = clean_punctuation(w[1])
                            en_full = clean_punctuation(w[2] if len(w) > 2 else '')
                            if zh_full and zh_full != '_':
                                add_transl_element(w_element, "zho", zh_full)
                            if en_full and en_full != '_':
                                add_transl_element(w_element, "en", en_full)
                            m    = clean_punctuation(w[0]).split('-')
                            m_zh = clean_punctuation(w[1]).split('-')
                            m_en = clean_punctuation(w[2] if len(w) > 2 else '').split('-')
                            if len(m) != len(m_zh):
                                with open(issues, mode='a', newline='') as issues_file:
                                    csv.writer(issues_file).writerow(
                                        [lang_name, file.split('.')[0], s['id'], m, m_zh])
                            for j, (mf, me, mc) in enumerate(
                                    itertools.zip_longest(m, m_en, m_zh, fillvalue='')):
                                part_f = re.split(r'(?<!=)=(?!=)', mf) if mf else ['']
                                part_e = re.split(r'(?<!=)=(?!=)', me) if me else ['']
                                part_c = re.split(r'(?<!=)=(?!=)', mc) if mc else ['']
                                if len(part_f) != len(part_c):
                                    with open(issues, mode='a', newline='') as issues_file:
                                        csv.writer(issues_file).writerow(
                                            [lang_name, file.split('.')[0], s['id'], part_f, part_c])
                                for k, (pf, pe, pc) in enumerate(
                                        itertools.zip_longest(part_f, part_e, part_c, fillvalue='')):
                                    sub_morphemes = expand_infixes(pf, pe, pc)
                                    if len(sub_morphemes) > 1:
                                        for n, (sf, se, sc) in enumerate(sub_morphemes):
                                            m_element = ET.SubElement(w_element, "M")
                                            m_element.set("id", f"{s_id_str}_W{wi}_M{j}_{k}_{n}")
                                            m_f = ET.SubElement(m_element, "FORM")
                                            m_f.set("kindOf", "original")
                                            m_f.text = sf
                                            mzh_elem = ET.SubElement(m_element, "TRANSL")
                                            mzh_elem.set('xml:lang', 'zho')
                                            mzh_elem.text = sc
                                    else:
                                        m_element = ET.SubElement(w_element, "M")
                                        m_element.set("id", f"{s_id_str}_W{wi}_M{j}_{k}")
                                        m_f = ET.SubElement(m_element, "FORM")
                                        m_f.set("kindOf", "original")
                                        m_f.text = pf
                                        mzh_elem = ET.SubElement(m_element, "TRANSL")
                                        mzh_elem.set('xml:lang', 'zho')
                                        mzh_elem.text = pc
                        if 'audio' in s:
                            a_name = s['audio'].split('/')[-1]
                            audio_element = ET.SubElement(s_element, "AUDIO")
                            audio_element.set("file", a_name)
                            audio_element.set("url",  s['audio'])
                    continue  # skip normal processing for this sentence

                # For A2 files with slash-separated variant forms, emit one <S> per variant.
                if 'A2' in file and 'ori_variants' in s:
                    form_list = s['ori_variants']
                    id_list   = [f"{base_id}{chr(ord('a') + i)}" for i in range(len(form_list))]
                else:
                    form_list = [s['ori']]
                    id_list   = [base_id]

                for variant_form, s_id_str in zip(form_list, id_list):
                    s_element = ET.SubElement(root, "S")
                    s_element.set("id", s_id_str)

                    form_elem = ET.SubElement(s_element, "FORM")
                    form_elem.set("kindOf", "original")
                    form_elem.text = insert_xxxx_tokens(
                        variant_form,
                        s.get('words', []) if 'A2' not in file else [])
                    if 'ori_notes' in s and 'ori_variants' not in s:
                        form_elem.set("notes", s['ori_notes'])

                    if 'zh' in s:
                        add_transl_element(s_element, "zho", s['zh'])
                    if 'en' in s:
                        add_transl_element(s_element, "en", s['en'])

                    if 'A2' in file:
                        zh_gloss = clean_punctuation(s['words'][0][0]) if s.get('words') else ''
                        if zh_gloss and zh_gloss != '_':
                            add_transl_element(s_element, "zho", zh_gloss)

                    elif 'words' in s:
                        fill_propername_gloss(s['words'], col_zh=1, col_en=2)
                        for i, w in enumerate(s['words']):
                            w[0] = _strip_slash_variant(w[0])
                            w[0], is_cs = strip_l2m(w[0])
                            if is_punct_only(w[0]):
                                continue
                            w_element = ET.SubElement(s_element, "W")
                            w_element.set("id", f"{s_id_str}_W{i}")
                            w_f = ET.SubElement(w_element, "FORM")
                            w_f.set("kindOf", "original")
                            w_f.text = w[0]
                            if is_cs:
                                w_f.set("notes", "code-switch")

                            # W-level full gloss TRANSL (before M elements)
                            zh_full = clean_punctuation(w[1])
                            en_full = clean_punctuation(w[2] if len(w) > 2 else '')
                            if zh_full and zh_full != '_':
                                add_transl_element(w_element, "zho", zh_full)
                            if en_full and en_full != '_':
                                add_transl_element(w_element, "en", en_full)

                            m, m_zh = (clean_punctuation(w[0]).split('-'),
                                       clean_punctuation(w[1]).split('-'))
                            m_en = clean_punctuation(w[2] if len(w) > 2 else '').split('-')

                            if len(m) != len(m_zh):
                                with open(issues, mode='a', newline='') as issues_file:
                                    csv.writer(issues_file).writerow(
                                        [lang_name, file.split('.')[0], s['id'], m, m_zh])

                            for j, (mf, me, mc) in enumerate(
                                    itertools.zip_longest(m, m_en, m_zh, fillvalue='')):
                                part_f = re.split(r'(?<!=)=(?!=)', mf) if mf else ['']
                                part_e = re.split(r'(?<!=)=(?!=)', me) if me else ['']
                                part_c = re.split(r'(?<!=)=(?!=)', mc) if mc else ['']

                                if len(part_f) != len(part_c):
                                    with open(issues, mode='a', newline='') as issues_file:
                                        csv.writer(issues_file).writerow(
                                            [lang_name, file.split('.')[0], s['id'], part_f, part_c])

                                for k, (pf, pe, pc) in enumerate(
                                        itertools.zip_longest(part_f, part_e, part_c, fillvalue='')):
                                    sub_morphemes = expand_infixes(pf, pe, pc)
                                    if len(sub_morphemes) > 1:
                                        for n, (sf, se, sc) in enumerate(sub_morphemes):
                                            m_element = ET.SubElement(w_element, "M")
                                            m_element.set("id", f"{s_id_str}_W{i}_M{j}_{k}_{n}")
                                            m_f = ET.SubElement(m_element, "FORM")
                                            m_f.set("kindOf", "original")
                                            m_f.text = sf
                                            mzh = ET.SubElement(m_element, "TRANSL")
                                            mzh.set('xml:lang', 'zho')
                                            mzh.text = sc
                                    else:
                                        m_element = ET.SubElement(w_element, "M")
                                        m_element.set("id", f"{s_id_str}_W{i}_M{j}_{k}")
                                        m_f = ET.SubElement(m_element, "FORM")
                                        m_f.set("kindOf", "original")
                                        m_f.text = pf
                                        mzh = ET.SubElement(m_element, "TRANSL")
                                        mzh.set('xml:lang', 'zho')
                                        mzh.text = pc

                    # Record the audio URL in the XML so the downloader can find it.
                    if 'audio' in s:
                        a_name = s['audio'].split('/')[-1]
                        audio_element = ET.SubElement(s_element, "AUDIO")
                        audio_element.set("file", a_name)
                        audio_element.set("url",  s['audio'])

        try:
            xml_string = prettify(root)
        except Exception as e:
            xml_string = ""
            print(f"Error prettifying {lang_name}: {e}")

        with open(os.path.join(xml_output, f"{lang_name}.xml"), "w", encoding="utf-8") as xmlfile:
            xmlfile.write(xml_string)

        print(f"Written: Final_XML/Grammar/{lang_name}/{lang_name}.xml")


if __name__ == "__main__":
    lang_codes = {
        "Amis": "ami", "Atayal": "tay", "Saisiyat": "xsy", "Thao": "ssf", "Seediq": "trv",
        "Bunun": "bnn", "Paiwan": "pwn", "Rukai": "dru", "Truku": "trv", "Kavalan": "ckv",
        "Tsou": "tsu", "Kanakanavu": "xnb", "Saaroa": "sxr", "Puyuma": "pyu", "Yami": "tao",
        "Sakizaya": "szy"
    }
    main(lang_codes)

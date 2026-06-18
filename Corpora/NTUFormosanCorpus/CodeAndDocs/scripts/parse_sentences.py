import itertools
import json
import os
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
import csv
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import clean_punctuation, add_transl_element, SPEAKER_TOKENS, is_speaker_token, strip_speaker_labels_from_translation, PAREN_TOKEN_RE, UNGRAMMATICAL_PAREN_RE, _drop_starred_slash, filter_punct_words, is_punct_only, fill_propername_gloss, _norm_paren, join_ori_tokens, insert_xxxx_tokens, strip_l2m, strip_prosodic_markers, expand_infixes

# Maps the folder-derived dialect token to the display name used in the XML
# dialect attribute.  Languages whose folder suffix equals their language name
# (e.g. Kanakanavu_Kanakanavu) are excluded and receive no dialect attribute.
DIALECT_NAMES = {
    'Ciwkangan': 'Coastal',   # Amis
    'Mayrinax':  'Wenshui',   # Atayal
    'Isbukun':   'Junqun',    # Bunun
    'Vedai':     'Wutai',     # Rukai
    'Tgdaya':    'Tegudaya',  # Seediq
}


def prettify(elem):
    """
    Return a pretty-printed XML string for the Element.

    Args:
        elem (xml.etree.ElementTree.Element): The XML element to be pretty-printed.

    Returns:
        str: A pretty-printed XML string representation of the element.
    """
    rough_string = ET.tostring(elem, 'utf-8')  # Convert the Element to a byte string
    reparsed = minidom.parseString(rough_string)  # Parse the byte string using minidom
    # print(reparsed.toprettyxml(indent="    "))  # For debugging purposes
    return reparsed.toprettyxml(indent="    ")  # Return the pretty-printed XML string

def clean_origin(ori):
    """
    Clean the original text by removing unwanted characters.
    """

    ori = re.sub(r"<L2[A-Za-z]", "", ori) #removing code-switching tag
    ori = re.sub(r"L2[A-Za-z]>", "", ori) #removing code-switching tag
    ori = re.sub(r"[\\/^,<>@_\[\]]+", "", ori)
    ori = re.sub("==", "", ori) #remove a prosodic marker
    ori = re.sub("=", "", ori) #remove clitic boundaries
    ori = re.sub(r"\.\.\.", "", ori) #remove a marker for pauses
    ori = re.sub(r"\.\.", "", ori) #remove a marker for pauses
    ori = re.sub(r"…", "", ori) #remove a marker for pauses

    ori = re.sub("-", "", ori)
    ori = ori.replace(".", "")
    
    ori = ori.strip() #remove leading and trailing whitespace
    ori = re.sub(r'\s+', ' ', ori) #replace multiple spaces with a single space
    # Add a period only if ori does not end with a period, question mark, or exclamation mark
    if not ori.endswith(('.', '?', '!')):
        ori += "."
    
    return ori

def get_sentences(data, src=""):
    """
    Process the data and extract sentence information.

    Args:
        data (list): A list of sentences with their annotations.
        src (str): Source filename, used in warning messages.

    Returns:
        list: A list of dictionaries, each containing processed data for a sentence.
    """
    # Sentences to exclude entirely from XML output, keyed by (basename, sentence_id).
    _SENTENCE_EXCLUSIONS = {
        ("1.json", 323),   # Kanakanavu: corrupt/incomplete gloss with '…,' placeholder
    }

    # Hardcoded gloss corrections keyed by (basename, sentence_id).
    # Used when the source JSON has errors that cannot easily be fixed upstream.
    _GLOSS_OVERRIDES = {
        ("59.json", 12): [
            ["pisauk-an=ik", "salute-LF=1SG.NOM", "敬禮-處焦=1SG.主格"],
            ["mas",          "OBL",                "斜格"],
            ["Subali=cia",   "PN=DIST.OBL",        "人名=遠距.斜格"],
            ["tu",           "LNK",                "連繫詞"],
            ["laduaz=av=ang=dau", "forgive=IMP=still=EVI,", "原諒-祈使=還=知識詞"],
            ["at",           "then",               "然後"],
            ["saiv-an=ik",   "give-LF=1SG.NOM",   "給-處焦=1SG.主格"],
            ["saicia",       "3SG.GEN",            "3SG.屬格"],
            ["mas",          "OBL",                "斜格"],
            ["sui.",         "money",              "錢"],
        ],
    }

    src_basename = os.path.basename(src) if src else ""

    to_return = list()

    for s in data:
        base_id = s[0]  # The sentence ID
        s = s[1]        # The sentence data

        # Apply hardcoded gloss override if one exists for this file + sentence.
        override_key = (src_basename, base_id)
        if override_key in _SENTENCE_EXCLUSIONS:
            continue  # Skip this sentence entirely
        if override_key in _GLOSS_OVERRIDES:
            s = dict(s)
            s['gloss'] = _GLOSS_OVERRIDES[override_key]

        # Split gloss list on ["/", "", ""] separators into sub-sentence groups.
        gloss_groups = []
        current = []
        for g in s['gloss']:
            if g[0] == '/' and not g[1] and not g[2]:
                if current:
                    gloss_groups.append(current)
                current = []
            else:
                current.append(g)
        if current:
            gloss_groups.append(current)
        if not gloss_groups:
            continue

        # Split free translations on " / " to match the gloss groups.
        free_zh_parts = []
        free_en_parts = []
        for tran in s['free']:
            if tran[:2] == "#c":
                free_zh_parts = [p.strip() for p in tran[2:].split('/')]
            elif tran[:2] == "#e":
                free_en_parts = [p.strip() for p in tran[2:].split('/')]

        # Split ori tokens on "/" to match the gloss groups.
        ori_groups = []
        current_ori = []
        for tok in s.get('ori', []):
            if tok == '/':
                ori_groups.append(current_ori)
                current_ori = []
            else:
                current_ori.append(tok)
        ori_groups.append(current_ori)

        use_suffix = len(gloss_groups) > 1
        suffixes = 'abcdefghijklmnopqrstuvwxyz'

        for gi, gloss_group in enumerate(gloss_groups):
            tmp = dict()
            tmp['id'] = f"{base_id}{suffixes[gi]}" if use_suffix else base_id

            # Build ori text for this sub-sentence.
            ori_tokens_raw = ori_groups[gi] if gi < len(ori_groups) else []

            # Remove speaker labels (e.g. A:, B:) BEFORE prosodic stripping:
            # strip_prosodic_markers removes bare ':'  so 'A:' → 'A' and the
            # colon-based regex in is_speaker_token would miss it.
            ori_tokens_raw = [t for t in ori_tokens_raw if not is_speaker_token(t)]
            gloss_group = [g for g in gloss_group
                           if not is_speaker_token(g[0],
                                                   g[1] if len(g) > 1 else '',
                                                   g[2] if len(g) > 2 else '')]

            # Strip prosodic/annotation markers before any other handling so that
            # paren-wrapped markers like (H) or (0.8) don't reach the parenthesis
            # handlers and get mis-classified as editorial insertions.
            ori_tokens_raw = [strip_prosodic_markers(t) for t in ori_tokens_raw]
            ori_tokens_raw = [t for t in ori_tokens_raw if t.strip()]
            gloss_group = [[strip_prosodic_markers(g[0])] + list(g[1:]) for g in gloss_group]
            gloss_group = [g for g in gloss_group if g[0].strip()]

            # Remove *(text) / (*text) — ungrammatical parentheticals — before any further
            # processing so they never appear in the S FORM or generate a <W> element.
            gloss_group = [w for w in gloss_group
                           if not UNGRAMMATICAL_PAREN_RE.search(w[0])]
            ori_tokens = [t for t in ori_tokens_raw
                          if not UNGRAMMATICAL_PAREN_RE.search(t)]

            # Resolve word-level slash alternatives where one part is starred:
            # e.g. 'patuelre/*makanaelre' → 'patuelre', '*tu-a-/ma-auvagavagay' → 'ma-auvagavagay'.
            # Apply to both ori tokens and gloss entries so the starred alternative
            # never appears in the S FORM or as a <W> element.
            ori_tokens = [r for t in ori_tokens
                          for r in (_drop_starred_slash(t),) if r is not None]
            new_gloss_group = []
            for w in gloss_group:
                form_res = _drop_starred_slash(w[0])
                if form_res is None:
                    continue   # all slash alternatives for this word are starred — drop it
                new_w = [form_res]
                for j in range(1, len(w)):
                    col_res = _drop_starred_slash(w[j])
                    new_w.append(col_res if col_res is not None else '')
                new_gloss_group.append(new_w)
            gloss_group = new_gloss_group

            gloss_words = list(gloss_group)  # speaker labels already removed above

            if ori_tokens and ori_tokens != ['.']:
                paren_toks = [t for t in ori_tokens if PAREN_TOKEN_RE.match(t)]
                if paren_toks:
                    gloss_set = {_norm_paren(w[0]) for w in gloss_words}
                    editorial = [t for t in paren_toks
                                 if _norm_paren(t) not in gloss_set]
                    if editorial:
                        editorial_set = set(editorial)
                        ori_stripped = [t for t in ori_tokens if t not in editorial_set]
                        tmp['ori']       = clean_punctuation(join_ori_tokens(ori_stripped))
                        tmp['ori_notes'] = clean_punctuation(" ".join(ori_tokens))
                    else:
                        tmp['ori'] = clean_punctuation(join_ori_tokens(ori_tokens))
                else:
                    tmp['ori'] = clean_punctuation(join_ori_tokens(ori_tokens))
            else:
                # Reconstruct from gloss if ori not available for this group.
                tmp['ori'] = clean_origin(
                    join_ori_tokens([l[0] for l in gloss_group])
                )

            # Skip sentences marked ungrammatical anywhere: if any ori token or any
            # gloss form starts with '*', the whole sentence is ungrammatical and dropped.
            if (any(t.startswith('*') for t in ori_tokens)
                    or any(w[0].startswith('*') for w in gloss_group)):
                continue

            # Normalise punctuation (speaker labels already removed above).
            raw_words = [
                [clean_punctuation(w[0]), clean_punctuation(w[1]), clean_punctuation(w[2])]
                for w in gloss_group]
            tmp['words'] = filter_punct_words(raw_words, s_id=str(tmp['id']), src=src)
            if not tmp['words']:
                continue  # Skip sub-sentences without words

            # Assign translations, using the matching part when split.
            if free_zh_parts:
                zh = free_zh_parts[gi] if gi < len(free_zh_parts) else free_zh_parts[-1]
                tmp['zh'] = strip_speaker_labels_from_translation(zh.replace("「這是真的中文翻譯」", "").strip())
            if free_en_parts:
                en = free_en_parts[gi] if gi < len(free_en_parts) else free_en_parts[-1]
                tmp['en'] = strip_speaker_labels_from_translation(clean_punctuation(en))

            # Store all free-translation alternatives for slash-alternative expansion.
            tmp['zh_alts'] = [strip_speaker_labels_from_translation(p.replace("「這是真的中文翻譯」", "").strip()) for p in free_zh_parts]
            tmp['en_alts'] = [strip_speaker_labels_from_translation(clean_punctuation(p)) for p in free_en_parts]

            to_return.append(tmp)  # Add the processed sentence to the list

    return to_return

def _log_slash_error(slash_log_path, lang, file_name, s_id, msg):
    """Log a slash-alternative expansion error to file and stdout."""
    with open(slash_log_path, mode='a', newline='') as f:
        csv.writer(f).writerow([lang, file_name, s_id, msg])
    print(f"[SLASH ERROR] {lang} {file_name} s{s_id}: {msg}", flush=True)


def _split_slash_raw(raw):
    """Split raw string on '/' filtering trailing empty; return None if ≤1 part."""
    parts = [p for p in str(raw).split('/') if p.strip()]
    return parts if len(parts) > 1 else None


def _expand_slash_parts(parts):
    """
    Expand partial clitic/affix alternatives.
    If parts[1:] start with '=' or '-', extract the base from parts[0]
    (everything before its final '=...' or '-...' segment) and prepend it.
    Otherwise treat all parts as standalone complete alternatives.
    """
    if len(parts) <= 1:
        return parts
    if parts[1].startswith('=') or parts[1].startswith('-'):
        m = re.match(r'^(.*?)(=[^=]*)$', parts[0])
        if not m:
            m = re.match(r'^(.*?)(\-[^\-=]*)$', parts[0])
        base = m.group(1) if m else parts[0]
        return [parts[0]] + [base + p for p in parts[1:]]
    return list(parts)


def expand_sentence_alternatives(s, lang, file_name, slash_log_path):
    """
    Detect and expand slash-delimited word alternatives in a sentence dict.

    Returns:
        None            — no slash-alternatives found; process sentence normally
        []              — mismatch error detected; already logged; caller should skip
        [sv1, sv2, ...] — N expanded sentence dicts, one per alternative
    """
    # Column layout: Kanakanavu triples are [form, zh, en]; others are [form, en, zh]
    col_form, col_zh, col_en = (0, 1, 2) if lang == "Kanakanavu" else (0, 2, 1)

    words = s['words']
    N = None
    word_expansions = []   # per-word: None | list of N (form, zh, en) tuples
    error_msg = None

    for w in words:
        if len(w) < 3:
            word_expansions.append(None)
            continue

        form_raw = str(w[col_form])
        zh_raw   = str(w[col_zh])
        en_raw   = str(w[col_en])

        form_parts = _split_slash_raw(form_raw)
        if form_parts is None:
            word_expansions.append(None)
            continue

        zh_parts = _split_slash_raw(zh_raw)
        en_parts = _split_slash_raw(en_raw)
        n_form = len(form_parts)
        n_zh   = len(zh_parts) if zh_parts else 1
        n_en   = len(en_parts) if en_parts else 1

        if n_form != n_zh or n_form != n_en:
            error_msg = (f"Word '{form_raw}': form={n_form}, zh={n_zh}, "
                         f"en={n_en} alternative counts disagree")
            break

        if N is None:
            N = n_form
        elif N != n_form:
            error_msg = (f"Word '{form_raw}': {n_form} alternatives but "
                         f"expected {N} (from earlier word)")
            break

        form_exp = _expand_slash_parts(form_parts)
        zh_exp   = _expand_slash_parts(zh_parts) if zh_parts else [zh_raw] * N
        en_exp   = _expand_slash_parts(en_parts) if en_parts else [en_raw] * N
        word_expansions.append(list(zip(form_exp, zh_exp, en_exp)))

    if error_msg:
        _log_slash_error(slash_log_path, lang, file_name, s['id'], error_msg)
        return []

    if N is None:
        return None  # no slash-alternatives in this sentence

    # Validate free-translation alternative counts.
    # A count mismatch here is logged as a WARNING but does NOT cause the sentence
    # to be skipped: instead the full (rejoined) free text is used for every variant.
    zh_alts = s.get('zh_alts', [])
    en_alts = s.get('en_alts', [])
    if len(zh_alts) > 1 and len(zh_alts) != N:
        _log_slash_error(slash_log_path, lang, file_name, s['id'],
                         f"WARNING: Free zh has {len(zh_alts)} parts, expected {N}; "
                         f"using full free zh for all {N} variants")
        zh_alts = ['/'.join(zh_alts)] * N   # same full text for every variant
    if len(en_alts) > 1 and len(en_alts) != N:
        _log_slash_error(slash_log_path, lang, file_name, s['id'],
                         f"WARNING: Free en has {len(en_alts)} parts, expected {N}; "
                         f"using full free en for all {N} variants")
        en_alts = ['/'.join(en_alts)] * N

    # Build N variant sentence dicts
    suffixes = 'abcdefghijklmnopqrstuvwxyz'
    variants = []
    for alt_idx in range(N):
        new_words = []
        for w, expansion in zip(words, word_expansions):
            if expansion is None:
                new_words.append(list(w))
            else:
                f, z, e = expansion[alt_idx]
                new_w = list(w)
                new_w[col_form] = f
                new_w[col_zh]   = z
                new_w[col_en]   = e
                new_words.append(new_w)

        # Reconstruct the S-level FORM from this variant's word forms
        new_ori = clean_origin(
            join_ori_tokens([w[col_form] for w in new_words])
        )

        sv = dict(s)
        sv['id']    = f"{s['id']}_v{alt_idx + 1}"
        sv['words'] = new_words
        sv['ori']   = new_ori

        if zh_alts and len(zh_alts) == N:
            sv['zh'] = zh_alts[alt_idx]
        if en_alts and len(en_alts) == N:
            sv['en'] = en_alts[alt_idx]

        variants.append(sv)

    return variants


def main(lang_codes):
    """
    Main function to process sentence data for each language and generate XML files.

    Args:
        lang_codes (dict): A dictionary mapping language names to their ISO codes.
    """
    # Get the current directory of the script
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    # Define the directory containing sentence data
    sentence_dir = os.path.join(curr_dir, "../sentence")
    os.makedirs(os.path.join(curr_dir, "../Final_XML", "Sentences"), exist_ok=True)

    # Define the path to the issues.csv file for logging issues
    issues = os.path.join(curr_dir, "../Final_XML", "Sentences", "mismatch_issues.csv")
    

    # Create the issues.csv file and write the header row
    with open(issues, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["language", "file_name", "Sentence_id", "Formosan", "En", "Ch"])

    # Create the slash-expansion errors log
    slash_log = os.path.join(curr_dir, "../Final_XML", "Sentences", "slash_expansion_errors.csv")
    with open(slash_log, mode='w', newline='') as f:
        csv.writer(f).writerow(["language", "file_name", "sentence_id", "error"])

    # Loop over each language directory in the sentence directory
    for lang_folder in os.listdir(sentence_dir):
        lang_dir = os.path.join(sentence_dir, lang_folder)  # Full path to the language directory
        lang = lang_folder.split('_')[0]  # Extract the language name before the underscore
        _folder_dialect = lang_folder.split('_')[1] if '_' in lang_folder else ''
        if _folder_dialect == lang:
            _folder_dialect = ''
        dialect = DIALECT_NAMES.get(_folder_dialect, '')

        # Define the output directory for XML files
        xml_output = os.path.join(curr_dir, "../Final_XML", "Sentences", lang)
        os.makedirs(xml_output, exist_ok=True)  # Create the directory if it doesn't exist

        # Create the root XML element for this language
        root = ET.Element("TEXT")
        root.set("id", f"NTU_Sen_{lang}")
        root.set("xml:lang", lang_codes[lang])
        root.set("source", f"NTU Corpus, sentences, {lang}")
        root.set("copyright", "CC BY-NC")
        root.set("citation", "Sung, L. M., Lily, I., Hsieh, F., & Lin, Z. (2008). Developing an online corpus of Formosan languages. Taiwan Journal of Linguistics, 6(2).")
        root.set("BibTeX_citation", "@article{sung2008developing,title={Developing an online corpus of Formosan languages.},author={Sung, Li-May and Lily, I and Hsieh, Fuhui and Lin, Zhemin and others},journal={Taiwan Journal of Linguistics},volume={6},number={2},year={2008}}")
        if dialect:
            root.set("dialect", dialect)

        # A few source JSONs assign the same record id to two *different*
        # sentences (e.g. sentence/Bunun_Isbukun/46.json numbers its records
        # 1,2,3,3,4,...). Propagating those collisions produces duplicate S
        # (and W/M) ids in the XML. Track ids per language root and suffix
        # second-and-later occurrences with -2, -3, ... in document order.
        seen_s_ids = {}

        # Loop over each JSON file in the language directory
        for file in os.listdir(lang_dir):
            with open(os.path.join(lang_dir, file), 'r') as js_file:
                data = json.load(js_file)  # Load the JSON data
            sentences = get_sentences(data['glosses'], src=os.path.join(lang_dir, file))  # Process the glosses to get sentences

            # Loop over each sentence
            for s in sentences:
                # Detect and expand slash-delimited alternatives (Kanakanavu only).
                # Each slash-word is split into N alternative forms; the sentence is
                # emitted N times, once per alternative.  Mismatches are logged and
                # the sentence is skipped.
                if lang == "Kanakanavu":
                    _expanded = expand_sentence_alternatives(
                        s, lang, file.split('.')[0], slash_log
                    )
                    if _expanded == []:
                        continue  # error logged — skip this sentence
                    elif _expanded is not None:
                        _to_process = [
                            (v, f"{file.split('.')[0]}_S_{v['id']}")
                            for v in _expanded
                        ]
                    else:
                        _to_process = [(s, f"{file.split('.')[0]}_S_{s['id']}")]
                else:
                    _to_process = [(s, f"{file.split('.')[0]}_S_{s['id']}")]

                for s_curr, s_id_str in _to_process:
                    # Disambiguate source record-id collisions (see seen_s_ids above).
                    n_seen = seen_s_ids.get(s_id_str, 0) + 1
                    seen_s_ids[s_id_str] = n_seen
                    if n_seen > 1:
                        s_id_str = f"{s_id_str}-{n_seen}"

                    # Create an 'S' element for the sentence
                    s_element = ET.SubElement(root, "S")
                    s_element.set("id", s_id_str)

                    # Add the 'FORM' element containing the sentence text
                    form_element = ET.SubElement(s_element, "FORM")
                    form_element.set("kindOf", "original")
                    form_element.text = insert_xxxx_tokens(s_curr['ori'], s_curr['words'])
                    if 'ori_notes' in s_curr:
                        form_element.set("notes", s_curr['ori_notes'])

                    # Add the 'TRANSL' element containing the Chinese translation
                    if 'zh' in s_curr:
                        add_transl_element(s_element, "zho", s_curr['zh'])

                    # Add the 'TRANSL' element containing the English translation
                    if 'en' in s_curr:
                        add_transl_element(s_element, "en", s_curr['en'])

                    # Fill empty glosses on consecutive capitalized proper names
                    col_zh = 1 if lang == 'Kanakanavu' else 2
                    col_en = 2 if lang == 'Kanakanavu' else 1
                    fill_propername_gloss(s_curr['words'], col_zh, col_en)

                    # Loop over each word in the sentence
                    for i, w in enumerate(s_curr['words']):
                        # Strip code-switch markers before any element is created;
                        # this may expose a purely-punctuation form that filter_punct_words
                        # missed because the L2M tags contained alphanumeric characters.
                        w[0], is_cs = strip_l2m(w[0])
                        if is_punct_only(w[0]):
                            continue
                        # Create a 'W' element for the word
                        w_element = ET.SubElement(s_element, "W")
                        w_element.set("id", f"{s_id_str}_W{i}")
                        w_form = ET.SubElement(w_element, "FORM")
                        w_form.set("kindOf", "original")
                        w_form.text = w[0]
                        if is_cs:
                            w_form.set("notes", "code-switch")

                        # W-level full gloss TRANSL (before M elements)
                        if lang == "Kanakanavu":
                            zh_full = clean_punctuation(w[1])
                            en_full = clean_punctuation(w[2])
                        else:
                            zh_full = clean_punctuation(w[2])
                            en_full = clean_punctuation(w[1])
                        if zh_full and zh_full != '_':
                            add_transl_element(w_element, "zho", zh_full)
                        if en_full and en_full != '_':
                            add_transl_element(w_element, "en", en_full)

                        # Handle the special case for the 'Kanakanavu' language
                        if lang == "Kanakanavu":
                            m = clean_punctuation(w[0]).split('-')     # Morphemes
                            m_en = clean_punctuation(w[2].replace('so-called', 'so.called')).split('-')  # English glosses
                            m_zh = clean_punctuation(w[1]).split('-')  # Chinese glosses
                        else:
                            m = clean_punctuation(w[0]).split('-')     # Morphemes
                            m_en = clean_punctuation(w[1].replace('so-called', 'so.called')).split('-')  # English glosses
                            m_zh = clean_punctuation(w[2]).split('-')  # Chinese glosses

                        # Log mismatches but continue — write Ms for all sides.
                        if len(m) != len(m_en) or len(m) != len(m_zh) or len(m_zh) != len(m_en):
                            with open(issues, mode='a', newline='') as issues_file:
                                csv.writer(issues_file).writerow(
                                    [lang, file.split('.')[0], s_curr['id'], m, m_en, m_zh])

                        # Loop over each morpheme in the word
                        for j, (mf, me, mc) in enumerate(
                                itertools.zip_longest(m, m_en, m_zh, fillvalue='')):
                            part_f = re.split(r'(?<!=)=(?!=)', mf) if mf else ['']
                            part_e = re.split(r'(?<!=)=(?!=)', me) if me else ['']
                            part_c = re.split(r'(?<!=)=(?!=)', mc) if mc else ['']

                            if len(part_f) != len(part_e) or len(part_f) != len(part_c) or len(part_c) != len(part_e):
                                with open(issues, mode='a', newline='') as issues_file:
                                    csv.writer(issues_file).writerow(
                                        [lang, file.split('.')[0], s_curr['id'], part_f, part_e, part_c])

                            for k, (pf, pe, pc) in enumerate(
                                    itertools.zip_longest(part_f, part_e, part_c, fillvalue='')):
                                # Expand infixes: a form like q<n>qda yields
                                # two M elements — one for <n> and one for qqda.
                                sub_morphemes = expand_infixes(pf, pe, pc)
                                for n, (sf, se, sc) in enumerate(sub_morphemes):
                                    m_element = ET.SubElement(w_element, "M")
                                    if len(sub_morphemes) > 1:
                                        m_element.set("id", f"{s_id_str}_W{i}_M{j}_{k}_{n}")
                                    else:
                                        m_element.set("id", f"{s_id_str}_W{i}_M{j}_{k}")
                                    # Add the morpheme form
                                    m_form = ET.SubElement(m_element, "FORM")
                                    m_form.set("kindOf", "original")
                                    m_form.text = sf
                                    # Add the morpheme English translation
                                    m_trans = ET.SubElement(m_element, "TRANSL")
                                    m_trans.set('xml:lang', 'en')
                                    m_trans.text = se
                                    # Add the morpheme Chinese translation
                                    mzh_trans = ET.SubElement(m_element, "TRANSL")
                                    mzh_trans.set('xml:lang', 'zho')
                                    mzh_trans.text = sc
        # Special-case patches: extra W elements for specific sentences
        # that have an ori token with no corresponding gloss entry.
        _EXTRA_ORI_WORDS = {
            "20200530-FW-Ryan_S_35": ["iya"],
        }
        for s_element in root:
            sid = s_element.get("id", "")
            if sid in _EXTRA_ORI_WORDS:
                existing_w = [c for c in s_element if c.tag == "W"]
                next_idx = len(existing_w)
                for extra_tok in _EXTRA_ORI_WORDS[sid]:
                    extra_w = ET.SubElement(s_element, "W")
                    extra_w.set("id", f"{sid}_W{next_idx}")
                    extra_f = ET.SubElement(extra_w, "FORM")
                    extra_f.set("kindOf", "original")
                    extra_f.text = extra_tok
                    next_idx += 1

        try:
            # Generate the pretty-printed XML string
            xml_string = prettify(root)
        except Exception as e:
            print(f"Error in language {lang}, file {file}: {e}")

        # Write the XML string to a file
        with open(os.path.join(xml_output, f"{lang}.xml"), "w", encoding="utf-8") as xmlfile:
            xmlfile.write(xml_string)

if __name__ == "__main__":
    # Mapping of language names to their ISO codes
    lang_codes = {
        "Amis": "ami", "Atayal": "tay", "Saisiyat": "xsy", "Thao": "ssf", "Seediq": "trv",
        "Bunun": "bnn", "Paiwan": "pwn", "Rukai": "dru", "Truku": "trv", "Kavalan": "ckv",
        "Tsou": "tsu", "Kanakanavu": "xnb", "Saaroa": "sxr", "Puyuma": "pyu", "Yami": "tao",
        "Sakizaya": "szy"
    }
    main(lang_codes)


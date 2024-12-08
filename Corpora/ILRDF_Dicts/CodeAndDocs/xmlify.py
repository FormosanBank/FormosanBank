import os
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import pickle
import PyPDF2

def get_first_word(file_path):
    # Open the PDF
    with open(file_path, "rb") as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        # Get text from the first page
        first_page_text = pdf_reader.pages[0].extract_text()
        # Extract the first word by splitting text
        first_word = first_page_text.split()[0] if first_page_text else None
        return first_word

def prettify(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = tostring(elem, 'utf-8')  # Convert XML element to string
    reparsed = minidom.parseString(rough_string)  # Parse string for pretty formatting
    return reparsed.toprettyxml(indent="    ")  # Return formatted XML string


def getPickles(lang: str):
    # Load processed data (good and failed requests) for the specified language
    PICKLE_FOLDER = '.PickleScrapes/'
    ckpt_good, ckpt_fail = None, None

    with open(os.path.join(PICKLE_FOLDER, lang, lang + '_ckpt_END.pkl'), 'rb') as f: 
        ckpt_good = pickle.load(f)
    with open(os.path.join(PICKLE_FOLDER, lang, lang + '_fails_END.pkl'), 'rb') as f: 
        ckpt_fail = pickle.load(f)

    return ckpt_good, ckpt_fail


def handleHelper(sent):
    # Check if sentence contains all necessary keys and return its components if valid
    for key in ['Original', 'Chinese', 'File']:
        if key not in sent.keys():
            return False

    # Extract components
    audio = sent['File']
    fr_tx = sent['Original']
    zh_tx = sent['Chinese']
    return [fr_tx, zh_tx, audio]


def createElemHelp(lang, count, r):
    # Create XML element structure for a sentence entry
    s = Element('S')
    s.set('id', str(lang) + "_" + str(count))  # Set sentence ID
    count += 1

    # Create sub-elements for the sentence (FORM), translation (TRANSL), and audio link (AUDIO)
    form = SubElement(s, 'FORM')
    tl = SubElement(s, 'TRANSL')
    tl.set('xml:lang', 'zho')  # Set language for translation element
    audio = SubElement(s, 'AUDIO')

    tl.text = r[1]  # Chinese translation text
    form.text = r[0]  # Original sentence text

    # Handle case where audio is a list (take first entry)
    if isinstance(r[2], list):
        r[2] = r[2][0]
    audio.set('url', r[2]['Path'])  # Set audio URL

    return s, count, form.text


def wrapperXML(sent, root, count, seen, lang):
    # Process a sentence entry and add to XML root if not duplicate
    if (r := handleHelper(sent)):
        s, count, te = createElemHelp(lang, count, r)
        
        # Check for duplicates using memoization
        if te in seen:
            return count - 1  # Skip duplicate
        else:
            seen.add(te)
            root.append(s)  # Add new entry to XML root
    return count


def handleExplanation(expl, root, lang: str, count: int, seen):
    # 'Explanation' is the key in the dictionary for the JSON that holds example sentences
    if isinstance(expl, dict):
        if 'Sentence' not in expl.keys():
            return count, seen
        sent = expl['Sentence']

        # Process single or multiple sentence entries
        if isinstance(sent, dict):        
            count = wrapperXML(sent, root, count, seen, lang)
        elif isinstance(sent, list):
            for n in sent:
                count = wrapperXML(n, root, count, seen, lang)

    elif isinstance(expl, list):
        for explan in expl:
            if 'Sentence' not in explan.keys(): 
                continue
            sent = explan['Sentence']

            if isinstance(sent, dict):        
                count = wrapperXML(sent, root, count, seen, lang)
            elif isinstance(sent, list):
                for n in sent:
                    count = wrapperXML(n, root, count, seen, lang)
    return count, seen


def makeLists(lang: str) -> tuple[list, list, list]:
    # Separate good and bad words based on pickle data and categorize sentences
    all, bad = getPickles(lang)
    goodwords = [q for q, w in all.items() if w != 'FAIL']
    assert len(goodwords) + len(bad) == len(all)  # Check data integrity

    singles, multi = [], []
    for w in goodwords:
        query = all[w]
        if isinstance(query, list):
            multi.append(query)  # Multiple sentences for a word
        elif isinstance(query, dict):
            singles.append(query)  # Single sentence for a word

    return goodwords, singles, multi


def xmlify_main():
    # Main function to process languages and generate XML files
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    lang_codes = {
        "Amis": "ami", "Atayal": "tay", "Saisiyat": "xsy", "Thao": "ssf", "Seediq": "trv", "Bunun": "bnn",
        "Paiwan": "pwn", "Rukai": "dru", "Truku": "trv", "Kavalan": "ckv", "Tsou": "tsu", "Kanakanavu": "xnb",
        "Saaroa": "sxr", "Puyuma": "pyu", "Yami": "tao", "Sakizaya": "szy"
    }
    
    for lang in lang_codes:
        # Initialize XML root element for the language
        ch = get_first_word(os.path.join(curr_dir, "dicts", f"{lang}.pdf"))
        citation = f"Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). 原住民族語言線上辭典: {ch} [Indigenous Languages Online Dictionary: {lang} language]. Executing Institution: National Taiwan Normal University. https://e-dictionary.ilrdf.org.tw/."
        BibTex = f"@misc{{ILRDF_{lang}, author = {{{{Council of Indigenous Peoples}} and {{Indigenous Languages Research and Development Foundation}}}}, title = {{原住民族語言線上辭典: {ch} [Indigenous Languages Online Dictionary: {lang} language]}}, year = {{2024}}, month = {{January}}, note = {{Executing Institution: National Taiwan Normal University}}, url = {{https://e-dictionary.ilrdf.org.tw/}}}}"

        root = Element("TEXT")
        root.set("id", f"ILRDF_Dicts_{lang}")
        root.set("xml:lang", lang_codes[lang])
        root.set("source", "Indigenous Languages Research and Development Foundation Dictionaries")
        root.set("audio", "diarized")
        root.set("copyright", "CC-BY-NC")
        root.set("citation", citation)
        root.set("BibTeX_citation", BibTex)

        # Generate lists and initialize variables for counting and duplicate detection
        gw, singles, multis = makeLists(lang)
        count, seen = 0, set()

        # Process single and multiple sentence entries
        for w in singles:
            if 'Explanation' in w.keys():
                count, seen = handleExplanation(w['Explanation'], root, lang, count, seen)

        for entry in multis:
            for w in entry:
                if 'Explanation' in w.keys():
                    count, seen = handleExplanation(w['Explanation'], root, lang, count, seen)

        # Log processing results
        g, f = getPickles(lang)
        g = len(g)
        print(f"{lang[0:6]}\t{g}\t{count}\t{g - count}")

        # Convert XML structure to a formatted string
        xml_string = prettify(root)

        # Create output path and write XML file
        output = os.path.join(curr_dir, 'Final_XML')
        if not os.path.exists(output):
            os.mkdir(output)
        
        os.makedirs(os.path.join(output, lang), exist_ok=True)
        lang_output = os.path.join(output, lang, f"{lang}.xml")
        with open(lang_output, 'w', encoding='utf-8') as file:
            file.write(xml_string)


if __name__ == "__main__":
    xmlify_main()

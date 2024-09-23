import xml.etree.ElementTree as ET
import os
import glob

def count_words_in_lang(dir_path):
    # Get a list of all folders in the directory
    folders = os.listdir(dir_path)
    lang_total = 0
    type_set = set()
    for folder in folders:
        if folder.startswith('.'):
            continue
        num_words = 0
        # Process each XML file
        xml_files = glob.glob(os.path.join(dir_path, folder, '**/*.xml'), recursive=True)
        for file_path in xml_files:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Iterate over all <S> elements
            for s in root.findall('.//S'):
                # Find the <FORM> element within the <S> element
                form = s.find('FORM')

                if form is not None and form.text is not None:
                    # Split the text of the <FORM> element into words
                    words = form.text.split()
                    type_set.update(words)
                    # Count the number of words
                    num_words += len(words)
        lang_total += num_words
        print(f'{folder}: {num_words} words')
    return lang_total, len(type_set)


xml_dir = "../XML_Final"
langs = os.listdir(xml_dir)

token_count = dict()
type_count = dict()

for lang in langs:
    if lang.startswith("."):
        continue
    lang_dir = os.path.join(xml_dir, lang)
    print(f"\n====={lang}======")
    token_count[lang], type_count[lang] = count_words_in_lang(lang_dir)

token_total = sum(token_count.values())
type_total = sum(type_count.values())

print("\n=====token count per language======")
print(token_count)
print("\n=====token count across languages======")
print(token_total)
print("\n=====type count per language======")
print(type_count)
print("\n=====type count across languages======")
print(type_total)
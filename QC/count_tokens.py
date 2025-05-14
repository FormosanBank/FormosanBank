import xml.etree.ElementTree as ET
import os
import argparse
from collections import defaultdict
# Determine the language of the file based on the path
def get_lang(path, file, langs):
    for lang in langs:
        if lang in path or (file.split('.')[0] == lang and file.split('.')[1:] == ['xml']):
            return lang


def read_file(file_path):

    num_words = 0
    tree = ET.parse(file_path)
    root = tree.getroot()
    if "dialect" in root.attrib:
        dialect = root.attrib['dialect']
    else:
        dialect = None
    # Iterate over all <S> elements
    for s in root.findall('.//S'):
        # Find the <FORM> element within the <S> element
        form = s.find('FORM')

        if form is not None and form.text is not None:
            # Split the text of the <FORM> element into words
            words = form.text.split()
            # Count the number of words
            num_words += len(words)

    return num_words, dialect

def count_source(path, tokens_by_lang, langs):
    source_total = 0
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".xml") and 'XML' in os.path.join(root, file):
                # print(root, file)
                lang = get_lang(root, file, langs)
                tokens_in_file, dialect = read_file(os.path.join(root, file))
                if dialect:
                    tokens_by_lang[lang][1][dialect] += tokens_in_file
                else:
                    tokens_by_lang[lang][1]['Not Specified'] += tokens_in_file
                tokens_by_lang[lang][0] += tokens_in_file
                source_total += tokens_in_file
    return source_total
    
    

def get_counts(corpora_path):
    
    langs = ['Amis', 'Atayal', 'Paiwan', 'Bunun','Puyuma', 'Rukai', 'Tsou', 'Saisiyat', 'Yami',
        'Thao', 'Kavalan', 'Truku', 'Sakizaya','Seediq','Saaroa', 'Kanakanavu', 'Siraya']

    tokens_by_lang = {lang: [0, defaultdict(int)] for lang in langs}
    tokens_by_source = dict()
    for source in os.listdir(corpora_path):
        if source.startswith('.'):
            continue
        if source  == 'Siraya_Gospels':
            continue
        tokens_by_source[source] = 0
        #print(f"\n=====counting in {source}======")
        tokens_by_source[source] = count_source(os.path.join(corpora_path, source), tokens_by_lang, langs)

    return tokens_by_lang, tokens_by_source
def main(corpora_path):

    tokens_by_lang, tokens_by_source = get_counts(corpora_path)
    #for lang in tokens_by_lang:
        #print(lang, ": ", tokens_by_lang[lang], "\n\n")
    #print("\n=====tokens count per language======")
    print(tokens_by_lang)
    #print("\n=====tokens count per source======")
    #print(tokens_by_source)
    #print("\n=====tokens total count======")
    #print(sum(tokens_by_source.values()))


    # with open('current_counts.txt', 'w') as file:
    #     json.dump(token_count, file)
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="count tokens per corpus and per language.")
    parser.add_argument('corpora_path', help='Specify the path of the corpora')
    args = parser.parse_args()
    main(args.corpora_path)

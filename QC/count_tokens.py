import xml.etree.ElementTree as ET
import os
import glob
import json


def read_file(file_path):

    num_words = 0
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    # Iterate over all <S> elements
    for s in root.findall('.//S'):
        # Find the <FORM> element within the <S> element
        form = s.find('FORM')

        if form is not None and form.text is not None:
            # Split the text of the <FORM> element into words
            words = form.text.split()
            # Count the number of words
            num_words += len(words)

    return num_words

def count_source(path, tokens_by_lang):
    source_total = 0
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".xml"):
                lang = os.path.join(root, file).split("/")[-2]
                tokens_in_file = read_file(os.path.join(root, file))
                tokens_by_lang[lang] += tokens_in_file
                source_total += tokens_in_file
    return source_total
    
    

def get_counts():
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    corpora = os.path.join(curr_dir, "..", "Corpora")
    langs = ['Amis', 'Atayal', 'Paiwan', 'Bunun','Puyuma', 'Rukai', 'Tsou', 'Saisiyat', 'Yami',
        'Thao', 'Kavalan', 'Truku', 'Sakizaya','Seediq','Saaroa', 'Kanakanavu']

    tokens_by_lang = {lang: 0 for lang in langs}
    tokens_by_source = dict()
    for source in os.listdir(corpora):
        tokens_by_source[source] = 0
        print(f"\n=====counting in {source}======")
        tokens_by_source[source] = count_source(os.path.join(corpora, source), tokens_by_lang)

    return tokens_by_lang, tokens_by_source
def main():

    tokens_by_lang, tokens_by_source = get_counts()

    print("\n=====tokens count per language======")
    print(tokens_by_lang)
    print("\n=====tokens count per source======")
    print(tokens_by_source)
    print("\n=====tokens total count======")
    print(sum(tokens_by_source.values()), sum(tokens_by_lang.values()))


    # with open('current_counts.txt', 'w') as file:
    #     json.dump(token_count, file)
if __name__ == "__main__":
    main()

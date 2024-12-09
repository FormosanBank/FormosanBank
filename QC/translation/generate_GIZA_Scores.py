import os
import xml.etree.ElementTree as ET
from sacremoses import MosesTokenizer
import pickle

def read_files(to_check):
    to_return = list()
    namespace = {'xml': 'http://www.w3.org/XML/1998/namespace'}
    # Iterate over all <S> elements
    for file, file_path in to_check:
        tree = ET.parse(file_path)
        root = tree.getroot()

        for s in root.findall('.//S'):
            # Find the <FORM> element within the <S> element
            s_id = s.get('id')
            form = s.find('FORM').text
            en_trans = s.find('TRANSL[@xml:lang="en"]', namespaces=namespace).text
            zh_trans = s.find('TRANSL[@xml:lang="zh"]', namespaces=namespace).text
            to_return.append([file, file_path, s_id, form, en_trans, zh_trans])
    
    return to_return
            
def tokenize(data, corpus):
    source_tokenizer = MosesTokenizer(lang="en")  # Replace "en" with source language code if different
    english_tokenizer = MosesTokenizer(lang="en")
    chinese_tokenizer = MosesTokenizer(lang="zh")

    source_sentences_tokenized = []
    english_sentences_tokenized = []
    chinese_sentences_tokenized = []
    metadata = []

    for entry in data:
        file_name, file_path, s_id, source_sent, english_trans, chinese_trans = entry
        # Tokenize sentences
        source_tokenized = source_tokenizer.tokenize(source_sent)
        english_tokenized = english_tokenizer.tokenize(english_trans)
        chinese_tokenized = chinese_tokenizer.tokenize(chinese_trans)
        metadata.append({"corpus":corpus, "file_name":file_name, "file_path":file_path, "s_id": s_id,
                         "tokenized_sent": " ".join(source_tokenized), "tokenized_trans": " ".join(english_tokenized)})
        
        # Join tokens back into strings
        source_sentences_tokenized.append(" ".join(source_tokenized))
        english_sentences_tokenized.append(" ".join(english_tokenized))
        chinese_sentences_tokenized.append(" ".join(chinese_tokenized))
    
    with open("tmp/source_tokenized.txt", "w", encoding="utf-8") as src_file:
        src_file.write("\n".join(source_sentences_tokenized))

    with open("tmp/target_en_tokenized.txt", "w", encoding="utf-8") as en_file:
        en_file.write("\n".join(english_sentences_tokenized))

    with open("tmp/target_zh_tokenized.txt", "w", encoding="utf-8") as zh_file:
        zh_file.write("\n".join(chinese_sentences_tokenized))
    
    return metadata


def parse_giza_output(giza_file, metadata):
    alignments = []
    with open(giza_file, "r") as file:
        lines = file.readlines()
    
    for i in range(0, len(lines), 3):  # GIZA++ output is grouped in 3-line blocks
        metadata_entry = metadata[i // 3]
        meta = lines[i].strip()
        alignment_data = lines[i + 2].strip()
        score = meta.split()[-1]  # Extract the alignment score
        metadata_entry["giza_score"] = score
        metadata_entry["giza_sent"] = alignment_data
        alignments.append(metadata_entry)
    return alignments

def main(corpus_path, lang):
    corpus_path = os.path.join(corpus_path, "Final_XML")
    to_check = list()
    for root, dirs, files in os.walk(corpus_path):
        for file in files:
            if file.endswith(".xml") and lang in os.path.join(root, file):
                to_check.append((file, os.path.join(root, file)))
    
    data = read_files(to_check)
    metadata = tokenize(data, "Presidential_Apologies")
    alignments = parse_giza_output("tmp/alignments_en.AA3.final", metadata)
    print(alignments[0])
    with open("tmp/alignement_results.pkl", mode="wb") as pfile:
        pickle.dump(alignments, pfile)

if __name__ == "__main__":
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    main(os.path.join(curr_dir, "..", "..", "..", "Presidential_Apologies"), "Amis")
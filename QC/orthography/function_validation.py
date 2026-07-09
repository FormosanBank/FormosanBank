import json
import argparse
import math
import os
from typing import Counter
import random
import string
import numpy as np


from language_clustering import get_language_from_file, load_file
from orthography_extract import remove_chinese_characters

IN_SCOPE_LANGS = ["ami", "tay", "bnn", "pwn", "pyu", "dru", "trv"]
CORPORA_PATH = "Corpora/"
WEIGHTS_PATH = "test_results/corpora_validation/optimal_weights.json"
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
IN_SCOPE_NAMES = {ISO_TO_LANGUAGE[iso] for iso in IN_SCOPE_LANGS}

def get_function_weights_from_results(results_file=WEIGHTS_PATH):
    """
    Reads the function validation results from a JSON file and returns a dictionary of the function weights.
    """
    with open(results_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # Extract function weights
    function_weights = results.get("optimal_weights", {})
    
    return function_weights

def get_documnent_texts(lang, corpora_path=CORPORA_PATH):
    """
    Retrieves the document texts for a given language from the corpora.
    """
    document_texts = {}
    document_languages = {}
    for corpus in sorted(os.listdir(corpora_path)):
            corpus_path = os.path.join(corpora_path, corpus + "/XML/")
            if os.path.isdir(corpus_path):
                print(f"Processing corpus: {corpus}")
                # Recursively find all XML files
                for root, dirs, files in os.walk(corpus_path):
                    for file in files:
                        if file.endswith(".xml"):
                            document_path = os.path.join(root, file)
                        document_path = os.path.join(root, file)
                        try:
                            text = load_file(document_path)
                            if text:
                                language = get_language_from_file(document_path)
                                if language not in IN_SCOPE_LANGS or (lang != 'all' and language != lang):
                                    continue
                                print(f"  Found XML file: {document_path}")
                                text = remove_chinese_characters(text)
                                document_texts[document_path] = text
                                if lang == 'all':
                                    document_languages[document_path] = language
                                else:
                                    document_languages[document_path] = lang
                        except Exception as e:
                            print(f"  Error processing {document_path}: {e}")
    return document_texts, document_languages

def get_unique_chars(lang):
    tsv_path = f"Orthographies/Ortho113/{ISO_TO_LANGUAGE[lang]}.tsv"
    unique_chars = set()
    with open(tsv_path, 'r', encoding='utf-8') as f:
        for line in f:
            for char in line.strip():
                unique_chars.add(char)
    return unique_chars

def perturb_text(text, lang, perturbation_level=0.5):
    """
    Perturbs the input text by randomly replacing a percentage of characters with random characters.
    """

    num_chars_to_perturb = int(len(text) * perturbation_level)
    text_list = list(text)
    unique_chars = get_unique_chars(lang)
    
    perturbed_indices = set()
    for _ in range(num_chars_to_perturb):
        index_to_perturb = random.randint(0, len(text_list) - 1)    
        while index_to_perturb in perturbed_indices:
            index_to_perturb = random.randint(0, len(text_list) - 1)
        random_char = random.choice(list(unique_chars.difference(set(string.punctuation))))
        text_list[index_to_perturb] = random_char
        perturbed_indices.add(index_to_perturb)
    
    return ''.join(text_list)

# def corpus_with_holdout(documents, languages, holdout_path, lang):
#     """
#     Creates a holdout set for a given corpus and language.
#     """
#     holdout_documents = {}
    
#     for document_path, document_lang in languages.items():
#         if document_lang == lang and holdout_path != document_path:
#             holdout_documents[document_path] = documents[document_path]
    
#     return "".join(holdout_documents.values())

def kl_divergence(p_counts, q_counts):
    """
    Computes the Kullback-Leibler divergence between two distributions represented by their counts.
    """
    p_total = sum(p_counts.values())
    q_total = sum(q_counts.values())
    
    kl_div = 0.0
    for char in p_counts:
        p_prob = p_counts[char] / p_total
        q_prob = q_counts[char] / q_total if q_counts[char] > 0 else 1e-10  # Avoid division by zero
        kl_div += p_prob * math.log(p_prob / q_prob)
    
    return kl_div

def get_char_grams(text):
    """
    Computes the frequency of unigrams, bigrams, and trigrams in the given text.
    """
    unigrams = Counter(text)
    bigrams = Counter(zip(text, text[1:]))
    trigrams = Counter(zip(text, text[1:], text[2:]))

    return [unigrams, bigrams, trigrams]

def get_word_unigrams(text):
    """
    Computes the frequency of word unigrams in the given text.
    """
    words = text.split()
    word_unigrams = Counter(words)
    return word_unigrams

def main(args):
    lang = args.lang
    weights = get_function_weights_from_results()
    print("Function weights:", weights)
    print(f"Perturbation level: {args.perturb_level}")

    document_texts, document_languages = get_documnent_texts(lang)
    print(f"Retrieved {len(document_texts)} documents for language '{lang}'.")

    reference_texts = {}
    for language in set(document_languages.values()):
        reference_texts[language] = []
        for document_path, doc_lang in document_languages.items():
            if doc_lang == language:
                reference_texts[language].append(document_texts[document_path])

    prev_holdout_path = {}
    holdout_corpus = {}
    num_correct = 0
    incorrect_pred_diffs = []
    incorrect_kl_divs_from_holdout = []
    for i in range(len(document_languages)):
        holdout_path = list(document_languages.keys())[i]
        holdout_lang = document_languages[holdout_path]
        holdout_text = document_texts[holdout_path]
        if holdout_lang not in holdout_corpus:
            holdout_corpus[holdout_lang] = {document_path: document_texts[document_path] \
                                            for document_path, doc_lang in document_languages.items() if doc_lang == holdout_lang}
        
        # Remove the current holdout from the corpus
        if holdout_path in holdout_corpus[holdout_lang]:
            holdout_corpus[holdout_lang].pop(holdout_path)
        
        holdout_corpus_text = "".join(holdout_corpus[holdout_lang].values())
        perturbed_text = perturb_text(holdout_text, holdout_lang, args.perturb_level)

        hc_grams = get_char_grams(holdout_corpus_text)
        p_grams = get_char_grams(perturbed_text)
        h_grams = get_char_grams(holdout_text)

        hc_grams.append(get_word_unigrams(holdout_corpus_text))
        p_grams.append(get_word_unigrams(perturbed_text))
        h_grams.append(get_word_unigrams(holdout_text))

        kl_divs_p = [kl_divergence(hc, p) for hc, p in zip(hc_grams, p_grams)]
        kl_divs_h = [kl_divergence(hc, h) for hc, h in zip(hc_grams, h_grams)]

        print(f"Holdout document: {holdout_path}, Language: {holdout_lang}")
        print(f"KL Divergence (Holdout Corpus vs Perturbed): {kl_divs_p}")
        print(f"KL Divergence (Holdout Corpus vs Holdout): {kl_divs_h}")
        print(f"Prediction Comparison:")
        h_pred = sum(w * kl for w, kl in zip(weights.values(), kl_divs_h))
        p_pred = sum(w * kl for w, kl in zip(weights.values(), kl_divs_p))
        print(f"  Holdout Prediction: {h_pred}")
        print(f"  Perturbed Prediction: {p_pred}")

        if h_pred < p_pred:
            num_correct += 1
        else:
            incorrect_pred_diffs.append(abs(h_pred - p_pred))
            kl_divs = [kl_divergence(h, p) for h, p in zip(h_grams, p_grams)]
            incorrect_kl_divs_from_holdout.append(kl_divs)

        holdout_corpus[holdout_lang][holdout_path] = holdout_text

    
    print(f"Number of correct predictions: {num_correct} out of {len(document_languages)} or {num_correct / len(document_languages) * 100:.2f}%")
    print(f"Average difference for incorrect predictions: {np.mean(incorrect_pred_diffs) if len(incorrect_pred_diffs) > 0 else 0:.4f}")
    print(f"Average KL divergences between original and perturbed for incorrect predictions: {np.mean(incorrect_kl_divs_from_holdout, axis=0) if len(incorrect_kl_divs_from_holdout) > 0 else [0]*4}")
    return num_correct

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get function weights from validation results.")
    parser.add_argument('--lang', type=str, help="Language code for the validation results. 'all' for all languages.", default='all')
    parser.add_argument('--perturb_level', type=float, help="Perturbation level for text perturbation (between 0 and 1).", default=0.5)
    args = parser.parse_args()

    if args.lang != 'all' and args.lang not in IN_SCOPE_LANGS:
        raise ValueError(f"Language '{args.lang}' is not in the list of in-scope languages: {IN_SCOPE_LANGS}")
    main(args)
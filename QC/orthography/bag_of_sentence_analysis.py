from orthography_extract import generate_corpus, extract_orthographic_info, is_dialect
from orthography_compare import jaccard_similarity, overlap_coefficient, normalize_vector, cosine_similarity, euclidean, kl_divergence, vis_diff
import numpy as np
import random
import re
import math
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

'''
This script is meant to test possible reference corpora (per specified dialect) by comparing relevant statistics between different aspects of a random partition multiple times.
The preference would be for the partitions to be similar/representative of each other in as many partitions as possible. It is required to run this script from "FormosanBank/"
'''

plt.switch_backend('Agg')  # Use a non-GUI backend
# plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']



# INVARIANT: args input is validated
def main(args):
    corpora_folder = "Corpora/" # change this if corora folder is different
    corpora_subfolder_names = ["ePark/", "ILRDF_Dicts/", "Paiwan_Stories/", "NTUFormosanCorpus/"]
    corpora_paths = [corpora_folder + directory for directory in corpora_subfolder_names] # names of folders with desired corpora
    # test_path = args.path
    lang = args.lang
    dialect = args.dialect
    # TBD save functionality for analyisi (JSON?)
    # save = False if not args.save else args.save

    # generate corpus from directory (or directories) looking for a specific dialect
    # note that generate_corpus when set to standard does not handle cases where the original is the same as the standard, since in those cases standard is ommitted
    # TBD: Change generate_corpus to handle "original" text that matches our standardization when looking for "standard"

    dialect_corpus = ""
    for path in corpora_paths:
        corpus = generate_corpus(lang, path, "standard", by_dialect=True) # output is a dictionary where the keys are the dialect and the values are the totality of text for that dialect as a string
        if dialect in corpus.keys():
            dialect_corpus += corpus[dialect] 

    # TBD: Verify whether the following line handles all pssible punctuation in Formosan languages

    sentences = re.split(r'(?<=[.!?])\s+', dialect_corpus) # regex for looking only at punctuation at end of sentence, if you would like to consider the following character, you can use (?<=[.!?])\s+(?=[A-Z]) instead

    # you can certainly change the following values to be in args but for ease of use they are not; manually change the these values if needed

    num_sim = 5 # number of simulations
    ref_ratio = 0.8 # the percentage of the partition to be used as the "reference" corpus

    # for num_sim times, split the corpus into reference corpus and target corpus, comparing them both
    for sim in range(num_sim):
        print(f"The following is for partition {sim + 1}:")
        # partitions the sentences before we sample from them
        ref = random.sample(sentences, math.ceil(ref_ratio * len(sentences)))
        target = [sentence for sentence in sentences if sentence not in ref]

        # recombine the sentences into one string of text
        ref_text = "".join(ref)
        target_text = "".join(target)

        ref_info = extract_orthographic_info(ref_text)
        target_info = extract_orthographic_info(target_text)

        # the following code is copied from orthography_compare.py with minor edits to pathing and more documentation

        # calculating jaccard similarity
        char_jaccard_similarity = jaccard_similarity(set(ref_info['unique_characters']), set(target_info['unique_characters']))
        print(f"Jaccard Similarity of unique characters: {char_jaccard_similarity:.2f}")

        # calculating overlap
        char_overlap_coefficient = overlap_coefficient(set(ref_info['unique_characters']), set(target_info['unique_characters']))
        print(f"Overlap Coefficient of unique characters: {char_overlap_coefficient:.2f}")

        # set of characters that appear in both corpus, which is all characters in the original corpus before being partitioned
        all_chars = set(ref_info['unique_characters']).union(set(target_info['unique_characters']))

        # create and normalize frequency vectors for the characters
        c1_freq_vector = np.array([ref_info['character_frequency'].get(char, 0) for char in all_chars])
        c2_freq_vector = np.array([target_info['character_frequency'].get(char, 0) for char in all_chars])
        c1_freq_vector = normalize_vector(c1_freq_vector)
        c2_freq_vector = normalize_vector(c2_freq_vector)

        # calculating cosine similarity
        cosine_sim = cosine_similarity([c1_freq_vector], [c2_freq_vector])[0][0]
        print(f"Cosine Similarity of character frequencies: {cosine_sim:.2f}")

        # calculating euclidean distance
        euclidean_dist = euclidean(c1_freq_vector, c2_freq_vector)
        print(f"Euclidean Distance of character frequencies: {euclidean_dist:.2f}")

        # calculating kl divergence
        kl_div = kl_divergence(c1_freq_vector, c2_freq_vector)
        print(f"KL Divergence of character frequencies: {kl_div:.2f}")

        # calculating bigram statistics
        c1_bigrams = ref_info['2-grams']
        c2_bigrams = target_info['2-grams']

        # Create a set of all bigrams
        all_bigrams = set(c1_bigrams.keys()).union(set(c2_bigrams.keys()))

        c1_bigram_vector = np.array([c1_bigrams.get(bigram, 0) for bigram in all_bigrams])
        c2_bigram_vector = np.array([c2_bigrams.get(bigram, 0) for bigram in all_bigrams])
        # Normalize and compute similarity measures as before
        c1_bigram_vector = normalize_vector(c1_bigram_vector)
        c2_bigram_vector = normalize_vector(c2_bigram_vector)

        # compute cosine similarity for bigrams
        bigram_cosine_sim = cosine_similarity([c1_bigram_vector], [c2_bigram_vector])[0][0]
        print(f"Cosine Similarity of bigram frequencies: {bigram_cosine_sim:.2f}")

        # calculating bigram Euclidean distance
        bigram_euclidean_dist = euclidean(c1_bigram_vector, c2_bigram_vector)
        print(f"Euclidean Distance of bigram frequencies: {bigram_euclidean_dist:.2f}")

        vis_diff(all_chars, ref_info['character_frequency'], target_info['character_frequency'], "reference", "target", "QC/orthography", lang + "_" + dialect + "_" +  str(sim + 1))
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare Partitions of a Corpora")
    # parser.add_argument('--path', help='path of the corpus you would like to analyze')
    parser.add_argument('--lang', help='name of the language you are analyzing the dialect of')
    parser.add_argument('--dialect', help='the target dialect of the text you are analyzing')

    args = parser.parse_args()

    # reading from the csv would better support changes in recognized langauge/dialect
    dialect_csv = pd.read_csv("dialects.csv")

    # ensure the path exists
    # if not args.path:
    #     parser.error("No corpora path provided")
    # # corpus should be in the "Corpora" directory, technically only checks if the path has "Corpora" in it at any point
    # elif "Corpora" not in Path(args.path).parts:
    #     parser.error("Target corpus is not in \"Corpora\" directory")
    if args.lang not in dialect_csv['Language'].unique():
        parser.error("Target language not recognized list of langauges. Verify your spelling and capitalization of first letter")
    # TBD: change this to include dialects that are in OtherNames
    elif not is_dialect(args.lang, args.dialect):
        parser.error("Target dialect not recognized for target language. Verify your spelling and capitalization of first letter")

    main(args)
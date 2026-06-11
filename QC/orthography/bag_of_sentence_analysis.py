from orthography_extract import generate_corpus, extract_orthographic_info, is_dialect, remove_chinese_characters
from orthography_compare import jaccard_similarity, overlap_coefficient, normalize_vector, cosine_similarity, euclidean, kl_divergence, vis_diff
import numpy as np
import random
import re
import math
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import string
from collections import Counter
import os
from scipy.spatial.distance import jensenshannon
'''
This script is meant to test possible reference corpora (per specified dialect) by comparing relevant statistics between different aspects of a random partition multiple times.
The preference would be for the partitions to be similar/representative of each other in as many partitions as possible. It is required to run this script from "FormosanBank/"
'''

plt.switch_backend('Agg')  # Use a non-GUI backend
# plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']

# determine if the language provided is officially recognized. Note that the first letter should be capitalized
def is_lang(lang):
    # reading from the csv would better support changes in recognized langauge/dialect
    dialect_csv = pd.read_csv("dialects.csv")
    return lang in dialect_csv['Language'].unique()


# Visualization for word level n-grams. Only meant for unigrams but should be compatible with arbitrary n. Focuses on the first {limit} n-grams with the corpora combined
def w_vis_diff(ref_freq: Counter, target_freq: Counter, logs_dir, ref_name="reference", target_name="target", limit=20):
    output_path = logs_dir
    os.makedirs(output_path, exist_ok=True)

    total_counter = ref_freq + target_freq
    total_counts_sorted = total_counter.most_common()
    top_limit_gram_counts = total_counts_sorted[:limit]
    top_limit_grams = [g for g, c in top_limit_gram_counts] # list of the top limit grams without counts listed
    gram_length = len(top_limit_grams[0])

    # Compute the total number of words in each corpus
    total_ref_grams = ref_freq.total()
    total_target_grams = target_freq.total()

    # Get the sorted list of words
    # sorted_grams = sorted(all_n_grams)

    # since we add 1 to each count for all grams, we add |V| grams as a result, and for relative probability we remove the extra count we added (-1)
    ref_rel_freqs = [
    np.log((ref_freq[gram] + 1) / (total_ref_grams - ref_freq[gram] + len(total_counter) - 1))
    for gram in top_limit_grams
    ]
    target_rel_freqs = [
        np.log((target_freq[gram] + 1) / (total_target_grams + len(total_counter) - 1))
        for gram in top_limit_grams
    ]

    # for absolute probability, we add an additional count of every n-gram, so we have |V| additional n-grams in conjunction with the original corpus
    ref_abs_freqs = [
    np.log((ref_freq[gram] + 1) / (total_ref_grams + len(total_counter)))
    for gram in top_limit_grams
    ]
    target_abs_freqs = [
        np.log((target_freq[gram] + 1) / (total_target_grams - target_freq[gram] + len(total_counter)))
        for gram in top_limit_grams
    ]

    # Plotting
    x = np.arange(limit)  # label locations
    width = 0.35  # width of the bars

    fig, ax = plt.subplots(figsize=(15, 5))

    rects1 = ax.bar(
    x - width / 2,
    [freq if freq is not None else 0 for freq in ref_rel_freqs],  # Replace `None` with 0 for plotting (does not happen anymore)
    width,
    label=ref_name,
    alpha=0.7)

    rects2 = ax.bar(
        x + width / 2,
        [freq if freq is not None else 0 for freq in target_rel_freqs],  # Replace `None` with 0 for plotting (does not happen anymore)
        width,
        label=target_name,
        alpha=0.7)

    # Add labels and title
    ax.set_ylabel('Relative Frequency on log-odds scale')
    ax.set_title(f'{gram_length}-Gram Relative Frequencies in {ref_name} and {target_name}')
    ax.set_xticks(x)
    ax.set_xticklabels(top_limit_grams)
    ax.legend(loc=3)
    print(ref_name, target_name)
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(os.path.join(output_path, f'{gram_length}_gram_rel_frequency_comparison_{ref_name}_{target_name}.png'))
    plt.close()

    fig, ax = plt.subplots(figsize=(15, 5))

    rects1 = ax.bar(
    x - width / 2,
    [freq if freq is not None else 0 for freq in ref_abs_freqs],  # Replace `None` with 0 for plotting (does not happen anymore)
    width,
    label=ref_name,
    alpha=0.7)

    rects2 = ax.bar(
        x + width / 2,
        [freq if freq is not None else 0 for freq in target_abs_freqs],  # Replace `None` with 0 for plotting (does not happen anymore)
        width,
        label=target_name,
        alpha=0.7)

    # Add labels and title
    ax.set_ylabel('Absolute Frequency on log-odds scale')
    ax.set_title(f'{gram_length}-Gram Absolute Frequencies in {ref_name} and {target_name}')
    ax.set_xticks(x)
    ax.set_xticklabels(top_limit_grams)
    ax.legend(loc=3)
    print(ref_name, target_name)
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(os.path.join(output_path, f'{gram_length}_gram_abs_frequency_comparison_{ref_name}_{target_name}.png'))
    plt.close()

# n_gram analysis at the word level
def n_gram_analysis(lang, ref_corpus, target_corpus, logs_dir, n=2, laplace=True):
    # take a corpus and turn it into a list of words
    def word_tokenize(corpus):
        if not is_lang(lang):
            raise ValueError("Target language not recognized list of langauges. Verify your spelling and capitalization of first letter")
        lang_ortho_table = pd.read_csv("Orthographies/Ortho113/" + lang + ".tsv", sep='\t')
         # currently (Ortho113) there is no such english punctuation characher that is used as part of a letter that does not have its own letter as well 
         # this may be subject to change with different/updated orthographies
         # example: Atayal has the letter 'n_g', which uses '_' but also has the letter '_'
        special_chars = set(string.punctuation).intersection(set(lang_ortho_table['letter'].to_list()))
        regex = r"[\w" + "".join(special_chars) + r"]+" # remove all puncutation except the ones used as characters for the language and tokenize words
        return re.findall(regex, corpus)
    # from tokens create n-gram counts for all discrete gram lengths within [1, n].
    # TBD: speed up this portion by making the grams in one loop of tokens
    def get_n_grams(tokens):
        counters = []
        # get n-gram for n=1 to n=n
        for gram_length in range(1, n + 1):
            n_grams = [tuple(tokens[i:i+gram_length]) for i in range(len(tokens) - gram_length + 1)] 
            counters.append(Counter(n_grams))
        return counters
    
    # tokenize and get the ngrams from n=1 to n=n from reference and target
    ref_tokens = word_tokenize(ref_corpus)
    target_tokens = word_tokenize(target_corpus)
    ref_n_grams_counts = get_n_grams(ref_tokens)
    target_n_grams_counts = get_n_grams(target_tokens)

    # n-grams for n (ex: n=2 for bigrams)
    ref_n_grams = ref_n_grams_counts[n - 1]
    target_n_grams = target_n_grams_counts[n - 1]

    # unigrams for reference and target
    ref_unigrams = ref_n_grams_counts[0]
    target_unigrams = target_n_grams_counts[0]
    
    # unique n-grams for reference and target
    ref_n_grams_set = set(ref_n_grams.elements())
    target_n_grams_set = set(target_n_grams.elements())

    all_n_grams = ref_n_grams_set.union(target_n_grams_set)

    # the following em algorithm was written using the following as reference: https://www.cs.cmu.edu/~roni/11761/Presentations/degenerateEM.pdf
    def em(counters, max_iter=10, eps=1e-3):
        # initialization
        lambdas = [1 / n] * n # uniform distribution of weight
        lambdas_prev = lambdas
        V = [len(c) for c in counters]
        def calc_n_gram_probs(n_gram):
            probs = []
            for gram_length in range(1, n + 1):
                # unigram case: P(w) = Count(w) / N
                if gram_length == 1:
                    probs.append(counters[0][n_gram] / counters[0].total())
                # non-unigram case: P(w | seq) = Count(seq+w) / Count(seq)
                # the following is the smoothed probabilty of a ngram for the non-unigram case 
                else:
                    probs.append((counters[gram_length - 1][n_gram] + 1 / (V[gram_length - 1] + counters[gram_length - 2][n_gram[n - gram_length:]])))  
            return probs
        
        for i in range(max_iter):
            y = []
            # update lambdas
            for n_gram in counters[n - 1].elements():
                probs = np.prod([lambdas , calc_n_gram_probs(n_gram)], axis=0)
                prob_sum = np.sum(probs)
                y_i = [p / prob_sum for p in probs]
                y.append(y_i)
            lambdas = np.sum(y, axis=0) / V[n - 1]

            # check convergence criteria
            l_prev = []
            l = []

            # calculate log likelihoods with previous iteration of lambas and current lambdas
            for n_gram in counters[n - 1].elements():
                prev_log_prob_sum = np.log(np.sum(np.prod([lambdas_prev, calc_n_gram_probs(n_gram)], axis=0)))
                log_prob_sum = np.log(np.sum(np.prod([lambdas_prev, calc_n_gram_probs(n_gram)], axis=0)))
                l_prev.append(prev_log_prob_sum)
                l.append(log_prob_sum)
            
            l_prev_norm = np.sum(l_prev) / V[n - 1]
            l_norm = np.sum(l) / V[n - 1]

            # convergence criteria
            if (l_norm - l_prev_norm) / abs(l_norm) <= eps:
                print(f"converged at iteration {i}")
                return lambdas_prev
            
            # set the current iteration to be the previous since we did not meet convergence criteria
            lambdas_prev = lambdas
        
        print(f"unable to converege within {max_iter} iterations")
        return lambdas_prev

    # calculate the probability distribution of the next word for a list of n_grams using interpolation. 
    # This is meant for bigrams were we predict the next word but it should be able to support other n-grams
    def calc_next_word_prob_from_inter(counters, n_grams):
        interpolated_weights = em(counters)
        return

    # commented code calculates probabilities, not counts
    if laplace:
    #     # note that since ref_n_grams and target_n_grams are Counter objects, if the n_gram does not exist in the respective Counter it would return 0
    #     ref_freq_vector = np.array([(ref_n_grams[n_gram] + 1) / (len(ref_n_grams_set) + ref_n_minus_one_grams[n_gram[:n-1]]) for n_gram in all_n_grams])
    #     target_freq_vector = np.array([(target_n_grams[n_gram] + 1) / (len(target_n_grams_set) + target_n_minus_one_grams[n_gram[:n-1]]) for n_gram in all_n_grams])
        ref_freq_vector = ref_freq_vector = np.array([(ref_n_grams[n_gram] + 1) for n_gram in all_n_grams])
        target_freq_vector = np.array([(target_n_grams[n_gram] + 1) for n_gram in all_n_grams])

        ref_freq_vector = normalize_vector(ref_freq_vector)
        target_freq_vector = normalize_vector(target_freq_vector)
    else:
        ref_freq_vector = np.array([(ref_n_grams[n_gram]) for n_gram in all_n_grams])
        target_freq_vector = np.array([(target_n_grams[n_gram]) for n_gram in all_n_grams])

        ref_freq_vector = normalize_vector(ref_freq_vector)
        target_freq_vector = normalize_vector(target_freq_vector)

    # calculating jaccard similarity
    word_jaccard_similarity = jaccard_similarity(ref_n_grams_set, target_n_grams_set)
    print(f"Jaccard Similarity of unique {n}-grams: {word_jaccard_similarity:.2f}")

    # calculating overlap
    word_overlap_coefficient = overlap_coefficient(ref_n_grams_set, target_n_grams_set)
    print(f"Overlap Coefficient of unique {n}-grams: {word_overlap_coefficient:.2f}")

    # calculating cosine similarity
    cosine_sim = cosine_similarity([ref_freq_vector], [target_freq_vector])[0][0]
    print(f"Cosine Similarity of word {n}-grams: {cosine_sim:.2f}")

    # calculating euclidean distance
    euclidean_dist = euclidean(ref_freq_vector, target_freq_vector)
    print(f"Euclidean Distance of word {n}-grams: {euclidean_dist:.2f}")

    # calculating kl divergence
    kl_div = kl_divergence(ref_freq_vector, target_freq_vector)
    print(f"KL Divergence of word {n}-grams: {kl_div:.2f}")

    w_vis_diff(ref_unigrams, target_unigrams, logs_dir, limit=40)
    w_vis_diff(ref_n_grams, target_n_grams, logs_dir, limit=40)
    return


# INVARIANT: args input is validated
def main(args):
    corpora_folder = "Corpora/" # change this if corora folder is different
    corpora_subfolder_names = ["ePark/", "ILRDF_Dicts/", "Paiwan_Stories/", "NTUFormosanCorpus/"]
    # corpora_subfolder_names = ["ePark/"]

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
     
    dialect_corpus = remove_chinese_characters(dialect_corpus)
    # TBD: Verify whether the following line handles all pssible punctuation in Formosan languages
    sentences = re.split(r'(?<=[.!?])\s+', dialect_corpus) # regex for looking only at punctuation at end of sentence, if you would like to consider the following character, you can use (?<=[.!?])\s+(?=[A-Z]) instead

    # you can certainly change the following values to be in args but for ease of use they are not; manually change the these values if needed
    num_sim = 5 # number of simulations
    ref_ratio = 0.8 # the percentage of the partition to be used as the "reference" corpus

    # for num_sim times, split the corpus into reference corpus and target corpus, comparing them both
    random.seed(0) # set seed for testing purposes
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

        n_gram_analysis(lang=lang, ref_corpus=ref_text, target_corpus=target_text, logs_dir="QC/orthography/" + lang + "_" + dialect + "_" +  str(sim + 1), n=2, laplace=True)
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare Partitions of a Corpora")
    # parser.add_argument('--path', help='path of the corpus you would like to analyze')
    parser.add_argument('--lang', help='name of the language you are analyzing the dialect of')
    parser.add_argument('--dialect', help='the target dialect of the text you are analyzing')

    args = parser.parse_args()

    # ensure the path exists
    # if not args.path:
    #     parser.error("No corpora path provided")
    # # corpus should be in the "Corpora" directory, technically only checks if the path has "Corpora" in it at any point
    # elif "Corpora" not in Path(args.path).parts:
    #     parser.error("Target corpus is not in \"Corpora\" directory")
    if not is_lang(args.lang):
        parser.error("Target language not recognized list of langauges. Verify your spelling and capitalization of first letter")
    # TBD: change this to include dialects that are in OtherNames
    elif not is_dialect(args.lang, args.dialect):
        parser.error("Target dialect not recognized for target language. Verify your spelling and capitalization of first letter")

    main(args)
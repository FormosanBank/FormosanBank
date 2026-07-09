import argparse
import string
import pandas as pd
from xml.etree import ElementTree as ET
from orthography_compare import normalize_vector, jaccard_similarity, kl_divergence, cosine_similarity, euclidean, kl_divergence, overlap_coefficient
from orthography_extract import is_lang, is_dialect, generate_corpus, remove_chinese_characters, parse_bool
from bag_of_sentence_analysis import word_tokenize, char_tokenize
from collections import Counter
import numpy as np
from scipy.optimize import minimize, LinearConstraint, Bounds
import matplotlib.pyplot as plt
import re

CORORA_PATH = "Corpora/" # this can be changed to the validation path in practice
# REF_SUBDIRS = ["ePark", "ILRDF_Dicts/", "Paiwan_Stories/", "NTUFormosanCorpus/"]
REF_SUBDIRS = ["ePark/"]
REF_PATHS = [CORORA_PATH + subdir for subdir in REF_SUBDIRS]
TARGET_SUBDIRS = ["ePark/"]
NUM_SIMS = 3

SEED = 0
np.random.seed(SEED)

LIMIT = 40
LAPLACE = True
N = 2
VERBOSE = True


def load_target_corpus_from_file(tar_path):
    if tar_path.lower().endswith('.xml'):
        tree = ET.parse(tar_path)
        root = tree.getroot()
        text = []
        for sentence in root.findall('.//S'):
            form = sentence.find("FORM[@kindOf='standard']")
            if form is not None and form.text:
                text.append(form.text)
        return " ".join(text)

    with open(tar_path, 'r', encoding='utf-8') as file_handle:
        return file_handle.read()


def em(counters, n=N, max_iter=10, eps=1e-5, verbose=VERBOSE, laplace=LAPLACE):
    """Expectation-Maximization algorithm for mixture weighting (not currently used)."""
    # initialization
    lambdas = np.random.dirichlet(np.ones(n), size=1)[0] # random distribution of weight
    lambdas_prev = lambdas.copy() # we use .copy() to prevent aliasing
    N_counts = [c.total() for c in counters]
    V = [len(c) for c in counters]
    def calc_n_gram_probs(n_gram):
        probs = []
        for gram_length in range(1, n + 1):
            # unigram case: P(w) = Count(w) / N
            if gram_length == 1:
                probs.append((counters[0][n_gram] + laplace) / 
                                (counters[0].total() + (laplace * len(counters[0]))))
            # non-unigram case: P(w | seq) = Count(seq+w) / Count(seq)
            # the following is the smoothed probabilty of a ngram for the non-unigram case 
            else:
                probs.append(((counters[gram_length - 1][n_gram] + laplace) / 
                                ((laplace * (V[gram_length - 1]) + counters[gram_length - 2][n_gram[n - gram_length:]]))))  
        return probs
    
    for i in range(max_iter):
        y = []
        # update lambdas
        for n_gram in counters[n - 1].elements():
            probs = np.prod([lambdas, calc_n_gram_probs(n_gram)], axis=0)
            prob_sum = np.sum(probs)
            y_i = [p / prob_sum for p in probs]
            y.append(y_i)
        lambdas = np.sum(y, axis=0) / counters[n - 1].total()

        # check convergence criteria
        l_prev = []
        l = []

        # calculate log likelihoods with previous iteration of lambas and current lambdas
        for n_gram in counters[n - 1].elements():
            prev_log_prob_sum = np.log(np.sum(np.prod([lambdas_prev, calc_n_gram_probs(n_gram)], axis=0)))
            log_prob_sum = np.log(np.sum(np.prod([lambdas, calc_n_gram_probs(n_gram)], axis=0)))
            l_prev.append(prev_log_prob_sum)
            l.append(log_prob_sum)
        
        l_prev_norm = np.sum(l_prev) / N_counts[n - 1]
        l_norm = np.sum(l) / N_counts[n - 1]

        # convergence criteria
        # note that l_norm should generally increase, but we use abs to handle floating point issues 
        if abs((l_norm - l_prev_norm) / max(abs(l_norm), 1e-12)) <= eps:
            if verbose:
                print(f"converged at iteration {i}")
            return lambdas_prev
        
        # set the current iteration to be the previous since we did not meet convergence criteria
        lambdas_prev = lambdas.copy()
    
    if verbose:
        print(f"unable to converege within {max_iter} iterations")
    return lambdas_prev


def deleted_interpolation(counters, n=N, verbose=VERBOSE, laplace=LAPLACE):
    """
    Deleted interpolation: optimize mixture weights using held-out likelihood.
    This avoids overfitting by optimizing weights on a held-out validation set.
    (Not currently used)
    """
    N_counts = [c.total() for c in counters]
    V = [len(c) for c in counters]
    
    def calc_n_gram_probs(n_gram):
        """Calculate probabilities for each n-gram model"""
        probs = []
        for gram_length in range(1, n + 1):
            if gram_length == 1:
                probs.append((counters[0][n_gram] + laplace) / 
                             (counters[0].total() + (laplace * len(counters[0]))))
            else:
                probs.append(((counters[gram_length - 1][n_gram] + laplace) / 
                             ((laplace * (V[gram_length - 1]) + counters[gram_length - 2][n_gram[n - gram_length:]]))))
        return np.array(probs)
    
    # Collect all unique n-grams and their probabilities from each model
    all_n_grams = list(counters[n - 1].elements())
    
    # Build probability matrix: rows = n-grams, cols = models
    prob_matrix = []
    counts = []
    for n_gram in all_n_grams:
        probs = calc_n_gram_probs(n_gram)
        prob_matrix.append(probs)
        counts.append(counters[n - 1][n_gram])
    
    prob_matrix = np.array(prob_matrix)
    counts = np.array(counts)
    
    def negative_log_likelihood(lambdas):
        """Objective: negative log likelihood of held-out n-grams"""
        # Ensure lambdas sum to 1 and are non-negative
        lambdas = np.abs(lambdas)
        lambdas = lambdas / (np.sum(lambdas) + 1e-10)
        
        # Compute interpolated probabilities for each n-gram
        interpolated_probs = np.dot(prob_matrix, lambdas)
        # Clamp to avoid log(0)
        interpolated_probs = np.clip(interpolated_probs, 1e-10, 1.0)
        
        # Weighted negative log likelihood
        nll = -np.sum(counts * np.log(interpolated_probs))
        return nll
    
    # Initialize with uniform weights
    x0 = np.random.dirichlet(np.ones(n), size=1)[0]  # random initialization
    
    constraints = LinearConstraint(np.ones((1, n)), 1.0, 1.0)  # sum to 1
    bounds = Bounds(0, 1)  # each weight between 0 and 1
    
    result = minimize(
        negative_log_likelihood,
        x0,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints,
        options={'ftol': 1e-9, 'maxiter': 1000}
    )
    
    lambdas = np.abs(result.x)
    lambdas = lambdas / (np.sum(lambdas) + 1e-10)
    
    return lambdas


def obtain_stats(ref_corpus, target_corpus, ref_lang, n=N, laplace=LAPLACE, limit=LIMIT, verbose=VERBOSE):
    """Compute n-gram statistics for both word and character tokenization in a single pass."""
    
    # HELPER FUNCTIONS (for commented-out advanced analyses)
    def calc_n_gram_prob(counters, n_gram):
        """Calculate probability of an n-gram using conditional probability."""
        if n != 1:
            return (counters[n - 1][n_gram] + laplace) / (counters[n - 2][n_gram[:n - 1]] + (laplace * len(counters[n - 1])))
        else:
            return (counters[0][n_gram] + laplace) /( counters[0].total() + laplace * len(counters[0]))
    
    def calc_n_gram_probs(counters, n_grams):
        """Calculate the probability of multiple n-grams using conditional probability."""
        return {n_gram: calc_n_gram_prob(counters, n_gram) for n_gram in n_grams}

    def calc_n_gram_inter_prob(n_gram, counters, interpolated_weights):
        """Calculate interpolated probability: sum(lambda_i * P(w | seq_i))."""
        gram_length = len(n_gram)
        return np.sum(np.prod([
            interpolated_weights,
            [calc_n_gram_prob(counters, n_gram[:i]) for i in range(1, gram_length + 1)]
        ], axis=0))

    def calc_n_gram_probs_from_inter(counters, n_grams, interpolated_weights):
        """Calculate interpolated probabilities for multiple n-grams."""
        return {
            n_gram: calc_n_gram_inter_prob(n_gram, counters, interpolated_weights)
            for n_gram in n_grams
        }
    
    def get_n_grams(tokens):
        """Extract n-grams for n=1 to N."""
        counters = []
        for gram_length in range(1, n + 1):
            n_grams = [tuple(tokens[i:i+gram_length]) for i in range(len(tokens) - gram_length + 1)] 
            counters.append(Counter(n_grams))
        return counters
    
    def compute_stats_for_mode(ref_tokens, target_tokens, mode_name):
        """Compute all statistics for a given tokenization mode."""
        ref_n_gram_counts = get_n_grams(ref_tokens)
        target_n_gram_counts = get_n_grams(target_tokens)

        ref_n_grams = ref_n_gram_counts[n - 1]
        target_n_grams = target_n_gram_counts[n - 1]

        unique_ref_n_grams = set(ref_n_grams)
        unique_target_n_grams = set(target_n_grams)
        all_unique_n_grams = unique_ref_n_grams.union(unique_target_n_grams)

        # Vectorize frequency computations
        ref_freq_vector = np.array([(ref_n_grams[ng] + laplace) for ng in all_unique_n_grams])
        ref_freq_vector = normalize_vector(ref_freq_vector)

        target_freq_vector = np.array([(target_n_grams[ng] + laplace) for ng in all_unique_n_grams])
        target_freq_vector = normalize_vector(target_freq_vector)

        # Compute all metrics
        jc_sim = jaccard_similarity(unique_ref_n_grams, unique_target_n_grams)
        ov_coeff = overlap_coefficient(unique_ref_n_grams, unique_target_n_grams)
        kl_div = kl_divergence(ref_freq_vector, target_freq_vector)
        cos_sim = cosine_similarity(np.atleast_2d(ref_freq_vector), np.atleast_2d(target_freq_vector))[0][0]
        eucl_dist = euclidean(ref_freq_vector, target_freq_vector)
        ratio = kl_div / ov_coeff if ov_coeff > 0 else 'undefined'
        
        # COMMENTED OUT: Advanced analyses (kept for future use)
        # if n > 1:
        #     top_n_minus_one_ref_n_grams = ref_n_gram_counts[n - 2].most_common(limit)
        #     top_n_minus_one_ref_n_grams_dict = dict(top_n_minus_one_ref_n_grams)
        #     kl_divs_next_word = []
        #     
        #     for prefix, _ in top_n_minus_one_ref_n_grams:
        #         # Get all n-grams with this prefix in both ref and target
        #         ref_next_words = {}
        #         target_next_words = {}
        #         
        #         for n_gram in ref_n_grams:
        #             if n_gram[:n - 1] == prefix:
        #                 ref_next_words[n_gram] = calc_n_gram_prob(ref_n_gram_counts, n_gram)
        #         
        #         for n_gram in target_n_grams:
        #             if n_gram[:n - 1] == prefix:
        #                 target_next_words[n_gram] = calc_n_gram_prob(target_n_gram_counts, n_gram)
        #         
        #         # Get all unique next word contexts
        #         all_next_words = set(ref_next_words.keys()).union(set(target_next_words.keys()))
        #         
        #         if len(all_next_words) > 0:
        #             # Create probability vectors
        #             ref_prob_vector = np.array([ref_next_words.get(n_gram, laplace / (laplace * len(ref_n_grams) + 1)) for n_gram in all_next_words])
        #             target_prob_vector = np.array([target_next_words.get(n_gram, laplace / (laplace * len(target_n_grams) + 1)) for n_gram in all_next_words])
        #             
        #             ref_prob_vector = normalize_vector(ref_prob_vector)
        #             target_prob_vector = normalize_vector(target_prob_vector)
        #             
        #             # Calculate KL divergence
        #             kl_div_next = kl_divergence(ref_prob_vector, target_prob_vector)
        #             kl_divs_next_word.append(kl_div_next)
        #     
        #     avg_kl_div_next_word = np.mean(kl_divs_next_word) if len(kl_divs_next_word) > 0 else 0
        #     if verbose:
        #         print(f"Average KL Divergence of next word probabilities given top {limit} {n-1}-grams: {avg_kl_div_next_word}")
        # 
        if verbose:
            print(f"Statistics for {mode_name} tokenization:")
            print(f"Jaccard Similarity of unique {n}-grams: {jc_sim}")
            print(f"Overlap Coefficient of unique {n}-grams: {ov_coeff}")
            print(f"Kullback-Leibler Divergence of {n}-grams: {kl_div}")
            print(f"Cosine Similarity of {n}-grams: {cos_sim}")
            print(f"Euclidean Distance of {n}-grams: {eucl_dist}")
            # print(f"Ratio of kl_div to overlap coefficient: {kl_div / ov_coeff if ov_coeff > 0 else 'undefined'}")
        # 
        # lambdas = deleted_interpolation(ref_n_gram_counts, n, laplace=laplace, verbose=verbose)
        # if verbose:
        #     print(f"Deleted interpolation optimized lambdas for {n}-grams: {lambdas}")
        # 
        # total_counter = ref_n_grams + target_n_grams
        # top_n_grams = total_counter.most_common(limit)
        # target_inter_probs_from_ref_weights = calc_n_gram_probs_from_inter(target_n_gram_counts, top_n_grams, lambdas)
        # target_cond_probs = calc_n_gram_probs(target_n_gram_counts, top_n_grams)
        # 
        # percentage_probs = {n_gram: target_inter_probs_from_ref_weights[n_gram] / target_cond_probs[n_gram] for n_gram in top_n_grams if target_cond_probs[n_gram] > 0}
        # 
        # if verbose:
        #     print(f"Top {limit} {n}-grams and their probabilities in target corpus: {target_inter_probs_from_ref_weights}")
        #     print(f"Top {limit} {n}-grams and their conditional probabilities in target corpus: {target_cond_probs}")
        #     print(f"Percentage of interpolated probability to conditional probability for top {limit} {n}-grams: {percentage_probs}")
        #     print(f"Average percentage of interpolated probability compare to conditional probability {np.mean(list(percentage_probs.values()))}")
        
        return jc_sim, ov_coeff, kl_div, cos_sim, eucl_dist, ratio, ref_n_gram_counts, target_n_gram_counts, all_unique_n_grams
    
    def save_plots(ref_n_gram_counts, target_n_gram_counts, all_unique_n_grams, mode_name):
        """Save n-gram distribution plots."""
        for i in range(1, n + 1):
            ref_n_grams_i = ref_n_gram_counts[i - 1]
            target_n_grams_i = target_n_gram_counts[i - 1]
            unique_ref_i = set(ref_n_grams_i)
            unique_target_i = set(target_n_grams_i)
            all_unique_i = unique_ref_i.union(unique_target_i)

            ref_freq_i = np.array([(ref_n_grams_i[ng] + laplace) for ng in all_unique_i])
            ref_freq_i = normalize_vector(ref_freq_i)

            target_freq_i = np.array([(target_n_grams_i[ng] + laplace) for ng in all_unique_i])
            target_freq_i = normalize_vector(target_freq_i)

            plt.figure(figsize=(10, 6))
            plt.bar(range(len(ref_freq_i)), ref_freq_i, alpha=0.5, label='Reference Corpus')
            plt.bar(range(len(target_freq_i)), target_freq_i, alpha=0.5, label='Target Corpus')
            plt.title(f'Frequency Distribution of {i}-grams ({mode_name} level)')
            plt.xlabel('Unique n-grams')
            plt.ylabel('Normalized Frequency')
            plt.legend(loc=3)
            plt.tight_layout()
            plt.savefig(f'logs/{ref_lang}_{mode_name}_{i}gram_distribution.png')
            plt.close()
    
    # Tokenize both modes once
    ref_word_tokens = word_tokenize(ref_corpus, ref_lang)
    target_word_tokens = word_tokenize(target_corpus, ref_lang)
    ref_char_tokens = char_tokenize(ref_corpus)
    target_char_tokens = char_tokenize(target_corpus)
    
    # Compute statistics for both modes
    word_stats = compute_stats_for_mode(ref_word_tokens, target_word_tokens, "word")
    char_stats = compute_stats_for_mode(ref_char_tokens, target_char_tokens, "char")
    
    # Save plots if needed
    save_plots(word_stats[6], word_stats[7], word_stats[8], "word")
    save_plots(char_stats[6], char_stats[7], char_stats[8], "char")
    
    return (word_stats[:6],), (char_stats[:6],)

def main(args):
    ref_lang = args.ref_lang
    ref_dialect = args.ref_dialect if args.ref_dialect else "default"
    tar_is_file = args.tar_is_file
    tar_path = args.tar_path
    tar_lang = args.tar_lang if args.tar_lang else ref_lang
    tar_dialect = args.tar_dialect if args.tar_dialect else ref_dialect
    perturb_type = args.perturb_type
    to_ortho = args.to_ortho

    # generate reference corpus
    dialect_corpus = ""
    for path in REF_PATHS:
        corpus = generate_corpus(ref_lang, path, "standard", by_dialect=ref_dialect != "default") # output is a dictionary where the keys are the dialect and the values are the totality of text for that dialect as a string
        if ref_dialect in corpus.keys():
            dialect_corpus += corpus[ref_dialect]
     
    dialect_corpus = remove_chinese_characters(dialect_corpus)
    
    lang_ortho_table = pd.read_csv("Orthographies/Ortho113/" + ref_lang + ".tsv", sep='\t')
    special_chars = set(string.punctuation).difference(set(lang_ortho_table['letter'].to_list()))
    sentences = re.split(r'(?<=[{}])\s+'.format(re.escape("".join(special_chars))), dialect_corpus)

    # generate target corpus
    target_ortho_table = pd.read_csv("Orthographies/Ortho113/" + tar_lang + ".tsv", sep='\t')
    target_special_chars = set(string.punctuation).difference(set(target_ortho_table['letter'].to_list()))
    if tar_is_file:
        target_corpus = load_target_corpus_from_file(tar_path)
        target_corpus = remove_chinese_characters(target_corpus)
        target_sentences = re.split(r'(?<=[{}])\s+'.format(re.escape("".join(target_special_chars))), target_corpus)
    else:
        target_corpus = ""
        for subdir in TARGET_SUBDIRS:
            path = CORORA_PATH + subdir
            corpus = generate_corpus(tar_lang, path, "standard", by_dialect=tar_dialect != "default") # output is a dictionary where the keys are the dialect and the values are the totality of text for that dialect as a string
            target_corpus += corpus[tar_dialect]
        target_corpus = remove_chinese_characters(target_corpus)
        target_sentences = re.split(r'(?<=[{}])\s+'.format(re.escape("".join(target_special_chars))), target_corpus)

    print(len(sentences), "sentences in reference corpus")
    print(len(target_sentences), "sentences in target corpus")

    # max_freq_char = Counter("".join(sentences)).most_common(1)[0][0]
    ref_unique_chars = set(lang_ortho_table['letter'].to_list())

    # word_ratios = []
    # char_ratios = []
    # perturbed_word_ratios = []
    # perturbed_char_ratios = []

    word_cos_sims = []
    char_cos_sims = []
    word_kl_divs = []
    char_kl_divs = []

    perturbed_word_cos_sims = []
    perturbed_char_cos_sims = []
    perturbed_word_kl_divs = []
    perturbed_char_kl_divs = []
    
    for i in range(NUM_SIMS):
        ref_samples = np.random.choice(sentences, size=min(len(target_sentences), len(sentences)), replace=False)
        if perturb_type != None:
            if perturb_type == 'swap':
                random_char = np.random.choice(list(ref_unique_chars.difference(set(string.punctuation))), size=1)[0].lower()
                other_random_char = np.random.choice(list(ref_unique_chars.difference(set(string.punctuation) | {random_char})), size=1)[0].lower()
                print(f"Swapping {other_random_char} with {random_char}")
                perturbed_sentences = [sentence.replace(other_random_char, random_char) for sentence in sentences]
                perturbed_samples = np.random.choice(perturbed_sentences, size=min(len(target_sentences), len(sentences)), replace=False)
            elif perturb_type == 'orthographic':
                conversion_table = pd.read_csv(f"Orthographies/ConversionTables/{ref_lang}_{to_ortho}_113.tsv", sep='\t', skipinitialspace=True)
                # Remove trailing empty columns that may result from trailing whitespace
                conversion_table = conversion_table.loc[:, ~conversion_table.columns.str.contains('^Unnamed')]
                for i in range(len(conversion_table)):
                    original = conversion_table.loc[i, 'original']
                    converted = conversion_table.loc[i, 'standard']
                    perturbed_sentences = [sentence.replace(original, converted) for sentence in sentences]
                perturbed_samples = np.random.choice(perturbed_sentences, size=min(len(target_sentences), len(sentences)), replace=False)
            perturbed_corpus = " ".join(perturbed_samples)

        
        ref_corpus = " ".join(ref_samples)
        target_corpus_str = " ".join(target_sentences)
        print(f"Simulation {i + 1}:")
        
        print("Reference to Target Comparison:")
        word_stats, char_stats = obtain_stats(ref_corpus, target_corpus_str, ref_lang)
        word_cos_sims.append(word_stats[0][3])
        char_cos_sims.append(char_stats[0][3])
        word_kl_divs.append(word_stats[0][2])
        char_kl_divs.append(char_stats[0][2])
        # word_ratios.append(word_stats[0][-1])
        # char_ratios.append(char_stats[0][-1])

        
        if perturb_type != None:
            print("Reference to Perturbed Comparison:")
            perturbed_word_stats, perturbed_char_stats = obtain_stats(ref_corpus, perturbed_corpus, ref_lang)
            perturbed_word_cos_sims.append(perturbed_word_stats[0][3])
            perturbed_char_cos_sims.append(perturbed_char_stats[0][3])
            perturbed_word_kl_divs.append(perturbed_word_stats[0][2])
            perturbed_char_kl_divs.append(perturbed_char_stats[0][2])
        # perturbed_word_ratios.append(perturbed_word_stats[0][-1])
        # perturbed_char_ratios.append(perturbed_char_stats[0][-1])  
    
    # average_word_ratio = np.mean(word_ratios if all(isinstance(ratio, (int, float)) for ratio in word_ratios) else "undefined")  # type: ignore # calculate the average ratio across simulations, handle case where ratio is undefined
    # average_char_ratio = np.mean(char_ratios if all(isinstance(ratio, (int, float)) for ratio in char_ratios) else "undefined")  # type: ignore # calculate the average ratio across simulations, handle case where ratio is undefined
    # print(f"Average Word Ratio of KL Divergence to Overlap Coefficient across {NUM_SIMS} simulations: {average_word_ratio}")
    # print(f"Average Character Ratio of KL Divergence to Overlap Coefficient across {NUM_SIMS} simulations: {average_char_ratio}")

    average_word_cos_sim = np.mean(word_cos_sims)
    average_char_cos_sim = np.mean(char_cos_sims)
    average_word_kl_div = np.mean(word_kl_divs)
    average_char_kl_div = np.mean(char_kl_divs)

    if perturb_type != None:
        print(f"Perturbed Comparison:")
        print(f"Average Word Cosine Similarity across {NUM_SIMS} simulations: {average_word_cos_sim}")
        print(f"Average Character Cosine Similarity across {NUM_SIMS} simulations: {average_char_cos_sim}")
        print(f"Average Word KL Divergence across {NUM_SIMS} simulations: {average_word_kl_div}")
        print(f"Average Character KL Divergence across {NUM_SIMS} simulations: {average_char_kl_div}")

    # average_perturbed_word_ratio = np.mean(perturbed_word_ratios if all(isinstance(ratio, (int, float)) for ratio in perturbed_word_ratios) else "undefined")  # type: ignore # calculate the average ratio across simulations, handle case where ratio is undefined
    # average_perturbed_char_ratio = np.mean(perturbed_char_ratios if all(isinstance(ratio, (int, float)) for ratio in perturbed_char_ratios) else "undefined")  # type: ignore # calculate the average ratio across simulations, handle case where ratio is undefined
    # print(f"Average Perturbed Word Ratio of KL Divergence to Overlap Coefficient across {NUM_SIMS} simulations: {average_perturbed_word_ratio}")
    # print(f"Average Perturbed Character Ratio of KL Divergence to Overlap Coefficient across {NUM_SIMS} simulations: {average_perturbed_char_ratio}")
    
    ref_corpus_full = " ".join(sentences)
    target_corpus_full = " ".join(target_sentences) if not isinstance(target_corpus, str) or not target_corpus else target_corpus
    print(f"Final Comparison on Full Corpora:")
    word_stats, char_stats = obtain_stats(ref_corpus_full, target_corpus_full, ref_lang)
    
    if perturb_type != None:
        print()
        print(f"Final Comparison on Perturbed Reference Corpus:")
        if perturb_type == 'swap':
            print(f"Swapping the random character '{other_random_char}' with a random character '{random_char}' in the reference corpus.")
        elif perturb_type == 'orthographic':
            print(f"Converting the reference corpus to the orthography '{to_ortho}'.")

        perturbed_corpus_full = " ".join(perturbed_sentences)
        perturbed_word_stats, perturbed_char_stats = obtain_stats(perturbed_corpus_full, target_corpus_full, ref_lang)

    return

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Compare Partitions of a Corpora")
    parser.add_argument('--ref_lang', help='name of the language you are analyzing the dialect of', required=True)
    parser.add_argument('--ref_dialect', help='the target dialect of the text you are analyzing', required=False)
    parser.add_argument('--tar_is_file', type=parse_bool, help='whether the target is a file, if not TARGET_SUBDIRS will be used to make the target corpus', required=True, default=False)
    parser.add_argument('--tar_path', help='the path to the target file or directory', required=False)
    parser.add_argument('--tar_lang', help='the language of the target corpus, if different from the reference language', required=False)
    parser.add_argument('--tar_dialect', help='the dialect of the target corpus, if different from the reference dialect', required=False)
    parser.add_argument('--perturb_type', help='the type of perturbation to apply to the reference corpus (e.g., swap, orthographic)', required=False, default=FileNotFoundError)
    parser.add_argument('--to_ortho', help='convert the reference corpus to this orthography', required=False, default='MinED')
    
    args = parser.parse_args()

    if not is_lang(args.ref_lang):
        raise ValueError(f"{args.ref_lang} is not a valid language. Verify that the language is in the list of languages in dialects.csv")
    if not is_dialect(args.ref_lang, args.ref_dialect) and args.ref_dialect is not None:
        raise ValueError(f"{args.ref_dialect} is not a valid dialect of {args.ref_lang}")
    if args.tar_is_file:
        if not args.tar_path:
            raise ValueError("If tar_is_file is True, tar_path must be provided")
    if args.perturb_type not in ['None', 'swap', 'orthographic']:
        raise ValueError(f"{args.perturb_type} is not a valid perturbation type. Choose from 'None', 'swap', or 'orthographic'.")

    main(args)
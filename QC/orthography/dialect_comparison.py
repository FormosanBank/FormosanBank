import argparse
from xml.etree import ElementTree as ET
from orthography_compare import normalize_vector, jaccard_similarity, kl_divergence, cosine_similarity, euclidean, kl_divergence, overlap_coefficient
from orthography_extract import is_lang, is_dialect, generate_corpus, remove_chinese_characters, parse_bool
from bag_of_sentence_analysis import word_tokenize, char_tokenize
from collections import Counter
import numpy as np
from scipy.optimize import minimize, LinearConstraint, Bounds
import re

CORORA_PATH = "Corpora/" # this can be changed to the validation path in practice
REF_SUBDIRS = ["ePark", "ILRDF_Dicts/", "Paiwan_Stories/", "NTUFormosanCorpus/"]
REF_PATHS = [CORORA_PATH + subdir for subdir in REF_SUBDIRS]
TARGET_SUBDIRS = ["ePark/"]
NUM_SIMS = 5

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
    """
    from scipy.optimize import minimize
    
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
    # x0 = np.ones(n) / n
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
    
    # if verbose:
    #     print(f"Deleted interpolation converged: lambdas = {lambdas}")
    #     print(f"Final NLL: {result.fun:.6f}")
    
    return lambdas


def obtain_stats(ref_corpus, target_corpus, ref_lang, n=N, laplace=LAPLACE, limit=LIMIT, verbose=VERBOSE):
    # calcuate probability of an n-gram
    def calc_n_gram_prob(counters, n_gram):
        if n != 1:
            return (counters[n - 1][n_gram] + laplace) / (counters[n - 2][n_gram[:n - 1]] + (laplace * len(counters[n - 1])))
        else:
            return (counters[0][n_gram] + laplace) /( counters[0].total() + laplace * len(counters[0]))
        
    # calculate the probability of n_grams using conditional probability
    def calc_n_gram_probs(counters, n_grams):
        return {n_gram: calc_n_gram_prob(counters, n_gram) for n_gram in n_grams}

    def calc_n_gram_inter_prob(n_gram, counters, interpolated_weights):
        gram_length = len(n_gram)
        # sum(lambda_i * P(w | seq_i)) where seq_i is the context for the respective gram length
        return np.sum(np.prod([
            interpolated_weights,
            [calc_n_gram_prob(counters, n_gram[:i]) for i in range(1, gram_length + 1)]
        ], axis=0))

    def calc_n_gram_probs_from_inter(counters, n_grams, interpolated_weights):
        return {
            n_gram: calc_n_gram_inter_prob(n_gram, counters, interpolated_weights)
            for n_gram in n_grams
        }
    
    def get_n_grams(tokens):
        counters = []
        # get n-gram for n=1 to n=n
        for gram_length in range(1, n + 1):
            n_grams = [tuple(tokens[i:i+gram_length]) for i in range(len(tokens) - gram_length + 1)] 
            counters.append(Counter(n_grams))
        return counters
    
    def obtain_n_gram_stats(ref_corpus, target_corpus, mode="word"):
        ref_tokens = word_tokenize(ref_corpus, ref_lang) if mode == "word" else char_tokenize(ref_corpus)
        target_tokens = word_tokenize(target_corpus, ref_lang) if mode == "word" else char_tokenize(target_corpus)

        ref_n_gram_counts = get_n_grams(ref_tokens)
        target_n_gram_counts = get_n_grams(target_tokens)

        ref_n_grams = ref_n_gram_counts[n - 1]
        target_n_grams = target_n_gram_counts[n - 1]

        unique_ref_n_grams = set(ref_n_grams)
        unique_target_n_grams = set(target_n_grams)

        all_unique_n_grams = unique_ref_n_grams.union(unique_target_n_grams)

        ref_freq_vector = np.array([(ref_n_grams[n_gram] + laplace) for n_gram in all_unique_n_grams])
        ref_freq_vector = normalize_vector(ref_freq_vector)

        target_freq_vector = np.array([(target_n_grams[n_gram] + laplace) for n_gram in all_unique_n_grams])
        target_freq_vector = normalize_vector(target_freq_vector)

        jc_sim = jaccard_similarity(unique_ref_n_grams, unique_target_n_grams)
        ov_coeff = overlap_coefficient(unique_ref_n_grams, unique_target_n_grams)
        kl_div = kl_divergence(ref_freq_vector, target_freq_vector)
        cos_sim = cosine_similarity(np.atleast_2d(ref_freq_vector), np.atleast_2d(target_freq_vector))[0][0]
        eucl_dist = euclidean(ref_freq_vector, target_freq_vector)

        if verbose:
        #     print(f"Jaccard Similarity of unique {n}-grams: {jc_sim}")
        #     print(f"Overlap Coefficient of unique {n}-grams: {ov_coeff}")
        #     print(f"Kullback-Leibler Divergence of {n}-grams: {kl_div}")
        #     print(f"Cosine Similarity of {n}-grams: {cos_sim}")
        #     print(f"Euclidean Distance of {n}-grams: {eucl_dist}")
            print(f"Ratio of kl_div to overlap coefficient: {kl_div / ov_coeff if ov_coeff > 0 else 'undefined'}")

        # lambdas = deleted_interpolation(ref_n_gram_counts, n, laplace=laplace, verbose=verbose)
        # if verbose:
        #     print(f"Deleted interpolation optimized lambdas for {n}-grams: {lambdas}")

        # total_counter = ref_n_grams + target_n_grams
        # top_n_grams = total_counter.most_common(limit)
        # target_inter_probs_from_ref_weights = calc_n_gram_probs_from_inter(target_n_gram_counts, top_n_grams, lambdas)
        # target_cond_probs = calc_n_gram_probs(target_n_gram_counts, top_n_grams)

        # percentage_probs = {n_gram: target_inter_probs_from_ref_weights[n_gram] / target_cond_probs[n_gram] for n_gram in top_n_grams if target_cond_probs[n_gram] > 0}

        # if verbose:
        #     print(f"Top {limit} {n}-grams and their probabilities in target corpus: {target_inter_probs_from_ref_weights}")
        #     print(f"Top {limit} {n}-grams and their conditional probabilities in target corpus: {target_cond_probs}")
        #     print(f"Percentage of interpolated probability to conditional probability for top {limit} {n}-grams: {percentage_probs}")
        #     print(f"Average percentage of interpolated probability compare to conditional probability {np.mean(list(percentage_probs.values()))}")

        return jc_sim, ov_coeff, kl_div, cos_sim, eucl_dist, kl_div / ov_coeff if ov_coeff > 0 else 'undefined'
    
    return obtain_n_gram_stats(ref_corpus, target_corpus, mode="word"), obtain_n_gram_stats(ref_corpus, target_corpus, mode="char")

def main(args):
    ref_lang = args.ref_lang
    ref_dialect = args.ref_dialect
    tar_is_file = args.tar_is_file
    tar_path = args.tar_path

    # generate reference corpus
    dialect_corpus = ""
    for path in REF_PATHS:
        corpus = generate_corpus(ref_lang, path, "standard", by_dialect=True) # output is a dictionary where the keys are the dialect and the values are the totality of text for that dialect as a string
        if ref_dialect in corpus.keys():
            dialect_corpus += corpus[ref_dialect]
     
    dialect_corpus = remove_chinese_characters(dialect_corpus)
    sentences = re.split(r'(?<=[.!?])\s+', dialect_corpus) # regex for looking only at punctuation at end of sentence, if you would like to consider the following character, you can use (?<=[.!?])\s+(?=[A-Z]) instead

    # generate target corpus
    if tar_is_file:
        target_corpus = load_target_corpus_from_file(tar_path)
        target_corpus = remove_chinese_characters(target_corpus)
        target_sentences = re.split(r'(?<=[.!?])\s+', target_corpus)
    else:
        target_corpus = ""
        for subdir in TARGET_SUBDIRS:
            path = CORORA_PATH + subdir
            corpus = generate_corpus(ref_lang, path, "standard", by_dialect=False)
            target_corpus += corpus  # type: ignore
        target_corpus = remove_chinese_characters(target_corpus)
        target_sentences = re.split(r'(?<=[.!?])\s+', target_corpus)

    word_ratios = []
    char_ratios = []
    for i in range(NUM_SIMS):
        ref_samples = np.random.choice(sentences, size=min(len(target_sentences), len(sentences)), replace=False)
        ref_corpus = " ".join(ref_samples)
        target_corpus = " ".join(target_sentences)
        print(f"Simulation {i + 1}:")
        word_stats, char_stats = obtain_stats(ref_corpus, target_corpus, ref_lang)
        word_ratios.append(word_stats[-1])
        char_ratios.append(char_stats[-1])
    
    average_word_ratio = np.mean(word_ratios if all(isinstance(ratio, (int, float)) for ratio in word_ratios) else "undefined")  # type: ignore # calculate the average ratio across simulations, handle case where ratio is undefined
    average_char_ratio = np.mean(char_ratios if all(isinstance(ratio, (int, float)) for ratio in char_ratios) else "undefined")  # type: ignore # calculate the average ratio across simulations, handle case where ratio is undefined
    print(f"Average Word Ratio of KL Divergence to Overlap Coefficient across {NUM_SIMS} simulations: {average_word_ratio}")
    print(f"Average Character Ratio of KL Divergence to Overlap Coefficient across {NUM_SIMS} simulations: {average_char_ratio}")
    
    ref_corpus = " ".join(sentences)
    target_corpus = " ".join(target_sentences) if not target_corpus else target_corpus
    print(f"Final Comparison on Full Corpora:")
    obtain_stats(ref_corpus, target_corpus, ref_lang)
    return

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Compare Partitions of a Corpora")
    parser.add_argument('--ref_lang', help='name of the language you are analyzing the dialect of', required=True)
    parser.add_argument('--ref_dialect', help='the target dialect of the text you are analyzing', required=True)
    parser.add_argument('--tar_is_file', type=parse_bool, help='whether the target is a file, if not TARGET_SUBDIRS will be used to make the target corpus', required=True)
    parser.add_argument('--tar_path', help='the path to the target file or directory', required=False)
    
    args = parser.parse_args()

    if not is_lang(args.ref_lang):
        raise ValueError(f"{args.ref_lang} is not a valid language. Verify that the language is in the list of languages in dialects.csv")
    if not is_dialect(args.ref_lang, args.ref_dialect):
        raise ValueError(f"{args.ref_dialect} is not a valid dialect of {args.ref_lang}")
    if args.tar_is_file:
        if not args.tar_path:
            raise ValueError("If tar_is_file is True, tar_path must be provided")
    main(args)
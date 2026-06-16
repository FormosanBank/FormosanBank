import os
import math
import random
import string
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pickle
from pathlib import Path
from collections import Counter
from sklearn.metrics.pairwise import cosine_similarity
from scipy.spatial.distance import euclidean
from scipy.special import rel_entr
import argparse
import re
from orthography_extract import generate_corpus, remove_chinese_characters, is_dialect as extract_is_dialect

plt.switch_backend('Agg')  # Use a non-GUI backend
# plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']


def _dialects_path():
    candidate = Path(__file__).resolve().parents[2] / "dialects.csv"
    if candidate.exists():
        return candidate
    return Path("dialects.csv")


def is_lang(lang):
    dialect_csv = pd.read_csv(_dialects_path())
    return lang in dialect_csv['Language'].unique()


def is_dialect(lang, dialect):
    dialect_csv = pd.read_csv(_dialects_path())
    return (dialect in dialect_csv[dialect_csv['Language'] == lang]['Official'].unique())


def get_lang(path, langs):
    for lang in langs:
        if lang in path:
            return lang


def plot_freqs(num_label_locations, ref_freqs, target_freqs, re_name, tar_name, y_label, x_labels, title, output, filename):
    x = np.arange(num_label_locations)
    width = 0.35

    fig, ax = plt.subplots(figsize=(15, 5))

    ax.bar(
        x - width / 2,
        [freq if freq is not None else 0 for freq in ref_freqs],
        width,
        label=re_name,
        alpha=0.7,
    )
    ax.bar(
        x + width / 2,
        [freq if freq is not None else 0 for freq in target_freqs],
        width,
        label=tar_name,
        alpha=0.7,
    )

    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels)
    ax.legend(loc=3)
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(os.path.join(output, filename))
    plt.close()


def w_vis_diff(ref_freq, target_freq, logs_dir, ref_name="reference", target_name="target", limit=20):
    output_path = logs_dir
    os.makedirs(output_path, exist_ok=True)

    total_counter = ref_freq + target_freq
    total_counts_sorted = total_counter.most_common()
    top_limit_gram_counts = total_counts_sorted[:limit]
    top_limit_grams = [g for g, _ in top_limit_gram_counts]
    gram_length = len(top_limit_grams[0])

    total_ref_grams = ref_freq.total()
    total_target_grams = target_freq.total()

    ref_rel_freqs = [
        np.log((ref_freq[gram] + 1) / (total_ref_grams - ref_freq[gram] + len(total_counter) - 1))
        for gram in top_limit_grams
    ]
    target_rel_freqs = [
        np.log((target_freq[gram] + 1) / (total_target_grams + len(total_counter) - 1))
        for gram in top_limit_grams
    ]

    ref_abs_freqs = [
        np.log((ref_freq[gram] + 1) / (total_ref_grams + len(total_counter)))
        for gram in top_limit_grams
    ]
    target_abs_freqs = [
        np.log((target_freq[gram] + 1) / (total_target_grams - target_freq[gram] + len(total_counter)))
        for gram in top_limit_grams
    ]

    plot_freqs(
        num_label_locations=limit,
        ref_freqs=ref_rel_freqs,
        target_freqs=target_rel_freqs,
        re_name=ref_name,
        tar_name=target_name,
        y_label='Relative Frequency on log-odds scale',
        x_labels=top_limit_grams,
        title=f"{gram_length}-Gram Relative Frequencies in {ref_name} and {target_name}",
        output=output_path,
        filename=f'{gram_length}_gram_rel_frequency_comparison_{ref_name}_{target_name}.png',
    )

    plot_freqs(
        num_label_locations=limit,
        ref_freqs=ref_abs_freqs,
        target_freqs=target_abs_freqs,
        re_name=ref_name,
        tar_name=target_name,
        y_label='Absolute Frequency on log-odds scale',
        x_labels=top_limit_grams,
        title=f"{gram_length}-Gram Absolute Frequencies in {ref_name} and {target_name}",
        output=output_path,
        filename=f'{gram_length}_gram_abs_frequency_comparison_{ref_name}_{target_name}.png',
    )


def compute_ngram_similarity_metrics(ref_tokens, target_tokens, gram_length, laplace=True):
    def get_ngrams(tokens):
        return Counter(tuple(tokens[i:i + gram_length]) for i in range(len(tokens) - gram_length + 1))

    ref_ngrams = get_ngrams(ref_tokens)
    target_ngrams = get_ngrams(target_tokens)

    ref_ngrams_set = set(ref_ngrams.elements())
    target_ngrams_set = set(target_ngrams.elements())
    all_ngrams = ref_ngrams_set.union(target_ngrams_set)

    if laplace:
        ref_freq_vector = np.array([(ref_ngrams[n_gram] + 1) for n_gram in all_ngrams], dtype=float)
        target_freq_vector = np.array([(target_ngrams[n_gram] + 1) for n_gram in all_ngrams], dtype=float)
    else:
        ref_freq_vector = np.array([(ref_ngrams[n_gram]) for n_gram in all_ngrams], dtype=float)
        target_freq_vector = np.array([(target_ngrams[n_gram]) for n_gram in all_ngrams], dtype=float)

    ref_freq_vector = normalize_vector(ref_freq_vector)
    target_freq_vector = normalize_vector(target_freq_vector)

    return {
        "n": gram_length,
        "jaccard_similarity": float(jaccard_similarity(ref_ngrams_set, target_ngrams_set)),
        "overlap_coefficient": float(overlap_coefficient(ref_ngrams_set, target_ngrams_set)),
        "cosine_similarity": float(cosine_similarity([ref_freq_vector], [target_freq_vector])[0][0]),
        "euclidean_distance": float(euclidean(ref_freq_vector, target_freq_vector)),
        "kl_divergence": float(kl_divergence(ref_freq_vector, target_freq_vector)),
        "ref_unique_ngram_count": len(ref_ngrams_set),
        "target_unique_ngram_count": len(target_ngrams_set),
    }


def safe_normalize_vector(vector):
    vector = np.asarray(vector, dtype=float)
    if vector.size == 0:
        return vector
    vector = np.clip(vector, 0.0, None)
    total = float(np.sum(vector))
    if not np.isfinite(total) or total <= 0:
        return np.full(vector.shape, 1.0 / len(vector), dtype=float)
    return vector / total


def js_distance(p, q):
    p = np.asarray(p, dtype=float).ravel()
    q = np.asarray(q, dtype=float).ravel()
    if p.shape != q.shape:
        raise ValueError("Probability vectors must have the same shape")

    p = safe_normalize_vector(p)
    q = safe_normalize_vector(q)

    eps = 1e-12
    p_safe = np.clip(p, eps, None)
    q_safe = np.clip(q, eps, None)
    m = 0.5 * (p_safe + q_safe)

    divergence = 0.5 * (
        np.sum(p_safe * np.log(p_safe / m)) + np.sum(q_safe * np.log(q_safe / m))
    )
    divergence = max(float(divergence), 0.0)
    return float(np.sqrt(divergence))


def n_gram_analysis(lang, ref_corpus, target_corpus, logs_dir, n=2, laplace=True, save_plots=True, verbose=True):
    def word_tokenize(corpus):
        if not is_lang(lang):
            raise ValueError("Target language not recognized list of languages. Verify your spelling and capitalization of first letter")
        ortho_path = Path(__file__).resolve().parents[2] / "Orthographies" / "Ortho113" / f"{lang}.tsv"
        if not ortho_path.exists():
            raise FileNotFoundError(f"Orthography table not found: {ortho_path}")
        lang_ortho_table = pd.read_csv(ortho_path, sep='\t')
        special_chars = set(string.punctuation).intersection(set(lang_ortho_table['letter'].to_list()))
        regex = r"[\w" + "".join(special_chars) + r"]+"
        return re.findall(regex, corpus)

    def get_n_grams(tokens):
        counters = []
        for gram_length in range(1, n + 1):
            n_grams = [tuple(tokens[i:i+gram_length]) for i in range(len(tokens) - gram_length + 1)]
            counters.append(Counter(n_grams))
        return counters

    def char_tokenize(corpus):
        return [char for char in corpus if not char.isspace()]

    ref_tokens = word_tokenize(ref_corpus)
    target_tokens = word_tokenize(target_corpus)
    ref_char_tokens = char_tokenize(ref_corpus)
    target_char_tokens = char_tokenize(target_corpus)
    ref_n_grams_counts = get_n_grams(ref_tokens)
    target_n_grams_counts = get_n_grams(target_tokens)

    ref_n_grams = ref_n_grams_counts[n - 1]
    target_n_grams = target_n_grams_counts[n - 1]
    ref_unigrams = ref_n_grams_counts[0]
    target_unigrams = target_n_grams_counts[0]

    ref_n_grams_set = set(ref_n_grams.elements())
    target_n_grams_set = set(target_n_grams.elements())
    all_n_grams = ref_n_grams_set.union(target_n_grams_set)

    def em(counters, max_iter=10, eps=1e-5):
        lambdas = np.random.dirichlet(np.ones(n), size=1)[0]
        smoothing = 1 if laplace else 0
        lambdas_prev = lambdas.copy()
        N = [c.total() for c in counters]
        V = [len(c) for c in counters]

        def calc_n_gram_probs(n_gram):
            probs = []
            for gram_length in range(1, n + 1):
                if gram_length == 1:
                    probs.append((counters[0][n_gram] + smoothing) / (counters[0].total() + (smoothing * len(counters[0]))))
                else:
                    probs.append(((counters[gram_length - 1][n_gram] + smoothing) / ((smoothing * (V[gram_length - 1]) + counters[gram_length - 2][n_gram[n - gram_length:]]))))
            return probs

        for i in range(max_iter):
            y = []
            for n_gram in counters[n - 1].elements():
                probs = np.prod([lambdas, calc_n_gram_probs(n_gram)], axis=0)
                prob_sum = np.sum(probs)
                y_i = [p / prob_sum for p in probs]
                y.append(y_i)
            lambdas = np.sum(y, axis=0) / counters[n - 1].total()

            l_prev = []
            l = []
            for n_gram in counters[n - 1].elements():
                prev_log_prob_sum = np.log(np.sum(np.prod([lambdas_prev, calc_n_gram_probs(n_gram)], axis=0)))
                log_prob_sum = np.log(np.sum(np.prod([lambdas, calc_n_gram_probs(n_gram)], axis=0)))
                l_prev.append(prev_log_prob_sum)
                l.append(log_prob_sum)

            l_prev_norm = np.sum(l_prev) / N[n - 1]
            l_norm = np.sum(l) / N[n - 1]

            if abs((l_norm - l_prev_norm) / max(abs(l_norm), 1e-12)) <= eps:
                if verbose:
                    print(f"converged at iteration {i}")
                return lambdas_prev

            lambdas_prev = lambdas.copy()

        if verbose:
            print(f"unable to converege within {max_iter} iterations")
        return lambdas_prev

    if laplace:
        ref_freq_vector = np.array([(ref_n_grams[n_gram] + 1) for n_gram in all_n_grams])
        target_freq_vector = np.array([(target_n_grams[n_gram] + 1) for n_gram in all_n_grams])
        ref_freq_vector = normalize_vector(ref_freq_vector)
        target_freq_vector = normalize_vector(target_freq_vector)
    else:
        ref_freq_vector = np.array([(ref_n_grams[n_gram]) for n_gram in all_n_grams])
        target_freq_vector = np.array([(target_n_grams[n_gram]) for n_gram in all_n_grams])
        ref_freq_vector = normalize_vector(ref_freq_vector)
        target_freq_vector = normalize_vector(target_freq_vector)

    word_jaccard_similarity = jaccard_similarity(ref_n_grams_set, target_n_grams_set)
    if verbose:
        print(f"Jaccard Similarity of unique {n}-grams: {word_jaccard_similarity:.2f}")

    word_overlap_coefficient = overlap_coefficient(ref_n_grams_set, target_n_grams_set)
    if verbose:
        print(f"Overlap Coefficient of unique {n}-grams: {word_overlap_coefficient:.2f}")

    cosine_sim = cosine_similarity([ref_freq_vector], [target_freq_vector])[0][0]
    if verbose:
        print(f"Cosine Similarity of word {n}-grams: {cosine_sim:.2f}")

    euclidean_dist = euclidean(ref_freq_vector, target_freq_vector)
    if verbose:
        print(f"Euclidean Distance of word {n}-grams: {euclidean_dist:.2f}")

    kl_div = kl_divergence(ref_freq_vector, target_freq_vector)
    if verbose:
        print(f"KL Divergence of word {n}-grams: {kl_div:.2f}")

    if save_plots:
        os.makedirs(logs_dir, exist_ok=True)
        w_vis_diff(ref_unigrams, target_unigrams, logs_dir, limit=40)
        if n != 1:
            w_vis_diff(ref_n_grams, target_n_grams, logs_dir, limit=40)

    def calc_n_gram_prob(counters, n_gram):
        smoothing = 1 if laplace else 0
        if n != 1:
            return (counters[n - 1][n_gram] + smoothing) / (counters[n - 2][n_gram[:n - 1]] + (smoothing * len(counters[n - 1])))
        else:
            return (counters[0][n_gram] + smoothing) / (counters[0].total() + smoothing * len(counters[0]))

    def calc_n_gram_inter_prob(n_gram, counters, interpolated_weights):
        gram_length = len(n_gram)
        return np.sum(np.prod([
            interpolated_weights,
            [calc_n_gram_prob(counters, n_gram[:i]) for i in range(1, gram_length + 1)]
        ], axis=0))

    def calc_n_gram_probs_from_inter(counters, n_grams, interpolated_weights):
        return {n_gram: calc_n_gram_inter_prob(n_gram, counters, interpolated_weights) for n_gram in n_grams}

    def calc_interpolated_next_word_prob(counters, context, next_word, interpolated_weights):
        n_gram = context + (next_word,)
        terms = []
        for i in range(1, len(n_gram) + 1):
            sub_ngram = n_gram[-i:] if i > 1 else (next_word,)
            terms.append(calc_n_gram_prob(counters, sub_ngram))
        return float(np.sum(np.prod([interpolated_weights, terms], axis=0)))

    def interpolated_next_word_distribution(counters, context, next_words, interpolated_weights):
        scores = np.array([
            calc_interpolated_next_word_prob(counters, context, word, interpolated_weights)
            for word in next_words
        ])
        return safe_normalize_vector(scores)

    def calc_n_gram_probs(counters, n_grams):
        return {n_gram: calc_n_gram_prob(counters, n_gram) for n_gram in n_grams}

    interpolated_weights = em(ref_n_grams_counts)

    limit = 40
    total_counter = ref_n_grams + target_n_grams
    top_limit_grams = [g for g, _ in total_counter.most_common(limit)]

    inter_probs = calc_n_gram_probs_from_inter(target_n_grams_counts, top_limit_grams, interpolated_weights)
    cond_probs = calc_n_gram_probs(target_n_grams_counts, top_limit_grams)

    percentage_probs = {n_gram: (inter_probs[n_gram] / cond_probs[n_gram]) * 100 for n_gram in top_limit_grams}

    valid_ratio_values = [
        inter_probs[n_gram] / cond_probs[n_gram]
        for n_gram in top_limit_grams
        if np.isfinite(cond_probs[n_gram]) and cond_probs[n_gram] > 0 and np.isfinite(inter_probs[n_gram])
    ]
    average_interpolated_conditional_probability_proportion = (
        float(np.mean(valid_ratio_values)) if valid_ratio_values else None
    )

    if save_plots:
        x = np.arange(limit)
        width = 0.35
        fig, ax = plt.subplots(figsize=(15, 5))
        ax.bar(
            x - width / 2,
            [p if p is not None else 0 for p in percentage_probs.values()],
            width,
            alpha=0.7,
        )
        ax.plot(x - width / 2, [100] * len(x), color='red', linewidth=2)
        ax.set_ylabel('Interpolated Probabilities Percentage of Conditional Probability')
        ax.set_title(f'Interploted Probabilites Over Conditional Probabilities for Top {limit} n-grams')
        ax.set_xticks(x)
        ax.set_xticklabels(top_limit_grams)
        plt.xticks(rotation=90)
        plt.tight_layout()
        plt.savefig(os.path.join(logs_dir, f'{n}_probability_comparison.png'))
        plt.close()

    def build_next_word_distributions(ngram_counter, context_length):
        distributions = {}
        for ngram, count in ngram_counter.items():
            context = ngram[:context_length]
            next_word = ngram[-1]
            if context not in distributions:
                distributions[context] = Counter()
            distributions[context][next_word] += count
        return distributions

    def get_top_contexts(ref_counters, target_counters, limit):
        context_length = n - 1
        total_context_counts = ref_counters[context_length - 1] + target_counters[context_length - 1]
        return [context for context, _ in total_context_counts.most_common(limit)]

    def compare_next_word_distributions(ref_counters, target_counters, top_contexts):
        if n < 2:
            return {}, None

        context_length = n - 1
        ref_context_counts = ref_counters[context_length - 1]
        target_context_counts = target_counters[context_length - 1]
        ref_next_word_dists = build_next_word_distributions(ref_counters[n - 1], context_length)
        target_next_word_dists = build_next_word_distributions(target_counters[n - 1], context_length)

        smoothing = 1 if laplace else 0
        js_by_context = {}

        for context in top_contexts:
            ref_next = ref_next_word_dists.get(context, Counter())
            target_next = target_next_word_dists.get(context, Counter())
            all_next_words = sorted(set(ref_next.keys()) | set(target_next.keys()))

            if not all_next_words:
                continue

            ref_context_count = ref_context_counts[context]
            target_context_count = target_context_counts[context]
            vocab_size = len(all_next_words)

            ref_probs = np.array([
                (ref_next[word] + smoothing) / (ref_context_count + smoothing * vocab_size)
                for word in all_next_words
            ])
            target_probs = np.array([
                (target_next[word] + smoothing) / (target_context_count + smoothing * vocab_size)
                for word in all_next_words
            ])

            ref_probs = safe_normalize_vector(ref_probs)
            target_probs = safe_normalize_vector(target_probs)
            js_value = js_distance(ref_probs, target_probs)
            if np.isfinite(js_value):
                js_by_context[context] = float(js_value)

        if not js_by_context:
            return {}, None

        mean_js = float(np.mean(list(js_by_context.values())))
        return js_by_context, mean_js

    def compare_interpolated_next_word_distributions(ref_counters, target_counters, top_contexts, interpolated_weights):
        if n < 2:
            return {}, None

        context_length = n - 1
        ref_next_word_dists = build_next_word_distributions(ref_counters[n - 1], context_length)
        target_next_word_dists = build_next_word_distributions(target_counters[n - 1], context_length)

        js_by_context = {}

        for context in top_contexts:
            ref_next = ref_next_word_dists.get(context, Counter())
            target_next = target_next_word_dists.get(context, Counter())
            all_next_words = sorted(set(ref_next.keys()) | set(target_next.keys()))

            if not all_next_words:
                continue

            ref_probs = interpolated_next_word_distribution(ref_counters, context, all_next_words, interpolated_weights)
            target_probs = interpolated_next_word_distribution(target_counters, context, all_next_words, interpolated_weights)

            js_value = js_distance(ref_probs, target_probs)
            if np.isfinite(js_value):
                js_by_context[context] = float(js_value)

        if not js_by_context:
            return {}, None

        mean_js = float(np.mean(list(js_by_context.values())))
        return js_by_context, mean_js

    def plot_next_word_js_distances(js_by_context, title, filename):
        context_labels = [" ".join(context) if isinstance(context, tuple) else str(context) for context in js_by_context.keys()]
        fig, ax = plt.subplots(figsize=(15, 5))
        x = np.arange(len(context_labels))
        ax.bar(x, list(js_by_context.values()), alpha=0.7)
        ax.set_ylabel("Jensen-Shannon Distance")
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(context_labels)
        plt.xticks(rotation=90)
        plt.tight_layout()
        plt.savefig(os.path.join(logs_dir, filename))
        plt.close()

    context_label = f"{n - 1}-gram" if n > 2 else "unigram"
    top_contexts = get_top_contexts(ref_n_grams_counts, target_n_grams_counts, limit)

    js_by_context, mean_js = compare_next_word_distributions(ref_n_grams_counts, target_n_grams_counts, top_contexts)
    if mean_js is not None and verbose:
        print(f"Mean Jensen-Shannon distance of next-word distributions for top {limit} {context_label}s: {mean_js:.4f}")
    if mean_js is not None and save_plots:
        plot_next_word_js_distances(js_by_context, title=(f"Next-Word Distribution JS Distance for Top {limit} {context_label}s (given {n}-gram context)"), filename=f"{n}_next_word_js_distance.png")

    inter_js_by_context, inter_mean_js = compare_interpolated_next_word_distributions(ref_n_grams_counts, target_n_grams_counts, top_contexts, interpolated_weights)
    if inter_mean_js is not None and verbose:
        print(f"Mean Jensen-Shannon distance of interpolated next-word distributions for top {limit} {context_label}s: {inter_mean_js:.4f}")
    if inter_mean_js is not None and save_plots:
        plot_next_word_js_distances(inter_js_by_context, title=(f"Interpolated Next-Word Distribution JS Distance for Top {limit} {context_label}s (given {n}-gram context)"), filename=f"{n}_interpolated_next_word_js_distance.png")

    n_gram_statistics = {}
    for gram_length in range(1, n + 1):
        n_gram_statistics[str(gram_length)] = {
            "character": compute_ngram_similarity_metrics(ref_char_tokens, target_char_tokens, gram_length, laplace=laplace),
            "word": compute_ngram_similarity_metrics(ref_tokens, target_tokens, gram_length, laplace=laplace),
        }

    return {
        "n": n,
        "jaccard_similarity": float(word_jaccard_similarity),
        "overlap_coefficient": float(word_overlap_coefficient),
        "cosine_similarity": float(cosine_sim),
        "euclidean_distance": float(euclidean_dist),
        "kl_divergence": float(kl_div),
        "mean_next_word_js_distance": None if mean_js is None else float(mean_js),
        "mean_interpolated_next_word_js_distance": None if inter_mean_js is None else float(inter_mean_js),
        "ref_token_count": len(ref_tokens),
        "target_token_count": len(target_tokens),
        "ref_unique_ngram_count": len(ref_n_grams_set),
        "target_unique_ngram_count": len(target_n_grams_set),
        "average_interpolated_conditional_probability_proportion": average_interpolated_conditional_probability_proportion,
        "n_gram_statistics": n_gram_statistics,
    }


def get_lang(path, langs):
    for lang in langs:
        if lang in path:
            return lang
    return None


def jaccard_similarity(set1, set2):
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    similarity = len(intersection) / len(union) if union else 0.0
    return similarity


def overlap_coefficient(set1, set2):
    intersection = set1.intersection(set2)
    smaller_set_size = min(len(set1), len(set2))
    coefficient = len(intersection) / smaller_set_size if smaller_set_size else 0.0
    return coefficient


def normalize_vector(vector):
    total = np.sum(vector)
    if total > 0:
        return vector / total
    else:
        return vector
    
def kl_divergence(p, q):
    # Add a small epsilon to avoid division by zero
    epsilon = 1e-10
    p = p + epsilon
    q = q + epsilon
    return np.sum(rel_entr(p, q))

def vis_diff(all_chars, c1_char_freq, c2_char_freq, source_1, source_2, logs_dir, lang):
    
    output_path = os.path.join(logs_dir, lang)
    os.makedirs(output_path, exist_ok=True)

    # Get the sorted list of characters
    all_chars = [c for c in all_chars if c.isalpha() or c == "'" or c == "’"]
    sorted_chars = sorted(all_chars)

    # Compute the total number of characters in each corpus
    total_corpus1_chars = sum(c1_char_freq.values())
    total_corpus2_chars = sum(c2_char_freq.values())

    # Calculate relative frequencies (ratios) for plotting
    # corpus1_freqs = [
    #     np.log((c1_char_freq.get(char, 0)+0.0001) / (total_corpus1_chars - c1_char_freq.get(char, 0) + 1)) for char in sorted_chars
    # ]
    # corpus2_freqs = [
    #    np.log((c2_char_freq.get(char, 0)+0.0001) / (total_corpus2_chars - c2_char_freq.get(char, 0) + 1)) for char in sorted_chars
    # ]

    corpus1_freqs = [
    np.log((c1_char_freq.get(char, 0) + 1) / (total_corpus1_chars - c1_char_freq.get(char, 0) + len(sorted_chars)))
    for char in sorted_chars
    ]

    corpus2_freqs = [
        np.log((c2_char_freq.get(char, 0) + 1) / (total_corpus2_chars - c2_char_freq.get(char, 0) + len(sorted_chars)))
        if c2_char_freq.get(char, 0) > 0 else None
        for char in sorted_chars
    ]

    # Optionally, convert ratios to percentages
    # corpus1_freqs = [freq * 100 for freq in corpus1_freqs]
    # corpus2_freqs = [freq * 100 for freq in corpus2_freqs]

    # Plotting
    x = np.arange(len(sorted_chars))  # label locations
    width = 0.35  # width of the bars

    fig, ax = plt.subplots(figsize=(15, 5))
    
    #rects1 = ax.bar(x - width / 2, corpus1_freqs, width, label=source_1)
    #rects2 = ax.bar(x + width / 2, corpus2_freqs, width, label=source_2)

    rects1 = ax.bar(
    x - width / 2,
    [freq if freq is not None else 0 for freq in corpus1_freqs],  # Replace `None` with 0 for plotting
    width,
    label=source_1,
    alpha=0.7)

    rects2 = ax.bar(
        x + width / 2,
        [freq if freq is not None else 0 for freq in corpus2_freqs],  # Replace `None` with 0 for plotting
        width,
        label=source_2,
        alpha=0.7)

    # Add labels and title
    ax.set_ylabel('Relative Frequency on log-odds scale')
    ax.set_title(f'Character Relative Frequencies in {source_1} and {source_2}')
    ax.set_xticks(x)
    ax.set_xticklabels(sorted_chars)
    ax.legend()
    print(source_1, source_2)
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(os.path.join(output_path, f'character_frequency_comparison_{source_1}_{source_2}.png'))
    plt.close()


def _average_stats(stats_list):
    if not stats_list:
        return {}

    averaged = {}
    for key in stats_list[0].keys():
        values = [entry.get(key) for entry in stats_list if entry.get(key) is not None]
        if not values:
            continue
        if all(isinstance(value, dict) for value in values):
            averaged[key] = _average_stats(values)
        elif all(isinstance(value, (int, float, np.integer, np.floating)) for value in values):
            averaged[key] = float(np.mean(values))
        else:
            averaged[key] = values[0]
    return averaged


def _partition_text(text, ref_ratio, rng):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [sentence.strip() for sentence in sentences if sentence and sentence.strip()]
    if not sentences:
        return "", ""

    if len(sentences) == 1:
        return sentences[0], ""

    target_count = max(1, min(len(sentences) - 1, math.ceil(ref_ratio * len(sentences))))
    ref_sentences = rng.sample(sentences, target_count)
    target_sentences = [sentence for sentence in sentences if sentence not in ref_sentences]
    return " ".join(ref_sentences), " ".join(target_sentences)


def compare_partitioned_corpora(reference_corpus, target_corpus, lang, num_sim=5, ref_ratio=0.8, seed=0, verbose=True, save_plots=True):
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(curr_dir, "compare_logs")
    os.makedirs(logs_dir, exist_ok=True)

    def summarize_partitioned_corpus(corpus, label):
        rng = random.Random(seed)
        simulation_stats = []
        for sim_idx in range(num_sim):
            ref_partition, target_partition = _partition_text(corpus, ref_ratio, rng)
            partition_logs_dir = os.path.join(logs_dir, f"{label}_sim_{sim_idx + 1}")
            simulation_stats.append(
                n_gram_analysis(
                    lang=lang,
                    ref_corpus=ref_partition,
                    target_corpus=target_partition,
                    logs_dir=partition_logs_dir,
                    n=2,
                    laplace=True,
                    save_plots=save_plots and bool(ref_partition and target_partition),
                    verbose=False,
                )
            )
        return _average_stats(simulation_stats)

    reference_summary = summarize_partitioned_corpus(reference_corpus, "reference")
    target_summary = summarize_partitioned_corpus(target_corpus, "target")

    combined_summary = n_gram_analysis(
        lang=lang,
        ref_corpus=reference_corpus,
        target_corpus=target_corpus,
        logs_dir=logs_dir,
        n=2,
        laplace=True,
        save_plots=save_plots,
        verbose=verbose,
    )

    return {
        "reference": reference_summary,
        "target": target_summary,
        "combined": combined_summary,
    }


def main(args):
    corpora_folder = "Corpora/"
    reference_subfolder_names = ["ePark/"]
    target_subfolder_names = ["ILRDF_DICT/XML/Amis"]

    reference_paths = [corpora_folder + directory for directory in reference_subfolder_names]
    target_paths = [corpora_folder + directory for directory in target_subfolder_names]

    lang = args.ref_lang
    dialect = args.ref_dialect

    # Generate reference corpus
    reference_corpus = ""
    for path in reference_paths:
        try:
            corpus = generate_corpus(lang, path, "standard", by_dialect=True)
            if dialect is None:
                # If no dialect specified, concatenate all dialects
                reference_corpus += " ".join(corpus.values())
            elif dialect in corpus.keys():
                reference_corpus += corpus[dialect]
        except ValueError as e:
            if "doesn't exist" not in str(e):
                raise

    # Generate target corpus (dialect independent, only from provided directory)
    target_corpus = ""
    for path in target_paths:
        try:
            corpus = generate_corpus(lang, path, "standard", by_dialect=False)
            target_corpus += corpus["default"]
        except ValueError as e:
            if "doesn't exist" not in str(e):
                raise

    reference_corpus = remove_chinese_characters(reference_corpus)
    target_corpus = remove_chinese_characters(target_corpus)

    if not reference_corpus or not target_corpus:
        print(f"Warning: Could not generate reference and/or target corpus for {lang} dialect {dialect}")
        return

    # Run the partitioned comparison
    result = compare_partitioned_corpora(
        reference_corpus=reference_corpus,
        target_corpus=target_corpus,
        lang=lang,
        num_sim=5,
        ref_ratio=0.8,
        seed=0,
        verbose=True,
        save_plots=True,
    )

    # Print results
    def print_section(title, data):
        print(f"\n=== {title} ===")
        for key, value in data.items():
            if isinstance(value, float):
                print(f"{key}: {value:.4f}")
            elif isinstance(value, dict) and key == "n_gram_statistics":
                print(f"\n{key}:")
                for gram_length, metrics in sorted(value.items(), key=lambda x: int(x[0])):
                    print(f"  {gram_length}-gram:")
                    for metric_type, metric_data in metrics.items():
                        print(f"    {metric_type}:")
                        for metric_name, metric_value in metric_data.items():
                            if isinstance(metric_value, float):
                                print(f"      {metric_name}: {metric_value:.4f}")
                            elif isinstance(metric_value, int):
                                print(f"      {metric_name}: {metric_value}")
            elif isinstance(value, dict):
                print(f"\n{key}:")
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, (int, float)):
                        print(f"  {sub_key}: {sub_value}")

    print_section("Reference Summary (averaged across partitions)", result["reference"])
    print_section("Target Summary (averaged across partitions)", result["target"])
    print_section("Combined Summary", result["combined"])

            
    
if __name__ == "__main__":
    langs = ['Amis', 'Atayal', 'Paiwan', 'Bunun', 'Puyuma', 'Rukai', 'Tsou', 'Saisiyat', 'Yami',
             'Thao', 'Kavalan', 'Truku', 'Sakizaya', 'Seediq', 'Saaroa', 'Siraya', 'Kanakanavu']
    
    parser = argparse.ArgumentParser(description="Compare reference and target orthographic statistics using partitioned corpora")
    parser.add_argument('--ref_lang', required=True, help='Language of the reference source(s)')
    parser.add_argument('--ref_dialect', help='Optional dialect of the reference source(s)')
    args = parser.parse_args()

    # Validate required arguments
    if not is_lang(args.ref_lang):
        parser.error("Target language not recognized. Verify your spelling and capitalization of first letter")
    
    if args.ref_dialect and not extract_is_dialect(args.ref_lang, args.ref_dialect):
        parser.error("Target dialect not recognized for target language. Verify your spelling and capitalization of first letter")
    
    main(args)
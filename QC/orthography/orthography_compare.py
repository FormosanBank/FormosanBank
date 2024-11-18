import os
import matplotlib.pyplot as plt
import numpy as np
import pickle
from sklearn.metrics.pairwise import cosine_similarity
from scipy.spatial.distance import euclidean
from scipy.special import rel_entr
import argparse

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']


def jaccard_similarity(set1, set2):
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    similarity = len(intersection) / len(union)
    return similarity

def overlap_coefficient(set1, set2):
    intersection = set1.intersection(set2)
    smaller_set_size = min(len(set1), len(set2))
    coefficient = len(intersection) / smaller_set_size
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

def vis_diff(all_chars, c1_char_freq, c2_char_freq, source_1, source_2):
    
    # Get the sorted list of characters
    sorted_chars = sorted(all_chars)

    # Compute the total number of characters in each corpus
    total_corpus1_chars = sum(c1_char_freq.values())
    total_corpus2_chars = sum(c2_char_freq.values())

    # Calculate relative frequencies (ratios) for plotting
    corpus1_freqs = [
        c1_char_freq.get(char, 0) / total_corpus1_chars for char in sorted_chars
    ]
    corpus2_freqs = [
        c2_char_freq.get(char, 0) / total_corpus2_chars for char in sorted_chars
    ]

    # Optionally, convert ratios to percentages
    # corpus1_freqs = [freq * 100 for freq in corpus1_freqs]
    # corpus2_freqs = [freq * 100 for freq in corpus2_freqs]

    # Plotting
    x = np.arange(len(sorted_chars))  # label locations
    width = 0.35  # width of the bars

    fig, ax = plt.subplots(figsize=(15, 5))
    rects1 = ax.bar(x - width / 2, corpus1_freqs, width, label=source_1)
    rects2 = ax.bar(x + width / 2, corpus2_freqs, width, label=source_2)

    # Add labels and title
    ax.set_ylabel('Relative Frequency')
    ax.set_title(f'Character Relative Frequencies in {source_1} and {source_2}')
    ax.set_xticks(x)
    ax.set_xticklabels(sorted_chars)
    ax.legend()

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()


def main(args, curr_dir):


    with open(os.path.join(curr_dir, "logs", args.o_info_1, "orthographic_info"), 'rb') as f:
        c1_info = pickle.load(f)
    with open(os.path.join(curr_dir, "logs", args.o_info_2, "orthographic_info"), 'rb') as f:
        c2_info = pickle.load(f)


    char_jaccard_similarity = jaccard_similarity(set(c1_info['unique_characters']), set(c2_info['unique_characters']))
    print(f"Jaccard Similarity of unique characters: {char_jaccard_similarity:.2f}")

    char_overlap_coefficient = overlap_coefficient(set(c1_info['unique_characters']), set(c2_info['unique_characters']))
    print(f"Overlap Coefficient of unique characters: {char_overlap_coefficient:.2f}")

    all_chars = set(c1_info['unique_characters']).union(set(c2_info['unique_characters']))

    c1_freq_vector = np.array([c1_info['character_frequency'].get(char, 0) for char in all_chars])
    c2_freq_vector = np.array([c2_info['character_frequency'].get(char, 0) for char in all_chars])
    c1_freq_vector = normalize_vector(c1_freq_vector)
    c2_freq_vector = normalize_vector(c2_freq_vector)

    cosine_sim = cosine_similarity([c1_freq_vector], [c2_freq_vector])[0][0]
    print(f"Cosine Similarity of character frequencies: {cosine_sim:.2f}")

    euclidean_dist = euclidean(c1_freq_vector, c2_freq_vector)
    print(f"Euclidean Distance of character frequencies: {euclidean_dist:.2f}")

    kl_div = kl_divergence(c1_freq_vector, c2_freq_vector)
    print(f"KL Divergence of character frequencies: {kl_div:.2f}")

    c1_bigrams = c1_info['2-grams']
    c2_bigrams = c2_info['2-grams']

    # Create a set of all bigrams
    all_bigrams = set(c1_bigrams.keys()).union(set(c2_bigrams.keys()))

    c1_bigram_vector = np.array([c1_bigrams.get(bigram, 0) for bigram in all_bigrams])
    c2_bigram_vector = np.array([c2_bigrams.get(bigram, 0) for bigram in all_bigrams])
    # Normalize and compute similarity measures as before
    c1_bigram_vector = normalize_vector(c1_bigram_vector)
    c2_bigram_vector = normalize_vector(c2_bigram_vector)

    # Compute cosine similarity
    bigram_cosine_sim = cosine_similarity([c1_bigram_vector], [c2_bigram_vector])[0][0]
    print(f"Cosine Similarity of bigram frequencies: {bigram_cosine_sim:.2f}")

    bigram_euclidean_dist = euclidean(c1_bigram_vector, c2_bigram_vector)
    print(f"Euclidean Distance of bigram frequencies: {bigram_euclidean_dist:.2f}")

    vis_diff(all_chars, c1_info['character_frequency'], c2_info['character_frequency'], "_".join(args.o_info_1.split('_')[1:]), "_".join(args.o_info_2.split('_')[1:]))

            
    
if __name__ == "__main__":

    curr_dir = os.path.dirname(os.path.abspath(__file__))
    
    parser = argparse.ArgumentParser(description="Compare orthographic info")
    #parser.add_argument('--verbose', action='store_true', help='increase output verbosity')
    parser.add_argument('--o_info_1', help='extracted orthographic info that will be used in comparison. Should be in the orthography folder. format is Lang_Corpus')
    parser.add_argument('--o_info_2', help='extracted orthographic info that will be used in comparison. Should be in the orthography folder. format is Lang_Corpus')
    args = parser.parse_args()

    # Validate required arguments
    if not args.o_info_1 or not args.o_info_2:
        parser.error("--o_info_1 and o_info_2 are required.")
    if not os.path.exists(os.path.join(curr_dir, "logs", args.o_info_1, "orthographic_info")):
        parser.error(f"The entered orthographic info, {args.o_info_1}, doesn't exist")
    if not os.path.exists(os.path.join(curr_dir, "logs", args.o_info_2, "orthographic_info")):
        parser.error(f"The entered orthographic info, {args.o_info_2}, doesn't exist")

    main(args, curr_dir)
import os
import matplotlib.pyplot as plt
import numpy as np
import pickle
import string
from sklearn.metrics.pairwise import cosine_similarity
from scipy.spatial.distance import euclidean
from scipy.special import rel_entr
import argparse

plt.switch_backend('Agg')  # Use a non-GUI backend
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
        0 if c1_char_freq.get(char, 0) == 0 else np.log((c1_char_freq.get(char, 0)+1) / (total_corpus1_chars - c1_char_freq.get(char, 0) + 1)) for char in sorted_chars
    ]
    corpus2_freqs = [
       0 if c2_char_freq.get(char, 0) == 0 else np.log((c2_char_freq.get(char, 0)+1) / (total_corpus2_chars - c2_char_freq.get(char, 0) + 1)) for char in sorted_chars
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
    ax.set_ylabel('Relative Frequency on log-odds scale')
    ax.set_title(f'Character Relative Frequencies in {source_1} and {source_2}')
    ax.set_xticks(x)
    ax.set_xticklabels(sorted_chars)
    ax.legend()

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(f'character_frequency_comparison_{source_1}_{source_2}.png')
    plt.close()


def main(args):

    # get the orthographic info for the target corpus
    with open(os.path.join(os.getcwd(),'QC/orthography/logs',args.o_info, "orthographic_info"), 'rb') as f:
        c1_info = pickle.load(f)

    # get the reference orthographic info for that language
    file_path = os.path.dirname(__file__)
    with open(os.path.join(file_path, "reference", args.language,'orthographic_info'), 'rb') as f:
        c2_info = pickle.load(f)

    # Filter unique_chars to exclude punctuation and numerals
    exclude_chars = set(string.punctuation + string.digits)
    c1_info['unique_characters'] = [char for char in c1_info['unique_characters'] if char not in exclude_chars]
    c2_info['unique_characters'] = [char for char in c2_info['unique_characters'] if char not in exclude_chars]

    
    char_jaccard_similarity = jaccard_similarity(set(c1_info['unique_characters']), set(c2_info['unique_characters']))
    print(f"Jaccard Similarity of unique characters: {char_jaccard_similarity:.2f}")
    if char_jaccard_similarity < .95:
        warnings.warn("The disjunction of character sets should be close to 0. It is recommended to check the unique characters in the orthographic info for the target corpus and the reference corpus.")

    char_overlap_coefficient = overlap_coefficient(set(c1_info['unique_characters']), set(c2_info['unique_characters']))
    print(f"Overlap Coefficient of unique characters: {char_overlap_coefficient:.2f}")

    all_chars = set(c1_info['unique_characters']).union(set(c2_info['unique_characters']))

    c1_freq_vector = np.array([c1_info['character_frequency'].get(char, 0) for char in all_chars])
    c2_freq_vector = np.array([c2_info['character_frequency'].get(char, 0) for char in all_chars])
    c1_freq_vector = normalize_vector(c1_freq_vector)
    c2_freq_vector = normalize_vector(c2_freq_vector)

    cosine_sim = cosine_similarity([c1_freq_vector], [c2_freq_vector])[0][0]
    print(f"Cosine Similarity of character frequencies: {cosine_sim:.2f}")
    if char_jaccard_similarity < .975:
        warnings.warn("Even when different orthographies are being used, cosine similarity is usually >.975.")

    euclidean_dist = euclidean(c1_freq_vector, c2_freq_vector)
    print(f"Euclidean Distance of character frequencies: {euclidean_dist:.2f}")
    if euclidean_dist > .03:
        warnings.warn("Even when different orthographies are being used, Euclidean distance is usually <.03.")

    kl_div = kl_divergence(c1_freq_vector, c2_freq_vector)
    print(f"KL Divergence of character frequencies: {kl_div:.2f}")
    if kl_div > .03:
        warnings.warn("Even when different orthographies are being used, KL divergence is usually <.03.")

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
    if bigram_cosine_sim < .95:
        warnings.warn("Even when different orthographies are being used, bigram cosine similarities are usually >.95.")

    bigram_euclidean_dist = euclidean(c1_bigram_vector, c2_bigram_vector)
    print(f"Euclidean Distance of bigram frequencies: {bigram_euclidean_dist:.2f}")
    if bigram_euclidean_dist < .04:
        warnings.warn("Even when different orthographies are being used, bigram Euclidean distance is usually <.04.")

    vis_diff(all_chars, c1_info['character_frequency'], c2_info['character_frequency'], "_".join(args.o_info.split('_')[1:]), "reference")         
    
if __name__ == "__main__":

    langs = ['Amis', 'Atayal', 'Paiwan', 'Bunun', 'Puyuma', 'Rukai', 'Tsou', 'Saisiyat', 'Yami',
             'Thao', 'Kavalan', 'Truku', 'Sakizaya', 'Seediq', 'Saaroa', 'Siraya', 'Kanakanavu']    
    
    parser = argparse.ArgumentParser(description="Compare orthographic info")
    #parser.add_argument('--verbose', action='store_true', help='increase output verbosity')
    parser.add_argument('--o_info', help='Name of log folder containing orthographic info that will be analyzed. You must be in root directory of corpus repo.')
    parser.add_argument('--language', help='Language code')
    args = parser.parse_args()

    # Validate required arguments
    if not args.o_info:
        parser.error("--o_info is required.")
    if not os.path.exists(os.path.join(os.getcwd(),'QC/orthography/logs',args.o_info, "orthographic_info")):
        parser.error(f"The entered orthographic info, {os.path.join(os.getcwd(),'QC/orthography/logs',args.o_info, "orthographic_info")}, doesn't exist")
    if not args.language in langs:
        parser.error(f"Enter a valid Formosan language from the list: {langs}")

    main(args)
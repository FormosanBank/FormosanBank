import os
import matplotlib.pyplot as plt
import numpy as np
import pickle
import string
import warnings
from sklearn.metrics.pairwise import cosine_similarity
from scipy.spatial.distance import euclidean
from scipy.special import rel_entr
import argparse

plt.switch_backend('Agg')  # Use a non-GUI backend
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']

# Suppress specific warnings about missing glyphs
warnings.filterwarnings("ignore", message="Glyph .* missing from font")

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

def vis_diff(all_chars, c1_char_freq, c2_char_freq, source_1, lang):
    
    # Get the sorted list of characters
    sorted_chars = sorted(all_chars)

    
    # Compute the total number of characters in each corpus
    total_corpus1_chars = sum(c1_char_freq.values())
    total_corpus2_chars = sum(c2_char_freq.values())
    '''
    # Calculate relative frequencies (ratios) for plotting
    corpus1_freqs = [
        0 if c1_char_freq.get(char, 0) == 0 else np.log((c1_char_freq.get(char, 0)+1) / (total_corpus1_chars - c1_char_freq.get(char, 0) + 1)) for char in sorted_chars
    ]
    corpus2_freqs = [
       0 if c2_char_freq.get(char, 0) == 0 else np.log((c2_char_freq.get(char, 0)+1) / (total_corpus2_chars - c2_char_freq.get(char, 0) + 1)) for char in sorted_chars
    ]
    '''

    # Optionally, convert ratios to percentages
    corpus1_freqs = [ 0 if c1_char_freq.get(char, 0) == 0 else  c1_char_freq.get(char, 0) / total_corpus1_chars * 100 for char in sorted_chars ]
    corpus2_freqs = [ 0 if c2_char_freq.get(char, 0) == 0 else  c2_char_freq.get(char, 0) / total_corpus2_chars * 100 for char in sorted_chars ]

    # Plotting
    x = np.arange(len(sorted_chars))  # label locations
    width = 0.35  # width of the bars

    fig, ax = plt.subplots(figsize=(15, 5))
    rects1 = ax.bar(x - width / 2, corpus1_freqs, width, label=source_1)
    rects2 = ax.bar(x + width / 2, corpus2_freqs, width, label="reference")

    # Add labels and title
    ax.set_ylabel('Relative Frequency on log-odds scale')
    ax.set_title(f'Character Relative Frequencies in {source_1} and reference for {lang}')
    ax.set_xticks(x)
    ax.set_xticklabels(sorted_chars)
    ax.legend()

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(os.path.join(source_1, lang + "_frequency_comparison.png"))
    plt.close()


def main(args, possiblelangs):

    if args.language:
        langs = [args.language]
    else:
        langs = os.listdir(args.o_info)
        langs = [lang for lang in langs if lang in possiblelangs]

    for lang in langs:
        # get the orthographic info for the target corpus
        with open(os.path.join(args.o_info, lang, 'orthographic_info'), 'rb') as f:
            c1_info = pickle.load(f)
        print(c1_info.keys())

        # get the reference orthographic info for that language
        with open(os.path.join(args.reference, lang, 'orthographic_info'), 'rb') as f:
            c2_info = pickle.load(f)
        print(c2_info.keys())

        # Filter unique_chars to exclude punctuation and numerals
        exclude_chars = set(string.punctuation + string.digits)
        c1_use_chars = [char for char in c1_info['unique_characters'] if char not in exclude_chars]
        c2_use_chars = [char for char in c2_info['unique_characters'] if char not in exclude_chars]

        # Create a subset of the character frequency dictionaries
        c1_character_frequency = {char: freq for char, freq in c1_info['character_frequency'].items() if char in c1_use_chars}
        c2_character_frequency = {char: freq for char, freq in c2_info['character_frequency'].items() if char in c2_use_chars}

        # Sort characters by frequency in descending order
        c1_sorted_characters = sorted(c1_character_frequency.items(), key=lambda item: item[1], reverse=True)
        c2_sorted_characters = sorted(c2_character_frequency.items(), key=lambda item: item[1], reverse=True)

        # Extract the top 30 characters and their frequencies
        c1_top_30_chars = dict(c1_sorted_characters[:30])
        c2_top_30_chars = dict(c2_sorted_characters[:30])

        # Update c1_info['unique_characters'] to contain only the top 30 characters
        c1_info['unique_characters'] = c1_top_30_chars
        c2_info['unique_characters'] = c2_top_30_chars

        print(c2_top_30_chars)

        char_jaccard_similarity = jaccard_similarity(set(c1_info['unique_characters']), set(c2_info['unique_characters']))
        print(f"Jaccard Similarity of unique characters: {char_jaccard_similarity:.2f}")
        if char_jaccard_similarity < .95:
            print("WARNING: The disjunction of character sets should be close to 0. It is recommended to check the unique characters in the orthographic info for the target corpus and the reference corpus.")

        char_overlap_coefficient = overlap_coefficient(set(c1_info['unique_characters']), set(c2_info['unique_characters']))
        print(f"Overlap Coefficient of unique characters: {char_overlap_coefficient:.2f}")

        all_chars = set(c1_info['unique_characters']).union(set(c2_info['unique_characters']))

        c1_freq_vector = np.array([c1_info['character_frequency'].get(char, 0) for char in all_chars])
        c2_freq_vector = np.array([c2_info['character_frequency'].get(char, 0) for char in all_chars])
        c1_freq_vector = normalize_vector(c1_freq_vector)
        c2_freq_vector = normalize_vector(c2_freq_vector)

        cosine_sim = cosine_similarity([c1_freq_vector], [c2_freq_vector])[0][0]
        print(f"Cosine Similarity of character frequencies: {cosine_sim:.2f}")
        if cosine_sim < .975:
            print("WARNING: Even when different orthographies are being used, cosine similarity is usually >.975.")

        euclidean_dist = euclidean(c1_freq_vector, c2_freq_vector)
        print(f"Euclidean Distance of character frequencies: {euclidean_dist:.2f}")
        if euclidean_dist > .03:
            print("WARNING: Even when different orthographies are being used, Euclidean distance is usually <.03.")

        kl_div = kl_divergence(c1_freq_vector, c2_freq_vector)
        print(f"KL Divergence of character frequencies: {kl_div:.2f}")
        if kl_div > .03:
            print("WARNING: Even when different orthographies are being used, KL divergence is usually <.03.")

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
            print("WARNING: Even when different orthographies are being used, bigram cosine similarities are usually >.95.")

        bigram_euclidean_dist = euclidean(c1_bigram_vector, c2_bigram_vector)
        print(f"Euclidean Distance of bigram frequencies: {bigram_euclidean_dist:.2f}")
        if bigram_euclidean_dist < .04:
            print("WARNING: Even when different orthographies are being used, bigram Euclidean distance is usually <.04.")

        vis_diff(all_chars, c1_info['character_frequency'], c2_info['character_frequency'], args.o_info, lang)         
        
if __name__ == "__main__":
    # Code requires that orthographic info is stored in a folder with the name of a language from this list
    possiblelangs = ['Amis', 'Atayal', 'Paiwan', 'Bunun', 'Puyuma', 'Rukai', 'Tsou', 'Saisiyat', 'Yami',
             'Thao', 'Kavalan', 'Truku', 'Sakizaya', 'Seediq', 'Saaroa', 'Siraya', 'Kanakanavu']    
    
    parser = argparse.ArgumentParser(description="Compare orthographic info")
    #parser.add_argument('--verbose', action='store_true', help='increase output verbosity')
    parser.add_argument('--o_info', help='Path to log folder containing orthographic info that will be analyzed.')
    parser.add_argument('--reference', help='Path to reference orthographic info. If blank, uses whatever is in the reference folder inside QC/validation')
    parser.add_argument('--language', help='Language code. If blank, all languages in o_info will be analyzed.')
    args = parser.parse_args()

    # Validate required arguments
    if not args.o_info:
        parser.error("--o_info is required.")
    if not args.reference:
        parser.error("--reference is required.")
    if not os.path.exists(os.path.join(args.o_info)):
        parser.error(f"The entered orthographic info, {os.path.join(args.o_info)}, doesn't exist")
    if not os.path.exists(os.path.join(args.reference)):
        parser.error(f"The path to reference orthographic info, {os.path.join(args.reference)}, doesn't exist")

    main(args, possiblelangs)
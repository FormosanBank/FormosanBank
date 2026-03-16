import os
import matplotlib.pyplot as plt
import numpy as np
import pickle
import string
from sklearn.metrics.pairwise import cosine_similarity
from scipy.spatial.distance import euclidean
from scipy.special import rel_entr
import argparse
import warnings

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

def compare_vocabulary(c1_dir, c2_dir, label):
    """Compare vocabulary from orthographic_info in c1_dir against the reference in c2_dir."""

    with open(os.path.join(c1_dir, 'orthographic_info'), 'rb') as f:
        c1_info = pickle.load(f)

    ref_path = os.path.join(c2_dir, 'orthographic_info')
    if not os.path.isfile(ref_path):
        print(f"WARNING: No reference orthographic info found at {c2_dir}. Skipping {label}.")
        return
    with open(ref_path, 'rb') as f:
        c2_info = pickle.load(f)

    vocab1 = [word for word, freq in c1_info['word_frequency'].most_common(100)]
    vocab2 = [word for word, freq in c2_info['word_frequency'].most_common(100)]

    warns = False  # flag to check if any warnings were raised

    word_jaccard_similarity = jaccard_similarity(set(vocab1), set(vocab2))
    print(f"Jaccard Similarity of words characters: {word_jaccard_similarity:.2f}")
    if word_jaccard_similarity < .975:
        warns = True
        warnings.warn("The disjunction of character sets should be close to 0.")

    word_overlap_coefficient = overlap_coefficient(set(vocab1), set(vocab2))
    print(f"Overlap Coefficient of unique words: {word_overlap_coefficient:.2f}")
    if word_overlap_coefficient < .975:
        warns = True
        warnings.warn("The disjunction of character sets should be close to 0.")

    if warns:
        unique_to_vocab1 = set(vocab1) - set(vocab2)
        warnings.warn(f"High-frequency words in corpus but not in reference: {unique_to_vocab1}")
        unique_to_vocab2 = set(vocab2) - set(vocab1)
        warnings.warn(f"High-frequency words in reference but not in corpus: {unique_to_vocab2}")


def main(args, possiblelangs):

    if args.language:
        langs = [args.language]
    else:
        langs = sorted([d for d in os.listdir(args.o_info)
                        if os.path.isdir(os.path.join(args.o_info, d))])

    for lang in langs:
        print(f"========== Analyzing {lang} ==========\n")

        lang_path = os.path.join(args.o_info, lang)

        # Determine whether the language folder contains dialect subdirectories or a
        # bare orthographic_info file (non-dialect / legacy layout).
        if os.path.isfile(os.path.join(lang_path, 'orthographic_info')):
            # No dialect subdirectories: compare the language folder directly.
            compare_vocabulary(
                lang_path,
                os.path.join(args.reference, lang),
                lang
            )
        else:
            # Each subdirectory is a dialect (including "default" if present).
            dialects = sorted([
                d for d in os.listdir(lang_path)
                if os.path.isdir(os.path.join(lang_path, d))
                and os.path.isfile(os.path.join(lang_path, d, 'orthographic_info'))
            ])
            if not dialects:
                print(f"WARNING: No orthographic_info found for {lang} in {lang_path}. Skipping.")
                continue
            for dialect in dialects:
                print(f"  --- Dialect: {dialect} ---")
                compare_vocabulary(
                    os.path.join(lang_path, dialect),
                    os.path.join(args.reference, lang, dialect),
                    f"{lang} / {dialect}"
                )

if __name__ == "__main__":
    # Code requires that orthographic info is stored in a folder with the name of a language from this list
    possiblelangs = ['Amis', 'Atayal', 'Paiwan', 'Bunun', 'Puyuma', 'Rukai', 'Tsou', 'Saisiyat', 'Yami',
             'Thao', 'Kavalan', 'Truku', 'Sakizaya', 'Seediq', 'Saaroa', 'Siraya', 'Kanakanavu']    
    
    parser = argparse.ArgumentParser(description="Compare highest frequency words")
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
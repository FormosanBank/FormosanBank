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

def main(args):

    # get the info for the target corpus
    with open(os.path.join(os.getcwd(),'QC/orthography/logs',args.o_info, "orthographic_info"), 'rb') as f:
        c1_info = pickle.load(f)

    # get the reference info for that language
    file_path = os.path.dirname(__file__)
    with open(os.path.join(file_path, "reference", args.language,'orthographic_info'), 'rb') as f:
        c2_info = pickle.load(f)

    vocab1 = [word for word, freq in c1_info['word_frequency'].most_common(100)]
    vocab2 = [word for word, freq in c2_info['word_frequency'].most_common(100)]


    warns = False # flag to check if any warnings were raised

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

if __name__ == "__main__":

    langs = ['Amis', 'Atayal', 'Paiwan', 'Bunun', 'Puyuma', 'Rukai', 'Tsou', 'Saisiyat', 'Yami',
             'Thao', 'Kavalan', 'Truku', 'Sakizaya', 'Seediq', 'Saaroa', 'Siraya', 'Kanakanavu']    
    
    parser = argparse.ArgumentParser(description="Compare highest frequency words")
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
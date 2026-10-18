#!/usr/bin/env python3
"""validate_orthography.py — compare a corpus's letter inventory with the reference.

Informational: prints metrics and WARNING lines and ALWAYS EXITS 0. It is the
reader's job (a port audit, a QC summary) to quote the SUMMARY line.

Inputs
  --o_info     the directory `orthography_extract.py --output_dir` wrote. Either
               the per-dialect layout <Language>/<dialect>/orthographic_info
               (`--by_dialect true`) or the legacy <Language>/orthographic_info.
  --reference  the matching reference tree, normally QC/validation/reference/
               (one orthographic_info per language or per language/dialect).
  --language   restrict to one <Language> directory (default: every one found).

What is compared, per language (or language/dialect) group
  * the set of distinct characters, digits excluded (Jaccard, overlap)
  * the character-frequency distribution over the reference's whole
    inventory plus the corpus's 30 most frequent characters (cosine,
    Euclidean, KL divergence)
  * the character-bigram distribution (cosine, Euclidean)
  Thresholds that print a WARNING: Jaccard < .95, cosine < .975, Euclidean
  > .03, KL > .03, bigram cosine < .95, bigram Euclidean > .04. They were set
  by eye on the existing corpora and are not calibrated; a WARNING is a
  reason to look at the SUMMARY line's corpus_only / reference_only sets,
  not a verdict.

Output
  * the metrics, one per line, with any WARNING lines
  * by default (development use) also the two pickles' key lists and the
    reference's character-frequency table; `--quiet` drops those and the
    matplotlib font messages, leaving the group header, the metric lines,
    the WARNING lines and the SUMMARY line — what the skills run
  * one greppable line per group:
      SUMMARY orthography | <Language> / <dialect> | jaccard=… overlap=… cosine=…
        euclid=… kl=… bigram_cosine=… bigram_euclid=… | corpus_only=[…]
        reference_only=[…] | warnings=N
    corpus_only lists the characters the corpus uses and the reference does
    not; reference_only the reverse. Both are what an auditor should read.
  * <group>_frequency_comparison.png beside the corpus's orthographic_info
  * a group with no reference prints `SUMMARY orthography | <group> |
    reference=missing | warnings=1` and is otherwise skipped

Usage
    python QC/validation/validate_orthography.py \
        --o_info <output_dir>/extract_logs --reference QC/validation/reference [--quiet]
"""
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
import logging

QUIET = False  # --quiet: only the group header, metric lines, WARNING lines and SUMMARY line

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

def vis_diff(all_chars, c1_char_freq, c2_char_freq, output_dir, label):
    
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
    rects1 = ax.bar(x - width / 2, corpus1_freqs, width, label="corpus")
    rects2 = ax.bar(x + width / 2, corpus2_freqs, width, label="reference")

    # Add labels and title
    ax.set_ylabel('Relative Frequency on log-odds scale')
    ax.set_title(f'Character Relative Frequencies in corpus and reference for {label}')
    ax.set_xticks(x)
    ax.set_xticklabels(sorted_chars)
    ax.legend()

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=90)
    plt.tight_layout()
    safe_label = label.replace(' / ', '_').replace('/', '_')
    plt.savefig(os.path.join(output_dir, safe_label + "_frequency_comparison.png"))
    plt.close()


def compare_orthography(c1_dir, c2_dir, label):
    """Compare orthographic info files in c1_dir against the reference in c2_dir.
    Saves the frequency comparison plot to c1_dir."""

    # get the orthographic info for the target corpus
    with open(os.path.join(c1_dir, 'orthographic_info'), 'rb') as f:
        c1_info = pickle.load(f)
    if not QUIET:
        print(c1_info.keys())

    # get the reference orthographic info
    ref_path = os.path.join(c2_dir, 'orthographic_info')
    if not os.path.isfile(ref_path):
        print(f"WARNING: No reference orthographic info found at {c2_dir}. Skipping {label}.")
        print(f"SUMMARY orthography | {label} | reference=missing | warnings=1")
        return None
    with open(ref_path, 'rb') as f:
        c2_info = pickle.load(f)
    if not QUIET:
        print(c2_info.keys())
    warnings_raised = 0

    # Filter unique_chars to exclude numerals
    exclude_chars = set(string.digits)
    c1_use_chars = [char for char in c1_info['unique_characters'] if char not in exclude_chars]
    c2_use_chars = [char for char in c2_info['unique_characters'] if char not in exclude_chars]
    if not c1_use_chars:
        # A group too small to profile (orthography_extract.py now skips these; an older orthographic_info may
        # still hold one): every ratio below would divide by zero.
        print(f"WARNING: {label}: no characters in the corpus profile (too little text). Skipping {label}.")
        print(f"SUMMARY orthography | {label} | corpus=too-small | warnings=1")
        return None

    # Create a subset of the character frequency dictionaries
    c1_character_frequency = {char: freq for char, freq in c1_info['character_frequency'].items() if char in c1_use_chars}
    c2_character_frequency = {char: freq for char, freq in c2_info['character_frequency'].items() if char in c2_use_chars}

    # Sort corpus characters by frequency in descending order
    c1_sorted_characters = sorted(c1_character_frequency.items(), key=lambda item: item[1], reverse=True)

    # Build all_chars from ALL reference characters (the full expected orthography) plus
    # the top 30 most-frequent corpus characters.  Using only the top-30 of each would
    # drop legitimate low-frequency orthographic letters (e.g. 'j' and 'v' in Sakizaya)
    # when they rank below 30 in both the corpus and the reference.
    c1_top_30_chars = dict(c1_sorted_characters[:30])
    all_chars = set(c2_use_chars).union(set(c1_top_30_chars))

    if not QUIET:
        print(c2_character_frequency)

    char_jaccard_similarity = jaccard_similarity(set(c1_use_chars), set(c2_use_chars))
    print(f"Jaccard Similarity of unique characters: {char_jaccard_similarity:.2f}")
    if char_jaccard_similarity < .95:
        warnings_raised += 1
        print("WARNING: The disjunction of character sets should be close to 0. It is recommended to check the unique characters in the orthographic info for the target corpus and the reference corpus.")

    char_overlap_coefficient = overlap_coefficient(set(c1_use_chars), set(c2_use_chars))
    print(f"Overlap Coefficient of unique characters: {char_overlap_coefficient:.2f}")

    c1_freq_vector = np.array([c1_info['character_frequency'].get(char, 0) for char in all_chars])
    c2_freq_vector = np.array([c2_info['character_frequency'].get(char, 0) for char in all_chars])
    c1_freq_vector = normalize_vector(c1_freq_vector)
    c2_freq_vector = normalize_vector(c2_freq_vector)

    cosine_sim = cosine_similarity([c1_freq_vector], [c2_freq_vector])[0][0]
    print(f"Cosine Similarity of character frequencies: {cosine_sim:.2f}")
    if cosine_sim < .975:
        warnings_raised += 1
        print("WARNING: Even when different orthographies are being used, cosine similarity is usually >.975.")

    euclidean_dist = euclidean(c1_freq_vector, c2_freq_vector)
    print(f"Euclidean Distance of character frequencies: {euclidean_dist:.2f}")
    if euclidean_dist > .03:
        warnings_raised += 1
        print("WARNING: Even when different orthographies are being used, Euclidean distance is usually <.03.")

    kl_div = kl_divergence(c1_freq_vector, c2_freq_vector)
    print(f"KL Divergence of character frequencies: {kl_div:.2f}")
    if kl_div > .03:
        warnings_raised += 1
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
        warnings_raised += 1
        print("WARNING: Even when different orthographies are being used, bigram cosine similarities are usually >.95.")

    bigram_euclidean_dist = euclidean(c1_bigram_vector, c2_bigram_vector)
    print(f"Euclidean Distance of bigram frequencies: {bigram_euclidean_dist:.2f}")
    if bigram_euclidean_dist > .04:
        warnings_raised += 1
        print("WARNING: Even when different orthographies are being used, bigram Euclidean distance is usually <.04.")

    vis_diff(all_chars, c1_info['character_frequency'], c2_info['character_frequency'], c1_dir, label)

    corpus_only = sorted(set(c1_use_chars) - set(c2_use_chars))
    reference_only = sorted(set(c2_use_chars) - set(c1_use_chars))
    summary = {
        'label': label,
        'jaccard': char_jaccard_similarity, 'overlap': char_overlap_coefficient,
        'cosine': cosine_sim, 'euclid': euclidean_dist, 'kl': kl_div,
        'bigram_cosine': bigram_cosine_sim, 'bigram_euclid': bigram_euclidean_dist,
        'corpus_only': corpus_only, 'reference_only': reference_only,
        'warnings': warnings_raised,
    }
    print(format_summary(summary))
    return summary


def format_summary(s):
    """One greppable line per group; what an audit quotes."""
    return (
        f"SUMMARY orthography | {s['label']} | "
        f"jaccard={s['jaccard']:.2f} overlap={s['overlap']:.2f} cosine={s['cosine']:.3f} "
        f"euclid={s['euclid']:.3f} kl={s['kl']:.3f} bigram_cosine={s['bigram_cosine']:.3f} "
        f"bigram_euclid={s['bigram_euclid']:.3f} | "
        f"corpus_only=[{''.join(s['corpus_only'])}] reference_only=[{''.join(s['reference_only'])}] | "
        f"warnings={s['warnings']}"
    )


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
            compare_orthography(
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
                compare_orthography(
                    os.path.join(lang_path, dialect),
                    os.path.join(args.reference, lang, dialect),
                    f"{lang} / {dialect}"
                )
        
if __name__ == "__main__":
    # Code requires that orthographic info is stored in a folder with the name of a language from this list
    possiblelangs = ['Amis', 'Atayal', 'Paiwan', 'Bunun', 'Puyuma', 'Rukai', 'Tsou', 'Saisiyat', 'Yami',
             'Thao', 'Kavalan', 'Truku', 'Sakizaya', 'Seediq', 'Saaroa', 'Siraya', 'Kanakanavu']    
    
    parser = argparse.ArgumentParser(description="Compare orthographic info")
    #parser.add_argument('--verbose', action='store_true', help='increase output verbosity')
    parser.add_argument('--o_info', help='Path to log folder containing orthographic info that will be analyzed.')
    parser.add_argument('--reference', help='Path to reference orthographic info. If blank, uses whatever is in the reference folder inside QC/validation')
    parser.add_argument('--language', help='Language code. If blank, all languages in o_info will be analyzed.')
    parser.add_argument('--quiet', action='store_true',
                        help='Print only the group header, the metric lines, WARNING lines and the SUMMARY line '
                             '(what the skills run). Default is the full development output.')
    args = parser.parse_args()
    QUIET = args.quiet
    if QUIET:
        logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)

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
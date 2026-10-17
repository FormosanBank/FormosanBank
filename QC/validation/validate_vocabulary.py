#!/usr/bin/env python3
"""validate_vocabulary.py — compare a corpus's most frequent words with the reference.

Informational: prints metrics and warnings and ALWAYS EXITS 0. The reader (a
port audit, a QC summary) quotes the SUMMARY line.

Inputs: the same --o_info / --reference / --language as validate_orthography.py
(the orthographic_info pickles written by orthography_extract.py, per language
or per language/dialect, and QC/validation/reference/).

What is compared, per group: the 100 most frequent words of the corpus against
the 100 most frequent words of the reference — Jaccard similarity and overlap
coefficient of the two sets. A warning is raised when either is below .975,
and the words on each side only are then listed. The thresholds are
uncalibrated and the comparison is noisy across genres (a dictionary's top
words are not a narrative's), so read the two word lists, not just the
numbers.

Output: the two metrics, a warning when either falls below threshold (a
Python `warnings` message on stderr by default; with `--quiet` a plain
`WARNING: …` line on stdout, which is what the skills run), and one
greppable line per group:
    SUMMARY vocabulary | <Language> / <dialect> | top100_jaccard=… overlap=… |
      corpus_only=[w1 w2 …] reference_only=[…] | warnings=N
A group with no reference prints `SUMMARY vocabulary | <group> |
reference=missing | warnings=1`.

Usage
    python QC/validation/validate_vocabulary.py \
        --o_info <output_dir>/extract_logs --reference QC/validation/reference [--quiet]
"""
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

QUIET = False  # --quiet: warnings as plain WARNING lines on stdout, no font messages


def _warn(message):
    if QUIET:
        print("WARNING: " + message)
    else:
        warnings.warn(message)


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
        print(f"SUMMARY vocabulary | {label} | reference=missing | warnings=1")
        return None
    with open(ref_path, 'rb') as f:
        c2_info = pickle.load(f)

    vocab1 = [word for word, freq in c1_info['word_frequency'].most_common(100)]
    vocab2 = [word for word, freq in c2_info['word_frequency'].most_common(100)]

    warns = False  # flag to check if any warnings were raised

    word_jaccard_similarity = jaccard_similarity(set(vocab1), set(vocab2))
    print(f"Jaccard Similarity of top-100 words: {word_jaccard_similarity:.2f}")
    if word_jaccard_similarity < .975:
        warns = True
        _warn("Top-100 word overlap with the reference is low (Jaccard < .975).")

    word_overlap_coefficient = overlap_coefficient(set(vocab1), set(vocab2))
    print(f"Overlap Coefficient of unique words: {word_overlap_coefficient:.2f}")
    if word_overlap_coefficient < .975:
        warns = True
        _warn("Top-100 word overlap with the reference is low (overlap coefficient < .975).")

    unique_to_vocab1 = sorted(set(vocab1) - set(vocab2))
    unique_to_vocab2 = sorted(set(vocab2) - set(vocab1))
    if warns:
        _warn(f"High-frequency words in corpus but not in reference: {unique_to_vocab1}")
        _warn(f"High-frequency words in reference but not in corpus: {unique_to_vocab2}")
    summary = {
        'label': label, 'jaccard': word_jaccard_similarity, 'overlap': word_overlap_coefficient,
        'corpus_only': unique_to_vocab1, 'reference_only': unique_to_vocab2,
        'warnings': (1 if word_jaccard_similarity < .975 else 0) + (1 if word_overlap_coefficient < .975 else 0),
    }
    print(format_summary(summary))
    return summary


def format_summary(s):
    """One greppable line per group; what an audit quotes."""
    return (
        f"SUMMARY vocabulary | {s['label']} | "
        f"top100_jaccard={s['jaccard']:.2f} overlap={s['overlap']:.2f} | "
        f"corpus_only=[{' '.join(s['corpus_only'])}] reference_only=[{' '.join(s['reference_only'])}] | "
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
    parser.add_argument('--quiet', action='store_true',
                        help='Warnings as plain WARNING lines on stdout and no matplotlib font messages '
                             '(what the skills run). Default is the full development output.')
    args = parser.parse_args()
    QUIET = args.quiet
    if QUIET:
        import logging
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
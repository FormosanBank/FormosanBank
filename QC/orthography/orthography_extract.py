import xml.etree.ElementTree as ET
import html
import os
import unicodedata
import collections
import regex as re
import string
import matplotlib.pyplot as plt
from matplotlib import font_manager
import seaborn as sns
import pandas as pd
import numpy as np
import pickle
import argparse
import math
import random
import warnings
from pathlib import Path

# Suppress specific warnings about missing glyphs
warnings.filterwarnings("ignore", message="Glyph .* missing from font")

plt.switch_backend('Agg')  # Use a non-GUI backend
# plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
# Set the font properties globally
#plt.rcParams['font.family'] = 'Noto Sans'


def _dialects_path():
    candidate = Path(__file__).resolve().parents[2] / "dialects.csv"
    if candidate.exists():
        return candidate
    return Path("dialects.csv")


def is_dialect(lang, dialect):
    dialect_csv = pd.read_csv(_dialects_path())
    return (dialect in dialect_csv[dialect_csv['Language'] == lang]['Official'].unique())


def is_lang(lang):
    dialect_csv = pd.read_csv(_dialects_path())
    return lang in dialect_csv['Language'].unique()


def parse_bool(value):
    if isinstance(value, bool):
        return value
    if value.lower() in {"1", "true", "t", "yes", "y"}:
        return True
    if value.lower() in {"0", "false", "f", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError("Expected a boolean value such as true or false.")

def generate_corpus(language_to_process, to_check_path, kindOf, by_dialect=False):
    corpus = {}
    if not by_dialect:
        corpus["default"] = ""
    if not os.path.exists(to_check_path):
        raise ValueError(f"corpus {to_check_path} doesn't exist")
    for root, dirs, files in os.walk(to_check_path):
        for file in files:
            if file.endswith(".xml") and re.findall(language_to_process, os.path.join(root)): # and 'Final_XML' in os.path.join(root, file) 
                tree = ET.parse(os.path.join(root, file))
                root_to_read = tree.getroot()
                
                text = ""        

                # Iterate over all <S> elements
                for s in root_to_read.findall('.//S'):
                    # Find the <FORM> element within the <S> element
                    if kindOf:
                        form = s.find(f"FORM[@kindOf='{kindOf}']")
                        if form is not None:
                            if form.text:
                                text += " " + form.text
                    else:
                        #if the kindOf attribute is not specified, add the form text to the corpus
                        forms = s.findall('FORM')
                        for form in forms:
                            if form.text:
                                text += " " + form.text

                # Now store
                if by_dialect:                
                    if not 'dialect' in root_to_read.attrib:
                        print(f"WARNING: No dialect found in the corpus for {file}")  
                        current_dialect = "default"
                    else:
                        current_dialect = root_to_read.attrib['dialect']
                    if current_dialect in corpus.keys():
                        corpus[current_dialect] += text
                    else:
                        # should only add to corpus if legal dialect
                        if is_dialect(language_to_process, current_dialect):
                            corpus[current_dialect] = text
                else:
                    corpus["default"] += text

    return corpus

def remove_chinese_characters(text):
    # Define a regex pattern for Chinese characters
    chinese_char_pattern = r'[\u4e00-\u9fff]+'
    # Remove Chinese characters
    text_without_chinese = re.sub(chinese_char_pattern, '', text)
    return text_without_chinese

def extract_orthographic_info(text):

    # Decode any HTML/XML entity references embedded as LITERAL text in
    # FORM/TRANSL content. This handles cases where source scrapers
    # produced literal "&amp;", "&lt;", "&gt;", "&nbsp;", "&quot;",
    # numeric character references etc. as part of the FORM text rather
    # than as XML entities (which lxml would already have decoded at
    # parse time). Without this, each occurrence of "&amp;" is counted
    # as five separate characters ("&", "a", "m", "p", ";") instead of
    # the single intended character — polluting orthography statistics
    # and downstream similarity metrics (which feed B4 threshold
    # calibration). Per roadmap B7.
    text = html.unescape(text)

    text = text.lower()
    #text = remove_chinese_characters(text)
    # Normalize text to NFC form (canonical decomposition followed by canonical composition)
    text_nfc = unicodedata.normalize('NFC', text)

    orthographic_info = {}

    # Get list of unique characters and their freq
    unique_chars = list(set(text_nfc))
    unique_chars.sort()
    if " " in unique_chars:
        unique_chars.remove(" ")
    char_freq = collections.Counter(text_nfc)
    char_freq.pop(" ", None)
    
    temp = unique_chars[:]
    for c in temp:
        if char_freq[c] < 5:
            del char_freq[c]
            unique_chars.remove(c)
    
    orthographic_info['unique_characters'] = unique_chars
    orthographic_info['character_frequency'] = char_freq

    # Classification of characters
    char_classes = {}
    for char in unique_chars:
        category = unicodedata.category(char)  # e.g., 'Ll' for Letter, lowercase
        char_classes.setdefault(category, []).append(char)
    orthographic_info['character_classes'] = char_classes

    # Diacritics and base characters
    base_chars = {}
    diacritics = {}
    for char in unique_chars:
        decomposition = unicodedata.decomposition(char)
        if decomposition:
            decomp_parts = decomposition.split()
            base = decomp_parts[0]
            if base.startswith('<'):
                # It's a compatibility character, skip it
                continue
            base_char = chr(int(base, 16))
            base_chars.setdefault(base_char, []).append(char)
            for part in decomp_parts[1:]:
                if part.startswith('<'):
                    continue
                diacritic_char = chr(int(part, 16))
                diacritics[diacritic_char] = diacritics.get(diacritic_char, 0) + text_nfc.count(char)
    if base_chars and diacritics:
        orthographic_info['base_characters'] = base_chars
        orthographic_info['diacritics'] = diacritics
    
    
    # N-gram analysis (e.g., bigrams)
    n = 2  # You can change this to 3 for trigrams, etc.
    ngrams = [
    text_nfc[i:i+n]
    for i in range(len(text_nfc) - n + 1)
    if ' ' not in text_nfc[i:i+n]
    ]
    ngram_counter = collections.Counter(ngrams)

    filtered_ngram_freq = {
        ngram: count for ngram, count in ngram_counter.items() if count >= 5
    }
    orthographic_info[f'{n}-grams'] = filtered_ngram_freq
    
   
    # Punctuation and special symbols
    punctuation = {}
    for char in unique_chars:
        if unicodedata.category(char).startswith('P'):
            punctuation[char] = char_freq[char]
    orthographic_info['punctuation'] = punctuation

    # # Numerals
    # numerals = {}
    # for char in unique_chars:
    #     if unicodedata.category(char) == 'Nd':
    #         numerals[char] = char_freq[char]
    # orthographic_info['numerals'] = numerals
    
    #word freq
    punctuation_without_apostrophe = string.punctuation.replace("'", "")
    translator = str.maketrans('', '', punctuation_without_apostrophe)
    text_no_punct = text_nfc.translate(translator)
    words = text_no_punct.split()
    word_freq = collections.Counter(words)
    orthographic_info['word_frequency'] = word_freq

    return orthographic_info

def visualize(o_info, output_folder):
    
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    if not o_info.get('unique_characters') or not o_info.get('character_frequency'):
        with open(os.path.join(output_folder, 'unique_characters.txt'), 'w', encoding='utf-8') as f:
            f.write("Unique Characters:\nNone\n")
        return
    
    """
    Get a set of unique characters
    """
    unique_chars = o_info['unique_characters']

    # Sort characters for display
    sorted_chars = sorted(unique_chars)

    # Save unique characters to a text file
    unique_chars_file = os.path.join(output_folder, 'unique_characters.txt')
    with open(unique_chars_file, 'w', encoding='utf-8') as f:
        f.write("Unique Characters:\n")
        for i, char in enumerate(sorted_chars, 1):
            f.write(f"{char} ")
            if i % 20 == 0:
                f.write("\n")
        f.write('\n')  # Add a newline after the grid

    """
    Visualize Character Frequency
    """

    char_freq = o_info['character_frequency']

    # Convert to a sorted list
    sorted_char_freq = char_freq.most_common()

    # Separate characters and frequencies
    characters, frequencies = zip(*sorted_char_freq)

    # Number of characters per row
    N = 35

    # Calculate the number of rows needed
    num_rows = math.ceil(len(characters) / N)

    fig, axes = plt.subplots(num_rows, 1, figsize=(12, 6 * num_rows))

    if num_rows == 1:
        axes = [axes]

    # Determine the maximum frequency for consistent y-axis range
    max_frequency = max(frequencies)

    for i in range(num_rows):
        start = i * N
        end = start + N
        row_characters = characters[start:end]
        row_frequencies = frequencies[start:end]

        sns.barplot(ax=axes[i], x=list(row_characters), y=list(row_frequencies), palette="viridis", hue=list(row_characters), dodge=False, legend=False)
        axes[i].set_xlabel('Characters')
        axes[i].set_ylabel('Frequency')
        axes[i].set_title(f'Character Frequencies (Row {i + 1})')
        axes[i].set_ylim(0, max_frequency)  # Set consistent y-axis range
        axes[i].tick_params(axis='x', labelsize=10)
        axes[i].tick_params(axis='y', labelsize=10)

    # Save the figure
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'character_frequencies.png'))
    plt.close()

    """
    Visualize Distribution of Character Classes
    """
    char_classes = o_info['character_classes']

    # Count the number of characters in each class
    class_counts = {cls: len(chars) for cls, chars in char_classes.items()}

    # Prepare data for pie chart
    labels = list(class_counts.keys())
    sizes = list(class_counts.values())

    # Map of category abbreviations to full names
    category_full_names = {
        'Lu': 'Letter, uppercase',
        'Ll': 'Letter, lowercase',
        'Lt': 'Letter, titlecase',
        'Lm': 'Letter, modifier',
        'Lo': 'Letter, other',
        'Mn': 'Mark, nonspacing',
        'Mc': 'Mark, spacing combining',
        'Me': 'Mark, enclosing',
        'Nd': 'Number, decimal digit',
        'Nl': 'Number, letter',
        'No': 'Number, other',
        'Pc': 'Punctuation, connector',
        'Pd': 'Punctuation, dash',
        'Ps': 'Punctuation, open',
        'Pe': 'Punctuation, close',
        'Pi': 'Punctuation, initial quote',
        'Pf': 'Punctuation, final quote',
        'Po': 'Punctuation, other',
        'Sm': 'Symbol, math',
        'Sc': 'Symbol, currency',
        'Sk': 'Symbol, modifier',
        'So': 'Symbol, other',
        'Zs': 'Separator, space',
        'Zl': 'Separator, line',
        'Zp': 'Separator, paragraph',
        'Cc': 'Other, control',
        'Cf': 'Other, format',
        'Cs': 'Other, surrogate',
        'Co': 'Other, private use',
        'Cn': 'Other, not assigned',
    }

    # Get full names for labels in the legend
    legend_labels = [f"{cls}: {category_full_names.get(cls, 'Unknown')}" for cls in labels]

    # Plot pie chart with labels inside wedges
    plt.figure(figsize=(8, 8))
    wedges, texts, autotexts = plt.pie(
        sizes,
        labels=labels,
        autopct='%1.1f%%',
        startangle=140,
        textprops={'color': 'w'}
    )

    # Style the labels inside the wedges
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(10)

    # Add a legend explaining the abbreviations
    plt.legend(
        wedges,
        legend_labels,
        title="Categories",
        loc="center left",
        bbox_to_anchor=(1, 0, 0.5, 1)
    )

    plt.title('Distribution of Character Classes')
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    # Save the figure
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'character_class_distribution.png'))
    plt.close()

    """
    Visualize 2-gram Frequency Distribution
    """
    # First method: Heatmap
    bigrams = o_info['2-grams']

    # Get the list of unique characters used in bigrams
    chars_in_bigrams = set(''.join(bigrams.keys()))

    # Create a DataFrame to hold bigram frequencies
    bigram_matrix = pd.DataFrame(
        data=np.zeros((len(chars_in_bigrams), len(chars_in_bigrams)), dtype=int),
        index=sorted(chars_in_bigrams),
        columns=sorted(chars_in_bigrams)
    )

    # Fill the DataFrame with bigram frequencies
    for bigram, freq in bigrams.items():
        if len(bigram) == 2:
            bigram_matrix.loc[bigram[0], bigram[1]] = freq

    # Plot the heatmap
    plt.figure(figsize=(12, 10))
    sns.heatmap(bigram_matrix, cmap='Blues')
    plt.title('Bigram Frequency Heatmap')
    plt.xlabel('Second Character')
    plt.ylabel('First Character')

    # Save the figure
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'bigram_heatmap.png'))
    plt.close()

    # Second method: Bar Chart of Top Bigrams
    sorted_bigrams = sorted(bigrams.items(), key=lambda x: x[1], reverse=True)

    # Limit to top N bigrams
    N = 30
    top_bigrams = sorted_bigrams[:N]
    bigrams_list, frequencies = zip(*top_bigrams)

    plt.figure(figsize=(12, 6))
    sns.barplot(x=list(bigrams_list), y=list(frequencies), palette="magma", legend=False, dodge=False, hue=list(bigrams_list))
    plt.xlabel('Bigrams')
    plt.ylabel('Frequency')
    plt.title('Top Bigrams')
    plt.xticks(rotation=90)

    # Save the figure
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'top_bigrams.png'))
    plt.close()

    """
    Visualize Punctuation Frequency Distribution
    """
    punctuation = o_info['punctuation']

    # Sort punctuation by frequency
    sorted_punct = sorted(punctuation.items(), key=lambda x: x[1], reverse=True)
    punct_marks, frequencies = zip(*sorted_punct)

    plt.figure(figsize=(8, 4))
    sns.barplot(x=list(punct_marks), y=list(frequencies), palette="cool", legend=False, dodge=False, hue=list(punct_marks))
    plt.xlabel('Punctuation Marks')
    plt.ylabel('Frequency')
    plt.title('Punctuation Frequencies')

    # Save the figure
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'punctuation_frequencies.png'))
    plt.close()

    """
    Visualize Word Frequency Distribution
    """
    word_freq = o_info['word_frequency']

    # Bar Chart of Top Words
    sorted_word_freq = word_freq.most_common(20)
    words, frequencies = zip(*sorted_word_freq)

    plt.figure(figsize=(12, 6))
    sns.barplot(x=list(words), y=list(frequencies), palette="viridis", legend=False, dodge=False, hue=list(words))
    plt.xlabel('Words')
    plt.ylabel('Frequency')
    plt.title('Top 20 Words')
    plt.xticks(rotation=45)

    # Save the figure
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'top_words.png'))
    plt.close()

def run_reference_simulations(language_to_process, dialect, corpora_paths, output_dir, num_sim=5, ref_ratio=0.8, kindOf="standard", by_dialect=True, verbose=True, seed=0):
    if not is_lang(language_to_process):
        raise ValueError(f"Target language not recognized: {language_to_process}")
    if not corpora_paths:
        raise ValueError("At least one corpus path is required")

    combined_text = ""
    for path in corpora_paths:
        if not os.path.exists(path):
            raise ValueError(f"corpus {path} doesn't exist")
        corpus = generate_corpus(language_to_process, path, kindOf, by_dialect=by_dialect)
        if by_dialect:
            combined_text += corpus.get(dialect, "")
        else:
            combined_text += corpus.get("default", "")

    combined_text = remove_chinese_characters(combined_text)
    sentences = re.split(r'(?<=[.!?])\s+', combined_text)
    sentences = [sentence.strip() for sentence in sentences if sentence and sentence.strip()]
    if not sentences:
        raise ValueError("No sentences were found for the requested dialect")

    rng = random.Random(seed)
    created_dirs = []
    output_root = Path(output_dir)

    for sim_idx in range(num_sim):
        ref_sentences = rng.sample(sentences, math.ceil(ref_ratio * len(sentences)))
        target_sentences = [sentence for sentence in sentences if sentence not in ref_sentences]
        ref_text = "".join(ref_sentences)
        target_text = "".join(target_sentences)

        partition_dir = output_root / language_to_process / dialect / f"partition_{sim_idx + 1}"
        partition_dir.mkdir(parents=True, exist_ok=True)

        reference_info = extract_orthographic_info(ref_text)
        with open(partition_dir / "orthographic_info", "wb") as fp:
            pickle.dump(reference_info, fp)
        visualize(reference_info, partition_dir)

        target_info = extract_orthographic_info(target_text)
        with open(partition_dir / "target_orthographic_info", "wb") as fp:
            pickle.dump(target_info, fp)

        if verbose:
            print(f"Wrote reference simulation {sim_idx + 1} to {partition_dir}")
        created_dirs.append(str(partition_dir))

    return created_dirs


def main(args, langs):
    if args.corpus == "all":
        to_check_path = args.corpora_path
    else:
        to_check_path = os.path.join(args.corpora_path, args.corpus)

    logs_dir = args.output_dir or os.path.join(to_check_path, "extract_logs")
    os.makedirs(logs_dir, exist_ok=True)

    if args.language == 'All':
        languages_to_process = langs
    else:
        languages_to_process = [args.language]

    for language in languages_to_process:
        corpus = None

        corpus = generate_corpus(language, to_check_path, args.kindOf, args.by_dialect)
        for corp in corpus.keys():
            if corpus[corp]:
                o_info = extract_orthographic_info(corpus[corp])
                if args.by_dialect:
                    output_folder = os.path.join(logs_dir, language, corp)
                else:
                    output_folder = os.path.join(logs_dir, language)
                os.makedirs(output_folder, exist_ok=True) #make the folder if needed. Doesn't overwrite.
                with open(os.path.join(output_folder, "orthographic_info"), 'wb') as fp:
                    pickle.dump(o_info, fp)
                visualize(o_info, output_folder)
                print(f"Successfully extracted orthographic information for {corp} from {language} using {to_check_path}")
            else:
                print(f"Warning: Unable to extract the orthographic information for {corp} from {language}. generate_corpus function didn't return any corpus")
    
if __name__ == "__main__":

    langs = ['Amis', 'Atayal', 'Paiwan', 'Bunun', 'Puyuma', 'Rukai', 'Tsou', 'Saisiyat', 'Yami',
             'Thao', 'Kavalan', 'Truku', 'Sakizaya', 'Seediq', 'Saaroa', 'Siraya', 'Kanakanavu']
    
    parser = argparse.ArgumentParser(description="Extract orthographic info")
    #parser.add_argument('--verbose', action='store_true', help='increase output verbosity')
    parser.add_argument('--corpora_path', help='the path to the corpus')
    parser.add_argument('--corpus', help='Set to "all" to process all corpora in the corpora_path. Otherwise, provide name of corpus.')
    parser.add_argument('--language', help='Language code')
    parser.add_argument('--kindOf', help='which XML tier to consider. Defaults to all, which is a problem if there is both an original and standard tier.')
    parser.add_argument('--by_dialect', nargs='?', const=True, default=False, type=parse_bool,
                        help='Process corpora by dialect. Accepts true/false; passing the flag alone means true.')
    parser.add_argument('--output_dir',
                        help='Directory for extracted orthographic info and plots. Defaults to <corpus>/extract_logs.')
    parser.add_argument('--simulate_references', action='store_true',
                        help='Generate partition-based reference orthographic_info files for simulation workflows.')
    parser.add_argument('--dialect', help='Dialect to use when generating reference simulations.')
    parser.add_argument('--num_sim', type=int, default=5,
                        help='Number of reference partitions to generate when --simulate_references is set.')
    parser.add_argument('--ref_ratio', type=float, default=0.8,
                        help='Fraction of sentences used as the reference corpus in each simulation.')
    args = parser.parse_args()

    # Validate required arguments
    if not args.language or not args.corpora_path or not args.corpus:
        parser.error("--language and --corpora_path and --corpus are required.")
    if not os.path.exists(os.path.join(args.corpora_path)):
        parser.error(f"The entered path, {args.corpora_path}, doesn't exist")
    if args.language != "All" and not args.language in langs:
        parser.error(f"Enter a valid Formosan language from the list: {langs}")
    if args.corpus != "all" and not os.path.exists(os.path.join(args.corpora_path, args.corpus)):
        parser.error(f"The entered corpus doesn't exist: {os.path.join(args.corpora_path, args.corpus)}")
    if args.simulate_references:
        if not args.dialect:
            parser.error("--dialect is required when --simulate_references is set")
        corpora_paths = [os.path.join(args.corpora_path, args.corpus)] if args.corpus != "all" else [args.corpora_path]
        run_reference_simulations(
            language_to_process=args.language,
            dialect=args.dialect,
            corpora_paths=corpora_paths,
            output_dir=args.output_dir or os.path.join(args.corpora_path, "reference_simulations"),
            num_sim=args.num_sim,
            ref_ratio=args.ref_ratio,
            kindOf=args.kindOf,
            by_dialect=True,
            verbose=True,
        )
        raise SystemExit(0)
    main(args, langs)

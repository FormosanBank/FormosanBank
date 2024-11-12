import glob
import xml.etree.ElementTree as ET
import os
import unicodedata
import collections
import regex as re
import string
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import pandas as pd
import numpy as np
import pickle
from sklearn.metrics.pairwise import cosine_similarity
from scipy.spatial.distance import euclidean
from scipy.special import rel_entr
import argparse
from tqdm import tqdm

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']

def get_lang(path, langs):
    for lang in langs:
        if lang in path:
            return lang

def generate_corpus(lang, langs, to_check_path):

    corpus = ""
    
    if not os.path.exists(to_check_path):
        raise ValueError(f"corpus {to_check_path} doesn't exist")

    for root, dirs, files in os.walk(to_check_path):
        for file in files:
            if file.endswith(".xml") and get_lang(os.path.join(root, file), langs) == lang and 'Final_XML' in os.path.join(root, file):       
                tree = ET.parse(os.path.join(root, file))
                root_to_read = tree.getroot()
                
                # Iterate over all <S> elements
                for s in root_to_read.findall('.//S'):
                    # Find the <FORM> element within the <S> element
                    form = s.find('FORM')
                    if form.text is not None:
                        corpus += " " + form.text
    return corpus

def remove_chinese_characters(text):
    # Define a regex pattern for Chinese characters
    chinese_char_pattern = r'[\u4e00-\u9fff]+'
    # Remove Chinese characters
    text_without_chinese = re.sub(chinese_char_pattern, '', text)
    return text_without_chinese

def extract_orthographic_info(text):
    
    text = text.lower()
    text = remove_chinese_characters(text)
    # Normalize text to NFC form (canonical decomposition followed by canonical composition)
    text_nfc = unicodedata.normalize('NFC', text)

    orthographic_info = {}

    # Get list of unique characters and their freq
    unique_chars = list(set(text_nfc))
    unique_chars.sort()
    unique_chars.remove(" ")

    char_freq = collections.Counter(text_nfc)
    del char_freq[" "]
    
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
    translator = str.maketrans('', '', string.punctuation)
    text_no_punct = text_nfc.translate(translator)
    text_no_punct = re.sub(r'\p{P}+', '', text_no_punct)
    words = text_no_punct.split()
    word_freq = collections.Counter(words)
    orthographic_info['word_frequency'] = word_freq

    return orthographic_info

def visualize(o_info, output_folder):
    
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
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

    # Limit to top N characters to avoid clutter
    N = 30
    characters = characters[:N]
    frequencies = frequencies[:N]

    plt.figure(figsize=(12, 6))
    sns.barplot(x=list(characters), y=list(frequencies), palette="viridis", legend=False, dodge=False, hue=list(characters))
    plt.xlabel('Characters')
    plt.ylabel('Frequency')
    plt.title('Top Character Frequencies')

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
    # First method: Word Cloud
    word_freq = o_info['word_frequency']

    # Generate a word cloud
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(word_freq)

    # Display the generated image
    plt.figure(figsize=(15, 7.5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title('Word Cloud of Word Frequencies')

    # Save the figure
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'word_cloud.png'))
    plt.close()

    # Second method: Bar Chart of Top Words
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

def vis_diff(all_chars, c1_char_freq, c2_char_freq):
    
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
    rects1 = ax.bar(x - width / 2, corpus1_freqs, width, label='ePark')
    rects2 = ax.bar(x + width / 2, corpus2_freqs, width, label='Dicts')

    # Add labels and title
    ax.set_ylabel('Relative Frequency')
    ax.set_title('Character Relative Frequencies in Corpus 1 and Corpus 2')
    ax.set_xticks(x)
    ax.set_xticklabels(sorted_chars)
    ax.legend()

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()

def compare_corpora(c1_info, c2_info):
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

    vis_diff(all_chars, c1_info['character_frequency'], c2_info['character_frequency'])

def extract_o_info(args, langs):
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    orthograpy_dir = os.path.join(curr_dir, "orthography")
    os.makedirs(orthograpy_dir, exist_ok=True)

    if args.corpus == 'All':
        output_folder = os.path.join(orthograpy_dir, f"{args.language}_All")
    else:
        corpus = os.path.basename(os.path.normpath(args.corpus))
        output_folder = os.path.join(orthograpy_dir, f"{args.language}_{corpus}")
    os.makedirs(output_folder, exist_ok=True)

    corpus_path = args.corpus
    if args.corpus == "All":
        corpus_path = args.corpora_path
    
    corpus = generate_corpus(args.language, langs, corpus_path)
    if corpus:
        o_info = extract_orthographic_info(corpus)

        with open(os.path.join(output_folder, "orthographic_info"), 'wb') as fp:
            pickle.dump(o_info, fp)
        
        visualize(o_info, output_folder)
        print(f"Successfully extracted orthographic information for {args.language} using {args.corpus}")
    else:
        print("there has been an error extracting the orthographic information. generate_corpus function didn't return any corpus")

def main(args, langs, curr_dir):

    if args.task == "extract":
        extract_o_info(args, langs)
    
    elif args.task == "compare":
        
        with open(os.path.join(curr_dir, "orthography", args.orthographic_info_1, "orthographic_info"), 'rb') as f:
            c1_info = pickle.load(f)
        with open(os.path.join(curr_dir, "orthography", args.orthographic_info_2, "orthographic_info"), 'rb') as f:
            c2_info = pickle.load(f)
            
        compare_corpora(c1_info, c2_info)
    
if __name__ == "__main__":

    curr_dir = os.path.dirname(os.path.abspath(__file__))
    langs = ['Amis', 'Atayal', 'Paiwan', 'Bunun', 'Puyuma', 'Rukai', 'Tsou', 'Saisiyat', 'Yami',
             'Thao', 'Kavalan', 'Truku', 'Sakizaya', 'Seediq', 'Saaroa', 'Kanakanavu']
    
    parser = argparse.ArgumentParser(description="Extract and compare orthographic info")
    #parser.add_argument('--verbose', action='store_true', help='increase output verbosity')
    parser.add_argument('task', choices=['extract', 'compare'],
                        help='Specify whether you want to extract orthographic info of a corpus or compare orthographic info of two corpora')
    parser.add_argument('--language', help='Language code (required for extract)')
    parser.add_argument('--corpus', help='the corpus path out of which orthographic info will be extracted. Could be set to "All" (required for extract)')
    parser.add_argument('--corpora_path', help='corpora path if corpus is set to "All" (required for extract if corpus is "All")')
    parser.add_argument('--orthographic_info_1', help='extracted orthographic info that will be used in comparison. Should be in the orthography folder. format is Lang_Corpus (required for compare)')
    parser.add_argument('--orthographic_info_2', help='extracted orthographic info that will be used in comparison. Should be in the orthography folder. format is Lang_Corpus (required for compare)')
    args = parser.parse_args()

    # Validate required arguments based on 'search_by'
    if args.task == 'extract':
        if not args.language or not args.corpus:
            parser.error("For 'extract', --language and --corpus are required.")
        if args.language not in langs:
            parser.error(f"Enter a valid Formosan language from the list: {langs}")
        if args.corpus != "All" and not os.path.exists(args.corpus):
            parser.error(f"The entered corpus path, {args.corpus}, doesn't exist")
        if args.corpus == "All" and not args.corpora_path:
            parser.error("if --corpus is set to 'All', --corpora_path is required")
        if args.corpus == "All" and not os.path.exists(args.corpora_path):
            parser.error(f"The entered corpora path, {args.corpora_path}, doesn't exist")
    
    elif args.task == 'compare':
        if not args.orthographic_info_1 or not args.orthographic_info_2:
            parser.error("For 'compare', --orthographic_info_1 and orthographic_info_2 are required.")
        if not os.path.exists(os.path.join(curr_dir, "orthography", args.orthographic_info_1, "orthographic_info")):
            parser.error(f"The entered orthographic info, {args.orthographic_info_1}, doesn't exist")
        if not os.path.exists(os.path.join(curr_dir, "orthography", args.orthographic_info_2, "orthographic_info")):
            parser.error(f"The entered orthographic info, {args.orthographic_info_2}, doesn't exist")

    main(args, langs, curr_dir)
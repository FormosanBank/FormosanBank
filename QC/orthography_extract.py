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

def generate_corpus(lang):

    curr_dir = os.path.dirname(os.path.abspath(__file__))
    corp_path = os.path.join(curr_dir, "..", "Corpora")
    lang_dirs, corpus = list(), ""
        

    for dirpath, dirnames, filenames in os.walk(corp_path):
        if lang in dirnames:
            lang_dir = os.path.join(dirpath, lang)
            lang_dirs.append(lang_dir)

    for source in lang_dirs:   
        xml_files = glob.glob(os.path.join(source, '**/*.xml'), recursive=True)
        for file_path in xml_files:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Iterate over all <S> elements
            for s in root.findall('.//S'):
                # Find the <FORM> element within the <S> element
                form = s.find('FORM')
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

    """
    Save the orthographic info in a pickle
    """
    with open(os.path.join(output_folder, "orthographic_info"), 'wb') as fp:
        pickle.dump(o_info, fp)

def main():
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    orthograpy_dir = os.path.join(curr_dir, "orthograpy")
    os.makedirs(orthograpy_dir, exist_ok=True)
    
    amis_corpus = generate_corpus("Amis")
    o_info = extract_orthographic_info(amis_corpus)
    visualize(o_info, os.path.join(orthograpy_dir, "Amis_all"))

if __name__ == "__main__":
    main()
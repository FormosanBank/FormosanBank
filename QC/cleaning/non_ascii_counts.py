import os
import re
import argparse
from lxml import etree
from collections import Counter

# Regular expression to match non-ASCII characters
non_ascii_pattern = re.compile(r'[^\x00-\x7F]')

# Unicode ranges for Chinese characters (CJK Unified Ideographs)
chinese_char_ranges = [
    (0x4E00, 0x9FFF),  # CJK Unified Ideographs
    (0x3400, 0x4DBF),  # CJK Unified Ideographs Extension A
    (0x20000, 0x2A6DF),  # CJK Unified Ideographs Extension B
    (0x2A700, 0x2B73F),  # CJK Unified Ideographs Extension C
    (0x2B740, 0x2B81F),  # CJK Unified Ideographs Extension D
    (0x2B820, 0x2CEAF),  # CJK Unified Ideographs Extension E
    (0x2CEB0, 0x2EBEF),  # CJK Unified Ideographs Extension F
    (0x30000, 0x3134F),  # CJK Unified Ideographs Extension G
]

# Counter to store counts of non-ASCII characters
non_ascii_counts = Counter()

def is_chinese_char(char):
    """
    Check if a character is within the Chinese Unicode ranges.
    """
    char_code = ord(char)
    return any(start <= char_code <= end for start, end in chinese_char_ranges)

def process_xml(file_path):
    """
    Process a single XML file to count non-ASCII characters in FORM elements.
    """
    global non_ascii_counts
    try:
        # Parse the XML file
        tree = etree.parse(file_path)
        # Find all FORM elements
        form_elements = tree.xpath("//FORM")
        for form in form_elements:
            # Extract text from FORM elements
            if form.text:
                # Find all non-ASCII characters
                non_ascii_chars = non_ascii_pattern.findall(form.text)
                # Filter out Chinese characters
                filtered_chars = [char for char in non_ascii_chars if not is_chinese_char(char)]
                # Update the Counter with filtered characters
                non_ascii_counts.update(filtered_chars)
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def main(corpora_path):
    # Walk through the directory to find XML files
    for root, _, files in os.walk(corpora_path):
        for file in files:
            if file.endswith(".xml"):
                file_path = os.path.join(root, file)
                print(f"Processing file: {file_path}")
                process_xml(file_path)

    # Print the counts of non-ASCII characters in descending order
    print("\nNon-ASCII Character Counts (Excluding Chinese, Descending Order):")
    for char, count in non_ascii_counts.most_common():
        print(f"{repr(char)}: {count}")

if __name__ == "__main__":
    # Parse the command-line arguments
    parser = argparse.ArgumentParser(description="Count non-ASCII characters in XML files.")
    parser.add_argument(
        "corpora_path",
        type=str,
        help="Path to the directory containing XML files."
    )
    args = parser.parse_args()

    # Run the main function with the provided path
    main(args.corpora_path)

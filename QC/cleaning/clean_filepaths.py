import os
import re
from lxml import etree
import argparse

def remove_windows_special(text):
    """
    Remove special reserved characters to maintain valid filepaths
    in windows. No doubling up of underscores and none at start or end of filename.
    """

    pattern = r'[<>:"|?*]'
    sanitized = re.sub(pattern, '_', text)
    sanitized = re.sub(r'_+', '_', sanitized)
    sanitized = sanitized.strip('_')
    sanitized = sanitized.strip()
    return sanitized

def sanitize_filename(filepath):
    """
    Sanitize xml file names for windows and unix.
    """
    
    dir_path, filename = os.path.split(filepath)
    base, ext = os.path.splitext(filename)          # split path and filename

    sani_base = remove_windows_special(base)
    sani_filename = f"{sani_base}{ext}"
    sani_filepath = os.path.join(dir_path, sani_filename) if dir_path else sani_filename
    if(sani_filepath!=filepath):
        unique_path = get_non_conflicting_path(sani_filepath)
        os.rename(filepath, unique_path)

def get_non_conflicting_path(path):
    """
    To make sure we dont accidentally have overlapping filenames
    in the event we removed chars that make them identical.
    """

    if not os.path.exists(path):
        return path
    print("Conflicting pathname detected, adding postfix")
    dir_path, filename = os.path.split(path)
    base, ext = os.path.splitext(filename)
    counter = 1

    while counter < 1000:
        new_filename = f"{base} ({counter}){ext}"
        new_path = os.path.join(dir_path, new_filename)
        if not os.path.exists(new_path):
            return new_path
        counter += 1
    raise Exception("Count of identical files exceeds 1000, likely error in corpora.")


def process_directory(xml_dir):
    """
    Processes all XML files in a directory.
    """
    for root, dirs, files in os.walk(xml_dir):
        for file in files:
            if file.endswith(".xml"):
                sanitize_filename(os.path.join(root, file))



def main(args):
    """
    Main function to process XML files in the corpora directory.
    """
    corpora_path = args.corpora_path
    for subdir in os.listdir(corpora_path):
        xml_dir = os.path.join(corpora_path, subdir)
        if os.path.isdir(xml_dir):
            process_directory(xml_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cleaning generated filenames for windows and unix.")
    parser.add_argument('--corpora_path', help='The path to the corpus', required=True)
    args = parser.parse_args()

    if not os.path.exists(args.corpora_path):
        parser.error(f"The entered path, {args.corpora_path}, doesn't exist.")

    main(args)

import os
import re
import sys
from pathlib import Path
from lxml import etree
import argparse

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from QC.corpus_counts import is_reproduction_path

def remove_windows_special(text):
    """
    Remove special reserved characters to maintain valid filepaths
    in windows. No doubling up of underscores and none at start or end of filename.
    NB: We dont look at slashes, as working between systems these may change.
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

    # Before checking path exists,
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


def process_directory(xml_dir, root_path=None):
    """
    Processes all XML files in a directory.

    ``root_path`` is what the caller was originally pointed at. ``main``
    expands a corpora directory into its children, and one child of a
    corpus root is CodeAndDocs -- which this must not enter, because it
    holds build scripts, raw scrapes and POL-035 snapshots, and this
    function *renames files on disk*. Judging the question against the
    expanded child would answer "yes, the caller meant it" for every
    corpus root; judging it against the original argument answers
    correctly, and a build that stages inside CodeAndDocs and points here
    directly still works.
    """
    root_path = xml_dir if root_path is None else root_path
    for root, dirs, files in os.walk(xml_dir):
        for file in files:
            candidate = os.path.join(root, file)
            if is_reproduction_path(candidate, root_path):
                continue
            if file.endswith(".xml") or file.endswith(".csv"):
                sanitize_filename(candidate)



def main(args):
    """
    Main function to process XML files in the corpora directory.
    """
    corpora_path = args.corpora_path
    for subdir in os.listdir(corpora_path):
        xml_dir = os.path.join(corpora_path, subdir)
        if os.path.isdir(xml_dir):
            process_directory(xml_dir, corpora_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cleaning generated filenames for windows and unix.")
    parser.add_argument('--corpora_path', help='The path to the corpus', required=True)
    args = parser.parse_args()

    if not os.path.exists(args.corpora_path):
        parser.error(f"The entered path, {args.corpora_path}, doesn't exist.")

    main(args)

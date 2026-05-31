import csv
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from lxml import etree
import html
import argparse
import unicodedata
from pathlib import Path

XML_LANG_ATTR = "{http://www.w3.org/XML/1998/namespace}lang"

_CHINESE_LANGS = frozenset({
    "zho", "zh", "cmn", "yue", "wuu", "hak", "nan",
})


def _get_xml_lang(element) -> str | None:
    """Return the effective xml:lang for element.

    Walk up from element through its ancestors, returning the first
    xml:lang value found. Falls back to None if no ancestor (including
    element itself) carries xml:lang.

    Used by language-aware cleaning rules to decide whether an element
    carries Chinese text.
    """
    node = element
    while node is not None:
        lang = node.get(XML_LANG_ATTR)
        if lang is not None:
            return lang
        node = node.getparent()
    return None


def _is_chinese(lang: str | None) -> bool:
    """Return True when lang matches a known Chinese variant."""
    if lang is None:
        return False
    return lang.lower() in _CHINESE_LANGS or lang.lower().startswith("zh")


@dataclass
class CleanerWarnings:
    """Accumulates per-occurrence warning rows and writes a CSV at end of run.

    CSV columns: rule_id, file, s_id, character, position.

    write_csv() is a no-op when no rows have been added (avoids creating
    empty files on clean corpora).
    """
    csv_path: Path
    _rows: list = field(default_factory=list, repr=False)

    def add(
        self,
        rule_id: str,
        file_path: str,
        s_id: str | None,
        character: str,
        position: int,
    ) -> None:
        self._rows.append({
            "rule_id": rule_id,
            "file": file_path,
            "s_id": s_id or "",
            "character": character,
            "position": position,
        })

    def write_csv(self) -> None:
        if not self._rows:
            return
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["rule_id", "file", "s_id", "character", "position"],
            )
            if f.tell() == 0:
                writer.writeheader()
            writer.writerows(self._rows)


@dataclass
class TransformCounter:
    """Tallies every (input_char → output_char) substitution.

    record() may be called with count > 1 when the transformation was
    applied to a string containing multiple occurrences.

    summary() returns a list of dicts sorted by count descending,
    suitable for printing as a human-readable table.
    """
    _counts: dict = field(default_factory=lambda: defaultdict(int), repr=False)

    def record(self, input_char: str, output_char: str, count: int = 1) -> None:
        self._counts[(input_char, output_char)] += count

    def record_string_delta(self, before: str, after: str) -> None:
        """Infer individual-character changes by comparing before/after strings.

        Lightweight heuristic: counts characters in before that are absent
        in after as deletions (output=""). Use for full-string deltas where
        a transformation produced a diff but the caller did not record
        each individual swap.
        """
        for ch in set(before):
            if ch not in after:
                self._counts[(ch, "")] += before.count(ch)

    def summary(self) -> list[dict]:
        return sorted(
            [
                {"input": inp, "output": out, "count": cnt}
                for (inp, out), cnt in self._counts.items()
            ],
            key=lambda r: r["count"],
            reverse=True,
        )

    def print_summary(self) -> None:
        rows = self.summary()
        if not rows:
            return
        print("\nTransformation summary (input → output : count):")
        for r in rows:
            out = r["output"] if r["output"] else "<deleted>"
            print(f"  {r['input']!r} → {out!r} : {r['count']}")


'''
def fix_parentheses(text):
    """
    Fixes imbalanced parentheses by removing unmatched ones.
    """
    stack = []
    indices_to_remove = set()
    for i, char in enumerate(text):
        if char == '(':
            stack.append(i)
        elif char == ')':
            if stack:
                stack.pop()
            else:
                indices_to_remove.add(i)
    indices_to_remove.update(stack)
    return ''.join(
        [char for i, char in enumerate(text) if i not in indices_to_remove]
    )
'''

def swap_punctuation(text):
    """
    Replaces specific non-ASCII punctuation with their ASCII equivalents.
    """
    # Define the mapping of full-width punctuation to regular punctuation
    # Also convert square brackets to parentheses    
    fullwidth_to_regular = {
        '（': '(',
        '）': ')',
        '：': ':',
        '，': ',',
        '？': '?',
        '！': '!',
        '。': '.',
        '》': '"',
        '《': '"',
        '」': '"',
        '「': '"',
        '、': ',',
        '】': ')',
        '【': '(',
        ']': ')',
        '[': '(',
        '〔': '(',
        '〕': ')',
        '“': '"',  # Left double quotation mark
        '”': '"',  # Right double quotation mark
        '‘': "'",  # Left single quotation mark
        '’': "'",   # Right single quotation mark
        'ˈ': "'",
        '`': "'",  
        'ʼ': "'",  # Modifier Letter Apostrophe (U+02BC)
        'ʻ': "'",
        '『': '"',
        '』': '"',
        '⌃': '^', # Caret
    }
    
    # Create a regular expression pattern to match any of the full-width punctuation characters
    pattern = re.compile('|'.join(map(re.escape, fullwidth_to_regular.keys())))
    
    # Define a function to replace each match with the corresponding regular punctuation
    def replace(match):
        return fullwidth_to_regular[match.group(0)]
    
    # Use re.sub to replace all full-width punctuation with regular punctuation
    return pattern.sub(replace, text)

def remove_junk_chars(text):
    """
    Replaces specific non-ASCII punctuation with their ASCII equivalents.
    """
    # Define the mapping of full-width punctuation to regular punctuation
    # Also convert square brackets to parentheses    
    to_remove = {
        'ㄇ': ''
    }
    
    # Create a regular expression pattern to match any of the full-width punctuation characters
    pattern = re.compile('|'.join(map(re.escape, to_remove.keys())))
    
    # Define a function to replace each match with the corresponding regular punctuation
    def replace(match):
        return to_remove[match.group(0)]
    
    # Use re.sub to replace all full-width punctuation with regular punctuation
    return pattern.sub(replace, text)


'''
def process_punctuation(text):
    """
    Cleans and standardizes punctuation in the text.
    """
    text = re.sub(r'‘([^’]*)’', r'"\1"', text)  # Paired single quotes
    text = text.replace("‘", "'").replace("’", "'")  # Single quotes
    text = re.sub(r'“([^”]*)”', r'"\1"', text)  # Paired double quotes
    text = text.replace('“', '"').replace('”', '"')  # Double quotes
    text = text.replace("ˈ", "'")  # Specific mark replacements
    return text
'''

def normalize_whitespace(text):
    """
    Standardizes whitespace in the text.
    """
    text = re.sub(r' {2,}', ' ', text)  # Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()  # Normalize whitespace
    return text

def trim_repeated_punctuation(text):
    """
    Replaces repeated punctuation with single marks.
    """
    text = re.sub(r'([?!])\1+', r'\1', text)  # !! -> !
    text = re.sub(r'--+', '-', text)  # --- -> -
    return text

def clean_text(text, lang):
    """
    Applies a sequence of cleaning functions to the text.
    """
    text = swap_punctuation(text)
    text = normalize_whitespace(text)
    text = trim_repeated_punctuation(text)
    text = remove_junk_chars(text)
    return text

def clean_trans(text, lang):
    """
    Applies a sequence of cleaning functions to the text.
    """
    text = normalize_whitespace(text)
    text = trim_repeated_punctuation(text)
    return text

def analyze_and_modify_xml_file(
    xml_dir,
    corpora_dir,
    warnings: CleanerWarnings | None = None,
    counter: TransformCounter | None = None,
    hard_remove_segmentation: bool = False,
    ortho_path: str | None = None,
):
    """
    Analyzes and modifies an XML file by cleaning text and handling specific cases in <FORM>.
    """
    for droot, dirs, files in os.walk(xml_dir):
        for file in files:
            if file.endswith(".xml"):
                print(f"Processing file: {file}")

                xml_file = os.path.join(droot, file)
                # Read the content of the XML file
                with open(xml_file, 'r', encoding='utf-8') as file:
                    content = file.read()

                # Replace all non-breaking spaces with regular spaces
                content = re.sub('\u00A0', ' ', content)

                # Write the modified content back to the XML file
                with open(xml_file, 'w', encoding='utf-8') as file:
                    file.write(content)

                # Silling to re-open the file, but such are the times we live in.
                tree = etree.parse(xml_file)
                root = tree.getroot()
                modified = False

                for sentence in root.findall('.//S'):
                    form_elements = sentence.findall('.//FORM')
                    for form_element in form_elements:
                        if form_element is not None:
                            form_text = form_element.text
                            if form_text is None or form_text == "":
                                continue
                            if form_text != unicodedata.normalize("NFC", form_text):
                                form_element.text = unicodedata.normalize("NFC", form_text)
                                modified = True

                            # Handle specific <FORM> cases
                            if "456otca" in form_text:  # Remove <S> if text contains 456otca
                                root.remove(sentence)
                                modified = True
                            else:
                                if html.unescape(form_text) != form_text:  # Replace HTML entities
                                    print('HTML entities found')
                                    # log the change
                                    with open(os.path.join(corpora_dir,"html_entities.log"), "a") as f:
                                        f.write(f"{xml_file}:\n")
                                        f.write(f"Original: {form_text}\n")
                                        f.write(f"Modified: {html.unescape(form_text)}\n\n")
                                    form_element.text = html.unescape(form_text)
                                    modified = True
                                cleaned_form_text = clean_text(form_text, lang="na")
                                if cleaned_form_text != form_text:
                                    form_element.text = cleaned_form_text
                                    modified = True

                    # Clean <TRANSL> elements
                    for transl in sentence.findall('TRANSL'):
                        lang = transl.get('{http://www.w3.org/XML/1998/namespace}lang')
                        transl_text = transl.text
                        if transl_text:
                            cleaned_transl_text = clean_trans(transl_text, lang)
                            if cleaned_transl_text != transl_text:
                                transl.text = cleaned_transl_text
                                modified = True

                if modified:
                    tree.write(xml_file, xml_declaration=True, pretty_print=True, encoding="utf-8")
                    print(f"File cleaned: {xml_file}")

def main(args):
    print(f"Processing XML files in directory: {args.corpora_path}")
    warnings_path = Path(args.corpora_path) / "cleaner_warnings.csv"
    warnings = CleanerWarnings(warnings_path)
    counter = TransformCounter()
    analyze_and_modify_xml_file(
        args.corpora_path,
        args.corpora_path,
        warnings=warnings,
        counter=counter,
        hard_remove_segmentation=getattr(args, "hard_remove_segmentation", False),
        ortho_path=getattr(args, "ortho_path", None),
    )
    warnings.write_csv()
    counter.print_summary()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Extract orthographic info")
    #parser.add_argument('--verbose', action='store_true', help='increase output verbosity')
    parser.add_argument('--corpora_path', help='the path to the corpus')
    parser.add_argument(
        "--hard-remove-segmentation",
        action="store_true",
        default=False,
        help=(
            "Force stripping of hyphens from S/FORM[@kindOf='standard'] even "
            "when the language's canonical orthography includes '-' as a letter. "
            "Overrides the default preserve-and-warn behavior for Bunun and Thao."
        ),
    )
    parser.add_argument(
        "--ortho-path",
        default=None,
        help=(
            "Path to the canonical orthography directory (default: "
            "Orthographies/Ortho113/ relative to the repo root). "
            "Each <Language>.tsv under this directory is consulted by C012."
        ),
    )
    args = parser.parse_args()

    if not args.corpora_path:
        parser.error("--corpora_path is required.")    
    if not os.path.exists(os.path.join(args.corpora_path)):
        parser.error(f"The entered path, {args.corpora_path}, doesn't exist")

    main(args)

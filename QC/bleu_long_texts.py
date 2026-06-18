"""
Calculate BLEU scores for long-text MT output in long_texts.txt format.

File format (each entry is a paragraph-per-line block):
    Amis: <source>
    Expert Chinese: <reference>
    FormosanBankMT Chinese: <hypothesis>
    NotebookLM Chinese: <hypothesis>
    [Expert English: <reference>]        # present only in some texts
    [FormosanBankMT English: <hypothesis>]
    [NotebookLM English: <hypothesis>]

Usage:
    python QC/bleu_long_texts.py path/to/long_texts.txt
"""

import argparse
import re
import sys
from pathlib import Path

try:
    import sacrebleu
except ImportError:
    sys.exit("sacrebleu is required. Install it with: pip install sacrebleu")

LABELS = [
    "Amis",
    "Expert Chinese",
    "FormosanBankMT Chinese",
    "NotebookLM Chinese",
    "Expert English",
    "FormosanBankMT English",
    "NotebookLM English",
]

# Build a regex that matches any known label at the start of a line
LABEL_RE = re.compile(
    r'^(' + '|'.join(re.escape(l) for l in LABELS) + r'):\s*(.*)',
    re.DOTALL
)


def parse_file(path: str) -> list[dict]:
    """Parse the file into a list of text-block dicts keyed by label."""
    blocks = []
    current = {}

    with open(path, encoding='utf-8') as f:
        for raw_line in f:
            line = raw_line.rstrip('\n')
            m = LABEL_RE.match(line)
            if m:
                label, text = m.group(1), m.group(2).strip()
                if label == 'Amis' and current:
                    blocks.append(current)
                    current = {}
                current[label] = text
            # Lines that don't start with a known label are ignored
            # (blank separators between blocks)

    if current:
        blocks.append(current)

    return blocks


def bleu_report(hypotheses: list[str], references: list[str],
                label: str, tokenize: str) -> None:
    result = sacrebleu.corpus_bleu(hypotheses, [references], tokenize=tokenize)
    print(f"  {label}: BLEU = {result.score:.2f}")
    print(f"    {result}")


def main():
    parser = argparse.ArgumentParser(
        description="Compute BLEU scores for long-text MT output."
    )
    parser.add_argument("txt_path", help="Path to the long_texts.txt file.")
    args = parser.parse_args()

    path = Path(args.txt_path)
    if not path.is_file():
        sys.exit(f"File not found: {path}")

    blocks = parse_file(str(path))
    if not blocks:
        sys.exit("No text blocks found in file.")

    print(f"Found {len(blocks)} text block(s).\n")

    # ── Chinese ──────────────────────────────────────────────────────────────
    zh_blocks = [b for b in blocks
                 if 'Expert Chinese' in b
                 and 'FormosanBankMT Chinese' in b
                 and 'NotebookLM Chinese' in b]

    if zh_blocks:
        print(f"Chinese BLEU  ({len(zh_blocks)} text(s)):")
        ref_zh  = [b['Expert Chinese']         for b in zh_blocks]
        hyp_fbmt_zh = [b['FormosanBankMT Chinese'] for b in zh_blocks]
        hyp_nlm_zh  = [b['NotebookLM Chinese']     for b in zh_blocks]

        bleu_report(hyp_fbmt_zh, ref_zh, "FormosanBankMT", tokenize="zh")
        bleu_report(hyp_nlm_zh,  ref_zh, "NotebookLM",     tokenize="zh")
    else:
        print("No complete Chinese blocks found.")

    print()

    # ── English ───────────────────────────────────────────────────────────────
    en_blocks = [b for b in blocks
                 if 'Expert English' in b
                 and 'FormosanBankMT English' in b
                 and 'NotebookLM English' in b]

    if en_blocks:
        print(f"English BLEU  ({len(en_blocks)} text(s)):")
        ref_en      = [b['Expert English']         for b in en_blocks]
        hyp_fbmt_en = [b['FormosanBankMT English'] for b in en_blocks]
        hyp_nlm_en  = [b['NotebookLM English']     for b in en_blocks]

        bleu_report(hyp_fbmt_en, ref_en, "FormosanBankMT", tokenize="13a")
        bleu_report(hyp_nlm_en,  ref_en, "NotebookLM",     tokenize="13a")
    else:
        print("No complete English blocks found.")


if __name__ == "__main__":
    main()

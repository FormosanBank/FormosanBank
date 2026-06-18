"""
Calculate BLEU scores for two MT models against a reference translation.

Usage:
    python QC/bleu_scores.py path/to/file.csv

The CSV must have at least 5 columns (with or without a header row):
    col 3  – reference translation
    col 4  – model A translation
    col 5  – model B translation

BLEU is computed only on rows where both model A and model B have provided
a non-empty translation.
"""

import argparse
import csv
import sys
from pathlib import Path

try:
    import sacrebleu
except ImportError:
    sys.exit("sacrebleu is required. Install it with: pip install sacrebleu")


def load_rows(csv_path: str):
    """Return (references, model_a, model_b) for rows where both models translated."""
    references, preds_a, preds_b = [], [], []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        first_row = next(reader, None)
        if first_row is None:
            sys.exit("CSV file is empty.")

        # Detect whether the first row is a header by checking if col 3/4/5
        # look like column labels rather than data.
        def _is_header(row):
            # Heuristic: none of the relevant cells end with common sentence
            # punctuation and they contain no Chinese/Formosan characters.
            for col in row[2:5]:
                if any('\u4e00' <= c <= '\u9fff' for c in col):
                    return False
            return True

        rows = [first_row] + list(reader)

    start = 1 if _is_header(rows[0]) else 0

    skipped = 0
    for i, row in enumerate(rows[start:], start=start + 1):
        if len(row) < 5:
            continue
        ref = row[2].strip()
        a   = row[3].strip()
        b   = row[4].strip()
        if not a or not b:
            skipped += 1
            continue
        references.append(ref)
        preds_a.append(a)
        preds_b.append(b)

    return references, preds_a, preds_b, skipped


def main():
    parser = argparse.ArgumentParser(
        description="Compute BLEU scores for two MT models from a CSV file."
    )
    parser.add_argument("csv_path", help="Path to the CSV file.")
    args = parser.parse_args()

    path = Path(args.csv_path)
    if not path.is_file():
        sys.exit(f"File not found: {path}")

    references, preds_a, preds_b, skipped = load_rows(str(path))

    if not references:
        sys.exit("No valid rows found (both models must have translations).")

    print(f"Evaluated on {len(references)} sentences "
          f"({skipped} skipped — at least one model had no translation).\n")

    bleu_a = sacrebleu.corpus_bleu(preds_a, [references], tokenize="zh")
    bleu_b = sacrebleu.corpus_bleu(preds_b, [references], tokenize="zh")

    col_name_a = "Model A (col 4)"
    col_name_b = "Model B (col 5)"

    width = max(len(col_name_a), len(col_name_b))
    print(f"{'Model':<{width}}  BLEU")
    print("-" * (width + 8))
    print(f"{col_name_a:<{width}}  {bleu_a.score:.2f}")
    print(f"{col_name_b:<{width}}  {bleu_b.score:.2f}")
    print()
    print(f"  {col_name_a}: {bleu_a}")
    print(f"  {col_name_b}: {bleu_b}")


if __name__ == "__main__":
    main()

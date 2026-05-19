import argparse
import json
from pathlib import Path

from corpus_metrics import KNOWN_LANGUAGES, analyze_corpora


def get_counts(corpora_path, form_kind="first"):
    metrics = analyze_corpora(Path(corpora_path), form_kind=form_kind)
    tokens_by_lang = {lang: [0, {}] for lang in sorted(KNOWN_LANGUAGES)}

    for row in metrics["by_language_dialect"]:
        lang = row["language"]
        dialect = row["dialect"]
        tokens = row["tokens"]
        if lang not in tokens_by_lang:
            tokens_by_lang[lang] = [0, {}]
        tokens_by_lang[lang][0] += tokens
        tokens_by_lang[lang][1][dialect] = tokens

    tokens_by_source = {
        source: counts["tokens"]
        for source, counts in metrics["by_source"].items()
    }
    return tokens_by_lang, tokens_by_source


def main(corpora_path, form_kind="first"):
    tokens_by_lang, _tokens_by_source = get_counts(corpora_path, form_kind=form_kind)
    print(json.dumps(tokens_by_lang, indent=4, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="count tokens per corpus and per language.")
    parser.add_argument('corpora_path', help='Specify the path of the corpora')
    parser.add_argument(
        "--form-kind",
        choices=["first", "auto", "standard", "original"],
        default="first",
        help="Sentence-level FORM selection mode. 'first' matches the legacy token counter.",
    )
    args = parser.parse_args()
    main(args.corpora_path, form_kind=args.form_kind)

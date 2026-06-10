"""Token counts per language/dialect as JSON, for the token-comparison CI.

Computes from XML via QC/corpus_counts.py (NOT from statistics/*.csv —
this script runs on arbitrary checkouts, e.g. a PR base in a worktree,
where the committed CSVs may be stale or absent).

Output shape (stable interface for tokens_delta.py / plot_counts.py /
plot_deltas.py): {LanguageName: [total_tokens, {dialect: tokens}]}.
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

import corpus_counts


def get_counts(corpora_path):
    records, _parse_errors = corpus_counts.collect_records(Path(corpora_path))

    tokens_by_lang = {name: [0, {}] for name in corpus_counts.LANGUAGE_NAMES}
    tokens_by_source = defaultdict(int)

    corpora_path = Path(corpora_path).resolve()
    for record in records:
        language = corpus_counts.resolve_language(record["language"], record["dialect"])
        if language is None:
            code = record["language"]
            language = f"Unknown ({code})" if code else "Unknown"
        dialect = record["dialect"] or "Not Specified"
        entry = tokens_by_lang.setdefault(language, [0, {}])
        entry[0] += record["word_count"]
        entry[1][dialect] = entry[1].get(dialect, 0) + record["word_count"]

        try:
            source = Path(record["path"]).resolve().relative_to(corpora_path).parts[0]
        except (ValueError, IndexError):
            source = "Unknown"
        tokens_by_source[source] += record["word_count"]

    return tokens_by_lang, dict(tokens_by_source)


def main(corpora_path):
    tokens_by_lang, _tokens_by_source = get_counts(corpora_path)
    print(json.dumps(tokens_by_lang, indent=4, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Count tokens per language and dialect.")
    parser.add_argument("corpora_path", help="Path of the corpora collection root")
    args = parser.parse_args()
    main(args.corpora_path)

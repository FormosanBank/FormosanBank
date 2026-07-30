from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import sys
from pathlib import Path
from typing import Iterable, Literal

import numpy as np
from joblib import dump, load
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

from QC.orthography.function_validation import perturb_text
from QC.orthography.language_clustering import get_document_texts_by_dialect

"""
Evaluate the efficacy of a multiclass SVM on synthetic and real dialect data.

The workflow mirrors the dialect-model evaluation script:
- train or load an SVM classifier for a target language
- generate synthetic text from inventory word n-gram counts
- evaluate on synthetic samples, original orthography samples, and perturbed text
"""

CORPORA_PATH = Path("Corpora")
IN_SCOPE_LANGS = ["ami", "tay", "bnn", "pwn", "pyu", "dru", "trv"]

ISO_TO_LANGUAGE: dict[str, str] = {
    "ami": "Amis",
    "tay": "Atayal",
    "pwn": "Paiwan",
    "bnn": "Bunun",
    "pyu": "Puyuma",
    "dru": "Rukai",
    "tsu": "Tsou",
    "xsy": "Saisiyat",
    "tao": "Yami",
    "ssf": "Thao",
    "ckv": "Kavalan",
    "trv": "Seediq",
    "szy": "Sakizaya",
    "sxr": "Saaroa",
    "xnb": "Kanakanavu",
    "fos": "Siraya",
}
IN_SCOPE_NAMES = {ISO_TO_LANGUAGE[iso] for iso in IN_SCOPE_LANGS}


def train_or_load_svm(
    lang: str,
    artifacts_dir: Path | None = None,
    train_svm: bool = False,
    num_dim: int | None = None,
    kernel: Literal["linear", "poly", "rbf", "sigmoid", "precomputed"] = "rbf",
    kind_of: str = "standard",
):
    """Train or load a multiclass SVM model for dialect classification."""
    artifacts_dir = artifacts_dir or Path(".")
    model_path = artifacts_dir / f"svm_model_{lang}.joblib"
    label_encoder_path = artifacts_dir / f"label_encoder_{lang}.joblib"
    vectorizer_path = artifacts_dir / f"tfidf_vectorizer_{lang}.joblib"
    reducer_path = artifacts_dir / f"svd_reducer_{lang}.joblib"

    if train_svm:
        document_texts, _char_counts, dialects = get_document_texts_by_dialect(target_lang=lang, kind_of=kind_of)
        doc_paths = list(document_texts.keys())
        texts = list(document_texts.values())

        vectorizer = TfidfVectorizer(ngram_range=(1, 2), analyzer="word")
        vectors = vectorizer.fit_transform(texts)

        if num_dim is None or num_dim <= 0:
            vectors_reduced = vectors
            reducer = None
        else:
            max_components = max(1, min(vectors.shape[0] - 1, vectors.shape[1] - 1))
            n_components = min(num_dim, max_components)
            reducer = TruncatedSVD(n_components=n_components, random_state=0)
            vectors_reduced = reducer.fit_transform(vectors)

        y_labels = [dialects[dp] for dp in doc_paths]
        label_encoder = LabelEncoder()
        y = label_encoder.fit_transform(y_labels)

        clf = SVC(kernel=kernel, gamma="scale", decision_function_shape="ovr", random_state=0, probability=True)
        clf.fit(vectors_reduced, y)
        y_pred = clf.predict(vectors_reduced)

        accuracy = float(np.mean(y_pred == y))
        misclassified = np.where(y_pred != y)[0]
        print(
            f"SVM Accuracy on training data: {accuracy:.2%} "
            f"({len(doc_paths) - len(misclassified)}/{len(doc_paths)} correctly classified)"
        )

        dump(clf, model_path)
        dump(label_encoder, label_encoder_path)
        dump(vectorizer, vectorizer_path)
        if reducer is not None:
            dump(reducer, reducer_path)
        elif reducer_path.exists():
            reducer_path.unlink()
    else:
        if not model_path.exists():
            raise FileNotFoundError(
                f"SVM model not found at {model_path}. Train it first with --train_svm."
            )
        clf = load(model_path)
        label_encoder = load(label_encoder_path)

        if not getattr(clf, "probability", False):
            raise ValueError(
                "Loaded SVM was trained without probability=True. "
                "Re-train with --train_svm to use probability-based confidence metrics."
            )

        if not vectorizer_path.exists():
            raise FileNotFoundError(
                f"Missing {vectorizer_path}. Re-train with --train_svm so prediction uses the same feature mapping as training."
            )
        vectorizer = load(vectorizer_path)
        reducer = load(reducer_path) if reducer_path.exists() else None

    return clf, label_encoder, vectorizer, reducer


def _get_inventory_path(lang: str) -> Path:
    language_name = ISO_TO_LANGUAGE.get(lang.lower())
    if language_name is None:
        raise ValueError(f"Unsupported language code: {lang}")
    return Path("QC/utilities/dialect_models") / f"{language_name}.json"


def _load_word_ngrams(lang: str) -> tuple[dict[str, dict[str, int]], dict[str, dict[str, int]]]:
    inventory_path = _get_inventory_path(lang)
    if not inventory_path.exists():
        raise FileNotFoundError(f"Inventory file not found at {inventory_path}")

    with inventory_path.open("r", encoding="utf-8") as handle:
        inventory = json.load(handle)

    return inventory.get("words", {}), inventory.get("word_bi", {})


def _weighted_choice(counts_dict: dict[str, int], rng: random.Random) -> str:
    """Sample one token from a token-to-count mapping with count-proportional weights."""
    if not counts_dict:
        return ""
    population = list(counts_dict.keys())
    weights = list(counts_dict.values())
    return rng.choices(population=population, weights=weights, k=1)[0]


def _generate_synthetic_samples(
    lang: str,
    dialects: Iterable[str],
    num_samples: int,
    text_length: int,
    rng: random.Random,
) -> list[tuple[str, str]]:
    """Generate synthetic text samples from stored dialect inventory n-grams."""
    word_unigrams, word_bigrams = _load_word_ngrams(lang)
    sample_texts: list[tuple[str, str]] = []
    dialect_choices = list(dialects)

    for _ in range(num_samples):
        dialect = rng.choice(dialect_choices)
        tokens: list[str] = []
        unigram_counts = dict(word_unigrams.get(dialect, {}))
        bigram_counts = word_bigrams.get(dialect, {})

        transitions: dict[str, dict[str, int]] = {}
        for bigram, count in bigram_counts.items():
            parts = bigram.split(maxsplit=1)
            if len(parts) != 2:
                continue
            prev_word, next_word = parts
            if prev_word not in transitions:
                transitions[prev_word] = {}
            transitions[prev_word][next_word] = transitions[prev_word].get(next_word, 0) + int(count)

        for position in range(text_length):
            if position == 0:
                word = _weighted_choice(unigram_counts, rng)
            else:
                prev_word = tokens[-1]
                if prev_word in transitions:
                    word = _weighted_choice(transitions[prev_word], rng)
                else:
                    word = _weighted_choice(unigram_counts, rng)
            if not word:
                break
            tokens.append(word)

        sample_texts.append((dialect, " ".join(tokens)))

    return sample_texts


def _iter_labeled_original_documents(corpora_path: Path, lang_code: str, kind_of: str = "original") -> list[tuple[str, str]]:
    document_texts, _char_counts, dialects = get_document_texts_by_dialect(target_lang=lang_code, kind_of=kind_of)
    return [(dialects[doc_path], text) for doc_path, text in document_texts.items() if dialects.get(doc_path)]


def _predict(
    clf: SVC,
    label_encoder: LabelEncoder,
    vectorizer: TfidfVectorizer,
    reducer: TruncatedSVD | None,
    text: str,
) -> tuple[str | None, float]:
    vector = vectorizer.transform([text])
    if reducer is not None:
        vector = reducer.transform(vector)

    probabilities = clf.predict_proba(vector)
    predicted_label = clf.predict(vector)[0]
    predicted_dialect = label_encoder.inverse_transform([predicted_label])[0]
    return predicted_dialect, float(np.max(probabilities[0]))


def _report_metrics(title: str, gold_pred_conf: Iterable[tuple[str, str | None, float]]) -> None:
    rows = list(gold_pred_conf)
    if not rows:
        print(f"\n{title}")
        print("  No samples available.")
        return

    total = len(rows)
    correct_flags = [gold == pred for gold, pred, _ in rows]
    confidence_values = [conf for _gold, _pred, conf in rows]
    correct_conf = [conf for (gold, pred, conf) in rows if gold == pred]
    incorrect_conf = [conf for (gold, pred, conf) in rows if gold != pred]

    accuracy = sum(correct_flags) / total
    avg_conf = sum(confidence_values) / total

    print(f"\n{title}")
    print(f"  Accuracy: {accuracy:.2%} ({sum(correct_flags)}/{total})")
    print(f"  F1 score: {f1_score([gold for gold, _, _ in rows], [pred for _, pred, _ in rows], average='macro'):.2%}")
    print(f"  Average confidence: {avg_conf:.2%}")
    print(f"  Confidence stddev: {statistics.pstdev(confidence_values):.2%}")
    if correct_conf:
        print(f"  Avg confidence on correct predictions: {sum(correct_conf) / len(correct_conf):.2%}")
    if incorrect_conf:
        print(f"  Avg confidence on incorrect predictions: {sum(incorrect_conf) / len(incorrect_conf):.2%}")


def _evaluate_samples(
    clf: SVC,
    label_encoder: LabelEncoder,
    vectorizer: TfidfVectorizer,
    reducer: TruncatedSVD | None,
    samples: Iterable[tuple[str, str]],
) -> list[tuple[str, str | None, float]]:
    rows: list[tuple[str, str | None, float]] = []
    for gold_dialect, text in samples:
        pred_dialect, confidence = _predict(clf, label_encoder, vectorizer, reducer, text)
        rows.append((gold_dialect, pred_dialect, confidence))
    return rows


def _perturb_text_chars(text: str, lang: str, perturbation_level: float, rng: random.Random) -> str:
    return perturb_text(text, lang=lang, perturbation_level=perturbation_level)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate trained SVM dialect classifiers.")
    parser.add_argument("--lang", required=True, help="ISO code, for example: ami, pwn, trv")
    parser.add_argument(
        "--artifacts_dir",
        type=Path,
        default=Path("."),
        help="Directory containing svm_model_<lang>.joblib and related artifacts",
    )
    parser.add_argument(
        "--corpora_path",
        type=Path,
        default=CORPORA_PATH,
        help="Corpora root used to gather original-tier labeled samples",
    )
    parser.add_argument("--train_svm", default=False, help="Train the SVM model before evaluation")
    parser.add_argument("--dim", type=int, default=None, help="Number of SVD dimensions; defaults to no reduction")
    parser.add_argument("--num_samples", type=int, default=300)
    parser.add_argument("--text_length", type=int, default=50)
    parser.add_argument("--perturbation_levels", nargs="+", type=float, default=[0.2, 0.5, 0.8])
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--kind_of", default="standard", choices=["standard", "original"], help="Tier used for training")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    lang = args.lang.lower().strip()
    if lang not in ISO_TO_LANGUAGE:
        raise ValueError(f"Unsupported language code: {lang}")

    artifacts_dir = args.artifacts_dir.resolve()
    rng = random.Random(args.seed)
    np.random.seed(args.seed)

    clf, label_encoder, vectorizer, reducer = train_or_load_svm(
        lang=lang,
        artifacts_dir=artifacts_dir,
        train_svm=args.train_svm,
        num_dim=args.dim,
        kind_of=args.kind_of,
    )

    synthetic_samples = _generate_synthetic_samples(
        lang=lang,
        dialects=label_encoder.classes_,
        num_samples=args.num_samples,
        text_length=args.text_length,
        rng=rng,
    )
    synthetic_results = _evaluate_samples(clf, label_encoder, vectorizer, reducer, synthetic_samples)
    _report_metrics("Synthetic data", synthetic_results)

    original_samples = _iter_labeled_original_documents(args.corpora_path, lang, kind_of="original")
    original_results = _evaluate_samples(clf, label_encoder, vectorizer, reducer, original_samples)
    _report_metrics("Original orthography", original_results)

    for level in args.perturbation_levels:
        perturbed_samples = [(gold, _perturb_text_chars(text, lang, level, rng)) for gold, text in original_samples]
        perturbed_results = _evaluate_samples(clf, label_encoder, vectorizer, reducer, perturbed_samples)
        _report_metrics(f"Character perturbation ({level:.0%})", perturbed_results)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
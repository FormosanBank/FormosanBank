from __future__ import annotations

import argparse
import random
import statistics
import string
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable
from sklearn.metrics import f1_score

# Allow both module execution and direct script execution:
#   python -m QC.utilities.dialect_model_test
#   python QC/utilities/dialect_model_test.py
if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

from QC.utilities.dialect_detector import candidates
from QC.utilities.dialect_detector import model as M
from QC.utilities.dialect_detector.data import xml_lang


def _weighted_choice(token_counts: dict[str, int], rng: random.Random) -> str:
    if not token_counts:
        return ""
    population = list(token_counts.keys())
    weights = list(token_counts.values())
    return rng.choices(population=population, weights=weights, k=1)[0]


def _predict(model: M.DialectModel, text: str) -> tuple[str | None, float]:
    ranked = model.score_text(text)
    if not ranked:
        return None, 0.0
    label, probability, _components = ranked[0]
    return label, float(probability)


def _extract_form_text(root: ET.Element, kind_of: str) -> str:
    parts = [
        form.text.strip()
        for s in root.findall(".//S")
        for form in s.findall(f"./FORM[@kindOf='{kind_of}']")
        if form.text and form.text.strip()
    ]
    return " ".join(parts).strip()


def _iter_labeled_original_documents(corpora_path: Path, lang_code: str) -> list[tuple[str, str]]:
    cands = candidates.candidate_dialects(lang_code)
    rows: list[tuple[str, str]] = []
    for xml_path in sorted(corpora_path.rglob("*.xml")):
        try:
            root = ET.parse(xml_path).getroot()
        except ET.ParseError:
            continue
        if root.tag != "TEXT":
            continue
        if xml_lang(root) != lang_code.lower():
            continue
        raw_dialect = (root.get("dialect") or "").strip()
        if not raw_dialect or raw_dialect.lower() == "unknown":
            continue
        dialect = candidates.reconcile_label(raw_dialect, cands)
        if dialect is None:
            continue
        text = _extract_form_text(root, "original")
        if not text:
            continue
        rows.append((dialect, text))
    return rows


def _generate_synthetic_samples(
    model: M.DialectModel,
    num_samples: int,
    text_length: int,
    rng: random.Random,
) -> list[tuple[str, str]]:
    samples: list[tuple[str, str]] = []

    transition_by_dialect: dict[str, dict[str, dict[str, int]]] = {}
    for dialect in model.dialects:
        transitions: dict[str, dict[str, int]] = {}
        for bigram, count in model.word_bi.get(dialect, {}).items():
            parts = bigram.split(maxsplit=1)
            if len(parts) != 2:
                continue
            prev_word, next_word = parts
            if prev_word not in transitions:
                transitions[prev_word] = {}
            transitions[prev_word][next_word] = transitions[prev_word].get(next_word, 0) + int(count)
        transition_by_dialect[dialect] = transitions

    for _ in range(num_samples):
        dialect = rng.choice(model.dialects)
        unigrams = dict(model.words.get(dialect, {}))
        transitions = transition_by_dialect[dialect]

        tokens: list[str] = []
        for position in range(text_length):
            if position == 0:
                word = _weighted_choice(unigrams, rng)
            else:
                prev_word = tokens[-1]
                if prev_word in transitions:
                    word = _weighted_choice(transitions[prev_word], rng)
                else:
                    word = _weighted_choice(unigrams, rng)
            if not word:
                break
            tokens.append(word)

        samples.append((dialect, " ".join(tokens)))

    return samples



def _swap_words(text: str, num_swaps: int, rng: random.Random) -> str:
    words = text.split()
    if len(words) < 2:
        return text
    for _ in range(num_swaps):
        i, j = rng.sample(range(len(words)), k=2)
        words[i], words[j] = words[j], words[i]
    return " ".join(words)


def _orthography_chars_for_lang(lang_code: str) -> list[str]:
    language_name = M.language_name_for(lang_code)
    if language_name is None:
        return []

    tsv_path = Path("Orthographies") / "Ortho113" / f"{language_name}.tsv"
    if not tsv_path.exists():
        return []

    unique_chars: set[str] = set()
    with tsv_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            for char in line.strip():
                if char and (not char.isspace()) and (char not in string.punctuation):
                    unique_chars.add(char)
    return sorted(unique_chars)


def _perturb_text_chars(
    text: str,
    perturbation_level: float,
    orthography_chars: list[str],
    rng: random.Random,
) -> str:
    if not text or not orthography_chars or perturbation_level <= 0:
        return text

    candidate_indices = [idx for idx, ch in enumerate(text) if not ch.isspace()]
    if not candidate_indices:
        return text

    num_to_perturb = int(len(candidate_indices) * perturbation_level)
    if num_to_perturb <= 0:
        return text

    num_to_perturb = min(num_to_perturb, len(candidate_indices))
    indices_to_perturb = rng.sample(candidate_indices, k=num_to_perturb)

    chars = list(text)
    for idx in indices_to_perturb:
        chars[idx] = rng.choice(orthography_chars)

    return "".join(chars)


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


def _evaluate_samples(model: M.DialectModel, samples: Iterable[tuple[str, str]]) -> list[tuple[str, str | None, float]]:
    rows: list[tuple[str, str | None, float]] = []
    for gold_dialect, text in samples:
        pred_dialect, confidence = _predict(model, text)
        rows.append((gold_dialect, pred_dialect, confidence))
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate trained dialect detector models.")
    parser.add_argument("--lang", required=True, help="ISO code, for example: ami, pwn, trv")
    parser.add_argument(
        "--models_dir",
        type=Path,
        default=Path("QC/utilities/dialect_models"),
        help="Directory containing <Language>.json model files",
    )
    parser.add_argument(
        "--corpora_path",
        type=Path,
        default=Path("Corpora"),
        help="Corpora root used to gather original-tier labeled samples",
    )
    parser.add_argument("--num_samples", type=int, default=300)
    parser.add_argument("--text_length", type=int, default=50)
    # parser.add_argument("--swap_counts", nargs="+", type=int, default=[5, 25, 50, 100])
    parser.add_argument("--perturbation_levels", nargs="+", type=float, default=[0.2, 0.5, 0.8])
    parser.add_argument("--seed", type=int, default=0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    lang = args.lang.lower().strip()
    language_name = M.language_name_for(lang)
    if language_name is None:
        raise ValueError(f"Unsupported language code: {lang}")

    model_path = args.models_dir / f"{language_name}.json"
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model file not found at {model_path}. Train models first with: "
            "python -m QC.utilities.dialect_detector train"
        )

    model = M.load_model(model_path)
    rng = random.Random(args.seed)

    synthetic_samples = _generate_synthetic_samples(
        model=model,
        num_samples=args.num_samples,
        text_length=args.text_length,
        rng=rng,
    )
    synthetic_results = _evaluate_samples(model, synthetic_samples)
    _report_metrics("Synthetic data", synthetic_results)

    original_samples = _iter_labeled_original_documents(args.corpora_path, lang)
    original_results = _evaluate_samples(model, original_samples)
    _report_metrics("Original orthography", original_results)

    # for swaps in args.swap_counts:
    #     swapped_samples = [(gold, _swap_words(text, swaps, rng)) for gold, text in original_samples]
    #     swapped_results = _evaluate_samples(model, swapped_samples)
    #     _report_metrics(f"Random word swaps ({swaps})", swapped_results)

    orthography_chars = _orthography_chars_for_lang(lang)
    if not orthography_chars:
        print("\nCharacter perturbation skipped: no orthography characters found.")
        return 0

    for level in args.perturbation_levels:
        perturbed_samples = [
            (gold, _perturb_text_chars(text, level, orthography_chars, rng))
            for gold, text in original_samples
        ]
        perturbed_results = _evaluate_samples(model, perturbed_samples)
        _report_metrics(f"Character perturbation ({level:.0%})", perturbed_results)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import warnings
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from QC.validation._dialect_inventory import ISO_TO_LANGUAGE
from QC.utilities.dialect_detector import features as F
from QC.utilities.dialect_detector import candidates as C
from QC.utilities.dialect_detector.combiner import fit_combiner, predict_proba
from QC.utilities.dialect_detector.data import extract_standard_text, iter_labeled_documents
from QC.utilities.dialect_detector.graphemes import (
    alphabet_of, load_letter_inventories, tokenize_graphemes,
)

COMPONENTS = ["orthography", "char", "bigram", "word"]
DEFAULT_UNKNOWN_THRESHOLD = 0.50

IN_SCOPE_LANGS = ["ami", "tay", "bnn", "pwn", "pyu", "dru", "trv"]


def language_name_for(lang_code: str) -> str | None:
    if lang_code == "trv":
        return "Seediq"   # the TSV that carries Truku + Seediq dialect columns
    return ISO_TO_LANGUAGE.get(lang_code)


@dataclass
class DialectModel:
    lang_code: str
    language_name: str
    dialects: list[str]                       # fixed order = combiner row order
    inventories: dict[str, frozenset[str]]
    alphabet: frozenset[str]
    support_count: dict[str, int]
    uni: dict[str, Counter]                    # per-dialect profiles
    bi: dict[str, Counter]
    words: dict[str, Counter]
    uni_total: dict[str, int]
    bi_total: dict[str, int]
    word_total: dict[str, int]
    uni_vocab: int
    bi_vocab: int
    word_vocab: int
    weights: list[float]
    bias: list[float]
    threshold: float = DEFAULT_UNKNOWN_THRESHOLD
    components: list[str] = field(default_factory=lambda: list(COMPONENTS))

    def _score_matrix(self, text: str) -> np.ndarray:
        graphemes = tokenize_graphemes(text, self.alphabet)
        uni, bi, words = F.extract_counts(graphemes, text)
        rows = []
        n = len(self.dialects)
        for d in self.dialects:
            o, _, _ = F.orthography_score(uni, self.inventories.get(d, frozenset()),
                                          self.support_count, n)
            c = F.log_prob_score(uni, self.uni[d], self.uni_total[d], self.uni_vocab)
            b = F.log_prob_score(bi, self.bi[d], self.bi_total[d], self.bi_vocab)
            w = F.log_prob_score(words, self.words[d], self.word_total[d], self.word_vocab)
            rows.append([o, c, b, w])
        return np.asarray(rows, dtype=float)

    def score_text(self, text: str) -> list[tuple[str, float, dict[str, float]]]:
        """Return [(dialect, probability, {component: score}), ...] best-first."""
        X = self._score_matrix(text)
        p = predict_proba(np.asarray(self.weights), np.asarray(self.bias), X)
        out = [
            (d, float(p[i]), dict(zip(self.components, X[i].tolist())))
            for i, d in enumerate(self.dialects)
        ]
        out.sort(key=lambda r: (-r[1], r[0]))
        return out


def _prune(counter: Counter, top_n: int) -> Counter:
    return Counter(dict(counter.most_common(top_n)))


def build_model(
    lang_code: str,
    corpora_path: Path,
    orthographies_path: Path,
    top_n: int = 2000,
) -> DialectModel | None:
    name = language_name_for(lang_code)
    if name is None:
        return None
    inventories = load_letter_inventories(name, orthographies_path)
    if not inventories:
        return None
    cands = C.candidate_dialects(lang_code)
    if len(cands) < 2:
        return None
    kept, dropped = iter_labeled_documents(corpora_path, lang_code)
    if dropped:
        warnings.warn(
            f"{lang_code}: {len(dropped)} document(s) skipped with dialect labels "
            f"that map to no candidate: {sorted({d.dialect for d in dropped})}",
            RuntimeWarning,
            stacklevel=2,
        )
    present = [d for d in cands if any(k.dialect == d for k in kept)]
    if len(present) < 2:
        return None

    alphabet = alphabet_of(inventories)
    support_count: dict[str, int] = defaultdict(int)
    for d in present:
        for g in inventories.get(d, frozenset()):
            support_count[g] += 1

    uni = {d: Counter() for d in present}
    bi = {d: Counter() for d in present}
    words = {d: Counter() for d in present}
    for doc in kept:
        if doc.dialect not in uni:
            continue
        g = tokenize_graphemes(doc.text, alphabet)
        u, b, w = F.extract_counts(g, doc.text)
        uni[doc.dialect] += u
        bi[doc.dialect] += b
        words[doc.dialect] += w

    # Vocab sizes are the smoothing denominators, so they must reflect the FULL
    # observed vocabulary, not the per-dialect top_n-pruned profiles (pruning
    # would understate the vocab and inflate unseen-token probabilities). The
    # per-dialect *totals* below ARE post-prune; the denominator is therefore
    # slightly underestimated, but the bias is symmetric across dialects and
    # does not affect relative rankings.
    uni_vocab = len({k for c in uni.values() for k in c}) or 1
    bi_vocab = len({k for c in bi.values() for k in c}) or 1
    word_vocab = len({k for c in words.values() for k in c}) or 1

    uni = {d: _prune(c, top_n) for d, c in uni.items()}
    bi = {d: _prune(c, top_n) for d, c in bi.items()}
    words = {d: _prune(c, top_n) for d, c in words.items()}
    uni_total = {d: sum(c.values()) for d, c in uni.items()}
    bi_total = {d: sum(c.values()) for d, c in bi.items()}
    word_total = {d: sum(c.values()) for d, c in words.items()}

    model = DialectModel(
        lang_code=lang_code, language_name=name, dialects=present,
        inventories={d: inventories.get(d, frozenset()) for d in present},
        alphabet=alphabet, support_count=dict(support_count),
        uni=uni, bi=bi, words=words,
        uni_total=uni_total, bi_total=bi_total, word_total=word_total,
        uni_vocab=uni_vocab, bi_vocab=bi_vocab, word_vocab=word_vocab,
        weights=[0.0] * len(COMPONENTS), bias=[0.0] * len(present),
    )

    Xs, ys = [], []
    index = {d: i for i, d in enumerate(present)}
    for doc in kept:
        if doc.dialect not in index:
            continue
        Xs.append(model._score_matrix(doc.text))
        ys.append(index[doc.dialect])
    w, bias = fit_combiner(Xs, ys, n_dialects=len(present), l2=1.0)
    model.weights = w.tolist()
    model.bias = bias.tolist()
    return model


def save_model(model: DialectModel, path: Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "lang_code": model.lang_code,
        "language_name": model.language_name,
        "dialects": model.dialects,
        "inventories": {d: sorted(s) for d, s in model.inventories.items()},
        "alphabet": sorted(model.alphabet),
        "support_count": model.support_count,
        "uni": {d: dict(c) for d, c in model.uni.items()},
        "bi": {d: dict(c) for d, c in model.bi.items()},
        "words": {d: dict(c) for d, c in model.words.items()},
        "uni_total": model.uni_total, "bi_total": model.bi_total,
        "word_total": model.word_total,
        "uni_vocab": model.uni_vocab, "bi_vocab": model.bi_vocab,
        "word_vocab": model.word_vocab,
        "weights": model.weights, "bias": model.bias,
        "threshold": model.threshold, "components": model.components,
    }
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")


def load_model(path: Path) -> DialectModel:
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    return DialectModel(
        lang_code=d["lang_code"], language_name=d["language_name"],
        dialects=d["dialects"],
        inventories={k: frozenset(v) for k, v in d["inventories"].items()},
        alphabet=frozenset(d["alphabet"]), support_count=d["support_count"],
        uni={k: Counter(v) for k, v in d["uni"].items()},
        bi={k: Counter(v) for k, v in d["bi"].items()},
        words={k: Counter(v) for k, v in d["words"].items()},
        uni_total=d["uni_total"], bi_total=d["bi_total"], word_total=d["word_total"],
        uni_vocab=d["uni_vocab"], bi_vocab=d["bi_vocab"], word_vocab=d["word_vocab"],
        weights=d["weights"], bias=d["bias"],
        threshold=d.get("threshold", DEFAULT_UNKNOWN_THRESHOLD),
        components=d.get("components", list(COMPONENTS)),
    )


def train_all(corpora_path, orthographies_path, models_dir, top_n=2000) -> list[str]:
    trained = []
    for lc in IN_SCOPE_LANGS:
        model = build_model(lc, corpora_path, orthographies_path, top_n=top_n)
        if model is None:
            continue
        save_model(model, Path(models_dir) / f"{model.language_name}.json")
        trained.append(lc)
    return trained


@dataclass(frozen=True)
class Prediction:
    top: str | None
    probability: float
    ranked: list[tuple[str, float, dict[str, float]]]
    is_unknown: bool


def predict_root(model: DialectModel, root) -> Prediction:
    text = extract_standard_text(root)
    if not text:
        return Prediction(None, 0.0, [], True)
    ranked = model.score_text(text)
    top, prob, _ = ranked[0]
    return Prediction(top, prob, ranked, prob < model.threshold)

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


COMPONENTS = ["orthography", "char", "bigram", "word", "word_bigram"] # unigram/bigram for both chars and words
DEFAULT_UNKNOWN_THRESHOLD = 0.50 # default threshold for predicting "unknown" (tuned via cross-validation)

IN_SCOPE_LANGS = ["ami", "tay", "bnn", "pwn", "pyu", "dru", "trv"] # codes for languages


def language_name_for(lang_code: str) -> str | None:
    '''
    Return the language name for a given ISO language code.
    '''
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
    word_bi: dict[str, Counter]
    uni_total: dict[str, int]
    bi_total: dict[str, int]
    word_total: dict[str, int]
    word_bi_total: dict[str, int]
    uni_vocab: int
    bi_vocab: int
    word_vocab: int
    word_bi_vocab: int
    weights: list[float]
    bias: list[float]
    threshold: float = DEFAULT_UNKNOWN_THRESHOLD
    kl_threshold: float = DEFAULT_UNKNOWN_THRESHOLD
    components: list[str] = field(default_factory=lambda: list(COMPONENTS))

    '''
    A DialectModel encapsulates all data and parameters needed to score new texts for dialect prediction. It includes:
    - Metadata: language code, language name, list of dialects, and their orthographic inventories
    - Feature profiles: unigram and bigram counts for characters and words, along with their totals and vocabulary sizes for smoothing
    - Combiner parameters: weights and bias for the logistic regression combiner, as well as thresholds for predicting "unknown" dialects based on softmax probabilities and KL divergence scores
    The model provides methods to extract features from new texts, compute component scores, and make predictions based on both softmax probabilities and KL divergence.
    '''

    def _extract_features(self, text: str):
        """Extract all features once; returns (uni, bi, words, word_bi)."""
        graphemes = tokenize_graphemes(text, self.alphabet)
        return F.extract_counts(graphemes, text)

    def _score_matrix(self, uni, bi, words, word_bi) -> np.ndarray:
        """Compute feature scores for each dialect (pre-extracted features)."""
        rows = []
        n = len(self.dialects)
        for d in self.dialects:
            o, _, _ = F.orthography_score(uni, self.inventories.get(d, frozenset()),
                                          self.support_count, n)
            # Calculate log-probability scores for each component using the model's profiles and totals, with smoothing based on the observed vocabulary size
            c = F.log_prob_score(uni, self.uni[d], self.uni_total[d], self.uni_vocab)
            b = F.log_prob_score(bi, self.bi[d], self.bi_total[d], self.bi_vocab)
            w = F.log_prob_score(words, self.words[d], self.word_total[d], self.word_vocab)
            wb = F.log_prob_score(word_bi, self.word_bi[d], self.word_bi_total[d], self.word_bi_vocab)
            rows.append([o, c, b, w, wb])
        return np.asarray(rows, dtype=float)

    def _kl_matrix(self, uni, bi, words, word_bi) -> np.ndarray:
        """Compute KL divergence scores for each component and dialect (pre-extracted features)."""
        rows = []
        for d in self.dialects:
            # Calculate KL divergence scores for each component using the model's profiles and totals, with smoothing based on the observed vocabulary size
            kl_uni = F.kl_divergence(uni, self.uni[d], self.uni_total[d], self.uni_vocab)
            kl_bi = F.kl_divergence(bi, self.bi[d], self.bi_total[d], self.bi_vocab)
            kl_w = F.kl_divergence(words, self.words[d], self.word_total[d], self.word_vocab)
            kl_wb = F.kl_divergence(word_bi, self.word_bi[d], self.word_bi_total[d], self.word_bi_vocab)
            rows.append([kl_uni, kl_bi, kl_w, kl_wb])
        return np.asarray(rows, dtype=float)

    def score_text(self, text: str) -> list[tuple[str, float, dict[str, float]]]:
        """Return [(dialect, probability, {component: score}), ...] best-first using softmax."""
        uni, bi, words, word_bi = self._extract_features(text)
        X = self._score_matrix(uni, bi, words, word_bi)
        p = predict_proba(np.asarray(self.weights), np.asarray(self.bias), X)
        out = [
            (d, float(p[i]), dict(zip(self.components, X[i].tolist())))
            for i, d in enumerate(self.dialects)
        ]
        out.sort(key=lambda r: (-r[1], r[0]))
        return out

    def score_text_kl(self, text: str) -> tuple[str | None, float, list[tuple[str, float, dict[str, float]]]]:
        """Predict dialect using KL divergence: minimum sum of KL divergences wins.
        
        Returns (predicted_dialect, confidence, ranked_list) where confidence is computed as:
        sqrt(sum_kl_best) / sum_across_dialects(sqrt(sum_kl_d))
        """
        uni, bi, words, word_bi = self._extract_features(text)
        kl = self._kl_matrix(uni, bi, words, word_bi)
        # Sum KL divergences across all components for each dialect
        kl_sums = np.sum(kl, axis=1)  # shape: (n_dialects,)
        
        if np.all(np.isnan(kl_sums)) or np.all(np.isinf(kl_sums)):
            return None, 0.0, []
        
        # Replace inf with a large value for computation
        kl_sums_safe = np.nan_to_num(kl_sums, nan=1e10, posinf=1e10, neginf=-1e10)
        
        # Find dialect with minimum KL divergence
        best_idx = np.argmin(kl_sums_safe)
        best_kl = kl_sums_safe[best_idx]
        
        # Compute confidence using sqrt-based weighting
        kls = (np.abs(kl_sums_safe))
        denominator = np.sum(kls)
        confidence = np.sqrt(float(kls[best_idx] / denominator)) if denominator > 0 else 0.0
        
        # Create ranked list
        ranked = [
            (self.dialects[i], float(kl_sums_safe[i]), 
             {"kl_uni": float(kl[i][0]), "kl_bi": float(kl[i][1]), 
              "kl_word": float(kl[i][2]), "kl_word_bi": float(kl[i][3])})
            for i in range(len(self.dialects))
        ]
        # Sort by KL sum ascending (lower is better)
        ranked.sort(key=lambda r: r[1])
        
        return self.dialects[best_idx], confidence, ranked


def _prune(counter: Counter, top_n: int) -> Counter:
    '''
    Return a new Counter containing only the top_n most common items from the input counter.
    '''
    return Counter(dict(counter.most_common(top_n)))


def build_model(
    lang_code: str,
    corpora_path: Path,
    orthographies_path: Path,
    top_n: int = 2000,
) -> DialectModel | None:
    '''
    Build a DialectModel for a given language code by loading the relevant data and fitting the model parameters. 
    Returns None if the language is out of scope or if there are insufficient dialects with data.
    '''
    name = language_name_for(lang_code)
    if name is None:
        return None
    inventories = load_letter_inventories(name, orthographies_path) # returns dict of dialect -> set of graphemes; may be empty if no inventories or no dialects with inventories
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
    return fit_model_from_docs(lang_code, name, inventories, kept, top_n=top_n)


def fit_model_from_docs(
    lang_code: str,
    name: str,
    inventories: dict[str, frozenset[str]],
    docs: list,
    top_n: int = 2000,
) -> DialectModel | None:
    """Fit a DialectModel from an explicit list of LabeledDoc.

    Shared by build_model (full corpus) and cross_validate (per-fold training
    subset). `present` is the set of dialects actually attested in `docs`;
    returns None if fewer than two dialects have data.
    """
    present = sorted({doc.dialect for doc in docs})
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
    word_bi = {d: Counter() for d in present}
    for doc in docs:
        if doc.dialect not in uni:
            continue
        g = tokenize_graphemes(doc.text, alphabet)
        u, b, w, wb = F.extract_counts(g, doc.text)
        uni[doc.dialect] += u
        bi[doc.dialect] += b
        words[doc.dialect] += w
        word_bi[doc.dialect] += wb

    # Vocab sizes are the smoothing denominators, so they must reflect the FULL
    # observed vocabulary, not the per-dialect top_n-pruned profiles (pruning
    # would understate the vocab and inflate unseen-token probabilities). The
    # per-dialect *totals* below ARE post-prune; the denominator is therefore
    # slightly underestimated, but the bias is symmetric across dialects and
    # does not affect relative rankings.
    uni_vocab = len({k for c in uni.values() for k in c}) or 1
    bi_vocab = len({k for c in bi.values() for k in c}) or 1
    word_vocab = len({k for c in words.values() for k in c}) or 1
    word_bi_vocab = len({k for c in word_bi.values() for k in c}) or 1

    uni = {d: _prune(c, top_n) for d, c in uni.items()}
    bi = {d: _prune(c, top_n) for d, c in bi.items()}
    words = {d: _prune(c, top_n) for d, c in words.items()}
    word_bi = {d: _prune(c, top_n) for d, c in word_bi.items()}
    uni_total = {d: sum(c.values()) for d, c in uni.items()}
    bi_total = {d: sum(c.values()) for d, c in bi.items()}
    word_total = {d: sum(c.values()) for d, c in words.items()}
    word_bi_total = {d: sum(c.values()) for d, c in word_bi.items()}

    model = DialectModel(
        lang_code=lang_code, language_name=name, dialects=present,
        inventories={d: inventories.get(d, frozenset()) for d in present},
        alphabet=alphabet, support_count=dict(support_count),
        uni=uni, bi=bi, words=words, word_bi=word_bi,
        uni_total=uni_total, bi_total=bi_total, word_total=word_total,
        word_bi_total=word_bi_total,
        uni_vocab=uni_vocab, bi_vocab=bi_vocab, word_vocab=word_vocab,
        word_bi_vocab=word_bi_vocab,
        weights=[0.0] * len(COMPONENTS), bias=[0.0] * len(present),
        threshold=DEFAULT_UNKNOWN_THRESHOLD, kl_threshold=DEFAULT_UNKNOWN_THRESHOLD,
    )

    Xs, ys = [], []
    index = {d: i for i, d in enumerate(present)}
    for doc in docs:
        if doc.dialect not in index:
            continue
        uni, bi, words, word_bi = model._extract_features(doc.text)
        Xs.append(model._score_matrix(uni, bi, words, word_bi))
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
        "word_bi": {d: dict(c) for d, c in model.word_bi.items()},
        "uni_total": model.uni_total, "bi_total": model.bi_total,
        "word_total": model.word_total, "word_bi_total": model.word_bi_total,
        "uni_vocab": model.uni_vocab, "bi_vocab": model.bi_vocab,
        "word_vocab": model.word_vocab, "word_bi_vocab": model.word_bi_vocab,
        "weights": model.weights, "bias": model.bias,
        "threshold": model.threshold, "kl_threshold": model.kl_threshold,
        "components": model.components,
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
        word_bi={k: Counter(v) for k, v in d.get("word_bi", {}).items()},
        uni_total=d["uni_total"], bi_total=d["bi_total"], word_total=d["word_total"],
        word_bi_total=d.get("word_bi_total", {}),
        uni_vocab=d["uni_vocab"], bi_vocab=d["bi_vocab"], word_vocab=d["word_vocab"],
        word_bi_vocab=d.get("word_bi_vocab", 1),
        weights=d["weights"], bias=d["bias"],
        threshold=d.get("threshold", DEFAULT_UNKNOWN_THRESHOLD),
        kl_threshold=d.get("kl_threshold", DEFAULT_UNKNOWN_THRESHOLD),
        components=d.get("components", list(COMPONENTS)),
    )


def train_all(corpora_path, orthographies_path, models_dir, top_n=2000,
              calibrate=True, precision_floor=0.95, k=5) -> list[str]:
    """Build and persist one model per in-scope language. When `calibrate`,
    set each model's softmax and KL thresholds from held-out cross-validation.
    """
    from QC.utilities.dialect_detector.evaluate import (
        calibrate_threshold, cross_validate,
    )
    trained = []
    for lc in IN_SCOPE_LANGS:
        model = build_model(lc, corpora_path, orthographies_path, top_n=top_n)
        if model is None:
            continue
        if calibrate:
            cv = cross_validate(lc, corpora_path, orthographies_path, k=k, top_n=top_n)
            if cv and cv["records"]:
                model.threshold = calibrate_threshold(cv["records"], precision_floor)
            if cv and cv.get("records_kl"):
                model.kl_threshold = calibrate_threshold(cv["records_kl"], precision_floor)
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

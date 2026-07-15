from __future__ import annotations

import warnings
from pathlib import Path
from collections import defaultdict
from typing import Any, cast
from QC.utilities.dialect_detector.data import iter_labeled_documents


def evaluate_language(lang_code: str, model, corpora_path: Path) -> dict:
    kept, dropped = iter_labeled_documents(corpora_path, lang_code)
    if dropped:
        warnings.warn(
            f"{lang_code}: {len(dropped)} document(s) skipped with dialect labels "
            f"that map to no candidate: {sorted({d.dialect for d in dropped})}",
            RuntimeWarning,
            stacklevel=2,
        )
    confusion: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    top1 = top2 = n = 0
    ambiguous: list[tuple[float, str, str, str]] = []  # (margin, path, true, pred)
    for doc in kept:
        ranked = model.score_text(doc.text)
        if not ranked:
            continue
        n += 1
        pred = ranked[0][0]
        confusion[doc.dialect][pred] += 1
        top1 += int(pred == doc.dialect)
        top2 += int(doc.dialect in {r[0] for r in ranked[:2]})
        margin = ranked[0][1] - (ranked[1][1] if len(ranked) > 1 else 0.0)
        ambiguous.append((margin, str(doc.path), doc.dialect, pred))
    ambiguous.sort(key=lambda r: r[0])
    return {
        "language": getattr(model, "language_name", lang_code),
        "confusion": {k: dict(v) for k, v in confusion.items()},
        "metrics": metrics_from_confusion({k: dict(v) for k, v in confusion.items()}),
        "top1": top1 / n if n else 0.0,
        "top2": top2 / n if n else 0.0,
        "n": n,
        "most_ambiguous": ambiguous[:20],
    }


def metrics_from_confusion(confusion: dict[str, dict[str, int]]) -> dict[str, float]:
    dialects = sorted(confusion)
    total = sum(sum(r.values()) for r in confusion.values())
    correct = sum(confusion[d].get(d, 0) for d in dialects)
    accuracy = correct / total if total else 0.0
    precisions, recalls, f1s, weighted, support_sum = [], [], [], 0.0, 0
    for d in dialects:
        tp = confusion[d].get(d, 0)
        fp = sum(confusion[o].get(d, 0) for o in dialects if o != d)
        fn = sum(confusion[d].get(o, 0) for o in dialects if o != d)
        support = sum(confusion[d].values())
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        precisions.append(prec); recalls.append(rec); f1s.append(f1)
        weighted += f1 * support; support_sum += support
    k = len(dialects) or 1
    return {
        "accuracy": accuracy,
        "macro_precision": sum(precisions) / k,
        "macro_recall": sum(recalls) / k,
        "macro_f1": sum(f1s) / k,
        "weighted_f1": weighted / support_sum if support_sum else 0.0,
    }


def calibrate_threshold(records, precision_floor: float = 0.95) -> float:
    """Choose the `unknown` threshold from held-out (top_prob, is_correct) records.

    A document is *committed* when its top probability >= threshold. Returns the
    threshold that MAXIMISES coverage subject to accuracy-on-committed >=
    precision_floor (ties broken toward the lower threshold = more coverage). If
    no threshold reaches the floor at any coverage, falls back to the threshold
    that maximises accuracy-on-committed, tie-broken toward a HIGHER threshold
    (fewer, more-confident commits) — i.e. when the precision floor is
    unreachable the detector stays selective rather than emitting low-precision
    guesses.
    """
    if not records:
        return 0.5
    n = len(records)
    thresholds = sorted({p for p, _ in records})
    best_feasible = None   # (coverage, -threshold), threshold
    best_effort = None     # (accuracy, threshold), threshold
    for t in thresholds:
        committed = [c for p, c in records if p >= t]
        if not committed:
            continue
        acc = sum(committed) / len(committed)
        cov = len(committed) / n
        effort_key = (acc, t)
        if best_effort is None or effort_key > best_effort[0]:
            best_effort = (effort_key, t)
        if acc >= precision_floor:
            feas_key = (cov, -t)
            if best_feasible is None or feas_key > best_feasible[0]:
                best_feasible = (feas_key, t)
    if best_feasible is not None:
        return best_feasible[1]
    return best_effort[1] if best_effort is not None else max(thresholds)


def _fold_assignment(kept, present, k):
    """Per-dialect round-robin fold labels (deterministic by path)."""
    from collections import defaultdict as _dd
    by_dialect = _dd(list)
    for doc in kept:
        by_dialect[doc.dialect].append(doc)
    labeled = []  # (doc, fold)
    for d in present:
        for i, doc in enumerate(sorted(by_dialect[d], key=lambda x: str(x.path))):
            labeled.append((doc, i % k))
    return labeled


def cross_validate(lang_code, corpora_path, orthographies_path, k: int = 5,
                   top_n: int = 2000) -> dict | None:
    """Honest held-out evaluation: stratified per-dialect K-fold, refitting the
    profiles AND combiner on each fold's training split (no test leakage).

    Returns {language, n, top1, top1_kl, confusion, confusion_kl, records,
    records_kl, svm_unknown_accuracy, svm_unknown_n}, where `records` and
    `records_kl` are lists of (score, is_correct) for threshold calibration
    (softmax and KL respectively), and `svm_unknown_*` evaluate a second-stage
    multiclass SVM trained on all known-label documents for the language
    (excluding unknown labels), using TF-IDF word unigram/bigram features and
    SVD reduction (target 200 dims), then scored on originally unknown
    held-out predictions (against their true labels). None if the language is
    out of scope or has <2 attested dialects.
    """
    from QC.utilities.dialect_detector.model import (
        fit_model_from_docs, language_name_for,
    )
    from QC.utilities.dialect_detector.graphemes import load_letter_inventories
    from sklearn.decomposition import TruncatedSVD
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.svm import SVC

    name = language_name_for(lang_code)
    if name is None:
        return None
    inventories = load_letter_inventories(name, orthographies_path)
    if not inventories:
        return None
    kept, _dropped = iter_labeled_documents(corpora_path, lang_code)
    present = sorted({d.dialect for d in kept})
    if len(present) < 2:
        return None
    labeled = _fold_assignment(kept, present, k)

    confusion: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    confusion_kl: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    records: list[tuple[float, bool]] = []  # (softmax_prob, is_correct)
    records_kl: list[tuple[float, bool]] = []  # (kl_confidence, is_correct)
    # Second-stage SVM evaluation set from out-of-fold unknown predictions.
    svm_unknown_texts: list[str] = []
    svm_unknown_true: list[str] = []
    # Train SVM on all known-label docs for this language (unknown labels excluded by iterator).
    svm_train_texts = [doc.text for doc in kept]
    svm_train_y = [doc.dialect for doc in kept]
    for f in range(k):
        train = [doc for doc, fold in labeled if fold != f]
        test = [doc for doc, fold in labeled if fold == f]
        if not test:
            continue
        model = fit_model_from_docs(lang_code, name, inventories, train, top_n=top_n)
        if model is None:
            continue
        score_text_kl = getattr(model, "score_text_kl", None)
        for doc in test:
            # Softmax-based prediction
            ranked = model.score_text(doc.text)
            if ranked:
                pred, prob, _ = ranked[0]
                confusion[doc.dialect][pred] += 1
                records.append((prob, pred == doc.dialect))
                if prob < model.threshold:
                    svm_unknown_texts.append(doc.text)
                    svm_unknown_true.append(doc.dialect)
            
            # KL divergence-based prediction
            if callable(score_text_kl):
                pred_kl, conf_kl, ranked_kl = cast(Any, score_text_kl(doc.text))
                if pred_kl is not None:
                    confusion_kl[doc.dialect][pred_kl] += 1
                    records_kl.append((conf_kl, pred_kl == doc.dialect))

    svm_unknown_accuracy = 0.0
    svm_unknown_n = len(svm_unknown_true)
    if svm_train_texts and svm_unknown_texts and len(set(svm_train_y)) >= 2:
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), analyzer="word")
        svm_train_x = vectorizer.fit_transform(svm_train_texts)
        svm_unknown_x = vectorizer.transform(svm_unknown_texts)

        max_components = min(200, svm_train_x.shape[0] - 1, svm_train_x.shape[1] - 1)
        if max_components >= 1:
            svd = TruncatedSVD(n_components=max_components, random_state=0)
            svm_train_x = svd.fit_transform(svm_train_x)
            svm_unknown_x = svd.transform(svm_unknown_x)

        svm = SVC(kernel="rbf", gamma="scale", decision_function_shape="ovr", random_state=0)
        svm.fit(svm_train_x, svm_train_y)
        svm_pred_unknown = svm.predict(svm_unknown_x)
        correct = sum(p == t for p, t in zip(svm_pred_unknown, svm_unknown_true))
        svm_unknown_accuracy = correct / svm_unknown_n if svm_unknown_n else 0.0
    
    n = len(records)
    top1 = sum(1 for _, c in records if c) / n if n else 0.0
    top1_kl = sum(1 for _, c in records_kl if c) / len(records_kl) if records_kl else 0.0
    return {
        "language": name,
        "n": n,
        "top1": top1,
        "top1_kl": top1_kl,
        "confusion": {kk: dict(vv) for kk, vv in confusion.items()},
        "confusion_kl": {kk: dict(vv) for kk, vv in confusion_kl.items()},
        "records": records,
        "records_kl": records_kl,
        "svm_unknown_accuracy": svm_unknown_accuracy,
        "svm_unknown_n": svm_unknown_n,
    }

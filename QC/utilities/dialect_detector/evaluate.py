from __future__ import annotations

import warnings
from pathlib import Path
from collections import defaultdict
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

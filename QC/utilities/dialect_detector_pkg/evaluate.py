from __future__ import annotations


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

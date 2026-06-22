from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from QC.utilities.dialect_detector import model as M
from QC.utilities.dialect_detector.data import xml_lang
from QC.utilities.dialect_detector.model import DialectModel

_REPO = Path(__file__).resolve().parents[3]
DEFAULT_CORPORA = _REPO / "Corpora"
DEFAULT_ORTH = _REPO / "Orthographies" / "Ortho113"
DEFAULT_MODELS = _REPO / "QC" / "utilities" / "dialect_models"


def _discover(path: Path) -> list[Path]:
    path = Path(path)
    if path.is_file():
        return [path] if path.suffix.lower() == ".xml" else []
    return sorted(path.rglob("*.xml"))


def _cmd_train(a) -> int:
    trained = M.train_all(a.corpora_path, a.orthographies, a.models_dir, a.top_n)
    print(f"Trained models for: {', '.join(trained) or '(none)'} -> {a.models_dir}")
    return 0


def _cmd_predict(a) -> int:
    cache: dict[str, DialectModel | None] = {}
    for xml_path in _discover(a.path):
        try:
            root = ET.parse(xml_path).getroot()
        except ET.ParseError:
            continue
        if root.tag != "TEXT":
            continue
        file_lang = xml_lang(root)
        lc = a.lang or file_lang
        # Skip files with mismatched language if --skip_mismatched is set
        if a.skip_mismatched and a.lang and file_lang and file_lang != a.lang:
            continue
        name = M.language_name_for(lc)
        if name is None:
            print(f"{xml_path}: unsupported language {lc or '(missing)'}")
            continue
        if name not in cache:
            mp = Path(a.models_dir) / f"{name}.json"
            cache[name] = None
            if mp.exists():
                try:
                    cache[name] = M.load_model(mp)
                except (json.JSONDecodeError, KeyError, OSError) as exc:
                    print(f"{xml_path}: could not load model {mp}: {exc}")
        model = cache[name]
        if model is None:
            print(f"{xml_path}: no trained model for {name} (run `train`)")
            continue
        text = M.extract_standard_text(root)
        if not text:
            print(f"\nFile: {xml_path}\nLanguage: {lc} -> {name}")
            print("  (no standard tier)")
            continue
        print(f"\nFile: {xml_path}\nLanguage: {lc} -> {name}")
        existing = (root.get("dialect") or "").strip()
        if existing:
            print(f"  existing dialect: {existing}")
        
        # Softmax-based prediction
        pred_softmax = model.score_text(text)
        top_softmax, prob_softmax, _ = pred_softmax[0]
        is_unknown = prob_softmax < model.threshold
        label_softmax = "unknown" if is_unknown else top_softmax
        print(f"\n  [Softmax] guess: {label_softmax}  (top1 p={prob_softmax:.3f})")
        for d, p, comps in pred_softmax:
            comp = "  ".join(f"{k}={comps[k]:+.3f}" for k in model.components)
            print(f"    {d:<14} p={p:.3f}  {comp}")
        
        # KL divergence-based prediction
        top_kl, conf_kl, ranked_kl = model.score_text_kl(text)
        print(f"\n  [KL Divergence] guess: {top_kl}  (confidence={conf_kl:.3f})")
        for d, kl_sum, kl_comps in ranked_kl:
            comp = "  ".join(f"{k}={v:.3f}" for k, v in kl_comps.items())
            print(f"    {d:<14} Σkl={kl_sum:.3f}  {comp}")
    return 0


def _cmd_evaluate(a) -> int:
    from QC.utilities.dialect_detector.evaluate import evaluate_language
    langs = [a.language] if a.language else M.IN_SCOPE_LANGS
    print("(apparent accuracy; train = test — not held-out)")
    for lc in langs:
        model = M.build_model(lc, a.corpora_path, a.orthographies, a.top_n)
        if model is None:
            print(f"  (skipping {lc}: unsupported language or no trainable data)")
            continue
        rep = evaluate_language(lc, model, a.corpora_path)
        print(f"\n{rep['language']} ({lc}): n={rep['n']} "
              f"top1={rep['top1']:.4f} top2={rep['top2']:.4f} "
              f"macro_f1={rep['metrics']['macro_f1']:.4f}")
    return 0


def _cmd_crossvalidate(a) -> int:
    from QC.utilities.dialect_detector.evaluate import calibrate_threshold, cross_validate
    langs = [a.language] if a.language else M.IN_SCOPE_LANGS
    print(f"(honest held-out {a.k}-fold; precision floor {a.precision_floor})\n")
    print(f"{'SOFTMAX-BASED':<60}")
    print(f"{'language':<10}{'n':>5}{'heldout1':>10}{'thr':>7}{'coverage':>10}{'acc|commit':>12}")
    cv_results = []
    for lc in langs:
        cv = cross_validate(lc, a.corpora_path, a.orthographies, k=a.k, top_n=a.top_n)
        if cv is None or not cv["records"]:
            print(f"  (skipping {lc}: unsupported language or no trainable data)")
            continue
        cv_results.append(cv)
        recs = cv["records"]
        t = calibrate_threshold(recs, a.precision_floor)
        committed = [c for p, c in recs if p >= t]
        cov = len(committed) / len(recs)
        accc = sum(committed) / len(committed) if committed else 0.0
        cv["softmax_holdout"] = 1 - cov
        print(f"{cv['language']:<10}{cv['n']:>5}{cv['top1']:>10.3f}"
              f"{t:>7.3f}{cov:>10.3f}{accc:>12.3f}")
    
    print(f"\n{'KL DIVERGENCE-BASED':<60}")
    print(f"{'language':<10}{'n':>5}{'heldout1':>10}{'thr':>7}{'coverage':>10}{'acc|commit':>12}{'unk|holdout':>12}{'unk|coverage':>12}{'unk|acc|commit':>12}")
    for cv in cv_results:
        recs_kl = cv.get("records_kl", [])
        if not recs_kl:
            continue
        t_kl = calibrate_threshold(recs_kl, a.precision_floor)
        committed_kl = [c for p, c in recs_kl if p >= t_kl]
        cov_kl = len(committed_kl) / len(recs_kl)
        accc_kl = sum(committed_kl) / len(committed_kl) if committed_kl else 0.0
        unknown_recs_kl = cv.get("unknown_records_kl", [])
        unknown_holdout_kl = (
            sum(1 for p in unknown_recs_kl if p < t_kl) / len(unknown_recs_kl)
            if unknown_recs_kl else 0.0
        )
        cv["kl_holdout_on_unknowns"] = unknown_holdout_kl
        unknown_committed_kl = [p for p in unknown_recs_kl if p >= t_kl]
        unk_coverage_kl = len(unknown_committed_kl) / len(unknown_recs_kl) if unknown_recs_kl else 0.0
        unk_accc_kl = 0.0  # unknowns should never be correct (they're unknowns)
        print(f"{cv['language']:<10}{len(recs_kl):>5}{cv['top1_kl']:>10.3f}"
              f"{t_kl:>7.3f}{cov_kl:>10.3f}{accc_kl:>12.3f}{unknown_holdout_kl:>12.3f}"
              f"{unk_coverage_kl:>12.3f}{unk_accc_kl:>12.3f}")
    
    print(f"\n{'COMBINED (softmax confident + KL on unknowns)':<60}")
    print(f"{'language':<10}{'n':>5}{'holdout':>10}")
    for cv in cv_results:
        softmax_holdout = cv.get("softmax_holdout", 0.0)
        kl_holdout_on_unknowns = cv.get("kl_holdout_on_unknowns", 0.0)
        combined_holdout = softmax_holdout + (1 - softmax_holdout) * kl_holdout_on_unknowns
        print(f"{cv['language']:<10}{cv['n']:>5}{combined_holdout:>10.3f}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Guess dialect from standard-tier XML.")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("train", "predict", "evaluate", "crossvalidate"):
        sp = sub.add_parser(name)
        sp.add_argument("--corpora_path", type=Path, default=DEFAULT_CORPORA)
        sp.add_argument("--orthographies", type=Path, default=DEFAULT_ORTH)
        sp.add_argument("--models_dir", type=Path, default=DEFAULT_MODELS)
        sp.add_argument("--top_n", type=int, default=2000)
        if name == "predict":
            sp.add_argument("--path", type=Path, required=True)
            sp.add_argument("--lang", type=str, default=None)
        if name in ("evaluate", "crossvalidate"):
            sp.add_argument("--language", type=str, default=None)
        if name == "crossvalidate":
            sp.add_argument("--k", type=int, default=5)
            sp.add_argument("--precision_floor", type=float, default=0.95)
        if name == "predict":
            sp.add_argument("--skip_mismatched", action="store_true",
                           help="Skip files whose xml:lang doesn't match --lang")
    a = p.parse_args(argv)
    return {
        "train": _cmd_train,
        "predict": _cmd_predict,
        "evaluate": _cmd_evaluate,
        "crossvalidate": _cmd_crossvalidate,
    }[a.cmd](a)

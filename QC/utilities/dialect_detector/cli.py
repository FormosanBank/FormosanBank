from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from QC.utilities.dialect_detector import model as M
from QC.utilities.dialect_detector.data import xml_lang

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
    cache: dict[str, object] = {}
    for xml_path in _discover(a.path):
        try:
            root = ET.parse(xml_path).getroot()
        except ET.ParseError:
            continue
        if root.tag != "TEXT":
            continue
        lc = a.lang or xml_lang(root)
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
        pred = M.predict_root(model, root)
        print(f"\nFile: {xml_path}\nLanguage: {lc} -> {name}")
        existing = (root.get("dialect") or "").strip()
        if existing:
            print(f"  existing dialect: {existing}")
        if pred.top is None:
            print("  (no standard tier)")
            continue
        label = "unknown" if pred.is_unknown else pred.top
        print(f"  guess: {label}  (top1 p={pred.probability:.3f})")
        for d, p, comps in pred.ranked:
            comp = "  ".join(f"{k}={comps[k]:+.3f}" for k in model.components)
            print(f"    {d:<14} p={p:.3f}  {comp}")
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


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Guess dialect from standard-tier XML.")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("train", "predict", "evaluate"):
        sp = sub.add_parser(name)
        sp.add_argument("--corpora_path", type=Path, default=DEFAULT_CORPORA)
        sp.add_argument("--orthographies", type=Path, default=DEFAULT_ORTH)
        sp.add_argument("--models_dir", type=Path, default=DEFAULT_MODELS)
        sp.add_argument("--top_n", type=int, default=2000)
        if name == "predict":
            sp.add_argument("--path", type=Path, required=True)
            sp.add_argument("--lang", type=str, default=None)
        if name == "evaluate":
            sp.add_argument("--language", type=str, default=None)
    a = p.parse_args(argv)
    return {"train": _cmd_train, "predict": _cmd_predict, "evaluate": _cmd_evaluate}[a.cmd](a)

#!/usr/bin/env python3
"""Run the pinned shared phonology generator with Lin's Amis source profile."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PROFILES = ROOT / "CodeAndDocs/Orthographies"


def load_shared_module(formosanbank_root: Path):
    module_path = formosanbank_root / "QC/utilities/add_phonology.py"
    if str(formosanbank_root) not in sys.path:
        sys.path.insert(0, str(formosanbank_root))
    module_name = "lin_shared_add_phonology"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--formosanbank-root", type=Path, required=True)
    parser.add_argument("--corpora-path", type=Path, default=ROOT / "XML")
    args = parser.parse_args()

    shared = load_shared_module(args.formosanbank_root.resolve())
    shared_load_profile = shared.load_profile

    def load_profile(scheme: str, language: str, dialect: str, *, target_column=None):
        if scheme != "LinAmis":
            return shared_load_profile(
                scheme,
                language,
                dialect,
                target_column=target_column,
            )
        public_path = shared.ORTHOGRAPHIES_PATH
        try:
            shared.ORTHOGRAPHIES_PATH = SOURCE_PROFILES
            return shared_load_profile(
                scheme,
                language,
                dialect,
                target_column=target_column,
            )
        finally:
            shared.ORTHOGRAPHIES_PATH = public_path

    shared.load_profile = load_profile
    phonology_args = argparse.Namespace(
        orthography="LinAmis",
        target_column=None,
        corpora_path=str(args.corpora_path.resolve()),
        language="Amis",
        preserve_existing_original=False,
    )
    return shared.main(phonology_args)


if __name__ == "__main__":
    raise SystemExit(main())

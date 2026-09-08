#!/usr/bin/env python3
"""Use shared extraction for Babuza-Favorlang, absent from its CLI allowlist."""

from __future__ import annotations

import argparse
import importlib.util
import pickle
from pathlib import Path


LANGUAGES = ("Babuza-Favorlang", "Siraya")


def load_extractor(path: Path):
    spec = importlib.util.spec_from_file_location("orthography_extract", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Cannot load shared extractor: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extractor", type=Path, required=True)
    parser.add_argument("--xml-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    extractor = load_extractor(args.extractor.resolve())
    xml_root = args.xml_root.resolve()
    output_dir = args.output_dir.resolve()

    for language in LANGUAGES:
        corpora = extractor.generate_corpus(
            language,
            str(xml_root),
            "original",
            by_dialect=True,
        )
        populated = {dialect: text for dialect, text in corpora.items() if text}
        if not populated:
            raise SystemExit(f"No original-tier corpus generated for {language}")
        for dialect, text in populated.items():
            profile_dir = output_dir / language / dialect
            profile_dir.mkdir(parents=True, exist_ok=True)
            profile = extractor.extract_orthographic_info(text)
            with (profile_dir / "orthographic_info").open("wb") as handle:
                pickle.dump(profile, handle)
            extractor.visualize(profile, str(profile_dir))
            print(
                "Successfully extracted orthographic information for "
                f"{language}/{dialect}"
            )


if __name__ == "__main__":
    main()

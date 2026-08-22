#!/usr/bin/env python3
"""Run shared PHON generation with the reviewed Asai 2026 source profile."""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCAL_ORTHOGRAPHIES = ROOT / "scripts/orthographies"


def load_shared_module(formosanbank_root: Path):
    module_path = formosanbank_root / "QC/utilities/add_phonology.py"
    if str(formosanbank_root) not in sys.path:
        sys.path.insert(0, str(formosanbank_root))
    spec = importlib.util.spec_from_file_location(
        "kanakanavu_shared_add_phonology", module_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--formosanbank-root", type=Path, required=True)
    parser.add_argument("--corpora-path", type=Path, required=True)
    args = parser.parse_args()

    shared = load_shared_module(args.formosanbank_root.resolve())
    shared_load_profile = shared.load_profile
    shared_form_text = shared._form_text

    def form_text_without_source_analysis_brackets(form):
        # Four grammatical-introduction examples use square brackets as
        # source analysis grouping. PHON is marker-free under POL-003. Strip
        # those input markers before mapping; profile-produced [r|ɾ] groups
        # are created afterward and remain intact.
        return shared_form_text(form).replace("[", "").replace("]", "")

    shared._form_text = form_text_without_source_analysis_brackets

    def load_profile(scheme: str, language: str, dialect: str, *, target_column=None):
        if language == "Kanakanavu" and scheme == "Asai2026":
            public_path = shared.ORTHOGRAPHIES_PATH
            try:
                shared.ORTHOGRAPHIES_PATH = LOCAL_ORTHOGRAPHIES
                return shared_load_profile(
                    scheme, language, dialect, target_column=target_column
                )
            finally:
                shared.ORTHOGRAPHIES_PATH = public_path

        profile = shared_load_profile(
            scheme, language, dialect, target_column=target_column
        )
        if language != "Kanakanavu" or scheme != "Ortho113" or profile is None:
            return profile
        rules = profile.rules + (
            shared.PhonologyRule(
                re.compile("ʦ(?=i)"),
                "tʂ",
                "Madeline Boese review: c is palatalized before i",
            ),
            shared.PhonologyRule(
                re.compile("s(?=i)"),
                "ʂ",
                "Madeline Boese review: s is palatalized before i",
            ),
        )
        return shared.PhonologyProfile(
            mappings=profile.mappings,
            ipa_characters=profile.ipa_characters | frozenset("tʂ"),
            rules=rules,
        )

    shared.load_profile = load_profile
    phonology_args = argparse.Namespace(
        orthography="Asai2026",
        target_column=None,
        corpora_path=str(args.corpora_path.resolve()),
        language="Kanakanavu",
        preserve_existing_original=False,
    )
    return shared.main(phonology_args)


if __name__ == "__main__":
    raise SystemExit(main())

# Normalization Report

- Unicode normalization: NFC.
- Whitespace normalization: repeated spaces collapsed in clean fields only.
- Truku orthography, case, apostrophes, hyphens, equals signs, phonetic symbols, and affix markers were preserved.
- Obvious text-layer artifacts were corrected in clean fields only: trailing footnote numbers, sentence-final doubled periods, and guarded page-initial translation continuations.
- Chinese source translations were preserved; no machine translation was used.
- Raw examples remain in `data/processed/examples_raw.jsonl` with original line breaks.
- Normalization artifact records written: 13.
- Clean records written: 334.

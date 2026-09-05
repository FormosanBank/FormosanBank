# Standard surface review

## Verdict

The source does not support blanket deletion of sentence-level hyphens or parenthetical text. Section 1.6 distinguishes three interlinear levels:

1. The first line is plain Paiwan text, copied with only documented corrections.
2. The second line is the morpheme analysis, where hyphen is a boundary and equals marks insertion.
3. The third line contains morpheme glosses.

Direct S FORM maps to the first line. W and M tiers preserve the second and third-line analysis. A hyphen printed in the first line can therefore be part of the source transcription rather than leaked analysis notation.

Text 001 sentence 009 shows the contrast. Its plain line has `pakazua-u`, while its analysis line has `pa-maka-zua-u`. The corrected direct standard retains `pakazua-u`; the W and M tiers retain the four-unit analysis.

## Exact decisions

`standard_surface_decisions.tsv` binds each reviewed value to an XML file, sentence ID, exact source FORM, former blanket output, corrected standard FORM, decision class, and source evidence.

- 153 sentences retain one or more plain-text source hyphens.
- 150 require only hyphen retention.
- 3 retain a source hyphen while removing separate parenthesized uncertainty.
- 8 additional sentences remove only parenthesized uncertainty.
- 5 parenthetical source tokens are represented as complete included and omitted S variants.
- 166 exact sentence decisions are recorded in total.

The complete variant pairs are `011S75`, `040S42`, `041S10`, `050S55`, and `068S9`, with omitted IDs ending in `-omit`. Both members preserve the source translation and have complete W and M tiers. No alternate FORM remains embedded inside a sentence.

Parenthesized question marks in the other cases are source uncertainty annotations. The standard tier removes only the marker. The original tier preserves the source notation.

## Reproducibility and drift protection

`normalize_sentence_standards.py` loads the exact decision table. It requires the expected file, sentence ID, source FORM, and a recorded pre-correction or corrected standard value. Unexpected source or tier text stops the run. PHON is treated as machine-owned output and must be complete and marker-free.

`make_xml.sh` applies the decisions only after rebuilding from the checksum-pinned Word source and running the pinned FormosanBank cleaner, Ferrell conversion, and phonology tools. It then reruns normalization to prove idempotence and runs the full validator and test suite.

The final validator review confirms that V133 and G010 identify exactly these 153 source-supported sentence hyphens. No hard finding remains. Current authority, source checksums, generated finding CSVs, and the ready-to-port verdict are recorded under `data/` and `reports/`.

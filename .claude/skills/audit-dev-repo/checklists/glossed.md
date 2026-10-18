# Checklist: glossed corpora (W/M tiers, interlinear sources)

1. **Gloss alignment.** A span gloss sliced word by word, whitespace counts that coincide, brackets bleeding into a neighbour, Latin codes on the Chinese tier, glosses one position left.
   How: `audit_gloss_scrape.py` G001/G002 (marker parity, M count), G014 (rare gloss ⊂ dominant), G015 (function-word aberrant rate per sentence), G016 (unbalanced brackets), G018 (Latin on the zho tier); label gloss columns by language, never by position.
   Example: Seediq-Chang — 4 shifted sentences and 32 bracket-bleed glosses; NTU Atayal — glosses one left in 16 of 488 sentences.

2. **Manufactured M tier.** A single M inserted so that every W has one asserts the word is monomorphemic (POL-057, 2026-10-15: "a single M = monomorphemic"); no M = unknown segmentation. No validator checks it.
   How: read the builder for where Ms are created; count single-M words per corpus and put the number to the maintainer.
   Example: roughly 176,000 single copy-Ms across Blust, Yedda, Huteson, Nowbucyang and NTU before the ruling.

3. **Placeholders.** `∅`, `?`, `—` added in processing; POL-060 (a word the source glosses as one unit is one W), POL-061 (an unglossed word is glossed `?`) against the 2026-09-04 HundredPaiwanStories ruling — surface both.
   How: provenance census against the scan (every-corpus item 7).

4. **Infix and clitic notation.** `<X>` infixes must survive into the W tier and reconstruct the root (G004); `=` clitics propagate (V-rules on clitic markers); book hyphens are not rewritten to the bank's convention silently.
   Example: Seediq-Chang — 61 of 83 infixed words rewritten.

5. **Starred parentheses in example sentences** (every-corpus item 5) — run it, do not just know it.

6. **The gloss language.** `TRANSL/@xml:lang` names the language of the gloss text; V143 flags script against language; `(eng)` and `(zho)` columns kept separate, combined glosses never lumped by the audit (maintainer rule: rows = gloss combinations, grouping only where ruled).

7. **Translations vs annotations.** Parenthetical annotator notes in S-level TRANSL are removed by the shared `suppress_transl_annotations.py` (POL-024), never by a corpus-local regex; W/M glosses are never touched.

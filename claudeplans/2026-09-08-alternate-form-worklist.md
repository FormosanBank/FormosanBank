# Alternate-FORM and TRANSL/@kindOf remediation worklist

Opened 2026-09-08 alongside POL-028, POL-053 and rules V149–V151.
Spec: `docs/superpowers/specs/2026-09-08-alternate-form-standardization-design.md`

The rules shipped without remediating the data they flag, deliberately: a
HARD rule firing thousands of times on published XML (Glosbe's 4,157
S-level `TRANSL/@kindOf`) would make `validate_xml.py` exit 1 on every
local run that touches it — including every `run-qc-pipeline` invocation —
and would poison the longitudinal finding baseline, not just block CI (the
PR workflow only blocks HARD fingerprints newly introduced in files a PR
touches, and the full-corpus job is non-blocking). This file is what closes
that gap.

## Item 1 — Latham-1862 cross-lexeme alternates (V150)

6 alternates are competing lexemes for the same gloss, not spelling
variants. Per POL-027 each becomes its own `S` block.

| S id | Gloss | original | alternate | ratio |
| --- | --- | --- | --- | --- |
| `S_favorlang_mouth` | mouth | `ranied` | `sabbacha` | 0.14 |
| `S_sida_foot` | foot | `rahpal` | `tiltil` | 0.17 |
| `S_favorlang_breast` | breast | `arrabis` | `zido` | 0.18 |
| `S_favorlang_neck` | neck | `bokkir` | `arribórribon` | 0.33 |
| `S_favorlang_man` | man | `bahosa` | `sjam` | 0.40 |
| `S_favorlang_hair` | hair | `tâu` | `ratta` | 0.50 |

`totto`/`tutta` (0.60) and `so`/`soa` (0.80) are genuine spelling variants
and stay as alternates.

Doing this means changing `CodeAndDocs/build_lexical_xml.py` so a
comma-separated source cell emits one `S` per option rather than an
alternate tier, then rebuilding via `make_xml.sh`. New S ids are new public
identifiers — POL-037 applies, so pick a scheme and record it in the corpus
README.

## Item 2 — Glosbe S-level TRANSL/@kindOf (V151)

4,157 S-level TRANSLs carry `kindOf="original"`, which means nothing on a
free translation. Confined to `Glosbe_{ami,tay,xsy}_eng_tmem.xml`; they are
legacy, since the current `glosbe_pipeline.py` emits only `xml:lang` and
`ver`. HundredPaiwanStories' 61,493 W/M uses are correct and must not be
touched.

Ordered; step 4 is what closes the item:

1. Add a strip step to `Corpora/Glosbe/CodeAndDocs/make_xml.sh` removing
   `@kindOf` from S-level TRANSLs. Glosbe's scrape is not reproducible and
   `make_xml.sh` operates in place on the published XML, so this is the
   POL-038-compliant way to make the change in code rather than by hand.
2. Run it. Confirm 4,157 attributes gone across the three files, and that
   no W- or M-level TRANSL was touched.
3. Confirm V151 reports zero bank-wide.
4. **Move `v151_S_TRANSL_has_no_kindOf` from `QC/validation/rules/soft.py`
   to `QC/validation/rules/hard.py`**, change `Severity.SOFT` to
   `Severity.HARD`, drop the `count`/`language`/`character` aggregation in
   favour of one Finding per offending element with `location`, update the
   docstring, and regenerate `RULES.md`.

Step 4 lives here rather than in the change that introduced V151 so that
introducing the rule did not make `validate_xml.py` exit 1 on every local
run over Glosbe (or the whole corpus) and did not poison the longitudinal
finding baseline with 4,157 entries that would never clear. (It would not,
on its own, have blocked CI beyond PRs that themselves touch Glosbe's three
`_tmem.xml` files — see V151's docstring in `QC/validation/rules/soft.py`.)

## Confirmed fine — do not re-litigate

V150 flags these and they are correct. Re-checking them each sweep wastes
review time; they are recorded here so a reviewer can skip them.

| Corpus | Node | base / alternate | Why it flags | Why it is fine |
| --- | --- | --- | --- | --- |
| WakelinTexts | `M S13W1M2` | `nem` / `namen` | overlap 0.50 | The `nem ~ namen` pronoun alternation, documented in the corpus README |
| WakelinTexts | `M S17W1M2` | `nem` / `namen` | overlap 0.50 | Same alternation |
| WakelinTexts | `M S7W1M3` | `am` / `namen` | proportion 2 vs 5 | Same alternation, against a shorter original |
| WakelinTexts | `W S20W1` | `pipangn-epen` / `pipangengne-eben` | overlap 0.57 | A three-way source alternation; both forms long and genuinely related |

## Open judgment calls — UtrechtManuscriptWordList

Neither is obviously right or wrong; both need someone who can consult the
manuscript.

| Node | original / alternate | Question |
| --- | --- | --- |
| `S W118` | `tigpapahoang` / `tigp` | 12 vs 4 characters. Almost certainly a truncated transcription of van der Vlis's reading rather than a real variant — check the 1842 edition. |
| `S W375` | `iit` / `jih` | Three letters each, overlap 0.33. Either a genuine witness difference or two different words; the gloss should settle it. |

## Future — gloss standardization

W/M-level `TRANSL/@kindOf` is the axis a gloss-standardization pass will
use: the source's gloss stays as `kindOf="original"` and a standardized
gloss is added as a separate `kindOf="standard"` TRANSL. GitBook already
documents this. HundredPaiwanStories is the existing precedent.

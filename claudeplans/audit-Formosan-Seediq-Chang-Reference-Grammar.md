# Audit — Formosan-Seediq-Chang-Reference-Grammar

Dev repo `Formosan-Seediq-Chang-Reference-Grammar`, audited 2026-10-15 to 2026-10-16 under the
`audit-dev-repo` skill, after the 2026-10 student proofreading review had been applied. Final state:
dev repo `origin/main` **`4080a90`**, built against FormosanBank **`4e60a1e09a84`** (recorded in
`CodeAndDocs/provenance.json`, built 2026-10-16). Every question this audit raised was ruled by the
maintainer; the rulings are quoted in `claudeplans/sweep-qa-decision-log.md`, rounds 60–70.

The maintainer asked for "all the usual stuff, but particular interest in whether optional content
and slashes are being handled appropriately". Those two topics produced most of the findings below.

## Verdict

**Ready to port.** The three orthography calls added on 2026-10-16 (round 8) are ruled: README note in the maintainer's wording, pronouns stay fused, Chang's vowels kept. Dev repo `work/round8` (`3e3f889`, `cea1494`) awaits push. 0 HARD findings across `validate_xml`,
`validate_text` and `validate_glosses`; 63 SOFT (V060 ×29, V061 ×4, V153 ×8, V154 ×22), all adjudicated. (An earlier version said 37: it mixed the adjudication table's per-file row counts with per-finding counts.) The build rebuilds from a clean
checkout with no `Private/` directory and leaves `git status` empty. Every place where the published
text departs from the printed book is listed in the README with its ruling.

Remaining work is port-time only (see "Before and at port").

## What the corpus is

Chang Yung-li 張永利 (2000), *賽德克語參考語法* [Seediq Reference Grammar], Yuan-Liou Publishing.
Seediq (`trv`), dialect Tegudaya. Licence CC BY-NC 4.0, granted by Prof. Chang on 2024-01-07.
Each example in the book prints three lines: the Seediq words with morpheme hyphens, a Chinese gloss
under each word, and a Chinese free translation.

| file | from | S | W | M |
|---|---|---:|---:|---:|
| `XML/Seediq/chang-2000-seediq-reference-grammar.xml` | 273 included example records, chapters 3–4 | 351 | 1,464 | 1,965 |
| `XML/Seediq/chang-2000-seediq-long-texts.xml` | chapter 5 narrative, 40 transcribed blocks | 37 | 269 | 319 |

The 273 records expand to 366 readings (optional material and alternatives give one sentence each);
15 repeat an earlier sentence and are merged (POL-022), leaving 351. Sentence ids are the record ids
(`R275`, `R275-opt`; chapter 5 `C5-002`), ruled 2026-10-16.

## What the build does

| # | Step | What it does to the data | Against FormosanBank |
|---|---|---|---|
| 1–6 | `finalize_source_inventory.py` (Hunter, `6d28fa5`; run once, its Apple Vision OCR input is not in the repo) | 115 scan-review overrides, 12 OCR fixes (q/g, missing spaces), bracket deletion, quote stripping, exclusion of starred/marginal examples (80 of 353 blocks), word–gloss pairing | Initial parsing (POL-046 exception). Tables moved to TSVs (POL-039). Produces the committed `source_inventory.tsv`, which is the build's input |
| — | `transcribe_chapter5.py` | Chapter 5, typed from 300-dpi page images by a Claude session (`cbcffea`), now data in `chapter5_transcription.tsv`; gloss-bracket rule merges continuation blocks | Initial parsing |
| — | `build_xml.py` | Review corrections first; bracket removal; parenthesis width; coindex removal; expansion of `(ka)`, groups, slashes, braces, starred parentheses, word-internal optional morphemes and word variants; per-reading translations; dedup; ids; POL-060 word units; POL-014 infixes; morpheme punctuation; translation spacing; notes | Each corpus-specific step ruled and documented in the README |
| — | shared tools | `apply_manual_edits` (no-op), `clean_xml`, `standardize --remove_accents --hard-remove-segmentation`, `add_phonology` | POL-047 order; deviations stated in the README |

## Findings, and what was done

### Optional content and slashes (the maintainer's focus)

1. **`h-(um)-uwa` (R275) was silently made obligatory.** A hard-coded rewrite in `build_xml.py`,
   added in `6d28fa5` with no reason, published only `h-um-uwa`. Ruled: *"Changes to segmentation
   should also be treated as additional S-blocks, not merely an alt."* R275 now gives four
   sentences (`huwa`/`h-um-uwa` × `kes-un`/`m-esa`). This led to the **POL-028 amendment** (merged),
   refined the same day to: split only when the optional morpheme is glossed and the readings would
   be glossed differently.
2. **`da/di` (R181–R185)** was published as two sentences each. Ruled a spelling variant: one
   sentence each, `di` as `ver="alt"` on S, W and M.
3. **`m-enaq/gaga` (R193).** Not `m-gaga`: 0 attestations in the book or in 2,120 FormosanBank
   Seediq files, and the book says `menaq` "can be replaced by `gaga`". The `gaga` reading now
   carries 在 (as in 6b) instead of the shared printed `AF-在`, with a note.
4. **`laqi/sapah-mu` (R070)**: the `-mu` printed once belongs to both readings (`laqi-mu`,
   `sapah-mu`). The only record with this shape.
5. **Per-reading translations.** R104 now 小孩要喝那杯水 / 小孩要喝這杯水. R103 keeps three
   translations; the third is printed with the same sentence at p. 122.
6. **Step-4 review of every splitting record.** 102 of the 273 records split. 30 non-routine ones
   were carded with the processed text and the published split: 24 confirmed right, R070 and R104
   fixed, R077 and R080 confirmed, R103 confirmed, R127 handled at gloss standardization. The 72
   routine or already-ruled records were listed; the maintainer's ruling is that they **"don't need
   a human checker right now"**, which is not a ruling that they are correct.

### (a) Orthographic letters lost — none

The orthography detector's best match is Seediq (Tegudaya) Ortho113, 23 of 23 letters, none missing.
The one unexpected letter, `z`, is in `pizu`, a Chinese loan per the book's footnote 16. No letter was
lost.

**Correction, 2026-10-16.** An earlier version of this report also said "copying the original into
the standard tier is right". That was wrong to say. The detector compares letter inventories only, and
no decision on the book's orthography was ever made. The book (2000) predates the official writing
system (2005; Ortho113 is its 2024 revision). `validate_vocabulary` (standard tier, exit 0, which I had
not read) gives a word-type overlap of 0.40 with the Tegudaya reference: 196 of 363 types are not in it.
53 types are pronouns the book hyphenates (`sapah-mu`, fused by `standardize` to `sapahmu`; every other
Seediq corpus writes `sapah mu`). 53 more appear in the reference with one or two vowels fewer
(`munekan` vs `mnekan`, again matching every other Seediq corpus), 21 have both differences, and 69 have
no candidate. **Ruled (round 8):** README note in the maintainer's words ("…we treat the original tier as 113 for convenience…The significance of this is not currently clear."); pronouns `fused`; vowels `leave`. Spelling normalization is future work ("not now"); the full list is `claudeplans/2026-10-16-seediq-chang-spelling-differences.tsv`.

**Dialect.** The book says it describes 霧社方言 (printed p. 37, consultants from 互助村) and never says Tegudaya. Ruled: *"For dialect, let's use Tegudaya."* The dialect detector agrees (Tegudaya p = 0.956 grammar, 0.939 chapter 5; it only displays the existing label, never scores with it). `dialects.csv` gains `Paran` and `霧社` as other names, in its own PR first (POL-049).

### (b) Punctuation lost — none

`validate_text`: 0 findings. The book prints a Chinese comma `，` in one Seediq line (p. 155); the
shared cleaner makes it ASCII, as it should. Morpheme FORMs now carry no punctuation (ruled).

### (c) Convention breaks — fixed or by design

- **POL-014:** 61 infixed words now written `b<n>eebu` (gloss `打<完成貌>`). The 18 words the book
  glosses as three pieces (`m-un-ekan` AF-完成貌-吃) follow the book: three morphemes in a row.
- **POL-039:** every data table moved out of the code (translation readings, shared-gloss pairs,
  scan overrides, OCR fixes, non-examples, chapter 5 transcription).
- **SOFT by design:** V060 ×29 (POL-060 word units), V061 ×4, V153 ×8, V154 ×22, all adjudicated. V154's 22 are names glossed as themselves (all 65 Latin-script Mandarin glosses checked 2026-10-16); its disposition still said "partly open" for R312, which the review fixed, and was corrected at port.

### (d) Extraction artifacts — none left

No published sentence starts with `*` or `?`. Starred parentheses go the right way (`*(wada)` kept,
`(*ka)` dropped). Footnote digits are not in any FORM.

### Departures from the printed book

All eight records where an earlier stage changed the book itself were traced to Hunter's overrides
in `6d28fa5` and are ruled; the README's Notes and Issues has the table (2b 吃→喝, 11b `--`, 17a
`musa meepah`, 25b borrowed translation, 28a 去-你→去-我 and 洗→洗（AF）, 29a–c 去-你→去-我), and since this audit
the `gaga` reading of example 5. All 60 edits from the student review were checked against the scan: every one restores
the print except 28a's 洗（AF）. R089's translation (example c's, from the OCR pass) was fixed by
the student to the print.

## Step 4b: build and rights (POLICIES §5–6)

| Rule | Verdict |
|---|---|
| POL-048 rebuilds from a checkout alone | PASS |
| POL-047 one entry point, canonical order | PASS (deviations stated) |
| POL-046 shared tools | PASS |
| POL-052 provenance | PASS (`built` now recorded) |
| POL-042 / 044 licence value and documentation | PASS |
| POL-037 published ids | FIXED (record ids, 2026-10-16) |
| POL-041 / 053 / 055 / 058 / 059 | PASS |
| POL-056 conversion | PASS (round 8: original treated as Ortho113 "for convenience"; no conversion) |
| POL-043 / 045 / 054 | n/a |
| POL-049 / 050 / 051 | at port |

## Changes made in other repositories as a result

- **POL-028 amended** (FormosanBank + GitBook, merged).
- **WakelinTexts** (merged): the article's `( )` ("in data, probable discrepancy") kept in sentence
  FORMs only, not as variants; Kangkang S18 corrected to the print; Kwaway S51 segmented reading only.
- **UtrechtManuscriptWordList** (merged): row 122 one word (a line wrap); row 1060's variant `vuxot`.
- **Blust Thao, Utrecht:** existing variants kept (unglossed words), per ruling.
- **NTU:** instructions for the agent working on NTU, `claudeplans/2026-10-15-ntu-pol028-instructions.md`
  (20 cases to split, 14 issues to check).

## Before and at port

- **Before the port PR:** merge the `dialects.csv` PR (`registry/tegudaya-aliases`), per POL-049.
- At port the build's default path to FormosanBank (`../FormosanBank`, `FORMOSANBANK_PATH`) must
  point at the repository it then lives in.
- `standardize_glosses.py` (PAREN_LABEL → `.LABEL`, e.g. `餵（AF）` → `餵.AF`) exists but is not
  wired, by the 2026-10-14 ruling.
- Port-time checks: POL-049 scope, POL-051 removals (none, as nothing is published), the GitBook
  page with its Notes and Issues section.

## Port (2026-10-16)

Ported as `Corpora/Seediq-Chang-Reference-Grammar` (FormosanBank branch
`port/seediq-chang-reference-grammar`), GitBook page on `corpus/seediq-chang-reference-grammar`.
Dev repo `work/port-prep`: build runs unchanged in both places (`formosanbank_path.sh`),
`scripts/` folded into `CodeAndDocs/`, `reproduce.sh` deleted (POL-047, ruled), V154
disposition corrected, README fixes. Not ported: `Private/`, the OCR text layers, seven
unused files (ruled). 39 ported files byte-identical to dev `82e099f`.

## Review pages

| Page | What it asked | Final count |
|---|---|---|
| [Student proofreading](https://claude.ai/artifact/BgZYpZeavuYmdbGwzsguKT) | words, glosses, translations per record | 312 cards, 305 marked reviewed |
| [Scan check](https://claude.ai/artifact/KBT4fKjH4QX4nTUBJMagA8), [Brackets](https://claude.ai/artifact/FQCkdeCBZaFMBYRDTgXZ5m), [Review diff](https://claude.ai/artifact/Wk3yCPzdFpwRG7sk3TDrwE), [Shared glosses](https://claude.ai/artifact/Hbmu6qpNarAHqNedTHoV66) | applying the review | all ruled |
| [Audit steps 2–3](https://claude.ai/artifact/7K48RnCfbWkLaM3uYpRqfr) | pipeline mapping, validators, Q1–Q8 | all ruled |
| [Decision page](https://claude.ai/artifact/CxSysfW7yq4jPamZBubEt3), rounds 3–7 | Q2–Q8, POL-028 reach, Wakelin, Utrecht, Q1, step 4b, step 4 | 59 cards, all answered |
| Same page, round 8 | README orthography statement, pronoun spacing, vowel spellings in the standard tier | 3 cards, all answered |

## Not verified

- The 72 routine and already-ruled splitting records were not checked by a human (by ruling).
- `finalize_source_inventory.py` cannot be re-run (its OCR input is not in the repo); its tables
  were checked equal to the old literals, not re-executed.

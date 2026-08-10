# HundredPaiwanStories regeneration: full diff vs `main`

Element-by-element comparison of the regenerated corpus
(`feature/hps-regen-phonology`, pipeline = new `clean_xml` → splits (no-ops)
→ new `standardize` → new `add_phonology` → rewritten `fix_ferrell`) against
the published corpus on `main`. Every FORM/PHON/TRANSL of every S/W/M element
was matched by element id and each difference classified by its character-level
edit operations. **After classifier refinement, 0 differences remain
unclassified** — every change is in a named category below.

Comparison scope (elements compared, identical structure both sides — no
S/W/M added or removed anywhere):

| tier | FORM orig | FORM std | PHON orig | PHON std | TRANSL |
|---|---|---|---|---|---|
| S | 2,915 | 2,915 | 2,844 | 2,844 | 2,915 |
| W | 24,478 | 24,478 | 23,373 | 23,373 | 10 |
| M | 36,705 | 36,705 | 36,705 | 36,705 | 36,705 |

Token count (standard-tier, corpus counting rules): **24,478 = 24,478, delta 0.**
`validate_xml`: clean. `*` (unknown-char) count in PHON: 126 = 126.

## Expected differences (all verified, with counts)

### PHON tiers (the bulk — new add_phonology conventions)

| category | S orig | S std | W orig | W std | M orig | M std | why expected |
|---|---|---|---|---|---|---|---|
| punctuation dropped | 2,824 | 2,824 | 5,549 | 5,533 | 97 | 95 | new `phonologize` drops unmapped punctuation — punctuation is not sound |
| segmentation hyphen dropped | 147 | 147 | 161 | 161 | 2,735 | 2,735 | same rationale; M count = the split-morpheme `-em-`/`k-an` PHONs |
| tj double-map fix (`ʦ`→`c`) | — | 1,180 | — | 1,753 | — | 1,902 | old code re-mapped generated IPA (`tj`→`c`, then `c`→`ʦ`); new longest-match tokenizer never re-maps output. `c` is the correct IPA for Ortho113 `tj` |
| spurious `ʔ` removed | 19 | 51 | 6 | 57 | — | 2 | question marks, quote-apostrophes, and `(?)` markers no longer leak into PHON (old fix_ferrell could only repair string-final and `ʔ"` cases) |
| PHON added | 71+71 | | 1,105+1,105 | | — | — | the four `dialect="unknown"` texts (090/091/097/099) now process via the new Ferrell `default` column; S/W PHON existed nowhere before. IPA provisional pending real dialect |

(A single differing PHON can carry several labels, so labels exceed the
per-tier "total differing" counts: S orig 2,825 / S std 2,828 / W orig 5,624 /
W std 6,791 / M orig 2,831 / M std 4,658 differing elements in all.)

### FORM standard tier

| category | S | W | M | why expected |
|---|---|---|---|---|
| C012 hyphen strip | 152 | — | — | standardize now strips segmentation hyphens from S-level standard FORMs of morpheme-segmented sentences (`pakazua-u` → `pakazuau`); digit-flanked survive. W/M keep segmentation by design |
| `'`→`?` reclassification | 24 | 11 | 0 | fix_ferrell's improved classification; fully enumerated below |
| hand edit 008S28 | 1 | 1 | 1 | quotation repair (see below) |

The 24 S / 11 W reclassifications decompose exactly:

- **13 mid-sentence question marks** restored by the TRANSL count-match +
  attestation rules (036S9, 037S14×2, 037S20, 039S3, 040S9, 040S35, 041S16,
  042S8, 042S9, 044S18, 061S9, 061S18) — maintainer-adjudicated; the words
  are attested elsewhere without glottal.
- **1 quote-adjacent case old code missed** (073S44 `"ainu a ku..?"` — old
  regex required a letter before the apostrophe; `..` blocked it).
- **10 S / 11 W source `(?)` uncertainty markers** (089S4, 090S11,
  091S22/23/24/28, 092S8/17/39/45/49) — the source annotates doubtful words
  as `word(?)`; old pipeline had turned these into glottals `(')` with a
  spurious `ʔ` in PHON. Now an explicit rule: `(` `?` `)` is punctuation.
- M tier: zero — no M standard FORM contains `?` anymore (main had the
  tier-blind `'aa?`).

### FORM original tier

Exactly **1 element per tier** differs (008S28): the word glossed 'ah' read
`'aa'` at S but `'aa?` in W/M — the `?` was a stray closing quote. Hand-edited
to `"aa"` (S, W) / `aa` (M) per the no-single-quotes-for-quotation ruling;
recorded in the README. **No other original-tier text changed anywhere** —
clean_xml's original-tier pass was a byte-level no-op on this corpus.

### TRANSL

**1,259 S-level translations** differ, all classified as typography
normalization by clean_xml: curly quotes/apostrophes → straight (`’`→`'`,
`“”`→`"`), and `[lit. …]` → `(lit. …)` in 2 sentences (010S1, 056S46).
No word of any translation changed. W/M glosses: zero differences.

## Issues found during this comparison (fixed before this report)

The comparison surfaced one genuine misclassification, which drove two new
classifier rules (now in `fix_ferrell.py`):

1. **`097S5 mare?a`: word-internal glottal flipped to a question mark** by a
   coincidental FORM/TRANSL count match (the TRANSL's question corresponds to
   an unmarked Paiwan question, and the M carries the citation form `mareka`,
   so the M-guard couldn't see the glottal). Fix: a `?` immediately followed
   by a letter is always the glottal letter (question marks never precede
   letters), overriding the count-match, and such `?` are excluded from the
   count. `?a?a`-style word-initial glottals are covered by the same rule.
2. **Source `(?)` uncertainty markers** were punctuation-classified only when
   a count-match happened to fire. Fix: `(` `?` `)` is now an explicit
   punctuation rule (and excluded from the count-match count), making all 11
   cases principled rather than lucky.

After these fixes the full diff classifies 100%, `fix_ferrell_report.csv` is
empty, and the pipeline is idempotent (rerun changes 0 elements).

## Residual judgment calls (documented, not blocking)

- The four `dialect="unknown"` texts' IPA uses the `default` columns —
  provisional until real dialects are assigned (README step 11 note).
- `validate_glosses` findings are byte-identical to main (pre-existing V062
  HARD ×1368: infix Ms lack angle-bracket glosses — untouched by this regen).

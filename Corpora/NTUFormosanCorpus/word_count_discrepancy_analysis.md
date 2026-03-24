# Word Count Discrepancy Analysis

Analysis of the 9,275 sentences in `validation_results.csv` where the number of space-delimited words in the sentence-level `<FORM>` (`word_count`) does not match the number of `<W>` elements (`w_element_count`).

---

## Overall Shape

| Subcorpus | Count | Missing W (`word_count > w_element_count`) | Extra W (`word_count < w_element_count`) |
|-----------|-------|-------------------------------------------|------------------------------------------|
| Grammar | 2,974 | 2,952 (99.3%) | 22 (0.7%) |
| Sentences | 1,906 | 1,877 (98.5%) | 29 (1.5%) |
| Stories | 4,395 | 4,184 (95.2%) | 211 (4.8%) |

The vast majority (97%) are **missing W elements** — the FORM string has more space-delimited words than there are `<W>` elements. A small minority (3%) go the other way.

### Distribution of differences (word_count − w_element_count)

| Diff | Count |
|------|-------|
| −14 | 1 |
| −5 | 2 |
| −4 | 1 |
| −3 | 5 |
| −2 | 37 |
| −1 | 216 |
| +1 | 6,282 |
| +2 | 1,712 |
| +3 | 619 |
| +4 | 185 |
| +5 | 88 |
| +6–10 | 82 |
| +11–20 | 32 |
| +22–49 | 7 |

The modal case is a discrepancy of exactly +1 (6,282 sentences, 68% of all flags).

---

## By Language

| Language | Discrepant sentences | Missing W | Extra W | Avg abs diff |
|----------|---------------------|-----------|---------|-------------|
| Kanakanavu | 2,502 | 2,487 | 15 | 1.45 |
| Seediq | 1,731 | 1,700 | 31 | 1.65 |
| Bunun | 1,714 | 1,694 | 20 | 1.79 |
| Kavalan | 1,279 | 1,210 | 69 | 1.46 |
| Sakizaya | 1,083 | 1,051 | 32 | 1.61 |
| Rukai | 385 | 351 | 34 | 1.36 |
| Amis | 266 | 260 | 6 | 1.26 |
| Atayal | 185 | 182 | 3 | 1.54 |
| Tsou | 81 | 70 | 11 | 1.17 |
| Saisiyat | 49 | 8 | 41 | 1.04 |

### By Subcorpus × Language

| Subcorpus/Language | Count | Missing W | Extra W | Avg abs diff |
|--------------------|-------|-----------|---------|-------------|
| Grammar/Kanakanavu | 1,274 | 1,267 | 7 | 1.38 |
| Grammar/Sakizaya | 717 | 702 | 15 | 1.76 |
| Grammar/Seediq | 983 | 983 | 0 | 1.61 |
| Sentences/Bunun | 1,178 | 1,178 | 0 | 1.59 |
| Sentences/Kanakanavu | 680 | 680 | 0 | 1.27 |
| Sentences/Rukai | 48 | 19 | 29 | 1.17 |
| Stories/Amis | 266 | 260 | 6 | 1.26 |
| Stories/Atayal | 185 | 182 | 3 | 1.54 |
| Stories/Bunun | 536 | 516 | 20 | 2.24 |
| Stories/Kanakanavu | 548 | 540 | 8 | 1.83 |
| Stories/Kavalan | 1,279 | 1,210 | 69 | 1.46 |
| Stories/Rukai | 337 | 332 | 5 | 1.39 |
| Stories/Saisiyat | 49 | 8 | 41 | 1.04 |
| Stories/Sakizaya | 366 | 349 | 17 | 1.31 |
| Stories/Seediq | 748 | 717 | 31 | 1.70 |
| Stories/Tsou | 81 | 70 | 11 | 1.17 |

Notable: three Grammar subcorpora (Kanakanavu, Sakizaya, Seediq) have **zero extra-W cases** and three Sentences subcorpora (Bunun, Kanakanavu) have **zero extra-W cases** — the extra-W phenomenon is concentrated in Stories and in Sentences/Rukai.

---

## Pattern 1 — Cliticization via `=` (missing W, most common)

**73.5% of all missing-W cases are fully explained** by the `=` clitic notation in `<W>` FORMs. Each single `=` inside a W FORM represents two adjacent FORM words being merged into one `<W>` element.

### Examples

| Sentence FORM | W FORM | FORM words merged |
|---------------|--------|------------------|
| `na madas` | `na=m-adas` | 2 → 1 (diff = 1) |
| `te pa kani` | `te=pa=kani` | 3 → 1 (diff = 2) |
| `Talum cia dau` | `Talum=cia=dau` | 3 → 1 (diff = 2) |
| `pat mata cia` | `pat-mata=cia` | 3 → 1 (diff = 1 via `=`) |

### The counting rule

> **predicted W count = (FORM word count) − (number of single `=` in all W FORMs of the sentence)**

### Critical notation distinction: `=` vs `==`

`==` (double equals) is a **prosodic attachment marker** — it appears trailing on a W form (`a==`, `ka==`) to indicate phonological leaning onto the next word, but the two items remain **separate W elements**. It must **not** be counted as a word merge.

Counting `==` as a merge (treating each `=` sign independently) inflates false residuals substantially. Once `==` is excluded, explanatory power jumps from 58.4% to **73.5%**.

### Per-language explanatory power of merging `=`

| Language | n (missing W) | Fully explained | Partial | None |
|----------|--------------|----------------|---------|------|
| Atayal | 182 | 99% | 1% | <1% |
| Amis | 260 | 98% | <1% | 2% |
| Bunun | 1,694 | 96% | 4% | 0% |
| Kavalan | 1,210 | 96% | 4% | <1% |
| Rukai | 351 | 94% | 1% | 5% |
| Tsou | 70 | 93% | 0% | 7% |
| Kanakanavu | 2,487 | 61% | 1% | **38%** |
| Seediq | 1,700 | 59% | 1% | **40%** |
| Sakizaya | 1,051 | 46% | 2% | **52%** |
| Saisiyat | 8 | 0% | 0% | 100% |

The large "none" fractions for Kanakanavu, Seediq, and Sakizaya are almost entirely explained by Pattern 2 below.

---

## Pattern 2 — Empty W lists in Grammar appendix entries (A2 word-lists)

The Grammar subcorpora for Kanakanavu, Sakizaya, and Seediq contain large **appendix A2 sections** where `<S>` elements hold a single lexical entry in their FORM but have **zero `<W>` elements**. These are vocabulary or paradigm lists entered in sentence-level structures without word-level annotation.

| Subcorpus/Language | Sentences with FORM but 0 W elements |
|--------------------|--------------------------------------|
| Grammar/Kanakanavu | 931 |
| Grammar/Seediq | 675 |
| Grammar/Sakizaya | 537 |
| Stories/Saisiyat | 5 |
| Stories/Rukai | 3 |
| Stories/Seediq | 3 |
| Stories/Atayal | 1 |

Every A2 entry has a diff of exactly 1 (one FORM word, zero W elements). These account for essentially all of the "none" category in Kanakanavu, Sakizaya, and Seediq.

### Examples

```
Kanakanavu Grammar A2_S_1: FORM="aka"    W=[]
Kanakanavu Grammar A2_S_2: FORM="anani"  W=[]
Seediq Grammar A2_S_1:     FORM="ado"    W=[]
Sakizaya Grammar A2_S_1:   FORM="a'am"   W=[]
```

**Recommended fix**: Exclude sentences with 0 `<W>` elements from the word-count validator, or create a separate check for these entries rather than counting them as errors.

---

## Pattern 3 — Saisiyat: systematic insertion of `ay` (extra W)

Saisiyat is the single clearest **extra-W** case: 41 of its 49 discrepancies have *more* W elements than FORM words. The cause is systematic: annotators insert an extra `ay` W element that has no counterpart in the FORM.

### Example

```
FORM:  hiza' boya' ina sahae' ray ra:i'.    (6 words)
W:    [hiza', boya', ay, ina, sahae', ray, ra:i']   (7 elements)
```

The `ay` appears to be a discourse particle/conjunction treated as phonologically suppressed in the FORM but made explicit at the W level. This is a **consistent annotation convention for Saisiyat**.

Most common extra tokens in Saisiyat:

| Token | Count |
|-------|-------|
| `ay` | 24 |
| `ay/` | 5 |
| `XX/` | 3 |
| `i` | 3 |

**Recommended fix**: Whitelist `ay` (and `ay/`) as an insertable particle for Saisiyat when comparing W count to FORM word count.

---

## Pattern 4 — Kavalan: `X` placeholder and function-word insertion (extra W)

Kavalan's 69 extra-W cases break into three types:

### 4a. `X` / `XXXX` placeholder (most common)

`X` is inserted as a W element for inaudible or unclear speech — a segment the annotator knows exists but cannot transcribe. This is legitimate annotation practice.

```
FORM:  nialaanna ta tu mulu.     (4 words)
W:    [X, ni-ala-an-na, ta, tu, mulu]   (5 elements)
```

Most common extra tokens in Kavalan:

| Token | Count |
|-------|-------|
| `X` | 66 |
| `ni` | 5 |
| `ni/` | 3 |
| `ni?/` | 2 |

**Recommended fix**: Exclude `X` and `XXXX` W elements from the W count when comparing against FORM word count.

### 4b. `ni` insertion

A function word (passive/genitive marker) inserted as its own W element without appearing in the FORM:

```
FORM:  yau qudusta masang.    (3 words)
W:    [yau, ni, qudus-ta, masang]   (4 elements)
```

### 4c. L2-embedded words

A handful of cases use `<L2J...L2J>`, `<L2T...L2T>`, `<L2M...L2M>` notation for Japanese and other loanwords, expanding the W count beyond what appears in the FORM.

---

## Pattern 5 — Rukai Sentences: word-splitting and punctuation W elements (extra W)

Rukai Sentences (29 extra-W cases) show a different mechanism: W elements **split** single FORM tokens rather than merging them, and punctuation marks are promoted to standalone W elements.

### 5a. Word splitting

```
FORM:  kaiasane             W: [kay, asane]
FORM:  sanaka               W: [sana, ka]
FORM:  lu dreele-ane        W: [lu, dreele-ane]
```

### 5b. Period `.` as its own W element

```
FORM:  ka Kui wasilasilape ki agiini.
W:    [ka, Kui, w-a-silape-silape, ., ki, agi=ini.]
```

The period is assigned its own `<W>` entry, inflating the element count by 1.

### 5c. Extra function word insertion

```
FORM:  Tarungeangeangea ki pakalreva.    (3 words)
W:    [Tarungeangeangea, ki, pakalreva, kay, *la-situ]   (5 elements)
```

---

## Pattern 6 — Minor patterns

### 6a. Q:/A: dialogue format (Kanakanavu)

Three Kanakanavu sentences use `Q: … A: …` attribution tokens inline in the FORM. These tokens inflate `word_count` by 2 without corresponding W elements.

```
FORM: Q: cau makananu sua nanmarua isi? A: cau mamanʉng.
W:   [cau, makananu, sua, nanmarua, isi, cau, ma-manʉng]
```

**Recommended fix**: Strip `Q:` and `A:` tokens from FORM before computing word count.

### 6b. Mandarin commentary embedded in FORM (Kanakanavu)

A handful of sentences embed Chinese explanatory parentheticals or even a full Chinese gloss in the FORM or W fields — data-entry errors where notes were placed in the wrong field.

```
FORM:  mima sua pa'ici sua cau（. 很少使用兩個sua）
W:    [人們在喝酒。]
```

### 6c. Hyphen as word merger without `=` (Sakizaya)

At least one case where `lingaling sa` in the FORM becomes `lingaling-sa` in the W (merged with `-` rather than `=`). This will not be caught by the `=`-counting strategy.

```
FORM:  lingaling sa ku tangah nu dietu a pakanen.
W:    [lingaling-sa, ku, tangah, nu, dietu, a, pa-kan-en.]
```

### 6d. Slash `/` alternate forms

Some large-diff cases have a `/` separator in the FORM, presenting two alternate forms as a single sentence. The `/` and surrounding words inflate FORM word count while the W only covers one form.

```
FORM:  asi melux / asi lux    (5 words including /)
W:    []   (0 elements)
```

---

## Summary by language

| Language | Missing W fully by `=` | Unaccounted "none" | Primary cause of "none" |
|----------|------------------------|-------------------|------------------------|
| Atayal | 99% | ~1 | minor |
| Amis | 98% | ~4 | minor |
| Bunun | 96% | 0 | all cliticization |
| Kavalan | 96% | ~4 | minor |
| Rukai | 94% | ~17 | word-splitting |
| Tsou | 93% | ~5 | minor |
| Kanakanavu | 61% | 935 | **A2 empty-W word-lists** |
| Seediq | 59% | 679 | **A2 empty-W word-lists** |
| Sakizaya | 46% | 549 | **A2 empty-W word-lists** |
| Saisiyat | 0% | 8 | **extra `ay` (opposite direction)** |

---

## Recommended algorithmic fixes

| Priority | Fix | Sentences affected |
|----------|-----|--------------------|
| 1 (high) | Count single `=` (not `==`) in W FORMs as merged FORM words; subtract from expected W count | ~73.5% of all flags |
| 2 (high) | Exclude sentences with 0 `<W>` elements from word-count validator (or create a separate report for A2 entries) | ~2,143 sentences in Grammar |
| 3 (medium) | Exclude `X` and `XXXX` W elements from W count (Kavalan) | ~66 sentences |
| 4 (medium) | Exclude `ay` / `ay/` from expected W-to-FORM match (Saisiyat) | ~29 sentences |
| 5 (medium) | Strip `Q:` / `A:` attribution tokens from FORM before computing word count (Kanakanavu) | 3 sentences |
| 6 (low/manual) | Flag for manual review: Rukai word-splitting, slash alternates, Mandarin-embedded notes | small number |

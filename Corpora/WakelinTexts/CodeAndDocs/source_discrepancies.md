# WakelinTexts: discrepancies between `pre_correction_snapshot` and the 1958 source

Method: every word token in the snapshot's S-level `original` FORM was checked
for attestation in the PDF text layer of its own text's pages **or** in the
p.22 "Errata Addenda"; per-sentence word counts were compared against the
printed lines; and S/W/M FORM containment was checked internally. 42 tokens and
19 count mismatches were flagged and reviewed by hand against the page images.

Sentence inventory reconciles exactly against the article's own numbering:
Kangkang 43, Kwaway 61, Kalaku1 20, Kalaku2 14, Kalaku3 10, Sunagu (published as `Kalaku4` until 2026-09-07) 23 — no
sentence is missing or extra. Nearly all flagged tokens are OCR noise in the PDF's *text layer*
(`vagay-ta` printed as `vaaay-ta` / `VasaY-ta` / `va,eay-ta`; `m.imama.yua.`
for `mimamayua`; `pasavuf'en` for `pasavuren`) and are **not** discrepancies.

What follows is what survived that filter, updated with the maintainer's
rulings of 2026-09-06 and 2026-09-07. **Three items remain open** — 2, 3 and 4,
all of them an erratum applied to some tiers of a sentence but not others.

---

## A. Errata not applied, or applied to only some tiers

**1. `Kangkang/S30` — `buken` → `puken`.** ✅ FIXED (ruled 2026-09-06).
Errata `A29, 30 for "buken" read "puken"`. Applied at S29 and at A34, missed at
S30. The *other* A30 entry (`si-ina-ku-imu` → `s-ina-ku-imu`) was already applied.

**2. ⏳ `Kangkang/S39` — `ana-na-m` should be `ama-na-m`.** OPEN.
Errata `A39 for "ana-ne-m mengep" read "ama-na-m mang-aep"`. The snapshot applied
`-ne-`→`-na-` and `mengep`→`mang-aep` but kept `ana` where the errata prints
`ama`. The gloss is `father-his`, and `ama` is `father` everywhere else in the
corpus (`s-ama-na` Kwaway/S9, `nu ama-da` Sunagu/S18, S20). Affects the S FORM
and `S39W3`.

**3. ⏳ `Kalaku2/S8` — errata applied at S but not at W.** OPEN.
`D8 for "ap-en-mu-rana" read "aep-en-mu-rana"`. The S FORM has
`aep-en-mu-rana`; `S8W1` still reads `ap-en-mu-rana`, so the word no longer
occurs in its own sentence.

**4. ⏳ `Kwaway/S4` — errata applied at S and W but not at M.** OPEN.
`B4 for "tunanal-a~ep-an" read "tunanal-aep-an"`. `S4W2` is `tunanal-aep-an`
but its `S4W2M2` still reads `agep`, so the morpheme no longer occurs in its
own word.

## B. Internal S/W/M inconsistencies — all ruled

**5. `Kalaku1/S13` — `S13W1` FORM was truncated to `katu`.** ✅ FIXED
(ruled 2026-09-06). Printed p.15: `13 katu-nem/namen-rana nukaden a-m-angay tu
di-taytu`. The W is glossed `unan-we-completely` and holds three morphemes, so
its FORM is now `katu-nem/namen-rana` and the defective W-level alternate
`namen-rana` is gone; the alternation is carried by `S13W1M2` (`nem` ~ `namen`).
Published: S FORM `katu-nem-rana …`, W `katu-nem-rana` + `katu-namen-rana`.

**6. `Kangkang/S18` — the W tier mis-segmented `(u)`.** ✅ FIXED
(ruled 2026-09-07). Printed p.3: `18 mengep su kan (u)kanen-da`. The S FORM now
reads `mengep su kan(u) kanen-da`, and the parenthesis is treated as an
alternation on the word: `S18W3` is `kan` with `alternate` `kan-u`. This is the
one place the article's optional-material parentheses are resolved rather than
left as notation.

**7. `Sunagu/S16` — `S16W4M1` was `cbyaa?`, its W `chyaa?`.** ✅ FIXED
(ruled 2026-09-07). `cbyaa?` is the PDF's OCR of `chyaa?` (`b` for `h`); the
morpheme now matches its word. The word is written as one morpheme but glossed
`it-doesn't-matter`, so under the alignment rule it keeps the word-level gloss
and publishes no morphemes — the intended signal for uncertain parsing.

## C. Spelling changed with no printed or errata authority

**8. `Kwaway/S29` — `mi-tubaus` / `tubaus`.** ✅ FIXED (ruled 2026-09-07).
Printed p.9: `29 mak-apia mi-tabaus k-angay-na`, glossed `unan-hat`; no errata
entry touches it. The snapshot now reads `mi-tabaus` / `tabaus`.

## D. Checked by eye and confirmed — no change

**9. `Kangkang/S19` — `kalagen` is correct** (ruled 2026-09-07). The text layer
prints `kala~en`, and `~` is its generic failure glyph — it stands for `-` in
`chita~en`, `r` in `sip~utan`, `g` in `a~apen`. Read from the page, the letter
is `g`.

**10. `Kangkang/S34` — `puken-ku(a)anak-imu` is correct** (ruled 2026-09-07),
against a text layer that prints `buken-ku(ll}anak-imu`. But **the glosses do
not match the text at all**: the article gives three gloss units
(`see-if-you-will-be-killed(unctn)`, `not-my`, `child-you`) for two printed
words, and the W tier splits them three ways. The corpus therefore publishes
this sentence's words **with no glosses and no morphemes**; only the
sentence-level free translation stands.

## Corrections to the source, made deliberately

**`Kalaku1/S11` — the last two glosses are in the wrong order** (maintainer,
2026-09-07). This is a **correction to the article**, so by definition it does
not match what the page prints; recorded here so no later reader mistakes it
for a transcription slip. The article prints

```
dy-aru•pa-sira            a-ni-padi/machyura•rana
unan-many-still/again•them   unan-past(unctn)-accompany-completely
```

and the glosses belong the other way round. Once swapped, the slash divides the
*word* rather than one morpheme inside it, and it divides the gloss at the same
point, so both halves align:

| published | FORM | gloss | morphemes |
| --- | --- | --- | ---: |
| `S11` | `… dy-aru-pa-sira a-ni-padi` | `unan-many-still` | 3 : 3 |
| `S11b` | `… dy-aru-pa-sira machyura-rana` | `again-them` | 2 : 2 |

with `dy-aru-pa-sira` glossed `unan-past(unctn)-accompany-completely` in both.

One further defect in this sentence is fixed by the alignment rule rather than
by hand: `S11W4` `dewdew-em` (two morphemes) is glossed `foreigners` (one unit),
and its morphemes were `dewdew`/'foreigners' and `em`/'foreigners'. The `-em`
narration suffix carries no gloss in this article, so the M tier is dropped.

**`Kwaway/S9` — `bamboo-strips` → `bamboo.strips`** (maintainer, 2026-09-07).
Neither `varit` nor its alternate `yaked` is segmented in the text, so the gloss
is a single two-word unit; written with a hyphen it reads as two morphemes.
Leipzig dot notation says what is meant.

## E. Gloss fragments left on a morpheme — both fixed

The transcription twice split a parenthesised multi-word gloss across two
morphemes, leaving half of it stranded. Both are corrected in the snapshot.

**11. `Kalaku1/S4W1` — `(next-morning)` split as `(next` + `morning)`.**
Printed p.14 gives one gloss, `unan-(next-morning)`, for a three-morpheme word.
Now written `(next.morning)` and carried whole on `pneřek`, with the `-em`
suffix taking its own gloss (see the README on the narration suffix).

**12. `Kwaway/S43W2` — `(1st-person-imp)` split, leaving `imp)unan` on `a`.**
Printed p.10 reads `43 tausya chi-kong-teb-a` / `don't-want-to
negative-(lst-person-imp)-cut-unan`. The word gloss is right; the morpheme
gloss for `a` had picked up the tail of the previous unit. Corrected to `unan`,
the article's own "unanalyzed" marker, which the build then publishes as no
gloss at all.

Both words now align and keep their morpheme tiers. The build guards against the
class: a morpheme gloss carrying an unmatched parenthesis drops the word's M
tier rather than publishing half a gloss.

## F. Invented `unan` glosses — the transcription padded the morpheme tier

The article's key defines `unan` as "unanalyzed". Where its printed gloss line
has **fewer units than the word's segmentation**, the hand transcription filled
the gap by writing `unan` on the leftover morphemes. **31 words** carry such a
padded `unan`, and in **28** of them the padded morpheme is the `-em`/`-m`
narration suffix, which the article's own NOTE says is left untranslated
throughout — so there the annotation is defensible, and the build overwrites it
with `PAR` anyway.

**Three are not the suffix, and all three are corrected here.**

**13. `Kangkang/S39W5` and `S40W5` — `mu` glossed `unan`.** ✅ FIXED
(ruled 2026-09-07). Printed p.5: `39 … ta-ka-mu …` / `… we-incl(E.A) …`. The
article gives **two** gloss units for a three-morpheme word and says nothing
about the third; the `unan` on `mu` is the transcription's own padding and
appears nowhere in the source. The gloss is deleted; `mu` now carries none.

**14. `Sunagu/S2W8` — `imurud)` glossed `unan`, and the word gloss truncated.**
✅ FIXED. Printed p.19: `2 ma-chita-da tu madegdeg (imurud nu tau)/(tau
d-imurud)` / `unan-see-them in early-morning (Imurud CM persons)/(persons from
Imurud)`. The article glosses this word **`from Imurud`**, not `from`. So the
word gloss becomes `from-Imurud)` and the morpheme `imurud)` takes `Imurud)`
instead of the invented `unan`. The word now aligns and keeps its morphemes.

⏳ **The 28 suffix cases are left as they are**, pending a decision. They are the
same mechanism — padding where the source's gloss line was short — but the
article documents that the suffix is untranslated, so `unan` there records a
real fact rather than inventing one, and nothing reaches the published data
because the narration rule replaces it with `PAR`.

## Not a discrepancy, recorded so it is not re-raised

- `Kwaway/S51` — printed p.10 reads `51 mikabak-abay-u/mikabakabayu u mwakay`.
  The `alternate` FORM that duplicates the standard spelling is **correct**: the
  source really does offer a hyphenated and an unhyphenated reading. This is the
  cleanest example in the corpus of a pure spelling variant. The snapshot had
  resolved this one slash out of its sentence FORM ahead of time; it has been
  put back, so every alternation in the snapshot is now unexpanded and the same
  code handles all of them.

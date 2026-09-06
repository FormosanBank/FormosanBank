# WakelinTexts: discrepancies between `pre_correction_snapshot` and the 1958 source

Method: every word token in the snapshot's S-level `original` FORM was checked
for attestation in the PDF text layer of its own text's pages **or** in the
p.22 "Errata Addenda"; per-sentence word counts were compared against the
printed lines; and S/W/M FORM containment was checked internally. 42 tokens and
19 count mismatches were flagged and reviewed by hand against the page images.

Sentence inventory reconciles exactly: Kangkang 43, Kwaway 61 (+`S48b`),
Kalaku1 20, Kalaku2 14, Kalaku3 10, Kalaku4 23 — no sentence is missing or
extra. Nearly all flagged tokens are OCR noise in the PDF's *text layer*
(`vagay-ta` printed as `vaaay-ta` / `VasaY-ta` / `va,eay-ta`; `m.imama.yua.`
for `mimamayua`; `pasavuf'en` for `pasavuren`) and are **not** discrepancies.

What follows is what survived that filter. Nothing here is fixed except item 1,
which was ruled on 2026-09-06.

---

## A. Errata not applied, or applied to only some tiers

**1. `Kangkang/S30` — `buken` → `puken`.** ✅ FIXED this branch (ruled).
Errata `A29, 30 for "buken" read "puken"`. Applied at S29 and at A34, missed at
S30. Printed p.4: `30 kuan-a nu anak-ne-m buken a si-ina-ku-imu kuan-a`.
Note the *other* A30 entry (`si-ina-ku-imu` → `s-ina-ku-imu`) **was** applied.

**2. `Kangkang/S39` — `ana-na-m` should be `ama-na-m`.**
Errata `A39 for "ana-ne-m mengep" read "ama-na-m mang-aep"`. The snapshot
applied `-ne-`→`-na-` and `mengep`→`mang-aep` but kept `ana`, where the errata
prints `ama`. The gloss is `father-his`, and `ama` is `father` everywhere else
in the corpus (`s-ama-na` Kwaway/S9, `nu ama-da` Kalaku4/S18, S20).
Affects the S FORM and `S39W3`.

**3. `Kalaku2/S8` — errata applied at S but not at W.**
`D8 for "ap-en-mu-rana" read "aep-en-mu-rana"`. S FORM has `aep-en-mu-rana`;
`S8W1` still reads `ap-en-mu-rana`. The W no longer occurs in its own sentence.

**4. `Kwaway/S4` — errata applied at S and W but not at M.**
`B4 for "tunanal-a~ep-an" read "tunanal-aep-an"`. `S4W2` is `tunanal-aep-an`
but its `S4W2M2` still reads `agep`. The M no longer occurs in its own W.

## B. Internal S/W/M inconsistencies

**5. `Kalaku1/S13` — `S13W1` FORM is truncated to `katu`.**
Printed p.15: `13 katu-nem/namen-rana nukaden a-m-angay tu di-taytu`. The W is
glossed `unan-we-completely` and holds three morphemes (`katu`/unan,
`nem`/we, `rana`/completely), so its FORM should be `katu-nem-rana`, with the
alternate reading `katu-namen-rana`. As it stands the W FORM contradicts both
its own gloss and its own morphemes, and the W-level `alternate` is recorded as
the bare `namen-rana`.

**6. `Kangkang/S18` — the W tier mis-segments `(u)`.**
Printed p.3: `18 mengep su kan (u)kanen-da` (four words, four gloss units:
`take CN much(unctn) food-their`). The S FORM matches. The W tier instead reads
`kan(u)` + `kanen-da`, moving the parenthesised `u` from the head of word 4 to
the tail of word 3.

**7. `Kalaku4/S16` — `S16W4M1` is `cbyaa?`, its W is `chyaa?`.**
`cbyaa?` is the PDF's OCR of `chyaa?` (`b` for `h`). The W was corrected and the
M was not; they should agree.

## C. Spelling changed with no printed or errata authority

**8. `Kwaway/S29` — `mi-tubaus` / `tubaus`.**
Printed p.9: `29 mak-apia mi-tabaus k-angay-na`, glossed `unan-hat`. No errata
entry touches D/B29. The snapshot reads `tubaus`; the source prints `tabaus`.

## D. Low confidence — flagged, not asserted

**9. `Kangkang/S19` — `kalagen`.** Printed `kala~en`, glossed `to-hunt-for`.
`~` is the text layer's generic failure glyph and is not consistently one
letter: it stands for `-` in `chita~en` (errata: read `chita-en`), for `r` in
`sip~utan` (snapshot `siprutan`), and for `g` in `a~apen` (snapshot `agapen`).
So `kalagen` may be right, but the text layer cannot confirm it; the page image
should be read at higher resolution.

**10. `Kangkang/S34` — `(a)` in `puken-ku(a)anak-imu`.** Printed as
`buken-ku(ll}anak-imu` — heavy OCR damage. The gloss is `not-my child-you`, so
`ku` is `my` and the parenthetical is a linker. `(a)` is plausible but
unverified; also note the snapshot emits **three** W for what the source prints
as two words.

---

## Not a discrepancy, recorded so it is not re-raised

- `Kwaway/S51` — printed p.10 reads `51 mikabak-abay-u/mikabakabayu u mwakay`.
  The `alternate` FORM that duplicates the standard spelling is **correct**: the
  source really does offer a hyphenated and an unhyphenated reading. This is the
  cleanest example in the corpus of a pure spelling variant.
- The snapshot is **not uniform** about slash notation: `S51` resolved the slash
  out of its S FORM and kept the alternation at W level, while the other 17
  slash expressions keep the slash in the S FORM. Any expansion code has to cope
  with both shapes.

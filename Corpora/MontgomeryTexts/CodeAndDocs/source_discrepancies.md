# Source discrepancies — MontgomeryTexts

Differences between the published XML and what
[`Original.pdf`](Original.pdf) prints, and what was done about each.
The snapshot in `pre_correction_snapshot/XML/` is the source of record
(POL-035); a correction is made *there*, not in `XML/`, which is rebuilt.

The article's four content pages (pp. 17–20 of the volume, PDF pages 2–5) are
image-only scans with no text layer. Every reading below was taken from a
600–1200 dpi render of the page, not from extracted text.

## 1. `mi-salrama` — RESOLVED 2026-09-07

| | |
|---|---|
| Location | `XML/Amis/Silo.xml`, `S5` (article: *Silo*, example 4), sentence-level FORM |
| Source | PDF p. 4 (volume p. 19): `itini i roma? ?i maorah a mi-salrama ato wawa` |
| Was | `mi-salama` on the S-level FORM; `mi-salrama` on `S5W8` |
| Now | `mi-salrama` at both levels |

The corpus README had recorded this as a correction — *"We corrected
'mi-salrama' to 'mi-salama'"* — but the article prints `mi-salrama`, and the
word-level FORM had always kept it. The edit had reached only the sentence
tier, so the file disagreed with itself.

POL-001 governs: the `original` tier is what the source prints, and its
spelling is preserved. `lr` is not an OCR artefact — the page is a clean
typescript and the sequence is legible at 600 dpi. Restored.

The `standard` tier follows automatically: `mi-salrama` → `misadlama` under
`l`→`d`, `r`→`l` (it read `misadama` before), and so does the PHON.

## 1b. `Orthographies/Montgomery/Amis.tsv`, row `l` — FIXED 2026-09-07

Not a source discrepancy but a profile one, recorded here because it changes
published data. The row read `l` → IPA `d`: the *letter* `l` maps to in
Ortho113, put in the column that wants that letter's *sound*. Ortho113's `d`
is /ɬ~ɮ/, so the same word came out /dafak/ from the original tier and
/ɬafak/ from the standard, in 50 of 394 elements.

Akiw's own example settles it: `tamlaw` → `tamdaw` "people", pronounced
/tamɬaw/. Montgomery's `l` writes /ɬ~ɮ/. The row now reads `[ɬ|ɮ]`; the two
PHON tiers agree everywhere, and `validate_conversion_table.py` resolves all
five rows. The profile's `d` → `[ɬ|ɮ]` row is untouched and inert: the
original tier contains no `d` at all.

## 2. The diacritic on `f` — OPEN, not changed

| | |
|---|---|
| Location | `XML/Amis/Day_I_Now.xml`, `S15` and `S15W6` (article: example 14) |
| Source | PDF p. 4 (volume p. 19): `ma-sasi?a` + `f` + diacritic + `a?ařaw` |
| Published | `f` + U+0306 COMBINING BREVE |
| History | U+0302 CIRCUMFLEX until `132bb7839` (June 2026) changed it to U+0306 |

The only occurrence of the letter in the corpus, and the only thing Akiw's
notes leave explicitly unresolved: *"The status of f̂ (which is rare) is
uncertain."*

At 1200 dpi the diacritic reads as a **caron** — the same mark the typescript
puts on every `ř` in the same line (`?ařaw`) and on the same page (`tahiřa`,
`hřek`, `řakot`, `iřa`), and visibly different from a breve. The letter body
is unambiguously an `f`: it has the ascender and crossbar, where the adjacent
`ř` is x-height with a shoulder. That would make the character `f` + U+030C.

**Not changed.** Maintainer ruling, 2026-09-07: one glyph on a 1962 mimeograph
is not enough to move a published letter a third time. Recorded so the next
reader starts from this rather than re-deriving it. Additional evidence that
would settle it: another occurrence anywhere in the SIL Work Papers series, or
a statement of the transcription's symbol inventory.

## 3. Checked and matching

Read against the scan and found faithful, so listed here to save the next
reader the work:

- The three printed titles, their English gloss lines, and their position in
  the article's two-line example format.
- The five slashed word glosses (`good/holy` p. 18 ex. 3, `noon/lunch` p. 19
  ex. 15, `trip/walk` p. 19 ex. 17, `whole/all` p. 19 ex. 2 of *Silo*,
  `and/with` p. 19 ex. 4 of *Silo*) — the slashes are the article's own.
- The parenthetical glosses `is (existing)`, `you (pl)` and the translation
  `eleven (?) o'clock` — all printed.
- `ř` vs `r` throughout: the transcription distinguishes them, and the XML
  does too.

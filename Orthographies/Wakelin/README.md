# The Wakelin 1958 Yami orthography

`Yami.tsv` is the phoneme table for the writing system used in

> Indosan, S., Wakelin, G., Dararyaw, S., and Kalaku, S. (1958). Yami texts.
> Work Papers of the Summer Institute of Linguistics, University of North
> Dakota Session: Vol. 2, Article 7. 10.31356/silwp.vol02.07

It is used by `add_phonology.py --orthography Wakelin` to generate PHON for the
**original** tier of `Corpora/WakelinTexts`. The companion
`../ConversionTables/Yami_Wakelin_113.tsv` converts that orthography into
Ortho113 to build the **standard** tier, whose PHON then comes from
`../Ortho113/Yami.tsv` in the ordinary way.

The article never states its writing system. Everything below was worked out
from the text itself, from the article's own key and errata, and by testing
proposed readings against the rest of FormosanBank's Yami data — 12,831 word
types over 135,435 tokens from RauDong, ePark, ILRDF_Dicts and
Presidential_Apologies. The measure used throughout is **attestation**: apply a
candidate rule and ask how much of Wakelin's text turns into forms that actually
occur in modern Yami, preferring matches whose glosses agree on both sides.

Under the tables as they stand, **78.7% of Wakelin's morph tokens** reach an
attested modern form, against a 45.9% baseline with no rules at all.

## Two cautions about the evidence

**Non-attestation is not disproof.** The reference data is fifty to seventy
years younger than Wakelin. A form that fails to match may be an orthographic
mismatch, or it may be a word that has changed or fallen out of use — `dewdew`
'foreigner' occurs seven times in Wakelin and matches nothing modern, with no
near neighbour. So a match counts as evidence for a rule; a non-match is only
weak evidence against one.

**The reference is not one orthography.** Modern Yami as represented here does
not consistently distinguish `l`, `z`, `r` and `y`: there are 20–34 co-attested
minimal pairs for every combination — `sira` ~ `siya`, `rana` ~ `yana`, `ala` ~
`aza` ~ `aya`, `malahet` ~ `marahet`. Any rule touching those letters cannot be
validated by attestation alone, and one such rule is left unresolved below.

## The vowels

**`u` is the phoneme Ortho113 writes `o`.** This single rule is worth 28 points
of token attestation, and three independent things support it:

- Wakelin barely uses the letter `o` — four word types in the whole corpus,
  against 510 tokens of `u`. A five-vowel system with a near-empty `o` slot is
  not a five-vowel system.
- The article's **own errata correct `o` to `u` twice** (F16 `di-kong-mi-lis` →
  `di-kung-mi-lis`, F17 `i-kongu` → `i-kungu`). Its typists treated `o` as the
  error and `u` as the norm.
- The gloss-matched pairs are the commonest words in the language: `su` → `so`
  斜格 (3,608 tokens), `u` → `o` 主格 (7,892), `ku` → `ko` 1.S.GEN (3,494),
  `mu` → `mo` 你.屬格 (2,485), `tau` → `tao` 人 (1,211), `nu` → `no` (4,540).

This is ordinary 1950s Americanist practice: write /u/ with `u`, where the later
official orthography chose `o`. Ortho113 itself maps `o` to [o] *or* [u], so the
two are the same phoneme in the target. The surviving `o` is mapped to itself.

**`e` is the schwa [ə]**, following Ortho113. This is the least settled vowel.
The article notes that /e/ and /a/ "fluctuate freely", `pengsu` corresponds to
modern `pongso` 'island', and the narration suffix `-em` corresponds to modern
`am` — so some Wakelin `e` is not a schwa. No blanket rule improved matters
(both `e` → ∅ and `e` → `a` lost ground overall), so the conditioning is real
and unsolved, and the plain Ortho113 value stands.

## The consonants

**`ch` is the digraph for /ʨ/, Ortho113's `c`.** The letter `c` occurs in
Wakelin *only* in this digraph — 76 of 77 occurrences, the odd one being the
`(unctn)` annotation rather than a letter. Confirmed by `chita` → `cita` 'see'
and `chitaǥen` → `citahen` (28 tokens).

**`ǥ` is a barred g, and it is modern `h` [ɰ].** The typescript distinguishes a
plain `g` from a g overstruck with a horizontal bar. It is phonemic, not scan
noise: the bar falls only on `g`, never a neighbouring letter; plain-g words
(`kangkang`, `m-angay`, `kagling`, `ragaw`) are never barred; every token of a
barred lexeme is barred; and the article's own errata reproduce the bar in their
"for …" fields, so its typists treated it as a character of the text.
Post-errata it maps exactly onto modern `h`: `vaǥay` ~ *vahay* 'house' (487
tokens), `aǥapen` ~ *ahapen* 'take', `laǥet` ~ *rahet* 'bad'. Barred g for a
voiced velar fricative is standard 1950s SIL practice.

**`r` is Ortho113's `r` [ɻ]**, and cleanly so: 19 of 47 word types and 93 of 140
tokens attest under that reading, against 10/30 for `z` and 5/11 for `l`, with
gloss agreement throughout — `rana` 已經, `sira` 3.P.NOM, `araw` 天 'days',
`ciring` 話 'words', `ngaran` 名字 'name', `sorod` 'comb', `itoro` 'give'. Note
it covers **both** modern `r` and modern `z` (`ripus` → `zipos` 'relative',
`ragaw` → `zagaw` 'neck', `marikna` → `mazikna` 'tired', all gloss-confirmed),
so Wakelin does not mirror the modern three-way liquid contrast.

**`ř` is deliberately left unmapped, and surfaces as `*` in PHON.** It is a
third liquid, distinct from `r` and `l`, and it is **not one modern phoneme**.
Of eleven words containing it, five resolve to an attested modern form — and
they resolve three different ways:

| Wakelin | gloss | modern | via |
| --- | --- | --- | --- |
| `ařwa` | 'two' | `adoa` (87 tokens, 'two') | `d` |
| `kařwan` | 'other' | `kadoan` (30, 'other') | `d` |
| `ařima` | 'five' | `alima` (64, 五) | `l` |
| `vařit` | 'bamboo strips' | `vazit` (9, 藤 'rattan') | `z` |
| `sipřutan` | 'strike' | `sipzotan` (1, 'whip') | `z` |

The other six resolve to nothing under any mapping. Corpus-wide the choice makes
no difference — `ř` is only 15 tokens, so every candidate lands within 0.2
points — which means aggregate attestation cannot decide it and gloss evidence
disagrees with itself. A single letter-to-letter row would therefore be a
fiction. The five known words are standardized individually by
`Corpora/WakelinTexts/CodeAndDocs/r_caron_words.tsv`; everywhere else `ř` is
carried through unchanged and stars.

If a single IPA value is ever wanted, the least bad is **[ɽ], the retroflex
flap**: all three modern reflexes are voiced coronals, and [ɽ] is retroflex like
`d` [ɖ], flapped like `z` [r] and liquid like `l` [l]. `*` is preferred because
[ɽ] asserts a segment nobody has heard.

**`h` alone occurs once** in the whole corpus (`ha-na-ni-aep`, from erratum
D14). There is no evidence for a value, and none is asserted.

## `?` is a glottal stop, and the conversion deletes it

Two sources agree that the letter is /ʔ/. The Ortho113 specification (pp. 21–23,
§九 雅美) *removed* [ʔ] from the Yami consonant table and moved it to the notes,
which state that the letter `’` marks the glottal stop, "a consonant that causes
a pause or breaks a syllable", kept by community decision but left out of the
tables. And the article's own errata delete `?` **exactly twice** (A42, A43),
both times word-finally before the vowel-initial word `u` — the hiatus where a
glottal transition is automatic — and leave it everywhere else. Of the 21
surviving occurrences, 8 are sentence-final and 10 precede a consonant, so it is
not merely a hiatus marker.

The profile therefore gives `?` → /ʔ/. **The conversion table nevertheless
deletes it**, for a different reason: modern Yami writes `’` medially (668
occurrences) and initially (306) but essentially **never word-finally** — 8 in
135,435 tokens, all apparent typos. Wakelin's `?` is word-final in every word
that has it, so mapping it to `’` would generate forms that do not occur in the
target. ⚠️ This is a real and documented loss: Ortho113 as practised cannot
represent a word-final glottal stop, so the standard tier discards a distinction
the original tier records. That is a property of the target, not a judgement
about the source, and it is a reason to treat the original tier as
authoritative.

## The glide rows, and why the table's order matters

Wakelin writes a glide where modern Yami writes a vowel, but **only after a
consonant**: `kwan` 'said' → `koan` 說 (746 tokens) is the clearest case. A
blanket `y` → `i` *loses* seven points, because word-initial `y` is a real
consonant (`ya`, `yaken`).

`standardize.apply_standard` iterates the conversion table's rows **in order**
and does a plain string replacement for each, so a context-sensitive rule can be
written as a set of multi-character rows. The sixteen consonant+glide sequences
that actually occur are therefore listed individually, and they are placed
**after** `ǥ` → `h` and `ch` → `c` (so that the digraphs are computed on the
post-substitution alphabet, which is what lets `panchy-` reach `panci`) and
**before** the single-letter rows.

**The row order in `Yami_Wakelin_113.tsv` is load-bearing. It is not an
alphabetical list, and reordering it will silently change the output.**

## What the tables do not fix

About a fifth of Wakelin's morph tokens still do not reach an attested modern
form. Much of that is not orthographic:

- **Segmentation.** Wakelin hyphenates proclitics that modern orthography writes
  bound — `k` 'in', `s` 'NM', `y` 'VR', `d` 'to' — roughly 55 tokens with
  nothing to match against.
- **Vocabulary.** `dewdew` 'foreigner' and others are simply 1950s words.
- **The `e` correspondence**, unsolved as described above.

A better test would run against Rau & Dong alone, so the target is one
orthography rather than four merged sources with the liquid variation described
at the top. That would probably lower the headline figure and make it mean more.

The measurement harness and the full working are in
`claudeplans/2026-09-07-wakelin-orthography-proposal/`.

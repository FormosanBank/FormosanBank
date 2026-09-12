# Uncertain decisions

Readings that are defensible but not certain, each with what the page shows,
what the corpus does, and why it could be wrong. The maintainer asked for this
list on 2026-09-11 so that a reader of the corpus can see where a judgement was
made rather than a fact recorded.

Every other decision in this corpus is either mechanical (a rule that applies
everywhere and is tested) or ruled (recorded with the maintainer's own words in
`entry-rulings.json` or `curated-readings.json`). These are the ones that are
neither.

---

## 1. `anun iza/anun-in ata iza ita` — printed p. 296

**The page** sets one slash in the middle of a short sentence.
**The corpus** splits at the slash: `anun iza` and `anun-in ata iza ita`, from a
curated entry — the two sides share only `iza`, which is too little for the
reordering rule to reach.
**Why it might be wrong** The two readings are very different lengths, so the
slash may separate a word rather than two whole clauses; if it does, the shorter
reading is missing its predicate. The maintainer ruled the split and asked for
the case to be listed here.

## 2. `... kun-na-tmaz/pish-na-tmaz cicu a punuq` — printed p. 924

**The page** puts the slash between two morphologically parallel words inside a
long sentence, and the words `cicu a punuq` appear both before and after it.
**The corpus** treats the slash as separating just the two words, so both
readings carry the whole frame.
**Why it might be wrong** The maintainer: *"I'm guessing that actually just the
two words alternate (kun-na-tmaz vs. pish-na-tmaz), but this is very uncertain."*
If the slash really separates two clauses, the second reading is a fragment.

## 3. `q-m-usaz iza/q-m-usaz a qali` — printed p. 815

**The page** repeats `q-m-usaz` on both sides of the slash.
**The corpus** splits at the slash: `q-m-usaz iza` and `q-m-usaz a qali`.
**Why it might be wrong** Because the verb is printed twice, `qali` could be a
tail both readings share, giving `q-m-usaz iza qali`. The maintainer ruled the
split and said *"Probably. Put this on our uncertain list."*

## 4. `danshiqan ma-nasha sa bzu/ma-pucum, capu-i uan` — printed p. 341

**The page** puts the slash after `bzu`, which is an argument of `ma-nasha`.
**The corpus** reads the alternation as the whole verb phrase, on the
maintainer's own analysis: `danshiqan ma-nasha sa bzu, capu-i uan` and
`danshiqan ma-pucum, capu-i uan`.
**Why it might be wrong** The maintainer: *"So there should only be one matrix
verb. What's going on here is that `bzu` appears to be an argument of
`ma-nasha`. ... Maybe. Definitely put this on our uncertain list."*

## 5. `ata ihu/tu patatara sa suma` — printed p. 694

**The page** puts the slash between `ihu` (a pronoun, "you") and `tu` (a
particle).
**The corpus** keeps the frame: `ata ihu patatara sa suma` and
`ata tu patatara sa suma`.
**Why it might be wrong** The two alternants are different parts of speech, so
it is not the usual substitution of one word for a comparable one. The
maintainer ruled the frame right and said *"But this is one for our
low-confidence list."*

## 6. Proper names glossed by a description — 169 senses

**The page** glosses `Abish` as *male name (husband of Kaluzut)*, `Rariku` as
*first district clockwise from Qaqcin*, `Lhqapamumu` as *a lineage name*.
**The corpus** publishes the name as the English and the description as a note,
on the maintainer's ruling of 2026-09-11 for `Rariku`, `Lhqapamumu` and
`Lhqatafatu`, extended to the rest of the class by a mechanical test so that no
judgement sits inside the pipeline. The test takes a sense only when the
headword is capitalised AND either the head of the gloss, up to its first
bracket or clause break, IS the word `name` (`male name`, `a lineage name`,
`a Thao dog name` - fourteen distinct heads in the book, all of that shape), or
the gloss is Blust's district formula, an ordinal followed by `district
clockwise from`.
**Why it might be wrong** It is deliberately narrower than the whole class.
`Haipin` *"name of a boat built by the Kao family in the story of the white
deer"* describes the referent rather than the kind of name and is left alone,
with 62 other capitalised headwords - among them `Maranash` "Japanese" and
`Shput` "Han people, Chinese", which are real translations and must stay.
Whether the boat names and the like should follow has not been ruled.

## 7. `maka-sia-siaq` p. 565 and `ma-kimzi` p. 567

Two entries whose sense has no definition, for two different reasons, neither
ruled. `maka-sia-siaq` has a cross-reference that wraps across a line break
(`->|sia-` then `siaq|:2`) and the continuation opened a sense of its own.
`ma-kimzi` is followed by an entry the book sets entirely in the sub-entry face
and indents like a continuation, so `makin-a-ihih continuously moan or groan`
reads as a form with the definition run into it. Both are printing anomalies,
one instance each. **Open.**

## 8. `/f/` is [f] in the original tier and [ɸ] in the standard tier

Blust p. 18 lists the symbols whose values are not the customary ones as exactly
`' g c sh z lh`; `f` is not among them, and p. 41 gives the value: *"The phonemes
/f/, /s/, /sh/, and /h/ are voiceless fricatives — labiodental [f], dental [θ],
palatal [ʃ], and glottal [h]"*. So the original PHON tier, which spells Blust's
own orthography, uses [f]. The standard PHON tier follows FormosanBank's
Ortho113, which maps `f` to [ɸ] as every other Thao profile in the bank does.
The two tiers therefore disagree about this one letter, on purpose.

Blust also records that the value is unstable: *"In casual speech /f/ is commonly
pronounced as [h] ... It is likely that /f/ to /h/ is a sound change in progress"*.
Neither PHON tier represents any of that variation; both give the citation form.

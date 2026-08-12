# Wakelin Yami texts (1958)

## License and AI Use

This corpus is subject to its source license and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

Indosan, S., Wakelin, G., Dararyaw, S., and Kalaku, S. (1958). Yami texts. Work Papers of the Summer Institute of Linguistics, University of North Dakota Session: Vol. 2, Article 7. 10.31356/silwp.vol02.07

Authors cannot be located. This text was previously licensed as CC-BY-ND by publisher, which we have interpreted liberally. If you are a copyright owner, please reach out to us.

## Contents

Six Yami (`xml:lang="tao"`, `dialect="Yami"`) narrative texts, collected on Orchid Island between 1955 and 1957 and published in the 1958 SIL Work Papers article reproduced at [`CodeAndDocs/Original.pdf`](CodeAndDocs/Original.pdf). Each sentence carries an English free translation; the texts are fully segmented into words and morphemes, with English glosses on both tiers. There is no audio.

> **Before you use this corpus: it has an `original` tier and nothing else.**
> Every `<FORM>` in it is `kindOf="original"` — the text as the 1958 article
> prints it. There is **no `standard` tier** and **no `PHON` (IPA) tier**,
> at the sentence, word or morpheme level. That is deliberate: the article's
> orthography has never been identified and we have no trustworthy way to
> convert it (see [Orthography](#orthography) below). Tooling and analyses
> that expect a standard tier will find none here; read the original tier
> instead, and treat its spelling as the article's own, not as
> FormosanBank's common orthography.

| File | Text in the article | Informant | Sentences | Words | Morphemes |
|---|---|---|---|---|---|
| `XML/Yami/Kangkang.xml` | A. *Ji Kangkang* (The Rooster) | Samen Indosan, April 1955 | 43 | 216 | 255 |
| `XML/Yami/Kwaway.xml` | B. *Kwaway* (The Spirit) | Sinan Dararyaw, May 1957 | 62 | 267 | 340 |
| `XML/Yami/Kalaku1.xml` | C. | Saman Kalaku, 6 September 1956 | 20 | 86 | 121 |
| `XML/Yami/Kalaku2.xml` | D. | Samen Kalaku, 6 September 1956 | 14 | 76 | 114 |
| `XML/Yami/Kalaku3.xml` | E. | Saman Kalaku, 13 September 1956 | 10 | 48 | 82 |
| `XML/Yami/Kalaku4.xml` | F. | Saman Sunagu, January 1957 | 23 | 158 | 185 |

Note that text F was given by Saman Sunagu, not by Saman Kalaku; the `Kalaku4` file name and TEXT id are historical and are kept because published identifiers are stable, but the attribution above is the one to cite.

## Orthography

**The orthography of these texts has not been identified, and no orthographic conversion is applied to them.** The article gives no statement of its writing system, and the transcription does not match any orthography currently profiled in [`Orthographies/`](../../Orthographies/): it uses `u` where modern Yami spelling uses `o`, `e` for a vowel the article describes only as fluctuating with `a`, and it has no `'`, `j`, or `z`.

It does have one symbol worth knowing about before using the data:

- **`?` is a letter, not punctuation.** There are **47 occurrences**, and they sit *inside* single words, word-internally and word-finally, on the word and morpheme tiers as well as the sentence tier — `tau?` 'person', `uvi?` 'potato', `lavi?` 'cry', `kayu?` 'tree', `ina?` 'mother'. They appear in plainly declarative sentences: `amyan su tau? nu-kakwa i-m-angay mang-aep su uvi?` = "A long time ago, there was a person who went to get some potatoes." On the evidence it writes a consonant that modern Yami spelling leaves unwritten, most plausibly a glottal stop — but **that identification is not confirmed**, and it is the single largest reason the writing system as a whole cannot be pinned down. Do not strip it as punctuation, and do not read a sentence containing it as a question.

### Why there is no standard tier and no IPA

A `standard` FORM is a claim that a passage has been transliterated into FormosanBank's single common orthography, and a `PHON` is a claim about how it was pronounced. Making either claim requires knowing which letters the source is using and what they stand for. Here we do not, so the corpus makes neither claim: **the published XML carries only the `original` tier.**

Concretely:

- **No orthographic conversion exists for this text.** The only table that ever purported to convert it, `Yami_Wakelin_113.tsv`, had a single rule — delete `-` — and mapped no letters at all; its source profile `Orthographies/Wakelin/Yami.tsv` was never written, so the table could not even be validated. It has been deleted from the repo. Earlier releases of this corpus did ship a standard tier produced by that table; it was the original text with its hyphens removed, and it asserted nothing. It is gone.
- **No phonology can be generated.** This was tested, not assumed. Running `add_phonology` with `Ortho113` — the profile Yami is assigned in [`standards.csv`](../../standards.csv) — yields 4240 IPA values and **zero** `*` uncertainty markers, i.e. it fails silently rather than loudly. It deletes every one of the 47 `?` letters (`tau?` → `tau`), and it invents sound values the article never claimed: `su` → `ʂu` (retroflex), `s-ina-na` → `ɕinana` (alveolo-palatal), `-em` → `-əm` (schwa, for the very vowel the article calls unstable). That is a fabricated pronunciation, so no phonology step is run.

If the orthography is later identified — starting with a confirmation of what `?` writes — a standard tier and a PHON tier can be generated by adding steps to the pipeline below. Until then their absence is the honest state of the data.

## Source notation preserved in the original tier

Two notations from the printed article survive in the text and are faithful to it — they are not conversion artifacts:

- **`( )` marks a probable discrepancy** in the data, per the article's own key: `(n)aku`, `ku(a)`, `puken-(en)`. In `Kalaku4.xml` sentence S2 the parentheses span several words in the article, so individual word FORMs there carry an unmatched `(` or `)`.
- **`/` separates alternative forms** that the article itself offers for the same stretch of text: `am/namen`, `varit/yaked`, `pipangn-epen/pipangungn-epen/pipangengne-eben`. These have not been split into separate sentences.

Hyphens mark morpheme boundaries, and are kept exactly as the article prints them, at every level. (In corpora that have a standard tier, sentence-level standard FORMs normally have these hyphens removed so that tier reads as running text. There is no standard tier here, so nothing is de-hyphenated: a sentence FORM reads `mang-anak-u-em`, as the article does.)

## KEY to symbols and abbreviations (from the article)

```
CM     construction marker      pl     plural
NM     name marker              incl   inclusive
unan   unanalyzed               VR     verbalizer
unctn  uncertain                rdpl   reduplication
imp    imperative               intrg  interrogative
EA     added from data of Erin Asai
( )    in data, probable discrepancy
```

The article also notes that the 'narration' suffix `-em`/`-m` occurs throughout without a translation given, and that phonemes /e/ and /a/ fluctuate freely.

## Project structure

- **`XML/`** — the published FormosanBank XML.
- **`CodeAndDocs/`**
  - `Original.pdf` — the 1958 article, the source of every sentence here.
  - `pre_correction_snapshot/XML/` — the hand-typed XML as first entered (see below).
  - `make_xml.sh` — regenerates `XML/` (see below). The one entry point.
  - `drop_derived_tiers.py` — pipeline step 2 (see below).

## Provenance and the pre-correction snapshot

These texts were transferred from the printed article to XML **by hand**. There is no scraper and no OCR stage, so the hand-typed XML *is* the corpus's source data and the corpus cannot be regenerated from anything else. It is therefore preserved verbatim in `CodeAndDocs/pre_correction_snapshot/XML/`, which is the baseline the pipeline below builds from. Neither the snapshot nor the published XML is ever edited by hand: every change to either comes from committed code.

## Processing pipeline

The whole pipeline is one script:

```bash
./CodeAndDocs/make_xml.sh [FORMOSANBANK_ROOT]
```

It restores `XML/` from the pre-correction snapshot and then runs the two steps below, using the QC scripts of the FormosanBank checkout the corpus lives in (pass a path, or set `FORMOSANBANK_ROOT`, to use another checkout; set `PYTHON` to override the interpreter, which defaults to that checkout's `.venv`). It is idempotent — it always rebuilds from the snapshot, so a second run reproduces the first byte for byte.

**Step 0 — restore.** `XML/` is deleted and re-copied from `CodeAndDocs/pre_correction_snapshot/XML/`. That snapshot is the corpus's source data (see "Provenance" above) and is never edited; every published byte is derived from it by the steps below.

1. **Clean the XML**

   ```bash
   python QC/cleaning/clean_xml.py --corpora_path Corpora/WakelinTexts/XML
   ```

   Removes empty elements, normalizes Unicode to NFC, decodes HTML escapes, and canonicalizes typographic look-alikes (curly quotes, dashes, tildes) and null-morpheme glyphs. The hand-typed text is plain ASCII, so this step currently changes nothing; it is the guarantee that it stays that way.

2. **Drop the derived tiers**

   ```bash
   python Corpora/WakelinTexts/CodeAndDocs/drop_derived_tiers.py \
       --corpora_path Corpora/WakelinTexts/XML
   ```

   Deletes every `FORM[@kindOf="standard"]` and every `PHON`, at sentence, word and morpheme level, leaving the `original` FORMs and the translations untouched. On the current snapshot it removes **2120 standard FORMs** (172 at S level, 851 at W, 1097 at M) and **0 PHON** — the snapshot has never contained a PHON. PHON is handled anyway so that "this corpus asserts no orthography and no pronunciation" is a guarantee of the pipeline rather than an accident of the input.

   The snapshot does contain a standard tier: it was written years ago by the `Yami_Wakelin_113.tsv` "conversion table", and it is the original text minus its hyphens. Because the snapshot is the reproduction baseline it is not edited to remove that tier; the tier is removed on the way out of it, by this committed step, on every run.

There is deliberately **no** `standardize.py` step and **no** `add_phonology.py` step; see "Why there is no standard tier and no IPA" above.

Any `cleaner_warnings.csv` file a run leaves behind is a per-run report: read it, then delete it. Never commit it. This corpus currently produces none.

## Known caveats

- Several words are not fully analyzed on the morpheme tier: some words carry no morphemes at all, and in a few cases the morpheme count does not match the hyphenation of the word's FORM. The word tier likewise does not line up with the sentence in `Kalaku1.xml` S20, where the sentence is a three-way `/` alternation but only one alternative is segmented.
- `Kwaway.xml` S36 and S40 are the same sentence. This is a narrative, and the repetition is in the article.

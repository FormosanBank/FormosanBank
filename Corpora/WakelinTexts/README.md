# Wakelin Yami texts (1958)

## Rights

**License:** CC BY-NC-ND 4.0
**Rights source:** Summer Institute of Linguistics / University of North Dakota (publisher), 2026-08-23; evidence: ask maintainer

> Indosan, S., Wakelin, G., Dararyaw, S., and Kalaku, S. (1958). Yami texts. Work Papers of the Summer Institute of Linguistics, University of North Dakota Session: Vol. 2, Article 7. 10.31356/silwp.vol02.07

The individual authors cannot be located. The publisher released the article as **CC-BY-ND**, and FormosanBank has **interpreted that licence liberally** in order to publish the texts with their glosses and translations; publication rights were confirmed by the maintainer on 2026-08-23. The value recorded in `TEXT/@copyright` is `CC BY-NC-ND 4.0`, the `rights_vocabulary.csv` spelling (POL-042; an unversioned licence is 4.0). If you are a copyright owner, please reach out to us.

This corpus is also subject to the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

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
| `XML/Yami/Kangkang.xml` | A. *Ji Kangkang* (The Rooster) | Samen Indosan, April 1955 | 44 | 219 | 260 |
| `XML/Yami/Kwaway.xml` | B. *Kwaway* (The Spirit) | Sinan Dararyaw, May 1957 | 64 | 278 | 348 |
| `XML/Yami/Kalaku1.xml` | C. | Saman Kalaku, 6 September 1956 | 21 | 92 | 131 |
| `XML/Yami/Kalaku2.xml` | D. | Samen Kalaku, 6 September 1956 | 14 | 76 | 114 |
| `XML/Yami/Kalaku3.xml` | E. | Saman Kalaku, 13 September 1956 | 11 | 56 | 92 |
| `XML/Yami/Kalaku4.xml` | F. | Saman Sunagu, January 1957 | 24 | 161 | 189 |

Sentence counts exceed the article's printed sentence numbers because seven printed alternations are published as separate sentences — see [Alternations](#alternations-the-sources-slash-notation) below.

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
- **`/` separated alternative readings** in the article: `am/namen`, `varit/yaked`, `pipangn-epen/pipangungn-epen/pipangengne-eben`. **No published FORM keeps a slash** — every one is resolved, either into `alternate` siblings or into separate sentences. See [Alternations](#alternations-the-sources-slash-notation) below.

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
  - `pre_correction_snapshot/XML/` — the hand-typed XML: this corpus's source of record (see below).
  - `generate_xml.sh` — the one entry point; regenerates `XML/` (POL-047).
  - `generate_xml.py` — step 1, the corpus-local parser.
  - `alternative_decisions.json` — how each printed alternation is published.
  - `source_discrepancies.md` — snapshot-vs-article findings that are still open.
  - [`provenance.json`](CodeAndDocs/provenance.json) — the FormosanBank commit `XML/` was built against (POL-052).

## Provenance and the pre-correction snapshot

These texts were transferred from the printed article to XML **by hand**. There is no scraper and no OCR stage, so the hand-typed XML *is* this corpus's source data: `CodeAndDocs/pre_correction_snapshot/XML/` is its **source of record** (POL-035), and the published `XML/` is derived from it on every run.

Because it is the source and not a build artefact, the snapshot is where a *source* correction belongs — a misread letter, a missed erratum, a mis-segmented word. Such corrections are made in the snapshot, and each one is evidenced against `Original.pdf` in [`CodeAndDocs/source_discrepancies.md`](CodeAndDocs/source_discrepancies.md). Everything *downstream* of the snapshot — the alternation handling below — is done by committed code, never by hand (POL-038). The published `XML/` is never edited directly.

The snapshot carries the `original` tier only. It once also held a `standard` tier written by the `Yami_Wakelin_113.tsv` "conversion table"; that tier was the original text minus its hyphens and asserted nothing, and both it and the table are gone.

The FormosanBank commit the published XML was built against is recorded in [`CodeAndDocs/provenance.json`](CodeAndDocs/provenance.json) (POL-052).

## Alternations: the source's slash notation

The article prints 18 alternations with a slash — `nipi/niripi`, `varit/yaked`, `akak-aep-an/(mangday su aep)`. These record **the transcriber's uncertainty about what was said**, not alternatives the speaker offered. That distinction matters: POL-027 turns a speaker's alternatives into one sentence per option, and applying it here would manufacture sentences the narrator never produced.

Each alternation is therefore classified by hand in `CodeAndDocs/alternative_decisions.json`, which records the printed string, the decision and the reason for all 18 (POL-039 — the table is data, not code). Two rules:

- **A clear spelling variant** — mostly overlapping letters, and the same gloss — is published as `FORM[@kindOf="alternate"]` siblings on the node that varies *and on each of its ancestors*, so the sentence, the word and the morpheme each read as one continuous text. 11 alternations: `nipi/niripi`, the `nem ~ namen` pronoun (six times), `mi-kalakala/mi-karakara`, the purely hyphenational `mikabak-abay-u/mikabakabayu`, and `pipangn-epen/pipangungn-epen/pipangengne-eben`, which is three-way.
- **Everything else** — different lexemes, different glosses, or a word against a phrase — becomes **separate sentences**. 7 alternations. The first branch keeps the printed sentence number and the rest take `b`, `c`, …: `Kwaway/S48` and `Kwaway/S48b`. POL-037 forbids renumbering an already-published bare id, so there is no `S48a`.

Two calls are marked `review: true` in the table as genuinely borderline: `Kalaku1/S6`, whose recorded alternate looks truncated, and `Kwaway/S2`, a single-vowel `a/u` alternation kept as a spelling variant even though the two share no letters.

## Processing pipeline

The whole pipeline is one script (POL-047):

```bash
./CodeAndDocs/generate_xml.sh [FORMOSANBANK_ROOT]
```

It rebuilds `XML/` from the snapshot using the QC scripts of the FormosanBank checkout the corpus lives in (pass a path, or set `FORMOSANBANK_ROOT`, to use another checkout; set `PYTHON` to override the interpreter, which defaults to that checkout's `.venv`). Nothing outside this checkout is required (POL-048). It is idempotent: a re-run over a clean checkout leaves `git status` empty.

1. **Generate the original tier**

   ```bash
   python Corpora/WakelinTexts/CodeAndDocs/generate_xml.py
   ```

   Reads the snapshot, applies `alternative_decisions.json`, and writes `XML/`. This is the corpus-local parsing step POL-046 exempts from "shared tools first": turning *this* hand-typed source into the original tier is inherently source-specific. It fails loudly if the snapshot ever acquires a derived tier, and if any published FORM still contains a slash.

2. **Clean the XML**

   ```bash
   python QC/cleaning/clean_xml.py --corpora_path Corpora/WakelinTexts/XML
   ```

   Removes empty elements, normalizes Unicode to NFC, decodes HTML escapes, and canonicalizes typographic look-alikes (curly quotes, dashes, tildes) and null-morpheme glyphs. The hand-typed text is plain ASCII, so this step currently changes nothing; it is the guarantee that it stays that way.

**Steps 4 and 5 of the POL-047 shape — `standardize.py` and `add_phonology.py` — are deliberately absent**, and this is the deviation POL-047 requires a corpus to state. See "Why there is no standard tier and no IPA" above. There is also no `apply_manual_edits.py` step: this corpus has no `manual_edits.xml`, because hand corrections belong in the snapshot, which is its source.

Validators do not run inside the build (POL-047, "build only"); run them from `QC/` separately.

Any `cleaner_warnings.csv` file a run leaves behind is a per-run report: read it, then delete it. Never commit it. This corpus currently produces none.

## Known caveats

- **Six source discrepancies are open**, found by checking every snapshot word against `Original.pdf` and its errata. They are listed with evidence in [`CodeAndDocs/source_discrepancies.md`](CodeAndDocs/source_discrepancies.md) and are **not** fixed: three erratum halves applied to some tiers but not others (`Kalaku2/S8W1`, `Kwaway/S4W2M2`, `Kangkang/S39` `ana-na-m` for `ama-na-m`), two internal mismatches (`Kangkang/S18W3` mis-segments `(u)`, `Kalaku4/S16W4M1` keeps the OCR spelling `cbyaa?`), and one unattested spelling (`Kwaway/S29` `tubaus` where the article prints `tabaus`). A seventh, `Kalaku1/S13W1`, is patched in memory at build time by the `snapshot_repairs` block of `alternative_decisions.json`, which fails loudly if the snapshot stops matching.
- **16 `V121` findings remain HARD.** They are the article's own optional-material parentheses inside word and morpheme FORMs — `(u)kanen-da`, `puken-(en)`, `(u)m-lavi`, `chi-ka-(y)bubu`. POL-026 would turn each into two sentences; whether to do that here is a separate question from the slash ruling and has not been decided, so the source notation stands. (`V121` was 28 before this rebuild.)
- Several words are not fully analyzed on the morpheme tier: some carry no morphemes at all, and in a few cases the morpheme count does not match the hyphenation of the word's FORM. These are the article's own selective analysis, not conversion losses.
- `Kwaway.xml` S36 and S40 are the same sentence. This is a narrative, and the repetition is in the article; both are retained under POL-022.

# Yedda Palemeq's Blog

## License and AI Use

This corpus is subject to its source license and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

## What this corpus is

Paiwan (`pwn`, Southern dialect) sentences from the "Paiwan Every Day" posts on
[Yedda Palemeq's blog](https://yeddapalemeq.blogspot.com/) — roughly 660 posts, 671 sentences.
Each sentence carries an English translation; most also carry word (`W`) segmentation with the
blog's own word glosses, and a YouTube `AUDIO` pointer to Yedda's reading of the sentence.
494 of the 671 sentences are also morpheme-segmented (`M`).

Orthography of the original tier is Ortho113. (The only difference from Ortho94 is the
addition of `o`, of which a small number appear in this text.)

Some words are glossed with an infix, written in the source with angle brackets — `k<em>acu`.
The angle brackets are stored as literal characters in the XML text (the serializer escapes
them), so the `W` FORM reads `k<em>acu` and the `M` FORMs read `k-acu` and `-em-` (POL-014:
the infixed root is one morpheme with `-` at the infixation point). Three words carry *two*
infixes — `d<em><in>udu`, `s<em><in>amalji`, `g<em><in>agalj` — and, per the maintainer's
2026-08-12 ruling, two infixes at the same site still take a single `-`: `d<em><in>udu` gives
the M FORMs `d-udu`, `-em-`, `-in-`.

**The corpus is only partly glossed and only partly parsed.** Yedda glosses the words she
wants to comment on and parses the sentences she wants to analyse; 772 `W` elements carry no
`TRANSL`, 161 sentences carry no `M` tier, and a further 16 have no `W` tier at all. That is a
property of the source, not a defect in the conversion — nothing was dropped, and no gloss or
analysis has been invented to fill the gaps.

Audio is not stored in git; fetch it with [`download_audio_data.sh`](download_audio_data.sh).

## Layout

- `XML/Paiwan/Paiwan_Yedda_Blog.xml` — the published corpus
- `CodeAndDocs/make_xml.sh` — the pipeline that produces it (below)
- `CodeAndDocs/raw_xml/` — the committed scrape output the pipeline starts from
- `CodeAndDocs/analyze_blog_structure.py` — the scraper/parser that produced `raw_xml/`
- `CodeAndDocs/fix_m_tier.py` — pipeline step 3, the per-sentence `M`-tier rule (below)
- `CodeAndDocs/Scripts/download_html.py` — downloads the blog HTML into `html_cache/`
- `CodeAndDocs/Scripts/download_audio.py` — pulls the audio from the YouTube links
- `CodeAndDocs/manual_edits.xml`, `manual_edits.md` — the recorded hand corrections (below)

## Reproducing `XML/`

```bash
CodeAndDocs/make_xml.sh            # optionally: make_xml.sh /path/to/FormosanBank
```

The script is idempotent — every step is a function of committed inputs, so re-running
reproduces `XML/` byte-for-byte. Its steps:

0. **Restore `XML/` from `CodeAndDocs/raw_xml/`.** `raw_xml/` is the parser's output, committed
   so the corpus can be rebuilt without re-scraping the blog.
1. **`clean_xml.py`** — decodes entity residue, canonicalizes Unicode and punctuation
   (square brackets to parentheses in translations, curly quotes to straight, whitespace).
2. **`apply_manual_edits.py`** — re-applies the six recorded hand corrections.
3. **`fix_m_tier.py`** — enforces the per-sentence `M`-tier rule (below).
4. **`standardize.py --remove_accents`** — builds the standard tier as a copy of the original
   with accents deleted. Only the acute accent is stripped; the macron in `āyi` is a letter of
   the source spelling and survives.
5. **`add_phonology.py --orthography Ortho113`** — generates the IPA `PHON` tiers.

### The `M` tier is per sentence

Yedda parses some sentences morphologically and leaves others unanalysed, but the parser
emitted one `M` per `W` unconditionally — so an unanalysed sentence got a tier of bare `M`
mirrors of its own words, asserting an analysis nobody made. Step 3 applies the maintainer's
2026-08-12 reading of POL-023 **per sentence**:

- a sentence carrying *some* parsing gives *every* one of its `W` at least one `M` (a lone
  `M` there reads "analysed as monomorphemic");
- a sentence carrying *no* parsing carries no `M` at all.

"Carries some parsing" means: some `W` in the sentence has two or more `M` children, or some
`M`'s FORM differs from its parent `W`'s FORM. On the current data the two clauses agree —
no sentence qualifies by the second alone. The step removed 1,165 mirror `M` from 161
sentences and added none (all 494 parsing sentences already gave every `W` an `M`).

Consequence for validators: `validate_xml`'s `V144` implements POL-023 *per file*, so it now
reports 1,165 SOFT `M`-less `W`. Those are the intended state under the per-sentence ruling;
V144 needs to be taught the per-sentence reading.

### Re-scraping (not part of `make_xml.sh`)

`raw_xml/` is refreshed only by going back to the blog, which needs network access and
`beautifulsoup4` (in `requirements.txt`, but not always installed in an existing `.venv`):

```bash
python CodeAndDocs/Scripts/download_html.py          # -> html_cache/
python CodeAndDocs/analyze_blog_structure.py --generate-xml
```

The blog's formatting is irregular — the parser identifies examples by their yellow
highlighting and carries a table of per-post special cases. Expect to extend that table
rather than to rewrite the parser.

## Manual edits

Three posts give two alternates for one word, written `qali/drava` (post 24), `abar (yasi)`
(post 483), and `tjangtjang / siyak` (post 535). Each was split into two sentences — the
`_1` sentence keeping one alternate and a new `_1b` sentence carrying the other — and the
audio was removed from the split sentences entirely — both the `AUDIO` element and the
sentence's `audio_url` attribute — because Yedda reads both options aloud, so the recording
matches neither sentence on its own and cannot usefully be aligned to either. Every other
sentence in the corpus keeps its audio (665 of 671).

In every pair the two sentences are identical except for the single `W` whose `FORM` carries
the alternate, and both sentences share the word gloss the blog gives for the pair
(`tjangtjang or siyak : pumkin`; `abar or yasi : coconut trees…`). The alternates are genuine
synonyms in the source, not optional material: post 483 is titled "abar / yasi", and the blog
glosses each pair under one entry.

Those six sentences are recorded in `CodeAndDocs/manual_edits.xml` and re-applied by step 2,
so they survive regeneration; `manual_edits.md` is the human-readable changelog. Per POL-038,
no XML file here is ever edited by hand.

**Identifier change (announced per POL-037).** Exactly one published identifier changes:
`S535_1W7` (and its `S535_1W7M1`), which used to hold `siyak`, is now `S535_1W5` (`W5M1`)
holding `tjangtjang` — unavoidable, because the word at that position is what the correction
changes, and `W5` is the id the raw parse gives `tjangtjang`. Every other `W`/`M` id in the six
split sentences keeps the numbering already published, gaps and all (POL-037: preserving ids
beats tidiness). So `S535_1` runs `W1 W2 W3 W4 W5 W8 W9 W10 W11 W12`, `S535_1b` keeps
`W1…W4 W7…W12`, `S483_1` keeps `W1…W7`, and `S483_1b` keeps `W1…W6 W8`; `S24_1`/`S24_1b` were
already contiguous. Sentence (`S`) ids are unchanged, as is every id in every other sentence.

## Duplicate sentences

Two sentences are re-posts of an earlier day's sentence with the same Paiwan text:
`S194_1`/`S511_1` and `S463_1`/`S531_1`. **Both pairs are kept.** Only literally identical `S`
blocks may be deduplicated, and neither pair is identical: within each pair the two members
carry different English translations, different word glosses, different `W`/`M` segmentation
(`aicu` vs `a-icu`, `mamaw` vs `ma-maw`, `kinamasanpazangalan` parsed only in the later post),
and different audio (different posts, different recordings). Yedda revisits the sentence with
a different analysis, so the second block is new content, not a copy. They remain 2 SOFT
within-file duplicate groups under POL-022.

## Known limitations

- **Morpheme glosses.** `M` elements carry a FORM but no `TRANSL`; the blog's glosses are
  attached at the word level. See issue #82.
- **Partly glossed, partly parsed.** 772 `W` elements have no `TRANSL` (V065) and 161
  sentences have no `M` tier. This is the source's own coverage — Yedda glosses and parses
  selectively — not a conversion defect, and it is deliberately not "fixed" by inventing
  glosses or mirror morphemes.
- **Infix function is glossed in prose, not in Leipzig notation.** 274 infix `M` sit under a
  parent gloss that does not use `<X>` notation (V062): the blog writes "bring, actor focus"
  or "bring, AV. The root is kacu 'bring'." instead of `<AV>`. The infixes involved are `-em-`
  (155), `-in-` (90), `-en-` (27), `-ema-` (1), `-ar-` (1). Under POL-036 the fix is
  *additive* — a standardized `<AV>`-style gloss would be added as a separate
  `TRANSL[@kindOf="standard"]`, never by rewriting Yedda's prose — and it is a linguist's
  judgment per word, so nothing has been changed.
- **Parentheses and slashes** appear widely in `W`/`M` FORMs and glosses (optional material,
  roots, alternates) and are preserved as the source writes them (POL-041).
- Sentence `S305_1` quotes Japanese, so its Paiwan FORM contains kana.

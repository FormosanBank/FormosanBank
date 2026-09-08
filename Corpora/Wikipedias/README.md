# Wikipedias

Articles from the Wikipedia editions for
Amis (ami), Atayal (tay), Paiwan (pwn), Sakizaya (szy), and Seediq (trv),
scraped 2026-06 and structured into the FormosanBank XML format. One XML
file per article (12,748 articles), sentence tier only (no word
segmentation, no translations).

## Rights

**License:** CC BY-SA 4.0
**Rights source:** Wikipedia contributors, 2023-06-07; evidence: ask maintainer

Wikipedia text uses CC BY-SA 4.0 under section 7 of the
[Wikimedia Terms of Use](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use/en),
effective June 7, 2023, before this June 2026 scrape. The corpus's previous
`CC BY-SA` value now includes the version required by the rights vocabulary.
Attribute the contributors through each article and its history, preserve
additional attribution notices, and identify modifications. `TEXT/@source`
identifies the article title; its language's Wikipedia and article history
provide the contributor record. The per-language citation is retained.

The corpus is also subject to the central FormosanBank notices in
[LICENSE.md](https://github.com/FormosanBank/FormosanBank/blob/main/LICENSE.md)
and [AI-USE-ADDENDUM.md](https://github.com/FormosanBank/FormosanBank/blob/main/AI-USE-ADDENDUM.md).
Commercial AI Use is prohibited without prior written permission.

## Reproducing `XML/`

The live wikis have changed since the June 2026 scrape. Rebuild from the
preserved 13,278-file [POL-035 snapshot](CodeAndDocs/pre_correction_snapshot/),
not a fresh scrape. Use the current shared FormosanBank environment:

```bash
PYTHON=python3 ./CodeAndDocs/generate_xml.sh [path-to-FormosanBank-root]
```

The optional root selects the current tools for a private development build.
In the published layout the default is the containing FormosanBank checkout.
The build reports differences from [tool provenance](CodeAndDocs/provenance.json)
and continues with the current tools. After reviewing a build intended for
commit, record its actual tools with:

```bash
python3 CodeAndDocs/generate_xml.py --record-provenance /path/to/FormosanBank
```

Steps, in order:

1. `generate_xml.py` restores the unchanged snapshot and spells its licence
   `CC BY-SA 4.0`; article text, IDs and citations remain source-owned.
2. Shared `apply_manual_edits.py` reapplies the recorded leading-`?` correction
   to Sakizaya/miladlad_tu_udip.xml, S=0 (August 12, 2026 ruling).
   [The original correction record](CodeAndDocs/manual_edits.md) is preserved.
3. `delete_duplicate_articles.py` removes 29 byte-identical repeat downloads
   of the same article ID. All groups are checked before deletion; differing
   content stops the build for review. Keep the counter-less filename, or the
   lowest counter where both names have counters.
4. `delete_nonlatin_articles.py` removes the 11 ruled non-content pages.
   The [40 exclusions](CodeAndDocs/source_exclusions.csv) name every source
   file, reason and retained duplicate counterpart.
5. `add_dialect_attrs.py` supplies `dialect="unknown"` for all five languages.
6. `normalize_seediq_quotes.py` applies the scoped quotation rulings below.
7. Shared `clean_xml.py` canonicalizes punctuation and Unicode.
8. `drop_redirect_copies.py` removes 490 repeat downloads through source
   redirects. The [source manifest](CodeAndDocs/source_redirects.csv) records
   each removed ID, retained article, historical revision or log evidence,
   and reviewed text hash. Every alias must match its retained article's
   original FORM exactly before any removal occurs (POL-022, POL-051).
9. Shared `standardize.py --remove_accents` regenerates standard FORM.
   It removes acute, breve and macron from Latin vowels while protecting
   registered standard letters. No conversion table is used.
10. Shared `add_phonology.py --orthography Ortho113` regenerates both PHON
   tiers using the corpus-wide orthography ruling below.

**POL-047 deviation:** After snapshot restoration and manual edits, the build
retains the approved duplicate-download removal, non-content removal, dialect
metadata and Seediq quotation steps before cleaning. These implement the
August 11–12, 2026 corpus decisions, not additional general cleaning rules.
The subsequent redirect-copy check runs after cleaning so it compares the
approved corrected originals; its manifest retains the historical source
evidence and a surviving counterpart for each excluded alias.

The result contains 12,748 articles: 1,892 Amis, 2,935 Atayal, 455 Paiwan,
5,498 Sakizaya and 1,968 Seediq. Each has one S with original and standard
FORM and PHON. Warning CSVs remain available in `XML/` for review;
copy them to an external report directory and do not commit them (POL-033).
The build does not download sources or run validators. Test the reviewed
source inventory, exact V129/V146 exceptions and protected corrections with:

```bash
PYTHONPATH=/path/to/FormosanBank python3 -m pytest CodeAndDocs/test_source.py
```

The [exception fixtures](CodeAndDocs/source_exceptions.csv) identify each
ruled record and its independently reviewed original FORM, not a shared
validator exemption. Current validators continue to report those findings.

### Historical scrape provenance

`download.py`, `clean_articles.py`, `remove_other_langs.py`,
`delete_empty_forms.py`, `consolidate_citations.py`, `Titles/` and their
existing logs in `CodeAndDocs/` document the historical acquisition and
filtering. Their former `Final_XML/` paths describe that obsolete process;
none runs in the current build. The POL-035 snapshot preserves the reviewed
result and subsequent manual corrections remain separate.

## Notes for data users

- **Language review remains open**: nine retained Amis-labeled biographies
  appear to contain substantial Ilocano passages: George Harrison, Joe Biden,
  Grover Cleveland, George Washington, Barack Obama, John Lennon, Ringo Starr,
  John F. Kennedy and Charles III. Their original text is preserved pending
  source-language review. Obama's article also contains Amis text, so a
  blanket article exclusion would lose relevant content. The two Seediq
  QSAN pages also retain predominantly English text and need the same review.
- **`dialect="unknown"` everywhere**: Wikipedia articles carry no dialect
  identification. For Seediq this means the corpus counts as Seediq, not
  Truku, under FormosanBank counting rules (trv counts as Truku only with
  an explicit `dialect="Truku"`).
- **One file per article**: the 29 same-ID repeat downloads are removed
  in pipeline step 3. `Sakizaya/Oro’raw (1).xml` retains its counter because
  the scrape never wrote a counter-less copy. The earlier retained
  `Atayal/msin (1).xml` and the Sakizaya African Union alias are now among
  the source-confirmed redirects; their final counterparts are recorded in
  the redirect manifest. A further 490 alias downloads point to
  retained source articles (step 8): 108 Amis, 81 Atayal, 17 Paiwan,
  194 Sakizaya and 90 Seediq. These removals do not deduplicate distinct
  source articles or different article readings merely because they match.
  Remaining cross-article repetition is reported by the duplicate validator.
- **PHON is provisional**: with dialect unknown, IPA uses default columns;
  dialect-dependent sounds appear as `[x|y]` variant groups. The corpus
  is phonologized under a blanket Ortho113 assumption, which the source
  text does not state. Characters with no IPA value (mostly digits, plus
  loanword letters and CJK) appear as `*`. What that assumption is worth,
  and what it costs, is documented in full in "Appendix - the orthography
  behind PHON" at the end of this file.
  **Decision (maintainer ruling, 2026-08-12): Ortho113 is used
  corpus-wide, for the reasons given in that appendix.** The one material
  divergence - Atayal `e` (Ortho113 `e` vs Church `ə`, 35,336
  occurrences in the August 12 inventory) - is known, quantified there, and accepted as
  unadjudicable: the articles state no orthography and carry no
  translations, so no evidence could settle which value their authors
  intended.
- **Wiki-markup residue**: some articles retain asterisks (list markup,
  reconstruction and footnote markers, separators, and multiplication),
  literal `|` from table/citation lines, and similar source-page artifacts.
  The August 12, 2026 ruling retains these characters as-is. After excluding
  verified redirect copies, 92 ASCII asterisks remain in 30 original and 30
  standard FORMs (60 V129 findings); literal pipes remain in 35 source
  articles (70 V146 PHON findings). The eight fewer V129 findings reflect
  four excluded alias copies, whose article text remains under its canonical
  source title. The abandoned
  `*` to `∗` substitution changed source text merely to avoid a validator.
  It is removed. These exact exceptions remain audit-visible and tested.

## Apostrophe (`'`) handling

Treatment differs by language (maintainer ruling, 2026-08-11):

**All languages except Seediq**: the apostrophe is the glottal-stop letter
in these orthographies, and **`'` is assumed glottal by fiat**. Wikipedia
articles carry no translations, so FormosanBank's quote/glottal classifier
cannot confirm most cases; ambiguous `'` are accepted as glottal and not
warned on. This should be revisited when a better language model can do
reliable automatic correction. (Wikipedia authors also mix straight/curly
punctuation inconsistently - e.g. Sakizaya articles write a word-final
glottal `'` followed by a curly `’` closing quote - so codepoint
distinctions in the source cannot be trusted as signal.)

**Seediq only**: Seediq orthography does not use `'` as a letter (no `'`
row in `Orthographies/Ortho113/Seediq.tsv`), and inspection of the trv
wikitext showed the corpus's apostrophes are quotation usage: literal `''`
pairs the authors typed as double-quote substitutes (`<nowiki>`-protected
so MediaWiki would not read them as italics markup) and single-quoted
titles of laws and documents. `CodeAndDocs/normalize_seediq_quotes.py`
(pipeline step 6, before `clean_xml`) therefore applies, to original FORMs
in `XML/Seediq/` only:

1. literal `''` → `"`;
2. every remaining `'` → `"`, with two exceptions that keep `'`:
   - **word-internal apostrophes** (a letter on both sides, e.g. `b'anux`,
     `hla'alua`, `mu'izzaddin`) - elided-vowel spellings and romanized
     names, not quotation marks;
   - the words `knita'` and `brbiru'`, which keep a genuine glottal `'`.
     These two occur in the article-stub boilerplate `cinkhulan sa knita'
     sa brbiru'` (≈ "source: seen in the writings/documents") and are
     Atayal vocabulary (`knita'` "view/seen", `biru'` "book/writing" -
     both attested only in Atayal corpora; Seediq uses *patas*), spelled
     with the Atayal glottal apostrophe.

## Appendix - the orthography behind PHON

This preserved August 12, 2026 analysis covers the previous 13,238-file
inventory, before redirect-copy exclusions. Its counts and percentages are
historical evidence for the unchanged corpus-wide Ortho113 ruling.

**Short version.** The `PHON` tiers in this corpus are generated by mapping
each letter of the `FORM` text to IPA through **one** orthography table -
`Orthographies/Ortho113/`, dialect-agnostic column - for all five languages
and all 13,238 articles. Wikipedia articles do not state which orthography
their author used, so this is an assumption, not a fact recovered from the
source. This appendix gives the evidence for it and the size of the residual
error, so you can decide whether `PHON` is usable for your purpose.

If you need phonemic precision, treat `PHON` here as a **broad, deliberately
under-specified** transcription and go back to `FORM`. If you need a rough
phone inventory, a searchable phonemic index, or a segment-level baseline,
`PHON` is sound to within the error described below.

### What the evidence says

FormosanBank's orthography detector scores a text's letter inventory against
every reference orthography table available for its language. Run over this
corpus, combined per language (original tier):

| language | top-scoring table | score | where Ortho113 lands |
|---|---|---|---|
| Amis | Ortho94 (all five dialect columns tie) | 88.4% | below the top 7 |
| Atayal | Church (Sekolik) / Ortho94 (Sekolik), tied | 86.1% | 5th, 84.3% |
| Paiwan | **Ortho113** (four dialect columns tie) | 82.1% | 1st |
| Sakizaya | **Ortho113** | 73.2% | 1st (Ortho94 2nd, 65.0%) |
| Seediq | **Ortho113** | 87.9% | 1st (Ortho94 4th, 87.9%) |

So Ortho113 is the best-supported table for Paiwan, Sakizaya and Seediq. For
Amis and Atayal another table scores higher - and the reason is *not* that
those wikis spell differently; see "Where the tables disagree" below.

### Is the orthography uniform across articles?

Effectively yes, as far as anything measurable shows. All 13,238 articles were
also scored individually:

| language | articles | best = Ortho113 | median score gap to the per-article winner |
|---|---|---|---|
| Amis | 2,000 | 225 (11.2%) | 0.018 |
| Atayal | 3,016 | 292 (9.7%) | 0.018 |
| Paiwan | 472 | 157 (33.3%) | 0.012 |
| Sakizaya | 5,692 | 5,209 (91.5%) | 0.000 |
| Seediq | 2,058 | 824 (40.0%) | 0.002 |

The per-article "winner" flips constantly, but the margins are within noise
(median gaps 0.000–0.018 on a 0–1 scale). The detector scores *inventory
coverage*, so a short article that happens not to use one letter of a larger
inventory hands the win to the smaller table. **These flips are scoring noise,
not evidence that different articles follow different spelling conventions.**
Nothing in the data supports phonologizing article by article, which is why a
single table is applied corpus-wide.

### Where the tables disagree - and why it mostly costs ambiguity, not accuracy

For nearly every letter where Ortho113 and a rival table differ, Ortho113's
value is a **variant group** rather than a competing single value: it records
"this letter is `o` *or* `u`" where Ortho94 commits to one. Those disagreements
therefore surface in `PHON` as explicit `[x|y]` groups you can see and handle,
not as silently wrong segments:

| language | PHON tokens containing a `[x\|y]` group | commonest groups |
|---|---|---|
| Amis | 51.4% | `[o\|u]`, `[ɬ\|ɮ]`, `[b\|v]` |
| Atayal | 24.8% | `[s\|ɕ]`, `[ʦ\|ʨ]` |
| Sakizaya | 19.0% | `[r\|ɾ]`, `[ʔ\|ʡ]` |
| Paiwan | 0% | - |
| Seediq | 0% | - |

Genuinely *conflicting* single values - where Ortho113 commits to one IPA
value and a plausible rival table commits to a different one - are few and
enumerable:

| language | letter | Ortho113 | rival | occurrences |
|---|---|---|---|---|
| Atayal | `e` | `e` | Church `ə` | 35,336 |
| Seediq | `j` | `ɟ` | Church (Tegudaya) `ɖʐ` | 18,777 |
| Sakizaya | `f` | `f` | Ortho94 `b` | 6,507 |
| Paiwan | `o` | `u` | (not listed by Ortho94/Church) | 2,031 |

Together these are **under 0.4% of the corpus's letter occurrences**. The
largest single item is Atayal `e`: Church, the corpus-wide top-scoring table
for Atayal, reads it as `ə` where this corpus writes `e`, 35,336 times. If you
work on Atayal vowels, that is the one substitution to apply yourself.

### Unmapped characters (`*`)

Any character with no IPA value in the table is written as `*` in `PHON`:

| language | `*` share of PHON characters | of the characters producing a `*`: digits |
|---|---|---|
| Amis | 1.39% | 89.3% |
| Atayal | 2.17% | 68.8% |
| Paiwan | 2.57% | 50.3% |
| Sakizaya | 2.28% | 60.4% |
| Seediq | 2.80% | 85.6% |

**None of this is attributable to Ortho113.** Between 50% and 89% of the stars
come from digits (dates, population figures, footnote numbers); most of the
rest are CJK quotations and loanword letters (`f`, `v`, `g`, `q`, `z`, `x`,
`J`, `R`) that no Formosan orthography table maps. Choosing Ortho94 or Church
instead would not change them - those tables have the same or smaller letter
inventories.

### Summary for users of `PHON`

- One table (Ortho113, dialect-agnostic) for the whole corpus; the source does
  not state an orthography, and per-article detection shows no real variation.
- Best-supported table for Paiwan, Sakizaya and Seediq; for Amis and Atayal a
  rival scores higher because it is *less* cautious, not because the wiki
  spells differently.
- The dominant cost is **ambiguity**: 19–51% of Amis/Atayal/Sakizaya `PHON`
  tokens carry a `[x|y]` variant group (0% for Paiwan and Seediq).
- Outright disputable segments are bounded by four letters, under 0.4% of
  letter occurrences, the largest being Atayal `e` (35,336).
- 1.4–2.8% of `PHON` characters are `*` (no IPA value), mostly digits.

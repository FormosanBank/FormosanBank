# Wikipedias

Wikipedia articles in the five Formosan languages that have a Wikipedia:
Amis (ami), Atayal (tay), Paiwan (pwn), Sakizaya (szy), and Seediq (trv),
scraped 2026-06 and structured into the FormosanBank XML format. One XML
file per article (13,238 articles), sentence tier only (no word
segmentation, no translations).

## License and AI Use

This corpus is subject to its source license and the central FormosanBank
terms in [LICENSE.md](../../LICENSE.md) and
[AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is
prohibited without prior written permission. Wikipedia text is CC BY-SA.

## Reproducing `XML/`

The corpus is **not re-scraped**: the live wikis have moved on since the
2026-06 scrape, so the published XML is the baseline. The pristine
pre-correction XML is snapshotted in `CodeAndDocs/pre_correction_snapshot/`
(POL-035), and `CodeAndDocs/make_xml.sh` regenerates `XML/` from it:

```bash
cd Corpora/Wikipedias
PYTHON=/path/to/python ./CodeAndDocs/make_xml.sh [path-to-FormosanBank-root]
```

Steps, in order:

1. **Restore** `XML/` from `CodeAndDocs/pre_correction_snapshot/`
   (13,278 files).
2. **`QC/cleaning/apply_manual_edits.py`** — re-applies the recorded hand
   edits in `CodeAndDocs/manual_edits.xml` (POL-030); it runs before
   `clean_xml`. One edit is recorded: `Sakizaya/miladlad_tu_udip.xml`
   `S id="0"`, whose original FORM began with a stray `? ` from the scrape
   (V142). It is not a grammaticality marker — the article body simply
   starts after it — so the `? ` is dropped (maintainer ruling
   2026-08-12); the standard tier and PHON regenerate from the corrected
   original in later steps. `CodeAndDocs/manual_edits.md` is the readable
   changelog.
3. **`delete_duplicate_articles.py`** — the scrape saved 29 articles
   twice (duplicate downloads named `<name> (1).xml` / `(2)`), giving 58
   files with colliding `TEXT/@id`. One file per id is kept — the
   canonically-named one, or the lowest counter when the group has no
   counter-less file — and the other copy is deleted (29 files). Every
   group is byte-identical across its copies, so no content is lost.
4. **`delete_nonlatin_articles.py`** — deletes the 11 articles whose
   FORMs contain no Latin letter at all (punctuation only, leftover
   `== ... ==` heading markup, or Chinese editorial remarks/headings).
   They are not language data.
5. **`add_dialect_attrs.py`** — sets `dialect="unknown"` on every TEXT.
   No Wikipedia article identifies its own dialect; the wikis are
   community-written with mixed dialect backgrounds.
6. **`normalize_seediq_quotes.py`** — Seediq only, before `clean_xml`;
   see "Apostrophe handling" below.
7. **`normalize_ascii_asterisks.py`**: replaces ASCII `*` with the Unicode
   asterisk operator `∗` in original FORMs only. The exact scraped bytes remain
   in the immutable snapshot; see "Wiki-markup residue" below.
8. **`QC/cleaning/clean_xml.py`** — punctuation/Unicode canonicalization
   (NFC, HTML entities, typographic quotes/dashes, non-breaking spaces).
   It writes a per-run `XML/cleaner_warnings.csv`. The immutable snapshot's
   residuals have been reviewed, and the pipeline deletes this run artifact
   after derived tiers regenerate (POL-033).
9. **`QC/utilities/standardize.py --remove_accents`** — standard tier =
   copy of the original tier with accents/stray combining marks removed.
   No conversion table is applied (dialect unknown).
10. **`QC/utilities/add_phonology.py --orthography Ortho113`** — PHON
   tiers from the default (dialect-unknown) IPA columns. Sounds that
   differ by dialect appear as `[x|y]` variant groups; punctuation is
   not carried into PHON.

The published corpus is the 13,238 files this leaves.

The pipeline is deterministic and idempotent: consecutive runs produce
byte-identical output.

### Historical scrape provenance (not part of the pipeline)

The original scrape-and-clean scripts and their logs are kept in
`CodeAndDocs/` for provenance only: `download.py` (Wikipedia API scrape;
article lists in `Titles/`), `clean_articles.py` (TXT → XML; link/citation
removal), `remove_other_langs.py` (strips non-Formosan text),
`delete_empty_forms.py` (drops articles left empty),
`consolidate_citations.py` (one shared citation per language Wikipedia),
and the `*.log` files recording exactly what those steps removed. Their
input (the live wikis of 2026-06) no longer exists in that state, so they
are not re-run.

## Notes for data users

- **`dialect="unknown"` everywhere**: Wikipedia articles carry no dialect
  identification. For Seediq this means the corpus counts as Seediq, not
  Truku, under FormosanBank counting rules (trv counts as Truku only with
  an explicit `dialect="Truku"`).
- **One file per article**: the 29 twice-downloaded articles now have a
  single file each (pipeline step 3). Two of them keep a `(1)` in the
  filename (`Atayal/msin (1).xml`, `Sakizaya/Oro’raw (1).xml`) because
  the scrape never wrote a counter-less copy; the file names carry no
  meaning, the `TEXT/@id` does. Sentence-level duplication *across*
  articles (wiki boilerplate) is still reported SOFT by the
  duplicate-sentence validator — this corpus declares no dedup step.
- **PHON is provisional**: with dialect unknown, IPA uses default columns;
  dialect-dependent sounds appear as `[x|y]` variant groups. The corpus
  is phonologized under a blanket Ortho113 assumption, which the source
  text does not state. Characters with no IPA value (mostly digits, plus
  loanword letters and CJK) appear as `*`. What that assumption is worth,
  and what it costs, is documented in full in "Appendix — the orthography
  behind PHON" at the end of this file.
  **Decision (maintainer ruling, 2026-08-12): Ortho113 is used
  corpus-wide, for the reasons given in that appendix.** The one material
  divergence — Atayal `e` (Ortho113 `e` vs Church `ə`, 35,336
  occurrences) — is known, quantified there, and accepted as
  unadjudicable: the articles state no orthography and carry no
  translations, so no evidence could settle which value their authors
  intended.
- **Wiki-markup residue**: some articles retain asterisks (list markup,
  reconstruction and footnote markers, separators, and multiplication),
  literal `|` from table/citation lines, and similar source-page artifacts.
  The immutable snapshot retains all 103 ASCII asterisks in 34 original FORMs
  across 34 files. Pipeline step 7 maps only those active-original code points
  to the equivalent Unicode `∗` so the validator does not misclassify them as
  acceptability notation (V129). Their visible and functional meaning is
  preserved, and the standard and PHON tiers regenerate downstream. Other
  residue remains source-faithful and audit-visible under the 2026-08-12
  maintainer ruling.

## Apostrophe (`'`) handling

Treatment differs by language (maintainer ruling, 2026-08-11):

**All languages except Seediq**: the apostrophe is the glottal-stop letter
in these orthographies, and **`'` is assumed glottal by fiat**. Wikipedia
articles carry no translations, so FormosanBank's quote/glottal classifier
cannot confirm most cases; ambiguous `'` are accepted as glottal and not
warned on. This should be revisited when a better language model can do
reliable automatic correction. (Wikipedia authors also mix straight/curly
punctuation inconsistently — e.g. Sakizaya articles write a word-final
glottal `'` followed by a curly `’` closing quote — so codepoint
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
     `hla'alua`, `mu'izzaddin`) — elided-vowel spellings and romanized
     names, not quotation marks;
   - the words `knita'` and `brbiru'`, which keep a genuine glottal `'`.
     These two occur in the article-stub boilerplate `cinkhulan sa knita'
     sa brbiru'` (≈ "source: seen in the writings/documents") and are
     Atayal vocabulary (`knita'` "view/seen", `biru'` "book/writing" —
     both attested only in Atayal corpora; Seediq uses *patas*), spelled
     with the Atayal glottal apostrophe.

## Appendix — the orthography behind PHON

**Short version.** The `PHON` tiers in this corpus are generated by mapping
each letter of the `FORM` text to IPA through **one** orthography table —
`Orthographies/Ortho113/`, dialect-agnostic column — for all five languages
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
Amis and Atayal another table scores higher — and the reason is *not* that
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

### Where the tables disagree — and why it mostly costs ambiguity, not accuracy

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
| Paiwan | 0% | — |
| Seediq | 0% | — |

Genuinely *conflicting* single values — where Ortho113 commits to one IPA
value and a plausible rival table commits to a different one — are few and
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
instead would not change them — those tables have the same or smaller letter
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

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
2. **`delete_duplicate_articles.py`** — the scrape saved 29 articles
   twice (duplicate downloads named `<name> (1).xml` / `(2)`), giving 58
   files with colliding `TEXT/@id`. One file per id is kept — the
   canonically-named one, or the lowest counter when the group has no
   counter-less file — and the other copy is deleted (29 files). Every
   group is byte-identical across its copies, so no content is lost.
3. **`delete_nonlatin_articles.py`** — deletes the 11 articles whose
   FORMs contain no Latin letter at all (punctuation only, leftover
   `== ... ==` heading markup, or Chinese editorial remarks/headings).
   They are not language data.
4. **`add_dialect_attrs.py`** — sets `dialect="unknown"` on every TEXT.
   No Wikipedia article identifies its own dialect; the wikis are
   community-written with mixed dialect backgrounds.
5. **`normalize_seediq_quotes.py`** — Seediq only, before `clean_xml`;
   see "Apostrophe handling" below.
6. **`QC/cleaning/clean_xml.py`** — punctuation/Unicode canonicalization
   (NFC, HTML entities, typographic quotes/dashes, non-breaking spaces).
   Writes a per-run `XML/cleaner_warnings.csv`: review, then delete —
   it is never committed (POL-033).
7. **`QC/utilities/standardize.py --remove_accents`** — standard tier =
   copy of the original tier with accents/stray combining marks removed.
   No conversion table is applied (dialect unknown).
8. **`QC/utilities/add_phonology.py --orthography Ortho113`** — PHON
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
  single file each (pipeline step 2). Two of them keep a `(1)` in the
  filename (`Atayal/msin (1).xml`, `Sakizaya/Oro’raw (1).xml`) because
  the scrape never wrote a counter-less copy; the file names carry no
  meaning, the `TEXT/@id` does. Sentence-level duplication *across*
  articles (wiki boilerplate) is still reported SOFT by the
  duplicate-sentence validator — this corpus declares no dedup step.
- **PHON is provisional**: with dialect unknown, IPA uses default columns;
  dialect-dependent sounds appear as `[x|y]` variant groups. The corpus
  is phonologized under a blanket Ortho113 assumption, which the source
  text does not state; see the orthography-evidence appendix in
  `claudeplans/phase-b-reports/Wikipedias.md`. Characters with no IPA
  value (mostly digits, plus loanword letters and CJK) appear as `*`.
- **Wiki-markup residue**: some articles retain asterisks (list markup),
  literal `|` from table/citation lines, and similar artifacts of the
  source pages. This residue is deliberately **retained as-is**
  (maintainer ruling 2026-08-12): it is audit-flagged (c022 / V129 / the
  `|` share of V146) but never silently edited out of the FORMs.

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
(pipeline step 4, before `clean_xml`) therefore applies, to original FORMs
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

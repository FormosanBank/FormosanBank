# Wikipedias

Wikipedia articles in the five Formosan languages that have a Wikipedia:
Amis (ami), Atayal (tay), Paiwan (pwn), Sakizaya (szy), and Seediq (trv),
scraped 2026-06 and structured into the FormosanBank XML format. One XML
file per article (12,748 articles), sentence tier only (no word
segmentation, no translations).

## License and AI Use

This corpus is subject to its source license and the central FormosanBank
terms in [LICENSE.md](../../LICENSE.md) and
[AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is
prohibited without prior written permission. Wikipedia text is CC BY-SA.

## Rights

**License:** CC BY-SA 4.0
**Rights source:** Wikipedia contributors (the source wikis' licence), date not recorded in this repository; evidence: ask maintainer

The articles are Wikipedia text, which Wikipedia publishes under CC BY-SA. The
`@copyright` value was recorded without a version (`CC BY-SA`) until
2026-10-16, when it was normalized to `CC BY-SA 4.0` under POL-042 (a value
that names no version is 4.0). The same one-attribute change was made in the
POL-035 snapshot (`CodeAndDocs/pre_correction_snapshot/`, 13,278 files),
because `generate_xml.sh` copies that snapshot into `XML/` and a rebuild must
reproduce the new value.

## Reproducing `XML/`

The corpus is **not re-scraped**: the live wikis have moved on since the
2026-06 scrape, so the published XML is the baseline. The pristine
pre-correction XML is snapshotted in `CodeAndDocs/pre_correction_snapshot/`
(POL-035), and `CodeAndDocs/generate_xml.sh` regenerates `XML/` from it:

```bash
cd Corpora/Wikipedias
PYTHON=/path/to/python ./CodeAndDocs/generate_xml.sh [path-to-FormosanBank-root]
```

The FormosanBank commit the published `XML/` was last built against is
recorded in [CodeAndDocs/provenance.json](CodeAndDocs/provenance.json)
(POL-052). The build reads it only to print a note when the checkout it runs
in is a different commit; it always builds with the tools in that checkout.

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
   original in later steps. A second Sakizaya record fixes `Luxembourg`
   (see "Apostrophe handling"). The other 30 records are Seediq: 25 restore
   article text the historical scrape cut off and 5 restore author credits
   — see "Restored Seediq source text and author credits" below.
   32 records in all; every one changes its file on a fresh build (the
   build log line is `apply: 32 edit(s) across 32 file(s); 0 no-op(s)`).
   `CodeAndDocs/manual_edits.md` is the readable changelog.
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
7. **`QC/cleaning/clean_xml.py`** — punctuation/Unicode canonicalization
   (NFC, HTML entities, typographic quotes/dashes, non-breaking spaces).
   Writes a per-run `XML/cleaner_warnings.csv`: review, then delete —
   it is never committed (POL-033).
7b. **`drop_redirect_copies.py`** — deletes 490 articles that the scrape
   downloaded a second time under a redirect title; see "Withdrawn
   articles: redirect copies" below. It runs after `clean_xml` because the
   hashes it checks are of the cleaned original FORM.
8. **`QC/utilities/standardize.py --remove_accents`** — standard tier =
   copy of the original tier with accents/stray combining marks removed.
   No conversion table is applied (dialect unknown).
9. **`QC/utilities/add_phonology.py --orthography Ortho113`** — PHON
   tiers from the default (dialect-unknown) IPA columns. Sounds that
   differ by dialect appear as `[x|y]` variant groups; punctuation is
   not carried into PHON.

The published corpus is the 12,748 files this leaves: 1,892 Amis,
2,935 Atayal, 455 Paiwan, 5,498 Sakizaya and 1,968 Seediq.

**POL-047 deviation:** besides the canonical steps (restore the source,
`apply_manual_edits`, `clean_xml`, `standardize`, `add_phonology`), the
build runs corpus-local steps 3–6 before `clean_xml` (duplicate-download
and non-content deletion, `dialect="unknown"`, the two apostrophe rulings)
and step 7b after it (redirect-copy deletion, which must compare cleaned
text). Each implements a maintainer ruling on this corpus (2026-08-11/12,
2026-10-14, 2026-10-18), not a general cleaning rule. The source is
restored by a shell loop in `generate_xml.sh` rather than a corpus-local
`generate_xml.py`, since the step is a plain copy.

The pipeline is deterministic and idempotent: consecutive runs produce
byte-identical output.

### Refreshing the source: `refresh_source.sh`

`CodeAndDocs/refresh_source.sh` (POL-047's optional source-acquisition
script) re-downloads the article text from the five live wikis with the
original scraper, `download.py`, into `CodeAndDocs/Articles/<Language>/`
(one plain-text file per article). By default it fetches every title in the
committed `Titles/` lists (the June 2026 inventory); `--new-titles` first
deletes those lists so `download.py` re-lists every article on each wiki.
It refuses to run when `Articles/` already exists, because `download.py`
skips files that are already there and would mix two download dates.
Requires network access to `*.wikipedia.org` and
`pip install -r CodeAndDocs/requirements.txt`.

`generate_xml.sh` never calls it, and a refresh changes no published data
by itself: the build reads only the committed snapshot. Turning a fresh
download into published XML is a re-scrape (the historical steps below,
reviewed, and a new snapshot committed), which needs the maintainer's
decision first.

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

## Restored Seediq source text and author credits

The historical scrape's citation cutter (`clean_articles.py`) stopped
reading 30 Seediq articles too early. 30 records in
`CodeAndDocs/manual_edits.xml` put the missing source text back
(maintainer ruling 2026-10-18, PR #176: "The manual edits are approve,
assuming they still run. The notes are approved."). Each record keeps the
article's previously published text unchanged as the start of the original
FORM; nothing already published is altered.

- **25 articles get their cut-off body text back** (28 source sections;
  Gluban has 3 and Tkijig 2). These are village articles whose later
  sections (beginning `Hangan alang` "village name") followed an early
  reference heading. The Chinese section labels that the source prints
  beside each Seediq heading — 322 in all, e.g. `Hangan alang(部落名稱)` —
  are kept in the FORM `notes` attribute, one per line, not in the text.
  Ten URL strings in the source sections are left out (link text, not
  language); the words around them are kept. Example: `Seediq/Ibuh.xml`
  went from 324 to 1,379 characters of original FORM.
- **5 articles get their author credit back**, in the FORM `notes`
  attribute only; their text is unchanged: Batul, Cyocuy, Hbun_kramay,
  Libu, Smangus (e.g. Libu: `Matis alang Ripu nii we, hlidan na Aking
  Nawi(黃美玉).`).

[`CodeAndDocs/citation_restorations.csv`](CodeAndDocs/citation_restorations.csv)
lists all 30: the source revision each was read from (a permanent
`trv.wikipedia.org/w/index.php?oldid=…` URL), the length and SHA-256 of the
previously published text that must remain the start of the FORM, the
SHA-256 of the notes, the number of restored sections and section labels,
and the excluded URLs. The restored text goes through the same Seediq
apostrophe step and `clean_xml` as everything else. These are the 30 cases
PR #176 identified; other articles cut the same way, if any, have not been
looked for since.

## Withdrawn articles: redirect copies

The scrape listed every page title on each wiki, including redirect titles,
so 490 articles were downloaded twice: once under their own title and once
under a title that redirects to it (e.g. `Amis/Abraham_Lincoln.xml` is the
article `Aparaham Linken` reached through the redirect `Abraham Lincoln`).
The copies are deleted (maintainer ruling 2026-10-18: "Yes, delete (record
the ids as withdrawn)"): 108 Amis, 81 Atayal, 17 Paiwan, 194 Sakizaya and
90 Seediq.

- [`CodeAndDocs/source_redirects.csv`](CodeAndDocs/source_redirects.csv)
  lists each deleted file and id, the kept article, the source titles, the
  evidence (wiki revision or redirect-log URLs) and the SHA-256 of the
  cleaned original FORM. `drop_redirect_copies.py` checks every copy before
  deleting any: same TEXT ids as listed, one S each, and the copy's original
  FORM identical to the kept article's and to the recorded hash. Any
  mismatch stops the build with nothing deleted.
- [`CodeAndDocs/old_to_new_ids.csv`](CodeAndDocs/old_to_new_ids.csv)
  records the 490 withdrawn `TEXT/@id`s (`old_id`), the id of the kept
  article with the same text (`new_id`), `change` = `withdrawn: redirect
  copy`, and the reason. No withdrawn id is reused.
- Six of the recorded hashes were re-recorded on 2026-10-18 when the
  deletion was ported onto the current build: the kept articles
  `Amis/Ina.xml`, `Atayal/’tayal.xml` (three copies),
  `Sakizaya/Fo-lu-lun-se.xml` and `Sakizaya/Lo-ma.xml` contain `''`, which
  the 2026-10-14 apostrophe step now writes as `"`. The copies still match
  their kept articles exactly.

Text is not lost: every withdrawn article's original FORM is published,
character for character, under the kept id. Token counts do fall, because
the copies were counted twice before: 1,311,509 tokens in all (Amis
1,131,630; Sakizaya 82,013; Seediq 65,191; Atayal 25,635; Paiwan 7,040).
Most of the Amis drop is one article: 50 redirect titles (US presidents and
`United_states`, among others) all led to the 21,766-token `Amis/Amilika.xml`
("America"), so the corpus held 51 copies of it. The 490 copies belong to
362 kept articles.

## Notes and Issues

- **`dialect="unknown"` everywhere**: Wikipedia articles carry no dialect
  identification. For Seediq this means the corpus counts as Seediq, not
  Truku, under FormosanBank counting rules (trv counts as Truku only with
  an explicit `dialect="Truku"`).
- **One file per article**: the 29 twice-downloaded articles now have a
  single file each (pipeline step 3), and the 490 copies downloaded under
  redirect titles are withdrawn (step 7b; see above). One kept file has a
  `(1)` in its name, `Sakizaya/Oro’raw (1).xml`, because the scrape never
  wrote a counter-less copy (`Atayal/msin (1).xml`, the other such file,
  is one of the 490 redirect copies); the file names carry no meaning,
  the `TEXT/@id` does. Sentence-level duplication *across*
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

**Two apostrophes (`''`), Amis / Atayal / Paiwan / Sakizaya** (maintainer
ruling, 2026-10-14): the articles were downloaded as Wikipedia's plain-text
extracts (`download.py` uses `wikipediaapi`'s default `ExtractFormat.WIKI`,
i.e. TextExtracts with `explaintext=1`), in which MediaWiki has already
rendered `''italic''` markup away. A `''` that survives is a character the
page shows — two apostrophes typed for a double quotation mark, as found for
Seediq below. `CodeAndDocs/normalize_double_apostrophes.py` (pipeline step 5b,
before `clean_xml`) rewrites every run of exactly two apostrophes in original
FORMs to `"` (380 runs in 97 articles). Runs of three or more are left alone,
since they can contain a glottal letter; the one such run that is a glottal
plus a closing quote, Sakizaya `Luxembourg` `''a puyuay nubuyu'''` →
`"a puyuay nubuyu'"`, is corrected by a `CodeAndDocs/manual_edits.xml`
record.

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
and all articles. (The figures in this appendix were computed on the
13,238 articles published before the 490 redirect copies were withdrawn on
2026-10-18; they were not recomputed.) Wikipedia articles do not state which orthography
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

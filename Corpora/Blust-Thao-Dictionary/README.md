# Blust-Thao-Dictionary

**Basecamp card:** [7012450955](https://app.basecamp.com/3340659/buckets/31258415/card_tables/cards/7012450955)

- **Primary language:** Thao, ISO 639-3 `ssf`
- **Dialect:** Thao
- **Source:** Robert Blust's 2003 *Thao Dictionary*, official Academia Sinica open-access PDF
- **Published:** 2026-09-11. Developed in a private dev repo and ported here
  once it passed QC; see "Canonical XML regeneration" for how to rebuild it.

## Rights

**License:** CC BY-NC 4.0
**Rights source:** Institute of Linguistics, Academia Sinica, 2024-01-30; evidence: ask maintainer

The Institute of Linguistics (Preparatory Office), Academia Sinica — the
publisher and economic rights holder of Blust's 2003 *Thao Dictionary* —
authorized FormosanBank to reprint, reproduce and adapt **the linguistic
material in the book** under CC BY-NC. That wording is the grant's own, and is
what puts the dictionary's headwords and definitions in scope alongside the
interlinear texts and example sentences (maintainer's ruling, 2026-09-11). The operative terms and the
checksum of the authorization document are recorded in
`CodeAndDocs/rights-evidence.json`; the document itself stays in ignored
`Private/` storage. Per POL-042 the XML's `@copyright` carries the licence
value alone — the permission behind it is documented here and nowhere else.

## Reproducible source acquisition

```bash
python3 CodeAndDocs/download_source.py
python3 CodeAndDocs/download_source.py --check
python3 -m unittest CodeAndDocs/test_source_lock.py -v
python3 CodeAndDocs/extract_source.py --check
python3 -m unittest CodeAndDocs/test_extraction.py -v
python3 CodeAndDocs/expand_source.py --check
python3 -m unittest CodeAndDocs/test_expansion.py -v
```

The exact 1,117-page PDF is locked by byte count and SHA-256 in
`CodeAndDocs/source-lock.json`. The PDF and authorization document remain in
ignored `Private/` storage. Their hashes and operative provenance are recorded
without committing private evidence.

## Corpus scope

The authorization from the Institute of Linguistics covers **the linguistic
material in the book**, not a named list of sections (maintainer's ruling,
2026-09-11). That is the five interlinear texts on printed pages 244-274 and
the Thao-English dictionary on printed pages 280-1068 -- its headwords, derived
forms, grammatical labels, definitions, etymologies, notes and
cross-references, as well as its example sentences. Front matter, the
expository chapters and the English-Thao index are not corpus source material
and are excluded.

The deterministic extraction contains five texts with 166 sentences and 2,531
raw aligned word positions, plus 8,368 dictionary examples. Explicitly optional
material and slash alternatives are expanded mechanically into complete
records, producing 167 text sentences with 2,542 aligned word positions and
8,651 dictionary sentences. Custom PDF glyphs, line-break hyphenation,
dictionary column order, and inline italic terms are handled explicitly in
`CodeAndDocs/pdf_text.py` and `CodeAndDocs/extract_source.py`. The recorded
visual review is in `CodeAndDocs/source-fidelity-review.json`.

The entry apparatus is parsed separately by `CodeAndDocs/parse_entries.py` into
`entry-records.json` -- 6,517 entries and 12,226 senses -- and built into XML by
`CodeAndDocs/build_entry_xml.py`. The two are kept in separate files because
they are different kinds of text, not for any rights reason: one S per sense in
`blust_2003_thao_entries_*.xml`, one S per example in
`blust_2003_thao_examples_*.xml`.

## Canonical XML regeneration

One entry point (POL-047), run with whatever FormosanBank tools are in the
checkout — never a pinned one (POL-048):

Run from this directory. The surrounding FormosanBank checkout is found
automatically, so there is nothing to point at:

```bash
python3 -m pip install -r requirements.txt
./CodeAndDocs/generate_xml.sh
./CodeAndDocs/generate_xml.sh --check
python3 -m unittest CodeAndDocs/test_xml.py -v
```

The build emits the raw source tiers, applies the canonical cleaner once,
creates standard FORM with the reviewed Blust-to-Ortho113 table, and creates
original and standard PHON with the recorded orthography profiles. `--check`
rebuilds in a temporary directory and requires byte-identical XML. The
canonical output is 21 files under `XML/Thao`; no `Final_XML/` tree is used.

The FormosanBank commit the published XML was built against is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052). It is
provenance, not a gate: a mismatch is noted on stderr and the build proceeds.

**No POL-047 deviation.** Every step is the shared tool, unwrapped. The two
orthography tables this corpus needs are registered in FormosanBank's own
`Orthographies/` and read from there like any other corpus's:

| file | what it is |
|---|---|
| [Orthographies/Blust2003/Thao.tsv](../../Orthographies/Blust2003/Thao.tsv) | the source orthography profile, for `add_phonology.py --orthography Blust2003` |
| [Orthographies/ConversionTables/Thao_Blust2003_113.tsv](../../Orthographies/ConversionTables/Thao_Blust2003_113.tsv) | Blust's spelling to Ortho113, for `standardize.py` |

Keeping them there rather than under `CodeAndDocs/` is deliberate: a
corpus-local conversion table escapes the repo-wide symbol sweep, which is
what POL-056 exists to prevent.

## Maintainer rulings, and what happens when the code catches up

Most of what this corpus does is a rule that applies everywhere and is tested.
Where a rule cannot reach, the maintainer's ruling is recorded as data and the
build consults it. Three files, in the order the build reads them:

| file | what it holds |
|---|---|
| `CodeAndDocs/curated-readings.json` | readings the rules cannot derive, keyed by the **printed Thao** exactly as it appears. `readings()` checks this first, so a curated record bypasses every rule. |
| `CodeAndDocs/settled-readings.json` | rulings that **used** to be curated and no longer need to be, because a later rule derives them. Nothing reads this at build time. |
| `CodeAndDocs/entry-rulings.json` | findings the maintainer has ruled are facts about the printed book, so `validate_entries.py` stops reporting them. |

### Why `settled-readings.json` exists

A curated reading is a decision somebody made about a page. When a new rule
starts deriving that same reading from the page itself, the curation becomes
dead weight — it makes the list longer for anyone trying to follow what the
build does, without changing anything. So it comes out of
`curated-readings.json`.

But the decision does not stop being true when the code that honours it changes.
It moves to `settled-readings.json`, where it goes on being **checked** instead
of applied. Two tests in `CodeAndDocs/test_entry_xml.py` keep the two files
honest:

- **`test_no_curated_reading_is_superfluous`** runs each curated entry with and
  without its curation. If the outcome is the same, the rules have caught up and
  the entry belongs in `settled-readings.json`. The test names it.
- **`test_settled_readings_still_hold`** asks the build to produce each retired
  ruling *without* consulting the file. If one no longer matches, the rule that
  replaced the curation has regressed.

### What to do when a test fires

**`test_no_curated_reading_is_superfluous` names an entry.** A rule now covers
it. Cut the entry out of `curated-readings.json` and paste it into
`settled-readings.json` with two extra fields — `retired` (the date and which
rule made it unnecessary) and `maintainer` (the words the ruling was given in,
so the reason survives). Re-run the tests.

**`test_settled_readings_still_hold` names an entry.** Something in this round's
changes stopped reproducing a ruling that used to hold. This is the point of the
file: decide which it is.

- *The new behaviour is wrong.* Fix the rule. The ruling was right and the test
  has just earned its keep.
- *The new behaviour is right and the old ruling is superseded.* Say so
  explicitly — POL-050 — and update the `readings` in `settled-readings.json`
  with a note saying what superseded it and when.
- *The rule can no longer reach it at all.* Move the entry back to
  `curated-readings.json`. That is not a defeat; it is the file doing its job.

Never delete an entry from `settled-readings.json` to make a test pass. The
whole value of the file is that a ruling given once is never silently dropped.

## Notes and Issues

**[Uncertain decisions](CodeAndDocs/uncertain-decisions.md)** lists the readings
that are defensible but not certain — where a judgement was made rather than a
fact recorded. Everything else in this corpus is either mechanical (a rule that
applies everywhere and is tested) or ruled (recorded with the maintainer's own
words in `CodeAndDocs/entry-rulings.json` and `CodeAndDocs/curated-readings.json`).


Audited 2026-09-10 against the locked source
(`claudeplans/audit-Blust-Thao-Dictionary.md` in FormosanBank). The extraction
reproduces byte-for-byte from the PDF, 16 of 14,044 Thao runs on the printed
pages are unaccounted for (0.11%), no extracted record is absent from the page
it claims, and every one of the 2,531 interlinear word forms was verified
against its page. Zero HARD validator findings.

Known limitations, all open:

- **Segmentation in the standard tier.** Blust prints morpheme boundaries in the
  dictionary examples (31% of tokens) and not in the five interlinear texts.
  Those hyphens are carried into the standard tier, so the corpus tokenizes
  unlike every other Thao corpus in FormosanBank. Ortho113 reserves the hyphen
  for syllable division inside loanword transliterations, and none of Blust's
  16,644 hyphens is one; stripping them awaits an attestation-driven rule in
  the shared cleaner.
- **`Tongpú`.** The `g` -> `ng` conversion rewrites the `g` inside the existing
  digraph `ng`, so this Sinitic place name becomes `Tonngpu` in the standard
  tier of `blust-text-t05-s065`, `-s067`, `blust-ex-p1024-e008` and
  `-p1038-e004`, with standard PHON `t*nŋpu`. Left as found: loanwords are not
  standardization's business, and the alternative was a bank-wide rule change.
- **Quotation marks.** Blust's quotations sometimes run past the sentence the
  text was split at, so eight sentences carry an unpaired mark
  (`blust-ex-p0772-e005`, `-p0804-e019`, `-p1018-e013`, `blust-text-t05-s033`,
  `-s049`, `-s097` open without closing; `blust-text-t05-s018`, `-s051` close
  without opening). Separately, 22 English translations begin mid-quotation
  because the opening glyph is absent from the PDF's text layer -- the closing
  mark is printed and extracted, the opening one produces no span at all.
- **Slash alternatives.** The 92 slash-bearing records are expanded from a
  hand-curated scope file. Eight of those scopes were wrong — they gave shared
  material to only one reading — and were corrected on the maintainer's ruling
  of 2026-09-10: `blust-ex-p0446-e019`, `-p0727-e001`, `-p0848-e005`,
  `-p0881-e009`, `-p0924-e006`, `-p0925-e005`, `-p0996-e003`, `-p1027-e009`.
  `CodeAndDocs/test_expansion.py::test_maintainer_ruled_slash_scopes` holds all
  eight, and FormosanBank's
  `tests/utilities/test_slash_alternative_rulings.py` asserts that
  `QC/utilities/slash_alternatives.py` reproduces each of them from the printed
  source without consulting the curation file at all.

  `slash_alternatives.py audit-curation` still reports eight scopes and twelve
  translations. The eight are cases where Blust prints two complete alternative
  sentences that genuinely differ in length (`q-m-usaz iza` / `q-m-usaz a
  qali`), which the rule cannot distinguish from a mis-split and reports as a
  superset — read eight rather than ninety-two. The twelve are records whose
  readings still share one translation that itself contains a slash, which
  remains open.
- **One translation is spliced with text from a later page.**
  `blust-ex-p0399-e015` ends `... her husband shau-na-hazish as`. It is the
  only one left: every other translation's last six words are on the page its
  record claims. (`blust-ex-p0290-e012` was the other, and was a symptom of
  the printed p. 291 problem, now fixed.)
- **Printed p. 291 is typeset in a different family** — Book Antiqua with
  Courier hyphens, not the Type 3 faces the rest of the book uses.
  `extract_source.py` classifies purely by font, so the page was invisible: its
  fourteen examples were all unextracted, and the record open when the page
  began survived across it and absorbed text from printed p. 292.
  `FONT_ALIASES` maps the family onto the roles the rest of the book uses, and
  the extractor now refuses to run past a dictionary page that carries text in
  no font it recognises.
- **Parentheticals in the English translations** are decided by
  `QC/utilities/parentheticals.py`, not by this corpus. A parenthetical that
  *pairs* with one in the Thao — the two sides carry the same number, so they
  are about the same thing — belongs to the example and is expanded in step
  with it. One that opens with an editorial marker (`lit.`, `answer to`,
  `said`, `viz.`, `e.g.`) or, having no counterpart in the Thao, runs to six
  words or more, is the author writing *about* the example and moves to
  `TRANSL/@notes`: **484 translations carry one** (170 literal paraphrases, 314
  other source notes). Everything else stays inline, which POL-024 requires for
  supplied words (`(and)`, `(it)`) and short naturalistic elaboration:
  **1,642 translations keep a parenthesis**. A bare grammatical label such as
  `(pl.)` or `(incl.)` is deliberately kept inline — it is attached to a
  pronoun, and "We (incl.) are early" loses its sense without it.

- **Twenty-eight expansions now split their translation in step.** Where the
  Thao carries an optional `(x)` and the translation carries exactly one
  parenthetical too, POL-026's two S blocks each take their own English:
  `yaku m-agqaqili sa azazak (sa pagka)` / `I was carrying a child (a chair) on
  my hip` gives an out-variant that no longer says "a chair". The other 151
  optional records have no translation parenthetical to split, so both readings
  correctly share one English.

- **The dictionary entries carry Blust's morpheme boundaries, and the
  interlinear texts carry word glosses.** The five texts have a TRANSL on 2,517
  of their 2,542 W; the 16,000-odd dictionary sentences are segmented into W and
  M but glossed only as wholes, because that is how the book glosses them. A
  tool that expects a gloss on every W will find most of this corpus empty at
  that tier.

- **Bound roots and the optional `(don't)` are not published.** Blust writes
  `(don't) give it` to tell the reader a bound form takes either polarity; it is
  notation, not a translation, and the 395 senses whose whole gloss was that are
  omitted, along with the 34 senses that are themselves a root printed in bars.
  A bar-marked header that is its own entry's only sense is a word the book
  decorated oddly rather than a bound root, and those nine are kept
  (`|Rariku|`, the lineage names `|Lhqapamumu|`, `|Lhqatafatu|`,
  `|Lhqashna'wanan|`, and five more).

- **62 pairs share a FORM and differ in gloss**, and every one has been read and
  ruled a genuine homophone — Blust's `a` the future marker beside `a` the
  linking particle. `validate_duplicate_sentences` reports them SOFT by design.
  The verdicts are in `CodeAndDocs/same-form-rulings.json` with the words they
  were given with.

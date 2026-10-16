# Seediq-Chang-Reference-Grammar

**Basecamp card:** [6922277585](https://app.basecamp.com/3340659/buckets/31258415/card_tables/cards/6922277585)

**Primary language:** Seediq (`trv`), Tegudaya dialect (the book's 霧社方言; see Notes and Issues)

**Status:** Audited 2026-10-16; see "Audit history" below

**Where it lives:** published in FormosanBank as `Corpora/Seediq-Chang-Reference-Grammar`;
developed in the private repository `Formosan-Seediq-Chang-Reference-Grammar`. The
two hold the same build code, and the build runs unchanged in either place.

**Created:** 2026-06-28 · **Last rebuilt:** 2026-10-16 (see `CodeAndDocs/provenance.json`)

## Source

Chang, Yung-li 張永利. 2000. 賽德克語參考語法 [Seediq Reference Grammar].
Yuan-Liou Publishing 遠流出版事業股份有限公司.

The author romanizes his name in **Wade-Giles**: *Chang Yung-li*. This repository
uses Chang everywhere: the corpus name, `TEXT/@id`, the XML filename, `@citation`,
`@BibTeX_citation`, `@source` and the documentation.

The 208-page primary scan and 105-page secondary scan came from the same Basecamp
card. They are kept in the private development repository (Git-ignored `Private/`)
and are not required for a build. Their hashes and page counts are recorded in
`CodeAndDocs/source_alignment_audit.md`.

## Rights

**License:** CC BY-NC 4.0

**Rights source:** Chang Yung-li 張永利, 2024-01-07; evidence: ask maintainer

Prof. Chang granted permission on 7 January 2024 to include the Formosan text,
translations and glosses under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).
Attribution and the original citation must be retained; the grant is
non-commercial. `TEXT/@copyright` carries the bare vocabulary value
`CC BY-NC 4.0` and nothing else, per POL-042 — the grantor, the date and this
evidence pointer belong here, not in the attribute.

## Corpus

### Scope: chapters 3 and 4 only

**The corpus covers printed pp. 54–148 — chapters 3 and 4 — and no more.** The
reviewed inventory was built for those chapters (see
`finalize_source_inventory.py`), and two later chapters of the book are **not
represented at all**:

| Printed | PDF | Chapter | Status |
|---|---|---|---|
| 39–53 | 55–69 | 1 導論, 2 (phonology) | prose, no interlinear examples |
| 54–148 | 70–164 | **3 構詞結構, 4 (syntax)** | **in the corpus** |
| 151–159 | 167–175 | **5 賽德克語的長篇語料** (long texts) | **extracted 2026-09-11** |
| 161–183 | 177–199 | **6 賽德克語的基本詞彙表** (basic vocabulary) | **not extracted** |
| 184–192 | 200–208 | 術語解釋, index, colophon | not corpus data |

Chapter 5 **has since been extracted** — see "The chapter 5 narrative" below. It
was missed for two compounding reasons, neither of which any check would have
caught: the inventory's page range stops at PDF 164, so chapter 5 was never in
scope; and the extraction is **marker-driven** — all 353 chapter 3–4 rows carry a
numbered marker (`1.`, `a.`, `7a.`) — while the narrative has no example numbers
at all, so a marker-keyed pass finds nothing there even when pointed at it.

Chapter 6 remains unextracted by decision (maintainer, 2026-09-11).

### The chapter 5 narrative

`XML/Seediq/chang-2000-seediq-long-texts.xml` — **37 S / 269 W / 319 M**, the
`sumuladuc` 祭祀 ritual account told by 傅景賢 (walis wadan) and retold by 錢成鏡
(pawan torih). It is the only running text in the book; everything else published
here is elicited example sentences, so sentence order is narrative order and
carries meaning.

**Transcribed from the page images at 300 dpi, not from the text layer**, by a
Claude session (commit `cbcffea`, 2026-09-11), and checked against the book in the
2026-10 student review (38 of its 39 chapter 5 cards marked reviewed; the 39th,
C5-009, she asked to fold into C5-008, which the bracket rule now does). The
scan's text layer is far more garbled in this chapter (`m “ usa s叫m.圖umalu`,
`A孔阻止風`, `祭把` for 祭祀) and — more dangerously — it collapses the column
spacing that carries the gloss alignment, which is exactly what produced the
shifted-gloss defects in chapters 3–4. The transcription is the data file
`CodeAndDocs/chapter5_transcription.tsv`, one row per printed block (Seediq line,
gloss line, translation, how the gloss bracket is printed, note);
`CodeAndDocs/transcribe_chapter5.py` reads it and emits `chapter5_inventory.tsv`. **That makes
the chapter 5 chain fully reproducible from a clean clone**, unlike chapters 3–4,
whose inventory came from an Apple Vision pass that is not in this repository.

Of the 40 transcribed blocks, 37 are published. The story title `sumuladuc` /
祭祀 carries a gloss but no free translation and is excluded, as chapters 3–4
exclude such blocks; two blocks continue the gloss bracket of the block before
them and are merged into it (C5-009 into C5-008, C5-030 into C5-029). Two footnote superscripts (15 on `sa-an-daha`, 16 on `pizu`)
are not part of the words and do not appear in any FORM — the audit asserts that
no chapter 5 FORM contains a digit at all.

Two things worth knowing about the text. `pizu` carries a `z`, which is not an
Ortho113 Seediq letter — the source's own footnote 16 explains it as a Mandarin
loan (`pizu為漢音字'譬如'`), so the detector flagging it is correct and no repair
is wanted. And `tanah tunux` 'red head' is the narrator's idiom for the Japanese
period, which the free translation renders as 日本時代.

### What is in the corpus

The checked-in `CodeAndDocs/source_inventory.tsv` is a complete reviewed inventory
of the 353 marked source blocks **in chapters 3–4**. It records an explicit
decision for every block:

- 273 source examples included
- 80 blocks excluded with exact reasons (47 ungrammatical, 27 not an interlinear
  example, 5 marginal, 1 with no source translation)
- 366 grammatical variants after expanding source options
- 15 of those variants are an exact repeat of an earlier one and are merged
  (POL-022), leaving **351 S / 1,464 W / 1,966 M** in canonical `XML/Seediq/`

Leading ungrammatical or marginal examples are excluded. Grammatical slash
alternatives and optional material are expanded. The source's parenthetical 用狗
reading is retained as an alternate translation.

**Starred parentheses are directional** (POL-017): `*(X)` marks X *obligatory*, so
X is published without its star; `(*X)` marks X *forbidden*, so X is dropped. The
two are not interchangeable — handling them alike is what published R173 and R174
as the starred string `tena m-ekan ido ka yaku`.

**Coindexation subscripts are dropped at intake and recorded nowhere.** The
source uses a subscript `ᵢ` to tie a bound pronoun to its antecedent. That is the
linguist's apparatus rather than Seediq spelling — the same class of thing as the
focus labels (受事焦點) this build also leaves out, and like them it is
recoverable from the morphosyntactic gloss. Keeping it made `yaku` and `yakuᵢ`
distinct tokens in every count and attestation dictionary, and forced
`add_phonology` to emit its unmapped-letter marker `*` (POL-003).

**Alternation scope.** A slash alternates one word with one word:
`laqi/heya`, `ini/uxe`. Chang braces the alternation when its scope is *wider*
than one word — `{laqi gaga/temi}` alternates `laqi gaga` 'that child' with
`temi`, not `gaga` with `temi`. The slash is the pivot: everything to its left
inside the braces belongs to the first reading, everything to its right to the
second. `brace_alternation()` raises rather than guesses on any shape it cannot
read, because the book contains exactly one braced example and a second one
deserves a human's eye. Where the parentheses enclose a starred alternation —
`(saya/*ciga/*kusun)`, `(kusun/*ciga)` — they only mark the scope of the
alternatives; the one surviving reading is obligatory, not optional, and yields a
single sentence.

**Optional whole words split the sentence** (POL-028). `x y (z)` changes the
sentence's word inventory and the gloss alignment, so it becomes two `S` blocks:
53 records are of this shape, each giving a pair. The split is made on the
**original** tier, so `standardize.py` derives each reading's standard tier from
its own original. Ids follow POL-028 — one base id per source record, further
readings taking `-opt`, then `-opt3`, `-opt4`; there is deliberately no `-opt2`.
The base id is the record's own id (`R275`, `R275-opt`; chapter 5 `C5-002`), so
neither adding a record nor adding a reading renumbers anything else (POL-037,
ruled 2026-10-16).

**Optional material inside a word splits the sentence too**, because it changes
the word's morpheme segmentation (POL-028 as amended 2026-10-15). R275 prints
`h-(um)-uwa`: the bare reading `huwa` (怎樣) is one M, `h-um-uwa` (怎樣-AF) is
two, so they are separate `S` blocks, bare first as for `(ka)`.
`optional_morpheme_options()` drops the optional morpheme's gloss from the bare
reading by finding it among the full reading's M, and raises when optional
letters are not a whole morpheme, since those would be a variant instead.
Combined with that record's `kes-un/m-esa`, R275 gives four sentences
(`R275` … `R275-opt4`), all with the one printed translation.

**Two readings of one word are a variant, not two sentences** (POL-028). The
book's `da/di` (起始貌, R181–R185, printed p. 104) gives one S each: `da` is
the base and `di` a `FORM kindOf="original" ver="alt"` on the S, the W and the
M, and `standardize.py` derives the standard-tier variant from it. Which slashes
are variants is a ruling about the source, kept per record in
`CodeAndDocs/word_variants.tsv`; every other slash gives one S per option
(POL-027).

**Each distinct sentence is published once.** Chang reuses examples across
chapters, so the same sentence arrives from several source records. The first is
kept; every merged record's locator rides along in that sentence's `S/@source`,
so nothing about provenance is lost; and where a merged copy carried a different
Mandarin rendering — an aspect 了, a progressive 在, a cleft 是 — that rendering
is kept as a `TRANSL[@ver="alt"]`. All 15 merges are listed in
`CodeAndDocs/deduplicated_variants.tsv` with what differed (POL-051).

## Notes and Issues

- **Dialect.** The book says it describes the 霧社方言 (Wushe dialect), spoken in
  南豐 and 互助 villages, with consultants from 互助村 (printed p. 37: 本文研究的是霧社方言).
  FormosanBank tags this dialect `Tegudaya` (德固達雅; also called Tgdaya, Paran, 霧社).
  The book also thanks a speaker of the 春陽 dialect, Pastor 張秋雄 (walis ukan), for
  "許多寶貴的意見" (p. 38). FormosanBank's dialect detector agrees: Tegudaya, p = 0.96
  (grammar file) and 0.94 (chapter 5).
- **Orthography.** The major Seediq writing systems (Church, ILRDF 94, ILRDF 113) are
  identical. Chang (2000) predates even ILRDF 94, but we treat the original tier as
  113 for convenience. Note that the writing here differs from our other Seediq
  sources in a few systematic ways: some words are written with vowels that the
  other corpora leave out (`munekan`, elsewhere `mnekan`), and pronouns are
  hyphenated onto the preceding word (`sapah-mu`, elsewhere `sapah mu`). The
  significance of this is not currently clear.
- **One W per printed gloss (POL-060).** Where the book prints one gloss under two
  words, the two are a single W: `ani naq` 雖然, `ani sa` 但是, `kiya ka` 所以,
  `ado ka` 如果, `bobo na` 之後, `di ge` 的時候, `daha ka` 跟, `asi ka` 應該/一定,
  `saya ali` 今天, `uka ka` 沒有, `cubeyo hayan` 從前. Seven of these the book names
  as single connectives in its own prose (printed pp. 138–146); the other four
  follow the gloss's position on the page. These sentences have fewer W than
  words, which V060 reports as SOFT by design.
- **A pronoun inside such a pair is written as an infix.** The book prints
  `ani-ku naq`, `ado-su ka` and `ado-ku ka`, with the pronoun between the two
  words of the connective. The W is `ani<ku>naq` glossed `雖然<我>` (likewise
  `ado<su>ka` 如果<你>, `ado<ku>ka` 如果<我>), split into M per POL-014. The
  sentence-level FORM keeps the printed `ani-ku naq`, but the W's PHON runs the
  words together (`anikunaq`). Each such W says so in its gloss's `notes`.
- **Infixed words are written with angle brackets at the word tier (POL-014),
  but the sentences keep the book's hyphens.** Where the book glosses a root
  interrupted by an infix, e.g. `b-n-eebu` 打-完成貌, the word is `b<n>eebu`
  glossed `打<完成貌>`, and its morphemes are the root `b-eebu` 打 and the infix
  `-n-` 完成貌 (61 words, ruled 2026-10-15). Where the book instead glosses each
  hyphen piece, e.g. `m-un-ekan` AF-完成貌-吃, the word follows the book: three
  morphemes in a row, `m` AF + `un` 完成貌 + `ekan` 吃, and the printed gloss (18
  words: `m-un-ekan`, `m-un-ekan-ku`, `m-un-usa`, `m-un-eyah`, `m-un-eyah-su`,
  `k-um-ubunux`; ruled 2026-10-15).
- **Morpheme FORMs carry no punctuation.** Quote marks, full-width punctuation and
  ASCII `.,;:?!` are removed from morphemes; words and sentences keep theirs as
  printed (ruled 2026-10-15).
- **`laqi/sapah-mu` (R070) is read as `laqi-mu` / `sapah-mu`**: the book prints the
  `-mu` (我的) once, on the second alternative, and it belongs to both (ruled
  2026-10-16; `slash_scope.tsv`).
- **`?` is a word the book leaves unglossed (POL-061)**, e.g. the question
  particle `yee`, `lux` in `h-um-uwa-su lux`, sentence-initial `soka`.
- **Where the published text corrects the book itself.** Everywhere else the
  original tier follows the printed page: OCR and scrape errors were corrected
  *toward* the print, in Hunter's scan review and in the 2026-10 student review,
  whose every edit was checked against the scan. These are the only places where
  what we publish departs from what the book prints. Each was ruled by the
  maintainer (2026-10-14/15) and carries a `notes` attribute on the element it
  changes:

  | Book (printed page, example) | Book prints | Published | Why |
  |---|---|---|---|
  | p. 83, 2b | `mah-un` glossed 吃-PF | 喝-PF | the object is 水 'water'; a dictionary gives 喝 |
  | pp. 119–120, 11b | 用-AF--我 | 用-AF-我 | the double hyphen is a typo |
  | p. 140, 17a | `musa meepah` | `m-usa m-eepah` | hyphenated as in the book's other examples |
  | p. 145, 25b | no translation | the translation of 23b/24b | the parallel examples |
  | p. 147, 28a | `m-aha-ku` glossed AF-去-你 | AF-去-我 | `-ku` is first person, as in 29a–c |
  | p. 147, 28a | `turima` glossed 洗 | 洗（AF） | to match 29a–c |
  | pp. 147–148, 29a–c | `m-aha-ku` glossed AF-去-你 | AF-去-我 | `-ku` is first person |
  | p. 108, 5 | one gloss, AF-在, under `m-enaq/gaga` | the `gaga` reading glossed 在 | the AF belongs to the `m-` of `m-enaq`; the book glosses bare `gaga` 在 in 6b |

- **A known printing error is left as printed:** the translation of 1c (p. 78,
  `yaku-naq (ka) pure ido`) reads 煮飯的的人是我自己, with 的 doubled; its `notes`
  says so.
- **Square and lenticular brackets are removed** from the Seediq and the
  translations (the book uses them for an embedded clause or for emphasis; each
  affected sentence's FORM `notes` records what was bracketed). **Parentheses are
  standardized**: full-width in Chinese, ASCII in Seediq. **Translations carry no
  spaces beside a Latin name** (`我相信pawan會打敗walis的。`), though the book sets
  one; a space between two Latin words stays (`Awi Tone`).
- **`da/di` is published as `da` with `di` as a variant FORM** (`ver="alt"`),
  not as two sentences: both are glossed 起始貌 under one translation.
- **`h-(um)-uwa` (R275) is published both ways**, `huwa` and `h-um-uwa`, as
  separate sentences, because the optional infix changes the W/M tier.
- **Notes from the 2026-10 student review** are in `notes` attributes, attributed
  to the source the reviewer named (the book, a dictionary, the ILRDF online
  grammar) or otherwise to the review.

## Reproduce and validate

```bash
# THE entry point: source -> XML/. Build only, no validators (POL-047).
CodeAndDocs/generate_xml.sh

# Validation, separately. Reads XML/, never writes it.
CodeAndDocs/validate.sh

# Both, twice, with a byte-comparison between the passes.
CodeAndDocs/reproduce.sh
```

Run from this corpus's folder. The scripts find FormosanBank themselves
(`CodeAndDocs/formosanbank_path.sh`): two levels up when this is the published copy
under `Corpora/`, a sibling `../FormosanBank` in the development repository, or
wherever `FORMOSANBANK_PATH=/path/to/FormosanBank` says. When the corpus is inside
the FormosanBank checkout, the read-only check below leaves the corpus's own folder
out, since that folder is what the build writes.

The two are separate because a build that aborts on a validator failure cannot be
used to investigate that failure — you need the XML the validator objected to.

The two-pass gate rebuilds from `source_inventory.tsv`, runs the complete current
QC pipeline, and compares deterministic outputs. It runs against **whatever
FormosanBank checkout it is pointed at** — the build is never pinned to an old
commit (POL-047). The FormosanBank dependency is treated as read-only: the runner
records its commit before and after each pass and refuses to report success if the
run changed it.

The commit whose tools built the XML currently under `XML/` is recorded in
[`CodeAndDocs/provenance.json`](CodeAndDocs/provenance.json) (POL-052). Rewrite
that file on every rebuild.

Key files:

- `CodeAndDocs/finalize_source_inventory.py`: records scan corrections and
  decisions for all 353 source blocks. **Note:** it takes the Apple Vision OCR
  geometry inventory as its argument, and that file is not tracked — so this step
  cannot be re-run from a clean clone. `source_inventory.tsv` is the earliest
  redistributable authoritative layer. Both OCR text layers are kept in the private
  development repository and are not published: the recorded permission covers the
  Formosan text, translations and glosses, not the book's prose. Its scan-review decisions are data files it
  loads (POL-039): `inventory_overrides.tsv` (115 records whose form, gloss,
  word alignment, translation or marker were replaced from the scan),
  `inventory_not_examples.tsv` (27 blocks that are not interlinear examples) and
  `ocr_form_fixes.tsv` (12 OCR misreadings, applied in file order).
- `CodeAndDocs/build_xml.py`: expands the reviewed inventory and builds canonical XML.
  Its data tables are `translation_readings.tsv` (hand-written translations for
  records whose printed translation covers more than one reading, each with the
  reason), `shared_gloss_pairs.tsv` (the POL-060 word pairs that share one
  gloss, each with the evidence), `word_variants.tsv` (slashes ruled to be two
  readings of one word) `reading_glosses.tsv` (a gloss printed once under a
  slash pair, given per reading) and `slash_scope.tsv` (a suffix printed once
  that belongs to every alternative of a slash)
- `CodeAndDocs/audit_source_alignment.py`: verifies full inventory and XML
  alignment, and — when the Git-ignored `Private/` scans are present — their
  SHA-256 and page counts. Page counting prefers `pdfinfo` but falls back to
  `pdfplumber` (pinned in FormosanBank's `requirements.txt`), so poppler is not
  a build requirement.
- `CodeAndDocs/deduplicated_variants.tsv`: generated; every merged duplicate and
  what differed about it
- R053's alternation-scope braces (`{laqi gaga/temi}`), which an older
  `clean_form()` deleted, were put back into the committed inventory by a one-off
  script in commit `4899d43`; the script was deleted on 2026-10-15 (maintainer's
  call; git history keeps it). The current `clean_form()` keeps braces.
- `CodeAndDocs/generate_xml.sh`: **the** entry point — source to published XML/
- `CodeAndDocs/validate.sh`: every validator, plus the adjudication gate
- `CodeAndDocs/adjudicate_findings.py`: requires zero HARD findings and dispositions every diagnostic
- `CodeAndDocs/reproduce.sh`: performs the deterministic two-pass clean-clone gate

### Review round trip

The Seediq words, their glosses and the free translations were all read off
printed pages, so all three can carry transcription errors: misread characters
in the Chinese, misread Seediq letters, and gloss columns that slipped by one,
which is invisible in the finished XML. A reviewer checks them against the book
in a web page, and three scripts carry the corrections back reproducibly:

```bash
python CodeAndDocs/export_review.py      # -> review_baseline.json + review_page.html
#   ... review_page.html is published as a claude.ai artifact; the reviewer works there ...
python CodeAndDocs/apply_review.py <downloaded.json | dumped edits/ directory>
                                         # -> review_corrections.tsv + review_log.tsv
FORMOSANBANK_PATH=... CodeAndDocs/generate_xml.sh   # publishes the corrections
```

The page shows **one card per source record**: the Seediq words in one row, the
gloss for each word beneath it, then the free translation. It is a record rather
than a sentence because a record with optional material expands into several
sentences that share one word list, and the word positions differ between them.
The reviewer can edit any word, gloss or translation, insert and delete boxes in
either row to realign glosses, leave a note, and mark the card reviewed. The page
saves to the artifact's own database when the viewer may write there (the owner,
or someone invited by email as an Editor), and otherwise to the viewer's browser,
with a download file that doubles as a save file and as the thing to send back.
`review_page.html` is generated from `review_page.template.html` with the baseline
embedded, so the page cannot show different text from what `apply_review.py`
compares against.

`apply_review.py` writes `review_corrections.tsv`, one row per changed field
(`words`, `glosses` or `translation`, space-joined, with `was` and `now`), and
`review_log.tsv`, one row per record the reviewer touched, including cards marked
reviewed with nothing changed and notes that are questions rather than fixes.
`build_xml.py` applies the corrections over both inventories before anything
else, so the sentence FORM, W and M tiers are all re-derived from the corrected
row. They are deliberately not written back into the inventories: those record
what the transcription pass read, and keeping "what we first read" separate from
"what review corrected" is the same reasoning that puts hand edits in
`manual_edits.xml` rather than in the published XML. Guards: an edit made against
a different baseline is refused; a correction whose `was` no longer matches the
inventory fails the build as stale; one matching no record fails the build; a
row left with unequal word and gloss counts fails. The 23 records whose published
translations are written out by hand in `translations_for()` refuse a translation
correction (the page makes their translation read-only and asks for a note).

Cards carry triage flags, so a reviewer with limited time knows where to start:
`latin_gloss`, `unbalanced`, `substring`, `adjacent` (two neighbouring glosses
that join into a word used elsewhere, which is the sharpest test), and `count`.

### Why dedup is corpus-local (POL-046)

`QC/cleaning/remove_duplicate_sentences.py` **deletes** a duplicate `S`; it keeps
the first by id order and drops the rest. As of 2026-09-11 it deletes only where
the FORM *and* every TRANSL match, leaving the differing case for a human to
resolve as `ver="alt"` (POL-025). This corpus needs that resolution, not a
deletion: 10 of its 15 duplicate pairs carry a *different* Mandarin rendering of
the same sentence, and every pair has a second source locator worth keeping. So
`build_xml.deduplicate()` merges rather than deletes — carrying the locators into
`S/@source` and the differing renderings into `TRANSL[@ver="alt"]` — and the
shared tool then finds nothing left to remove. Folding the merge behaviour into
the shared tool would be the better long-term answer and belongs in its own
`QC/` pull request (POL-049).

### Deviations from POL-047 (stated, per the policy)

- The initial parser is named `build_xml.py` rather than `generate_xml.py`, and a
  second corpus-local step, `transcribe_chapter5.py`, runs before it — the
  narrative's transcription is its own source layer. Both are initial parsing,
  POL-046's standing exception.
- `clean_xml.py` used to run twice, before and after `standardize.py`. The second
  call is gone: it was a structural no-op, because `clean_xml` excludes
  `FORM[@kindOf="standard"]` and every text-writing line in `standardize.py`
  targets exactly that tier, so their write-sets are disjoint.
- `standardize.py` is passed `--hard-remove-segmentation`, which is the
  Bunun/Thao "hyphen is a letter" escape and does nothing for Seediq — verified
  by building with and without it. Harmless, and still worth removing.

## Audit history

Findings from the 2026-09-11 dev-repo audit, with their status:

- **Shifted gloss columns: FIXED by the 2026-10 review** (checked 2026-10-15:
  `R312` `daha ka`=跟, `walis`=walis; `R315` `bobo na`=然後; `R323` and
  `R323-opt` `rudan,`=老人). As first reported: from `normalize_pairs()` zipping gloss
  whitespace-chunks to form words whenever the counts happen to match. A
  multi-word gloss printed over a span gets sliced word-by-word:

  | sentence | record | published | should be |
  |---|---|---|---|
  | `R312` | R312 | `ka`=`w`, `walis`=`alis` | `daha ka` is one gloss 跟, so `ka`=∅ and `walis`=`walis` |
  | `R315` | R315 | `bobo`=然, `na`=後 | 然後 is one word |
  | `R323` | R323 | `naq`=老, `rudan`=人 | 老人 is one word |
  | `R323-opt` | R323 | same | same |

  A fifth, 雖然 split across `ani`/`naq` in R321, is **gone**: dedup merged R321
  into R320 and the defective copy was the one dropped.
- ~~**32 gloss elements across 11 sentences** carry a stray parenthesis taken from a
  neighbour's gloss.~~ **FIXED:** 0 W glosses have unbalanced parentheses as of
  2026-10-15.
- The source's focus labels (受事焦點 / 處所焦點 / 參考焦點) are dropped from the
  FORM and not recorded. **Settled 2026-09-11:** that is fine — the focus is
  already carried by the morphosyntactic gloss (`-un` PF, `-an` LF, `s-`/`su-` RF),
  so nothing is lost.
- ~~Render infix glosses inline, and reconcile `maha-ku`~~ — **both closed
  2026-09-11.** Infix glosses are now written inline (`AF<完成貌>-吃` then; since 2026-10-15 `打<完成貌>`, see Notes and Issues), taking
  V153 from 26 findings to 8.

  The `maha-ku` half was **withdrawn as a mistaken finding**. An earlier audit
  recommended making `maha-ku`/`musa-ku`/`mpuuyas-ku` consistent with the 26
  hyphenated spellings elsewhere. The scan says otherwise: printed p. 144 has
  `m-aha-ku` at 23b and `maha-ku` at 24b, and p. 145 has `m-usa-ku` at 26a and
  `musa-ku` at 26b — the same word, adjacent sub-examples of a single pair. The
  author is inconsistent; the transcription is faithful. Acting on the
  recommendation would have edited the corpus away from the printed page, which
  POL-001 forbids.
- ~~**POL-037:** base ids were positional across records~~ — **closed 2026-10-16.**
  Every sentence id is now its source record's id (`R275`, `R275-opt`, …; chapter 5
  `C5-002`, …), so adding, excluding or merging a record renumbers nothing else.
  All ids changed once, before publication.
- **Chapter 6 is not extracted** — the basic vocabulary list, by decision
  (maintainer, 2026-09-11). Chapter 5 is extracted; see "Scope" above.
- ~~POL-047 split~~ — **closed 2026-09-11.** `CodeAndDocs/generate_xml.sh` builds
  and runs no validator; `CodeAndDocs/validate.sh` validates and writes nothing
  under `XML/`. `run_qc_pipeline.sh` is gone.

No publication action has been taken.

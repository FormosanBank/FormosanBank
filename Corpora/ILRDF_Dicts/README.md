# ILRDF Dictionaries

Example sentences and headword entries for all sixteen Formosan languages,
drawn from the Council of Indigenous Peoples / Indigenous Languages Research
and Development Foundation online dictionary,
<https://e-dictionary.ilrdf.org.tw/>.

| | Sentences | Dictionaries |
|---|---:|---:|
| Files | 16 | 16 |
| `S` records | 167,241 | 139,097 |
| Translations | 169,364 | 164,359 |
| Audio links | 132,281 | — |
| Alternate spellings | 1,998 | — |

## Rights

**License:** CC BY-NC 4.0
**Rights source:** Indigenous Languages Research and Development Foundation, 2026-09-07; evidence: ask maintainer

The ILRDF copyright statement allows quotation for research and teaching
within a reasonable scope, with attribution, and requires permission beyond
that. This corpus is published under those terms, with attribution to the
Council of Indigenous Peoples and to ILRDF. See
[CodeAndDocs/source_data/RIGHTS.md](CodeAndDocs/source_data/RIGHTS.md) and the
source's own statement, linked there.

## What is in it

**Sentences** — one `<S>` per example sentence, with the source's Chinese
translation and, where the source has one, a link to its audio recording.

**Dictionaries** — `XML/<Language>/<Language>_dictionary.xml`, one `<S>` per
headword and one `<TRANSL>` per sense. A sense's part of speech rides on that
sense's `TRANSL/@notes`. There is no `W` or `M` tier: the source carries no
morphological analysis.

Sentence and entry ids carry the source's own GUID —
`Amis_20a69646-e70a-f011-bd65-00155db40116`, entries with a `d` before the
GUID. This means a published id survives our corrections to the text, which a
hash of the text would not, and it is what lets `manual_edits.xml` work at
all. See [CodeAndDocs/docs/id_scheme.md](CodeAndDocs/docs/id_scheme.md).

## Reproducing the XML

```bash
export FORMOSANBANK_AUTHORITY=/path/to/a/clean/FormosanBank/checkout
CodeAndDocs/make_xml.sh
```

That rebuilds everything from the committed snapshots in
`CodeAndDocs/source_data/snapshots/` and needs no network access. The
snapshots are the source boundary.

The build uses whatever shared QC tooling the authority checkout has, and
reports the commit and the resulting digest when it finishes.
`CodeAndDocs/docs/reproduction.md` records the pair that produced the
committed XML: same pin with a different digest means something has stopped
being reproducible.

**Full regeneration** re-scrapes the ILRDF API first:

```bash
CodeAndDocs/refresh_source.sh     # changes the source of truth
CodeAndDocs/make_xml.sh
python CodeAndDocs/generate_xml.py ledger --write   # then review the id diff
```

`refresh_source.sh` is deliberately not part of reproduction: it can add,
remove or reword source records, and each of those moves published ids.

## Changes we make to the source

Everything below is reproducible from committed code and data. Nothing was
edited by hand.

### Source-fidelity repairs — 15 records

The ILRDF API sometimes returns material that is not Formosan text. These are
corrected on the **original** tier through the repo's manual-edits mechanism
(POL-030), and every one is recorded in
[CodeAndDocs/manual_edits.xml](CodeAndDocs/manual_edits.xml) with a readable
changelog in [CodeAndDocs/manual_edits.md](CodeAndDocs/manual_edits.md). The
reviewed table behind them is
[CodeAndDocs/source_data/source_repairs.json](CodeAndDocs/source_data/source_repairs.json).

| Class | Records | Example |
|---|---:|---|
| Part-of-speech label standing in for a word | 6 | `u數詞u paapuhla…` → `ʉnʉmʉ paapuhla…` (數詞 = "numeral") |
| Chinese editorial text welded onto a sentence | 9 | `…mawtu zau.這` → `…mawtu zau.` |

### Recovered `?` corruption — 61 tokens

The source has lost the letter **ʉ** in places, leaving a literal `?`. Where
the intended word can be confirmed, it is restored automatically; where it
cannot, the `?` is left visible rather than guessed at.

The repair applies only to Kanakanavu, Saaroa and Tsou, and only to a `?`
with a Formosan letter on **both** sides — so a sentence-final question mark
is never touched (1,128 of those survive). The candidate must already occur,
intact, elsewhere in the same language's snapshot, in a sentence containing no
`?`, so a corruption cannot vouch for itself. Of 85 candidates, **61 were
repaired — every one to ʉ, none to ɨ** — with attestation counts from 2 to 54
(`cim?r?` → `cimʉrʉ`, attested 54 times). **24 were left unrepaired** for want
of an attested candidate.

### Source-side alternatives

The source packs alternative wordings into one record three ways: `=` ("same
as"), parentheses, and slashes. Two different things hide under that, and they
are treated differently:

- a **spelling variant** — the same utterance written differently, `hiya` /
  `hiyaʼ` — stays one record, with the other spellings carried as
  `FORM[@kindOf="alternate"]`. **1,998** of these.
- a **lexical alternative** — different wording, `tanux` /
  `(mnaw tay tanux)` — becomes separate `<S>` records.

A parenthesis is kept as written when it holds Chinese, a Japanese loanword in
Romaji (listed in
[CodeAndDocs/source_data/bracket_annotations.csv](CodeAndDocs/source_data/bracket_annotations.csv)),
a proper noun or a number — those are annotation, not alternation.

**2,049 records were resolved into 2,146.** Where the reading was not clear we
delete rather than guess: a phrase alternative that shares no word with the
term it replaces could substitute for any span, and options too dissimilar to
be one word spelled two ways might be either. **718 fragments were dropped on
those grounds, every one listed in
[CodeAndDocs/docs/split_report.csv](CodeAndDocs/docs/split_report.csv).**

Headword notation is left alone — `uculru(wa)` marks an optional ending, not
an annotation — so the dictionaries are as the source wrote them.

Each rewritten record keeps its source string in `FORM/@notes`, and records
split into several take a letter suffix on their id (`…_a`, `…_b`).

### Excluded content

- 820 all-zero audio ids, two confirmed transcript mismatches, and both uses
  of 40 audio ids assigned to different forms in different languages
  ([source_data/audio_exclusions.json](CodeAndDocs/source_data/audio_exclusions.json)).
- Three Kanakanavu lesson numbers that are not translations
  ([source_data/source_content_exclusions.json](CodeAndDocs/source_data/source_content_exclusions.json)).

## Code

| | |
|---|---|
| `refresh_source.py` / `.sh` | re-scrape the API into snapshots |
| `generate_xml.py` | sentences; also the `ledger` and `audit` modes |
| `generate_dictionary.py` | headword entries |
| `split_alternatives.py` | source-side alternatives |
| `build_manual_edits.py` | renders `manual_edits.xml` from the repair table |
| `make_xml.sh` | the reproduction pipeline |
| `tests/` | 70 tests; `python -m unittest discover -s CodeAndDocs/tests` |

Every derived tier is produced by the shared QC tools and by nothing else: the
standard `FORM` comes from `standardize.py`, `PHON` from `add_phonology.py`.
The corpus's own scripts emit source tiers only.

`source_data/published_ids.csv` is a lockfile of every published id.
`generate_xml.py audit` fails if an id disappears without being marked
suppressed, if the XML carries an id the ledger does not declare, or if an
id's source GUIDs change — which is how a correction that silently merged two
records would be caught.

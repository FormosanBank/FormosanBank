---
icon: layer-group
---

# orthography_detector.py

> Scores a corpus's text against the reference orthography tables to suggest which orthography it is written in — the input to the pipeline's human "what orthography is this?" decision.

## What it's for

Before a corpus can be transliterated to the standard tier, a human has to decide what orthography its source text actually uses. `orthography_detector.py` informs that judgment: it compares the letters appearing in the text against every reference orthography in `Orthographies/` and reports, ranked, which orthographies best explain the text. The maintainer reads the output and decides; the script does not change any data.

## How it works

It takes the XML path as a **positional argument** (there is no `--corpora_path`). By default it analyzes the **original** tier (`FORM[@kindOf="original"]`, sentence-level, falling back to word-level `W` forms); pass `--use-standard` to analyze the standard tier instead. Text is lightly cleaned (digits, commas, `!`, `"` removed) before scoring.

**Accents are stripped before the statistics are computed.** Most accents in a source text are prosody rather than spelling (for example Glosbe's stress-marked Truku `máduk`, `dálix`) — the plain vowel wearing a diacritic. The detector removes these marks (the combining acute, breve and macron — decompose to NFD, drop the marks, recompose) so an accented vowel is scored as its bare vowel: it counts toward coverage of the plain letter instead of being miscounted as an *unexpected* token that under-scores the true orthography. Without it, a stress-accented source like the Truku Glosbe data scores its own orthography far too low (in practice ~70% instead of ~97%).

**Letters the language actually spells with are kept.** Some accented letters are real graphemes — Puyuma's `ē`, Siraya's `ǣ`, Favorlang's `ḡ` — and folding them into their bare base would make the detector score a genuine letter as missing. So the detector passes a **keep set** built from the orthographies it is about to score the text against: an accent survives iff some orthography in that test set contains a letter carrying it. Letters whose language has no reference orthography at all are covered by `QC/utilities/_accents.ALWAYS_KEEP`, which is unioned into the keep set on every call. The same mechanism protects the standard tier in [standardize.py](standardize.md), which describes it in full.

This affects statistics only; no data is modified, and accents stay untouched in the corpus's original tier either way.

For the file's language (from `xml:lang`, mapped to a language name) it loads each orthography directory under `Orthographies/` (excluding `ConversionTables`) — e.g. `Church`, `MinEd`, `Ortho113` — building a letter inventory per orthography and dialect. Each candidate orthography gets a score combining:

- **coverage** — how many of the orthography's "common" letters actually appear, and
- **cleanliness** — penalized by the percentage of *unexpected* tokens (letters in the text but not in the orthography),

with a small bonus for the number of letters matched. Multi-letter graphemes (e.g. digraphs) defined by an orthography are matched as units. Results are ranked best-first; the top entry is the suggested orthography. For each candidate it also reports missing letters and the most frequent unexpected tokens.

Pointed at a **directory**, it analyzes every `*.xml` file and aggregates: file-by-file by default, or grouped/combined per dialect with `--combine`. `--ignore-dialect` tests all orthographies regardless of the XML's `dialect` tag (and, in directory mode, groups by the best-matching orthography dialect).

## Usage

Run from the FormosanBank repo root after `source .venv/bin/activate`.

```bash
# Single file (analyzes the original tier by default)
python QC/utilities/orthography_detector.py Corpora/<Corpus>/XML/<file>.xml

# A whole corpus, combining files by dialect into one dataset each
python QC/utilities/orthography_detector.py Corpora/<Corpus>/XML --combine

# Ignore dialect tags and test every orthography; or score the standard tier
python QC/utilities/orthography_detector.py Corpora/<Corpus>/XML --ignore-dialect
python QC/utilities/orthography_detector.py Corpora/<Corpus>/XML/<file>.xml --use-standard
```

| Flag | Default | Notes |
| --- | --- | --- |
| `input_path` (positional) | (required) | An XML file or a directory of XML files. |
| `--orthographies`, `-o` | `Orthographies/` (next to repo) | Reference orthographies directory. |
| `--ignore-dialect`, `-i` | off | Test all orthographies regardless of the XML `dialect` tag. |
| `--combine`, `-c` | off | Directory mode: merge files of the same dialect into one dataset. |
| `--use-standard`, `-s` | off | Analyze the standard tier instead of the original. |
| `--language`, `-l` | none | Only process files with this ISO 639-3 code. |

## Output & side effects

**Read-only** — prints a ranked report to stdout and writes nothing. For a single file it lists every orthography match (score, matched/common letters, unexpected percentage) and highlights the best match with its missing letters and top unexpected tokens. Directory mode adds per-dialect summaries and an overall best-match.

## When to run it

This is the **human-judgment step** of the pipeline: run it on the original tier *before* standardizing, read the ranking, and decide the source orthography (which then drives the transliteration TSV used by [standardize.py](standardize.md) and the source table used by [add_phonology.py](add-phonology.md)). See the [Running an Audit](../running-an-audit.md) and [Porting a Corpus In](../porting-a-corpus.md) workflows.

## Related

- [QC Pipeline overview](README.md)
- [standardize.py](standardize.md)
- [add_phonology.py](add-phonology.md)
- [orthography_extract.py](orthography-extract.md)
- [validate_orthography.py](validate-orthography.md)

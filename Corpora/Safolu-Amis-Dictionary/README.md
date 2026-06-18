# Safolu Amis Dictionary

## License and AI Use

This corpus is subject to its source license and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

The **Safolu (Tsai Chung-Han / 蔡中涵) Amis dictionary** from the g0v Amis Moedict
project, converted into valid FormosanBank XML.

| Field | Value |
| --- | --- |
| Type | Published FormosanBank corpus |
| Language | Amis (`ami`, glottocode `amis1246`) |
| Source | Safolu Kacaw Lalanges / 蔡中涵 dictionary, generated JSON in [g0v/amis-moedict](https://github.com/g0v/amis-moedict) `docs/s` (see https://amis.moedict.tw/) |
| Published XML | `XML/Amis/Safolu/amis_safolu_examples.xml` |
| Reproduction code | `CodeAndDocs/` (build scripts + `Makefile` + `SOURCE_AUDIT.md`) |

> **Reproduction note.** The build scripts and `Makefile` under `CodeAndDocs/`
> regenerate the XML from the upstream sources. They were authored in the
> `Formosan-Safolu-Amis-Dictionary` development repo and expect a sibling
> FormosanBank checkout for the shared QC tools (`FB=…`); when run from the
> published layout, point `make -C CodeAndDocs` at this checkout's tools
> (`FB=../../..`) and note that the build writes its working tree
> (`Final_XML/`, `_sources/`, `data/`) under `CodeAndDocs/`. The canonical,
> QC'd copy is the one committed under `XML/`.

> **Scope note.** This repository previously also built the Poinsot/Pourrias
> Amis–French dictionary (`docs/m`). That corpus needs OCR-correction work, so it
> was split into its own repository, **`Formosan-Poinsot-Amis-Dictionary`**, to avoid blocking
> publication of Safolu. Virginia Fey (`docs/p`) was processed separately and is
> out of scope here.

## Output

```sh
make -C CodeAndDocs formosanbank
```

The build:

1. Fetches the pinned upstream `g0v/amis-moedict` (`docs/s`) and `miaoski/amis-safolu` checkouts into `_sources/`.
2. Builds `Final_XML/Amis/Safolu/amis_safolu_examples.xml`.
3. Writes provenance + rejected-record audits under `data/formosanbank_audit/`.
4. Runs a structural validator and a source-coverage audit.

### Result

- `Final_XML/Amis/Safolu/amis_safolu_examples.xml`: **49,145** Amis sentences (49,400 extracted from 49,419 source fields, then 255 duplicate cross-lemma example sentences removed; the original naive parse kept 48,914).
- `data/formosanbank_audit/Safolu/*.metadata.json`: provenance for every sentence (incl. its `source_ordinal`).
- `data/formosanbank_audit/Safolu/*.rejected.json`: source fields that cannot be represented (**44**, down from 505).

Coverage is tracked at the **source-field** level (one field can expand into several sentences — see CJK splitting below): all **49,419** source example fields are accounted for — represented by ≥1 sentence or in the rejected audit.

### Recovery / repair of source rows

The Safolu source has 49,419 example fields delimited by `U+FFF9` (Amis form), `U+FFFA` (middle), `U+FFFB` (final Chinese translation). Malformed rows are recovered/repaired rather than dropped:

- **187** rows recover the Amis from the start of the Chinese field (`recovered_form_from_translation`). A leading loanword annotation — `〔…〕`, `(…)`, or `（…）` — is peeled off first, so notes like `(閩南語借詞) O 'amis ko hongti niyam.…` recover the real sentence instead of a stray parenthesis. (A `（…）` annotation that straddles the split point, e.g. `…hikoki（外來語）.孩子…`, is repaired so the form stays pure Amis.)
- **32** rows recover an Amis phrase embedded in a Chinese grammar/pronunciation note via the source `` `…~ `` link markup (`recovered_form_from_note`), e.g. `如\`ha~\`sapakaen~ 飼養、餵養用的。` → `hasapakaen` / 飼養、餵養用的.
- **191** sentences come from splitting **CJK-in-FORM** fields (`split_from_cjk_form`): the source packed `Amis 中文gloss` content into the form slot — either a single glued `Itira 在那裡.` → FORM `Itira` / TRANSL `在那裡`, or a `；`/`，`-separated derivational list (often prefixed `如`) such as `kalacokap 當鞋子穿；kalasakaen 當菜餚吃；…` → one sentence per pair. Fields that cannot be cleanly segmented are rejected (`cjk_in_form_unsplittable`), which also catches the 4 pure-Chinese notes.
- **272** rows have a real Amis FORM but no Chinese translation; FormosanBank's schema makes `TRANSL` optional (`S_Type` is an `xs:choice minOccurs="0"`), so they are kept as valid **FORM-only** sentences (`no_translation`).
- A handful of source form fields begin with an orphaned `）`/`)` (a digitization artifact); the leading close-paren is stripped.
- **44** fields remain unrecoverable: **26** `empty_form` and **18** `cjk_in_form_unsplittable` (multi-phrase grammar notes + the 4 pure-Chinese notes).

`TEXT/@dialect` is currently `"unknown"` (the dictionary does not record a single Amis dialect); set the real dialect during QC (e.g. via the FormosanBank dialect detector) before porting into `Corpora/`.

## FormosanBank Shape

A single `TEXT` root with `S` children. After QC enrichment (below) each sentence has:

- `FORM kindOf="original"` — the source text.
- `FORM kindOf="standard"` — the common-orthography tier (a copy of original; the
  source is already in the Ortho113 letter set, so no transliteration is applied).
- `PHON kindOf="standard"` — IPA generated from the standard FORM via Ortho113.
- `TRANSL xml:lang="zho"` — when the source provided a Chinese translation
  (272 sentences are valid FORM-only with no translation).

No `W`/`M` segmentation — the Moedict examples carry no source-attested word or
morpheme tiers.

`make qc`'s `clean_xml` normalizes source noise (smart quotes, zero-width chars,
bracket/width variants). A dozen rows still carry stray OCR characters faithful to
the source (e.g. `mafutiۥ`, `cangaw﹑fiting`); these are SOFT `validate_text`
findings, not auto-corrected.

## QC enrichment pipeline (Ortho113)

The build (`make safolu`) emits only the **original** tier. The standard tier, IPA
phonology, and character cleaning are added by FormosanBank's shared QC tools as a
second stage. Run it **after** the build:

```sh
make -C CodeAndDocs qc   # requires FormosanBank's QC tools (FB=../../.. from CodeAndDocs)
```

`make qc` runs, in this exact order (the ordering matters):

1. `clean_xml.py` — normalize unicode/HTML artifacts **before** standardizing
   (smart quotes `’‘“”` → ASCII, strip zero-width characters, caret variants, etc.).
2. `standardize.py --copy` — create `FORM kindOf="standard"`. Amis here is already
   in the **Ortho113** letter set, so the standard tier is a faithful copy (no TSV
   transliteration). `'` and `^` are distinct Ortho113 letters (different phonemes:
   `'` → ʡ, `^` → ʔ) and are both preserved as-is.
3. `clean_xml.py` — clean again **after** standardizing, so the new standard tier
   is normalized too.
4. `add_phonology.py` — generate `PHON kindOf="standard"` IPA from the standard
   FORM via `Orthographies/Ortho113/Amis.tsv` (e.g. `^` → `ʔ`, `'` → `ʡ`, `e` → `ə`,
   `c` → `ʦ`). Characters outside the Ortho113 inventory become `*`.
5. `remove_duplicate_sentences.py --apply` — drop duplicate example sentences (the
   same example reused under related headwords; compared on the standard tier,
   first occurrence kept). 255 removed → 49,145.
6. `validate_xml.py` + `validate_text.py` — structural + text-content validation.

`clean_xml.py` writes an informational `cleaner_warnings.csv`; `make qc` moves it
to the gitignored `qc-logs/` so `Final_XML/` stays XML-only.

> The committed XML is the **post-QC** artifact. Re-running `make safolu` resets it
> to original-tier-only, so re-run `make qc` after any rebuild.

## Reproduce

```sh
make -C CodeAndDocs sources   # clone g0v/amis-moedict (docs/s) + miaoski/amis-safolu
make -C CodeAndDocs safolu    # build original-tier XML + validate + coverage audit
make -C CodeAndDocs qc        # enrich: standard tier + IPA PHON + clean (Ortho113)
```

(`make -C CodeAndDocs` runs from `CodeAndDocs/`, so the build's working tree —
`Final_XML/`, `_sources/`, `data/` — is created there; the published copy lives
under `XML/`. Set `FB=../../..` so the QC tools resolve to this checkout.)

Pinned source commits live in `CodeAndDocs/fetch_sources.py`. See
`CodeAndDocs/SOURCE_AUDIT.md` for the detailed source mapping and coverage accounting.

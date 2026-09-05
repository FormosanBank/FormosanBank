---
icon: layer-group
---

# add_phonology.py

> Adds `PHON` (phonemic transcription) tiers by mapping a corpus's text through orthography→phoneme tables under `Orthographies/`.

## What it's for

`add_phonology.py` derives an IPA-ish phonemic transcription from already-spelled text and stores it as a sister `PHON` element next to each `FORM`. It processes the **standard** tier through the language's *designated standard orthography*, and with `--orthography <Name>` it can additionally transcribe the **original** tier through a second, source-specific orthography table.

Which orthography is "designated" comes from [`standards.csv`](https://github.com/FormosanBank/FormosanBank/blob/main/standards.csv) at the repo root, one row per language. Sixteen of the eighteen languages currently name `Ortho113`; **a blank entry means standard `PHON` is deliberately skipped** for that language, and the script says so rather than guessing. Siraya and Babuza-Favorlang are blank today. Per POL-003 the `PHON` tier is machine-owned: `add_phonology.py` regenerates it, and hand edits to it are stripped from manual-edit records.

## How it works

For each file it reads `TEXT/@xml:lang` (mapped to a language name) and `TEXT/@dialect`, then loads `Orthographies/<Scheme>/<Language>.tsv`, where `<Scheme>` is the language's `standards.csv` entry. That TSV has a `letter` column plus value columns; the column actually used is chosen by whether the language is multi-dialect (per `dialects.csv`):

- **Explicit override**: `--target_column` selects that value column in the standard orthography table and takes precedence over dialect detection.
- **Multi-dialect**: without an override, the `dialect` attribute selects the column, falling back to a `default` column.
- **Single-dialect**: the sole value column, else `IPA`, else `default`.

It builds an ordered list of `(letter → phoneme)` pairs (rows whose value is the literal `NA` are skipped), then for every `FORM[@kindOf="standard"]`:

1. **Ensure the tier exists.** A sibling `PHON[@kindOf="standard"]` is created right after the `FORM` if there is not one already.
2. **Null morphemes are silent.** A null *unit* inside a longer form — `∅` plus one bridging segmentation hyphen — is dropped before anything else, since it has no sound. A FORM that *is* the null marker yields `PHON` `∅` rather than an empty string: `V073` makes an empty `PHON` a HARD error, and a visible `∅` states "this morpheme is silent" instead. Only the canonical `∅` (U+2205) counts — normalizing `ø`/`Ø` is `clean_xml`'s job, so a Danish `ø` arriving here takes the ordinary unmapped-letter path. See POL-012.
3. **Fold stress accents.** Acute and macron diacritics are usually prosody, not segments, so a stress accent folds to its base vowel — otherwise it would fall through to step 6 and surface as `*`.

   The same judgement is already made once upstream, and by the same rule: since 2026-09-04 [`standardize.py`](standardize.md) folds accents out of the standard tier **while keeping those the language's reference orthography attests**, in `--remove_accents` and conversion-table modes alike. So an unattested stress accent is normally gone before `add_phonology` sees the standard tier, while an attested one survives — and then needs a row in the orthography table here, or it stars in step 6.

   The **original** tier always keeps its accents; nothing rewrites it (POL-001). That is why this fold runs on a working copy of the text and never on the `FORM` itself, and why the original tier is where the fold does most of its work.

   An accented letter a language genuinely attests must not be folded, or two distinct letters merge. The **keep set** here is the accented letters of the language's own orthography table **plus** those in its reference orthography (`QC/validation/reference/<Language>/`): Rukai `é`, Puyuma `é ē`, Yami `á é í ó` and Thao `í`.

   **Being kept is not the same as being mapped.** A kept letter still needs a row in the orthography table; without one it reaches step 6 as an unmapped letter and becomes `*`. Only Rukai's `é` currently has such a row — see the note below.
4. **Strip segmentation markers**, so `PHON` stays clean IPA even when the FORM tier carries them: `=` (clitic) and the `<...>` infix brackets are always removed — the infix content is kept, since it is pronounced — while `-` is removed only when it is **not** a letter in the language's orthography (Bunun/Thao keep `-`). The mappings are then applied by longest-grapheme match, preferring an exact match before a case-insensitive one, and never remapping IPA the pass has already produced.
5. **Apply the contextual rules**, if the language has any. A `<Language>.rules.tsv` sidecar beside the orthography table holds ordered `pattern`/`replacement`/`description` regex rules, applied in file order after the mappings — for context-sensitive realizations a flat letter table cannot express. Four exist today: Bunun, Seediq, Thao and Yami. An optional `dialect` column scopes a rule the same way the mapping columns are scoped: blank means universal, a named dialect means that dialect only, and `default` means "the fallback, for dialects no rule names explicitly".
6. **Clean up what is left.** Known phonemes, `*`, whitespace and combining marks pass through. Unmapped **punctuation is dropped** — it is not sound, and mapped punctuation such as an orthographic apostrophe was already consumed in step 4. Anything else — an unmapped *letter* — becomes `*`.

The resulting string becomes the `PHON` element's text. With `--orthography <Name>`, the same procedure runs over `FORM[@kindOf="original"]` using `Orthographies/<Name>/<Language>.tsv`, writing `PHON[@kindOf="original"]`.

### Reading a `*` in a PHON tier

A `*` means **an unmapped letter**, and it is a signal worth chasing: either the orthography table is missing a grapheme, or the FORM carries a character that does not belong to that orthography. It does **not** mean a prosodic stress accent (folded in step 3) or stray punctuation (dropped in step 6).

> **Known gap — attested accented letters with no table row.** Puyuma `é ē`, Yami `á é í ó` and Thao `í` are attested in their reference orthographies, so step 3 correctly declines to fold them — but `Orthographies/Ortho113/<Language>.tsv` has no row for any of them, so they star in step 6. This accounts for **2,076 `*` in published `PHON`**: RauDong Yami 1,098, ePark Puyuma 910, Presidential_Apologies Puyuma 54, ILRDF_Dicts Thao 14, Li-Conjunction-Thao 20.
>
> Which tier stars depends on when the corpus was last standardized. ePark, Presidential_Apologies and ILRDF_Dicts carry the accented letters on both tiers, so both star, in equal numbers. RauDong and Li-Conjunction-Thao star only on the **original** tier, because their published standard tier was built by a `standardize.py` run that predates the 2026-09-04 keep-set fix and stripped the letters unconditionally. **Regenerating either corpus will restore those letters to its standard tier** — correctly, since they are attested — and they will then star there too until the orthography table gains rows.
>
> The fix is a row per letter in the orthography table, not a code change. Until then, treat a `*` on one of those letters as known rather than as a new orthography problem.

## Schema note (PHON is fully supported)

A `PHON` tier is **valid under the current schema**. [`QC/validation/xml_template.xsd`](validate-xml.md) defines a `PHON_Type` (mixed content; optional `kindOf` enumerated `original`/`standard`) and allows `PHON` in any order within `S`, `W`, and `M`. The retained fallback DTD also permits `PHON*`. So the older caveat that adding `PHON` could trip XSD/DTD validation **no longer applies** — files with `PHON` tiers pass `validate_xml.py`. (Still re-run [validate_xml.py](validate-xml.md) after this step as a matter of course.)

## Usage

Run from the FormosanBank repo root after `source .venv/bin/activate`.

```bash
# Standard tier only (uses each language's standards.csv orthography)
python QC/utilities/add_phonology.py \
  --corpora_path /path/to/corpus-or-Final_XML

# Also transcribe the original tier through a source orthography
python QC/utilities/add_phonology.py \
  --corpora_path /path/to/corpus-or-Final_XML \
  --orthography Church \
  --language Amis
```

| Flag | Default | Notes |
| --- | --- | --- |
| `--corpora_path` | (required) | Corpora root (iterated entry-by-entry), a corpus dir, or a single `.xml` file. |
| `--orthography` | none | Folder name under `Orthographies/` used to also transcribe the **original** tier. Must exist. |
| `--language` | none | Restrict to files whose path matches this language name. |
| `--target_column` | none | Force a specific value column in the standard orthography table; otherwise auto-detect from dialect/language. |

### Single-file wrapper

`add_phonology.py --corpora_path <file.xml>` can operate on one XML file directly. `QC/utilities/add_phonology_single_file.py` is still available as a wrapper for workflows that prefer an explicit `--xml_path`; it runs `add_phonology.py` on one file via a temp directory, copying the result back. Flags: `--xml_path`, `--orthography`, `--target_column`, `--language`.

## Output & side effects

**Modifies XML in place.** A `PHON` element is inserted after each processed `FORM`, and each file is re-serialized and overwritten. The serializer preserves inline mixed content without inserting formatting whitespace inside it. Inspect the diff before committing. Confirm the phonemic strings look right and that stray `*` markers (unmapped letters) are not hiding orthography problems. If the language has no `standards.csv` entry, standard `PHON` is skipped with a warning; if it has one but the table is missing, that is reported as a separate warning.

## When to run it

After the standard tier exists (see [standardize.py](standardize.md)) and after orthography has been validated, so the input spelling is trustworthy. It is an optional enrichment step rather than a gate. See [Running an Audit](../running-an-audit.md) and [Porting a Corpus In](../porting-a-corpus.md).

## Related

- [QC Pipeline overview](README.md)
- [standardize.py](standardize.md)
- [orthography_detector.py](orthography-detector.md)
- [validate_xml.py](validate-xml.md)

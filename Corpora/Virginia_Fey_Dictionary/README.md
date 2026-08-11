# Virginia Fey Amis Dictionary

## License and AI Use

This corpus is subject to its source license and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

This corpus contains the example sentences and phrases of Virginia Fey's (1986) *Amis Dictionary* (阿美語字典), structured into the [FormosanBank XML format](https://ai4commsci.gitbook.io/formosanbank/the-bank-architecture/xml-standardize-format). Language: Amis (`ami`), dialect Xiuguluan; 2,040 sentences in a single file, `XML/Amis/Amis.xml`.

The XML was created from a CSV provided by [https://github.com/miaoski/amis-data](https://github.com/miaoski/amis-data) and then **cleaned by hand** to address parentheticals and other annotations. Because the hand-cleaning is not reproducible from the source CSV, the published XML is itself the baseline: this corpus is **non-regenerable** and falls under POL-035. The pristine pre-correction `XML/` is preserved byte-identically at `CodeAndDocs/pre_correction_snapshot/`, and `make_xml.sh` rebuilds the published `XML/` from it, so the published files are exactly `snapshot + pipeline`.

## Notes

1. According to Li et al. (2024), "Fey’s (1986) dictionary ... misses certain phonemic contrasts, such as the distinction between the glottal stop and the pharyngealized stop, for example, e.g., Central Amis ’op’op ‘frog’ vs. qopo ‘assemble’."

However, the repo from which this corpus is derived states:

> Thanks to Mr. Wu Ming-yi for rewriting the old Catholic spelling into the newer spelling of the original Minzu Kung Hui version.

It is not clear whether this addressed the concerns raised by Li and colleagues, but the orthography seems to be a good match for our reference corpus.

2. There are often multiple translations into the same non-Formosan language for a particular sentence. Thus do not assume there is only one `<TRANSL>` element per target language.

## Layout

- **XML/** — the published, canonical data (`Amis/Amis.xml`).
- **CodeAndDocs/pre_correction_snapshot/** — POL-035 pre-correction baseline; the pipeline's input.
- **CodeAndDocs/fix_duplicate_ids.py** — pipeline step 1 (see below).
- **CodeAndDocs/make_xml.sh** — regenerates `XML/` from the snapshot; runs the full pipeline.
- **CodeAndDocs/requirements.txt** — Python libraries for the original processing scripts.

## Regenerating XML/ (the pipeline)

Everything is wrapped by:

```bash
cd Corpora/Virginia_Fey_Dictionary/CodeAndDocs
./make_xml.sh [path/to/FormosanBank]   # defaults to the repo this corpus sits in
# Use PYTHON=/path/to/python to override the interpreter (default: <root>/.venv/bin/python)
```

The script restores `XML/` from the snapshot and then runs, in order:

1. **Fix duplicate ids**

   ```bash
   python fix_duplicate_ids.py --path ../XML
   ```

   Ensures every S id is unique within the file (re-ids the second occurrence of a duplicated id with a letter suffix, e.g. `S3797` → `S3797b`). The fix is already applied to the snapshot, so this runs as an idempotent no-op guard.

2. **Clean XML**

   ```bash
   python path/to/FormosanBank/QC/cleaning/clean_xml.py --corpora_path ../XML
   ```

   Original-tier cleaning: removes empty elements, flattens Unicode (NFC), decodes HTML escapes, normalizes dash/quote look-alikes and null glyphs, and applies the Amis apostrophe/quote classifier. Any quote correction is logged durably to `CodeAndDocs/quote_corrections.csv`, which must then be committed.

3. **Standardize orthography**

   ```bash
   python path/to/FormosanBank/QC/utilities/standardize.py --remove_accents --corpora_path ../XML
   ```

   Creates the `kindOf="standard"` FORM tier as a copy of `kindOf="original"`, then deletes stress accents and removes S-level null-morpheme units. No conversion table is applied because the dictionary's orthography already matches the reference orthography.

4. **Add IPA**

   ```bash
   python path/to/FormosanBank/QC/utilities/add_phonology.py --corpora_path ../XML --orthography Ortho113
   ```

   Regenerates the PHON tiers (original and standard) from the FORMs.

5. **Remove duplicate sentences**

   ```bash
   python path/to/FormosanBank/QC/cleaning/remove_duplicate_sentences.py by_path --path ../XML --apply
   ```

   As a dictionary (reference resource), this corpus is duplicate-free per POL-022: sentences repeating an earlier sentence's standard FORM text are dropped, keeping the first occurrence. Because the pipeline declares this step, any duplicate found by `validate_duplicate_sentences` is a HARD finding for this corpus.

Warning sidecars (`cleaner_warnings.csv`, `standardize_warnings.csv`) are per-run reports (POL-033): review them after a run, never commit them. `quote_corrections.csv` is the exception — durable, append-only, committed.

## References

Fey, Virginia (1986). *Amis Dictionary* (阿美語字典). The Bible Society in Taiwan.

Li, P. J. K., Joby, C., & Zeitoun, E. (2024). Word Lists and Dictionaries of Formosan Languages. Handbook on Formosan languages: The indigenous languages of Taiwan. Leiden: Brill.

## License

According to [the github repo we sourced this from](https://github.com/miaoski/amis-data), permission for a CC-BY-NC license was provided by the Taipei Bible Society:

>謹感謝 台灣聖經公會 授權電子化。商業使用之授權，請洽[台灣聖經公會]。

>感謝吳明義老師將天主教的舊式拼法，改寫成原民會版本的新式拼法。

>This work is licensed under the Creative Commons 姓名標示-非商業性 3.0 Unported License. To view a copy of this license, visit http://creativecommons.org/licenses/by-nc/3.0/deed.zh_TW.

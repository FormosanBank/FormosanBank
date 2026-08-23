# Virginia Fey Amis Dictionary

## License and AI Use

This corpus is subject to its source license and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

This corpus contains the example sentences and phrases of Virginia Fey's (1986) *Amis Dictionary* (阿美語字典), structured in the [FormosanBank XML format](https://ai4commsci.gitbook.io/formosanbank/the-bank-architecture/formosanbank-xml-format). It contains 2,041 deduplicated Amis (`ami`) sentence records in `XML/Amis/Amis.xml`, routed to the Xiuguluan dialect.

The lost original converter and extensive hand cleaning cannot be recreated. Under POL-035, the preserved hand-cleaned XML is therefore the pre-correction baseline. The current pipeline combines that baseline with a pinned 6,899-row maintenance sheet, reviewed source decisions, canonical cleaning, standardization, PHON generation, and reference-resource deduplication. It accounts for 2,012 complete source rows and all 2,051 form alternatives before ten declared duplicate attestations are merged.

## Notes

1. The pinned upstream commit descends from the `ramoh-fixed` tag. Its README states that Wu Ming-yi revised the old Catholic spelling into the newer Council of Indigenous Peoples spelling. The pipeline therefore preserves source FORM and uses `--remove_accents` plus the current Amis `Ortho113` profile rather than applying a conversion table.

2. Wu's dissertation identifies Fey 1986 as a dictionary of the “Standard Central Dialect” from Fuyuan to Fuli and Fengbin to Yiwan (PDF page 27, printed page 7). FormosanBank's current dialect registry maps Central to Xiuguluan, confirming the XML routing.

3. Many source example translations contain slash alternatives, parenthetical explanations, or analytic notes. Clean readings remain separate TRANSL elements under POL-024 and POL-025. Whenever a reading is split or cleaned, the exact source field is preserved in the primary TRANSL's `notes` attribute and checked by `audit_source_alignment.py`.

## Layout

- **XML/** — the published, canonical data (`Amis/Amis.xml`).
- **CodeAndDocs/pre_correction_snapshot/** — POL-035 pre-correction baseline; the pipeline's input.
- **CodeAndDocs/source/** — pinned maintenance CSV, upstream license, README, and raw evidence files.
- **CodeAndDocs/source_decisions.json** — source hashes, all slash expansions, evidence-backed corrections, dedup mappings, and reviewed translation exceptions.
- **CodeAndDocs/fix_duplicate_ids.py** — pipeline step 1 (see below).
- **CodeAndDocs/reconcile_source.py** — data-driven source reconciliation.
- **CodeAndDocs/audit_source_alignment.py** — complete pre-dedup and canonical source-coverage gate.
- **CodeAndDocs/make_xml.sh** — regenerates `XML/` from the snapshot; runs the full pipeline.
- **CodeAndDocs/requirements.txt** — pinned Python dependencies.

## Regenerating XML/ (the pipeline)

Everything is wrapped by:

```bash
cd CodeAndDocs
./make_xml.sh [path/to/FormosanBank]   # auto-detects an embedded or sibling checkout
# Use PYTHON=/path/to/python to override the interpreter (default: <root>/.venv/bin/python)
```

The script restores `XML/` from the snapshot and then runs, in order:

1. **Fix duplicate ids**

   ```bash
   python fix_duplicate_ids.py --path ../XML
   ```

   Ensures every S id is unique within the file (re-ids the second occurrence of a duplicated id with a letter suffix, e.g. `S3797` → `S3797b`). The fix is already applied to the snapshot, so this runs as an idempotent no-op guard.

2. **Reconcile the true source**

   ```bash
   python reconcile_source.py --path ../XML/Amis/Amis.xml
   ```

   Verifies every pinned input hash, corrects the CC BY-NC 3.0 metadata, repairs the reviewed form and translation defects, creates every POL-027 alternative, and preserves exact transformed source translations as notes.

3. **Clean XML**

   ```bash
   python path/to/FormosanBank/QC/cleaning/clean_xml.py --corpora_path ../XML
   ```

   Original-tier cleaning: removes empty elements, flattens Unicode (NFC), decodes HTML escapes, normalizes dash/quote look-alikes and null glyphs, and applies the Amis apostrophe/quote classifier. Any quote correction is logged durably to `CodeAndDocs/quote_corrections.csv`, which must then be committed.

4. **Standardize orthography**

   ```bash
   python path/to/FormosanBank/QC/utilities/standardize.py --remove_accents --corpora_path ../XML
   ```

   Creates the `kindOf="standard"` FORM tier as a copy of `kindOf="original"`, then deletes stress accents and removes S-level null-morpheme units. No conversion table is applied because the dictionary's orthography already matches the reference orthography.

5. **Add IPA**

   ```bash
   python path/to/FormosanBank/QC/utilities/add_phonology.py --corpora_path ../XML --orthography Ortho113
   ```

   Regenerates the PHON tiers (original and standard) from the FORMs.

6. **Audit all source units before deduplication**

   ```bash
   python audit_source_alignment.py --stage pre-dedup --path ../XML/Amis/Amis.xml
   ```

   Requires the exact 2,012 source rows and 2,051 source units, no unreviewed form or translation additions, exact source notes for transformed translations, and the declared metadata.

7. **Remove duplicate sentences**

   ```bash
   python path/to/FormosanBank/QC/cleaning/remove_duplicate_sentences.py by_path --path ../XML --apply
   ```

   As a dictionary (reference resource), this corpus is duplicate-free per POL-022: sentences repeating an earlier sentence's standard FORM text are dropped, keeping the first occurrence. Because the pipeline declares this step, any duplicate found by `validate_duplicate_sentences` is a HARD finding for this corpus.

8. **Audit the canonical deduplicated output**

   ```bash
   python audit_source_alignment.py --stage canonical --path ../XML/Amis/Amis.xml
   ```

   Requires exactly the ten declared source-unit merges and confirms that their translations remain attached to the surviving S records.

Warning sidecars (`cleaner_warnings.csv`, `standardize_warnings.csv`) are per-run reports (POL-033): review them after a run, never commit them. `quote_corrections.csv` is the exception — durable, append-only, committed.

## References

Fey, Virginia (1986). *Amis Dictionary* (阿美語字典). The Bible Society in Taiwan.

Li, P. J. K., Joby, C., & Zeitoun, E. (2024). Word Lists and Dictionaries of Formosan Languages. Handbook on Formosan languages: The indigenous languages of Taiwan. Leiden: Brill.

Wu, J. (2006). *Verb Classification, Case Marking, and Grammatical Relations in Amis*. University at Buffalo. Dialect evidence is in Table 1.4, PDF page 27.

## License

According to the pinned [upstream repository](https://github.com/miaoski/amis-data), the Taiwan Bible Society authorized digitization and the source data is CC BY-NC 3.0. `CodeAndDocs/source_decisions.json` records the exact upstream revision and file hashes.

>謹感謝 台灣聖經公會 授權電子化。商業使用之授權，請洽[台灣聖經公會]。

>感謝吳明義老師將天主教的舊式拼法，改寫成原民會版本的新式拼法。

>This work is licensed under the Creative Commons 姓名標示-非商業性 3.0 Unported License. To view a copy of this license, visit http://creativecommons.org/licenses/by-nc/3.0/deed.zh_TW.

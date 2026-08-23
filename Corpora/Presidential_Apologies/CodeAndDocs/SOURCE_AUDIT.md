# Source audit

Audit date: 2026-08-22

## Authority and scope

The 16 PDFs are official Council of Indigenous Peoples publications linked from the Presidential Office Indigenous Historical Justice project. The current FormosanBank source coordination record labels the corpus public domain and identifies the official source. Every PDF has 28 physical pages and presents an Indigenous-language translation beside Mandarin.

The audit covers:

- all 524 native transcript sections against their corresponding PDF;
- all 524 Mandarin transcript sections against their corresponding PDF;
- source file SHA-256, byte size, page count, and text section count;
- deterministic mapping of the separate official English transcript snapshot;
- stable TEXT and sentence identifiers against the published FormosanBank baseline.

English is outside the PDF alignment claim because it is not printed in these bilingual PDFs.

## Method

`scripts/audit_source_alignment.py` extracts PDF text blocks with PyMuPDF, separates predominantly Latin and predominantly CJK blocks, orders them by physical page and position, and joins adjacent blocks when one section spans a layout break. For body sections, it first locates each Mandarin section, then requires the paired native section to occur on the same physical page range. This prevents repeated native text from being credited to the wrong source section. The title is exempt because the Mandarin cover title and native title page are separate.

Comparison uses NFC text and ignores PDF layout whitespace. It treats the following presentation variants as equivalent:

- straight, curly, and fullwidth apostrophes and quotation marks;
- fullwidth and ASCII punctuation;
- Unicode and repeated-period ellipses;
- a transcript terminal period on the title or final section when the display text omits it.

It does not fold case, change letters, normalize diacritics, or apply language-specific spelling rules. A passing row requires exact containment after only those documented presentation normalizations.

## Results

- Source manifest: 36 files verified.
- Native PDF alignment: 524 of 524 sections passed.
- Mandarin PDF alignment: 524 of 524 sections passed.
- Total alignment rows: 1,048 of 1,048 passed at `100.000`.
- Native source-content corrections: 2, both listed in `data/source_corrections.csv`.
- Published word-boundary reconciliations: 1 Kavalan section, also listed in `data/source_corrections.csv`.

The Saaroa title correction was visually checked on physical page 5. The Truku punctuation correction was visually checked on physical page 23. Additional visual checks covered Amis physical pages 1 through 3 and 27 through 28, Saaroa pages 1 through 2, and the relevant Truku body page.

Saaroa sections `22` and `23` contain the same native text with different Mandarin and English translations. Physical pages 22 and 23 repeat that native paragraph beside the two distinct Mandarin sections. The duplicate is therefore source-faithful and is retained under the corpus's policy of preserving source-authored repetition.

The dialect labels are not attributed to the PDFs. They are inherited from the published FormosanBank baseline at commit `3a3c47c220520113f747e6a2d441494000e13c4b` and documented separately in `data/dialect_authority.tsv`.

# Formosan-SEALS

Source-faithful Saisiyat and Seediq text from the SEALS 33 national-languages page.

## License and AI use

This corpus is subject to its source rights and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI use is prohibited without prior written permission.

## Source and permission

The source is the SEALS 33 organizing committee's [national-languages page](https://sites.google.com/view/seals33/national-languages). It presents parallel Mandarin, Saisiyat, and Seediq text, with English translations for program titles.

The Formosan Corpora Basecamp card records the organizers' permission to include the page in FormosanBank. The XML therefore identifies the organizing committee as the copyright holder and says that FormosanBank uses the material with permission. The previous `CC-BY-NC` claim was removed because the source and permission record do not establish that license.

## Corpus contents

- `XML/Saisiyat/saisiyat_seals.xml`: 28 source rows, `xml:lang="xsy"`, `dialect="Saisiyat"`.
- `XML/Seediq/seediq_SEALS.xml`: 28 source rows, `xml:lang="trv"`, `dialect="unknown"`.
- Each retained row has a Mandarin translation. Fifteen retained program rows also have English translations.
- There is no audio and no word or morpheme analysis.

The source has 29 parallel rows. Source row 25 is excluded from both languages under POL-016 because both Formosan titles contain reconstruction asterisks. Its exact source text remains in `CodeAndDocs/data/source_snapshot.json`, and the original stable S IDs are preserved with a deliberate gap at 25.

## Publication provenance

- Development baseline: the private Formosan-SEALS repository, audited and approved on 2026-08-23.
- FormosanBank tooling used for QC: `3a3c47c220520113f747e6a2d441494000e13c4b`.
- QC verdict: `ready to port` on 2026-08-23, with 0 applicable hard findings and 0 port-readiness warnings.
- Stable IDs: TEXT IDs remain `saisiyat_seals` and `seediq_SEALS`; S IDs are the source row numbers, with row 25 deliberately absent.

## Reproduction

Create an environment and install the pinned public reproduction dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r CodeAndDocs/requirements.txt
```

Run the complete build against a current FormosanBank checkout:

```bash
./CodeAndDocs/reproduce.sh
```

The script performs these steps in order:

1. Build source-tier XML from the committed structured snapshot.
2. Audit all source rows and the POL-016 exclusion.
3. Run the manual-edits phase, which is an explicit no-op because this corpus has no manual-edits file.
4. Run FormosanBank's source-safe XML cleaner.
5. Regenerate standard FORM with `standardize.py --copy`.
6. Regenerate original and standard PHON with source orthography `Ortho94`; standard PHON follows FormosanBank's Ortho113 registry.
7. Repeat the source audit and remove the reviewed ephemeral cleaner-warning CSV.

The source transcription is Ortho94. Current FormosanBank conversion tables contain no Ortho94-to-Ortho113 spelling rules for either Saisiyat or Seediq, so standard FORM is a machine-owned copy. The Seediq source does not identify one of the registered dialects, so it uses the evidence-preserving `unknown` route and the registered default phonology column.

The cleaner's repeated-dash, bracket, apostrophe, and Chinese-quotation rewrites are audited as current project normalization. Ambiguous Saisiyat apostrophe warnings are accepted only because the final source audit checks every resulting original FORM against the committed source row.

## Source refresh and audit

Normal reproduction is offline and uses the committed snapshot. To verify that the live page still matches it:

```bash
python CodeAndDocs/scripts/scrape_source.py --check
```

To intentionally refresh the snapshot after reviewing a live-source change:

```bash
python CodeAndDocs/scripts/scrape_source.py
```

The scraper fails closed if the audited page structure, 29-row sequence, 16 English-title rows, or presenter-block accounting changes.

Run the focused tests and source audit with:

```bash
cd CodeAndDocs
python -m pytest -q
python scripts/source_audit.py --json
```

Generated XML belongs only in `XML/`. Audit reports, QC reports, warning sidecars, caches, and local paths are not committed.

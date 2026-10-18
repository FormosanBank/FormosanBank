# Reproduction record

```bash
Corpora/ILRDF_Dicts/CodeAndDocs/generate_xml.sh
```

rebuilds `XML/` from committed files only, with the shared QC tools of the
checkout it is run from (POL-047/048). It needs no network access and no
environment variables (`PYTHON` optionally picks the interpreter). It writes
`CodeAndDocs/provenance.json` with the FormosanBank commit it built against
(POL-052) and prints a digest of the XML: `sha256` over the sorted
per-file `sha256sum` lines of every `XML/**/*.xml`,

```bash
find Corpora/ILRDF_Dicts/XML -name '*.xml' | sort | xargs sha256sum | sha256sum
```

Verified 2026-10-18: two consecutive full runs produced byte-identical output
for all 40 files under Corpora/ILRDF_Dicts/ that the build writes (the 32 XML
files, `manual_edits.xml/.md`, `old_to_new_ids.csv`, `docs/split_report.csv`,
`docs/audio_not_published.csv`, `docs/recording_split_ids.csv`,
`docs/edge_space_report.csv`, `provenance.json`); digest
`c4e5462804b729903fa59702a4351817b9aa6c10f2cc1a016552fedb49f40487`.

Same tools, different digest means something stopped being reproducible.
Different tools (a newer commit in `provenance.json`) can legitimately change
the digest: the shared tools moved.

`CodeAndDocs/validate.sh` runs the published-id audit and the corpus tests;
it is not part of the build.

## Refreshing the source

`refresh_source.sh` re-scrapes the ILRDF API into `source_data/snapshots/`
and rewrites the manifest. It is not part of reproduction: it changes the
source of truth, can add, remove or reword records, and can orphan rows of the
frozen main-id ledger. Review the snapshot diff, rebuild, then regenerate
`published_ids.csv` (`python generate_xml.py ledger --write`) and review the
id diff.

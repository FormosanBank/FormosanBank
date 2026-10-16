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

Verified 2026-10-16: two consecutive full runs produced byte-identical output
for all 80 files under Corpora/ILRDF_Dicts/ that the build writes or reads back (XML, `manual_edits.xml/.md`,
`old_to_new_ids.csv`, `docs/split_report.csv`, `provenance.json`);
digest `aa1b31870e88b948108d674a515eabfe686e7655957a164069d20ba4981bc27c`.

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

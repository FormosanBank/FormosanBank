# Reproduction record

Verified 2026-09-08.

| | |
|---|---|
| Pinned authority commit | `b88146902f6a90ab2d73aca0e304d45f565c392e` |
| Combined XML digest | `406bf55bf681082607071cdb5c7b230d73f65da60ef647d265ab8c3369878981` |
| Published ids | 306,820 |
| Tests | 75, passing |
| `validate_xml` | 32 files, 0 issues |

The digest is `sha256` over the sorted per-file `sha256sum` lines of every
`XML/**/*.xml`:

```bash
find Corpora/ILRDF_Dicts/XML -name '*.xml' | sort | xargs sha256sum | sha256sum
```

Two consecutive full runs of `make_xml.sh` against the pinned authority
produced byte-identical output.

## Reproducing

```bash
export FORMOSANBANK_AUTHORITY=/path/to/FormosanBank   # clean, at the pin
CodeAndDocs/make_xml.sh
```

The pin is **informational**. A rebuild uses whatever shared tooling the
authority checkout has, and the script says so — it prints the commit it
actually built against, and its digest, at the end. Pinning the tooling
forever would mean the corpus could never be rebuilt with a fixed
standardizer or cleaner without editing the script, and the pin would rot.

The pin still earns its keep, because it is recorded here beside the digest it
produced. **Same pin, different digest** means something has stopped being
reproducible and wants investigating. **Different pin, different digest** is
ordinary: the shared tooling moved, and this file should be updated to the new
pin and digest once the diff has been reviewed.

To verify a published digest rather than rebuild, set
`FORMOSANBANK_STRICT_AUTHORITY=1` and the mismatch becomes a hard failure.

## Refreshing the source

`refresh_source.sh` re-scrapes the ILRDF API into `source_data/snapshots/`
and rewrites the manifest. `make_xml.sh` then builds from those new
snapshots — the two are independent, and reproduction needs only the second.
A refresh changes the source of truth, so review the snapshot diff and
regenerate the id ledger afterwards.

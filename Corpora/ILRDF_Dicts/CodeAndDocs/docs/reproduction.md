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

The script refuses to run if the authority checkout is at a different commit
or has uncommitted changes: a rebuild against different shared tooling is a
different build, and silently producing one would defeat the point.

When the authority is deliberately moved — because `standardize.py`,
`clean_xml.py` or `add_phonology.py` has changed — update the pin, rebuild,
and record the new digest here. A changed digest with an unchanged pin means
something is not reproducible and wants investigating before it is committed.

# Siraya Gospels reproduction files

`data/verses.jsonl` is the canonical structured source snapshot for the 1,951 reviewed verse units. It records the scan-reviewed Siraya tier and the aligned reference translations. `data/source_ledger.csv` maps every unit to its printed locator, scan page range, reference locator, XML path, and stable sentence ID.

Run the public build from this directory:

```bash
PYTHON=/path/to/python3 ./reproduce.sh
```

The build refreshes the pinned English and Mandarin references, reapplies the committed focused source corrections, regenerates `../XML/`, rebuilds the ledger, and checks translation coverage, source-review hashes, scope decisions, and published IDs. A second run must produce no tracked change.

The Mandarin USFM inputs are checked in with deterministic gzip compression. Their manifest hashes cover the decompressed source bytes, so compression does not change the pinned reference identity. See `reference_translations/cmn-cu89t_usfm/PUBLIC_DOMAIN.md` for provenance and rights.

The two rendered scans are not distributed in FormosanBank. Their identities are recorded in `data/source_review_manifest.json`:

- `Matthew.pdf`: SHA-256 `2c197bf35d4c7affd7d9ccaa5d3743622bfdae8d959e332abd17b5fa7cf1ff80`
- `Gospels of St. Matthew and St. John.pdf`: SHA-256 `bb382f8157b1b2359b7a47d7ec4ad1cfcf396ae8754cfe52a6e01c0ebcc23ca6`

The private development pipeline verified those files directly and hash-locks the full 1,951-unit review by chapter and corpus. This public pipeline verifies the published structured snapshot and all public evidence without requiring or copying the scans.

No standard FORM or PHON tier is generated. The current FormosanBank authority designates no Siraya standard and provides no `fos` phonology profile.

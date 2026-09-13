> Historical output ledger from private commit 43f17c8. Retained as correction evidence; it does not describe the revised parser or establish current readiness. See the root README.

# FormosanBank Audit

Audit files for the finalized FormosanBank XML export of the Safolu Amis dictionary.

- `Amis/Safolu/amis_safolu_examples.xml`: 49,179 sentences; 22 rejected source records; 261 duplicates audited

These XML files contain example sentence / phrase translation pairs. Headwords and definitions are preserved in metadata.

Virginia Fey (`g0v/amis-moedict/docs/p`) is intentionally excluded because it was already processed separately. The Poinsot dictionary (`docs/m`) lives in the Formosan-Poinsot-Amis-Dictionary repository.

Final XML files live under `XML`, which intentionally contains only `.xml` files. The JSON files in this directory are durable source-provenance ledgers. Per-run audit and QC reports are written outside the repository.

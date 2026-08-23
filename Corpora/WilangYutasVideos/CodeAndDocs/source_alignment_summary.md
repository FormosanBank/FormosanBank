# Source alignment summary

- Pinned transcript files: 34
- Manifested XML outputs: 82
- Transcript outputs: 34
- Audio-only outputs: 48
- Timestamped source rows: 6,455
- Included non-empty source rows: 3,014
- Explicitly omitted blank source rows: 3,441
- Translation lines: 237
- Wrapped source continuations restored: 5
- Generated pre-clean XML mismatches: 0
- Issue #1 findings reviewed: 21/21
- Unresolved issue #1 findings: 0

The audit verifies every generated pre-clean XML element against the pinned
source manifest and fails on missing, extra, reclassified, or changed input.
The current FormosanBank cleaning, standardization, and phonology stages run
only after this exact source-alignment gate passes.

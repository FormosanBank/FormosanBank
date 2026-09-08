# Latham source and QC notes

The reviewed source is Latham 1862, printed pp. 315-318, within the six-page
excerpt identified in the README. All 64 Formosan cells are accounted for:
62 records, eight alternate readings and two source dashes. The source ledger,
independent fixtures and reviewer-feedback ledger preserve the full July 25
and July 27 review. Current source content matches the published readings.

## Required invariants

- 38 Siraya and 24 Babuza-Favorlang records retain their published IDs and
  source associations. A spelling correction does not create a new ID.
- Preserve all 70 original/alternate readings and 62 English translations.
- Preserve `motaus`, `chárrina`, `cháan`, `arribórribon`, and `so`/`soa`.
- No standard FORM or PHON, under the merged August 12 ruling. No W/M or audio
  is inferred from a lexical table.
- The historical pre-correction snapshot remains unchanged. Generation reads
  committed transcription, never previous output or a private PDF.

## Finding dispositions

| Check | Expected disposition |
| --- | --- |
| XML V014 | 62 SOFT occurrences: deliberately absent standard FORM, 24 Babuza-Favorlang and 38 Siraya |
| Text V116 | One SOFT occurrence: source `ó` in alternate `arribórribon`, `S_favorlang_neck` |
| Glosses | No W/M analysis; current rules produce no findings |
| Original duplicates | Two SOFT groups with distinct source provenance: `rahpal` across pp. 315/318, `rima` across Favorlang/Sida on p. 317 |
| Orthography comparison | Unavailable: no reference for either historical variety |
| Standard orthography/vocabulary | Inapplicable: the standard tier is deliberately absent |
| Audio | Inapplicable: no source or XML audio |

Removing the unauthorized standard copies removes eight duplicate diacritic
warnings and restores the 62 intended V014 occurrences. No source character
is removed. The old 62 V060 findings disappeared when the shared rule stopped
requiring W tiers in sources without analysis (POL-041).

`validate.sh` checks source consistency, regression fixtures, every applicable
validator, registries and port readiness. Its adjudicator verifies exact
finding scope and rejects any unexpected result. Reports stay outside Git.
The shared orthography CLI currently omits Babuza-Favorlang; the existing
wrapper calls its own extraction functions for both historical varieties.

Rights vocabulary spelling and README/GitBook agreement also require direct
review because current automated rights coverage is incomplete. The existing
public-domain claim is normalized to `public domain`; its textual delta must
receive maintainer review at merge. Technical QC is not merge authorization.

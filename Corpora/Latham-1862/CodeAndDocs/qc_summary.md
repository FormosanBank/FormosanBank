# Latham source and QC notes

The reviewed source is Latham 1862, printed pp. 315-318, within the six-page
excerpt identified in the README. All 64 Formosan cells are accounted for:
62 occupied cells and two source dashes, yielding 68 records and two spelling
variants under revised POL-028. The source ledger,
independent fixtures and reviewer-feedback ledger preserve the full July 25
and July 27 review. Current source content matches the published readings.

## Required invariants

- 38 Siraya and 24 Babuza-Favorlang records retain their published IDs and
  source associations. A spelling correction does not create a new ID.
- Six competing lexemes get separate records with stable `-lex2` IDs: Favorlang
  Man, Hair, Mouth, Neck and Breast, and Sida Foot. Final counts are 39 Siraya
  and 29 Babuza-Favorlang records, 70 original FORM readings and 68 translations.
- Preserve `so`/`soa` and `totto`/`tutta` as original base and `ver="alt"`.
- Preserve `motaus`, `chárrina`, `cháan`, `arribórribon`, and `so`/`soa`.
- No standard FORM or PHON, under the merged August 12 ruling. No W/M or audio
  is inferred from a lexical table.
- The historical pre-correction snapshot remains unchanged. Generation reads
  committed transcription, never previous output or a private PDF.

## Finding dispositions

| Check | Expected disposition |
| --- | --- |
| XML V014 | 68 SOFT occurrences: deliberately absent standard FORM, 29 Babuza-Favorlang and 39 Siraya |
| Text | No findings; all historical source accents remain |
| Glosses | No W/M analysis; current rules produce no findings |
| Original duplicates | Two SOFT groups with distinct source provenance: `rahpal` across pp. 315/318, `rima` across Favorlang/Sida on p. 317 |
| Orthography comparison | Unavailable: no reference for either historical variety |
| Standard orthography/vocabulary | Inapplicable: the standard tier is deliberately absent |
| Audio | Inapplicable: no source or XML audio |

The POL-028 migration removes six V150 and eight V157 findings by correcting
representation, not by dropping readings. Six added lexical records raise
V014 by six. The former V116 on `arribórribon` disappears because original-tier
accents are allowed; its `ó` is unchanged. The August 12 standard/PHON omission
and the POL-041 acceptance of an unparsed wordlist remain in force.

`validate.sh` checks source consistency, regression fixtures, every applicable
validator, registries and port readiness. Its adjudicator verifies exact
finding scope and rejects any unexpected result. Reports stay outside Git.
The shared orthography CLI currently omits Babuza-Favorlang; the existing
wrapper calls its own extraction functions for both historical varieties.

Rights vocabulary spelling and README/GitBook agreement also require direct
review because current automated rights coverage is incomplete. The existing
public-domain claim is normalized to `public domain`; its textual delta must
receive maintainer review at merge. Technical QC is not merge authorization.

# Latham source and QC notes

The reviewed source is Latham 1862, printed pp. 315-318, within the six-page
excerpt identified in the README. All 64 Formosan cells are accounted for.
**40 are published**, yielding 45 records and two spelling variants under
revised POL-028; the 24 cells of the Gabelentz "Sida" column are transcribed
but not published (see the README's *Notes and Issues*). The source ledger,
independent fixtures and reviewer-feedback ledger preserve the full July 25
and July 27 review. Current source content matches the published readings.

## Required invariants

- Every published record keeps the ID it was published under. A spelling
  correction does not create a new ID, and a withdrawn column does not renumber
  what remains.
- Five competing lexemes get separate records with stable `-opt` IDs: Favorlang
  Man, Hair, Mouth, Neck and Breast. Final counts are 16 Siraya and 29
  Babuza-Favorlang records, 47 original FORM readings and 45 translations.
- The 22 published `S_sida_*` records are removed with the Sida column; their
  IDs are retired, not reused.
- Preserve `so`/`soa` and `totto`/`tutta` as original base and `ver="alt"`.
- Preserve `chárrina`, `cháan`, `arribórribon`, and `so`/`soa`. (`motaus` was
  a Sida cell and is no longer published.)
- No standard FORM or PHON, under the merged August 12 ruling. No W/M or audio
  is inferred from a lexical table.
- The historical pre-correction snapshot remains unchanged. Generation reads
  committed transcription, never previous output or a private PDF.

## Finding dispositions

| Check | Expected disposition |
| --- | --- |
| XML V014 | 45 SOFT occurrences: deliberately absent standard FORM, 29 Babuza-Favorlang and 16 Siraya |
| Text | No findings; all historical source accents remain |
| Glosses | No W/M analysis; current rules produce no findings |
| Original duplicates | None. Both former groups needed a Sida record |
| Orthography | Not run at all (POL-058): `standard_orthography` is blank for both varieties and neither has a reference inventory |
| Standard orthography/vocabulary | Inapplicable: the standard tier is deliberately absent |
| Audio | Inapplicable: no source or XML audio |

The POL-028 migration removes six V150 and eight V157 findings by correcting
representation, not by dropping readings. Five added lexical records raise V014
by five; withdrawing the Sida column lowers it by 22. The former V116 on `arribórribon` disappears because original-tier
accents are allowed; its `ó` is unchanged. The August 12 standard/PHON omission
and the POL-041 acceptance of an unparsed wordlist remain in force.

`validate.sh` checks source consistency, regression fixtures, every applicable
validator, registries and port readiness. Its adjudicator verifies exact
finding scope and rejects any unexpected result. Reports stay outside Git.
The orthography steps are gone from `validate.sh` under POL-058, and with them
the wrapper that worked around the shared CLI's language allowlist. That
allowlist is fixed on main, and the corpus layout now satisfies POL-059.

Rights vocabulary spelling and README/GitBook agreement also require direct
review because current automated rights coverage is incomplete. The existing
public-domain claim is normalized to `public domain`; its textual delta must
receive maintainer review at merge. Technical QC is not merge authorization.

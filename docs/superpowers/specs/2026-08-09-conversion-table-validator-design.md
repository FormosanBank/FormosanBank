# Conversion-table validator design

`QC/validation/validate_conversion_table.py` — audits an orthography
conversion table by checking, transitively through IPA, that applying the
table to a source orthography reproduces a target orthography as closely as
possible. It surfaces the cases where that is *impossible* (a grapheme
covering two phonemes, an unencoded distinction) and the cases where two
orthographies notate the same sound differently, producing a human-readable
audit report rather than silently "passing".

## Inputs

Three positional arguments, all TSV paths:

1. **original orthography** — e.g. `Orthographies/Li/Rukai.tsv`
2. **output orthography** — e.g. `Orthographies/Ortho113/Rukai.tsv`
3. **conversion table** — e.g. `Orthographies/ConversionTables/Rukai_Li_113.tsv`

Optional: `--output <path>` (write the report to a file instead of stdout),
`--dialect <name>` (restrict checking to one dialect column).

### Data shapes (existing in-repo)

- **Orthography profile**: TSV with a `letter` column plus one or more value
  columns holding IPA. Value columns are either per-dialect (e.g.
  `Ortho113/Rukai.tsv`: `Wutai Eastern … default`) or a single `IPA`/`default`
  column (e.g. `Li/Rukai.tsv`: `letter IPA`). `NA` means "not in this
  dialect". This is the same shape `QC/utilities/add_phonology.py` consumes.
- **Conversion table**: TSV whose first column is the source grapheme and
  whose remaining column(s) are the target grapheme(s). Single-column tables
  use a header like `original / standard` (e.g. `Rukai_Li_113.tsv`);
  multi-dialect tables use per-dialect columns (e.g. `Amis_Church_113.tsv`).

## Core model

Load both profiles with the existing longest-match, dialect-aware loader
(reuse `add_phonology.load_profile` / its column-selection logic). Load the
conversion table with the analogous per-dialect column selection.

The check is **transitive through IPA**, evaluated per output dialect column
(falling back to `default`/the single value column when a dialect column is
absent in either the conversion table or a profile):

> For each conversion row `src → tgt`:
> `IPA(src)` in the original profile, versus `IPA(tgt)` obtained by
> re-tokenizing `tgt` through the **output** profile's grapheme→IPA map
> (longest-match) and concatenating.

Re-tokenizing the target matters because the target field is orthographic
text in the output orthography, and that orthography has multi-character
graphemes: `tr` must be read as one grapheme (`tr`→ʈ), not `t`+`r`, while
`aa` (no such grapheme) tokenizes to the sequence `[a, a]`.

## Verdict tiers

Each conversion row resolves to exactly one tier, split by *whether the only
reconciling transform can change segmentation* (one segment vs. two):

- **Confirmed** (exit 0) — IPA equal after safe glyph-only normalization
  that cannot change segment count: Unicode NFC/NFD, Latin `g` (U+0067) ↔ IPA
  script `ɡ` (U+0261), and affricate tie-bar ↔ ligature (`t͡s` ↔ `ʦ`,
  `d͡z` ↔ `ʣ`, `t͡ʃ` ↔ `ʧ`, `d͡ʒ` ↔ `ʤ`). Both sides are unambiguously the
  same single segment.
- **Warning** (exit 0, human must confirm) — IPA equal only after a transform
  that reinterprets one-vs-two segments, which the orthography does not
  disambiguate: length ↔ doubling (`aː`/`a:` ↔ `aa`) and bare digraph ↔
  affricate (`ts` ↔ `t͡s`). Surfaced in its own report section.
- **Unresolved mismatch** (exit nonzero) — IPA differ even after all of the
  above.

## Information-loss and table-integrity findings

Beyond per-row IPA comparison:

- **Phoneme merge** (Warning, exit 0) — two distinct source graphemes with
  distinct source IPA whose targets resolve to the same output IPA. The
  distinction is lost; a human confirms this is intended.
- **Original-can't-encode** (Warning, exit 0) — the output orthography
  distinguishes two IPA values that the source writes with a single grapheme,
  so the source cannot have encoded the distinction. This is the "one
  character for two phonemes" case.
- **Coverage gap** (Warning, exit 0) — a source-profile grapheme with no
  conversion row and no valid identity passthrough (identity passthrough =
  the same grapheme exists in the output profile with equal IPA).
- **Unknown source grapheme** (Unresolved, exit nonzero) — a conversion row
  whose `src` is absent from the original profile. The table references
  something the orthography does not define.
- **Untokenizable target** (Unresolved, exit nonzero) — a conversion `tgt`
  containing a grapheme absent from the output profile, so no IPA can be
  computed.

## Exit contract

Exit nonzero if any **Unresolved mismatch**, **unknown source grapheme**, or
**untokenizable target** is found. Warnings and coverage gaps do not affect
the exit code — they are for human review.

## Report

Markdown to stdout (or `--output`). Sections, each scoped per dialect where
relevant:

- **Summary** — counts per tier and per dialect; overall pass/fail.
- **Confirmed equivalences** — `src → tgt` with the shared IPA.
- **Warnings — assumed equivalences** — each with the two IPA forms and the
  transform that reconciled them (e.g. "length↔doubling"), so a human can
  confirm.
- **Unresolved mismatches** — `src → tgt`, source IPA vs. target IPA.
- **Information loss** — merges and can't-encode findings.
- **Coverage** — source graphemes with no route to the output.
- **Table integrity** — unknown source graphemes, untokenizable targets.

## Testing

`tests/validators/test_validate_conversion_table.py` (pytest, building small
throwaway TSVs under `tmp_path`; one characterization test against the real
Rukai trio).

Loading / dialect resolution:
1. `test_loads_three_tsvs`
2. `test_dialect_column_selected_per_dialect_with_default_fallback`
3. `test_single_value_column_profile`

Core IPA equivalence:
4. `test_exact_ipa_match_confirmed`
5. `test_multigrapheme_target_tokenized` (`tr` as one grapheme; `aa` as `a`+`a`)
6. `test_length_notation_is_warning` (`a:`→`aa` ⇒ WARN, exit 0)
7. `test_tiebar_ligature_is_confirmed` (`t͡s`↔`ʦ`, no warning)
8. `test_bare_digraph_affricate_is_warning` (`ts`↔`t͡s` ⇒ WARN)
9. `test_true_mismatch_is_unresolved_and_exits_nonzero` (/p/→/b/)

Information loss & table integrity:
10. `test_phoneme_merge_detected` (Warning)
11. `test_original_cannot_encode_distinction` (Warning)
12. `test_unknown_source_grapheme_is_unresolved` (exit nonzero)
13. `test_untokenizable_target_is_unresolved` (exit nonzero)

Coverage & passthrough:
14. `test_uncovered_original_grapheme_reported` (Warning)
15. `test_identity_passthrough_ok` (same grapheme + IPA, no row ⇒ no gap)

Report & exit contract:
16. `test_report_has_documented_sections`
17. `test_exit_zero_when_only_warnings`
18. `test_rukai_li_113_real_files_smoke` (runs against the real Rukai trio;
    asserts it completes and `a:`→`aa` lands in the Warning section)

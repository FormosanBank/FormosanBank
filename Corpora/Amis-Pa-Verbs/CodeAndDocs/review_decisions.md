# Reviewed sentence decisions

The final source table incorporates these source-backed changes from the
manual-edit record:

- `s20c_person`: stop the person variant at `cingra`; keep the causee
  explanation as a translation note.
- `s20c_car`: retain `k-u-ni a paliding` as the complete car variant and store
  the `i.e.` reading as `ver="alt"`.
- `s20d`: retain only the grammatical person variant ending at `cingra`.
- `s36a-opt`: add the printed `i`/`PREP` case variant with the unstarred reading.
- `s38a_prime`: exclude the `??` example and its inconsistent name alignment.
- `s38c_prime`: exclude the `?` example.

The corresponding raw displays and locators remain in
`direct_source_checks.tsv` and `rejected_source_examples.tsv`.
The six records were pruned from `manual_edits.xml` on 2026-09-11 with the
maintainer's approval: all six were no-ops on every build because this table
encodes the same decisions, and POL-030 reserves `--prune` for exactly that
case. The decisions are the list above; their locators are in
`direct_source_checks.tsv` and `rejected_source_examples.tsv`.

September 2026 source review also restores obligatory `i/PREP` in 32c (POL-017),
the 22 printed S endings, and the unglossed Pa/fli M boundary. All six decisions
survive in this table.

The `i/PREP` case variant of 36a is `s36a-opt`, renamed from `s36aalt` on
2026-09-11: POL-028 was amended on 2026-09-10 to give a split's second block the
first block's id plus `-opt`. `s36a` keeps its id. Renamed before publication,
so POL-037 is not engaged.

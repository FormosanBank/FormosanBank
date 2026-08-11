# Reviewed sentence decisions

The final source table incorporates these source-backed manual-edit records:

- `s20c_person`: stop the person variant at `cingra`; keep the causee
  explanation as a translation note.
- `s20c_car`: retain `k-u-ni a paliding` as the complete car variant and store
  the `i.e.` reading as `ver="alt"`.
- `s20d`: retain only the grammatical person variant ending at `cingra`.
- `s36aalt`: add the printed `i`/`PREP` case variant with the unstarred reading.
- `s38a_prime`: exclude the `??` example and its inconsistent name alignment.
- `s38c_prime`: exclude the `?` example.

The corresponding raw displays and locators remain in
`direct_source_checks.tsv` and `rejected_source_examples.tsv`.
The records remain in `manual_edits.xml` as required no-ops because the
generator now emits the reviewed content directly. They must not be pruned
without an explicit review decision.

# Phase B regeneration — NTUFormosanCorpus (2026-08-12)

Branch `work/ntu` (off `work/classifier`, which carries the quote-classifier
fixes `59a4212ab`). The corpus's own documented pipeline, `CodeAndDocs/make.sh`,
was run end-to-end from the committed source JSONs (audio download skipped — XML
generation never reads audio files) and the result is what is committed here.

No POL-035 snapshot: this corpus is fully regenerable from committed inputs
(`CodeAndDocs/{grammar,sentence,story}`), so per POL-035 the pipeline *is* the
baseline.

## Pipeline changes made this turn

`make.sh` already had exactly one `clean_xml` pass, so the bank-wide
"remove the second `clean_xml`" ruling was a no-op here. Five changes were
needed to make a fresh run correct and self-contained:

1. **`make.sh` — sidecar routing.** `clean_xml` writes three files beside the
   XML it processes, and `make.sh` then rsyncs that directory into the published
   `XML/`. So `cleaner_warnings.csv`, `html_entities.log` and — worse — the
   durable `quote_corrections.csv` would all have been published inside `XML/`.
   The first two now move to `CodeAndDocs/` as per-run reports (POL-033, never
   committed); `quote_corrections.csv` is folded, append-only and with its paths
   rewritten to the corpus-relative `XML/…` form the other corpora use, into
   `CodeAndDocs/quote_corrections.csv` (POL-035, committed). `run_parsers.py`'s
   `sentences_with_bad_glosses_removed.csv` is installed at the corpus root
   where the README points users. Two `[[ … ]] && cmd` one-liners that would
   have aborted the script under `set -e` when their file was absent were
   rewritten as `if` blocks. `CodeAndDocs/Final_XML/` (the parser's working
   directory) was added to `.gitignore`.
2. **`run_parsers.py` — null-glyph canonicalization** in the existing
   normalization pass. See README step 1. Fixes 2 V124 findings and stops the
   annotation glyph leaking into the S-level standard FORM.
3. **`apply_manual_corrections.py` — standard-tier twins of the three
   Grammar/Sakizaya citation repairs.** Regression found by the diff audit; see
   README step 11.
4. **`apply_manual_corrections.py` — fresh-parse variants of the three Kavalan
   gloss-column-shift repairs.** The known regen-time worklist item from the
   2026-08-10 audit; see README step 11.
5. **README** rewritten where it described the old state.

The pipeline was run three times from scratch; the committed XML is run 3.

## Quote/glottal correction — 2 rewrites, both wrong

`work/classifier` reduced this corpus from 44 rewrites in 22 sentences to **2
rewrites in 1 sentence**, reproduced exactly here. Both land in
`Stories/Amis/Amis_Amis_Nr-frog_cinhua.xml`, `Amis_Nr-frog_cinhua_S_14`:

```
before  itini i hakini tuna 'pung sa'an ku falucu' nira a miceli'.
after   itini i hakini tuna "pung sa'an ku falucu' nira a miceli".
TRANSL  「是否在這個洞裡呢?」他這樣說,呼叫著.
TRANSL  'Is it inside this hole?' he said so and called.
```

- **Position 20 (`'pung` → `"pung`) — WRONG.** `'pung` is a word of this very
  text, carrying its own `<W>` and gloss: `S_12` "tayra cingra i kilakilangan
  mikilim tunian a 'pung." and `S_18` "ira ku ccay a 'pung itini i suta'." The
  `'` is the glottal-stop letter.
- **Position 56 (`miceli'` → `miceli"`) — WRONG.** `miceli'` ("call out")
  occurs with the same final glottal in five other sentences of the same file
  (`S_8`, `S_11`, `S_15`, `S_21`, `S_31`).

Both have one cause, and it is dictionary coverage rather than classifier logic:
NTU writes Amis in the `u` orthography while
`QC/validation/reference/Amis/attestation.txt` is `o`-only (`faloco'` is
present, `falucu'` is not), so no reading of either word can be looked up and
nothing vetoes the pairing. There *is* a quotation in this sentence — the
Chinese translation brackets it — but its span is the sentence-initial
`itini i hakini tuna 'pung`, not the quotative frame `sa'an … miceli'` the
classifier wrapped.

**Disposition.** Landed as produced, not hand-reverted: it is one sentence in
20,130, both rewrites are recorded in the committed `quote_corrections.csv`, the
maintainer inspected this exact case when lifting the Saisiyat guard and carried
it forward as a dictionary task, and reverting it in the correction table would
hide the defect and fight `clean_xml` on every run. **It is a genuine
original-tier corruption of two real words and should be undone** by extending
the Amis attestation dictionary with `u`-orthography forms (a reopening of
Amis's Phase A review under sweep ruling 1's revisitability clause) and
rerunning `make.sh`. Zero rewrites fired in the corpus's other nine languages,
so no other language's dictionary review gates this corpus.

735 further apostrophe positions were flagged ambiguous (`c030`) and left alone.

## Diff audit vs `main` (git HEAD) — 100% classified

193 files on both sides, 20,130 `<S>` on both sides, no file or sentence added
or removed, no `TEXT` attribute changed, all 14,663 AUDIO elements unchanged.
1,558 sentences are byte-identical; 18,572 differ. Element-level rows: 191,484,
every one classified.

| rows | class |
|---:|---|
| 98,242 | PHON: legacy `x~y` → `[x\|y]` variant notation (this is V147: 98,292 → 0) |
| 58,766 | PHON: segmentation `-` / clitic `=` / infix `<>` markers stripped |
| 32,631 | PHON: punctuation dropped |
| 682 | TRANSL: quote/bracket glyph normalization (`「」『』“”` → `＂`, `[…]` → `(…)`) |
| 310 | the 4 sentences that regained a dropped source word (all tiers, incl. PHON) |
| 222 | PHON: contextual rules now applying across removed boundaries (`ng`→`ŋ`, `s`→`ɕ`, `r`→`ʁ`) and the Sakizaya `ə`→`e` profile |
| 168 | id renumbering below a recovered/inserted `W` |
| 154 | PHON: `*` removed (nulls and unmapped characters are now silent) |
| 98 | borrowed/repaired segmentation: FORM + PHON re-split across `M`s |
| 44 | PHON emptied because the FORM is punctuation only |
| 42 | TRANSL: parenthetical-note extraction differs (regen usually drops a junk tail) |
| 40 | FORM: C012 strips segmentation `-` / clitic `=` from the S-level standard tier |
| 37 | FORM: null unit restored in the W standard tier (`ni-vatu-` → `ni-vatu-∅`), healing orphaned boundary markers left by the retired `remove_null_symbols.py` |
| 22 | FORM: null glyph `ø`/`Ø` → `∅` |
| 13 | FORM: Kavalan/Tsou trailing-punctuation drift (`Raw.`→`Raw`, `o...`→`o`, `wu—`→`wu.`) |
| 6 | TRANSL: em/en dash → `-` |
| 5 | FORM: dash / fullwidth canonicalization |
| 2 | FORM: the Amis quote correction (1 sentence × 2 tiers) — **false positive**, above |
| **0** | **UNEXPLAINED** |

Structural detail behind the 310 + 168 rows — the whole inventory change is
+4 `W`, +8 `M`, +24 FORM/PHON, +24 TRANSL, in four sentences:

- `Sentences/Rukai` `20200529-FW-Lixing-2_S_2` regains `malra`. This is the
  POL-017 fix (`*(X)` = obligatory, keep unstarred; `(*X)` = forbidden, drop)
  landing in published data for the first time — the parser fix `149537a10` was
  committed but its effect was deferred to this regeneration.
- `Sentences/Kanakanavu` `3_S_190` regains `arivuree=maku`, and `3_S_190-opt`,
  `3_S_27-opt` regain a word each — source words the previous publication had
  dropped.

Inserting a word shifts the positional `W`/`M` ids after it (168 rows). This is
a POL-037 id change, confined to these four sentences and forced by the
recovery: the alternative is publishing the sentence without its word.

## Token delta

Computed with `QC/count_tokens.py` (standard tier, original fallback):

| language | before | after | delta |
|---|---:|---:|---:|
| Kanakanavu | 20,352 | 20,355 | +3 |
| Rukai | 17,985 | 17,986 | +1 |
| Amis, Atayal, Bunun, Kavalan, Saisiyat, Sakizaya, Seediq, Tsou | — | — | 0 |
| **total** | **149,565** | **149,569** | **+4** |

Contrary to expectation there is **no counting discontinuity to announce**: C012
only removes word-internal markers, and the null units it strips are fused, so
neither creates or destroys a whitespace token. The +4 are exactly the four
recovered words.

## Validators, before → after (this corpus only; `validate_xml` over all of
`Corpora/` OOMs)

| | before | after | note |
|---|---:|---:|---|
| `validate_xml` HARD | 4,160 | 4,146 | |
| V017 form_must_have_content | 2,080 | 2,062 | −18: empty `M` FORM shells filled by `borrow_segmentation`; +2 new (the recovered `arivuree=maku` has 3 glosses against 2 form pieces) |
| V073 phon_non_empty | 2,080 | 2,084 | same fills, plus 11 elements whose FORM is punctuation only and 2 from the recovery |
| `validate_text` HARD | 580 | 589 | |
| V121 parens_slashes_in_W_or_M_FORM | 580 | 580 | unchanged; the standing manual worklist (README step 20) |
| V124 / V125 null propagation | 0 | 4 / 5 | newly surfaced source condition, see README "user beware" |
| `validate_text` SOFT | 101,303 | 2,997 | |
| V147 phon_legacy_tilde_variant | 98,292 | **0** | the headline win |
| V122 parens_slashes_anywhere | 2,880 | 2,875 | |
| V133 dash_in_S_standard_FORM | 48 | 12 | C012 |
| V126 equal_sign_in_S_standard | 14 | 7 | C012 |
| V116 non_ascii_in_form | 46 | 80 | the `∅` markers now retained in W/M standard FORMs |
| V137 | 5 | 5 | |
| V111 / V134 / V141 / V142 | 10 / 4 / 2 / 2 | unchanged | |
| `validate_glosses` HARD | 12,862 | 12,865 | |
| V062 infix_M_needs_angle_gloss | 50 | 50 | |
| V066 clitic_in_W_requires_clitic_in_M | 12,801 | 12,804 | +3 from the recovered clitic-bearing words |
| V067 no_angle_brackets_in_M_FORM | 11 | 11 | |
| `validate_glosses` SOFT | 4,825 | 4,817 | V061 950 → 942 |

**The expected large HARD reduction did not happen, because two of its premises
are not true on this branch.** POL-023's per-sentence V144 amendment *has*
landed (V144 = 0 here; `validate_xml` reports no SOFT findings at all), but
**V062 and V064 are still HARD** in `QC/validation/rules/gloss.py` — no
severity change exists on `work/classifier` or `main`. If that downgrade is
intended, it is still to be written.

## Issue #67 dispositions

| claim | verdict |
|---|---|
| 2,080 V017 + 2,080 V073 across 119 files | CONFIRMED at HEAD → now 2,062 / 2,084 |
| 580 V121 | CONFIRMED, unchanged (manual worklist, README step 20) |
| 50 V062, 12,801 V066, 11 V067 | CONFIRMED → 50 / 12,804 / 11 |
| 796 within-file + 34 cross-file duplicate groups | CONFIRMED as counts |
| "upgraded to HARD because the corpus pipeline declares deduplication under POL-022" | **WRONG.** `validate_duplicate_sentences.dedup_in_pipeline` greps `CodeAndDocs/` for `remove_duplicate_sentences\|dedup`; it matches `dedupe_sentence_ids.py`, which renames duplicate *ids*. NTU declares no sentence dedup, and its narrative material is exactly what POL-022 says may repeat. Recommend tightening the token to `remove_duplicate_sentences` (bank-wide QC change, not made here) |
| 7 V144 | STALE — 0 under the per-sentence POL-023 amendment |
| 2 V141, 2 V142 | CONFIRMED, unchanged |
| 98,292 V147 | CONFIRMED → **0** |
| audio statistics stale for Sakizaya and Tegudaya | CONFIRMED (`get_corpus_stats.py --report-stale-audio`); out of scope here, needs `refresh_audio_stats.py` |
| "repair the earliest responsible source/generator layer" | followed: the null-glyph fix went into the parser, not into a post-hoc script |

## Open items for the maintainer

1. **Amis attestation dictionary** — add `u`-orthography forms so the one quote
   false positive stops firing, then rerun `make.sh` (reopens Amis Phase A).
2. **V062/V064 severity** — the expected SOFT downgrade does not exist in code.
3. **`validate_duplicate_sentences` dedup detection** — token is too loose.
4. **Audio stats** — Sakizaya and Tegudaya seconds are stale.
5. **V124/V125 ×9** — source condition; needs a linguistic call, not a script.
6. **Citation repairs before `standardize`** — the three Grammar/Sakizaya
   records are currently repaired twice (once per tier) because the correction
   step runs after standardization; repairing them pre-standardize would remove
   the standard-tier entries.
7. **GitBook corpus page** — not touched this turn (sweep ruling 4 step 9).

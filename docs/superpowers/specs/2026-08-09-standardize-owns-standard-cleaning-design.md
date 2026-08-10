# standardize owns standard-tier cleaning — design

## Goal

Make `standardize.py` produce a **clean** standard tier at the moment it creates
it, so the redundant post-`standardize` `clean_xml` pass can be dropped. Split
responsibilities cleanly by tier, and add dash/hyphen canonicalization to the
original-tier cleanup. The **original tier is never changed in meaning** — only
punctuation is canonicalized on it (dashes → `-`), as `clean_xml` already
canonicalizes other punctuation.

Today the pipeline is `clean_xml → standardize → clean_xml → add_phonology`. The
second `clean_xml` exists only because `standardize` regenerates the standard
FORM from the original (re-importing the original's hyphens), and C012 (hyphen
stripping) is the *only* standard-tier-specific operation in `clean_xml`. After
this change the pipeline is `clean_xml → standardize → add_phonology`.

## Responsibility split (the core boundary)

- **`standardize` owns every `FORM[@kindOf='standard']` — S, W, and M.** It already
  regenerates all of them: its loop is `root.findall('.//FORM/..')`
  ([standardize.py:55](../../../QC/utilities/standardize.py#L55)), the parent of
  *every* FORM, so `create_standard` runs on S, W and M elements, recreating each
  standard FORM from the sibling original FORM.
- **`clean_xml` owns all `FORM[@kindOf='original']` (S/W/M), TRANSL, and metadata**
  — and **stops touching any `FORM[@kindOf='standard']` at any level.**

C012 (hyphen stripping) stays **S-level only**: standardize applies it just when
the element is an `S`, so W/M standard FORMs keep their morpheme segmentation
exactly as today. W/M standard FORMs are still recreated (and therefore inherit
the cleaned original, including dash canonicalization) — they simply are not
C012-stripped.

## `clean_xml.py` changes

1. **Restrict FORM cleanup to original FORMs.** The FORM loop
   ([clean_xml.py:619](../../../QC/cleaning/clean_xml.py#L619), currently
   `sentence.findall('.//FORM')`) must skip **every** `FORM[@kindOf='standard']`
   (S, W, and M). Its general cleanup (`clean_text`) and the c022 `*` warning then
   apply only to the original FORMs at all levels. TRANSL and metadata handling
   unchanged.
2. **Remove C012 from `clean_xml`.** Delete the `_process_standard_hyphens` call
   ([clean_xml.py:665-682](../../../QC/cleaning/clean_xml.py#L665)) and move the
   function to `standardize` (see below). Remove the flags that only C012 used:
   `--hard-remove-segmentation` and `--ortho-path`. (Verify during implementation
   that nothing else in `clean_xml` reads `ortho_path`.)
3. **Add dash/hyphen canonicalization to `swap_punctuation`.** Map every
   hyphen/dash look-alike and its full-width form to ASCII HYPHEN-MINUS `-`
   (U+002D), on the original tier (part of `clean_text`, so W/M FORMs get it too):

   | codepoint | char | name |
   |---|---|---|
   | U+2010 | ‐ | HYPHEN |
   | U+2011 | ‑ | NON-BREAKING HYPHEN |
   | U+2012 | ‒ | FIGURE DASH |
   | U+2013 | – | EN DASH |
   | U+2014 | — | EM DASH |
   | U+2015 | ― | HORIZONTAL BAR |
   | U+2212 | − | MINUS SIGN |
   | U+FE58 | ﹘ | SMALL EM DASH |
   | U+FE63 | ﹣ | SMALL HYPHEN-MINUS |
   | U+FF0D | － | FULLWIDTH HYPHEN-MINUS |

   This is intentional new behavior (canonicalizes all dashes to one character on
   the original tier). Downstream, `standardize`'s C012 then treats the resulting
   `-` uniformly (stripped from standard for all languages except Bunun/Thao,
   where it is a letter and preserved).

## `standardize.py` changes

1. **Own the C012 transform (S-level only).** `create_standard`/`apply_standard`
   already run on S, W and M elements. After a standard FORM is written, apply the
   moved `_process_standard_hyphens` **only when the element is an `S`** (guard on
   `element.tag == 'S'`): strip `-` and clitic `=` and null `Ø` (and its bridging
   hyphen); for Bunun/Thao (where `-` is an orthographic letter) preserve `-` and
   warn, unless `--hard-remove-segmentation`. W/M standard FORMs are recreated but
   NOT C012-stripped (they keep segmentation). Preserve mixed content
   (`<UNCLEAR/>`) — apply only to `form.text`, never to element children
   (`_copy_mixed_content` already deep-copies children).
2. **Reuse the resolved language/dialect.** `standardize` already computes
   `dialect = root.get('dialect')` and `language = ISO_TO_LANGUAGE.get(xlang)`
   ([standardize.py:215-224](../../../QC/utilities/standardize.py#L215)) for column
   selection. The hyphen-is-letter check reuses that — no separate `xml:lang`
   parse. (`_hyphen_is_letter` may be adapted to take a language name directly.)
3. **Do NOT re-run the general cleanup.** The standard FORM is a copy of the
   already-clean original, so NFC / caret / punctuation / whitespace / dash
   canonicalization are inherited. `standardize` adds only the standard-specific
   transform (C012).
4. **Emit the same warnings.** Reuse `CleanerWarnings` to write, to
   `standardize`'s own warnings CSV (`standardize_warnings.csv` under
   `--corpora_path`), the c012 (hyphen preserved — S-level only, matching C012's
   scope) and c022 (`*` in a standard FORM standardize created) rows that
   `clean_xml` no longer emits for the standard tier. Gains
   `--hard-remove-segmentation` and `--ortho-path`.

## CLI summary

- `clean_xml.py`: **loses** `--hard-remove-segmentation`, `--ortho-path`.
- `standardize.py`: **gains** `--hard-remove-segmentation`, `--ortho-path`.
- The `--copy` / `--remove_accents` / `--tsv_path` / `--target_column` behavior of
  `standardize` is unchanged except that the produced standard FORM is now cleaned
  (C012) before it is written.

## Edge cases to verify

- **TSV mode.** `apply_standard` runs `strip_accents` + table replacements on the
  standard FORM. This design assumes those outputs are already clean (no new
  full-width / smart-quote / dash characters that `clean_text` would have fixed).
  If the equivalence test (below) shows otherwise for any table, revisit.
- **No preceding `clean_xml`.** As today, `standardize` assumes the original tier
  was already cleaned by a prior `clean_xml`. Running `standardize` on an
  un-cleaned original produces an un-cleaned (but C012-processed) standard — same
  assumption as the current pipeline.

## Testing

**Committed unit tests** (`tests/…`, following existing pytest conventions):

1. `swap_punctuation` maps each of the 10 dash/hyphen variants → `-`; idempotent;
   ASCII `-` unchanged.
2. `standardize` C012 on the standard tier: strips `-`/`=`/`Ø` for a non-Bunun/Thao
   language; preserves `-` (and warns c012) for Bunun and Thao; `--hard-remove-segmentation`
   strips anyway with no warning; mixed-content `<UNCLEAR/>` survives.
3. `clean_xml` no longer alters any standard FORM (S/W/M): feed a doc whose
   standard FORMs have dashes/hyphens; assert `clean_xml` leaves every
   `kindOf='standard'` FORM untouched while canonicalizing dashes → `-` in the
   original FORMs at all levels.
4. W/M behavior in `standardize`: a word-segmented doc's W and M standard FORMs
   are recreated from their originals (so they inherit dash canonicalization) but
   **retain** their segmentation hyphens (C012 not applied below S).
5. `standardize` writes c012/c022 rows to its warnings CSV.

**Temporary tests** (NOT committed — throwaway, to confirm no regression):

6. **Equivalence snapshot** of the C012-move (behavior-preserving part): for a
   Bunun/Thao corpus, a `--copy` corpus, and a TSV corpus, assert the standard
   FORM + both PHON tiers from `standardize_new` equal those from
   `standardize_old → clean_xml_old`, after canonicalizing the intended
   dash-normalization difference on both sides (so the comparison isolates the
   C012 move) and ignoring known XML-serialization noise.
7. **Song-Kanakanavu full pipeline**: run its rebuild end-to-end with the
   refactored scripts; `normalize_standard_forms.py` must complete without raising
   (its own asserts anchor the 128 decisions against the untouched original tier),
   and the final standard tier must match the committed one. If it does not
   already assert every decision was *applied* (not merely loaded), add that
   assertion to the temporary harness.

## Out of scope (separate follow-ups)

- Updating corpus READMEs to drop the now-redundant second `clean_xml` pass.
- Any change to the original tier's *content* beyond punctuation canonicalization.
- Bespoke per-corpus standard-tier scripts (e.g. Song-Kanakanavu's
  `normalize_standard_forms`, Safolu's dedup) remain their own pipeline steps.

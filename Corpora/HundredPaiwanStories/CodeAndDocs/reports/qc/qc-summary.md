# QC summary

## Inventory

- 100 TEXT elements
- 2,921 S elements
- 24,556 W elements
- 36,938 M elements
- 64,515 globally unique TEXT, S, W, and M IDs
- all 64,198 previously published IDs preserved

## Validator results

Findings per validator, by severity (all rules, reviewed or not):

- XML: no findings
- Text: 8,094 SOFT
- Gloss: 1,346 SOFT
- Gloss scrape: 1 HARD, 1 SOFT, 158 WARN

Reviewed rules:

- Text: 8,028 V122 soft findings
- Gloss: 1,302 V061 soft findings, 1 V064 soft finding
- Gloss scrape: 1 accepted G001 hard finding, 1 G002 soft finding, 0 G003 soft findings (1,370 infix-root gap forms, all exempt under POL-014), 153 G010 warnings

## Reviewed soft findings

- V061: all 1,302 are reduplicated W forms using the canonical tilde marker. The validator does not split `~` when estimating the M count.
- G010: all 153 are source hyphens kept in the original tier; the standard tier carries none. V133 does not fire: no standard FORM contains a hyphen.
- V122: all 8,028 are preserved source TRANSL and W/M FORM notation. No sentence FORM carries a parenthesis: the source’s "(?)" annotation is recorded in a notes attribute instead. Parentheses are balanced after the recorded 057S3 punctuation repair. The occurrences comprise 448 in source free translations, 3,790 in source W glosses, and 3,790 in source M glosses.

## Findings from rules this corpus has not reviewed

These come from shared validator rules added or changed after this corpus's
review. They are reported here and do not stop the build; any HARD finding
other than the accepted G001 does. The per-finding detail is in the
validators' CSVs, which the build writes but does not commit.

- G014 `rare_gloss_is_substring_of_dominant` (scrape): 5 WARN
- V135 `trailing_punct_mismatch` (text): 66 SOFT
- V153 `gloss_pieces_match_morphemes` (gloss): 43 SOFT

No remaining finding blocks publication. The corpus is ready to port under the rights conditions recorded in the corpus README.
